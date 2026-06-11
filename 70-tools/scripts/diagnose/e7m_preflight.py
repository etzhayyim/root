#!/usr/bin/env python3
"""e7m_preflight.py — single-command operator pre-flight for ADR-2605262500.

Aggregates the 3 diagnostic CLIs (vision_pii_diagnose / pds_diagnose /
assemble_diagnose) + the deps.toml book-keeping audit into one
PASS/FAIL summary. Operators run this BEFORE any production fetch /
assemble / eval to know "is my env ready end-to-end?".

Usage:

  python3 70-tools/scripts/diagnose/e7m_preflight.py
  python3 70-tools/scripts/diagnose/e7m_preflight.py --json
  python3 70-tools/scripts/diagnose/e7m_preflight.py --skip-pds-network
  python3 70-tools/scripts/diagnose/e7m_preflight.py --filter ADR-2605262500

Exit codes:
  0 — all 4 checks PASS
  1 — at least one check FAIL (operator action item)
  2 — script/dep failure

Each sub-check delegates to its respective `check` CLI subcommand, so
the per-tool diagnostics still work standalone for fine-grained
debugging. This wrapper is just convenience: one command in CI / one
command in operator runbook.

Reusable for: the operator-diagnostic-CLI-triad pattern (cycle 40
retrospective §pattern 4) — when an ADR ships multiple operator-facing
diagnostic surfaces, also ship a unified preflight that runs them all.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_VERIFIER = _REPO_ROOT / "70-tools" / "scripts" / "lint" / "verify_deps_toml_paths.py"
_ASSEMBLE_DIAGNOSE = _REPO_ROOT / "70-tools" / "e7m-sim" / "scripts" / "assemble_diagnose.py"
_E7M_DATASET_SRC = _REPO_ROOT / "70-tools" / "e7m-dataset" / "src"


def _run_check(label: str, argv: list[str], *, env_extra: Optional[dict] = None,
               cwd: Optional[Path] = None) -> dict:
    """Run a check subprocess; capture exit code + stderr/stdout."""
    import os
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    try:
        result = subprocess.run(
            argv, cwd=cwd or _REPO_ROOT, env=env,
            capture_output=True, text=True, timeout=30,
        )
        return {
            "label": label,
            "argv": argv,
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout_tail": result.stdout[-500:] if result.stdout else "",
            "stderr_tail": result.stderr[-500:] if result.stderr else "",
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {
            "label": label,
            "argv": argv,
            "exit_code": -1,
            "passed": False,
            "stderr_tail": str(exc),
        }


def run_preflight(*, skip_pds_network: bool = False,
                   verifier_filter: str = "ADR-2605262500") -> dict:
    """Run all 4 checks; return aggregated report."""
    py_env_extra = {
        "PYTHONPATH": f"{_E7M_DATASET_SRC}:" + (
            __import__("os").environ.get("PYTHONPATH") or ""
        ),
    }

    results = []

    # 1. Vision PII diagnose check
    results.append(_run_check(
        "vision_pii_diagnose",
        [sys.executable, "-m", "e7m_dataset.vision_pii_diagnose", "check"],
        env_extra=py_env_extra,
    ))

    # 2. PDS diagnose check
    pds_argv = [sys.executable, "-m", "e7m_dataset.pds_diagnose", "check"]
    if skip_pds_network:
        pds_argv.append("--skip-network")
    results.append(_run_check(
        "pds_diagnose",
        pds_argv,
        env_extra=py_env_extra,
    ))

    # 3. Assemble diagnose check
    results.append(_run_check(
        "assemble_diagnose",
        [sys.executable, str(_ASSEMBLE_DIAGNOSE), "check"],
    ))

    # 4. deps.toml verifier (filtered to ADR-2605262500 by default)
    results.append(_run_check(
        f"verify_deps_toml_paths --filter {verifier_filter}",
        [sys.executable, str(_VERIFIER), "--filter", verifier_filter],
    ))

    all_passed = all(r["passed"] for r in results)
    return {
        "all_passed": all_passed,
        "n_checks": len(results),
        "n_passed": sum(1 for r in results if r["passed"]),
        "results": results,
    }


def _print_human(report: dict) -> None:
    print("e7m preflight — operator pre-flight summary\n")
    for r in report["results"]:
        mark = "✓" if r["passed"] else "✘"
        print(f"  {mark} {r['label']}  (exit {r['exit_code']})")
        if not r["passed"] and r.get("stderr_tail"):
            for line in r["stderr_tail"].rstrip().splitlines()[-5:]:
                print(f"      {line}")
    print()
    if report["all_passed"]:
        print(f"PREFLIGHT: PASS  ({report['n_passed']}/{report['n_checks']} checks)")
    else:
        print(f"PREFLIGHT: FAIL  ({report['n_passed']}/{report['n_checks']} checks)")
        print("\nOperator action: review failing check(s) above.")
        print("  python3 -m e7m_dataset.vision_pii_diagnose check")
        print("  python3 -m e7m_dataset.pds_diagnose check")
        print("  python3 70-tools/e7m-sim/scripts/assemble_diagnose.py check")
        print("  python3 70-tools/scripts/lint/verify_deps_toml_paths.py")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="ADR-2605262500 operator pre-flight check (4-in-1)."
    )
    parser.add_argument("--json", action="store_true",
                          help="Emit JSON report instead of human-readable summary.")
    parser.add_argument("--skip-pds-network", action="store_true",
                          help="Pass --skip-network to pds_diagnose (offline-friendly).")
    parser.add_argument("--filter", default="ADR-2605262500",
                          help="ADR filter for deps.toml verifier (default: ADR-2605262500).")
    args = parser.parse_args(argv)

    report = run_preflight(
        skip_pds_network=args.skip_pds_network,
        verifier_filter=args.filter,
    )

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(report)

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
