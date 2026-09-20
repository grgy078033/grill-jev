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
  → presents compact scored choices using an available question tool or plain-text fallback
  → asks the user to settle, revise, or defer the decision
  → records the settled decision using the normal grill-with-docs workflow
```

Follow the [presentation contract](../skills/grill-jev/references/presentation.md): keep essential scores and warnings visible in short option labels/descriptions, not hidden in long previews. Tool schemas differ across hosts. New candidates are not evaluated until a later authorized call; selecting a menu option is not permission to rerun Jev automatically.

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
