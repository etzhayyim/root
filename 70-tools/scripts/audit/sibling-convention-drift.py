#!/usr/bin/env python3
"""
sibling-convention-drift.py — find @etzhayyim/* package.json files that
are missing standard fields used by >=80% of their siblings.

Convention drift is a common monorepo bug: a sibling-class of packages
develops a shared convention (publishConfig + GH Packages registry,
license, repository, engines.node, etc.) over time, but newer packages
get added without it. The omission may be deliberate (e.g., private =
true intentionally skips publishConfig) or accidental — but accidental
omissions are *distribution-blocking* bugs that don't surface until
someone tries to publish or install.

History:
  - iter-36 of /loop (2026-05-27): the SDK was missing publishConfig
    while every sibling @etzhayyim/* package had a standard 2-field
    block ({access: public, registry: npm.pkg.github.com}). Fixed in
    commit 488021b6e.
  - this script codifies the audit pattern.

Heuristic:

  1. Enumerate all package.json files declaring `name: "@etzhayyim/*"`.
  2. For each top-level field of interest (CHECK_FIELDS below), count
     how many siblings have it.
  3. If coverage >= 80% (i.e., the field is "the convention"), report
     the <20% of packages that are missing it.
  4. Exclude packages with `private: true` (those don't intend to
     publish, so publishConfig + license are not load-bearing).

Usage:
  python3 70-tools/scripts/audit/sibling-convention-drift.py
  python3 70-tools/scripts/audit/sibling-convention-drift.py --strict

Returns: count of outlier-packages × missing-fields pairs via stdout.
Exit code 0 unless --strict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


# Fields whose presence/absence in siblings the script audits.
# Each field's "coverage" is the fraction of @etzhayyim/* package.json
# files that declare it; "outliers" are packages missing a field that
# >=80% of siblings have.
CHECK_FIELDS = [
    "publishConfig",
    "license",
    "repository",
    "engines",
    "description",
]


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    strict = "--strict" in sys.argv

    # Discover package.json files via `git ls-files` (~25 ms) instead
    # of pathlib.rglob (~9 s including walking node_modules + dist +
    # build trees that we'd then explicitly skip). git honours
    # .gitignore for free, so the per-path filter list shrinks too.
    # Same perf pattern applied to e7m verify (iter-5/6/7) and the
    # subrepo audits (iter-57).
    import subprocess
    try:
        ls_out = subprocess.check_output(
            ["git", "-C", str(repo), "ls-files", "*package.json"],
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Fallback to rglob if git isn't available (rare; pre-clone).
        ls_out = "\n".join(
            str(p.relative_to(repo)) for p in repo.rglob("package.json")
        )

    pkgs: list[tuple[Path, dict]] = []
    for rel in ls_out.splitlines():
        if not rel:
            continue
        pkg_path = repo / rel
        try:
            pkg = json.loads(pkg_path.read_text())
        except Exception:
            continue
        name = pkg.get("name", "")
        if not isinstance(name, str) or not name.startswith("@etzhayyim/"):
            continue
        # Skip explicitly-private packages — they don't intend to publish,
        # so the publishConfig + license expectations don't apply.
        if pkg.get("private") is True:
            continue
        pkgs.append((pkg_path.relative_to(repo), pkg))

    total = len(pkgs)
    if total == 0:
        print("no @etzhayyim/* publish-eligible packages found")
        return 0

    # Compute coverage per field
    coverage: dict[str, set[Path]] = {f: set() for f in CHECK_FIELDS}
    for path, pkg in pkgs:
        for f in CHECK_FIELDS:
            if pkg.get(f) is not None:
                coverage[f].add(path)

    THRESHOLD = 0.80
    outliers: list[tuple[Path, str, float]] = []  # (package_path, missing_field, sibling_coverage_pct)
    for field, present in coverage.items():
        pct = len(present) / total
        if pct < THRESHOLD:
            continue
        # >= 80% of siblings have this field; the <20% missing it are outliers
        for path, _ in pkgs:
            if path not in present:
                outliers.append((path, field, pct))

    # Sort by field, then by path
    outliers.sort(key=lambda x: (x[1], str(x[0])))

    print(f"@etzhayyim/* publish-eligible packages scanned: {total}")
    print(f"convention-drift outliers (field has >=80% coverage but this package lacks it): {len(outliers)}")
    print()
    for path, field, pct in outliers:
        print(f"  {path}: missing `{field}` (sibling coverage: {pct:.0%})")

    return 1 if strict and outliers else 0


if __name__ == "__main__":
    sys.exit(main())
