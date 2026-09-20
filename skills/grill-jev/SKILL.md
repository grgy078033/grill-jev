---
name: grill-jev
description: Evaluate candidate decisions with Jev during planning or grilling. Produces structured decision evidence without owning the interview, decision tree, or final choice.
---

# grill-jev

Use this skill when an agent-led planning workflow has reached a **real decision** with at least two viable candidate options and meaningful trade-offs.

Core rule:

> **Jev judges. The agent reasons. The user decides.**

## Boundary

This skill is a decision-evidence layer, not a grilling framework.

Do not use it to:

- create or manage a decision tree/frontier;
- choose the next interview question;
- replace `grill-with-docs`, `grilling`, `grill-me`, or another planner;
- write `CONTEXT.md`, ADRs, specs, or tickets;
- automatically accept the option with the highest Jev probability.

The upstream planner owns the interview. `grill-jev` receives one current decision and returns evidence.

## Workflow

1. Confirm this is a decision, not a factual question.
2. Form a canonical `DecisionState` using only minimum sufficient context.
3. Apply the State Firewall and Recommendation Firewall.
4. Build an `EvaluationPlan` whose dimensions are traceable to goals, constraints, or settled principles.
5. Validate both JSON documents against the protocol.
6. Run `scripts/grill_jev.py`.
7. Present Jev evidence separately from the parent agent's recommendation.
8. Ask the user to make the final decision.
9. Return control to the upstream planning workflow.

## State Firewall

Only include information that is materially relevant to the current decision:

- explicit user goals;
- explicit constraints;
- settled decisions;
- verified facts;
- current candidate options;
- known unknowns.

Do not send the full conversation, full source files, secrets, credentials, unrelated proprietary material, stale alternatives, or unverified speculation.

Read `references/state-firewall.md` before constructing state.

## Recommendation Firewall

Never place any parent-agent preference inside `DecisionState`, including fields or prose such as:

- `agent_recommendation`;
- `assistant_preference`;
- `preferred_option`;
- "I think option B is best";
- previous Jev results.

The script rejects common recommendation-leak fields recursively.

## Evaluation

Use Jev primitives by meaning:

- **Choice**: overall fit among the offered candidates.
- **Score**: degree along a concrete ordered rubric for one option and one evaluation dimension.
- **Noul**: crisp yes/no conditions such as hard-constraint violation or candidate-set incompleteness.

Do not invent a weighted aggregate score unless the user supplied the weights.

Read `references/evaluation-plan.md` for question design.

## Presentation

Keep these three layers visibly separate:

1. **Jev Evidence** — distributions, scores, constraint warnings, missing-option probability.
2. **Agent Recommendation** — the parent agent's own reasoning after seeing the evidence.
3. **User Decision** — the final choice, including the ability to choose another option.

Read `references/presentation.md` for the display contract.

## Command

Resolve `<skill-dir>` relative to this `SKILL.md`, not relative to the project working directory.

Dry-run first when developing a new integration:

```bash
python <skill-dir>/scripts/grill_jev.py \
  --state /path/to/decision-state.json \
  --plan /path/to/evaluation-plan.json \
  --dry-run
```

Live evaluation requires `typesafe-sdk` and `TYPESAFE_API_KEY`:

```bash
python <skill-dir>/scripts/grill_jev.py \
  --state /path/to/decision-state.json \
  --plan /path/to/evaluation-plan.json \
  --output /tmp/decision-evidence.json
```

## Integration notes

For `grill-with-docs`, call this skill **after** the current frontier question has candidate options but **before** the user settles the decision. After the user decides, return control to `grill-with-docs` so it can update domain documentation normally.

See `references/integrations.md`.
