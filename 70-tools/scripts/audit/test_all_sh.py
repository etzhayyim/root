"""End-to-end tests for the audit aggregator `all.sh`.

The individual audit scripts are well-tested (iters 46/53/60/61/66
→ 74 tests). The aggregator orchestration in `all.sh` is NOT tested
end-to-end: it could mis-roll up counts, emit wrong format, or
mis-handle `--strict` / `--test` / `--all` modes without any test
catching it. This suite closes that gap.

Tests use the real aggregator against the real repo state. The
baseline (25 documented-deferred findings) is locked-in — any
unintended drift in either direction fails fast.
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ALL_SH = REPO_ROOT / "70-tools/scripts/audit/all.sh"

# Rollup baseline. Was 25 at iter-52 closure (2026-05-27); re-baselined to 7
# on 2026-06-01 after a week of cleanup legitimately resolved the other
# findings (every non-subrepo audit now reports 0 — dependabot / sdk-exports /
# convention-drift / manifests / lexicons all clean). The remaining findings are
# entirely "stale subrepo upstream URLs" (the etzhayyim→etzhayyim 404 .gitrepo
# remotes), matching test_subrepo_scripts.EXPECTED_STALE_URLS. Fixing
# those will drop this to 0 and intentionally fail this test for a conscious
# re-baseline.
#
# 2026-06-05 re-baseline 7 → 8 (investigated, not blind-bumped): the subrepo set
# turned over since the 2026-05-27 baseline — several 2026-06-03/04 60-apps
# subrepos (har / watashi / intel / os / news / activity-monitor / etzhayyim-
# resources) were vendored with upstreams that were never published, so all 8
# current stale URLs are confirmed 404 defunct/unpublished upstreams of vendored
# app code (nothing internally fixable; restoring them would require pushing the
# external repos). Full list lives in test_subrepo_scripts.EXPECTED_STALE_URLS.
EXPECTED_TOTAL_FINDINGS = 8
PERF_BUDGET_S = 5.0      # iter-61 actual ~1.1 s; 4.5x headroom for CI
TEST_MODE_BUDGET_S = 20.0  # iter-66 pytest ~8 s; --all combined ~10 s; headroom


def _run_all_sh(args: list[str] | None = None) -> tuple[int, str, float]:
    cmd = ["bash", str(ALL_SH)]
    if args:
        cmd.extend(args)
    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=120)
    elapsed = time.perf_counter() - t0
    return result.returncode, result.stdout, elapsed


# ─── Module-scope fixtures memoize subprocess outputs ──────────────────
#
# Pre-fix: each test ran a fresh `bash all.sh` (~1-10 s each); 13 tests
# × avg 4 s = 52 s wall. By memoizing the 4 distinct invocations at
# module scope, the suite drops to ~10-12 s (the four invocations run
# once each, all assertions are pure dict-lookups).


@pytest.fixture(scope="module")
def default_run():
    return _run_all_sh()


@pytest.fixture(scope="module")
def strict_run():
    return _run_all_sh(["--strict"])


@pytest.fixture(scope="module")
def test_mode_run():
    return _run_all_sh(["--test"])


@pytest.fixture(scope="module")
def all_mode_run():
    return _run_all_sh(["--all"])


# ─── Default mode (aggregator only) ────────────────────────────────────


class TestDefaultMode:
    def test_exits_zero_non_strict(self, default_run):
        rc, _, _ = default_run
        assert rc == 0, "default mode (non-strict) should always exit 0"

    def test_emits_total_findings_line(self, default_run):
        _, out, _ = default_run
        m = re.search(r"total findings across all audits:\s*(\d+)", out)
        assert m, f"expected total-findings rollup line; got:\n{out}"

    def test_rollup_matches_baseline(self, default_run):
        _, out, _ = default_run
        m = re.search(r"total findings across all audits:\s*(\d+)", out)
        total = int(m.group(1))
        assert total == EXPECTED_TOTAL_FINDINGS, (
            f"baseline drift: expected {EXPECTED_TOTAL_FINDINGS}, got {total}.\n"
            f"Two batched-fix categories were closed iter-39 + iter-52; "
            f"remaining 25 are documented-deferred. Either new drift was "
            f"introduced (bump above 25) or a deferred item resolved "
            f"(drop below 25, in which case update the baseline)."
        )

    def test_runs_all_6_aggregator_scripts(self, default_run):
        _, out, _ = default_run
        for name in (
            "dependabot-defunct",
            "sdk-exports-dist",
            "subrepo-upstream-health",
            "subrepo-symlink-health",
            "sibling-convention-drift",
            "manifest-lexicon-drift",
        ):
            assert f"── {name} ──" in out, f"missing audit: {name}\n{out}"

    def test_performance_budget(self, default_run):
        _, _, elapsed = default_run
        assert elapsed < PERF_BUDGET_S, (
            f"perf regression: all.sh took {elapsed:.2f} s "
            f"(budget {PERF_BUDGET_S} s). iter-61 baseline ~1.1 s. "
            f"Likely regression in subrepo-* or sibling-convention-drift "
            f"perf optimizations."
        )


# ─── Strict mode ───────────────────────────────────────────────────────


class TestStrictMode:
    def test_exits_1_on_documented_deferred(self, strict_run):
        """The 25 documented-deferred findings (subrepos + symlinks)
        intentionally fail strict — `--strict` is the operator's
        pre-PR gate: 'I want to publish/merge with no debt.'"""
        rc, _, _ = strict_run
        assert rc == 1, (
            f"strict mode with {EXPECTED_TOTAL_FINDINGS} findings should exit 1; got {rc}"
        )


# ─── --test mode (pytest only) ─────────────────────────────────────────


class TestTestMode:
    def test_runs_pytest_only(self, test_mode_run):
        _, out, _ = test_mode_run
        assert "pytest" in out.lower(), f"--test mode should run pytest:\n{out}"

    def test_no_aggregator_summary_in_test_mode(self, test_mode_run):
        _, out, _ = test_mode_run
        # --test alone should NOT print the aggregator's "total findings" line.
        assert "total findings across all audits" not in out, (
            f"--test mode should not run aggregator:\n{out}"
        )

    def test_exits_zero_when_pytest_passes(self, test_mode_run):
        rc, _, _ = test_mode_run
        assert rc == 0, "all tests should pass; --test should exit 0"


# ─── --all mode ────────────────────────────────────────────────────────


class TestAllMode:
    def test_runs_both_pytest_and_aggregator(self, all_mode_run):
        _, out, _ = all_mode_run
        # Should contain both the pytest banner AND the aggregator total.
        assert "pytest" in out.lower(), f"--all should run pytest:\n{out}"
        assert "total findings across all audits" in out, (
            f"--all should run aggregator:\n{out}"
        )

    def test_within_combined_perf_budget(self, all_mode_run):
        _, _, elapsed = all_mode_run
        assert elapsed < TEST_MODE_BUDGET_S, (
            f"--all took {elapsed:.2f} s (budget {TEST_MODE_BUDGET_S} s)"
        )


# ─── Argument validation ───────────────────────────────────────────────


class TestArgValidation:
    def test_unknown_arg_exits_2(self):
        rc, _, _ = _run_all_sh(["--bogus"])
        assert rc == 2, f"unknown arg should exit 2; got {rc}"

    def test_unknown_arg_emits_error_message(self):
        cmd = ["bash", str(ALL_SH), "--bogus"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=10)
        # Error goes to stderr per the script's `echo ... >&2` pattern.
        assert "unknown arg" in (result.stderr + result.stdout).lower()
