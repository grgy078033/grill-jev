# Compatibility

## TypeSafe Python SDK

The repository pins:

```text
typesafe-sdk==0.7.0
```

This is the SDK version used as the compatibility baseline. Offline tests exercise the real SDK request serialization and response parsing through a mock HTTP transport, including Choice, Score, Noul, and backend failures. Run them with `python evals/run_local.py`; no API key or network access is needed.

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

`typesafe-sdk 0.7.0` requires Python 3.10 or newer.

## Upgrade verification

The 0.7.0 upgrade also passed one authorized live System One request using a reduced synthetic product example (two options, one score dimension, and one hard constraint). All six Choice/Score/Noul questions returned usable decision evidence with `status: "ok"`; `jev-latest` resolved to `jev-1.13.0`. Automatic retries were disabled. This is a point-in-time connectivity and adapter check, not a guarantee of future service availability or model stability. CI remains offline and requires no secrets.

## Failure behavior

Backend/API failures return structured degraded evidence by default. Use `--strict-backend` to opt into fail-fast behavior.
