#!/usr/bin/env python3
"""State-machine tests for hotaru cells (R0). .solve() is NOT called (it raises).

Standalone-runnable AND pytest-compatible (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
    python3 test_state_machines.py
"""
from __future__ import annotations

from bulk_crystal_design.cell import BulkCrystalDesignCell
from bulk_crystal_design.state_machine import (
    GrowthPhase,
    transition_to_designed,
    transition_to_screened as growth_screen,
)
from commons_readiness.cell import CommonsReadinessCell
from commons_readiness.state_machine import (
    ReadinessPhase,
    transition_to_assessed,
    transition_to_reported,
)
from commons_ingest.cell import CommonsIngestCell
from commons_ingest.state_machine import (
    IngestPhase,
    transition_to_recorded,
    transition_to_screened,
)
from precursor_safety.cell import PrecursorSafetyCell
from precursor_safety.state_machine import SafetyPhase, review
from wafer_fab_design.cell import WaferFabDesignCell
from wafer_fab_design.state_machine import (
    WaferPhase,
    transition_to_screened as wafer_screen,
    transition_to_specified,
)


# ─────────────────────────── commons_ingest (G1/G5) ────────────────────────
def _ingest(license_="textbook-public", stage="bulk-growth", cite="Mullin 1968", proc="p-bulk-lec"):
    s = transition_to_screened(
        {"cell_state": {}, "proc_id": proc, "source_license": license_, "stage": stage,
         "source_cite": cite, "maturity": "open-mature"}
    )
    return transition_to_recorded(s)


def test_commons_ingest_open_license_records():
    out = _ingest()
    cs = out["cell_state"]
    assert cs["phase"] == IngestPhase.RECORDED.value
    assert cs["payload"]["sourceLicense"] == "textbook-public"
    assert cs["payload"]["screened"] is True


def test_commons_ingest_accepts_edn_keyword_form():
    out = _ingest(license_=":patent-expired")
    assert out["cell_state"]["payload"]["sourceLicense"] == "patent-expired"


def test_commons_ingest_rejects_vendor_proprietary():
    try:
        _ingest(license_="vendor-proprietary")
    except ValueError as e:
        assert "G1 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on vendor-proprietary license")


def test_commons_ingest_rejects_patent_active():
    try:
        _ingest(license_="patent-active")
    except ValueError as e:
        assert "G1 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on patent-active license")


def test_commons_ingest_requires_citation():
    try:
        transition_to_screened(
            {"cell_state": {}, "proc_id": "p", "source_license": "academic-oa",
             "stage": "wafering", "source_cite": ""}
        )
    except ValueError as e:
        assert "G5 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on missing citation")


def test_commons_ingest_record_requires_screen_first():
    try:
        transition_to_recorded({"cell_state": {}})
    except ValueError as e:
        assert "open-IP screen" in str(e)
    else:
        raise AssertionError("expected ValueError when recording before screen")


def test_commons_ingest_cell_solve_raises_at_r0():
    try:
        CommonsIngestCell().solve({})
    except RuntimeError as e:
        assert "R0 scaffold" in str(e)
    else:
        raise AssertionError("expected RuntimeError from R0 cell .solve()")


# ─────────────────────────── precursor_safety (G3/G4) ───────────────────────
def _precursors(in_clean=True, ph3_ack=True):
    return [
        {"name": "phosphine", "hazard_class": "acute-toxic-pyrophoric",
         "conflict_mineral": False, "export_control": "ear", "acknowledged": ph3_ack},
        {"name": "indium", "hazard_class": "low", "conflict_mineral": True,
         "export_control": "none", "acknowledged": True},
        {"name": "boric-oxide", "hazard_class": "benign", "conflict_mineral": False,
         "export_control": "none", "acknowledged": True},
    ]


def test_precursor_safety_clears_clean_design():
    out = review({"cell_state": {}, "design_id": "c-lec-s",
                  "in_sourcing": "conflict-free-attested", "precursors": _precursors()})
    cs = out["cell_state"]
    assert cs["phase"] == SafetyPhase.CLEARED.value
    assert cs["payload"]["cleared"] is True
    assert "ear" in cs["payload"]["exportControls"]


def test_precursor_safety_refuses_unverified_conflict_mineral():
    out = review({"cell_state": {}, "design_id": "c-x",
                  "in_sourcing": "unverified", "precursors": _precursors()})
    cs = out["cell_state"]
    assert cs["phase"] == SafetyPhase.REFUSED.value
    assert "G4" in cs["refusal"]


def test_precursor_safety_refuses_unacknowledged_acute_toxic():
    out = review({"cell_state": {}, "design_id": "c-y",
                  "in_sourcing": "recycled", "precursors": _precursors(ph3_ack=False)})
    cs = out["cell_state"]
    assert cs["phase"] == SafetyPhase.REFUSED.value
    assert "G3" in cs["refusal"]


def test_precursor_safety_accepts_edn_keyword_sourcing():
    out = review({"cell_state": {}, "design_id": "c-z",
                  "in_sourcing": ":recycled", "precursors": _precursors()})
    assert out["cell_state"]["phase"] == SafetyPhase.CLEARED.value


def test_precursor_safety_cell_solve_raises_at_r0():
    try:
        PrecursorSafetyCell().solve({})
    except RuntimeError as e:
        assert "R0 scaffold" in str(e)
    else:
        raise AssertionError("expected RuntimeError from R0 cell .solve()")


# ─────────────────────── bulk_crystal_design (G2/G4) ───────────────────────
def _growth(method="lec", dopant="sulfur", in_sourcing="conflict-free-attested",
            crystal="c-lec-s", fabricated=False):
    s = growth_screen({"cell_state": {}, "crystal_id": crystal, "method": method,
                       "dopant": dopant, "in_sourcing": in_sourcing,
                       "target_wafer": "w-2in-n", "fabricated": fabricated})
    return transition_to_designed(s)


