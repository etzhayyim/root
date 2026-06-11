#!/usr/bin/env python3
"""
dependabot-defunct.py — find `.github/dependabot.yml` `directory:` entries
pointing at paths that don't exist in the working tree.

GitHub Actions' dependabot silently no-ops on missing directories — weekly
runs fail without surfacing an error to humans. Removing defunct entries
reduces background noise and keeps the configuration honest about which
package ecosystems the repo actually tracks.

History:
  - iter-18 of /loop (2026-05-26): retired 20-actors/kami-engine-sdk
    dependabot entry post Phase 3 directory deletion (ADR-2605265200)
  - iter-23 of /loop (2026-05-26): the same audit pattern surfaced 7
    more defunct entries — Foundry-vendored-lib subpath entries under
    50-infra/etzhayyim-paymaster/lib/* that dependabot cannot scan
    (submodule subpaths) and that didn't exist on disk anyway
  - this script codifies that pattern as a reusable audit tool

Usage:
  python3 70-tools/scripts/audit/dependabot-defunct.py
  python3 70-tools/scripts/audit/dependabot-defunct.py --strict   # exit 1 on findings

Returns: count of defunct entries via stdout. Exit code 0 unless --strict.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[3]  # /Users/.../etzhayyim-root
    config = repo / ".github/dependabot.yml"
    if not config.exists():
        print(f"missing: {config}", file=sys.stderr)
        return 0

    strict = "--strict" in sys.argv

    content = config.read_text()
    defunct: list[tuple[int, str]] = []
    for m in re.finditer(r'^\s*directory:\s*"(.+?)"', content, re.M):
        path = m.group(1).lstrip("/")
        if not (repo / path).exists():
            line_no = content[: m.start()].count("\n") + 1
            defunct.append((line_no, path))

    print(f"dependabot defunct entries: {len(defunct)}")
    for ln, p in defunct:
        print(f"  line {ln}: /{p}")

    return 1 if strict and defunct else 0


if __name__ == "__main__":
    sys.exit(main())
