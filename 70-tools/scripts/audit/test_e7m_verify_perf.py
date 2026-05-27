"""Tests for the e7m verify pre-commit hook (perf + structural).

The `e7m verify` hook runs on every commit, scanning 9 constitutional
hard-invariants. Pre-iter-5 it took ~121 s (pathlib.rglob over the
worktree). Iter-5/6/7 brought it to ~2.3 s via `git ls-files`. Iter-56
brought it to ~0.7 s via `concurrent.futures.ThreadPoolExecutor`.

This test suite locks in both wins so a future refactor can't
silently undo them — the e7m verify hook stays cheap on every commit.

Same shape as the iter-60 subrepo perf-budget tests:
- CORRECTNESS  — exit 0 + 9/9 invariants pass
- PERFORMANCE  — wall time within budget (generous headroom for CI jitter)
- STRUCTURAL   — required patterns in source body (ThreadPoolExecutor,
                  git-grep usage)
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
E7M_BIN = REPO_ROOT / "70-tools/e7m/.venv/bin/e7m"
E7M_COMMANDS = REPO_ROOT / "70-tools/e7m/src/e7m/commands.py"

# iter-56 baseline: ~0.71 s steady state on the dev box.
# Budget: 5 s with comfortable headroom for CI cold-start + jitter +
# slower hardware. A regression that removed the ThreadPoolExecutor
# parallelization would push past this (sequential = ~2.3 s on dev
# box, possibly 4-5x slower on smaller CI runners).
PERF_BUDGET_S = 5.0

# Constitutional invariants checked by verify (per ADR-2605192100 §1
# HARD_INVARIANTS). Locked-in so the count itself becomes a canary:
# adding a new invariant requires updating the test consciously.
EXPECTED_INVARIANT_COUNT = 9


def _run_verify() -> tuple[int, str, float]:
    """Run `e7m verify`, return (rc, stdout, elapsed_s)."""
    t0 = time.perf_counter()
    result = subprocess.run(
        [str(E7M_BIN), "verify"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    elapsed = time.perf_counter() - t0
    return result.returncode, result.stdout, elapsed


# ─── Skip-if-not-installed guard ───────────────────────────────────────


def _e7m_available() -> bool:
    return E7M_BIN.is_file() and E7M_BIN.stat().st_mode & 0o111 != 0


pytestmark = pytest.mark.skipif(
    not _e7m_available(),
    reason="e7m not installed (run `cd 70-tools/e7m && uv venv .venv && uv pip install -e .`)",
)


# ─── Correctness ───────────────────────────────────────────────────────


class TestVerifyCorrectness:
    def test_exit_zero(self):
        rc, _, _ = _run_verify()
        assert rc == 0, f"e7m verify should exit 0; got {rc}"

    def test_reports_all_invariants_pass(self):
        _, out, _ = _run_verify()
        # Final summary line: "N/M constitutional invariants verified".
        expected = f"{EXPECTED_INVARIANT_COUNT}/{EXPECTED_INVARIANT_COUNT} constitutional invariants verified"
        assert expected in out, (
            f"expected '{expected}' in output; got:\n{out}"
        )

    def test_constitutional_anchor_present(self):
        """The output cites the anchor ADR so an operator who hits a
        failure can trace it to the constitutional source."""
        _, out, _ = _run_verify()
        assert "ADR-2605192100" in out, (
            f"output missing constitutional anchor ADR-2605192100:\n{out}"
        )


# ─── Performance budget (iter-56 ThreadPoolExecutor) ──────────────────


class TestVerifyPerformance:
    def test_within_perf_budget(self):
        _, _, elapsed = _run_verify()
        assert elapsed < PERF_BUDGET_S, (
            f"perf regression: e7m verify took {elapsed:.2f} s "
            f"(budget {PERF_BUDGET_S} s). iter-56 baseline ~0.71 s steady. "
            f"Likely regression of ThreadPoolExecutor → sequential for-loop, "
            f"or of git ls-files → pathlib.rglob (iter-5/6/7)."
        )


# ─── Structural canaries (iter-56 ThreadPoolExecutor must stay) ───────


class TestVerifyStructural:
    """If the optimization patterns disappear from commands.py, perf
    tests would catch it too — but these tests fail with a clearer
    pointer to the exact missing pattern."""

    def test_uses_thread_pool_executor(self):
        body = E7M_COMMANDS.read_text()
        assert "ThreadPoolExecutor" in body, (
            "70-tools/e7m/src/e7m/commands.py lost the iter-56 "
            "ThreadPoolExecutor parallelization. The 9 checks are "
            "I/O-bound (git grep subprocess) and overlap well in a "
            "thread pool — sequential for-loop adds ~1.6 s per commit."
        )

    def test_verify_returns_pool_map_ordered(self):
        """iter-56 used `pool.map(...)` which preserves submit order.
        If a future refactor switches to as_completed() the report
        layout would change unpredictably for the operator."""
        body = E7M_COMMANDS.read_text()
        assert "pool.map" in body, (
            "iter-56 pool.map was changed; the report's check ordering "
            "is unstable. Either restore pool.map or update operator "
            "expectations + this test."
        )

    def test_uses_git_grep_not_pathlib_walk(self):
        """iter-5/6/7 swapped pathlib.rglob for git ls-files / git grep
        in the hot paths."""
        body = E7M_COMMANDS.read_text()
        # The actual scan helpers use subprocess + git grep / git ls-files.
        assert "git" in body and ("grep" in body or "ls-files" in body), (
            "70-tools/e7m/src/e7m/commands.py lost the iter-5/6/7 "
            "git-based scan patterns. pathlib.rglob over the worktree "
            "was 121 s pre-fix."
        )
