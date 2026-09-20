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
7. Present a compact comparison of Jev evidence separately from the parent agent's recommendation.
8. Ask the user to decide using concise, scored options in an available native question tool; use a plain-text comparison and ID selection when that tool is unavailable or too restrictive.
9. Return control to the upstream planning workflow.

See `../../docs/schema.md` for the input/output field contract.

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
- **Score**: degree along a concrete ordered rubric for one option and one evaluation dimension. Follow [TypeSafe's official Score contract](https://docs.typesafe.ai/primitives/score): 2–10 distinct levels indexed from 0, so N levels yield a 0–(N−1) score. The score is the probability-weighted mean of those indices; high does not inherently mean good. Five levels / 0–4 is an example, not a required scale.
- **Noul**: crisp yes/no conditions such as hard-constraint violation or candidate-set incompleteness.

Hard-constraint checks are policy signals, not automatic filters. A likely violation must remain visible to the user.

If the missing-alternative signal crosses the configured threshold, ask the generative parent agent to propose additional candidates for discussion. Jev does not invent the missing option. Label new candidates as not evaluated, and only evaluate again within the user's API-call authorization; a coverage warning or menu selection does not itself authorize another call.

Do not invent a weighted aggregate score unless the user supplied the weights.

Read:

- `references/evaluation-plan.md` for question design;
- `../../docs/decision-policy.md` for thresholds and workflow behavior.

## Fallback behavior

If Jev is unavailable because the API key is missing, the request times out, or the backend fails, the default CLI behavior returns structured evidence with:

```json
{
  "status": "degraded",
  "fallback": {"action": "agent_reasoning"}
}
```

Continue the planning workflow using normal agent reasoning, clearly say that Jev evidence is unavailable, and do not invent Jev probabilities.

If `status` is `low_confidence`, show the available Jev evidence but treat it as weak.

Use `--strict-backend` only when backend failure should stop the workflow.

## Presentation

Keep these three layers visibly separate:

1. **Jev Evidence** — distributions, scores, constraint warnings, missing-option probability.
2. **Agent Recommendation** — the parent agent's own reasoning after seeing the evidence.
3. **User Decision** — the final choice, including the ability to choose another option.

Read `references/presentation.md` before presenting results or asking for a choice. It is the normative cross-agent display contract:

- Show the comparison, confidence/uncertainty, and missing-alternative signal in the conversation first.
- In a structured question, put each option's stable ID, short name, and Jev Choice percentage in its label when space permits. Put the same one or two relevant scores and a concise constraint warning in each description.
- Keep these summaries directly visible. Omit `preview` by default; do not hide essential scores or warnings in long previews or expandable panels.
- Explain the rubric's actual scale and direction. A five-level rubric is 0–4; higher is better only when the rubric says so. Choice probability is not success probability.
- Preserve all candidates and expose all constraint warnings in the preceding comparison. If the tool cannot fit the choices or required information, use a compact plain-text table and ask for an option ID instead.
- Use only tools actually exposed and permitted by the host. Adapt to their schemas; do not assume Codex or Claude Code accepts Pi's `ask_user_question` arguments.
- When Jev is unavailable, show no invented scores. Keep unevaluated proposals separate from scored candidates.
- Let the user propose an alternative, revise, or defer. Selecting a menu option does not authorize implementation or automatic reevaluation.

## Command

Resolve `<skill-dir>` relative to this `SKILL.md`, not relative to the project working directory.

Dry-run first when developing a new integration:

```bash
python <skill-dir>/scripts/grill_jev.py \
  --state /path/to/decision-state.json \
  --plan /path/to/evaluation-plan.json \
  --dry-run
```

Live evaluation requires the pinned `typesafe-sdk` dependency and `TYPESAFE_API_KEY`:

```bash
python <skill-dir>/scripts/grill_jev.py \
  --state /path/to/decision-state.json \
  --plan /path/to/evaluation-plan.json \
  --output /tmp/decision-evidence.json
```

See `../../docs/compatibility.md` for the current SDK/model compatibility target.

## Integration notes

For `grill-with-docs`, call this skill **after** the current frontier question has candidate options but **before** the user settles the decision. After the user decides, return control to `grill-with-docs` so it can update domain documentation normally.

See:

- `references/integrations.md`;
- `../../docs/grill-with-docs-contract.md`.
