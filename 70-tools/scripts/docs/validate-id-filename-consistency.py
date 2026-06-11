#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Validate id↔filename consistency across 90-docs/_registry/docs.json.

Per 90-docs/CLAUDE.md "ADR ID Convention", ADR id should match the
filename slug (optionally prefixed with 'adr-' or 'doc-'). Some
historical conventions are tolerated:
  - timestamp-only id (e.g. id='2605262500' for filename
    '2605262500-foo-bar.md')
  - lowercase 'adr-<timestamp>' for short legacy IDs

Catches 4 drift classes (cycle 61 baseline 57, after 6 uppercase-ADR
auto-fix + permissive matching improvement):

  - uppercase 'ADR-' prefix — should be 'adr-' (cycle 61 cleaned 6;
    baseline 0 going forward; auto-fix-safe in future)
  - etzhayyimcojp/amanomibashira pre-cutover filename — accepted per
    CLAUDE.md root §"Do Not" rename-invariants (2 known;
    documented-deferred)
  - short id missing slug — id='adr-NNNN' but filename has slug
    (1 remaining after permissive matching; legacy 4-digit ADR scheme
    pre-modern timestamp convention)
  - engineering policy old-style — `/engineering/` docs with
    short 'adr-NNNN-foo' IDs (3 known)
  - other rename-related — filename uses old name, id uses new name
    (or vice versa) — mostly legitimate pre-cutover invariants
    (amanomibashira → etzhayyim, shinka → etzhayyim, etc.) (51 known)

Cycle 61 ships this as 7th-axis NIGHTLY TRACKER (Pattern B from cycles
50/60). Cleanup of 57 remaining requires per-entry judgment.

Usage:
    70-tools/scripts/docs/validate-id-filename-consistency.py
    70-tools/scripts/docs/validate-id-filename-consistency.py --json
    70-tools/scripts/docs/validate-id-filename-consistency.py --strict
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DOCS_JSON = REPO / "90-docs" / "_registry" / "docs.json"


def categorize_mismatch(path: str, fid: str) -> str:
    """Return category name for an id↔filename mismatch."""
    if fid.startswith("ADR-"):
        return "uppercase-ADR-prefix"
    if "etzhayyimcojp" in path or "amanomibashira" in path:
        return "pre-cutover-rename"
    if re.match(r"^adr-\d{4,10}$", fid):
        return "short-id-missing-slug"
    if "/engineering/" in path:
        return "engineering-policy-old-style"
    return "other-rename-related"


def find_mismatches(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Scan entries for id↔filename mismatches; categorize each."""
    by_category: dict[str, list[dict[str, str]]] = {}
    for e in entries:
        fid = e.get("id", "")
        path = e.get("path", "")
        if not fid or not path:
            continue
        basename = os.path.basename(path).replace(".md", "")
        fid_norm = re.sub(r"^(adr-|doc-)", "", fid)
        # Multiple acceptable equivalences:
        # 1. exact match after prefix strip
        # 2. basename ends with the id (timestamp prefix match)
        # 3. basename starts with id + '-' (slug omitted from id)
        if (
            basename == fid_norm
            or basename.endswith(fid_norm)
            or basename.startswith(fid + "-")
            or basename.startswith(fid_norm + "-")
        ):
            continue
        cat = categorize_mismatch(path, fid)
        by_category.setdefault(cat, []).append({"path": path, "id": fid, "basename": basename})

    total = sum(len(v) for v in by_category.values())
    return {
        "total": total,
        "by_category": by_category,
        "categories": list(by_category.keys()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on ANY mismatch (default cycle-61 tracker mode: exit 0)",
    )
    args = ap.parse_args()

    if not DOCS_JSON.exists():
        print(
            f"validate-id-filename-consistency: missing {DOCS_JSON.relative_to(REPO)}",
            file=sys.stderr,
        )
        return 2

    docs = json.loads(DOCS_JSON.read_text(encoding="utf-8"))
    entries = docs.get("entries", [])
    result = find_mismatches(entries)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"id↔filename consistency ({len(entries)} entries):")
        if result["total"] == 0:
            print("  No mismatches. Clean.")
        else:
            for cat in sorted(result["by_category"]):
                lst = result["by_category"][cat]
                print(f"  {cat}: {len(lst)}")
            print(f"  Total mismatches: {result['total']}")
            print()
            print(
                "  Baseline as of cycle 61 (2026-05-27): 57 known mismatches"
                " across 4 remaining categories (cycle 61 cleaned 6 uppercase-ADR;"
                " count reduced from 88 → 57 by permissive matching improvement)."
            )
            print(
                "  Tracker mode — exit 0 by default. Run with --strict to"
                " enforce; promotion to PR-gate awaits cleanup."
            )

    if args.strict:
        return 0 if result["total"] == 0 else 1
    return 0  # tracker mode


if __name__ == "__main__":
    sys.exit(main())
