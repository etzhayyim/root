"""Fail-closed invariants tests for the moushibumi (申文) WORLDWIDE seed registry.

Pins the constitutional properties of the multi-jurisdiction democratic-
participation target registry (ADR-2605312400 §2, worldwide expansion
2026-06-02) so a future edit cannot silently weaken a seed-honesty / coverage /
political-neutrality invariant. R0-safe: pure JSON inspection — no cell import,
no network, no live submission. Mirrors test_toritsugi_invariants.py style.

Invariants under test:

  1. file parses as JSON and ships a non-empty "targets" list.
  2. every entry has a unique "targetId" (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed; live submission is gated on
     human/Council verification).
  4. every entry has a non-empty https provenance URL + a lastVerified stamp.
  5. every entry has a "jurisdiction" and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide long-tail coverage,
     guards against regression to JP-only / shallow coverage.
  6. boundary caveat: every entry's notes is non-empty, and the registry as a
     whole references its political-neutrality / 公選法 boundary regime (G3).
  7. a top-level freshnessWindowDays integer is present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "moushibumi" / "registry" / "targets.seed.json"


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses as JSON + non-empty "targets" list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_targets():
    assert _SEED.exists(), f"missing registry: {_SEED}"
    reg = _load()
    assert isinstance(reg, dict), "registry top level must be a JSON object"
    targets = reg.get("targets")
    assert isinstance(targets, list), '"targets" must be a list'
    assert len(targets) > 0, '"targets" must be non-empty'


# ─────────────────────────────────────────────────────────────────────────
# 2. unique targetId — fail-closed on duplicates
# ─────────────────────────────────────────────────────────────────────────


def test_target_ids_unique():
    targets = _load()["targets"]
    ids = [t.get("targetId") for t in targets]
    assert all(ids), "every entry MUST have a non-empty targetId"
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"duplicate targetId(s) — fail-closed: {sorted(dupes)}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — EVERY entry ships unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_unverified_seed():
    targets = _load()["targets"]
    for t in targets:
        assert t.get("verificationStatus") == "unverified-seed", (
            f"G14: {t.get('targetId')} MUST ship verificationStatus="
            f"unverified-seed; got {t.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. provenance (https) + lastVerified on every entry
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_and_last_verified():
    targets = _load()["targets"]
    for t in targets:
        prov = t.get("provenance") or ""
        assert prov, f"G8: {t.get('targetId')} MUST cite a provenance/source URL"
        assert prov.startswith("https://"), (
            f"G8: {t.get('targetId')} provenance MUST be an https official source; "
            f"got {prov!r}"
        )
        assert t.get("lastVerified"), (
            f"G14: {t.get('targetId')} MUST carry a lastVerified timestamp"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. jurisdiction present + worldwide span (>= 5 distinct)
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    targets = _load()["targets"]
    for t in targets:
        assert t.get("jurisdiction"), (
            f"{t.get('targetId')} MUST declare a jurisdiction"
        )
    distinct = {t["jurisdiction"] for t in targets}
    assert len(distinct) >= 12, (
        f"worldwide coverage regression guard: expected >= 12 distinct "
        f"jurisdictions, got {len(distinct)}: {sorted(distinct)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. G3 boundary caveat: per-entry notes + registry-wide neutrality regime
# ─────────────────────────────────────────────────────────────────────────


def test_boundary_caveat_present():
    reg = _load()
    targets = reg["targets"]
    for t in targets:
        assert (t.get("notes") or "").strip(), (
            f"{t.get('targetId')} MUST carry a non-empty notes boundary caveat"
        )
    # Registry as a whole references its political-neutrality / 公選法 boundary
    # regime (G3) — JP entries cite 公選法 directly; worldwide entries carry the
    # "公選法-equivalent" neutrality phrasing.
    blob = json.dumps(reg, ensure_ascii=False)
    assert "公選法" in blob, (
        "G3: registry MUST reference its 公選法 / political-neutrality boundary regime"
    )
    neutrality_hits = sum(
        ("公選法" in (t.get("notes") or "")
         or "political-neutrality" in (t.get("notes") or "").lower())
        for t in targets
    )
    assert neutrality_hits >= 5, (
        f"G3: expected the political-neutrality boundary regime cited across many "
        f"entries; only {neutrality_hits} entries reference it"
    )


# ─────────────────────────────────────────────────────────────────────────
# 7. top-level freshnessWindowDays integer
# ─────────────────────────────────────────────────────────────────────────


def test_freshness_window_days_present():
    reg = _load()
    fwd = reg.get("freshnessWindowDays")
    assert isinstance(fwd, int) and not isinstance(fwd, bool), (
        f"freshnessWindowDays MUST be an integer; got {fwd!r}"
    )
    assert fwd > 0, "freshnessWindowDays MUST be positive"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
