# Presentation Contract

This contract applies to Pi, Codex, Claude Code, and other hosts. It specifies the information the user must see, not a particular tool API or identical rendering. Never collapse the output into "Jev says B, so choose B."

## 1. Jev Evidence

Read the current `DecisionEvidence` before constructing a menu. Show a compact comparison in the conversation containing:

- every evaluated candidate, identified by its stable option ID;
- the overall Choice distribution and its confidence;
- relevant dimension scores, their scales/directions, and notable score uncertainty;
- hard-constraint violation probabilities and warnings;
- the missing-alternative probability and its policy signal.

Use the returned values, not invented numbers or a previous round's results. Choice probabilities are not success probabilities; Choice confidence is a different field. Display rounding is allowed, but do not replace a missing value with zero, recompute policy from rounded values, or invent an aggregate score. Use the actual rubric range: a five-level rubric uses 0–4, but other lengths are valid. Explain whether higher means better for each displayed dimension. A `pass` is a policy signal, not proof of feasibility.

If status is `low_confidence`, label the evidence as weak. If status is `degraded`, say "Jev unavailable" and present agent reasoning without fabricated probabilities or scores. A normal overall status does not mean every dimension has high confidence.

## 2. Agent Recommendation

Give the parent agent's reasoning separately, including whether it agrees with Jev. A recommendation marker in a menu is the agent's recommendation, not an additional Jev output.

When `missing_alternative.status` is `expand_candidates`, propose discussing additional candidates before settling. Any new candidate must say "not evaluated"; do not attach scores from another option. Jev identifies a coverage concern, not the missing solution itself.

## 3. User Decision: compact choices by default

If a native structured question tool is exposed and permitted in the current host/mode, use it for the final choice. Otherwise use the plain-text fallback below. Do not assume that a tool exists because a host has a particular name.

### Menu content

- Ask one current decision at a time, normally single-select for mutually exclusive candidates.
- Put the stable ID, short option name, and Jev Choice percentage in the **label/title** when they fit.
- Put the **same one or two decision-relevant dimensions**, in the same order, plus a concise hard-constraint warning in each option's **description**. Identify the metrics and scale; do not show unexplained numbers.
- Select those dimensions from the EvaluationPlan's goals and constraints, not to favor the agent's preferred option. Keep remaining dimensions and all constraint warnings in the preceding comparison; explicitly indicate that the menu is a summary if any are omitted.
- State the scale/direction and missing-alternative warning once in the question/context, or immediately before it if the host limits question length.
- Keep descriptions to one short line where possible. Narrow windows may still wrap or truncate; no fixed character count guarantees visibility.
- **Do not use long previews, expandable panels, hover text, or hidden lines as the only place containing decision-critical scores or warnings. Omit `preview` by default.** Optional detail views must not replace the visible comparison.
- Keep every evaluated candidate available, including low-probability or constraint-violating candidates. A warning does not authorize silently filtering an option.
- Let the user revise requirements, suggest another option, or defer. Use the host's built-in custom-answer facility if available; do not duplicate reserved "Other" / "Type something" entries. An explicit "Discuss alternatives" action is not an evaluated candidate and gets no Jev score.
- If option/field limits would hide candidates or warnings, use the full comparison plus plain-text ID selection instead of squeezing or silently dropping information.

### Example: visible option summaries

Illustrative values only; replace all numbers with the current evidence. These labels/descriptions are a content template, **not a tool invocation schema**. The example uses two five-level rubrics, both higher-is-better; "Less upkeep" is the inverse of maintenance burden.

```text
Question: Which direction do you prefer?
Context: Search / Less upkeep: 0–4, higher is better.
         Jev flags a possible missing alternative: 74%.

Label: A: Markdown | Jev 77%
Description: Search 1.56/4 | Less upkeep 2.96/4 | Offline violation 7%

Label: B: SQLite | Jev 23%
Description: Search 3.19/4 | Less upkeep 0.72/4 | Offline violation 4%

Label: C: Cloud | Jev 0%
Description: Search 3.41/4 | Less upkeep 3.78/4 | WARNING: offline violation 98%

Label: Discuss alternatives
Description: Explore an offline ready-made tool; not evaluated. No new API call yet.
```

The conversation before this menu must already distinguish Jev Evidence from Agent Recommendation and show confidence/uncertainty. Translate labels and descriptions into the user's language without changing option IDs or numeric meaning.

### Plain-text fallback

Show the same information in a compact table directly in the conversation, not a code preview:

| Option | Jev Choice | Search /4 | Less upkeep /4 | Offline violation |
|---|---:|---:|---:|---:|
| A: Markdown | 77% | 1.56 | 2.96 | 7% |
| B: SQLite | 23% | 3.19 | 0.72 | 4% |
| C: Cloud | 0% | 3.41 | 3.78 | 98% — warning |

Then ask: "Choose A/B/C, discuss another option, revise the requirements, or defer." Use the same scale, uncertainty, and coverage caveats as the interactive version. If the user reports truncation, shorten the menu or switch to this fallback; do not repeat a longer preview.

## 4. After the answer

Return the user's choice or requested revision to the upstream planner. Selecting, opening, or dismissing a menu is not authorization to implement a solution or spend more API credits. Dismissal is not acceptance of a default. Discuss a proposed new candidate before any new evaluation; respect the user's existing authorization scope, and ask before an additional API call when that scope does not cover it. Never automatically rerun just to improve confidence or get a preferred answer.

Probability is evidence, not authority. The user makes the final decision.
