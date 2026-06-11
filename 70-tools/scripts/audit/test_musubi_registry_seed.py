"""Fail-closed invariants test for the musubi (結) WORLDWIDE ceremony-recognition seed registry.

Pins the constitutional invariants of
`20-actors/musubi/registry/ceremony-recognition.seed.json` (ADR-2605263400) so a
future edit cannot silently weaken them. musubi performs covenant ceremonies
(Reformed 万人祭司, NO clergy class) and does NOT confer civil status; this
registry only maps, INFORMATIONALLY, the SEPARATE civil-registration step a
member must perform themselves. R0-safe: test-only, deterministic, network-free
(no cell execution, no live reliance). Mirrors the style of
test_toritsugi_invariants.py.

Invariants under test (all fail-closed):

  1. File parses as JSON and has a non-empty "recognitions" list.
  2. Every entry has a unique "recognitionId" (no duplicates).
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed).
  4. Every entry has a non-empty https provenance URL and a lastVerified stamp.
  5. Every entry has a "jurisdiction" and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct — proves deep worldwide coverage after the
     long-tail deepening, guards against regression to JP-only).
  6. Boundary caveat present: every entry's "notes" is non-empty AND references
     the informational-only / no-civil-registration / no-advice regime.
  7. A top-level integer "freshnessWindowDays" is present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "musubi" / "registry" / "ceremony-recognition.seed.json"


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. file parses + non-empty recognitions list
# ─────────────────────────────────────────────────────────────────────────


def test_seed_parses_and_has_recognitions():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "seed root MUST be a JSON object"
    recs = seed.get("recognitions")
    assert isinstance(recs, list), "top-level 'recognitions' MUST be a list"
    assert len(recs) > 0, "recognitions list MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique recognitionId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_recognition_ids_unique():
    recs = _load()["recognitions"]
    ids = [r.get("recognitionId") for r in recs]
    for i in ids:
        assert i, "every entry MUST have a non-empty recognitionId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate recognitionId values (fail-closed): {dupes}"
    assert len(set(ids)) == len(ids), "recognitionId values MUST be unique"


# ─────────────────────────────────────────────────────────────────────────
# 3. G14: every entry ships verificationStatus == unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_unverified_seed():
    recs = _load()["recognitions"]
    for r in recs:
        assert r.get("verificationStatus") == "unverified-seed", (
            f"G14: {r.get('recognitionId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified); got "
            f"{r.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. every entry: non-empty https provenance + lastVerified timestamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_and_last_verified():
    recs = _load()["recognitions"]
    for r in recs:
        rid = r.get("recognitionId")
        prov = r.get("provenance") or ""
        assert prov, f"{rid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith("https://"), (
            f"{rid}: provenance MUST be an https source URL; got {prov!r}"
        )
        lv = r.get("lastVerified") or ""
        assert lv, f"{rid}: MUST carry a lastVerified timestamp"
        # tolerant: just require an ISO-8601-ish date-time prefix, not an exact value
        assert lv[:4].isdigit() and "T" in lv, (
            f"{rid}: lastVerified MUST look like an ISO-8601 timestamp; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. jurisdiction present + worldwide coverage (>= 5 distinct)
# ─────────────────────────────────────────────────────────────────────────


def test_worldwide_multiple_jurisdictions():
    recs = _load()["recognitions"]
    for r in recs:
        assert r.get("jurisdiction"), (
            f"{r.get('recognitionId')}: MUST carry a jurisdiction"
        )
    distinct = {r["jurisdiction"] for r in recs}
    assert len(distinct) >= 12, (
        f"worldwide invariant: registry MUST span >= 12 distinct jurisdictions "
        f"(locks in the long-tail deepening; guards against regression to "
        f"JP-only); got {len(distinct)}: {sorted(distinct)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. boundary caveat: per-entry notes non-empty + references the regime
# ─────────────────────────────────────────────────────────────────────────


def test_boundary_caveat_present():
    seed = _load()
    recs = seed["recognitions"]
    # 6a. every entry carries a non-empty notes (boundary text) field.
    for r in recs:
        notes = r.get("notes") or ""
        assert notes.strip(), (
            f"{r.get('recognitionId')}: MUST carry non-empty notes (boundary caveat)"
        )

    # 6b. the registry as a whole references its boundary regime. The seed
    #     standardizes the caveat string across entries + the top-level
    #     _comment. Tolerant: require, for EVERY entry, evidence of all three
    #     regime pillars (informational-only / no civil registration /
    #     no legal advice), matched against the entry's notes.
    for r in recs:
        text = (r.get("notes") or "").lower()
        rid = r.get("recognitionId")
        assert "informational" in text, (
            f"{rid}: notes MUST flag the registry is INFORMATIONAL only"
        )
        # no civil registration / does not confer civil status
        assert ("does not confer civil status" in text) or (
            "never claims to register a civil marriage" in text
        ), f"{rid}: notes MUST disclaim conferring civil status / registration"
        assert "no legal advice" in text or "gives no legal advice" in text, (
            f"{rid}: notes MUST disclaim giving legal advice (UPL boundary)"
        )

    # 6c. the top-level _comment also documents the boundary regime.
    comment = (seed.get("_comment") or "").lower()
    assert comment, "seed MUST carry a top-level _comment documenting the regime"
    assert "not legal advice" in comment or "never live use" in comment, (
        "top-level _comment MUST document the boundary regime "
        "(informational / never live use / not legal advice)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 7. top-level integer freshnessWindowDays
# ─────────────────────────────────────────────────────────────────────────


def test_freshness_window_days_present_int():
    seed = _load()
    fwd = seed.get("freshnessWindowDays")
    assert isinstance(fwd, int) and not isinstance(fwd, bool), (
        f"freshnessWindowDays MUST be a top-level integer; got {fwd!r}"
    )
    assert fwd > 0, f"freshnessWindowDays MUST be positive; got {fwd}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
