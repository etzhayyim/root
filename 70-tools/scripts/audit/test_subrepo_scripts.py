"""Tests for the two subrepo audit bash scripts.

Locks in:
1. CORRECTNESS — finding counts + specific known paths
2. PERFORMANCE — wall time bounds (iter-57 optimized both scripts
   from ~20 s each to ~0.5 s; this test catches a regression if
   someone reintroduces `find` or serializes the `gh` calls)
3. STRUCTURAL — scripts retain the iter-57 patterns (git ls-files
   discovery + xargs -P parallel network calls)

The bash scripts themselves are too short for unit-style testing,
so these are end-to-end tests via subprocess invocation. Each test
runs in <1 s under the iter-57 optimization (vs ~20 s pre-fix).
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
UPSTREAM_HEALTH = REPO_ROOT / "70-tools/scripts/audit/subrepo-upstream-health.sh"
SYMLINK_HEALTH = REPO_ROOT / "70-tools/scripts/audit/subrepo-symlink-health.sh"

# Iter-57 baselines (with comfortable headroom — actual is ~0.5 s).
# A regression to `find` or serial `gh` would bump these past 5 s.
UPSTREAM_HEALTH_PERF_BUDGET_S = 5.0
SYMLINK_HEALTH_PERF_BUDGET_S = 2.0

# Iter-39/52 baselines (post-audit-closure). Any drift in either
# direction signals new work — investigate before bumping.
EXPECTED_STALE_URLS = 7
EXPECTED_ESCAPE_SYMLINKS = 18


def _run_script(path: Path, args: list[str] | None = None) -> tuple[int, str, float]:
    """Run a bash script, capture (returncode, stdout, elapsed_seconds)."""
    cmd = ["bash", str(path)]
    if args:
        cmd.extend(args)
    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=60)
    elapsed = time.perf_counter() - t0
    return result.returncode, result.stdout, elapsed


# ─── subrepo-upstream-health.sh ────────────────────────────────────────


class TestSubrepoUpstreamHealth:
    def test_script_exists_and_executable(self):
        assert UPSTREAM_HEALTH.is_file()
        # `bash` invocation doesn't require +x but having it set is conventional.
        assert UPSTREAM_HEALTH.stat().st_mode & 0o111

    def test_runs_clean_non_strict(self):
        rc, out, elapsed = _run_script(UPSTREAM_HEALTH)
        assert rc == 0, f"non-strict mode should exit 0; got {rc}\nstdout:\n{out}"

    def test_reports_expected_stale_count(self):
        _, out, _ = _run_script(UPSTREAM_HEALTH)
        # Final line format: "stale subrepo upstream URLs: N"
        assert f"stale subrepo upstream URLs: {EXPECTED_STALE_URLS}" in out, (
            f"expected {EXPECTED_STALE_URLS} stale URLs (ADR-2605211845 baseline); "
            f"got different count\nstdout:\n{out}"
        )

    def test_strict_mode_exits_1_on_findings(self):
        rc, _, _ = _run_script(UPSTREAM_HEALTH, ["--strict"])
        # 7 stale URLs > 0, so strict mode MUST fail.
        assert rc == 1, f"strict mode with {EXPECTED_STALE_URLS} findings should exit 1; got {rc}"

    def test_performance_budget(self):
        """Iter-57 optimized to ~0.5s via git ls-files + xargs -P10.
        Regression to find/serial-gh would push past 5s."""
        _, _, elapsed = _run_script(UPSTREAM_HEALTH)
        assert elapsed < UPSTREAM_HEALTH_PERF_BUDGET_S, (
            f"perf regression: subrepo-upstream-health took {elapsed:.2f} s "
            f"(budget {UPSTREAM_HEALTH_PERF_BUDGET_S} s; iter-57 baseline ~0.5 s). "
            f"Likely regression of `find` → walk or `gh` → serial."
        )

    def test_uses_git_ls_files_not_find(self):
        """Structural canary: iter-57 replaced `find` with `git ls-files`.
        If `find` reappears, perf budget will fail too — but this catches
        it earlier with a clear pointer to the optimization being lost."""
        body = UPSTREAM_HEALTH.read_text()
        assert "git ls-files" in body, (
            "subrepo-upstream-health.sh lost the iter-57 `git ls-files` "
            "optimization. Restore per the iter-57 commit message."
        )

    def test_uses_xargs_parallel_gh(self):
        """Structural canary: iter-57 added `xargs -P` for parallel `gh` calls."""
        body = UPSTREAM_HEALTH.read_text()
        assert "xargs -I" in body and "-P 10" in body, (
            "subrepo-upstream-health.sh lost the iter-57 `xargs -P10` "
            "parallel-gh optimization. Restore per the iter-57 commit message."
        )


# ─── subrepo-symlink-health.sh ─────────────────────────────────────────


class TestSubrepoSymlinkHealth:
    def test_script_exists_and_executable(self):
        assert SYMLINK_HEALTH.is_file()
        assert SYMLINK_HEALTH.stat().st_mode & 0o111

    def test_runs_clean_non_strict(self):
        rc, out, _ = _run_script(SYMLINK_HEALTH)
        assert rc == 0, f"non-strict mode should exit 0; got {rc}\nstdout:\n{out}"

    def test_reports_expected_escape_count(self):
        _, out, _ = _run_script(SYMLINK_HEALTH)
        assert f"escape-symlinks in subrepos: {EXPECTED_ESCAPE_SYMLINKS}" in out, (
            f"expected {EXPECTED_ESCAPE_SYMLINKS} escape symlinks (ADR-2605262130 baseline); "
            f"got different count\nstdout:\n{out}"
        )

    def test_detects_kotoba_charter_rider_pattern(self):
        """The canonical iter-31 finding is the kotoba subrepo's
        CHARTER-RIDER.md symlinks escaping to ../../CHARTER-RIDER.md."""
        _, out, _ = _run_script(SYMLINK_HEALTH)
        assert "kotoba" in out and "CHARTER-RIDER.md" in out, (
            "expected to find the kotoba CHARTER-RIDER.md escape pattern; "
            f"stdout:\n{out}"
        )

    def test_strict_mode_exits_1_on_findings(self):
        rc, _, _ = _run_script(SYMLINK_HEALTH, ["--strict"])
        assert rc == 1, f"strict mode with {EXPECTED_ESCAPE_SYMLINKS} findings should exit 1; got {rc}"

    def test_performance_budget(self):
        """Iter-57 replaced nested `find` walks with a single git ls-files -s scan.
        Regression would push past 2s."""
        _, _, elapsed = _run_script(SYMLINK_HEALTH)
        assert elapsed < SYMLINK_HEALTH_PERF_BUDGET_S, (
            f"perf regression: subrepo-symlink-health took {elapsed:.2f} s "
            f"(budget {SYMLINK_HEALTH_PERF_BUDGET_S} s; iter-57 baseline ~0.5 s). "
            f"Likely regression of nested `find` walks."
        )

    def test_uses_git_ls_files_dash_s(self):
        """Structural canary: iter-57 used `git ls-files -s` to find
        symlinks via mode 120000."""
        body = SYMLINK_HEALTH.read_text()
        assert "git ls-files -s" in body, (
            "subrepo-symlink-health.sh lost the iter-57 `git ls-files -s` "
            "symlink-discovery optimization."
        )
        assert "120000" in body, (
            "subrepo-symlink-health.sh lost the mode-120000 symlink filter."
        )


# ─── Cross-script invariant ────────────────────────────────────────────


class TestNeitherScriptUsesFind:
    """Both scripts were `find`-based pre-iter-57 and that was the main
    perf bottleneck. This test fails if either reverts."""

    def test_upstream_health_no_find(self):
        body = UPSTREAM_HEALTH.read_text()
        # Only flag lines that are uncommented script body (rough heuristic
        # via line-start) — bash comments and docstrings are OK.
        for i, line in enumerate(body.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            assert "find ." not in stripped, (
                f"subrepo-upstream-health.sh line {i} reintroduces `find .` — "
                f"iter-57 replaced this with git ls-files for perf.\nLine: {stripped}"
            )

    def test_symlink_health_no_find(self):
        body = SYMLINK_HEALTH.read_text()
        for i, line in enumerate(body.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            assert "find ." not in stripped, (
                f"subrepo-symlink-health.sh line {i} reintroduces `find .` — "
                f"iter-57 replaced this with git ls-files for perf.\nLine: {stripped}"
            )
