#!/usr/bin/env python3
"""State-machine tests for hotaru cells (R0). .solve() is NOT called (it raises).

Standalone-runnable AND pytest-compatible (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
    python3 test_state_machines.py
"""
from __future__ import annotations

from commons_ingest.cell import CommonsIngestCell
from commons_ingest.state_machine import (
    IngestPhase,
    transition_to_recorded,
    transition_to_screened,
)
from precursor_safety.cell import PrecursorSafetyCell
from precursor_safety.state_machine import SafetyPhase, review


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


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok: {fn.__name__}")
    print(f"hotaru cells: {len(fns)}/{len(fns)} tests green")


if __name__ == "__main__":
    _run_all()
