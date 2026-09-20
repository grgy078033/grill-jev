#!/usr/bin/env python3
"""grill-jev v0.1 evaluator.

Validates a canonical DecisionState + EvaluationPlan, enforces a simple
recommendation firewall, then batches Choice / Score / Noul judgments through
TypeSafe Jev. Use --dry-run to inspect the generated question set offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


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


def enforce_recommendation_firewall(value: Any, path: str = "$", key: str | None = None) -> None:
    if key is not None:
        lowered = key.lower()
        if lowered in FORBIDDEN_KEY_FRAGMENTS or any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
            raise ProtocolError(f"Recommendation Firewall blocked field at {path}: {key}")

    if isinstance(value, dict):
        for k, v in value.items():
            enforce_recommendation_firewall(v, f"{path}.{k}", k)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            enforce_recommendation_firewall(item, f"{path}[{i}]", key)
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                raise ProtocolError(f"Recommendation Firewall blocked recommendation-like prose at {path}")


def validate_decision_state(state: dict[str, Any]) -> None:
    enforce_recommendation_firewall(state)
    allowed = {
        "schema_version", "decision", "objective", "goals", "constraints",
        "settled_decisions", "facts", "options", "unknowns"
    }
    required = set(allowed)
    _require(state, required, "DecisionState")
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

    def validate_sourced(items: Any, where: str, constraint: bool = False) -> None:
        if not isinstance(items, list):
            raise ProtocolError(f"{where} must be an array")
        seen: set[str] = set()
        required_fields = {"id", "text", "source"} | ({"severity"} if constraint else set())
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
                raise ProtocolError(f"{where}[{i}].severity must be hard or soft")

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
    if not isinstance(unknowns, list) or any(not isinstance(x, str) or not x.strip() for x in unknowns):
        raise ProtocolError("unknowns must be an array of non-empty strings")


def available_basis_refs(state: dict[str, Any]) -> set[str]:
    refs = set()
    refs.update(f"goal:{x['id']}" for x in state["goals"])
    refs.update(f"constraint:{x['id']}" for x in state["constraints"])
    refs.update(f"settled:{x['id']}" for x in state["settled_decisions"])
    refs.update(f"fact:{x['id']}" for x in state["facts"])
    refs.add("objective:primary")
    return refs


def validate_evaluation_plan(plan: dict[str, Any], state: dict[str, Any]) -> None:
    allowed = {"schema_version", "decision_id", "dimensions"}
    _require(plan, allowed, "EvaluationPlan")
    _reject_extra(plan, allowed, "EvaluationPlan")
    if plan["schema_version"] != "0.1":
        raise ProtocolError("EvaluationPlan.schema_version must be '0.1'")
    if plan["decision_id"] != state["decision"]["id"]:
        raise ProtocolError("EvaluationPlan.decision_id must match DecisionState.decision.id")
    dims = plan["dimensions"]
    if not isinstance(dims, list) or not dims:
        raise ProtocolError("EvaluationPlan.dimensions must contain at least one dimension")

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
            raise ProtocolError(f"{where}.basis must contain at least one reference")
        unknown_refs = [ref for ref in basis if ref not in valid_refs]
        if unknown_refs:
            raise ProtocolError(f"{where}.basis contains unknown refs: {unknown_refs}")
        rubric = dim["rubric"]
        if not isinstance(rubric, list) or not 2 <= len(rubric) <= 10:
            raise ProtocolError(f"{where}.rubric must contain 2-10 ordered levels")
        for j, level in enumerate(rubric):
            _nonempty_str(level, f"{where}.rubric[{j}]")


def state_hash(state: dict[str, Any]) -> str:
    canonical = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalized_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return the exact minimal structured state sent to Jev."""
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


