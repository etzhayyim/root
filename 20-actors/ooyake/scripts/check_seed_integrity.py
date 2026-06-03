#!/usr/bin/env python3
"""check_seed_integrity.py — ooyake registry integrity guard (ADR-2606021600 §4/§5).

Institutionalizes the lesson of the 2026-06-03 QID-fabrication finding (see
MATURITY.md § "QID integrity fix"): a contiguous fake Wikidata block had been
hand-entered for the JP ministries — MOF's "Q1023766" actually resolved to *CIUTI*,
a Brussels translators' association, and MOF + MEXT shared the same fake QID. This
checker fails CI/pre-commit on the structural tells of that class of bug so it
cannot silently recur.

Checks (each a hard ERROR unless noted):
  1. duplicate :gov.unit/wikidata across distinct units      (the MOF/MEXT tell)
  2. malformed Wikidata QID (must match ^Q[1-9][0-9]*$)
  3. G5: every unit carries :gov.unit/{sourcing,provenance,last-verified}
  4. authority-reference :wikidata / :official-url must AGREE with the seed unit
     (a mismatch means the bundled "verification" is circular/stale)
  5. authority-reference record pointing at a non-existent unit (dangling)

This is READ-ONLY (G9): it inspects committed registry files, never writes.

Usage:
    python3 check_seed_integrity.py            # human report, exit 1 on any ERROR
    python3 check_seed_integrity.py --quiet     # only print on failure
"""
from __future__ import annotations

import os
import re
import sys

# reuse the single-source EDN reader + loaders from the reconcile cell
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(_HERE, "..", "cells", "reconcile")))
from cell import DEFAULT_AUTH_FILE, DEFAULT_SEED_FILES, load_authority, load_units  # noqa: E402

_QID_RE = re.compile(r"^Q[1-9][0-9]*$")
_G5_REQUIRED = (":gov.unit/sourcing", ":gov.unit/provenance", ":gov.unit/last-verified")


def check(seed_files=None, auth_file=None) -> list[str]:
    """Return a list of ERROR strings. Empty list == clean."""
    units = load_units(seed_files or DEFAULT_SEED_FILES)
    auth = load_authority(auth_file or DEFAULT_AUTH_FILE)
    errors: list[str] = []

    # 1 + 2 — QID uniqueness + format
    seen: dict[str, str] = {}
    for uid, u in sorted(units.items()):
        qid = u.get(":gov.unit/wikidata")
        if qid is None:
            continue
        if not _QID_RE.match(qid):
            errors.append(f"[malformed-qid] {uid}: {qid!r} is not a valid Wikidata QID")
        if qid in seen:
            errors.append(
                f"[duplicate-qid] {qid} used by BOTH {seen[qid]} and {uid} "
                f"(two government bodies cannot share one Wikidata entity)"
            )
        else:
            seen[qid] = uid

    # 3 — G5 provenance discipline
    for uid, u in sorted(units.items()):
        for key in _G5_REQUIRED:
            if not u.get(key):
                errors.append(f"[g5-missing] {uid}: missing {key} (provenance discipline)")

    # 4 + 5 — authority-reference consistency
    for unit_id, rec in sorted(auth.items()):
        u = units.get(unit_id)
        if u is None:
            errors.append(f"[dangling-authority] authority record for unknown unit {unit_id!r}")
            continue
        if u.get(":gov.unit/wikidata") != rec.get(":wikidata"):
            errors.append(
                f"[authority-qid-mismatch] {unit_id}: seed={u.get(':gov.unit/wikidata')!r} "
                f"authority={rec.get(':wikidata')!r} (circular/stale 'verification')"
            )
        if u.get(":gov.unit/official-url") != rec.get(":official-url"):
            errors.append(
                f"[authority-url-mismatch] {unit_id}: seed={u.get(':gov.unit/official-url')!r} "
                f"authority={rec.get(':official-url')!r}"
            )
    return errors


def main() -> int:
    quiet = "--quiet" in sys.argv
    errors = check()
    units = load_units(DEFAULT_SEED_FILES)
    n_qid = sum(1 for u in units.values() if u.get(":gov.unit/wikidata"))
    if errors:
        print("ooyake seed integrity: FAIL")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"  ({len(errors)} error(s); {len(units)} units, {n_qid} with QIDs)")
        return 1
    if not quiet:
        print("ooyake seed integrity: OK")
        print(f"  {len(units)} units, {n_qid} with Wikidata QIDs — all unique + well-formed,")
        print("  authority-reference agrees with seed, G5 provenance present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
