# grill-jev

**Jev judges. The agent reasons. The user decides.**

`grill-jev` is a portable Agent Skill that adds a structured **decision-evidence layer** to planning and grilling workflows. It is designed to work across skills-compatible coding agents such as Pi, Codex, Claude Code, and similar harnesses.

Instead of becoming another interview framework, `grill-jev` evaluates a decision that an upstream planner has already formed:

```text
planning / grilling workflow
        ↓
question + candidate options
        ↓
     grill-jev
        ↓
state firewall
recommendation firewall
evaluation plan
        ↓
       Jev
 Choice + Score + Noul
        ↓
DecisionEvidence
        ↓
parent agent explains trade-offs
        ↓
user makes the final decision
```

## Why this is different from `jev-me`

`jev-me` is a Jev-enhanced grilling workflow: it owns the interview, design tree/frontier, question progression, and output artifact.

`grill-jev` deliberately lives one layer lower. It does **not**:

- run the interview;
- own a decision tree or frontier;
- decide what question comes next;
- write specs, ADRs, or tickets;
- automatically accept Jev's highest-probability answer.

It only turns a well-formed decision into auditable decision evidence. That makes it usable from `grill-with-docs`, `grill-me`, custom planning skills, or an ordinary agent session.

## Core ideas

### 1. Canonical `DecisionState`

The current decision is normalized into a small structured state containing goals, constraints, settled decisions, verified facts, candidate options, and known unknowns.

### 2. State Firewall

Do not send the full transcript or entire repository to Jev. Send the minimum sufficient state for the decision.

### 3. Recommendation Firewall

The parent agent's preference must not be included in the state sent to Jev. Jev should judge the decision state, not the parent's opinion about it.

### 4. Multi-dimensional evidence

`grill-jev` does not reduce everything to one fake 0–100 score. It returns:

- an overall Choice distribution;
- per-option Score judgments on explicit dimensions;
- Noul checks for hard-constraint violations;
- a Noul check for materially missing candidate options;
- uncertainty and provenance.

### 5. Human decision remains final

Jev output is evidence, not an instruction. The parent agent may reason differently, and the user decides.

## Quick start

1. Install the TypeSafe SDK and set your API key:

```bash
python -m pip install typesafe-sdk
export TYPESAFE_API_KEY='...'
```

2. Prepare a `DecisionState` and `EvaluationPlan` (examples are included).

3. Run:

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json
```

Use `--dry-run` to validate and inspect the Jev questions without making a network call:

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json \
  --dry-run
```

## Integration with `grill-with-docs`

Recommended flow:

```text
grill-with-docs
  → forms a frontier question and candidate options
  → grill-jev evaluates those options
  → agent explains evidence and gives its own recommendation
  → user settles the decision
  → grill-with-docs records vocabulary / ADRs as usual
  → to-spec
  → to-tickets
```

`grill-jev` never takes ownership of `CONTEXT.md` or ADRs.

## Repository layout

```text
grill-jev/
├── README.md
├── LICENSE
├── skills/grill-jev/
│   ├── SKILL.md
│   ├── references/
│   ├── schemas/
│   └── scripts/grill_jev.py
├── examples/
├── evals/
└── tests/
```

## Related projects

- TypeSafe / Jev SDK: https://github.com/typesafe-ai/typesafe-sdk-python
- Matt Pocock skills (`grill-with-docs`, `grilling`, `to-spec`, `to-tickets`): https://github.com/mattpocock/skills
- `jev-me` prior art: https://github.com/jon-devlapaz/jev-me

`grill-jev` is an independent project and is not presented as an official extension of those projects.

## Status

Early v0.1 implementation. The protocol and schemas are intentionally explicit so they can be evaluated and evolved without coupling the project to one agent harness.

## License

MIT
