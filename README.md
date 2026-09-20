[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

# grill-jev

**Jev judges. The agent reasons. The user decides.**

`grill-jev` is a portable Agent Skill for evaluating candidate options during planning and grilling workflows.

It helps an agent turn a decision into structured evidence using Jev:

```text
question + candidate options
        ↓
     grill-jev
        ↓
       Jev
        ↓
Choice + Scores + constraint checks
        ↓
agent explains the trade-offs
        ↓
user makes the final decision
```

## What it does

`grill-jev`:

- evaluates multiple candidate options;
- compares them across relevant dimensions;
- checks hard constraints;
- checks whether the candidate set may be missing an important alternative;
- keeps Jev's judgment separate from the agent's recommendation;
- works with planning workflows such as `grill-with-docs` or custom Agent Skills.

It is designed to work across skills-compatible agents such as Pi, Codex, Claude Code, and similar harnesses.

## Installation

Install the TypeSafe SDK:

```bash
python -m pip install typesafe-sdk
```

Set your TypeSafe API key:

```bash
export TYPESAFE_API_KEY='your-api-key'
```

Then install or copy the `skills/grill-jev` directory into your agent's skills directory.

## Usage

Prepare:

- a `DecisionState` describing the current goal, constraints, settled decisions, and candidate options;
- an `EvaluationPlan` describing which dimensions should be evaluated.

Example files are included in `examples/`.

Run a dry-run first:

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json \
  --dry-run
```

Run a live Jev evaluation:

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json
```

## With grill-with-docs

A typical workflow is:

```text
grill-with-docs
  → creates a question and candidate options
  → grill-jev evaluates the options
  → agent explains the results
  → user chooses
  → grill-with-docs continues
```

## License

MIT
