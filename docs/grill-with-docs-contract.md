# grill-with-docs integration contract

`grill-jev` expects one already-formed decision from the upstream planning workflow.

## Handoff into grill-jev

The upstream agent should provide:

1. the current decision question;
2. two or more candidate options;
3. goals and constraints relevant to this decision;
4. settled decisions and verified facts that materially affect the choice;
5. known unknowns;
6. evaluation dimensions justified by the state.

Candidate options map directly to `DecisionState.options`:

```json
{
  "options": [
    {"id": "A", "text": "Player delivers orders"},
    {"id": "B", "text": "Employees deliver orders"},
    {"id": "C", "text": "Delivery resolves automatically"}
  ]
}
```

The option ID must remain stable for one evaluation round.

## Recommended flow

```text
grill-with-docs
  → identifies the current frontier question
  → generates candidate options
  → constructs DecisionState + EvaluationPlan
  → calls grill-jev
  → explains Jev evidence separately from its own recommendation
  → asks the user to settle the decision
  → records the settled decision using the normal grill-with-docs workflow
```

## Handoff back

`grill-jev` returns evidence only. It does not update `CONTEXT.md`, ADRs, specs, or tickets.

The upstream workflow owns those artifacts after the user settles the decision.

## Degraded mode

If `DecisionEvidence.status` is `degraded`:

- state clearly that Jev evidence was unavailable;
- continue with normal agent reasoning;
- do not invent Jev probabilities;
- still let the user make the final decision.

If status is `low_confidence`, show the available Jev evidence but treat it as weak.
