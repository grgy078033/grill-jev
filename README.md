[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

# grill-jev

**Jev judges. The agent reasons. The user decides.**

`grill-jev` is a portable Agent Skill for evaluating candidate options during planning and grilling workflows.

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

- evaluates multiple candidate options;
- compares options across relevant dimensions;
- checks hard constraints;
- checks whether an important alternative may be missing;
- keeps Jev evidence separate from the agent's recommendation;
- works with `grill-with-docs` or custom planning skills.

It is designed for skills-compatible agents such as Pi, Codex, Claude Code, and similar harnesses.

## Installation

```bash
python -m pip install -r requirements.txt
export TYPESAFE_API_KEY='your-api-key'
```

The repository currently pins `typesafe-sdk==0.7.0` and targets TypeSafe's `jev-latest` model alias.

Preserve the repository layout when installing: `SKILL.md` references `../../docs/`. For Pi, place the repository under `~/.agents/skills/grill-jev/`; Pi discovers the nested `skills/grill-jev/SKILL.md` recursively.

### Windows PowerShell

If you already saved the key as a Windows user environment variable, load it into the current shell before starting Pi:

```powershell
$env:TYPESAFE_API_KEY = [Environment]::GetEnvironmentVariable('TYPESAFE_API_KEY', 'User')
# Check presence without printing the secret.
-not [string]::IsNullOrWhiteSpace($env:TYPESAFE_API_KEY)
pi
```

To save a new key without putting it in command history:

```powershell
$secret = Read-Host 'TYPESAFE_API_KEY' -AsSecureString
$value = [System.Net.NetworkCredential]::new('', $secret).Password
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', $value, 'User')
$env:TYPESAFE_API_KEY = $value
Remove-Variable value, secret
```

Windows user environment variables persist as plaintext; do not print or commit the key. An already running Pi process does not inherit later changes. `/reload` reloads resources, not the process environment: restart Pi from the shell above, or restart the entire terminal/IDE so a new shell inherits the saved key.

## Usage

Prepare:

- `DecisionState`: the current goal, constraints, settled decisions, facts, and candidate options;
- `EvaluationPlan`: the dimensions used to compare those options.

Examples are available in `examples/`.

Dry-run:

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/product/decision-state.json \
  --plan examples/product/evaluation-plan.json \
  --dry-run
```

Live evaluation:

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/product/decision-state.json \
  --plan examples/product/evaluation-plan.json
```

If Jev is unavailable, the default behavior returns `status: "degraded"` with an `agent_reasoning` fallback instead of breaking the planning flow.

## Agent interaction: Pi, Codex, Claude Code

Agents must read [SKILL.md](skills/grill-jev/SKILL.md) and follow the [presentation contract](skills/grill-jev/references/presentation.md). If your host does not discover the nested skill automatically, ask it to read that file by its full path; preserve the repository layout for relative references.

1. Show **Jev Evidence**, then **Agent Recommendation**, then request the **User Decision**.
2. Prefer the host's native structured question tool when it is exposed and allowed. Inspect its current schema; Pi's `ask_user_question` arguments are not a universal API.
3. Put the option ID/name and Choice probability in each label, with the same one or two scores and constraint warnings in each short description. **Omit long previews by default**; essential comparisons must not depend on hidden lines or expanding a panel.
4. State the scales/directions and missing-option warning once. Keep confidence, remaining dimensions, and all warnings in the preceding comparison. If choices or required information cannot fit, show a plain-text table and ask for an option ID; never silently remove a candidate.
5. Allow alternatives or deferral. Mark new proposals as **not evaluated**. Selecting an option is not permission to implement or automatically call Jev again.

Illustrative visible menu (not a host-specific tool payload):

```text
Search / Less upkeep: 0–4, higher is better. Possible missing option: 74%.
A: Markdown | Jev 77% — Search 1.56/4 | Less upkeep 2.96/4 | Offline violation 7%
B: SQLite   | Jev 23% — Search 3.19/4 | Less upkeep 0.72/4 | Offline violation 4%
C: Cloud    | Jev  0% — Search 3.41/4 | Less upkeep 3.78/4 | WARNING: offline violation 98%
Discuss alternatives — Not evaluated; no new API call yet.
```

These are illustrative values; agents must use current evidence, not copy these numbers. This is a portable content contract, not a guarantee of identical widgets or no truncation in every terminal. See [host integration guidance](skills/grill-jev/references/integrations.md).

### Official TypeSafe scoring

[Score](https://docs.typesafe.ai/primitives/score) uses **2–10 ordered, distinctly described levels** for one dimension. N levels produce a score from **0 to N−1**; five levels happen to mean 0–4. The score is the probability-weighted mean of the level indices, so it can be fractional. For example, `[0.0, 0.57, 0.43]` produces `1.43` on a three-level 0–2 scale.

Use only as many levels as can be described meaningfully. High scores are not inherently better: severity and maintainability have different directions. Show each dimension's native scale and direction; do not assume every score is out of 4 or silently convert it to a percentage. [Confidence](https://docs.typesafe.ai/confidence) describes the probability distribution's concentration, not correctness. Choice probability is not success probability, and Noul returns a yes/no probability rather than a rubric score. See [rubric design rules](skills/grill-jev/references/evaluation-plan.md).

## Example output

Simulated excerpt:

```json
{
  "status": "ok",
  "overall_choice": {
    "choice": "A",
    "confidence": 0.79,
    "probabilities": {"A": 0.58, "B": 0.11, "C": 0.31}
  },
  "dimensions": {
    "user-friction": {
      "options": {
        "A": {"score": 3.07, "confidence": 0.76},
        "B": {"score": 2.59, "confidence": 0.70},
        "C": {"score": 3.57, "confidence": 0.84}
      }
    }
  },
  "constraint_checks": {
    "offline": {
      "options": {
        "B": {
          "violation_probability": 0.94,
          "status": "violation"
        }
      }
    }
  },
  "missing_alternative": {
    "probability": 0.18,
    "status": "complete_enough"
  }
}
```

Full simulated output: `examples/product/example-output.json`.

## With grill-with-docs

```text
grill-with-docs
  → creates a question and candidate options
  → grill-jev evaluates the options
  → agent explains the results
  → user chooses
  → grill-with-docs continues
```

## Documentation

- [Schema reference](docs/schema.md)
- [Decision policy](docs/decision-policy.md)
- [grill-with-docs contract](docs/grill-with-docs-contract.md)
- [Compatibility](docs/compatibility.md)

## License

MIT
