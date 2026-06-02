"""Fail-closed invariants for the toritsugi (取次) WORLDWIDE seed registry.

Pins the constitutional properties of the multi-jurisdiction
government-procedure seed registry (`registry/procedures.seed.json`, per
ADR-2605312030 §2, expanded 2026-06-02 from JP-only to worldwide). This suite is
R0-safe: test-only, deterministic, network-free — it never imports/executes a
cell and never touches a live channel. It fails fast (fail-closed) if any
constitutional invariant drifts.

Sibling of test_toritsugi_invariants.py (which pins the lexicon/manifest/cell
shape). Where that suite enforced a JP-only .go.jp provenance rule, THIS suite
enforces the worldwide-coverage invariants on the registry data itself.

Invariants under test:

  1. file parses as JSON and exposes a non-empty `procedures` list.
  2. every entry has a UNIQUE `procedureId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed).
  4. every entry has a non-empty https provenance URL + a lastVerified stamp.
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage / guards against
     regression to JP-only.
  6. G5 行政書士法/UPL boundary caveat is present: every entry's `notes` is
     non-empty, and the registry as a whole references its UPL boundary regime.
  7. a top-level integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "toritsugi" / "registry" / "procedures.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty procedures list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_procedures():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    procs = seed.get("procedures")
    assert isinstance(procs, list), "`procedures` MUST be a list"
    assert len(procs) > 0, "`procedures` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique procedureId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_procedure_ids_unique():
    procs = _load()["procedures"]
    ids = [p.get("procedureId") for p in procs]
    assert all(ids), "every entry MUST have a non-empty procedureId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate procedureId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    procs = _load()["procedures"]
    for p in procs:
        assert p.get("verificationStatus") == "unverified-seed", (
            f"G14: {p.get('procedureId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified); got "
            f"{p.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. provenance https URL + lastVerified timestamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_and_last_verified():
    procs = _load()["procedures"]
    for p in procs:
        pid = p.get("procedureId")
        prov = p.get("provenance") or ""
        assert prov, f"{pid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith("https://"), (
            f"{pid}: provenance MUST be an https URL; got {prov!r}"
        )
        lv = p.get("lastVerified") or ""
        assert lv, f"{pid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{pid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 5 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    procs = _load()["procedures"]
    for p in procs:
        assert p.get("jurisdiction"), (
            f"{p.get('procedureId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {p["jurisdiction"] for p in procs}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        f"jurisdictions (raised from 5 after the 2026-06-02 long-tail "
        f"deepening to lock in deeper coverage; guards against regression to "
        f"JP-only); got {sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. G5 行政書士法/UPL boundary caveat present
# ─────────────────────────────────────────────────────────────────────────


def test_upl_boundary_caveat_present():
    seed = _load()
    procs = seed["procedures"]
    # Per-entry: a non-empty `notes` text field.
    for p in procs:
        notes = p.get("notes") or ""
        assert notes.strip(), (
            f"{p.get('procedureId')}: notes MUST be non-empty (carries the "
            "per-entry boundary caveat)"
        )
    # Registry-as-a-whole references its UPL boundary regime. The seed encodes
    # this as the "行政書士法 / UPL" phrasing in the top-level _comment and/or
    # the per-entry notes — assert it appears somewhere in the serialized file.
    blob = _SEED.read_text()
    assert "行政書士法" in blob, "registry MUST reference its 行政書士法 boundary"
    assert "UPL" in blob, "registry MUST reference the UPL boundary regime"


# ─────────────────────────────────────────────────────────────────────────
# 7. top-level integer freshnessWindowDays
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
