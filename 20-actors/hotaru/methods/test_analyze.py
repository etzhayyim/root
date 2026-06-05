#!/usr/bin/env python3
"""hotaru 蛍 — analyzer tests (ADR-2606051200).

Standalone-runnable (no pytest required) AND pytest-compatible, mirroring nusa.
Run:  python3 test_analyze.py   (or via pytest with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1)
"""
from __future__ import annotations

import copy
import pathlib

import analyze as A

SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-iii-v-substrate.kotoba.edn"


def _load():
    rows = A.load_edn(SEED)
    return A.classify(rows)


def test_seed_parses_and_classifies():
    materials, procs, crystals, wafers, precursors = _load()
    assert "inp" in materials
    assert materials["inp"][":iiiv.material/bandgap-type"] == ":direct"
    assert len(procs) >= 10 and len(crystals) >= 3 and len(wafers) >= 2
    assert "ph3" in precursors and "in-metal" in precursors


def test_g1_all_processes_open_license():
    _, procs, _, _, _ = _load()
    # must not raise
    A.screen_licenses(procs)
    for p in procs.values():
        assert p[":iiiv.proc/source-license"] in A.ALLOWED_LICENSES


def test_g1_vendor_proprietary_is_rejected():
    _, procs, _, _, _ = _load()
    bad = copy.deepcopy(procs)
    next(iter(bad.values()))[":iiiv.proc/source-license"] = ":vendor-proprietary"
    try:
        A.screen_licenses(bad)
    except ValueError as e:
        assert "G1 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on :vendor-proprietary license")


def test_g2_fabricated_true_is_rejected():
    _, _, crystals, wafers, _ = _load()
    bad = copy.deepcopy(crystals)
    next(iter(bad.values()))[":iiiv.crystal/fabricated"] = True
    try:
        A.screen_fabrication(bad, wafers)
    except ValueError as e:
        assert "G2 violation" in str(e)
    else:
        raise AssertionError("expected ValueError on :fabricated true crystal")


def test_g2_all_designs_are_not_fabricated():
    _, _, crystals, wafers, _ = _load()
    A.screen_fabrication(crystals, wafers)  # must not raise
    assert all(c[":iiiv.crystal/fabricated"] is False for c in crystals.values())
    assert all(w[":iiiv.wafer/fabricated"] is False for w in wafers.values())


def test_substrate_stages_are_all_open_mature():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    # synthesis / bulk-growth / wafering / surface-prep each have an open-mature process
    assert a["covered"] == a["total"] == 4
    assert a["substrate_commons_ready"] is True


def test_epitaxy_is_a_gap_and_r4_gate_not_satisfiable():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    # epitaxy exists in the seed but only as :gap maturity → not open-mature
    assert a["epitaxy"]["n"] >= 1
    assert a["epitaxy"]["open_mature"] is False
    # the honest headline: the commons does NOT yet satisfy the 2605265500 R4+ gate;
    # fabrication stays prohibited. The binding gap is epitaxy, not substrate growth.
    assert a["r4_gate_satisfiable"] is False


def test_g4_conflict_mineral_indium_detected_and_designs_clean():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    assert "In" in a["cm_elements"] and "Ga" in a["cm_elements"]
    # every seed crystal declares clean In sourcing → nothing flagged
    assert a["cm_flagged"] == {}


def test_g4_unverified_sourcing_is_flagged():
    materials, procs, crystals, wafers, precursors = _load()
    crystals = copy.deepcopy(crystals)
    next(iter(crystals.values()))[":iiiv.crystal/in-sourcing"] = ":unverified"
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    assert len(a["cm_flagged"]) == 1


def test_render_report_smoke():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    rep = A.render_report(materials, procs, crystals, wafers, precursors, a)
    assert "R4+ re-evaluation gate" in rep
    assert "PROHIBITED through R3" in rep
    datoms = A.render_datoms(materials, procs, crystals, wafers, a)
    assert ":hotaru.derived/substrate-commons-ready" in datoms


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok: {fn.__name__}")
    print(f"hotaru analyze: {len(fns)}/{len(fns)} tests green")


if __name__ == "__main__":
    _run_all()
