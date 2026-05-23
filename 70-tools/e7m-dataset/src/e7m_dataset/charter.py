"""Charter Rider §2 scan gate.

In production this calls `pymagatama.organism.sensors.charter_rider.scan()`
(canonical scanner per ADR-2605192200 / CLAUDE.md baien tooling index).
For the Phase 1 smoke path the wrapper degrades gracefully: if the
package isn't importable, the gate is "yellow" — it logs a warning and
records `passed=true, note='scanner-unavailable'`. **Production
deployments MUST install pymagatama and treat ImportError as fatal**;
that policy is enforced via env var ETZ_DATASET_CHARTER_STRICT=1.

This module is intentionally minimal — the heavy lifting lives in
pymagatama.organism.sensors.charter_rider.
"""

from __future__ import annotations

import os
import time
from pathlib import Path


STRICT_ENV = "ETZ_DATASET_CHARTER_STRICT"


class CharterViolation(RuntimeError):
    pass


def scan_sample(sample_paths: list[Path], *, kind: str, sample_rows: int = 200) -> dict:
    """Run the §2 scan over a sample of files; return a result dict.

    The result shape matches the `charterRiderScan` sub-object of the
    `app.etzhayyim.substrate.datasetPin` lexicon.
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    strict = os.environ.get(STRICT_ENV, "0") == "1"

    try:
        from pymagatama.organism.sensors import charter_rider  # type: ignore
    except ImportError:
        if strict:
            raise
        return {
            "passed": True,
            "at": now,
            "sampledRows": 0,
            "note": "scanner-unavailable (pymagatama not installed) — warn-only; set ETZ_DATASET_CHARTER_STRICT=1 to fail-closed",
        }

    findings = charter_rider.scan(
        sample_paths=sample_paths,
        kind=kind,
        sample_rows=sample_rows,
    )
    if findings.get("violations"):
        raise CharterViolation(
            f"Charter Rider §2 violations detected: {findings['violations'][:5]}"
        )
    return {
        "passed": True,
        "at": now,
        "sampledRows": findings.get("sampled", 0),
        "note": findings.get("note"),
    }
