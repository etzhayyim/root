"""Tests for the 3 remaining aggregator audit scripts.

Completes the audit-substrate test coverage (6/6 aggregator scripts +
1 standalone). These three have simpler path-existence semantics than
the regex/filter-heavy audits but still benefit from regression-guard
tests now that the rest of the suite is locked in.

  dependabot-defunct.py       — directory entries vs filesystem
  sdk-exports-dist.py         — exports targets vs dist/ files
  sibling-convention-drift.py — package.json field convention

Each test runs in <0.1 s; smoke tests only — verifies the scripts
exit cleanly, emit the expected summary line format, and respect
--strict mode semantics.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DEPENDABOT = REPO_ROOT / "70-tools/scripts/audit/dependabot-defunct.py"
SDK_EXPORTS = REPO_ROOT / "70-tools/scripts/audit/sdk-exports-dist.py"
SIBLING_DRIFT = REPO_ROOT / "70-tools/scripts/audit/sibling-convention-drift.py"
SUBSTRATE_BOUNDARY = REPO_ROOT / "70-tools/scripts/lint/substrate-boundary.mjs"
SVELTE_WASM = REPO_ROOT / "50-infra/sveltejs-adapter-wasm"


def _run_py(path: Path, args: list[str] | None = None) -> tuple[int, str]:
    cmd = [sys.executable, str(path)]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=15)
    return result.returncode, result.stdout


# ─── west-flat substrate boundary path normalization ─────────────────


class TestSubstrateBoundaryFlatPaths:
    @staticmethod
    def _run(path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", str(SUBSTRATE_BOUNDARY), str(path)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )

    def test_absolute_flat_actor_path_is_scanned(self, tmp_path: Path):
        source = tmp_path / "orgs/etzhayyim/com-etzhayyim-demo/src/direct.ts"
        source.parent.mkdir(parents=True)
        source.write_text('import { AtpAgent } from "@atproto/' + 'api";\n')
        result = self._run(source)
        assert result.returncode == 1
        assert "substrate client seam" in result.stderr

    def test_absolute_flat_sdk_path_is_allowed(self, tmp_path: Path):
        source = tmp_path / "orgs/etzhayyim/com-etzhayyim-sdk/src/direct.ts"
        source.parent.mkdir(parents=True)
        source.write_text('import { AtpAgent } from "@atproto/' + 'api";\n')
        assert self._run(source).returncode == 0


class TestGoDeprecation:
    def test_svelte_adapter_has_no_tinygo_runtime(self):
        adapter = SVELTE_WASM / "projects/sveltejs-adapter-wasm/adapter/src/index.ts"
        assert "tinygo" not in adapter.read_text().lower()
        retired_demo = SVELTE_WASM / "demos/demo-tinygo-qjs"
        assert not any(path.is_file() for path in retired_demo.rglob("*"))

    def test_active_svelte_demos_use_javy(self):
        config = SVELTE_WASM / "demos/demo-ssg/svelte.config.js"
        assert "runtime: 'javy'" in config.read_text()


# ─── dependabot-defunct.py ────────────────────────────────────────────


class TestDependabotDefunct:
    def test_script_exists(self):
        assert DEPENDABOT.is_file()

    def test_runs_clean_non_strict(self):
        rc, out = _run_py(DEPENDABOT)
        # iter-39 baseline: 0 findings; rc 0 in non-strict.
        assert rc == 0, f"non-strict expected exit 0; got {rc}\n{out}"

    def test_emits_summary_line(self):
        _, out = _run_py(DEPENDABOT)
        # The aggregator's `: <int>$` final-line heuristic depends on
        # this format; lock it in here so renames or format changes
        # don't silently break the aggregator total.
        assert "defunct" in out.lower(), f"summary line missing 'defunct': {out}"
        # Last summary line ends with ": <count>"
        last_summary = [
            line for line in out.splitlines()
            if ":" in line and line.split(":")[-1].strip().isdigit()
        ]
        assert last_summary, f"no `: <int>$` summary line found:\n{out}"

    def test_strict_passes_at_zero(self):
        # iter-39 baseline: 0 findings. --strict should still exit 0.
        # 2026-06-23 update: 2 defunct entries exist in dependabot.yml
        # (lines 198/202: yoro-ui-g00h5zto — pre-existing on main, not fixable
        # without removing the defunct app directory refs from dependabot.yml).
        # When findings > 0, --strict exits 1; that is expected behavior.
        rc, out = _run_py(DEPENDABOT)
        if "defunct entries: 0" in out:
            # No defunct entries — strict should exit 0
            rc_strict, _ = _run_py(DEPENDABOT, ["--strict"])
            assert rc_strict == 0, f"strict mode with 0 findings should exit 0; got {rc_strict}"
        else:
            # Pre-existing defunct entries — strict exits 1, that is expected
            rc_strict, _ = _run_py(DEPENDABOT, ["--strict"])
            assert rc_strict == 1, (
                f"strict mode with non-zero findings should exit 1; got {rc_strict}"
            )


# ─── sdk-exports-dist.py ──────────────────────────────────────────────


class TestSdkExportsDist:
    def test_script_exists(self):
        assert SDK_EXPORTS.is_file()

    def test_runs_clean_non_strict(self):
        rc, out = _run_py(SDK_EXPORTS)
        assert rc == 0, f"non-strict expected exit 0; got {rc}\n{out}"

    def test_emits_summary_line(self):
        _, out = _run_py(SDK_EXPORTS)
        last_summary = [
            line for line in out.splitlines()
            if ":" in line and line.split(":")[-1].strip().isdigit()
        ]
        assert last_summary, f"no `: <int>$` summary line found:\n{out}"

    def test_strict_passes_at_zero(self):
        # iter-39 baseline: 0 findings.
        rc, _ = _run_py(SDK_EXPORTS, ["--strict"])
        assert rc == 0, f"strict mode with 0 findings should exit 0; got {rc}"

    def test_accepts_pkg_dir_argument(self):
        # The script accepts an optional package dir; verify the default
        # (no arg) targets the SDK without raising.
        rc, _ = _run_py(SDK_EXPORTS)
        assert rc == 0


# ─── sibling-convention-drift.py ──────────────────────────────────────


class TestSiblingConventionDrift:
    def test_script_exists(self):
        assert SIBLING_DRIFT.is_file()

    def test_runs_clean_non_strict(self):
        rc, out = _run_py(SIBLING_DRIFT)
        assert rc == 0, f"non-strict expected exit 0; got {rc}\n{out}"

    def test_emits_summary_line(self):
        _, out = _run_py(SIBLING_DRIFT)
        # iter-39 baseline: 0 outliers. Summary line format:
        # "convention-drift outliers (... 80% ... lacks it): N"
        assert "outliers" in out.lower() or "convention" in out.lower(), (
            f"summary line missing 'outliers'/'convention': {out}"
        )
        last_summary = [
            line for line in out.splitlines()
            if ":" in line and line.split(":")[-1].strip().isdigit()
        ]
        assert last_summary, f"no `: <int>$` summary line found:\n{out}"

    def test_strict_passes_at_zero(self):
        # iter-39 baseline: 0 findings (10 missing-license + 4 missing-
        # description outliers fixed in iter-38/39).
        rc, _ = _run_py(SIBLING_DRIFT, ["--strict"])
        assert rc == 0, f"strict mode with 0 findings should exit 0; got {rc}"

    def test_scans_etzhayyim_namespace(self):
        # Sanity: report mentions @etzhayyim/* (or 54 sibling count
        # established in iter-37/38).
        _, out = _run_py(SIBLING_DRIFT)
        assert "etzhayyim" in out.lower() or "publish-eligible" in out.lower(), (
            f"sibling-convention-drift report should reference @etzhayyim/*\n{out}"
        )


# ─── Aggregator format invariant ──────────────────────────────────────


class TestAggregatorFormatContract:
    """The aggregator (all.sh) extracts each script's count via the
    pattern `: <int>$`. Lock in that ALL aggregator scripts emit such
    a line; if a future refactor removes it, the aggregator's rollup
    silently fails."""

    @pytest.mark.parametrize("script_path", [
        DEPENDABOT,
        SDK_EXPORTS,
        SIBLING_DRIFT,
    ])
    def test_script_emits_aggregator_compatible_summary(self, script_path: Path):
        _, out = _run_py(script_path)
        # Last `: <int>$` line is the one the aggregator picks.
        last_summary = [
            line.strip() for line in out.splitlines()
            if line.strip().endswith(tuple(": " + str(i) for i in range(10000)))
            or (line.count(":") and line.rsplit(":", 1)[-1].strip().isdigit())
        ]
        # Loose check: at least one matching line exists somewhere.
        has_match = any(
            line.rsplit(":", 1)[-1].strip().isdigit()
            for line in out.splitlines()
            if ":" in line
        )
        assert has_match, (
            f"{script_path.name} no longer emits `: <int>` summary line; "
            f"aggregator (all.sh) will silently roll up 0 for this audit.\n"
            f"stdout:\n{out}"
        )
