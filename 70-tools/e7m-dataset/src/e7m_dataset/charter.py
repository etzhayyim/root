"""Charter Rider §2 scan gate.

Calls `kotodama.organism.sensors.charter_rider.scan()` (canonical
scanner per ADR-2605192200 / CLAUDE.md baien tooling index). Three
import strategies are tried in order:

  1. Standard `kotodama.organism.sensors.charter_rider` — works when
     kotodama is installed in the venv (production).
  2. `ETZ_PYKOTODAMA_SRC` env var (path to `40-engine/kotoba/crates/kotoba-kotodama/py/src`)
     — operator-controlled override.
  3. Repo-root auto-discovery — finds the monorepo by walking up from
     the CLI's cwd and prepends `40-engine/kotoba/crates/kotoba-kotodama/py/src` to
     `sys.path`. Works when run from inside the monorepo without
     installing the heavy kotodama deps (arrow-udf, langgraph, etc.).

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
SRC_OVERRIDE_ENV = "ETZ_PYKOTODAMA_SRC"


class CharterViolation(RuntimeError):
    pass


def _try_repo_root_inject() -> bool:
    """Walk up from cwd looking for the monorepo root marker, prepend
    `40-engine/kotoba/crates/kotoba-kotodama/py/src` to sys.path. Returns True on success."""
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        cand = p / "20-actors" / "kotodama" / "py" / "src"
        if cand.is_dir() and (cand / "kotodama" / "organism" / "sensors" / "charter_rider.py").is_file():
            if str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
            return True
    return False


def _direct_load_charter_rider(charter_rider_path: Path) -> ModuleType | None:
    """Load charter_rider.py as a standalone module.

    Avoids triggering ``kotodama/__init__.py`` (which imports
    langchain → pydantic; on machines with a broken pydantic-core
    pinning that init poisons the import). The Charter scanner is pure
    stdlib + regex; it does not need the rest of the kotodama
    package to function.
    """
    import importlib.util

    if not charter_rider_path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(
            "_e7m_dataset_charter_rider_direct", charter_rider_path
        )
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 — best-effort sidecar load
        return None


def _find_charter_rider_path() -> Path | None:
    """Try the SRC_OVERRIDE_ENV first, then repo-root walk-up."""
    override = os.environ.get(SRC_OVERRIDE_ENV)
    if override:
        ov = Path(override).resolve()
        candidate = ov / "kotodama" / "organism" / "sensors" / "charter_rider.py"
        if candidate.is_file():
            return candidate
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        candidate = (
            p
            / "20-actors" / "kotodama" / "py" / "src"
            / "kotodama" / "organism" / "sensors" / "charter_rider.py"
        )
        if candidate.is_file():
            return candidate
    return None


def _load_scanner() -> ModuleType | None:
    """Return the charter_rider module or None.

    Strategy ordering:
      1. Direct file-load from the in-tree source (skips kotodama
         package __init__, robust to unrelated langchain/pydantic
         pinning issues).
      2. Standard ``kotodama.organism.sensors.charter_rider`` import
         — works in production where kotodama is installed cleanly.
      3. ETZ_PYKOTODAMA_SRC sys.path prepend + standard import.
      4. Repo-root auto-discovery sys.path prepend + standard import.
    """
    # Strategy 1: direct file-load. Try this FIRST so we never touch
    # the broken kotodama package init when the scanner is enough.
    charter_path = _find_charter_rider_path()
    if charter_path is not None:
        mod = _direct_load_charter_rider(charter_path)
        if mod is not None:
            return mod

    # Strategy 2: standard package import.
    try:
        from kotodama.organism.sensors import charter_rider  # type: ignore
        return charter_rider
    except ImportError:
        pass

    # Strategy 3: env override + standard package import.
    override = os.environ.get(SRC_OVERRIDE_ENV)
    if override:
        ov = Path(override).resolve()
        if (ov / "kotodama" / "organism" / "sensors" / "charter_rider.py").is_file():
            if str(ov) not in sys.path:
                sys.path.insert(0, str(ov))
            try:
                from kotodama.organism.sensors import charter_rider  # type: ignore
                return charter_rider
            except ImportError:
                pass

    # Strategy 4: repo-root walk-up + standard package import.
    if _try_repo_root_inject():
        try:
            from kotodama.organism.sensors import charter_rider  # type: ignore
            return charter_rider
        except ImportError:
            return None
    return None


def scan_sample(sample_paths: Iterable[Path], *, kind: str, sample_rows: int = 200) -> dict:
    """Run the §2 scan over a sample of files; return a result dict.

    The result shape matches the `charterRiderScan` sub-object of the
    `com.etzhayyim.substrate.datasetPin` lexicon.
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    strict = os.environ.get(STRICT_ENV, "0") == "1"

    scanner = _load_scanner()
    if scanner is None:
        if strict:
            raise ImportError(
                "Charter Rider scanner unavailable (kotodama.organism.sensors.charter_rider "
                "could not be imported); ETZ_DATASET_CHARTER_STRICT=1 forces fail-closed."
            )
        return {
            "passed": True,
            "at": now,
            "sampledRows": 0,
            "note": "scanner-unavailable — warn-only; install kotodama, set ETZ_PYKOTODAMA_SRC, or run from inside the monorepo to enable",
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
