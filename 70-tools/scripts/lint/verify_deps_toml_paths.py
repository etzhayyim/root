#!/usr/bin/env python3
"""verify_deps_toml_paths.py — book-keeping lint for deps.toml path entries.

Walks every `[[adrs]]` and `[[modules]]` block in `deps.toml`, checks that
each `path` value resolves to an existing file or directory under the
repo root, and reports drifts.

Purpose: when a linter / refactor / parallel agent renames or removes
a file referenced from deps.toml, this lint catches the orphaned
entry on the next CI run instead of letting it rot silently.

Usage:

  python3 70-tools/scripts/lint/verify_deps_toml_paths.py
  python3 70-tools/scripts/lint/verify_deps_toml_paths.py --json
  python3 70-tools/scripts/lint/verify_deps_toml_paths.py --filter ADR-2605262500

Exit codes:
  0 — no drift (accepted-reserved + stale-marker counts may be nonzero)
  1 — at least one drift entry (bare missing, no marker)
  2 — usage / parse error

Reservation markers (cycle 46, 2026-05-27)
--------------------------------------------
Paths intentionally not yet present may carry a trailing marker:

  path = "90-docs/adr/2605250730-tatekata-r1.md (reserved)"
  path = "00-contracts/lexicons/com/etzhayyim/apps/unispsc (deferred-rename)"

The verifier strips the marker before resolving and reports the
entry as "accepted-reserved" instead of drift. Two markers supported:

  (reserved)         — future R-cycle will produce this path
  (deferred-rename)  — path is intentionally pre-cutover per CLAUDE.md
                       etzhayyim→etzhayyim rename invariant

A path that EXISTS but still carries a marker is flagged as
"stale-marker" (warning, not drift) — operator should drop the
suffix.

Honest scoring per Charter Rider §G10 / ADR-2605261600 §G10: no
threshold-juggling — every BARE missing path is a real audit-trail
defect. Add the missing file, mark with `(reserved)` if owner-asserted
future-impl, or remove the deps.toml entry.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Optional


# Suffix conventions for paths intentionally not yet present.
# Format: trailing " (token)" where token is one of:
#   - reserved          → path will appear when a future R-cycle lands
#   - deferred-rename   → path is intentionally pre-cutover (per CLAUDE.md)
# Convention is owner-asserted: marker promises "this is not drift; the
# operator who added the entry knows the path is missing on purpose."
_RESERVED_SUFFIX_RE = re.compile(r"\s+\((?P<marker>reserved|deferred-rename)\)\s*$")


def _strip_reserved_marker(raw_path: str) -> tuple[str, Optional[str]]:
    """If raw_path ends in ' (reserved)' or ' (deferred-rename)', strip it.

    Returns (clean_path, marker) where marker is None if no suffix found,
    else the marker token (without parens).
    """
    m = _RESERVED_SUFFIX_RE.search(raw_path)
    if not m:
        return raw_path, None
    return raw_path[:m.start()], m.group("marker")


@dataclass
class PathCheck:
    section: str              # "adrs" | "modules"
    path: str                 # raw entry from deps.toml (including any marker)
    exists: bool              # whether the cleaned path resolves
    resolved: str             # absolute resolved cleaned path (for diagnostics)
    adr: Optional[str] = None    # ADR ref (when present in the [[modules]] block)
    id: Optional[str] = None     # ADR id (when section=="adrs")
    reserved_marker: Optional[str] = None  # "reserved" / "deferred-rename" / None

    @property
    def is_drift(self) -> bool:
        """True iff missing AND not owner-asserted as reserved/deferred."""
        return not self.exists and self.reserved_marker is None

    @property
    def is_accepted_missing(self) -> bool:
        """True iff missing AND owner-asserted via a reservation marker."""
        return not self.exists and self.reserved_marker is not None

    @property
    def is_stale_marker(self) -> bool:
        """True iff path exists but still carries a reservation marker.

        Warning state: the operator should drop the marker. Not drift.
        """
        return self.exists and self.reserved_marker is not None


def _iter_entries(data: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield ('adrs', entry) and ('modules', entry) blocks from deps.toml."""
    for section in ("adrs", "modules"):
        blocks = data.get(section)
        if not isinstance(blocks, list):
            continue
        for entry in blocks:
            if isinstance(entry, dict) and "path" in entry:
                yield section, entry


def find_duplicates(deps_toml: Path) -> dict[str, list[tuple[str, str]]]:
    """Return composite-key duplicates as (kind, key) → list of label tuples.

    Catches stale entries that were never deleted when a path was
    re-registered (e.g. "w1-deliverable-stub" → "w1-impl-landed-concrete"
    where the older entry should have been removed).

    Cycle 59 addition: prior to this, the verifier only checked that
    each entry's path resolved; if the same path was registered twice,
    both passed. Cycle 59 discovered 25 module path dupes + 12 ADR id
    dupes; cycle 59 cleanup removed 37 stale blocks.
    """
    with deps_toml.open("rb") as f:
        data = tomllib.load(f)
    seen: dict[tuple[str, str], list[tuple[str, str]]] = {}
    # Module path duplicates
    for entry in data.get("modules", []) or []:
        path = str(entry.get("path") or "")
        if not path:
            continue
        clean, _ = _strip_reserved_marker(path)
        adr = str(entry.get("adr") or "")
        key = ("modules", clean)
        seen.setdefault(key, []).append((path, adr))
    # ADR id duplicates
    for entry in data.get("adrs", []) or []:
        aid = str(entry.get("id") or "")
        if not aid:
            continue
        title = str(entry.get("title") or "")[:80]
        key = ("adrs", aid)
        seen.setdefault(key, []).append((aid, title))
    return {f"{k[0]}:{k[1]}": v for k, v in seen.items() if len(v) > 1}


