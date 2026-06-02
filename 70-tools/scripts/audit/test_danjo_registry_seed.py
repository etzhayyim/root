"""Fail-closed invariants for the danjo (弾正) WORLDWIDE fiscal-source registry.

Pins the constitutional properties of the multi-jurisdiction fiscal-transparency
ingestion-SOURCE seed registry (`registry/sources.seed.json`, per ADR-2605301600
danjo public-accountability oversight actor + ADR-2605302245 global fiscal-flow
extension). This suite is R0-safe: test-only, deterministic, network-free — it
never imports/executes a cell, never re-fetches a live portal (G3 passive-only),
and never touches a live channel. It fails fast (fail-closed) if any
constitutional invariant drifts.

Sibling of `test_toritsugi_registry_seed.py` (which pins the toritsugi worldwide
procedure registry). Where that suite guards a UPL/行政書士法 boundary on a
service-delivery actor, THIS suite guards the danjo NON-ADJUDICATING +
OBSERVATIONAL boundary on a passive cross-reference catalog of already-public
official fiscal datasets — danjo finds + cross-references, kanae renders, neither
adjudicates (ADR-2605192100 §1.12 + §2(c)).

Invariants under test:

  1. file parses as JSON and exposes a non-empty `sources` list.
  2. every entry has a UNIQUE `sourceId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed; no live ingestion runs against an
     unverified/stale source).
  4. every entry has a non-empty https provenance URL + a lastVerified stamp.
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage / guards against
     regression to JP-only.
  6. every entry's `sourceKind` is in the allowed catalog set.
  7. boundary caveat present: every entry's `notes` is non-empty, and the
     registry as a whole references its non-adjudicating / observational
     boundary regime.
  8. a top-level integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "danjo" / "registry" / "sources.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# Allowed fiscal-source kinds. danjo ingests already-public official
# fiscal-transparency datasets only; any new kind must be added here
# consciously (fail-closed against an unbounded sourceKind vocabulary).
_ALLOWED_SOURCE_KINDS = {
    "audit-institution",
    "budget-portal",
    "intl-aggregator",
    "legislature-record",
    "open-spending",
    "procurement-system",
}


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty sources list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_sources():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    srcs = seed.get("sources")
    assert isinstance(srcs, list), "`sources` MUST be a list"
    assert len(srcs) > 0, "`sources` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique sourceId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_source_ids_unique():
    srcs = _load()["sources"]
    ids = [s.get("sourceId") for s in srcs]
    assert all(ids), "every entry MUST have a non-empty sourceId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate sourceId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    srcs = _load()["sources"]
    for s in srcs:
        assert s.get("verificationStatus") == "unverified-seed", (
            f"G14: {s.get('sourceId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified; no live "
            f"ingestion against an unverified source); got "
            f"{s.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. provenance https URL + lastVerified timestamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_and_last_verified():
    srcs = _load()["sources"]
    for s in srcs:
        sid = s.get("sourceId")
        prov = s.get("provenance") or ""
        assert prov, f"{sid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith("https://"), (
            f"{sid}: provenance MUST be an https URL; got {prov!r}"
        )
        lv = s.get("lastVerified") or ""
        assert lv, f"{sid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{sid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 12 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    srcs = _load()["sources"]
    for s in srcs:
        assert s.get("jurisdiction"), (
            f"{s.get('sourceId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {s["jurisdiction"] for s in srcs}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        "jurisdictions (guards against regression to JP-only; danjo is a "
        f"global fiscal-flow catalog per ADR-2605302245); got "
        f"{sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. sourceKind in allowed catalog set
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_source_kind_in_allowed_set():
    srcs = _load()["sources"]
    for s in srcs:
        sid = s.get("sourceId")
        kind = s.get("sourceKind")
        assert kind in _ALLOWED_SOURCE_KINDS, (
            f"{sid}: sourceKind {kind!r} not in allowed catalog "
            f"{sorted(_ALLOWED_SOURCE_KINDS)} — fail-closed against an "
            "unbounded sourceKind vocabulary"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. non-adjudicating / observational boundary caveat present
# ─────────────────────────────────────────────────────────────────────────


def test_non_adjudicating_boundary_caveat_present():
    seed = _load()
    srcs = seed["sources"]
    # Per-entry: a non-empty `notes` text field.
    for s in srcs:
        notes = s.get("notes") or ""
        assert notes.strip(), (
            f"{s.get('sourceId')}: notes MUST be non-empty (carries the "
            "per-entry boundary caveat)"
        )
    # Registry-as-a-whole references its non-adjudicating / observational
    # boundary regime — the constitutional discipline that danjo emits factual
    # cross-reference observations only and renders NO verdict. The seed encodes
    # this in the top-level _comment and/or per-entry notes; assert it appears
    # in the serialized file (case-insensitive — the seed uses uppercase).
    blob = _SEED.read_text().lower()
    assert "adjudicat" in blob, (
        "registry MUST reference its NON-ADJUDICATING boundary (danjo renders "
        "no verdict)"
    )
    assert "observational" in blob, (
        "registry MUST reference its OBSERVATIONAL boundary regime"
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
