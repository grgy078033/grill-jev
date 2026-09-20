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

A Score rubric must be ordered and concrete. Five levels are a good default:

1. strongly conflicts with the dimension;
2. mostly conflicts;
3. mixed / neutral;
4. mostly supports;
5. strongly supports.

Internally Jev scores these as indices 0–4, and the value can fall between levels.

## Hard constraints

Do not convert a hard constraint into a normal Score. Ask a Noul:

> Does option B violate the offline-only constraint?

This keeps a serious violation visible instead of averaging it with strengths elsewhere.

## Candidate coverage

Always ask whether the supplied options appear to omit a materially distinct viable alternative implied by the state. A high probability does not let Jev invent the alternative; it tells the generative parent agent to expand the candidate set and evaluate again.
