"""Fail-closed constitutional-invariants tests for the kurashimori (暮らし守)
WORLDWIDE consumer-remedy seed registry.

Pins the structural / honesty properties of
`20-actors/kurashimori/registry/targets.seed.json` (per ADR-2605312500 §4) so a
future edit cannot silently weaken a constitutional invariant. R0-safe:
test-only, network-free, no cell execution, no live send. Mirrors the repo
pytest style of test_toritsugi_invariants.py.

Invariants under test:

  1. file parses as JSON and has a non-empty "targets" list + a top-level
     integer "freshnessWindowDays".
  2. every entry has a UNIQUE "remedyId" (no duplicates) — fail-closed.
  3. G14: EVERY entry ships verificationStatus == "unverified-seed"
     (no seed entry may be pre-marked verified).
  4. every entry has a non-empty https provenance/source URL + a "lastVerified"
     timestamp.
  5. every entry has a "jurisdiction"; the registry spans MULTIPLE jurisdictions
     (>= 12 distinct values — proves long-tail worldwide coverage, guards
     against regression to JP-only / shallow-bloc-only).
  6. G5/UPL boundary caveat is present: every entry's "notes" is non-empty, and
     the registry references its 弁護士法 / 司法書士法 / UPL boundary regime.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "kurashimori" / "registry" / "targets.seed.json"


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses as JSON, non-empty targets list, integer freshnessWindowDays
# ─────────────────────────────────────────────────────────────────────────


def test_parses_and_has_targets_and_freshness_window():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    reg = _load()
    targets = reg.get("targets")
    assert isinstance(targets, list), "top-level 'targets' MUST be a list"
    assert len(targets) > 0, "'targets' MUST be non-empty"

    fw = reg.get("freshnessWindowDays")
    assert isinstance(fw, int) and not isinstance(fw, bool), (
        "freshnessWindowDays MUST be a top-level integer"
    )
    assert fw > 0, "freshnessWindowDays MUST be positive"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique remedyId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_remedy_ids_unique():
    targets = _load()["targets"]
    ids = [t.get("remedyId") for t in targets]
    assert all(ids), "every entry MUST have a non-empty remedyId"
    dupes = sorted({rid for rid in ids if ids.count(rid) > 1})
    assert not dupes, f"duplicate remedyId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed (no pre-marked verified entry)
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_unverified_seed():
    for t in _load()["targets"]:
        assert t.get("verificationStatus") == "unverified-seed", (
            f"G14: {t.get('remedyId')} MUST ship verificationStatus=unverified-seed"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. provenance (https) + lastVerified on every entry
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_and_last_verified():
    for t in _load()["targets"]:
        rid = t.get("remedyId")
        prov = t.get("provenance") or ""
        assert prov, f"{rid} MUST cite a non-empty provenance/source URL"
        assert prov.startswith("https://"), (
            f"{rid} provenance MUST be an https URL; got {prov!r}"
        )
        lv = t.get("lastVerified") or ""
        assert lv, f"{rid} MUST carry a lastVerified timestamp"
        # ISO-8601 Zulu shape (e.g. 2026-06-02T00:00:00Z) — date + time.
        assert "T" in lv and lv.endswith("Z"), (
            f"{rid} lastVerified MUST be an ISO-8601 Z timestamp; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. jurisdiction present + worldwide coverage (>= 5 distinct)
# ─────────────────────────────────────────────────────────────────────────


def test_jurisdiction_present_and_worldwide():
    targets = _load()["targets"]
    jurs = [t.get("jurisdiction") for t in targets]
    assert all(jurs), "every entry MUST carry a 'jurisdiction'"
    distinct = set(jurs)
    assert len(distinct) >= 12, (
        "registry MUST span >= 12 distinct jurisdictions (long-tail worldwide "
        "coverage; guards against JP-only / shallow-bloc-only regression); "
        f"got {sorted(distinct)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. G5/UPL boundary caveat present per-entry + registry-wide regime reference
# ─────────────────────────────────────────────────────────────────────────


def test_boundary_caveat_present():
    reg = _load()
    targets = reg["targets"]

    # Per-entry: notes is the boundary/caveat text field; must be non-empty.
    for t in targets:
        notes = t.get("notes") or ""
        assert notes.strip(), f"{t.get('remedyId')} MUST carry non-empty notes"

    # Registry-wide: the 弁護士法 / 司法書士法 / UPL boundary regime must be
    # referenced (in entry notes and/or the top-level _comment). Tolerant: pass
    # if ANY of the regime tokens appears across the registry text.
    blob = _SEED.read_text()
    regime_tokens = ("弁護士法", "司法書士法", "UPL")
    assert any(tok in blob for tok in regime_tokens), (
        "registry MUST reference its 弁護士法 / 司法書士法 / UPL boundary regime"
    )
    # And the boundary must be asserted on the entries themselves, not only in a
    # single comment: at least most entries restate the regime in notes.
    with_regime = sum(
        1
        for t in targets
        if any(tok in (t.get("notes") or "") for tok in regime_tokens)
    )
    assert with_regime >= len(targets) // 2, (
        "the UPL/弁護士法/司法書士法 boundary caveat must appear in entry notes, "
        f"not only a top-level comment; only {with_regime}/{len(targets)} carry it"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
