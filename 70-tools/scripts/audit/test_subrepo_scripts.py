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
#
# 2026-06-05 re-baseline 7 → 8 (investigated, not blind-bumped). The subrepo set
# turned over since the 2026-05-27 baseline: most of the original 7 stale entries
# were superseded and several new 60-apps subrepos were vendored on 2026-06-03/04
# with upstreams that were never published. All 8 current stale URLs are
# confirmed 404 (defunct/unpublished upstreams of vendored app code), none
# internally fixable (would require pushing the external repos):
#   1. 50-infra/yata/yata-wasm/lance-fork → etzhayyimcojp/lancedb-wasm (404)
#   2. 60-apps/etzhayyim-project-har/.../svelte → etzhayyim/etzhayyim-har (404)
#   3. 60-apps/etzhayyim-project-watashi → etzhayyim/watashi (404)
#   4. 60-apps/etzhayyim-project-resources/...-i2zikw31 → etzhayyim/...-i2zikw31 (404)
#   5. 60-apps/etzhayyim-project-os → etzhayyim/etzhayyim-project-os (404)
#   6. 60-apps/etzhayyim-project-news → etzhayyimcojp/etzhayyim-apps-media (404)
#   7. 60-apps/etzhayyim-project-activity-monitor/...-xgng091s → etzhayyimcojp/...-xgng091s (404)
# 2026-06-08 main merge: stale upstream count dropped 8 → 7 after one vendored
# path was removed from the active tree. Keep the audit strict in both
# directions: a count change means the subrepo set changed and must be reviewed.
# 2026-07-19 ADR-2607193620: activity-monitor's unpublished/defunct vendored
# checkout residue was retired with exact EDN provenance, shrinking 7 → 6.
# 2026-07-20 ADR-2607200200: the os app and its stale .gitrepo marker moved to
# its private flat repository, shrinking the root-owned baseline 6 → 5.
# 2026-07-20 ADR-2607200800: intel and its stale .gitrepo marker moved to its
# private flat repository, shrinking the root-owned baseline 5 → 4.
EXPECTED_STALE_URLS = 4
# ESCAPE_SYMLINKS baseline dropped 18 → 0 (2026-05-31): the 18 escape
# symlinks were all the `CHARTER-RIDER.md → ../../CHARTER-RIDER.md`
# pattern inside the kotoba **git-subrepo** (1 root + 17 crates), a
# root-side charter-rider-applicator artifact that the script itself
# flags as a DEFECT (dangles when the subrepo is extracted standalone).
# kotoba was converted from git-subrepo → git-submodule (`.gitmodules`,
# url=github.com/etzhayyim/kotoba), so its tree is no longer vendored
# into this repo and `subrepo-symlink-health.sh` (which only scans
# `.gitrepo` subrepos) correctly finds 0. This is the resolved end-state,
# not a regression. Charter Rider application to kotoba's 17 crates is now
# decoupled from the symlink mechanism and tracked separately as the
# upstream Phase-1 deliverable D1 of ADR-2605262130 (apply Apache-2.0 +
# Charter Rider v2.0 in the kotoba repo via upstream PR per N5).
EXPECTED_ESCAPE_SYMLINKS = 0


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
        # stale URLs > 0, so strict mode MUST fail.
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

    def test_kotoba_charter_rider_escape_pattern_resolved(self):
        """The canonical iter-31 finding was the kotoba git-subrepo's
        `CHARTER-RIDER.md → ../../CHARTER-RIDER.md` escape symlinks (1 root
        + 17 crates). kotoba migrated git-subrepo → git-submodule (2026-05),
        so those symlinks are no longer vendored in this repo and the scan
        is expected to find NONE of the kotoba escape pattern.

        Charter Rider application to kotoba's crates is now the upstream
        Phase-1 deliverable D1 of ADR-2605262130 (not the symlink hack)."""
        _, out, _ = _run_script(SYMLINK_HEALTH)
        assert "kotoba" not in out, (
            "kotoba CHARTER-RIDER.md escape symlinks reappeared — kotoba "
            "should be a git-submodule (no vendored tree). If kotoba was "
            "re-vendored as a subrepo, re-evaluate the Charter Rider "
            "application strategy (ADR-2605262130 D1) before re-baselining.\n"
            f"stdout:\n{out}"
        )

    def test_strict_mode_clean_at_zero_findings(self):
        """With kotoba now a submodule, there are 0 escape symlinks, so
        strict mode is clean (exit 0). If new escape symlinks are added to
        a remaining `.gitrepo` subrepo, this flips to exit 1 — investigate
        and bump EXPECTED_ESCAPE_SYMLINKS before changing this assertion."""
        rc, _, _ = _run_script(SYMLINK_HEALTH, ["--strict"])
        assert rc == 0, (
            f"strict mode with {EXPECTED_ESCAPE_SYMLINKS} findings should "
            f"exit 0; got {rc} (new escape symlinks introduced?)"
        )

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
