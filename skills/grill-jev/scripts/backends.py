"""Backend adapters for grill-jev.

The protocol layer talks only to the normalized backend shape returned here.
Provider-specific SDK objects stay isolated in this module.
"""

from __future__ import annotations

import os
from typing import Any, Protocol


class BackendError(RuntimeError):
    """Raised when a decision backend is unavailable or fails."""


class DecisionBackend(Protocol):
    name: str

    def evaluate(
        self,
        *,
        state: dict[str, Any],
        questions: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Return normalized Choice / Score / Noul answers."""


def _jsonable_map(value: Any) -> dict[str, float]:
    if value is None:
        return {}
    return {str(k): float(v) for k, v in dict(value).items()}


class TypeSafeJevBackend:
    """TypeSafe Jev adapter using the official Python SDK."""

    name = "typesafe-jev"

    def evaluate(
        self,
        *,
        state: dict[str, Any],
        questions: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        if not os.getenv("TYPESAFE_API_KEY"):
            raise BackendError("TYPESAFE_API_KEY is not set")

        try:
            from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
        except ImportError as exc:
            raise BackendError(
                "typesafe-sdk is not installed; install the pinned version from requirements.txt"
            ) from exc

        sdk_questions: dict[str, Any] = {}
        for qid, spec in questions.items():
            kind = spec["type"]
            if kind == "choice":
                sdk_questions[qid] = Choice(
                    instructions=spec["instructions"],
                    criteria=spec["criteria"],
                )
            elif kind == "score":
                sdk_questions[qid] = Score(
                    instructions=spec["instructions"],
                    criteria=spec["criteria"],
                )
            elif kind == "noul":
                sdk_questions[qid] = Noul(instructions=spec["instructions"])
            else:
                raise BackendError(f"Unsupported question type: {kind}")

        try:
            with TypeSafeClient() as client:
                response = client.system_one(state=state, questions=sdk_questions)
        except Exception as exc:
            raise BackendError(f"TypeSafe Jev request failed: {exc}") from exc

        return {
            "backend": self.name,
            "model": getattr(response, "model", None),
            "choices": {
                qid: {
                    "choice": str(answer.choice),
                    "confidence": float(answer.confidence),
                    "probabilities": _jsonable_map(answer.probabilities),
                }
                for qid, answer in response.choices.items()
            },
            "scores": {
                qid: {
                    "score": float(answer.score),
                    "confidence": float(answer.confidence),
                    "probabilities": _jsonable_map(answer.probabilities),
                    "legend": {str(k): v for k, v in dict(answer.legend).items()},
                }
                for qid, answer in response.scores.items()
            },
            "nouls": {
                qid: float(answer.noul)
                for qid, answer in response.nouls.items()
            },
        }


def make_backend(name: str) -> DecisionBackend:
    if name == "typesafe":
        return TypeSafeJevBackend()
    raise BackendError(f"Unknown backend: {name}")
