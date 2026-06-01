#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Validate in-repo markdown links in 90-docs/**/*.md.

Catches broken in-repo links — markdown body references to paths that
don't exist. Distinct from cycle 60's relation integrity which checks
YAML frontmatter relation fields.

Resolves 3 link styles:
  - absolute path (/Users/.../...)              → Path(target).exists()
  - repo-root-relative (/90-docs/...)           → REPO/target.lstrip("/").exists()
  - file-relative (./foo.md / ../bar.md / foo.md) → (md.parent/target).resolve().exists()

Skips:
  - URLs (http://, https://, mailto:, etc.)
  - Anchor-only (#section)
  - Scheme-prefixed (foo:bar)

Cycle 67 ships this as 8th-axis NIGHTLY TRACKER (Pattern B from cycles
50/60). Baseline as of cycle 67: 33 broken (down from cycle 66's 86;
cycles 66+67 auto-fixed 56 wrong-absolute-prefix + line-number-suffix
cases). The 33 remaining are mostly truly-broken (target never existed
in repo); cleanup requires manual per-entry judgment.

Usage:
    70-tools/scripts/docs/validate-md-links.py
    70-tools/scripts/docs/validate-md-links.py --json
    70-tools/scripts/docs/validate-md-links.py --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DOCS = REPO / "90-docs"
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
URL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "ftp://")


def find_broken_links() -> list[dict[str, str]]:
    """Scan every 90-docs/**/*.md for broken in-repo markdown links."""
    broken: list[dict[str, str]] = []
    for md in DOCS.rglob("*.md"):
        if any(skip in md.parts for skip in ("_registry", ".git", "datasets")):
            continue
        if md.name == "CLAUDE.md":
            continue
        if not md.is_file():
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in LINK_RE.finditer(text):
            target = m.group(2)
            if target.startswith(URL_PREFIXES) or target.startswith("#"):
                continue
            if ":" in target.split("/")[0]:
                # Scheme-prefixed (e.g., 'app:foo')
                continue
            path_part = target.split("#")[0]
            if not path_part:
                continue
            # Resolve based on path style
            if path_part.startswith("/Users/"):
                full = Path(path_part)
            elif path_part.startswith("/"):
                full = REPO / path_part.lstrip("/")
            else:
                full = (md.parent / path_part).resolve()
            if not full.exists():
                broken.append({
                    "source": str(md.relative_to(REPO)),
                    "target": target,
                    "link_text": m.group(1)[:80],
                })
    return broken


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--json", action="store_true", help="emit JSON output")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any broken link")
    args = ap.parse_args()

    broken = find_broken_links()
    result = {"total_broken": len(broken), "broken": broken}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"md-links: {len(broken)} broken in-repo links")
        if broken:
            print()
            print("Baseline as of cycle 67 (2026-05-27): 33 known broken")
            print("  (cycle 66 auto-fixed 54 wrong-absolute-prefix; cycle 67 auto-fixed")
            print("   2 line-number-suffix; remaining 33 are truly-broken or require")
            print("   manual judgment).")
            print()
            print("Tracker mode — exit 0 by default. Run with --strict to enforce.")
            for b in broken[:10]:
                print(f"  {b['source'][:50]}  →  {b['target'][:80]}")
            if len(broken) > 10:
                print(f"  ... and {len(broken)-10} more")

    if args.strict:
        return 0 if not broken else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
