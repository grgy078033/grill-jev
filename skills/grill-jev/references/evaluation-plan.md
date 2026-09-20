# Evaluation Plan

The parent agent generates an `EvaluationPlan` before Jev is called. This makes evaluation dimensions visible and auditable.

## Dimension rule

Every dimension must cite one or more `basis` references such as:

- `goal:low-micromanagement`
- `constraint:small-team`
- `settled:staff-hiring`
- `fact:existing-save-format`

A dimension without a basis should be removed or explicitly justified by the user.

## Good dimensions

- "Player friction" because the user explicitly wants low micromanagement.
- "Implementation burden" because the team-size constraint is strict.
- "NPC-system synergy" because staff hiring is already a settled system.

## Bad dimensions

- "Elegance" with no definition.
- "Best architecture" with no decision boundary.
- A dimension chosen only because it makes the agent's preferred option look stronger.

## Score rubrics

Follow the official [TypeSafe Score specification](https://docs.typesafe.ai/primitives/score):

- Supply **2–10 ordered, distinctly described levels**, from the low end to the high end of **one dimension**. In this skill, `dimensions[].rubric` is passed to SDK `Score.criteria` unchanged.
- Levels are zero-indexed by their position. With N levels, the returned score ranges from **0 to N−1**: three levels mean 0–2; five mean 0–4; ten mean 0–9. TypeSafe does not prescribe a universal five-level or 0–100 scale.
- `score = sum(level_index * probability_of_level)`. It is a probability-weighted mean and can be fractional, not just the most likely level. For probabilities `[0.0, 0.57, 0.43]`, the score is `1.43` on a 0–2 scale.
- Describe concrete situations, not just numbers or generic labels such as "poor / good / excellent". Use only as many levels as you can distinguish meaningfully; do not add levels merely for apparent precision.
- State the direction explicitly. High severity can be bad; high maintainability can be good. "Higher is better" is a rubric choice, not an SDK rule.
- Read `probabilities`, `legend`, and `confidence` alongside `score`. Different distributions can have the same mean. [Confidence](https://docs.typesafe.ai/confidence) summarizes distribution concentration, not the probability that the answer is correct; do not invent a formula for it or derive it from the score alone.

Example four-level rubric for a single dimension, **retrieval convenience** (0–3, higher is more convenient):

```json
[
  "Finding a note requires browsing individual notes without search.",
  "Keyword search is available, but classification and filtering are manual.",
  "Keyword search and separate tag/date filters are available; combining them requires extra steps.",
  "Keyword, tag, and date conditions can be combined directly in one query."
]
```

Do not also put implementation cost or offline availability into these levels; those are separate dimensions or constraints. Use the same rubric for every candidate evaluated on a dimension.

Five-level rubrics in repository examples are example-specific choices, not a mandatory default. The skill currently accepts text descriptions for rubric levels; the official API also accepts structured descriptions, which this skill's input schema does not expose. Keep raw returned scores in their native scale in evidence and menus. Any separately requested rescaling must be clearly labeled as an application-derived value, not a native Jev score. Never add or average dimension scores to rank candidates unless an explicit aggregation policy was supplied.

## Hard constraints

Do not convert a hard constraint into a normal Score. Ask a Noul:

> Does option B violate the offline-only constraint?

This keeps a serious violation visible instead of averaging it with strengths elsewhere.

## Candidate coverage

Always ask whether the supplied options appear to omit a materially distinct viable alternative implied by the state. A high probability does not let Jev invent the alternative; it tells the generative parent agent to expand the candidate set and evaluate again.
