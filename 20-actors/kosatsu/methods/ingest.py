"""ingest.py — 高札 (kosatsu) offline designation membrane. ADR-2606072000.

Normalizes an authority's PUBLIC designation export (a list of {asserter, subject, measure,
program, status, posted_at, sources}) into validated `:designation/*` datoms ready for the
kotoba Datom log. EVERY normalized record passes the same G1..G5/G10 gates as the seed
(weave.validate_*), so a verdict measure, an asserter-less or etzhayyim-authored designation, a
non-primary or under-sourced citation, or a missing attribution NOTICE is refused here too.

`--live` is REFUSED without the G8 gate (Council Lv6+ + operator + member signature). At R0 this
is an OFFLINE normalizer only: it reads a local JSON file and prints the datoms it WOULD assert.
It never fetches a remote list and never writes to the log.

Stdlib only. Deterministic.
"""

from __future__ import annotations

import json
import sys

from weave import (validate_authority, validate_designation, validate_subject)


def normalize_designation(rec: dict) -> dict:
    """Map a plain ingest record → a `:designation/*` datom, then VALIDATE it (raises on a gate)."""
    d = {
        ":designation/id": rec["id"],
        ":designation/asserter": rec["asserter"],
        ":designation/subject": rec["subject"],
        ":designation/measure": rec["measure"] if str(rec["measure"]).startswith(":") else ":" + rec["measure"],
        ":designation/program": rec.get("program", "(unspecified)"),
        ":designation/status": rec.get("status", ":listed") if str(rec.get("status", "listed")).startswith(":") else ":" + rec.get("status", "listed"),
        ":designation/posted-at": int(rec["posted_at"]),
        ":designation/asserted-notice": True,
        ":designation/sourcing": rec.get("sourcing", ":representative") if str(rec.get("sourcing", "representative")).startswith(":") else ":" + rec.get("sourcing", "representative"),
        ":designation/sources": list(rec.get("sources", [])),
    }
    if "lifted_at" in rec and rec["lifted_at"] is not None:
        d[":designation/lifted-at"] = int(rec["lifted_at"])
    validate_designation(d)
    return d


def normalize_authority(rec: dict) -> dict:
    a = {
        ":authority/id": rec["id"],
        ":authority/kind": rec["kind"] if str(rec["kind"]).startswith(":") else ":" + rec["kind"],
        ":authority/label": rec.get("label", rec["id"]),
        ":authority/jurisdiction": rec.get("jurisdiction", "?"),
        ":authority/stance": rec["stance"],
        ":authority/sourcing": rec.get("sourcing", ":representative") if str(rec.get("sourcing", "representative")).startswith(":") else ":" + rec.get("sourcing", "representative"),
        ":authority/sources": list(rec.get("sources", [])),
    }
    validate_authority(a)
    return a


def normalize_subject(rec: dict) -> dict:
    s = {
        ":subject/id": rec["id"],
        ":subject/kind": rec["kind"] if str(rec["kind"]).startswith(":") else ":" + rec["kind"],
        ":subject/label": rec.get("label", rec["id"]),
        ":subject/jurisdiction": rec.get("jurisdiction", "(rep)"),
        ":subject/sourcing": rec.get("sourcing", ":representative") if str(rec.get("sourcing", "representative")).startswith(":") else ":" + rec.get("sourcing", "representative"),
    }
    validate_subject(s)
    return s


def ingest_file(path: str) -> dict:
    """Read a local JSON {authorities, subjects, designations}; normalize+validate each. Offline."""
    raw = json.loads(open(path, encoding="utf-8").read())
    out = {
        "authorities": [normalize_authority(a) for a in raw.get("authorities", [])],
        "subjects": [normalize_subject(s) for s in raw.get("subjects", [])],
        "designations": [normalize_designation(d) for d in raw.get("designations", [])],
    }
    return out


def main(argv: list[str]) -> int:
    if "--live" in argv:
        sys.stderr.write(
            "REFUSED: live designation ingest is G8-gated (Council Lv6+ + operator + member "
            "signature). kosatsu R0 is an OFFLINE normalizer only — pass a local JSON path.\n"
        )
        return 2
    if len(argv) < 2:
        sys.stderr.write("usage: python3 ingest.py <designations.json>   (offline only; --live is refused)\n")
        return 1
    out = ingest_file(argv[1])
    print(f"# normalized {len(out['authorities'])} authorities, {len(out['subjects'])} subjects, "
          f"{len(out['designations'])} designations (offline, NOT written to the log)")
    for d in out["designations"]:
        print(d[":designation/id"], d[":designation/asserter"], "→", d[":designation/subject"],
              d[":designation/measure"], d[":designation/status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
