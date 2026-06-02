"""Fail-closed invariants for the hagukumi (育み) WORLDWIDE care-support seed registry.

Pins the constitutional properties of the multi-jurisdiction care-support
directory (`registry/programs.seed.json`, per ADR-2605261030). This suite is
R0-safe: test-only, deterministic, network-free — it never imports/executes a
hagukumi cell (those raise RuntimeError on import by design) and never touches a
live channel or care session. It fails fast (fail-closed) if any constitutional
invariant drifts.

Sibling of test_toritsugi_registry_seed.py (which pins the toritsugi procedure
registry). Where toritsugi enforces a 行政書士法/UPL boundary, THIS suite enforces
hagukumi's no-eligibility-determination + non-provider boundary on the registry
data itself: hagukumi is a community CARE substrate (Liberation Ladder L4 Care),
NOT a licensed care provider and NOT a benefits-determination service. The
directory routes families to OFFICIAL public care-support programs and makes NO
eligibility or benefit determination (eligibility + amounts vary by case and
drift — confirm with the authority).

Invariants under test:

  1. file parses as JSON and exposes a non-empty `programs` list.
  2. every entry has a UNIQUE `programId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed).
  4. every entry has a non-empty accessUrl + provenance + lastVerified; URLs are
     http(s) (note: today every URL is https — the test allows http only so a
     legitimate http-only official source is surfaced, never masked).
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage / guards against
     regression to JP-only.
  6. every entry's `careKind` is one of the allowed care taxonomy values.
  7. every entry's `notes` is non-empty AND re-states hagukumi's
     no-eligibility-determination + non-provider boundary.
  8. a top-level integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "hagukumi" / "registry" / "programs.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# Allowed care taxonomy (per ADR-2605261030 — child + elder + family + intl).
_ALLOWED_CARE_KINDS = {
    "child-allowance",
    "parental-leave",
    "childcare-subsidy",
    "elder-care-benefit",
    "disability-care-support",
    "family-support-service",
    "intl-reference",
}


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty programs list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_programs():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    progs = seed.get("programs")
    assert isinstance(progs, list), "`programs` MUST be a list"
    assert len(progs) > 0, "`programs` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique programId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_program_ids_unique():
    progs = _load()["programs"]
    ids = [p.get("programId") for p in progs]
    assert all(ids), "every entry MUST have a non-empty programId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate programId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    progs = _load()["programs"]
    for p in progs:
        assert p.get("verificationStatus") == "unverified-seed", (
            f"G14: {p.get('programId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified); got "
            f"{p.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. non-empty accessUrl + provenance + lastVerified
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_access_provenance_and_last_verified():
    progs = _load()["programs"]
    for p in progs:
        pid = p.get("programId")

        access = (p.get("accessUrl") or "").strip()
        assert access, f"{pid}: MUST cite a non-empty accessUrl"
        assert access.startswith(("https://", "http://")), (
            f"{pid}: accessUrl MUST be an http(s) URL; got {access!r}"
        )

        prov = (p.get("provenance") or "").strip()
        assert prov, f"{pid}: MUST cite a non-empty provenance/source URL"
        # provenance may carry a corroboration trail after the leading URL, so
        # only the leading token must be an http(s) source. http allowed (not
        # masked) so a legitimate http-only official source is surfaced.
        assert prov.startswith(("https://", "http://")), (
            f"{pid}: provenance MUST begin with an http(s) source URL; got "
            f"{prov!r}"
        )

        lv = (p.get("lastVerified") or "").strip()
        assert lv, f"{pid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{pid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 12 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    progs = _load()["programs"]
    for p in progs:
        assert p.get("jurisdiction"), (
            f"{p.get('programId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {p["jurisdiction"] for p in progs}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        "jurisdictions (guards against regression to JP-only); got "
        f"{sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. careKind in allowed taxonomy
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_care_kind_in_taxonomy():
    progs = _load()["programs"]
    for p in progs:
        ck = p.get("careKind")
        assert ck in _ALLOWED_CARE_KINDS, (
            f"{p.get('programId')}: careKind MUST be one of "
            f"{sorted(_ALLOWED_CARE_KINDS)}; got {ck!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. no-eligibility-determination + non-provider boundary in every notes
# ─────────────────────────────────────────────────────────────────────────


def test_boundary_caveat_present_in_every_notes():
    seed = _load()
    progs = seed["programs"]
    for p in progs:
        notes = (p.get("notes") or "")
        assert notes.strip(), (
            f"{p.get('programId')}: notes MUST be non-empty (carries the "
            "per-entry boundary caveat)"
        )
        low = notes.lower()
        # no-eligibility-determination boundary
        assert "no eligibility or benefit determination" in low, (
            f"{p.get('programId')}: notes MUST re-state the "
            "no-eligibility/benefit-determination boundary"
        )
        # non-provider boundary
        assert "not a licensed care provider" in low, (
            f"{p.get('programId')}: notes MUST re-state the non-provider "
            "(NOT a licensed care provider) boundary"
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
