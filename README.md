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
        "A": {"score": 3.7, "confidence": 0.76},
        "B": {"score": 3.0, "confidence": 0.70},
        "C": {"score": 4.5, "confidence": 0.84}
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
