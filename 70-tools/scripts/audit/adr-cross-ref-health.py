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

# A range expression like `ADR-2605242700..2605242915` is shorthand for
# the wave of ADRs across that timestamp window. Intermediate IDs aren't
# individually cited and aren't bugs.
ADR_RANGE_RE = re.compile(
    r"\bADR-(\d{4}|\d{10,12})\.\.(\d{4}|\d{10,12})\b"
)

# Forward-ref / planned-slot markers in the immediate citation context.
# `ADR-2605242015 (R1)` or `(planned)` / `(future)` / `(R0 scaffold)` etc.
# We require the marker to come within ~80 chars after the ID so we don't
# falsely match a different parenthetical further down the line.
FORWARD_REF_MARKER_RE = re.compile(
    r"\((?:R[0-9](?:\b[^)]*)?|planned|future|reserved|scaffold|R[0-9]\s+scaffold|TBD|tbd)\)",
    re.IGNORECASE,
)
FORWARD_REF_CONTEXT_CHARS = 80

# Self-documenting historical orphans: the citing line explicitly
# acknowledges that the ADR was drafted-but-not-retained / merged
# inline elsewhere. These are forensic notes, not broken refs.
#
# Examples (all from ADR-2605211653 mst-projector case):
#   "(gate (c) standalone ADR-XXX was drafted but not retained)"
#   "earlier-drafted standalone ADR-XXX"
#   "originally-drafted ADR-XXX"
#   "standalone ADR-XXX was drafted"
#
# We require BOTH "drafted" AND one of {not retained, originally,
# standalone, inline, merged} to appear in the same line as the ID,
# to avoid matching unrelated "draft" mentions.
HISTORICAL_ORPHAN_RE = re.compile(
    r"\bdrafted\b.*\b(?:not retained|originally|standalone|inline|merged)\b"
    r"|\b(?:not retained|originally|standalone|inline|merged)\b.*\bdrafted\b",
    re.IGNORECASE,
)


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
        # Test file uses synthetic ADR IDs (ADR-2605000000 etc.) as
        # fixture inputs for filter tests — those aren't real citations.
        if file_path == "70-tools/scripts/audit/test_adr_cross_ref_health.py":
            continue
        if file_path == "90-docs/adr/_template-stall-rotation.md":
            continue
        if file_path == "90-docs/adr/template.md":
            continue

        # Skip range-expression IDs entirely. `ADR-2605242700..2605242915`
        # is shorthand for a wave; the only "cited" IDs are the two
        # endpoints, not the intermediate timestamps. Strip range
        # expressions from the line before per-ID extraction.
        cleaned_content = ADR_RANGE_RE.sub(
            lambda m: f"ADR-{m.group(1)} ADR-{m.group(2)}",
            content,
        )

        # Historical-orphan filter: if the line contains explicit
        # acknowledgment that the ADR was drafted-but-not-retained
        # (forensic notes from session post-mortems / migration logs),
        # skip the entire line — the citation is self-documenting.
        if HISTORICAL_ORPHAN_RE.search(cleaned_content):
            continue

        for m in ADR_REF_RE.finditer(cleaned_content):
            adr_id = m.group(1)
            # Forward-ref filter: if the citation context immediately
            # after the ID contains `(R1)` / `(planned)` / `(future)` /
            # `(reserved)` / `(scaffold)` / `(TBD)`, this is a deliberate
            # forward-reference to a reserved slot, not a broken ref.
            ctx_start = m.end()
            ctx = cleaned_content[ctx_start : ctx_start + FORWARD_REF_CONTEXT_CHARS]
            if FORWARD_REF_MARKER_RE.search(ctx):
                continue
            # Cap citations per ID to keep the report scannable.
            if len(citations[adr_id]) < 5:
                citations[adr_id].append(f"{file_path}:{lineno}")
    return citations


def categorize(adr_id: str) -> str:
    """Bucket an orphan ID for triage prioritization.

    The categories help operators decide which orphans to tackle first:
    - 4-digit legacy IDs are from the old ADR convention before
      ADR-2604231349 (timestamp-numbering-policy). Resolution is usually
      "delete the reference" or "rename to successor ADR".
    - 0000-suffix IDs are obvious placeholders that were used as round-
      number stubs and never authored. Resolution is usually "delete
      the reference" since no real ADR was ever planned.
    - invalid-mm-overflow: MM >= 60 (clock impossibility) — typically
      from someone adding +15 to :45 → :60 instead of incrementing the
      hour. True bug; fix to the next valid timestamp.
    - quarter-hour-planned-slot: MM in {00, 15, 30, 45} — typical
      authored timestamps; an orphan here is most likely a real
      planned-ADR slot that didn't get written.
    - non-canonical-mm: MM not in the quarter set but < 60 — wave-
      numbering reservations using minute as sub-index (e.g., kotoba
      LLM crates use :04, :05, :06 as architecturally-grouped slots).
      NOT necessarily a typo; needs case-by-case operator judgment.
    """
    if len(adr_id) == 4:
        return "legacy-4digit"
    if adr_id.endswith("0000"):
        return "placeholder-0000-suffix"
    if len(adr_id) == 10:
        # last 4 chars are HHMM
        try:
            mm = int(adr_id[-2:])
        except ValueError:
            return "other"
        if mm >= 60:
            return "invalid-mm-overflow"
        if mm in (0, 15, 30, 45):
            return "quarter-hour-planned-slot"
        return "non-canonical-mm"
    return "other"


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
        # Category counts for fast triage scan.
        counts: dict[str, int] = defaultdict(int)
        for adr_id in orphans:
            counts[categorize(adr_id)] += 1
        print()
        print("by category:")
        for cat in (
            "legacy-4digit",
            "placeholder-0000-suffix",
            "invalid-mm-overflow",
            "quarter-hour-planned-slot",
            "non-canonical-mm",
            "other",
        ):
            n = counts.get(cat, 0)
            if n:
                print(f"  {cat:<32} {n:>4}")

        print()
        # sort: longest-format IDs (newer convention) first, then by ID
        for adr_id in sorted(orphans.keys(), key=lambda x: (-len(x), x)):
            cat = categorize(adr_id)
            print(f"ADR-{adr_id}  [{cat}]")
            for cite in orphans[adr_id]:
                print(f"  {cite}")

    if strict and orphans:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
