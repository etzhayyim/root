"""Fail-closed invariants for the kazaori (風折) WORLDWIDE disaster-agency seed.

Pins the constitutional properties of the multi-jurisdiction civilian
disaster-agency directory (`registry/agencies.seed.json`, per ADR-2605263200).
This suite is R0-safe: test-only, deterministic, network-free — it never
imports/executes a cell and never touches a live channel or agency. It fails
fast (fail-closed) if any constitutional invariant drifts.

Sibling of test_toritsugi_registry_seed.py (which pins the toritsugi
government-procedure seed). Where that suite pinned a procedure registry, THIS
suite pins kazaori's OBSERVATIONAL directory of OFFICIAL public CIVILIAN
disaster-management agencies + early-warning / public-alert systems.

kazaori boundary (re-asserted by these tests): kazaori is a CIVILIAN-ONLY
emergency-coordination substrate; this directory is OBSERVATIONAL only — it
issues no alerts of its own, commands no response, and is NOT an official
emergency service / channel. The directory MUST route to official sources, not
become one.

Invariants under test:

  1. file parses as JSON and exposes a non-empty `agencies` list.
  2. every entry has a UNIQUE `agencyId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed).
  4. every entry has a non-empty accessUrl + provenance (each a valid http(s)
     URL) + a lastVerified ISO-8601 Zulu stamp.
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage.
  6. every entry's `agencyKind` is in the allowed civilian-disaster taxonomy.
  7. every entry's `notes` is non-empty AND references kazaori's CIVILIAN-ONLY /
     observational boundary (per-entry boundary re-assertion).
  8. a top-level integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "kazaori" / "registry" / "agencies.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# Allowed civilian-disaster agency taxonomy (closed set — fail-closed on drift).
_ALLOWED_KINDS = {
    "disaster-management-agency",
    "early-warning-system",
    "official-alert-channel",
    "civilian-relief-coordination",
    "intl-disaster-body",
}


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty agencies list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_agencies():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    agencies = seed.get("agencies")
    assert isinstance(agencies, list), "`agencies` MUST be a list"
    assert len(agencies) > 0, "`agencies` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique agencyId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_agency_ids_unique():
    agencies = _load()["agencies"]
    ids = [a.get("agencyId") for a in agencies]
    assert all(ids), "every entry MUST have a non-empty agencyId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate agencyId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    agencies = _load()["agencies"]
    for a in agencies:
        assert a.get("verificationStatus") == "unverified-seed", (
            f"G14: {a.get('agencyId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified); got "
            f"{a.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. accessUrl + provenance (http(s) URLs) + lastVerified timestamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_access_provenance_and_last_verified():
    agencies = _load()["agencies"]
    for a in agencies:
        aid = a.get("agencyId")

        access = a.get("accessUrl") or ""
        assert access, f"{aid}: MUST carry a non-empty accessUrl"
        assert access.startswith(("https://", "http://")), (
            f"{aid}: accessUrl MUST be an http(s) URL; got {access!r}"
        )

        prov = a.get("provenance") or ""
        assert prov, f"{aid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith(("https://", "http://")), (
            f"{aid}: provenance MUST be an http(s) URL; got {prov!r}"
        )

        lv = a.get("lastVerified") or ""
        assert lv, f"{aid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{aid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 12 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    agencies = _load()["agencies"]
    for a in agencies:
        assert a.get("jurisdiction"), (
            f"{a.get('agencyId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {a["jurisdiction"] for a in agencies}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        f"jurisdictions (guards against regression to a single-country "
        f"directory); got {sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. agencyKind in the allowed civilian-disaster taxonomy
# ─────────────────────────────────────────────────────────────────────────


def test_every_agency_kind_in_allowed_taxonomy():
    agencies = _load()["agencies"]
    for a in agencies:
        kind = a.get("agencyKind")
        assert kind in _ALLOWED_KINDS, (
            f"{a.get('agencyId')}: agencyKind {kind!r} not in allowed "
            f"civilian-disaster taxonomy {sorted(_ALLOWED_KINDS)}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. per-entry notes non-empty + re-assert CIVILIAN-ONLY / observational
#    boundary
# ─────────────────────────────────────────────────────────────────────────


def test_notes_reassert_civilian_only_observational_boundary():
    agencies = _load()["agencies"]
    for a in agencies:
        aid = a.get("agencyId")
        notes = a.get("notes") or ""
        assert notes.strip(), (
            f"{aid}: notes MUST be non-empty (carries the per-entry boundary "
            "re-assertion)"
        )
        assert "CIVILIAN-ONLY" in notes, (
            f"{aid}: notes MUST re-assert the kazaori CIVILIAN-ONLY boundary"
        )
        assert "OBSERVATIONAL" in notes, (
            f"{aid}: notes MUST state this is an OBSERVATIONAL directory "
            "(not an official channel/target-list)"
        )

    # Registry-as-a-whole references its civilian-only observational regime.
    blob = _SEED.read_text()
    assert "CIVILIAN-ONLY" in blob, (
        "registry MUST reference its CIVILIAN-ONLY boundary"
    )
    assert "ADR-2605263200" in blob, (
        "registry MUST cite its governing ADR-2605263200"
    )


# ─────────────────────────────────────────────────────────────────────────
# 8. top-level integer freshnessWindowDays
# ─────────────────────────────────────────────────────────────────────────


def test_freshness_window_days_present_integer():
    seed = _load()
    fw = seed.get("freshnessWindowDays")
    assert isinstance(fw, int) and not isinstance(fw, bool), (
        f"freshnessWindowDays MUST be a top-level integer; got {fw!r}"
    )
    assert fw > 0, f"freshnessWindowDays MUST be positive; got {fw}"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
