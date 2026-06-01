#!/usr/bin/env python3
"""
sdk-exports-dist.py — find `package.json` subpath-export targets that
don't exist in `dist/` (or wherever the target path resolves to).

Modern npm packages declare a multi-condition `exports` map per
subpath:

  "./genko/components": {
    "types":   "./dist/genko/components/index.d.ts",
    "svelte":  "./dist/genko/components/NodeTree.svelte",
    "default": "./dist/genko/components/NodeTree.svelte"
  }

When the build script (svelte-package / tsc / etc.) doesn't generate
one of those targets, TypeScript and bundlers silently fall back to
`default`-derived types or emit `any` — both are regressions relative
to having a working `types` pointer.

History:
  - iter-26 of /loop (2026-05-26): the SDK's `./genko/components`
    `types` target pointed at `./dist/genko/components/index.d.ts`
    that didn't exist (svelte-package never generated it because
    there's no `src/lib/genko/components/index.ts` to compile from);
    fixed iter-27 commit 66feacc5f to point at the actual
    NodeTree.svelte.d.ts
  - this script codifies the audit pattern

Usage:
  python3 70-tools/scripts/audit/sdk-exports-dist.py
  python3 70-tools/scripts/audit/sdk-exports-dist.py <pkg-dir>
  python3 70-tools/scripts/audit/sdk-exports-dist.py <pkg-dir> --strict

Default pkg-dir is `40-engine/kami-engine/kami-engine-sdk` (the SDK
this script was originally written against). Pass any other package
root as the first arg to audit a different package.

Returns: count of missing exports targets via stdout. Exit code 0
unless --strict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    args = [a for a in sys.argv[1:] if a != "--strict"]
    strict = "--strict" in sys.argv
    pkg_dir = repo / (args[0] if args else "40-engine/kami-engine/kami-engine-sdk")
    pkg_json = pkg_dir / "package.json"
    if not pkg_json.exists():
        # No package.json — e.g. the package is a git-submodule that wasn't
        # initialised (kami-engine-sdk, ADR-2606011500). Nothing to audit, but
        # the aggregator (all.sh) keys on a trailing `: <int>` summary line, so
        # emit one (0 findings) rather than silently producing no stdout.
        print(f"  (no package.json at {pkg_dir.relative_to(repo)} — submodule not checked out?)", file=sys.stderr)
        print(f"missing dist/ targets in {pkg_dir.relative_to(repo)}: 0")
        return 0

    pkg = json.loads(pkg_json.read_text())
    exports = pkg.get("exports") or {}
    missing: list[tuple[str, str, str]] = []

    # Export targets resolve into the build output (`dist/`), which is
    # git-ignored. When the package hasn't been built (no `dist/`), EVERY
    # target is trivially "missing", so the audit is only meaningful AFTER a
    # build. Skip pre-build so it's a no-op on a fresh checkout (e.g. CI
    # without `npm run build`) and still catches genuine dist-target
    # mismatches once a build is present.
    dist_dir = pkg_dir / "dist"
    if dist_dir.exists():
        for subpath, dispatch in exports.items():
            # exports values can be a string (legacy single-target) or a dict
            # of condition → target.
            if isinstance(dispatch, str):
                f = pkg_dir / dispatch.lstrip("./")
                if not f.exists():
                    missing.append((subpath, "default", dispatch))
            elif isinstance(dispatch, dict):
                for cond, target in dispatch.items():
                    if not isinstance(target, str):
                        continue
                    f = pkg_dir / target.lstrip("./")
                    if not f.exists():
                        missing.append((subpath, cond, target))
    else:
        print("  (dist/ not built — export targets not audited)", file=sys.stderr)

    print(f"missing dist/ targets in {pkg_dir.relative_to(repo)}: {len(missing)}")
    for subpath, cond, target in missing:
        print(f"  {subpath} [{cond}]: {target}")

    return 1 if strict and missing else 0


if __name__ == "__main__":
    sys.exit(main())
