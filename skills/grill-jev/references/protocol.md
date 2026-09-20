# grill-jev Protocol v0.1

`grill-jev` accepts two artifacts:

1. `DecisionState`: what is true or currently intended about this decision.
2. `EvaluationPlan`: which dimensions should be judged and why they are legitimate.

It produces `DecisionEvidence`.

## Invariants

- The parent agent's recommendation is not part of Jev state.
- Every option has a stable ID.
- Every evaluation dimension declares its basis.
- Hard constraints are checked independently; they are not averaged away.
- Candidate coverage is checked independently.
- Jev evidence never becomes an automatic user decision.
- No weighted composite score is produced unless a future protocol explicitly receives user-defined weights.

## Primitive mapping

- Overall candidate fit → `Choice`
- Graded dimension → one `Score` per option/dimension
- Hard-constraint violation → one `Noul` per option/constraint
- Candidate-set incompleteness → `Noul`

All independent questions share the same normalized state and should be batched in one System One request.
