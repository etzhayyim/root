"""Fail-closed invariants for the kokoro (心) WORLDWIDE crisis-support registry.

Pins the constitutional properties of the multi-jurisdiction crisis-support
seed directory (`registry/support-lines.seed.json`, per ADR-2605263700). This
suite is R0-safe: test-only, deterministic, network-free — it never imports/
executes a cell and never dials/contacts a live line. It fails fast
(fail-closed) if any constitutional invariant drifts.

SAFETY-CRITICAL framing: this is a crisis-support directory. A wrong or stale
contact number is actively harmful, so G14 (`unverified-seed`) is enforced
per-entry and no entry may ship pre-marked verified. The matching human
re-verification workflow lives in `20-actors/kokoro/registry/VERIFICATION.md`;
this suite is its machine floor.

Sibling of `test_toritsugi_registry_seed.py` (which pins the toritsugi
government-procedure seed). Where that suite enforces 行政書士法/UPL boundary
phrasing, THIS suite enforces kokoro's NON-CLINICAL support-routing boundary
phrasing on the registry data itself.

Invariants under test:

  1. file parses as JSON and exposes a non-empty `lines` list.
  2. every entry has a UNIQUE `lineId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 —
     SAFETY-CRITICAL: no crisis line may be pre-marked verified in the seed).
  4. every entry has a non-empty `contact` + non-empty https `provenance`
     URL + an ISO-8601 Zulu `lastVerified` stamp.
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage / guards
     against regression to JP-only.
  6. every `supportKind` is one of the allowed crisis-support kinds.
  7. every entry's `notes` is non-empty AND references kokoro's NON-CLINICAL
     support-routing boundary (per-entry caveat, never blank).
  8. a top-level integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "kokoro" / "registry" / "support-lines.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# The closed set of crisis-support kinds the seed is allowed to use.
_ALLOWED_SUPPORT_KINDS = {
    "emergency-number",
    "crisis-hotline",
    "text-or-chat-line",
    "youth-line",
    "specialized-line",
    "intl-directory",
}


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty lines list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_lines():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    lines = seed.get("lines")
    assert isinstance(lines, list), "`lines` MUST be a list"
    assert len(lines) > 0, "`lines` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique lineId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_line_ids_unique():
    lines = _load()["lines"]
    ids = [ln.get("lineId") for ln in lines]
    assert all(ids), "every entry MUST have a non-empty lineId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate lineId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed (SAFETY-CRITICAL)
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    lines = _load()["lines"]
    for ln in lines:
        assert ln.get("verificationStatus") == "unverified-seed", (
            f"G14 (SAFETY-CRITICAL): {ln.get('lineId')} MUST ship "
            f"verificationStatus=unverified-seed — a crisis line may NEVER be "
            f"pre-marked verified in the seed (a wrong/stale number is "
            f"harmful); got {ln.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. contact + provenance https URL + lastVerified timestamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_contact_provenance_and_last_verified():
    lines = _load()["lines"]
    for ln in lines:
        lid = ln.get("lineId")
        contact = (ln.get("contact") or "").strip()
        assert contact, (
            f"{lid}: MUST carry a non-empty contact (the safety-critical "
            "number/channel)"
        )
        prov = ln.get("provenance") or ""
        assert prov, f"{lid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith("https://"), (
            f"{lid}: provenance MUST be an https URL; got {prov!r}"
        )
        lv = ln.get("lastVerified") or ""
        assert lv, f"{lid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{lid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 12 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    lines = _load()["lines"]
    for ln in lines:
        assert ln.get("jurisdiction"), (
            f"{ln.get('lineId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {ln["jurisdiction"] for ln in lines}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        "jurisdictions (guards against regression to JP-only crisis coverage); "
        f"got {sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. supportKind in the allowed crisis-support set
# ─────────────────────────────────────────────────────────────────────────


def test_support_kind_in_allowed_set():
    lines = _load()["lines"]
    for ln in lines:
        kind = ln.get("supportKind")
        assert kind in _ALLOWED_SUPPORT_KINDS, (
            f"{ln.get('lineId')}: supportKind {kind!r} not in allowed set "
            f"{sorted(_ALLOWED_SUPPORT_KINDS)}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. non-clinical support-routing boundary present in every notes
# ─────────────────────────────────────────────────────────────────────────


def test_non_clinical_boundary_caveat_present():
    lines = _load()["lines"]
    for ln in lines:
        lid = ln.get("lineId")
        notes = (ln.get("notes") or "").strip()
        assert notes, (
            f"{lid}: notes MUST be non-empty (carries the per-entry "
            "non-clinical support-routing boundary caveat)"
        )
        # kokoro's structural discipline: every entry must re-assert that this
        # is NON-CLINICAL support ROUTING — never clinical care/diagnosis.
        assert "kokoro" in notes, (
            f"{lid}: notes MUST name kokoro's boundary"
        )
        assert "NOT clinical" in notes, (
            f"{lid}: notes MUST assert the NON-CLINICAL boundary "
            "('NOT clinical ...')"
        )
        assert any(
            tok in notes for tok in ("SUPPORT routing", "ROUTES", "routes", "routing")
        ), (
            f"{lid}: notes MUST frame kokoro as SUPPORT-ROUTING (it ROUTES to "
            "an official/recognized line; renders no clinical opinion)"
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
