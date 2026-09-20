# Integrations

## Matt Pocock `grill-with-docs`

Recommended sequence:

```text
grilling frontier question
  → candidate options exist
  → construct DecisionState
  → construct EvaluationPlan
  → run grill-jev
  → present evidence + agent recommendation
  → user settles decision
  → return to grill-with-docs
  → CONTEXT.md / ADR handling remains upstream
```

`grill-jev` must not fork or duplicate the `grilling` primitive.

## Custom planning workflows

Any workflow can integrate if it can provide:

- one current decision question;
- two or more candidate options;
- minimum sufficient state;
- an evaluation plan with traceable dimensions.

## Harness portability

The protocol intentionally avoids Pi-specific session APIs. Pi, Codex, Claude Code, or another compatible agent can build the JSON artifacts and call the same script.
