"""Exercise the pinned SDK at the HTTP boundary, without a key or network."""

import json
import os
import unittest
from unittest.mock import patch

import httpx2
from typesafe_sdk import RetryPolicy, TypeSafeClient

from test_protocol import load_example, mod
from backends import TypeSafeJevBackend


class SDKCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.state, self.plan = load_example("product")
        self.payload = mod.build_dry_run_payload(self.state, self.plan)
        self.requests = []
        self.client = None
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {"TYPESAFE_API_KEY": "offline-test-key"}).start()

    def use_transport(self, handler):
        # Patch only construction: serialization, transport and response parsing
        # all run through the installed TypeSafe SDK.
        def make_client():
            self.client = TypeSafeClient(
                api_key="offline-test-key",
                model="jev-latest",
                base_url="https://offline.invalid",
                transport=httpx2.MockTransport(handler),
                retry=RetryPolicy(max_retries=0),
            )
            return self.client

        patch("typesafe_sdk.TypeSafeClient", side_effect=make_client).start()

    def success_response(self, request):
        body = json.loads(request.content)
        self.requests.append(body)
        self.assertEqual(request.method, "POST")
        self.assertEqual(body["state"], self.payload["state"])
        self.assertEqual(body["model"], "jev-latest")
        self.assertEqual(set(body["questions"]), set(self.payload["questions"]))
        answers = {}
        for qid, question in body["questions"].items():
            expected = self.payload["questions"][qid]
            self.assertEqual(
                question, {k: v for k, v in expected.items() if k != "basis"}
            )
            kind = question["type"]
            if kind == "choice":
                answers[qid] = {
                    "type": "choice", "choice": "A", "confidence": 0.8,
                    "probabilities": {"A": 0.6, "B": 0.1, "C": 0.3},
                }
            elif kind == "score":
                answers[qid] = {
                    "type": "score", "score": 3.5, "confidence": 0.9,
                    "probabilities": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.5, "4": 0.5},
                    "legend": {str(i): label for i, label in enumerate(question["criteria"])},
                }
            elif kind == "noul":
                answers[qid] = {"type": "noul", "noul": 0.1}
            else:
                self.fail(f"Unexpected question kind: {kind}")
        return httpx2.Response(200, json={
            "model": "jev-test", "usage": {"input_tokens": 100, "output_tokens": 20},
            "answers": answers,
        })

    def test_sdk_request_and_answer_normalization(self):
        self.use_transport(self.success_response)
        result = TypeSafeJevBackend().evaluate(
            state=self.payload["state"], questions=self.payload["questions"]
        )
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(result["backend"], "typesafe-jev")
        self.assertEqual(result["model"], "jev-test")
        self.assertEqual(result["choices"]["overall_choice"]["probabilities"]["A"], 0.6)
        self.assertEqual(result["nouls"]["candidate_coverage"], 0.1)
        self.assertEqual(len(result["scores"]), len(self.plan["dimensions"]) * len(self.state["options"]))
        for score in result["scores"].values():
            self.assertEqual(score["score"], 3.5)
            self.assertEqual(score["confidence"], 0.9)
            self.assertEqual(set(score["legend"]), {"0", "1", "2", "3", "4"})
            self.assertEqual(score["probabilities"]["4"], 0.5)
        json.dumps(result)  # Normalized evidence remains JSON-serializable.
        self.assertTrue(self.client._http_client.is_closed)

    def test_sdk_answers_build_complete_decision_evidence(self):
        self.use_transport(self.success_response)
        evidence = mod.evaluate_with_backend(
            self.state, self.plan, TypeSafeJevBackend(), strict_backend=True
        )
        self.assertEqual(evidence["status"], "ok")
        self.assertEqual(evidence["overall_choice"]["choice"], "A")
        self.assertEqual(set(evidence["dimensions"]), {d["id"] for d in self.plan["dimensions"]})
        self.assertEqual(evidence["constraint_checks"]["offline"]["options"]["B"]["status"], "pass")
        self.assertEqual(evidence["missing_alternative"]["status"], "complete_enough")
        self.assertEqual(len(self.requests), 1)

    def test_sdk_http_failure_degrades(self):
        self.use_transport(lambda request: httpx2.Response(503, json={"detail": "offline test outage"}))
        evidence = mod.evaluate_with_backend(self.state, self.plan, TypeSafeJevBackend())
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(evidence["fallback"]["action"], "agent_reasoning")
        self.assertTrue(self.client._http_client.is_closed)

    def test_sdk_invalid_response_is_backend_error_in_strict_mode(self):
        self.use_transport(lambda request: httpx2.Response(200, json={"answers": {}}))
        with self.assertRaises(mod.BackendError):
            mod.evaluate_with_backend(
                self.state, self.plan, TypeSafeJevBackend(), strict_backend=True
            )
        self.assertTrue(self.client._http_client.is_closed)

    def test_missing_key_never_constructs_client(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}), patch("typesafe_sdk.TypeSafeClient") as client:
            with self.assertRaisesRegex(mod.BackendError, "TYPESAFE_API_KEY is not set"):
                TypeSafeJevBackend().evaluate(
                    state=self.payload["state"], questions=self.payload["questions"]
                )
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