def test_bulk_crystal_design_lec_designs():
    cs = _growth()["cell_state"]
    assert cs["phase"] == GrowthPhase.DESIGNED.value
    assert cs["payload"]["fabricated"] is False
    assert cs["payload"]["method"] == "lec"


def test_bulk_crystal_design_accepts_edn_keyword_method():
    cs = _growth(method=":vgf", dopant=":iron")["cell_state"]
    assert cs["payload"]["method"] == "vgf" and cs["payload"]["dopant"] == "iron"


def test_bulk_crystal_design_g2_refuses_fabricated_true():
    try:
        _growth(fabricated=True)
    except ValueError as e:
        assert "G2 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on fabricated=true crystal")


def test_bulk_crystal_design_g4_refuses_unverified_sourcing():
    try:
        _growth(in_sourcing="unverified")
    except ValueError as e:
        assert "G4 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on unverified In sourcing")


def test_bulk_crystal_design_refuses_epitaxy_method():
    try:
        _growth(method="movpe")
    except ValueError as e:
        assert "bulk-growth method" in str(e)
    else:
        raise AssertionError("expected ValueError on epitaxy method in bulk-growth cell")


def test_bulk_crystal_design_cell_solve_raises_at_r0():
    try:
        BulkCrystalDesignCell().solve({})
    except RuntimeError as e:
        assert "R0 scaffold" in str(e)
    else:
        raise AssertionError("expected RuntimeError from R0 cell .solve()")


# ───────────────────────── wafer_fab_design (G2/spec) ───────────────────────
def _wafer(diameter_um=50800, orientation="(100)", epd=5000, fabricated=False, wid="w-2in-n"):
    s = wafer_screen({"cell_state": {}, "wafer_id": wid, "diameter_um": diameter_um,
                      "orientation": orientation, "epd_cm2": epd, "doping": "sulfur-n",
                      "fabricated": fabricated})
    return transition_to_specified(s)


def test_wafer_fab_design_specifies():
    cs = _wafer()["cell_state"]
    assert cs["phase"] == WaferPhase.SPECIFIED.value
    assert cs["payload"]["fabricated"] is False
    assert cs["payload"]["diameterUm"] == 50800


def test_wafer_fab_design_g2_refuses_fabricated_true():
    try:
        _wafer(fabricated=True)
    except ValueError as e:
        assert "G2 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on fabricated=true wafer")


def test_wafer_fab_design_refuses_unknown_diameter():
    try:
        _wafer(diameter_um=60000)
    except ValueError as e:
        assert "diameter" in str(e)
    else:
        raise AssertionError("expected ValueError on unknown diameter")


def test_wafer_fab_design_refuses_nonpositive_epd():
    try:
        _wafer(epd=0)
    except ValueError as e:
        assert "epd-cm2" in str(e)
    else:
        raise AssertionError("expected ValueError on non-positive EPD")


def test_wafer_fab_design_cell_solve_raises_at_r0():
    try:
        WaferFabDesignCell().solve({})
    except RuntimeError as e:
        assert "R0 scaffold" in str(e)
    else:
        raise AssertionError("expected RuntimeError from R0 cell .solve()")


# ─────────────────────── commons_readiness (G3) ────────────────────────────
def _readiness(per_stage=None, epitaxy=False, conflict=0, **extra):
    per_stage = per_stage or {"synthesis": "open-mature", "bulk-growth": "open-mature",
                              "wafering": "open-mature", "surface-prep": "open-mature"}
    s = transition_to_assessed({"cell_state": {}, "per_stage": per_stage,
                                "epitaxy_open_mature": epitaxy, "conflict_flagged": conflict,
                                **extra})
    return transition_to_reported(s)


def test_commons_readiness_full_substrate_scores_one():
    cs = _readiness()["cell_state"]
    assert cs["phase"] == ReadinessPhase.REPORTED.value
    assert cs["payload"]["maturityScore"] == 1.0
    assert cs["payload"]["substrateCommonsReady"] is True
    # epitaxy gap → R4+ gate not satisfiable; fabrication stays prohibited
    assert cs["payload"]["r4GateSatisfiable"] is False
    assert cs["payload"]["fabricationProhibited"] is True


def test_commons_readiness_emerging_stage_lowers_score():
    cs = _readiness(per_stage={"synthesis": "open-mature", "bulk-growth": "open-mature",
                               "wafering": "open-emerging", "surface-prep": "open-mature"})["cell_state"]
    assert cs["payload"]["maturityScore"] == 0.875
    assert cs["payload"]["substrateCommonsReady"] is False


def test_commons_readiness_g3_refuses_adjudicating_key():
    try:
        _readiness(gateOpened=True)
    except ValueError as e:
        assert "G3 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on adjudicating key (G3)")


def test_commons_readiness_r4_satisfiable_only_with_open_epitaxy():
    cs = _readiness(epitaxy=True)["cell_state"]
    assert cs["payload"]["r4GateSatisfiable"] is True
    # even when the commons would satisfy the gate, the report never opens fabrication
    assert cs["payload"]["fabricationProhibited"] is True


def test_commons_readiness_cell_solve_raises_at_r0():
    try:
        CommonsReadinessCell().solve({})
    except RuntimeError as e:
        assert "R0 scaffold" in str(e)
    else:
        raise AssertionError("expected RuntimeError from R0 cell .solve()")


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok: {fn.__name__}")
    print(f"hotaru cells: {len(fns)}/{len(fns)} tests green")


if __name__ == "__main__":
    _run_all()
