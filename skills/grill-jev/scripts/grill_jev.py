#!/usr/bin/env python3
"""grill-jev evaluator.

Validates DecisionState + EvaluationPlan, builds typed decision questions,
delegates provider-specific work to a backend adapter, and converts the result
into portable DecisionEvidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from backends import BackendError, DecisionBackend, make_backend


DEFAULT_CONSTRAINT_WARNING_THRESHOLD = 0.75
DEFAULT_MISSING_ALTERNATIVE_THRESHOLD = 0.65
DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.55


class ProtocolError(ValueError):
    pass


FORBIDDEN_KEY_FRAGMENTS = {
    "recommendation",
    "agent_recommendation",
    "assistant_preference",
    "preferred_option",
    "previous_jev",
    "jev_result",
}

FORBIDDEN_TEXT_PATTERNS = [
    re.compile(r"\bagent recommendation\b", re.I),
    re.compile(r"\bassistant (?:prefers|preference|recommends?)\b", re.I),
    re.compile(r"\bi (?:prefer|recommend) option\b", re.I),
    re.compile(r"\bjev (?:preferred|recommends?|selected)\b", re.I),
]


def load_json(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"Could not read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProtocolError(f"Expected a JSON object in {path}")
    return value


def _require(obj: dict[str, Any], keys: set[str], where: str) -> None:
    missing = keys - obj.keys()
    if missing:
        raise ProtocolError(f"{where} missing required fields: {sorted(missing)}")


def _reject_extra(obj: dict[str, Any], allowed: set[str], where: str) -> None:
    extra = obj.keys() - allowed
    if extra:
        raise ProtocolError(f"{where} has unsupported fields: {sorted(extra)}")


def _nonempty_str(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"{where} must be a non-empty string")
    return value.strip()


def _probability(value: float, where: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ProtocolError(f"{where} must be between 0 and 1")
    return value


def enforce_recommendation_firewall(
    value: Any,
    path: str = "$",
    key: str | None = None,
) -> None:
    if key is not None:
        lowered = key.lower()
        if lowered in FORBIDDEN_KEY_FRAGMENTS or any(
            fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS
        ):
            raise ProtocolError(
                f"Recommendation Firewall blocked field at {path}: {key}"
            )

    if isinstance(value, dict):
        for k, v in value.items():
            enforce_recommendation_firewall(v, f"{path}.{k}", k)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            enforce_recommendation_firewall(item, f"{path}[{i}]", key)
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                raise ProtocolError(
                    f"Recommendation Firewall blocked recommendation-like prose at {path}"
                )


def validate_decision_state(state: dict[str, Any]) -> None:
    enforce_recommendation_firewall(state)
    allowed = {
        "schema_version",
        "decision",
        "objective",
        "goals",
        "constraints",
        "settled_decisions",
        "facts",
        "options",
        "unknowns",
    }
    _require(state, allowed, "DecisionState")
    _reject_extra(state, allowed, "DecisionState")

    if state["schema_version"] != "0.1":
        raise ProtocolError("DecisionState.schema_version must be '0.1'")

    decision = state["decision"]
    if not isinstance(decision, dict):
        raise ProtocolError("decision must be an object")
    _require(decision, {"id", "question"}, "decision")
    _reject_extra(decision, {"id", "question"}, "decision")
    _nonempty_str(decision["id"], "decision.id")
    _nonempty_str(decision["question"], "decision.question")

    objective = state["objective"]
    if not isinstance(objective, dict):
        raise ProtocolError("objective must be an object")
    _require(objective, {"primary"}, "objective")
    _reject_extra(objective, {"primary"}, "objective")
    _nonempty_str(objective["primary"], "objective.primary")

    def validate_sourced(
        items: Any,
        where: str,
        constraint: bool = False,
    ) -> None:
        if not isinstance(items, list):
            raise ProtocolError(f"{where} must be an array")
        seen: set[str] = set()
        required_fields = {"id", "text", "source"} | (
            {"severity"} if constraint else set()
        )

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise ProtocolError(f"{where}[{i}] must be an object")
            _require(item, required_fields, f"{where}[{i}]")
            _reject_extra(item, required_fields, f"{where}[{i}]")
            item_id = _nonempty_str(item["id"], f"{where}[{i}].id")
            if item_id in seen:
                raise ProtocolError(f"Duplicate id {item_id!r} in {where}")
            seen.add(item_id)
            _nonempty_str(item["text"], f"{where}[{i}].text")
            _nonempty_str(item["source"], f"{where}[{i}].source")
            if constraint and item["severity"] not in {"hard", "soft"}:
                raise ProtocolError(
                    f"{where}[{i}].severity must be hard or soft"
                )

    validate_sourced(state["goals"], "goals")
    validate_sourced(state["constraints"], "constraints", constraint=True)
    validate_sourced(state["settled_decisions"], "settled_decisions")
    validate_sourced(state["facts"], "facts")

    options = state["options"]
    if not isinstance(options, list) or len(options) < 2:
        raise ProtocolError("options must contain at least two candidates")

    seen_options: set[str] = set()
    for i, option in enumerate(options):
        if not isinstance(option, dict):
            raise ProtocolError(f"options[{i}] must be an object")
        _require(option, {"id", "text"}, f"options[{i}]")
        _reject_extra(option, {"id", "text"}, f"options[{i}]")
        option_id = _nonempty_str(option["id"], f"options[{i}].id")
        if option_id in seen_options:
            raise ProtocolError(f"Duplicate option id: {option_id}")
        seen_options.add(option_id)
        _nonempty_str(option["text"], f"options[{i}].text")

    unknowns = state["unknowns"]
    if not isinstance(unknowns, list) or any(
        not isinstance(x, str) or not x.strip() for x in unknowns
    ):
        raise ProtocolError("unknowns must be an array of non-empty strings")


def available_basis_refs(state: dict[str, Any]) -> set[str]:
    refs = set()
    refs.update(f"goal:{x['id']}" for x in state["goals"])
    refs.update(f"constraint:{x['id']}" for x in state["constraints"])
    refs.update(f"settled:{x['id']}" for x in state["settled_decisions"])
    refs.update(f"fact:{x['id']}" for x in state["facts"])
    refs.add("objective:primary")
    return refs


def validate_evaluation_plan(
    plan: dict[str, Any],
    state: dict[str, Any],
) -> None:
    allowed = {"schema_version", "decision_id", "dimensions"}
    _require(plan, allowed, "EvaluationPlan")
    _reject_extra(plan, allowed, "EvaluationPlan")

    if plan["schema_version"] != "0.1":
        raise ProtocolError("EvaluationPlan.schema_version must be '0.1'")
    if plan["decision_id"] != state["decision"]["id"]:
        raise ProtocolError(
            "EvaluationPlan.decision_id must match DecisionState.decision.id"
        )

    dims = plan["dimensions"]
    if not isinstance(dims, list) or not dims:
        raise ProtocolError(
            "EvaluationPlan.dimensions must contain at least one dimension"
        )

    valid_refs = available_basis_refs(state)
    seen: set[str] = set()

    for i, dim in enumerate(dims):
        where = f"dimensions[{i}]"
        if not isinstance(dim, dict):
            raise ProtocolError(f"{where} must be an object")

        fields = {"id", "label", "instruction", "basis", "rubric"}
        _require(dim, fields, where)
        _reject_extra(dim, fields, where)

        dim_id = _nonempty_str(dim["id"], f"{where}.id")
        if dim_id in seen:
            raise ProtocolError(f"Duplicate dimension id: {dim_id}")
        seen.add(dim_id)

        _nonempty_str(dim["label"], f"{where}.label")
        _nonempty_str(dim["instruction"], f"{where}.instruction")

        basis = dim["basis"]
        if not isinstance(basis, list) or not basis:
            raise ProtocolError(
                f"{where}.basis must contain at least one reference"
            )

        unknown_refs = [ref for ref in basis if ref not in valid_refs]
        if unknown_refs:
            raise ProtocolError(
                f"{where}.basis contains unknown refs: {unknown_refs}"
            )

        rubric = dim["rubric"]
        if not isinstance(rubric, list) or not 2 <= len(rubric) <= 10:
            raise ProtocolError(
                f"{where}.rubric must contain 2-10 ordered levels"
            )

        for j, level in enumerate(rubric):
            _nonempty_str(level, f"{where}.rubric[{j}]")


def state_hash(state: dict[str, Any]) -> str:
    canonical = json.dumps(
        state,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def normalized_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": state["decision"],
        "objective": state["objective"],
        "goals": state["goals"],
        "constraints": state["constraints"],
        "settled_decisions": state["settled_decisions"],
        "facts": state["facts"],
        "options": state["options"],
        "unknowns": state["unknowns"],
    }


def build_dry_run_payload(
    state: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    option_map = {o["id"]: o["text"] for o in state["options"]}

    questions: dict[str, Any] = {
        "overall_choice": {
            "type": "choice",
            "instructions": (
                "Which candidate option best fits the stated objective, goals, "
                "constraints, settled decisions, facts, and known unknowns? "
                "Judge only the supplied state; do not infer an agent preference."
            ),
            "criteria": option_map,
        },
        "candidate_coverage": {
            "type": "noul",
            "instructions": (
                "Do the currently supplied candidate options omit a materially "
                "distinct, viable alternative that is strongly implied by the "
                "stated decision state?"
            ),
        },
    }

    for dim in plan["dimensions"]:
        for option in state["options"]:
            qid = f"score__{dim['id']}__{option['id']}"
            questions[qid] = {
                "type": "score",
                "instructions": (
                    f"{dim['instruction']} Evaluate candidate "
                    f"{option['id']}: {option['text']}"
                ),
                "criteria": dim["rubric"],
                "basis": dim["basis"],
            }

    for constraint in state["constraints"]:
        if constraint["severity"] != "hard":
            continue

        for option in state["options"]:
            qid = (
                f"violation__{constraint['id']}__{option['id']}"
            )
            questions[qid] = {
                "type": "noul",
                "instructions": (
                    f"Does candidate {option['id']} ({option['text']}) "
                    f"violate this hard constraint: {constraint['text']}?"
                ),
            }

    return {
        "state_hash": state_hash(state),
        "state": normalized_state(state),
        "questions": questions,
    }


def build_decision_evidence(
    state: dict[str, Any],
    plan: dict[str, Any],
    backend_result: dict[str, Any],
    *,
    constraint_warning_threshold: float,
    missing_alternative_threshold: float,
    low_confidence_threshold: float,
) -> dict[str, Any]:
    constraint_warning_threshold = _probability(
        constraint_warning_threshold,
        "constraint_warning_threshold",
    )
    missing_alternative_threshold = _probability(
        missing_alternative_threshold,
        "missing_alternative_threshold",
    )
    low_confidence_threshold = _probability(
        low_confidence_threshold,
        "low_confidence_threshold",
    )

    try:
        overall = backend_result["choices"]["overall_choice"]
        coverage_probability = float(
            backend_result["nouls"]["candidate_coverage"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProtocolError(
            "Backend result is missing required overall_choice or candidate_coverage answers"
        ) from exc

    overall_confidence = _probability(
        float(overall["confidence"]),
        "overall_choice.confidence",
    )
    coverage_probability = _probability(
        coverage_probability,
        "candidate_coverage",
    )

    status = "ok"
    warnings: list[str] = []
    fallback: dict[str, Any] | None = None

    if overall_confidence < low_confidence_threshold:
        status = "low_confidence"
        warnings.append(
            "Overall Choice confidence is below the configured threshold."
        )
        fallback = {
            "action": "agent_reasoning",
            "reason": (
                "Treat Jev as weak evidence and continue using normal agent "
                "reasoning before asking the user to decide."
            ),
        }

    evidence: dict[str, Any] = {
        "schema_version": "0.1",
        "status": status,
        "decision_id": state["decision"]["id"],
        "state_hash": state_hash(state),
        "backend": {
            "name": backend_result.get("backend", "unknown"),
            "model": backend_result.get("model"),
        },
        "policy": {
            "constraint_warning_threshold": constraint_warning_threshold,
            "missing_alternative_threshold": missing_alternative_threshold,
            "low_confidence_threshold": low_confidence_threshold,
        },
        "overall_choice": {
            "choice": str(overall["choice"]),
            "confidence": overall_confidence,
            "probabilities": {
                str(k): _probability(float(v), f"overall_choice.probabilities.{k}")
                for k, v in dict(overall["probabilities"]).items()
            },
        },
        "dimensions": {},
        "constraint_checks": {},
        "missing_alternative": {
            "probability": coverage_probability,
            "status": (
                "expand_candidates"
                if coverage_probability >= missing_alternative_threshold
                else "complete_enough"
            ),
        },
        "warnings": warnings,
        "fallback": fallback,
    }

    scores = backend_result.get("scores", {})
    for dim in plan["dimensions"]:
        dim_out: dict[str, Any] = {
            "label": dim["label"],
            "basis": dim["basis"],
            "options": {},
        }

        for option in state["options"]:
            qid = f"score__{dim['id']}__{option['id']}"
            try:
                answer = scores[qid]
            except KeyError as exc:
                raise ProtocolError(
                    f"Backend result is missing score answer: {qid}"
                ) from exc

            dim_out["options"][option["id"]] = {
                "score": float(answer["score"]),
                "confidence": _probability(
                    float(answer["confidence"]),
                    f"{qid}.confidence",
                ),
                "probabilities": {
                    str(k): _probability(float(v), f"{qid}.probabilities.{k}")
                    for k, v in dict(answer["probabilities"]).items()
                },
                "legend": {
                    str(k): str(v)
                    for k, v in dict(answer["legend"]).items()
                },
            }

        evidence["dimensions"][dim["id"]] = dim_out

    nouls = backend_result.get("nouls", {})
    for constraint in state["constraints"]:
        if constraint["severity"] != "hard":
            continue

        constraint_out = {
            "text": constraint["text"],
            "threshold": constraint_warning_threshold,
            "options": {},
        }

        for option in state["options"]:
            qid = (
                f"violation__{constraint['id']}__{option['id']}"
            )

            try:
                probability = _probability(
                    float(nouls[qid]),
                    qid,
                )
            except KeyError as exc:
                raise ProtocolError(
                    f"Backend result is missing hard-constraint answer: {qid}"
                ) from exc

            option_status = (
                "violation"
                if probability >= constraint_warning_threshold
                else "pass"
            )

            constraint_out["options"][option["id"]] = {
                "violation_probability": probability,
                "status": option_status,
            }

            if option_status == "violation":
                evidence["warnings"].append(
                    f"Option {option['id']} may violate hard constraint "
                    f"{constraint['id']}."
                )

        evidence["constraint_checks"][constraint["id"]] = constraint_out

    if evidence["missing_alternative"]["status"] == "expand_candidates":
        evidence["warnings"].append(
            "The candidate set may omit a materially distinct alternative; "
            "ask the parent agent to expand the options before settling."
        )

    return evidence


def build_degraded_evidence(
    state: dict[str, Any],
    *,
    backend_name: str,
    reason: str,
    constraint_warning_threshold: float,
    missing_alternative_threshold: float,
    low_confidence_threshold: float,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "status": "degraded",
        "decision_id": state["decision"]["id"],
        "state_hash": state_hash(state),
        "backend": {
            "name": backend_name,
            "model": None,
        },
        "policy": {
            "constraint_warning_threshold": constraint_warning_threshold,
            "missing_alternative_threshold": missing_alternative_threshold,
            "low_confidence_threshold": low_confidence_threshold,
        },
        "overall_choice": None,
        "dimensions": {},
        "constraint_checks": {},
        "missing_alternative": None,
        "warnings": [
            f"Jev evidence was not produced: {reason}"
        ],
        "fallback": {
            "action": "agent_reasoning",
            "reason": (
                "Continue the planning flow using normal agent reasoning, "
                "clearly state that Jev evidence is unavailable, and let the "
                "user make the final decision."
            ),
        },
    }


def evaluate_with_backend(
    state: dict[str, Any],
    plan: dict[str, Any],
    backend: DecisionBackend,
    *,
    constraint_warning_threshold: float = DEFAULT_CONSTRAINT_WARNING_THRESHOLD,
    missing_alternative_threshold: float = DEFAULT_MISSING_ALTERNATIVE_THRESHOLD,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    strict_backend: bool = False,
) -> dict[str, Any]:
    payload = build_dry_run_payload(state, plan)

    try:
        result = backend.evaluate(
            state=payload["state"],
            questions=payload["questions"],
        )
    except BackendError as exc:
        if strict_backend:
            raise
        return build_degraded_evidence(
            state,
            backend_name=getattr(backend, "name", "unknown"),
            reason=str(exc),
            constraint_warning_threshold=constraint_warning_threshold,
            missing_alternative_threshold=missing_alternative_threshold,
            low_confidence_threshold=low_confidence_threshold,
        )

    return build_decision_evidence(
        state,
        plan,
        result,
        constraint_warning_threshold=constraint_warning_threshold,
        missing_alternative_threshold=missing_alternative_threshold,
        low_confidence_threshold=low_confidence_threshold,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a grill decision with Jev"
    )
    parser.add_argument(
        "--state",
        required=True,
        help="Path to DecisionState JSON",
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Path to EvaluationPlan JSON",
    )
    parser.add_argument(
        "--output",
        help="Write DecisionEvidence JSON to this path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the generated Jev payload without calling the API",
    )
    parser.add_argument(
        "--backend",
        default="typesafe",
        choices=["typesafe"],
        help="Decision backend adapter",
    )
    parser.add_argument(
        "--constraint-warning-threshold",
        type=float,
        default=DEFAULT_CONSTRAINT_WARNING_THRESHOLD,
    )
    parser.add_argument(
        "--missing-alternative-threshold",
        type=float,
        default=DEFAULT_MISSING_ALTERNATIVE_THRESHOLD,
    )
    parser.add_argument(
        "--low-confidence-threshold",
        type=float,
        default=DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    )
    parser.add_argument(
        "--strict-backend",
        action="store_true",
        help="Fail instead of returning degraded evidence when Jev is unavailable",
    )
    args = parser.parse_args(argv)

    try:
        state = load_json(args.state)
        plan = load_json(args.plan)
        validate_decision_state(state)
        validate_evaluation_plan(plan, state)

        if args.dry_run:
            result = build_dry_run_payload(state, plan)
        else:
            backend = make_backend(args.backend)
            result = evaluate_with_backend(
                state,
                plan,
                backend,
                constraint_warning_threshold=args.constraint_warning_threshold,
                missing_alternative_threshold=args.missing_alternative_threshold,
                low_confidence_threshold=args.low_confidence_threshold,
                strict_backend=args.strict_backend,
            )
    except ProtocolError as exc:
        print(f"grill-jev: {exc}", file=sys.stderr)
        return 2
    except BackendError as exc:
        print(f"grill-jev: backend failed: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(
            rendered + "\n",
            encoding="utf-8",
        )
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
