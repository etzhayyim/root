"""Lock-in tests for the kamado (竈) constitutional invariants.

Pins the structural properties designed in ADR-2606051500 (kamado — closed-loop
carbon refining + fossil-refinery decommission/transition + refinery observation)
so a future refactor cannot silently weaken a constitutional invariant. None of
these are amendable without Council process (the fossil exclusion is Lv7+ and, per
§2(d) + ADR-2605263500 D3, effectively un-addable); this suite fails fast if any
artifact drifts.

The signature kamado invariant is G1: a refining feedstock MUST be closed-loop
carbon. `:fossil-virgin-crude` is structurally UNREPRESENTABLE — the same
discipline as nusa's `:thc-class` and tazuna's `:weaponizable`. kamado declares
the invariant THREE times and this suite proves all three agree:

  enforcement point 1 — the ontology schema (`refining-ontology.kotoba.edn`):
      `:feedstock/class :db/allowed` excludes every fossil member.
  enforcement point 2 — the published lexicons (`com.etzhayyim.kamado.*`):
      feedstockClass `enum` excludes fossil; closedLoop/screened are const true.
  enforcement point 3 — the guard (`methods/feedstock_guard.py`):
      `screen_feedstock(":fossil-virgin-crude")` raises ValueError.

Invariants under test:

  1. G1 (ontology) — :feedstock/class :db/allowed is exactly the 4 closed-loop
     classes; `:fossil-virgin-crude` (and any fossil member) is absent.
  2. G1 (lexicon) — feedstockProvenance + synthesisRun feedstockClass enum match
     the ontology set and exclude fossil; closedLoop + screened are const true.
  3. G1 (guard) — screen_feedstock raises on fossil, passes on each allowed
     class, and ALLOWED_FEEDSTOCK matches the ontology / lexicon set.
  4. G3 — decommissionPlan intervention enum + guard ALLOWED_INTERVENTION are the
     wind-down/convert set only; `:expand` / `:restart-fossil` are excluded and
     screen_intervention raises on them.
  5. G4 — refineryAsset.isObservation is const true (observe ≠ operate; not a
     target-list).
  6. G5 — decommissionPlan.serverHeldKey is const false (no-server-key,
     ADR-2605231525).
  7. G8 — decommissionPlan.outwardGated is const true (real teardown gated).
  8. G7 — carbonBalance.sourcing is const "derived" (analyzer output, never
     re-ingested as authoritative).
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "refining-ontology.kotoba.edn"
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "kamado"
_GUARD = _REPO / "20-actors" / "kamado" / "methods" / "feedstock_guard.py"

# The closed-loop carbon classes — the ONLY representable feedstocks (G1).
_EXPECTED_FEEDSTOCK = {
    "biogenic",
    "captured-co2",
    "recycled-carbon",
    "existing-inventory-decommission",
}
# §2(d): the ONLY representable interventions on an existing fossil asset (G3).
_EXPECTED_INTERVENTION = {"decommission", "remediate", "convert", "monitor"}
# Tokens that MUST NEVER appear as an allowed feedstock / intervention.
_FORBIDDEN_FEEDSTOCK = {"fossil-virgin-crude", "fossil", "crude", "virgin-crude"}
_FORBIDDEN_INTERVENTION = {"expand", "restart-fossil", "revamp-throughput"}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text())


def _record_props(lex: dict) -> dict:
    return lex["defs"]["main"]["record"]["properties"]


def _ontology_feedstock_allowed() -> set[str]:
    """Extract the :feedstock/class :db/allowed keyword set from the ontology."""
    text = _ONTOLOGY.read_text()
    m = re.search(r":feedstock/class\s*\{.*?:db/allowed\s*\[(.*?)\]", text, re.S)
    assert m, "could not locate :feedstock/class :db/allowed in the ontology"
    return {tok.lstrip(":") for tok in re.findall(r":[a-z0-9-]+", m.group(1))}


def _import_guard():
    spec = importlib.util.spec_from_file_location("kamado_feedstock_guard", _GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────────────────────────────────
# 1. G1 — ontology :feedstock/class :db/allowed excludes fossil
# ─────────────────────────────────────────────────────────────────────────


def test_g1_ontology_feedstock_allowed_excludes_fossil():
    assert _ONTOLOGY.exists(), f"missing ontology: {_ONTOLOGY}"
    allowed = _ontology_feedstock_allowed()
    assert allowed == _EXPECTED_FEEDSTOCK, (
        f"G1: ontology :feedstock/class drifted; got {sorted(allowed)}"
    )
    for bad in _FORBIDDEN_FEEDSTOCK:
        assert bad not in allowed, (
            f"G1 VIOLATION: fossil feedstock {bad!r} became representable in the "
            f"ontology — :fossil-virgin-crude must stay structurally absent"
        )


# ─────────────────────────────────────────────────────────────────────────
# 2. G1 — lexicon feedstockClass enum + closedLoop/screened consts
# ─────────────────────────────────────────────────────────────────────────


def test_g1_lexicon_feedstock_enum_matches_and_excludes_fossil():
    for name in ("feedstockProvenance.json", "synthesisRun.json"):
        p = _LEX / name
        assert p.exists(), f"missing published lexicon: {p}"
        props = _record_props(_load_json(p))
        enum = set(props["feedstockClass"]["enum"])
        assert enum == _EXPECTED_FEEDSTOCK, (
            f"G1: {name} feedstockClass enum drifted from the ontology set; "
            f"got {sorted(enum)}"
        )
        for bad in _FORBIDDEN_FEEDSTOCK:
            assert bad not in enum, (
                f"G1 VIOLATION: {name} feedstockClass enum admits fossil {bad!r}"
            )


def test_g1_feedstock_provenance_closed_loop_and_screened_const_true():
    props = _record_props(_load_json(_LEX / "feedstockProvenance.json"))
    for field in ("closedLoop", "screened"):
        assert props[field].get("const") is True, (
            f"G1: feedstockProvenance.{field} MUST be const true "
            f"(a provenance record exists ONLY for screened closed-loop carbon)"
        )


# ─────────────────────────────────────────────────────────────────────────
# 3. G1 — the guard raises on fossil, passes on each allowed class
# ─────────────────────────────────────────────────────────────────────────


def test_g1_guard_rejects_fossil_accepts_closed_loop():
    guard = _import_guard()
    assert {c.lstrip(":") for c in guard.ALLOWED_FEEDSTOCK} == _EXPECTED_FEEDSTOCK, (
        f"G1: guard ALLOWED_FEEDSTOCK drifted; got {guard.ALLOWED_FEEDSTOCK}"
    )
    with pytest.raises(ValueError):
        guard.screen_feedstock(":fossil-virgin-crude")
    for cls in _EXPECTED_FEEDSTOCK:
        # accepts both with and without a leading colon (guard normalises).
        guard.screen_feedstock(f":{cls}")


# ─────────────────────────────────────────────────────────────────────────
# 4. G3 — intervention wind-down/convert set only; never expand/restart-fossil
# ─────────────────────────────────────────────────────────────────────────


def test_g3_intervention_enum_and_guard_exclude_life_extension():
    props = _record_props(_load_json(_LEX / "decommissionPlan.json"))
    enum = set(props["intervention"]["enum"])
    assert enum == _EXPECTED_INTERVENTION, (
        f"G3: decommissionPlan.intervention enum drifted; got {sorted(enum)}"
    )
    for bad in _FORBIDDEN_INTERVENTION:
        assert bad not in enum, (
            f"G3 VIOLATION: fossil life-extension {bad!r} became representable"
        )
    guard = _import_guard()
    assert {k.lstrip(":") for k in guard.ALLOWED_INTERVENTION} == _EXPECTED_INTERVENTION
    with pytest.raises(ValueError):
        guard.screen_intervention(":expand")
    with pytest.raises(ValueError):
        guard.screen_intervention(":restart-fossil")


# ─────────────────────────────────────────────────────────────────────────
# 5. G4 — refineryAsset observes (observe ≠ operate)
# ─────────────────────────────────────────────────────────────────────────


def test_g4_refinery_asset_is_observation_const_true():
    props = _record_props(_load_json(_LEX / "refineryAsset.json"))
    assert props["isObservation"].get("const") is True, (
        "G4: refineryAsset.isObservation MUST be const true — kamado OBSERVES "
        "public assets; observation ≠ operation; not a target-list"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6 + 7. G5 / G8 — decommissionPlan no-server-key + outward-gated
# ─────────────────────────────────────────────────────────────────────────


def test_g5_g8_decommission_plan_key_and_gate_consts():
    props = _record_props(_load_json(_LEX / "decommissionPlan.json"))
    assert props["serverHeldKey"].get("const") is False, (
        "G5: decommissionPlan.serverHeldKey MUST be const false (no-server-key)"
    )
    assert props["outwardGated"].get("const") is True, (
        "G8: decommissionPlan.outwardGated MUST be const true (real teardown = "
        "Council Lv6+ + operator; R0 intent-only)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 8. G7 — carbonBalance is a derived analyzer output
# ─────────────────────────────────────────────────────────────────────────


def test_g7_carbon_balance_sourcing_const_derived():
    props = _record_props(_load_json(_LEX / "carbonBalance.json"))
    sourcing = props["sourcing"]
    assert sourcing.get("const") == "derived", (
        "G7: carbonBalance.sourcing MUST be const 'derived' (analyzer output, "
        "never re-ingested as authoritative)"
    )
    assert sourcing.get("enum") == ["derived"], (
        f"G7: carbonBalance.sourcing enum MUST be ['derived']; got {sourcing.get('enum')}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
