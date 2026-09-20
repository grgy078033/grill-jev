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


class GrillJevProtocolTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((ROOT / "examples" / "game-design" / "decision-state.json").read_text())
        self.plan = json.loads((ROOT / "examples" / "game-design" / "evaluation-plan.json").read_text())

    def test_example_validates(self):
        mod.validate_decision_state(self.state)
        mod.validate_evaluation_plan(self.plan, self.state)

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
        self.assertEqual(mod.state_hash(self.state), mod.state_hash(json.loads(json.dumps(self.state))))


if __name__ == "__main__":
    unittest.main()
