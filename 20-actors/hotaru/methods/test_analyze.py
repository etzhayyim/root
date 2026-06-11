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
    assert len(procs) >= 16 and len(crystals) >= 3 and len(wafers) >= 2
    assert len(materials) >= 6 and "insb" in materials
    assert "ph3" in precursors and "in-metal" in precursors
    # metalorganic precursors are conflict-mineral (In/Ga) and acute-toxic
    assert precursors["tmin"][":iiiv.precursor/conflict-mineral"] is True


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


def test_maturity_score_and_per_material_completeness():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    # 4 substrate stages all have an open-mature process → score 1.0
    assert a["maturity_score"] == 1.0
    # InP is the seed's lead material and has processes in all 4 substrate stages
    assert a["per_material"]["inp"]["covered"] == 4
    assert a["per_material"]["inp"]["fraction"] == 1.0
    # GaAs now also has a full open substrate chain (LEC/VGF GaAs textbook/expired-patent)
    assert a["per_material"]["gaas"]["covered"] == 4
    assert a["per_material"]["gaas"]["fraction"] == 1.0
    # GaN bulk is now tracked (ammonothermal/HVPE) at bulk-growth ONLY → 1/4, never full
    assert a["per_material"]["gan"]["fraction"] == 0.25
    assert a["per_material"]["gan"]["covered"] == 1


def test_maturity_score_drops_when_a_stage_is_only_emerging():
    materials, procs, crystals, wafers, precursors = _load()
    procs = copy.deepcopy(procs)
    # demote both wafering processes to emerging → that stage weight 0.5 → score 0.875
    for p in procs.values():
        if p[":iiiv.proc/stage"] == ":wafering":
            p[":iiiv.proc/maturity"] = ":open-emerging"
    score, _ = A.maturity_metrics(procs, materials)
    assert score == 0.875


def test_per_material_maturity_weighted_score():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    # InP & GaAs full open-mature chains → maturity-weighted score 1.0
    assert a["per_material"]["inp"]["score"] == 1.0
    assert a["per_material"]["gaas"]["score"] == 1.0
    # GaN: only bulk-growth, at emerging (0.5) → weighted score 0.5/4 = 0.125 (never full)
    assert a["per_material"]["gan"]["score"] == 0.125


def test_per_material_score_reflects_emerging_demotion():
    materials, procs, crystals, wafers, precursors = _load()
    procs = copy.deepcopy(procs)
    # demote InP surface-prep to emerging → InP score (3*1.0 + 0.5)/4 = 0.875; GaAs stays 1.0
    for p in procs.values():
        if p[":iiiv.proc/material"] == "inp" and p[":iiiv.proc/stage"] == ":surface-prep":
            p[":iiiv.proc/maturity"] = ":open-emerging"
    _, per_material = A.maturity_metrics(procs, materials)
    assert per_material["inp"]["score"] == 0.875
    assert per_material["gaas"]["score"] == 1.0


def test_substrate_material_coverage_excludes_epitaxial_only():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    sm = a["substrate_materials"]
    # InGaAs is epitaxial-only (grown on InP) — excluded from the substrate denominator
    assert "ingaas" in sm["epitaxial_only"]
    assert sm["bulk_substrate"] == 5  # inp, gaas, gan, gasb, insb (NOT ingaas)
    # InP, GaAs, GaSb, InSb now have full open chains
    assert sm["full_chain"] == 4
    assert set(sm["full_chain_materials"]) == {"inp", "gaas", "gasb", "insb"}
    # honest: GaN bulk (HVPE/ammonothermal) is the only bulk substrate NOT a full chain → 4/5
    assert sm["coverage"] == 0.8


def test_gasb_full_chain_and_ingaas_is_epitaxial_only():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    assert a["per_material"]["gasb"]["fraction"] == 1.0
    assert materials["ingaas"][":iiiv.material/form"] == ":epitaxial-only"
    # ingaas still 0 chain, but that is correct (not a gap) — it is excluded above
    assert a["per_material"]["ingaas"]["fraction"] == 0.0


def test_safety_metrics_export_control_and_conflict_mineral():
    _, _, _, _, precursors = _load()
    sf = A.safety_metrics(precursors)
    # PH3 + TMIn + TMGa + AsH3 are acute-toxic (red-P is flammable, not acute)
    assert sf["acute_toxic"] >= 4
    # In/Ga conflict-mineral precursors present (in-metal, ga-metal, tmin, tmga)
    assert sf["conflict_mineral"] >= 4
    assert "In" in sf["conflict_mineral_formulas"]
    # EAR present (Ga/PH3/metalorganics); no ITAR in the seed
    assert sf["ear_present"] is True
    assert sf["itar_present"] is False


def test_gap_register_lists_gan_and_epitaxy_honestly():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    gaps = a["gaps"]
    # the structural epitaxy/device gap is always present (the gate's binding leg)
    assert any(g["material"] == "*" and g["stage"] == "epitaxy" for g in gaps)
    # GaN bulk-growth is now tracked at emerging (ammonothermal) — a gap, not absent
    gan_bulk = [g for g in gaps if g["material"] == "gan" and g["stage"] == "bulk-growth"]
    assert gan_bulk and gan_bulk[0]["status"] == "emerging"
    # GaN's other stages are honestly absent (no congruent-melt synthesis/wafering/surface)
    gan_absent = {g["stage"] for g in gaps if g["material"] == "gan" and g["status"] == "absent"}
    assert {"synthesis", "wafering", "surface-prep"} <= gan_absent
    # full-chain materials (inp/gaas/gasb/insb) contribute NO substrate gaps
    assert not any(g["material"] in {"inp", "gaas", "gasb", "insb"} for g in gaps)


