import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "grill-jev" / "scripts" / "grill_jev.py"
SPEC = importlib.util.spec_from_file_location("grill_jev", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)


def load_example(domain: str):
    state = json.loads((ROOT / "examples" / domain / "decision-state.json").read_text())
    plan = json.loads((ROOT / "examples" / domain / "evaluation-plan.json").read_text())
    return state, plan


def fake_backend_result(
    state,
    plan,
    *,
    choice_confidence=0.80,
    candidate_coverage=0.20,
    violation_overrides=None,
):
    violation_overrides = violation_overrides or {}
    options = state["options"]
    probabilities = {
        option["id"]: (0.6 if i == 0 else 0.4 / max(1, len(options) - 1))
        for i, option in enumerate(options)
    }

    result = {
        "backend": "fake",
        "model": "fake-1",
        "choices": {
            "overall_choice": {
                "choice": options[0]["id"],
                "confidence": choice_confidence,
                "probabilities": probabilities,
            }
        },
        "scores": {},
        "nouls": {
            "candidate_coverage": candidate_coverage,
        },
    }

    for dim in plan["dimensions"]:
        for option in options:
            qid = f"score__{dim['id']}__{option['id']}"
            result["scores"][qid] = {
                "score": 3.5,
                "confidence": 0.8,
                "probabilities": {"0": 0.05, "1": 0.10, "2": 0.15, "3": 0.30, "4": 0.40},
                "legend": {str(i): label for i, label in enumerate(dim["rubric"])},
            }

    for constraint in state["constraints"]:
        if constraint["severity"] != "hard":
            continue
        for option in options:
            qid = f"violation__{constraint['id']}__{option['id']}"
            result["nouls"][qid] = violation_overrides.get(
                (constraint["id"], option["id"]),
                0.05,
            )

    return result


class FailingBackend:
    name = "fake-failing"

    def evaluate(self, *, state, questions):
        raise mod.BackendError("simulated outage")


class GrillJevProtocolTests(unittest.TestCase):
    def setUp(self):
        self.state, self.plan = load_example("game-design")

    def test_example_validates(self):
        mod.validate_decision_state(self.state)
        mod.validate_evaluation_plan(self.plan, self.state)

    def test_product_example_validates(self):
        state, plan = load_example("product")
        mod.validate_decision_state(state)
        mod.validate_evaluation_plan(plan, state)

    def test_recommendation_firewall_rejects_nested_leak(self):
        bad = json.loads(json.dumps(self.state))
        bad["facts"].append({
            "id": "leak",
            "text": "Agent recommendation: option B is best",
            "source": "assistant"
        })
        with self.assertRaises(mod.ProtocolError):
            mod.enforce_recommendation_firewall(bad)

    def test_duplicate_option_ids_rejected(self):
        bad = json.loads(json.dumps(self.state))
        bad["options"][1]["id"] = bad["options"][0]["id"]
        with self.assertRaises(mod.ProtocolError):
            mod.validate_decision_state(bad)

    def test_plan_basis_must_resolve(self):
        bad = json.loads(json.dumps(self.plan))
        bad["dimensions"][0]["basis"] = ["goal:not-real"]
        with self.assertRaises(mod.ProtocolError):
            mod.validate_evaluation_plan(bad, self.state)

    def test_dry_run_contains_all_question_kinds(self):
        payload = mod.build_dry_run_payload(self.state, self.plan)
        kinds = {q["type"] for q in payload["questions"].values()}
        self.assertEqual(kinds, {"choice", "score", "noul"})

    def test_state_hash_is_stable(self):
        self.assertEqual(
            mod.state_hash(self.state),
            mod.state_hash(json.loads(json.dumps(self.state))),
        )

    def test_hard_constraint_threshold_marks_violation(self):
        state, plan = load_example("product")
        result = fake_backend_result(
            state,
            plan,
            violation_overrides={("offline", "B"): 0.91},
        )
        evidence = mod.build_decision_evidence(
            state,
            plan,
            result,
            constraint_warning_threshold=0.75,
            missing_alternative_threshold=0.65,
            low_confidence_threshold=0.55,
        )
        self.assertEqual(
            evidence["constraint_checks"]["offline"]["options"]["B"]["status"],
            "violation",
        )
        self.assertEqual(
            evidence["constraint_checks"]["offline"]["options"]["A"]["status"],
            "pass",
        )

    def test_missing_alternative_threshold_requests_expansion(self):
        state, plan = load_example("product")
        result = fake_backend_result(
            state,
            plan,
            candidate_coverage=0.80,
        )
        evidence = mod.build_decision_evidence(
            state,
            plan,
            result,
            constraint_warning_threshold=0.75,
            missing_alternative_threshold=0.65,
            low_confidence_threshold=0.55,
        )
        self.assertEqual(
            evidence["missing_alternative"]["status"],
            "expand_candidates",
        )

    def test_low_confidence_returns_agent_reasoning_fallback(self):
        state, plan = load_example("product")
        result = fake_backend_result(
            state,
            plan,
            choice_confidence=0.40,
        )
        evidence = mod.build_decision_evidence(
            state,
            plan,
            result,
            constraint_warning_threshold=0.75,
            missing_alternative_threshold=0.65,
            low_confidence_threshold=0.55,
        )
        self.assertEqual(evidence["status"], "low_confidence")
        self.assertEqual(evidence["fallback"]["action"], "agent_reasoning")

    def test_backend_failure_degrades_without_interrupting_flow(self):
        state, plan = load_example("product")
        evidence = mod.evaluate_with_backend(
            state,
            plan,
            FailingBackend(),
            strict_backend=False,
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(evidence["fallback"]["action"], "agent_reasoning")

    def test_strict_backend_failure_raises(self):
        state, plan = load_example("product")
        with self.assertRaises(mod.BackendError):
            mod.evaluate_with_backend(
                state,
                plan,
                FailingBackend(),
                strict_backend=True,
            )


if __name__ == "__main__":
    unittest.main()
