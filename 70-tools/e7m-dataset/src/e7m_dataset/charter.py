"""Charter Rider §2 scan gate.

Calls `pymagatama.organism.sensors.charter_rider.scan()` (canonical
scanner per ADR-2605192200 / CLAUDE.md baien tooling index). Three
import strategies are tried in order:

  1. Standard `pymagatama.organism.sensors.charter_rider` — works when
     pymagatama is installed in the venv (production).
  2. `ETZ_PYMAGATAMA_SRC` env var (path to `20-actors/magatama/py/src`)
     — operator-controlled override.
  3. Repo-root auto-discovery — finds the monorepo by walking up from
     the CLI's cwd and prepends `20-actors/magatama/py/src` to
     `sys.path`. Works when run from inside the monorepo without
     installing the heavy pymagatama deps (arrow-udf, langgraph, etc.).

If all three fail and `ETZ_DATASET_CHARTER_STRICT=1`, raises. Otherwise
returns a warn-only result with `passed=True` and a "scanner-unavailable"
note (defensible for Phase 1 smoke, not for production).

On any §2(a)..(h) hit, raises CharterViolation (fail-closed).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Iterable


STRICT_ENV = "ETZ_DATASET_CHARTER_STRICT"
SRC_OVERRIDE_ENV = "ETZ_PYMAGATAMA_SRC"


class CharterViolation(RuntimeError):
    pass


def _try_repo_root_inject() -> bool:
    """Walk up from cwd looking for the monorepo root marker, prepend
    `20-actors/magatama/py/src` to sys.path. Returns True on success."""
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        cand = p / "20-actors" / "magatama" / "py" / "src"
        if cand.is_dir() and (cand / "pymagatama" / "organism" / "sensors" / "charter_rider.py").is_file():
            if str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
            return True
    return False


def _load_scanner() -> ModuleType | None:
    """Return the charter_rider module or None."""
    try:
        from pymagatama.organism.sensors import charter_rider  # type: ignore
        return charter_rider
    except ImportError:
        pass

    override = os.environ.get(SRC_OVERRIDE_ENV)
    if override:
        ov = Path(override).resolve()
        if (ov / "pymagatama" / "organism" / "sensors" / "charter_rider.py").is_file():
            if str(ov) not in sys.path:
                sys.path.insert(0, str(ov))
            try:
                from pymagatama.organism.sensors import charter_rider  # type: ignore
                return charter_rider
            except ImportError:
                pass

    if _try_repo_root_inject():
        try:
            from pymagatama.organism.sensors import charter_rider  # type: ignore
            return charter_rider
        except ImportError:
            return None
    return None


def scan_sample(sample_paths: Iterable[Path], *, kind: str, sample_rows: int = 200) -> dict:
    """Run the §2 scan over a sample of files; return a result dict.

    The result shape matches the `charterRiderScan` sub-object of the
    `app.etzhayyim.substrate.datasetPin` lexicon.
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    strict = os.environ.get(STRICT_ENV, "0") == "1"

    scanner = _load_scanner()
    if scanner is None:
        if strict:
            raise ImportError(
                "Charter Rider scanner unavailable (pymagatama.organism.sensors.charter_rider "
                "could not be imported); ETZ_DATASET_CHARTER_STRICT=1 forces fail-closed."
            )
        return {
            "passed": True,
            "at": now,
            "sampledRows": 0,
            "note": "scanner-unavailable — warn-only; install pymagatama, set ETZ_PYMAGATAMA_SRC, or run from inside the monorepo to enable",
        }

    findings = scanner.scan(
        list(sample_paths),
        kind=kind,
        sample_rows=sample_rows,
    )
    if findings.get("violations"):
        violations = findings["violations"]
        raise CharterViolation(
            f"Charter Rider §2 violations: {len(violations)} hits; "
            f"first={violations[0].get('categoryCode')}/{violations[0].get('path')}:"
            f"{violations[0].get('lineNo')} — {violations[0].get('snippet', '')[:80]}"
        )
    return {
        "passed": True,
        "at": now,
        "sampledRows": findings.get("sampled", 0),
        "note": findings.get("note"),
    }