def check_paths(
    deps_toml: Path,
    repo_root: Path,
    *,
    filter_token: Optional[str] = None,
) -> list[PathCheck]:
    """Parse deps.toml and verify every path entry. Returns a flat list."""
    with deps_toml.open("rb") as f:
        data = tomllib.load(f)

    results: list[PathCheck] = []
    for section, entry in _iter_entries(data):
        raw_path = str(entry["path"])
        if filter_token is not None:
            adr_field = str(entry.get("adr") or entry.get("id") or "")
            if filter_token not in adr_field and filter_token not in raw_path:
                continue
        clean_path, marker = _strip_reserved_marker(raw_path)
        resolved = (repo_root / clean_path).resolve()
        # Paths ending in '/' are explicit directory references.
        check = PathCheck(
            section=section,
            path=raw_path,
            exists=resolved.exists(),
            resolved=str(resolved),
            adr=entry.get("adr") if section == "modules" else None,
            id=entry.get("id") if section == "adrs" else None,
            reserved_marker=marker,
        )
        results.append(check)
    return results


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify every deps.toml [[adrs]] / [[modules]] path resolves."
    )
    parser.add_argument(
        "--deps-toml",
        type=Path,
        default=None,
        help="Path to deps.toml (default: <repo_root>/deps.toml).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Path to repo root. Auto-detected if not given.",
    )
    parser.add_argument(
        "--filter",
        dest="filter_token",
        help="Only check entries whose adr/id/path contains this token.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON report instead of human-readable summary.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root
    deps_toml = args.deps_toml
    if repo_root is None:
        # Walk up from this script's directory until we find a deps.toml.
        here = Path(__file__).resolve()
        for cand in [here.parent, *here.parents]:
            if (cand / "deps.toml").is_file():
                repo_root = cand
                break
        if repo_root is None:
            print("verify_deps_toml_paths: cannot find repo root", file=sys.stderr)
            return 2
    if deps_toml is None:
        deps_toml = repo_root / "deps.toml"

    if not deps_toml.is_file():
        print(f"verify_deps_toml_paths: deps.toml not found at {deps_toml}", file=sys.stderr)
        return 2

    try:
        results = check_paths(deps_toml, repo_root, filter_token=args.filter_token)
    except tomllib.TOMLDecodeError as exc:
        print(f"verify_deps_toml_paths: toml parse error: {exc}", file=sys.stderr)
        return 2

    drift = [r for r in results if r.is_drift]
    accepted_missing = [r for r in results if r.is_accepted_missing]
    stale_markers = [r for r in results if r.is_stale_marker]
    n_total = len(results)
    n_ok = sum(1 for r in results if r.exists and r.reserved_marker is None)

    # Duplicate detection (cycle 59) — only runs in unfiltered mode
    # because filtering can legitimately hide a duplicate's twin.
    duplicates = (
        find_duplicates(deps_toml) if args.filter_token is None else {}
    )

    if args.json:
        print(json.dumps({
            "total": n_total,
            "ok": n_ok,
            "drift_count": len(drift),
            "drift": [asdict(d) for d in drift],
            "accepted_missing_count": len(accepted_missing),
            "accepted_missing": [asdict(a) for a in accepted_missing],
            "stale_marker_count": len(stale_markers),
            "stale_markers": [asdict(s) for s in stale_markers],
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
            "filter": args.filter_token,
        }, indent=2))
    else:
        summary_parts = [f"{n_ok}/{n_total} entries resolve"]
        if accepted_missing:
            summary_parts.append(
                f"{len(accepted_missing)} accepted-reserved (owner-asserted)"
            )
        if stale_markers:
            summary_parts.append(
                f"{len(stale_markers)} stale marker(s) — drop the suffix"
            )
        if drift:
            summary_parts.append(f"{len(drift)} drift")
        print("deps.toml path audit: " + " / ".join(summary_parts))

        if accepted_missing:
            print(f"ACCEPTED-RESERVED ({len(accepted_missing)}) — owner-asserted not drift:")
            for a in accepted_missing:
                tag = a.adr or a.id or "—"
                print(f"  [{a.section}] {a.path}  ({tag})")
        if stale_markers:
            print(f"STALE-MARKER ({len(stale_markers)}) — path exists, remove ' ({stale_markers[0].reserved_marker})' suffix:")
            for s in stale_markers:
                tag = s.adr or s.id or "—"
                print(f"  [{s.section}] {s.path}  ({tag})")
        if drift:
            print(f"DRIFT ({len(drift)}) — fix the file or remove the entry:")
            for d in drift:
                tag = d.adr or d.id or "—"
                print(f"  [{d.section}] {d.path}  ({tag})")
        if duplicates:
            print(f"DUPLICATES ({len(duplicates)}) — same key registered multiple times:")
            for k, occurrences in duplicates.items():
                print(f"  {k}: {len(occurrences)} entries")
        if not drift and not stale_markers and not duplicates:
            print("No drift. Clean.")

    # Exit 1 only on real drift OR duplicates; stale markers +
    # accepted-reserved are warnings.
    return 1 if (drift or duplicates) else 0


if __name__ == "__main__":
    raise SystemExit(main())
