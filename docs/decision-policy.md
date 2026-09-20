# Decision policy

This document defines how `grill-jev` turns Jev probabilities into workflow signals.

The thresholds below are **application policy**, not universal truths about Jev. They are configurable from the CLI.

## Hard-constraint checks

Hard constraints are written as short natural-language statements in `DecisionState.constraints`.

Example:

```json
{
  "id": "offline",
  "text": "The feature must work without a network connection.",
  "severity": "hard",
  "source": "user"
}
```

For every hard constraint and every option, `grill-jev` asks a Noul question:

> Does candidate X violate this hard constraint?

Default policy:

- violation probability **< 0.75** → `pass`
- violation probability **>= 0.75** → `violation`

A `violation` result is a **warning**, not an automatic filter. The option remains visible so the parent agent can explain the trade-off and the user can decide.

Override:

```bash
--constraint-warning-threshold 0.85
```

## Missing-alternative check

`grill-jev` asks one Noul question about the candidate set:

> Do the supplied options omit a materially distinct, viable alternative strongly implied by the state?

Default policy:

- probability **< 0.65** → `complete_enough`
- probability **>= 0.65** → `expand_candidates`

When `expand_candidates` is returned, Jev does **not** invent the missing option. The generative parent agent should brainstorm one or more additional candidates, then run `grill-jev` again.

Override:

```bash
--missing-alternative-threshold 0.70
```

### Expected examples

**Correct: complete enough**

Question: choose local persistence for a small offline desktop tool.

Options: JSON, SQLite, embedded key-value store.

State does not imply another materially different requirement.

Expected signal: low missing-alternative probability.

**Correct: expand candidates**

Question: how should deliveries work?

Options: player always delivers, employee always delivers.

State says the game should begin hands-on but later reward automation.

A hybrid progression option is materially distinct and strongly implied.

Expected signal: elevated missing-alternative probability.

**Do not overreact**

If Jev flags a missing alternative only because it can imagine a niche variation with no support in goals, constraints, or settled decisions, the parent agent should not automatically add it. The signal means "reconsider coverage", not "Jev discovered the correct fourth answer".

## Low confidence

Choice and Score responses include confidence. Noul is handled as a probability signal.

Default overall Choice confidence policy:

- confidence **>= 0.55** → normal evidence
- confidence **< 0.55** → top-level `status: low_confidence`

Low confidence does not discard the Jev result. It tells the parent agent to treat Jev as weak evidence and continue with normal reasoning.

Override:

```bash
--low-confidence-threshold 0.60
```

## Backend failure

Missing API key, timeout, SDK failure, or service errors produce:

```json
{
  "status": "degraded",
  "fallback": {
    "action": "agent_reasoning"
  }
}
```

By default the CLI exits successfully with this structured degraded result so an upstream planning workflow can continue.

Use `--strict-backend` when backend failure should instead stop the command with a non-zero exit code.
