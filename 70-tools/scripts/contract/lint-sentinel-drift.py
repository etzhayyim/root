#!/usr/bin/env python3
# ruff: noqa: T201
"""
CI lint: maps Sentinel scaffolding drift check.

Asserts that the four artefacts defining the maps Sentinel pipeline stay in sync:

  A  BPMN files (orgs/etzhayyim/com-etzhayyim-maps/wire/bpmn/maps/sentinel*.bpmn)
     • sentinelIngest.bpmn  — timer-start R/PT24H
     • sentinelAnalyze.bpmn — XRPC-triggered

  B  zeebe:taskDefinition type attributes extracted from each BPMN

  C  Primitive task types registered in
     40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/maps_sentinel.py

  D  Lexicon NSID JSON files
     (00-contracts/lexicons/com/etzhayyim/apps/maps/satellite{Ingest,Analyze}.json)

  E  Phase 2 typed-table migration file
     (30-graph/graph-schema/migrations/20260427220000_vertex_satellite_typed_tables.ts)

Checks (all must pass for exit 0):

  C1  Both BPMN files exist on disk
  C2  Each BPMN's sentinel zeebe:taskDefinition type is registered in
      maps_sentinel.py (B ∩ C — no phantom task types)
  C3  Each task type in maps_sentinel.py has a matching BPMN that uses it
      (C ∩ B — no orphan registrations)
  C4  Each BPMN's `nsid` metadata field points to an existing lexicon JSON
  C5  Phase 2 migration file exists

Usage:
    python3 70-tools/scripts/contract/lint-sentinel-drift.py
    python3 70-tools/scripts/contract/lint-sentinel-drift.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[3]

BPMN_DIR = REPO_ROOT / "00-contracts" / "bpmn" / "com" / "etzhayyim" / "maps"
LEXICON_DIR = REPO_ROOT / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "apps" / "maps"
PRIMITIVE_PATH = (
    REPO_ROOT
    / "20-actors"
    / "kotodama"
    / "py"
    / "src"
    / "kotodama"
    / "primitives"
    / "maps_sentinel.py"
)
MIGRATION_PATH = (
    REPO_ROOT
    / "30-graph"
    / "graph-schema"
    / "migrations"
    / "20260427220000_vertex_satellite_typed_tables.ts"
)

EXPECTED_BPMN_FILES = ["sentinelIngest.bpmn", "sentinelAnalyze.bpmn"]

NS_BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS_ZEEBE = "http://camunda.org/schema/zeebe/1.0"

# Only check task types that belong to the maps.sentinel.* namespace.
SENTINEL_TASK_PREFIX = "maps.sentinel."


def _parse_bpmn(path: Path) -> tuple[list[str], str | None]:
    """Return (sentinel_task_types, nsid) extracted from a BPMN file."""
    tree = ET.parse(path)
    root = tree.getroot()

    task_types: list[str] = []
    for td in root.iter(f"{{{NS_ZEEBE}}}taskDefinition"):
        t = td.get("type", "")
        if t.startswith(SENTINEL_TASK_PREFIX):
            task_types.append(t)

    nsid: str | None = None
    for doc in root.iter(f"{{{NS_BPMN}}}documentation"):
        text = (doc.text or "").strip()
        try:
            meta = json.loads(text)
            nsid = meta.get("nsid")
            break
        except (json.JSONDecodeError, AttributeError):
            pass

    return task_types, nsid


def _parse_primitive_task_types() -> list[str]:
    """Return all task_type strings registered in maps_sentinel.py."""
    src = PRIMITIVE_PATH.read_text()
    return re.findall(r'task_type\s*=\s*"(maps\.sentinel\.[^"]+)"', src)


def _nsid_to_lexicon_path(nsid: str) -> Path:
    """com.etzhayyim.apps.maps.fooBar → lexicons/com/etzhayyim/apps/maps/fooBar.json"""
    parts = nsid.split(".")
    # NSIDs follow com.etzhayyim.apps.<appName>.<methodName>
    method = parts[-1]
    return LEXICON_DIR / f"{method}.json"


def run(json_output: bool = False) -> int:
    failures: list[str] = []
    info: dict = {
        "bpmn_files": {},
        "bpmn_task_types": [],
        "primitive_task_types": [],
        "lexicons": {},
        "migration": str(MIGRATION_PATH.relative_to(REPO_ROOT)),
        "checks": {},
    }

    # ── C1: BPMN files exist ────────────────────────────────────────────
    bpmn_task_types: list[str] = []
    nsids_from_bpmn: list[str] = []

    for fname in EXPECTED_BPMN_FILES:
        path = BPMN_DIR / fname
        exists = path.exists()
        info["bpmn_files"][fname] = str(path.relative_to(REPO_ROOT)) if exists else "MISSING"
        if not exists:
            failures.append(f"C1 MISSING bpmn: {BPMN_DIR.relative_to(REPO_ROOT)}/{fname}")
            continue
        types, nsid = _parse_bpmn(path)
        bpmn_task_types.extend(types)
        if nsid:
            nsids_from_bpmn.append(nsid)

    info["bpmn_task_types"] = sorted(set(bpmn_task_types))
    info["checks"]["C1_bpmn_files_exist"] = not any("C1" in f for f in failures)

    # ── C2/C3: task type symmetry ────────────────────────────────────────
    primitive_task_types: list[str] = []
    if not PRIMITIVE_PATH.exists():
        failures.append(f"primitive not found: {PRIMITIVE_PATH.relative_to(REPO_ROOT)}")
    else:
        primitive_task_types = _parse_primitive_task_types()

    info["primitive_task_types"] = sorted(set(primitive_task_types))

    bpmn_set = set(bpmn_task_types)
    prim_set = set(primitive_task_types)

    phantom = bpmn_set - prim_set  # in BPMN but not in primitive
    orphan = prim_set - bpmn_set   # in primitive but not in any BPMN

    for t in sorted(phantom):
        failures.append(f"C2 BPMN uses task type '{t}' not found in maps_sentinel.py")
    for t in sorted(orphan):
        failures.append(f"C3 maps_sentinel.py registers '{t}' with no matching BPMN")

    info["checks"]["C2_no_phantom_task_types"] = len(phantom) == 0
    info["checks"]["C3_no_orphan_registrations"] = len(orphan) == 0

    # ── C4: lexicon JSON exists for each BPMN nsid ──────────────────────
    for nsid in nsids_from_bpmn:
        lex_path = _nsid_to_lexicon_path(nsid)
        exists = lex_path.exists()
        rel = str(lex_path.relative_to(REPO_ROOT))
        info["lexicons"][nsid] = rel if exists else "MISSING"
        if not exists:
            failures.append(f"C4 MISSING lexicon for nsid '{nsid}': {rel}")

    info["checks"]["C4_lexicons_exist"] = not any("C4" in f for f in failures)

    # ── C5: Phase 2 migration file exists ───────────────────────────────
    migration_ok = MIGRATION_PATH.exists()
    info["checks"]["C5_phase2_migration_exists"] = migration_ok
    if not migration_ok:
        failures.append(
            f"C5 MISSING Phase 2 migration: {MIGRATION_PATH.relative_to(REPO_ROOT)}"
        )

    # ── report ───────────────────────────────────────────────────────────
    info["failures"] = failures
    info["ok"] = len(failures) == 0

    if json_output:
        print(json.dumps(info, indent=2))
    else:
        total = len(info["checks"])
        passed = sum(1 for v in info["checks"].values() if v)
        print(f"lint-sentinel-drift: {passed}/{total} checks passed")
        for check, ok in info["checks"].items():
            mark = "✓" if ok else "✗"
            print(f"  {mark}  {check}")
        if failures:
            print()
            for f in failures:
                print(f"  FAIL: {f}")
        else:
            print()
            print("  All checks passed.")

    return 0 if info["ok"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args()
    sys.exit(run(json_output=args.json))


if __name__ == "__main__":
    main()
