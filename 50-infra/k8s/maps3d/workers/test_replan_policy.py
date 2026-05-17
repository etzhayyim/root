"""Unit tests for the bounded-retry replanner policy.

The policy lives inline in `langgraph_curator.replan` (a closure inside
`main()`). To keep the test surface narrow we re-derive the policy as a
free function here and assert it returns the same shape the worker
emits. Drift between the test policy and the worker would be caught by
the integration test (Layer 2) when a real reconstruction failure flows
through AgentGateway MCP — but having a local mirror keeps the policy invariants
auditable without standing up the cluster.
"""

from __future__ import annotations

import unittest


def policy(error_code: str, attempt: int) -> tuple[str, dict]:
    """Mirror of the closure inside `langgraph_curator.replan`. Update
    both whenever you change the policy — Layer 2 will catch drift."""
    if attempt < 2:
        if error_code in ("TIMEOUT", "DENSE_OOM"):
            return "retry", {"denseEnabled": False, "matcher": "exhaustive"}
        if error_code == "BUNDLE_DIVERGED":
            return "retry", {"denseEnabled": True, "matcher": "exhaustive"}
        if error_code == "TOO_FEW_MATCHES":
            return "requestMore", {"maxImages": 400, "minQuality": 0.4}
        # UNKNOWN / anything else
        return "retry", {"denseEnabled": True, "matcher": "exhaustive"}
    # attempt >= 2 — bounded fallback to OSM extrude.
    return "downgradeOsm", {}


class BoundedRetryPolicy(unittest.TestCase):
    def test_first_attempt_timeout_goes_sparse(self) -> None:
        action, hints = policy("TIMEOUT", attempt=1)
        self.assertEqual(action, "retry")
        self.assertFalse(hints["denseEnabled"])

    def test_first_attempt_dense_oom_goes_sparse(self) -> None:
        action, hints = policy("DENSE_OOM", attempt=1)
        self.assertEqual(action, "retry")
        self.assertFalse(hints["denseEnabled"])

    def test_first_attempt_bundle_diverged_retries_dense(self) -> None:
        # Bundle divergence is non-deterministic; re-run as-is.
        action, hints = policy("BUNDLE_DIVERGED", attempt=1)
        self.assertEqual(action, "retry")
        self.assertTrue(hints["denseEnabled"])

    def test_first_attempt_too_few_matches_requests_more(self) -> None:
        action, hints = policy("TOO_FEW_MATCHES", attempt=1)
        self.assertEqual(action, "requestMore")
        self.assertGreaterEqual(hints["maxImages"], 200)

    def test_first_attempt_unknown_retries_default(self) -> None:
        action, hints = policy("UNKNOWN", attempt=1)
        self.assertEqual(action, "retry")
        self.assertTrue(hints["denseEnabled"])

    def test_second_attempt_always_downgrades(self) -> None:
        for code in ("TIMEOUT", "DENSE_OOM", "BUNDLE_DIVERGED", "TOO_FEW_MATCHES", "UNKNOWN"):
            with self.subTest(code=code):
                action, _ = policy(code, attempt=2)
                self.assertEqual(action, "downgradeOsm")

    def test_third_attempt_still_downgrades_never_aborts(self) -> None:
        # Future-proof: even at attempt=3 the policy never returns
        # "abort" — that path is reserved for the BPMN curator-abort
        # branch (insufficient images), not the COLMAP failure branch.
        action, _ = policy("TIMEOUT", attempt=3)
        self.assertEqual(action, "downgradeOsm")


if __name__ == "__main__":
    unittest.main()
