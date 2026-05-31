#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Validate doc-relation integrity in 90-docs/_registry/docs.json.

Catches 4 classes of relation drift that schema validation does NOT catch
(the schema only checks field shape, not target existence):

  - dangling targets    — related/supersedes/amends references doc id
                          that doesn't exist in the registry
  - self-references     — entry's related field points at itself
  - circular related    — A→B and B→A both have `related` reference
                          (mutual; often intentional sibling docs but
                          worth flagging for review)
  - missing targets in   — superseded_by points to non-existent doc
    supersession chain    (breaks supersession graph traversal)

Cycle 60 ships this as a 6th-axis NIGHTLY TRACKER (parallel to cycle 50's
schema validation pattern) because the live baseline has ~1461 known
relation issues (1366 dangling related + 56 supersedes + 6 superseded_by
+ 6 amends + 1 self + 26 circular). The detector documents the baseline
so future cleanup cycles can chip away. Promotion to PR-gate awaits
baseline = 0 (or operator-asserted exempt list).

Usage:
    70-tools/scripts/docs/validate-relation-integrity.py
    70-tools/scripts/docs/validate-relation-integrity.py --json
    70-tools/scripts/docs/validate-relation-integrity.py --no-circular
        # treat circular `related` as accepted (often intentional siblings)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DOCS_JSON = REPO / "90-docs" / "_registry" / "docs.json"


def find_relation_issues(
    entries: list[dict[str, Any]],
    *,
    skip_circular: bool = False,
) -> dict[str, Any]:
    """Scan entries for dangling/self/circular relation issues."""
    all_ids = {e["id"] for e in entries if "id" in e}

    dangling: dict[str, list[dict[str, str]]] = {
        "related": [],
        "supersedes": [],
        "superseded_by": [],
        "amends": [],
        "amended_by": [],
        "depends_on": [],  # added cycle 64
    }
    self_refs: list[dict[str, str]] = []

    for e in entries:
        src = e.get("id")
        if not src:
            continue
        for field in dangling:
            targets = e.get(field) or []
            if isinstance(targets, str):
                targets = [targets]
            for target in targets:
                if not target or not isinstance(target, str):
                    continue
                if target == src:
                    self_refs.append({"src": src, "field": field})
                elif target not in all_ids:
                    dangling[field].append({"src": src, "target": target})

    circular: list[dict[str, str]] = []
    if not skip_circular:
        id_to_related = {
            e["id"]: set(e.get("related") or [])
            for e in entries
            if "id" in e
        }
        seen_pairs: set[tuple[str, str]] = set()
        for src, targets in id_to_related.items():
            for tgt in targets:
                if tgt in id_to_related and src in id_to_related[tgt]:
                    pair = tuple(sorted([src, tgt]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        circular.append({"a": pair[0], "b": pair[1]})

    return {
        "total_entries": len(entries),
        "total_ids": len(all_ids),
        "dangling_count": sum(len(v) for v in dangling.values()),
        "dangling": dangling,
        "self_reference_count": len(self_refs),
        "self_references": self_refs,
        "circular_count": len(circular),
        "circular": circular,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of human summary",
    )
    ap.add_argument(
        "--no-circular",
        action="store_true",
        help="skip circular `related` detection (mutual siblings often intentional)",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on ANY issue (default cycle-60 tracker mode: exit 0 with summary)",
    )
    args = ap.parse_args()

    if not DOCS_JSON.exists():
        print(
            f"validate-relation-integrity: missing {DOCS_JSON.relative_to(REPO)}",
            file=sys.stderr,
        )
        return 2

    docs = json.loads(DOCS_JSON.read_text(encoding="utf-8"))
    entries = docs.get("entries", [])
    issues = find_relation_issues(entries, skip_circular=args.no_circular)

    if args.json:
        print(json.dumps(issues, indent=2, ensure_ascii=False))
    else:
        print(f"doc relation integrity ({issues['total_entries']} entries):")
        for field, lst in issues["dangling"].items():
            if lst:
                print(f"  dangling {field}: {len(lst)}")
        if issues["self_reference_count"]:
            print(f"  self-references: {issues['self_reference_count']}")
        if issues["circular_count"]:
            print(f"  circular related pairs: {issues['circular_count']}")
        total = (
            issues["dangling_count"]
            + issues["self_reference_count"]
            + issues["circular_count"]
        )
        if total == 0:
            print("  No relation drift. Clean.")
        else:
            print(f"  Total issues: {total}")
            print()
            print(
                "  Baseline as of cycle 60 (2026-05-27): 1461 known issues"
                " (1366 dangling related + 56 supersedes + 6 superseded_by"
                " + 6 amends + 1 self + 26 circular)."
            )
            print(
                "  Tracker mode — exit 0 by default. Run with --strict to"
                " enforce; promotion to PR-gate awaits baseline cleanup."
            )

    total = (
        issues["dangling_count"]
        + issues["self_reference_count"]
        + issues["circular_count"]
    )
    if args.strict:
        return 0 if total == 0 else 1
    return 0  # tracker mode


if __name__ == "__main__":
    sys.exit(main())