def build_dry_run_payload(state: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    option_map = {o["id"]: o["text"] for o in state["options"]}
    questions: dict[str, Any] = {
        "overall_choice": {
            "type": "choice",
            "instructions": "Which candidate option best fits the stated objective, goals, constraints, settled decisions, facts, and known unknowns? Judge only the supplied state; do not infer an agent preference.",
            "criteria": option_map,
        },
        "candidate_coverage": {
            "type": "noul",
            "instructions": "Do the currently supplied candidate options omit a materially distinct, viable alternative that is strongly implied by the stated decision state?",
        },
    }

    for dim in plan["dimensions"]:
        for option in state["options"]:
            qid = f"score__{dim['id']}__{option['id']}"
            questions[qid] = {
                "type": "score",
                "instructions": f"{dim['instruction']} Evaluate candidate {option['id']}: {option['text']}",
                "criteria": dim["rubric"],
                "basis": dim["basis"],
            }

    for constraint in state["constraints"]:
        if constraint["severity"] != "hard":
            continue
        for option in state["options"]:
            qid = f"violation__{constraint['id']}__{option['id']}"
            questions[qid] = {
                "type": "noul",
                "instructions": f"Does candidate {option['id']} ({option['text']}) violate this hard constraint: {constraint['text']}?",
            }

    return {
        "state_hash": state_hash(state),
        "state": normalized_state(state),
        "questions": questions,
    }


def _jsonable_map(value: Any) -> dict[str, float]:
    if value is None:
        return {}
    return {str(k): float(v) for k, v in dict(value).items()}


def evaluate_live(state: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
    except ImportError as exc:
        raise ProtocolError(
            "Live evaluation requires the official TypeSafe Python SDK. Install it with: python -m pip install typesafe-sdk"
        ) from exc

    payload = build_dry_run_payload(state, plan)
    questions: dict[str, Any] = {}
    for qid, q in payload["questions"].items():
        if q["type"] == "choice":
            questions[qid] = Choice(instructions=q["instructions"], criteria=q["criteria"])
        elif q["type"] == "score":
            questions[qid] = Score(instructions=q["instructions"], criteria=q["criteria"])
        elif q["type"] == "noul":
            questions[qid] = Noul(instructions=q["instructions"])
        else:
            raise AssertionError(q["type"])

    with TypeSafeClient() as client:
        response = client.system_one(state=payload["state"], questions=questions)

    overall = response.choices["overall_choice"]
    evidence: dict[str, Any] = {
        "schema_version": "0.1",
        "decision_id": state["decision"]["id"],
        "state_hash": payload["state_hash"],
        "model": getattr(response, "model", None),
        "overall_choice": {
            "choice": str(overall.choice),
            "confidence": float(overall.confidence),
            "probabilities": _jsonable_map(overall.probabilities),
        },
        "dimensions": {},
        "constraints": {},
        "candidate_coverage": {
            "missing_material_option_probability": float(response.nouls["candidate_coverage"].noul)
        },
        "warnings": [],
    }

    for dim in plan["dimensions"]:
        dim_out: dict[str, Any] = {"label": dim["label"], "basis": dim["basis"], "options": {}}
        for option in state["options"]:
            answer = response.scores[f"score__{dim['id']}__{option['id']}"]
            dim_out["options"][option["id"]] = {
                "score": float(answer.score),
                "confidence": float(answer.confidence),
                "probabilities": _jsonable_map(answer.probabilities),
                "legend": {str(k): v for k, v in dict(answer.legend).items()},
            }
        evidence["dimensions"][dim["id"]] = dim_out

    for constraint in state["constraints"]:
        if constraint["severity"] != "hard":
            continue
        out = {"text": constraint["text"], "options": {}}
        for option in state["options"]:
            answer = response.nouls[f"violation__{constraint['id']}__{option['id']}"]
            out["options"][option["id"]] = float(answer.noul)
        evidence["constraints"][constraint["id"]] = out

    # Warnings are deliberately descriptive, not automatic policy decisions.
    coverage = evidence["candidate_coverage"]["missing_material_option_probability"]
    if coverage >= 0.5:
        evidence["warnings"].append(
            "Candidate coverage signal is elevated; consider asking the parent agent to expand the option set before settling the decision."
        )

    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a grill decision with Jev")
    parser.add_argument("--state", required=True, help="Path to DecisionState JSON")
    parser.add_argument("--plan", required=True, help="Path to EvaluationPlan JSON")
    parser.add_argument("--output", help="Write DecisionEvidence JSON to this path")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the generated Jev payload without calling the API")
    args = parser.parse_args(argv)

    try:
        state = load_json(args.state)
        plan = load_json(args.plan)
        validate_decision_state(state)
        validate_evaluation_plan(plan, state)
        result = build_dry_run_payload(state, plan) if args.dry_run else evaluate_live(state, plan)
    except ProtocolError as exc:
        print(f"grill-jev: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # SDK/network errors remain visible without pretending success.
        print(f"grill-jev: evaluation failed: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
