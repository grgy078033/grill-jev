# Compatibility

## TypeSafe Python SDK

The repository pins:

```text
typesafe-sdk==0.6.0
```

This is the published stable SDK version used as the compatibility baseline when this document was written.

The provider-specific code is isolated in:

```text
skills/grill-jev/scripts/backends.py
```

so future SDK or provider changes do not need to alter the DecisionState / EvaluationPlan protocol.

## Jev model

The TypeSafe Python SDK defaults to the model alias:

```text
jev-latest
```

`grill-jev` currently targets that alias rather than hard-coding a concrete Jev server version. The alias may move as TypeSafe updates its service, so production users should keep live evals if model stability matters.

## Python

`typesafe-sdk 0.6.0` requires Python 3.10 or newer.

## Failure behavior

Backend/API failures return structured degraded evidence by default. Use `--strict-backend` to opt into fail-fast behavior.
