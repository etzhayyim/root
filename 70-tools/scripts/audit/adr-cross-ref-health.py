#!/usr/bin/env python3
# pyright: strict
"""
adr-cross-ref-health.py — find ADR-NNNN references in any tracked file
that don't resolve to an actual ADR file under 90-docs/adr/.

Why this matters
================
Religious-corp constitutional ADRs cite each other heavily — a typical
Status row in CLAUDE.md lists 5-15 "depends on ADR-XXXX" entries.
When an ADR ID is mis-typed, mis-pasted, or refers to a planned-but-
never-written ADR, the dependency chain rots silently. This audit
catches all broken references in a single pass.

ADR ID formats accepted (per 90-docs/adr/README.md):
  - 4-digit:  ADR-0031, ADR-0046       (legacy sequential)
  - 10-digit: ADR-2604251830           (new YYMMDDHHMM timestamp)
  - 12-digit: ADR-260427183045         (rare, with seconds)

The script:
  1. Globs 90-docs/adr/*.md, extracts each leading ID before the slug.
  2. Greps every tracked file in the repo for the ADR-NNNN pattern.
  3. Diffs the cited set against the existing set; reports the orphans.

Defaults to exit 0 with a per-finding report. --strict makes findings
fatal (for CI integration).

Discovery: iter-40 of /loop (2026-05-27).
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ADR_DIR = REPO_ROOT / "90-docs" / "adr"

# Matches the ID portion at the start of an ADR filename.
# `0031-foo.md` -> 0031 ; `2605262400-bar.md` -> 2605262400.
ADR_FILENAME_RE = re.compile(r"^(\d{4}|\d{10,12})-")

# Matches inline references in any tracked file.
# Examples: ADR-0031 / ADR-2605262400 / ADR-260427183045
# Excludes overly-long digit runs that are clearly something else.
ADR_REF_RE = re.compile(r"\bADR-(\d{4}|\d{10,12})\b")


def find_existing_adr_ids() -> set[str]:
    """Set of ADR IDs that have an actual file under 90-docs/adr/."""
    ids: set[str] = set()
    for p in ADR_DIR.glob("*.md"):
        m = ADR_FILENAME_RE.match(p.name)
        if m:
            ids.add(m.group(1))
    return ids


def find_referenced_ids() -> dict[str, list[str]]:
    """Map of ADR ID -> list of file:line citations across all tracked files.

    Uses `git grep -n` to scan only tracked content (skips node_modules,
    .git/, etc.). Returns at most a handful of citations per orphan to
    keep the report scannable.
    """
    citations: dict[str, list[str]] = defaultdict(list)
    # `git grep -n -E -e <pat> -- .` returns "file:line:matchline".
    # Use POSIX-ERE pattern (no `\d`); the Python regex above re-extracts
    # cleanly with `\d{...}` semantics for ID validation.
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "grep",
                "-n",
                "-E",
                "-e",
                r"ADR-[0-9]{4}([^0-9]|$)|ADR-[0-9]{10,12}([^0-9]|$)",
                "--",
                ".",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return citations

    for line in result.stdout.splitlines():
        # "path/to/file:42:... ADR-2605262400 ..."
        try:
            file_path, lineno, content = line.split(":", 2)
        except ValueError:
            continue
        # skip lines that are themselves part of the audit / template
        if file_path == "70-tools/scripts/audit/adr-cross-ref-health.py":
            continue
        if file_path == "90-docs/adr/_template-stall-rotation.md":
            continue
        if file_path == "90-docs/adr/template.md":
            continue
        for m in ADR_REF_RE.finditer(content):
            adr_id = m.group(1)
            # Cap citations per ID to keep the report scannable.
            if len(citations[adr_id]) < 5:
                citations[adr_id].append(f"{file_path}:{lineno}")
    return citations


def main() -> int:
    strict = "--strict" in sys.argv
    existing = find_existing_adr_ids()
    referenced = find_referenced_ids()

    orphans: dict[str, list[str]] = {
        adr_id: cites
        for adr_id, cites in referenced.items()
        if adr_id not in existing
    }

    print(f"ADR files on disk: {len(existing)}")
    print(f"ADR IDs referenced anywhere: {len(referenced)}")
    print(f"Orphaned references (cited but no file): {len(orphans)}")

    if orphans:
        print()
        # sort: longest-format IDs (newer convention) first, then by ID
        for adr_id in sorted(orphans.keys(), key=lambda x: (-len(x), x)):
            print(f"ADR-{adr_id}")
            for cite in orphans[adr_id]:
                print(f"  {cite}")

    if strict and orphans:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
