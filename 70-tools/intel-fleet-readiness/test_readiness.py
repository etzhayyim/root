#!/usr/bin/env python3
"""Tests for intel-fleet-readiness (readiness.py).

    python3 test_readiness.py

Validates the pre-flight checker: it parses both test-count formats, computes the
READY-PENDING-GATE verdict from (suite green AND tests>0 AND artifacts present), records
the blocking outward gate per actor, and — run for real over the cohort — finds every
actor deploy-ready (only the gate remains). This tool must NEVER claim a live deploy.
"""
from __future__ import annotations

import sys

import readiness as R


def test_count_parses_slash_format():
    assert R._count_tests("score.py: 26/26 tests passed") == 26
    assert R._count_tests("kanjō tests: 10/10 passed") == 10


def test_count_parses_unittest_format():
    assert R._count_tests("Ran 8 tests in 0.00s\nOK") == 8


def test_count_sums_multiple_suites():
    out = "a: 5/5 tests passed\nb: 7/7 passed\nRan 3 tests"
    assert R._count_tests(out) == 15


def test_verdict_requires_suite_tests_and_artifacts():
    # the verdict logic is (suite_ok AND n_tests>0 AND artifacts) — checked via a real run
    rows = R.run()
    for r in rows:
        ready = r["suite_ok"] and r["n_tests"] > 0 and bool(r["artifacts"])
        assert (r["verdict"] == "READY-PENDING-GATE") == ready


def test_every_actor_has_a_blocking_gate():
    # the whole point: readiness never implies "deployed" — every actor names its gate
    for r in R.run():
        assert r["gate"] and ("G" in r["gate"] or "Council" in r["gate"])


def test_cohort_is_deploy_ready_pending_gate():
    rows = R.run()
    not_ready = [r["actor"] for r in rows if r["verdict"] != "READY-PENDING-GATE"]
    assert not not_ready, f"not deploy-ready: {not_ready}"


def test_render_edn_and_md_never_claim_deployed():
    rows = R.run()
    edn, md = R.render_edn(rows), R.render_md(rows)
    assert "never deploys" in md.lower() and "outward-gated" in md.lower()
    assert ":fleet.ready/verdict" in edn and "Council" in edn


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"readiness.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
