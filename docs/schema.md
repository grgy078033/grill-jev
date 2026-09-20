# Schema reference

`grill-jev` uses two input documents: `DecisionState` and `EvaluationPlan`.

The machine-readable JSON Schemas are available in:

- `skills/grill-jev/schemas/decision-state.schema.json`
- `skills/grill-jev/schemas/evaluation-plan.schema.json`
- `skills/grill-jev/schemas/decision-evidence.schema.json`

## DecisionState

| Field | Type | Required | Description | Example |
|---|---|---:|---|---|
| `schema_version` | string | yes | Protocol version. | `"0.1"` |
| `decision.id` | string | yes | Stable ID for the current decision. | `"delivery-model"` |
| `decision.question` | string | yes | The question being decided. | `"How should delivery work?"` |
| `objective.primary` | string | yes | Main objective the decision should support. | `"Keep play relaxed while preserving progression."` |
| `goals` | array | yes | Desired outcomes. Each item has `id`, `text`, and `source`. | `{"id":"low-friction","text":"Avoid busywork","source":"user"}` |
| `constraints` | array | yes | Limits. Each item has `id`, `text`, `severity`, and `source`. | `{"id":"offline","text":"Must work offline","severity":"hard","source":"user"}` |
| `settled_decisions` | array | yes | Previously settled decisions that materially affect this one. | `{"id":"staff","text":"Staff can be hired","source":"CONTEXT.md"}` |
| `facts` | array | yes | Verified facts relevant to the decision. | `{"id":"platform","text":"Desktop only","source":"codebase"}` |
| `options` | array | yes | Two or more candidate options. Each item has `id` and `text`. | `{"id":"B","text":"NPC staff deliver orders"}` |
| `unknowns` | array[string] | yes | Important uncertainties that should remain visible. | `["Pathfinding cost is not measured"]` |

### Constraint severity

- `hard`: checked independently with a Jev Noul question. A likely violation is surfaced as a warning and is **not automatically removed**.
- `soft`: may be represented as an evaluation dimension instead of an automatic constraint check.

## EvaluationPlan

| Field | Type | Required | Description | Example |
|---|---|---:|---|---|
| `schema_version` | string | yes | Protocol version. | `"0.1"` |
| `decision_id` | string | yes | Must match `DecisionState.decision.id`. | `"delivery-model"` |
| `dimensions` | array | yes | One or more dimensions used to compare options. | — |
| `dimensions[].id` | string | yes | Stable dimension ID. | `"player-friction"` |
| `dimensions[].label` | string | yes | Human-readable label. | `"Player friction"` |
| `dimensions[].instruction` | string | yes | What Jev should assess. | `"How well does this minimize repetitive work?"` |
| `dimensions[].basis` | array[string] | yes | References to state fields that justify the dimension. | `["goal:low-friction"]` |
| `dimensions[].rubric` | array[string] | yes | Ordered Score levels, 2–10 items. | `["Very poor","Poor","Mixed","Good","Excellent"]` |

Valid `basis` references are:

- `objective:primary`
- `goal:<id>`
- `constraint:<id>`
- `settled:<id>`
- `fact:<id>`

### Native Score semantics

Each dimension's `rubric` maps directly to TypeSafe `Score.criteria`. Following the [official Score contract](https://docs.typesafe.ai/primitives/score), its 2–10 ordered levels are numbered from 0 to N−1. The returned `score` is the probability-weighted mean of those indices, not a fixed 0–4 or percentage score. Use concrete descriptions for a single dimension, and document its direction in the label/instruction/rubric. This protocol has no separate scale or direction fields; agents must read the rubric, not invent new JSON properties. See [evaluation-plan guidance](../skills/grill-jev/references/evaluation-plan.md).

## DecisionEvidence

The output contains:

- `status`: `ok`, `low_confidence`, or `degraded`;
- `overall_choice`: Choice result and probabilities;
- `dimensions`: per-option Score results;
- `constraint_checks`: pass/violation signals for hard constraints;
- `missing_alternative`: whether the candidate set should be expanded;
- `warnings`: human-readable warnings;
- `fallback`: instructions for the parent agent when Jev evidence is unavailable or weak.