def test_gan_bulk_is_tracked_but_never_open_mature():
    materials, procs, crystals, wafers, precursors = _load()
    a = A.analyze(materials, procs, crystals, wafers, precursors)
    # GaN is a bulk substrate but honestly NOT a full chain → still 4/5 coverage
    assert a["substrate_materials"]["coverage"] == 0.8
    assert "gan" not in a["substrate_materials"]["full_chain_materials"]
    # adding GaN :gap/:emerging processes did not inflate the per-stage maturity score
    assert a["maturity_score"] == 1.0


def test_seed_conforms_to_ontology_allowed_sets():
    """Every constrained attribute in the seed is within the ontology's :db/allowed —
    machine-validated against the schema SSoT (generalizes the per-attribute G1/G2/G4
    checks to all constrained attrs)."""
    rows = A.load_edn(SEED)
    allowed = A.load_allowed_map()
    # the validator actually covers the constrained attributes we rely on
    assert ":iiiv.proc/source-license" in allowed
    assert ":iiiv.crystal/fabricated" in allowed
    assert ":iiiv.material/form" in allowed
    violations = A.validate_against_schema(rows, allowed)
    assert violations == [], violations


def test_schema_validator_catches_bad_value():
    allowed = A.load_allowed_map()
    bad = [{":iiiv.proc/id": "p-x", ":iiiv.proc/maturity": ":bogus"},        # not in allowed
           {":iiiv.crystal/id": "c-x", ":iiiv.crystal/fabricated": True}]    # G2 — only false
    v = A.validate_against_schema(bad, allowed)
    attrs = {x["attr"] for x in v}
    assert ":iiiv.proc/maturity" in attrs
    assert ":iiiv.crystal/fabricated" in attrs


def test_referential_integrity_process_material_ids():
    materials, procs, crystals, wafers, precursors = _load()
    known = set(materials)
    for pid, p in procs.items():
        assert p[":iiiv.proc/material"] in known, f"process {pid} references unknown material"
    for cid, c in crystals.items():
        assert c[":iiiv.crystal/material"] in known, f"crystal {cid} references unknown material"
    for wid, w in wafers.items():
        assert w[":iiiv.wafer/material"] in known, f"wafer {wid} references unknown material"


# ── the "invariant lives in THREE places" claim, machine-checked (anti-drift) ──
_ROOT = pathlib.Path(__file__).resolve().parents[3]
_LEX = pathlib.Path(__file__).resolve().parents[1] / "lex"
_ONTO = _ROOT / "00-contracts" / "schemas" / "iii-v-substrate-ontology.kotoba.edn"


def _strip(xs):
    return {str(x).lstrip(":") for x in xs}


def test_three_places_open_license_set_agrees():
    """schema :db/allowed  ==  lexicon enum  ==  code ALLOWED_LICENSES (G1, 3 places)."""
    onto = A.load_edn(_ONTO)
    schema_set = _strip(onto[":attributes"][":iiiv.proc/source-license"][":db/allowed"])
    lex = A.load_edn(_LEX / "processKnowledge.edn")
    lex_set = _strip(lex[":defs"][":main"][":record"][":properties"][":sourceLicense"][":enum"])
    code_set = _strip(A.ALLOWED_LICENSES)
    assert schema_set == lex_set == code_set, (schema_set, lex_set, code_set)


def test_three_places_fabricated_false_agrees():
    """schema :db/allowed [false]  ==  lexicon const false  ==  code rejects true (G2)."""
    onto = A.load_edn(_ONTO)
    assert onto[":attributes"][":iiiv.crystal/fabricated"][":db/allowed"] == [False]
    assert onto[":attributes"][":iiiv.wafer/fabricated"][":db/allowed"] == [False]
    lex = A.load_edn(_LEX / "crystalGrowthDesign.edn")
    assert lex[":defs"][":main"][":record"][":properties"][":fabricated"][":const"] is False
    wlex = A.load_edn(_LEX / "waferSpec.edn")
    assert wlex[":defs"][":main"][":record"][":properties"][":fabricated"][":const"] is False
    # code: screen_fabrication raises on true (the 3rd place)
    try:
        A.screen_fabrication({"x": {":iiiv.crystal/fabricated": True}}, {})
    except ValueError:
        pass
    else:
        raise AssertionError("code did not reject fabricated=true")


def test_three_places_in_sourcing_clean_set_agrees():
    """G4 in-sourcing has a deliberate asymmetry: the schema can REPRESENT :unverified
    (so the analyzer can flag it), but the lexicon enum + code CLEAN_SOURCING list only
    the CLEAN values (a record/clearance exists only after the screen passes). The
    invariant: lexicon enum == code CLEAN_SOURCING, and that clean set ⊂ schema, with
    exactly :unverified as the representable-but-not-clean extra."""
    onto = A.load_edn(_ONTO)
    schema_set = _strip(onto[":attributes"][":iiiv.crystal/in-sourcing"][":db/allowed"])
    lex = A.load_edn(_LEX / "crystalGrowthDesign.edn")
    lex_set = _strip(lex[":defs"][":main"][":record"][":properties"][":inSourcing"][":enum"])
    code_set = _strip(A.CLEAN_SOURCING)
    assert lex_set == code_set, (lex_set, code_set)          # clean set agrees (2 places)
    assert code_set < schema_set                              # clean ⊂ representable
    assert schema_set - code_set == {"unverified"}            # the only flagged-but-representable value


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
