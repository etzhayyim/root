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
  0 — all paths resolve
  1 — at least one missing path
  2 — usage / parse error

Honest scoring per Charter Rider §G10 / ADR-2605261600 §G10: no
threshold-juggling — every missing path is a real audit-trail
defect. Add the missing file, or remove the deps.toml entry.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Optional


@dataclass
class PathCheck:
    section: str              # "adrs" | "modules"
    path: str                 # raw entry from deps.toml
    exists: bool
    resolved: str             # absolute resolved path (for diagnostics)
    adr: Optional[str] = None    # ADR ref (when present in the [[modules]] block)
    id: Optional[str] = None     # ADR id (when section=="adrs")


def _iter_entries(data: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield ('adrs', entry) and ('modules', entry) blocks from deps.toml."""
    for section in ("adrs", "modules"):
        blocks = data.get(section)
        if not isinstance(blocks, list):
            continue
        for entry in blocks:
            if isinstance(entry, dict) and "path" in entry:
                yield section, entry


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
        resolved = (repo_root / raw_path).resolve()
        # Paths ending in '/' are explicit directory references.
        check = PathCheck(
            section=section,
            path=raw_path,
            exists=resolved.exists(),
            resolved=str(resolved),
            adr=entry.get("adr") if section == "modules" else None,
            id=entry.get("id") if section == "adrs" else None,
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

    missing = [r for r in results if not r.exists]
    n_total = len(results)
    n_ok = n_total - len(missing)

    if args.json:
        print(json.dumps({
            "total": n_total,
            "ok": n_ok,
            "missing_count": len(missing),
            "missing": [asdict(m) for m in missing],
            "filter": args.filter_token,
        }, indent=2))
    else:
        print(f"deps.toml path audit: {n_ok}/{n_total} entries resolve")
        if missing:
            print(f"MISSING ({len(missing)}):")
            for m in missing:
                tag = m.adr or m.id or "—"
                print(f"  [{m.section}] {m.path}  ({tag})")
        else:
            print("All paths resolve. Clean.")

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
