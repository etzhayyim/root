"""Tests for kamado 竈 methods (ADR-2606051500).

Run in isolation (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_kamado.py
"""
from __future__ import annotations

import pathlib

import pytest

import analyze
import carbon_balance as cb
from feedstock_guard import (ALLOWED_FEEDSTOCK, screen_feedstock,
                             screen_intervention)

SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-refinery-graph.kotoba.edn"


def _load():
    return analyze.classify(analyze.load_edn(SEED))


# ── carbon_balance: the empirical thesis ──────────────────────────────────────
def test_fossil_baseline_is_strongly_positive_multigenerational():
    """A fossil→combusted pathway is ~+3.5 tCO2e/t — genuinely multi-generational."""
    base = cb.balance(cb.PATHWAYS[0])
    assert base["net"] > 3.0
    assert not base["passes_d3"]


def test_robotics_apc_cannot_close_the_fossil_gap():
    """Full robotic APC on the SAME fossil pathway barely moves the needle (process only)."""
    base = cb.balance(cb.PATHWAYS[0])
    apc = cb.balance(cb.PATHWAYS[1])
    cut = base["net"] - apc["net"]
    assert cut > 0                       # APC helps a little
    assert cut < 0.20                    # ...but only the ~0.4 process slice, ≤30% of it
    assert not apc["passes_d3"]          # still nowhere near net≤0


def test_closed_loop_pathways_pass_d3():
    """Changing the feedstock to closed-loop carbon is the ONLY route to net≤0."""
    biogenic = cb.balance(cb.Pathway("b", ":biogenic", ":hikari-renewable", ":combusted-fuel", apc=True))
    efuel = cb.balance(cb.Pathway("e", ":captured-co2", ":hikari-renewable", ":combusted-fuel", apc=True))
    locked = cb.balance(cb.Pathway("p", ":biogenic", ":hikari-renewable", ":durable-material", apc=True))
    assert biogenic["passes_d3"] and efuel["passes_d3"] and locked["passes_d3"]
    assert locked["net"] < 0             # carbon locked into a durable material is net-negative


# ── feedstock_guard: G1 / G3 structural invariants ────────────────────────────
def test_g1_fossil_virgin_crude_is_not_representable():
    with pytest.raises(ValueError, match="G1 violation"):
        screen_feedstock(":fossil-virgin-crude", ctx="test")


def test_g1_allows_only_closed_loop_carbon():
    for f in ALLOWED_FEEDSTOCK:
        assert screen_feedstock(f) == f


def test_g3_refuses_fossil_life_extension():
    for bad in (":expand", ":restart-fossil", ":revamp-throughput"):
        with pytest.raises(ValueError, match="G3 violation"):
            screen_intervention(bad, ctx="test")
    for ok in (":decommission", ":convert", ":remediate", ":monitor"):
        assert screen_intervention(ok) == ok


def test_origin_credit_rejects_fossil_origin_silent_zero():
    """Fossil origin gets ZERO credit (the stock→flow harm); closed-loop gets the draw-down."""
    assert cb.origin_credit(":fossil-virgin-crude") == 0.0
    assert cb.origin_credit(":biogenic") == -cb.C_PROD
    assert cb.origin_credit(":captured-co2") == -cb.C_PROD


# ── analyze: the seed graph is charter-clean end to end ────────────────────────
def test_seed_parses_and_classifies():
    refineries, units, outages, decoms, synths = _load()
    assert refineries and units and decoms and synths
    assert "rf.jp.negishi" in refineries
    assert "syn.bio-polymer" in synths


def test_seed_every_synthesis_feedstock_is_representable():
    *_, synths = _load()
    for sid, s in synths.items():
        assert s.get(":synthesis/feedstock-class") in ALLOWED_FEEDSTOCK, sid


def test_analyze_runs_and_all_synthesis_pass_d3():
    refineries, units, outages, decoms, synths = _load()
    a = analyze.analyze(refineries, units, outages, decoms, synths)
    assert a["syn_pass"] == len(synths)
    assert a["decom_keyless"] is True


def test_analyze_raises_if_seed_smuggles_a_fossil_synthesis():
    refineries, units, outages, decoms, synths = _load()
    synths["syn.bad"] = {":synthesis/id": "syn.bad",
                         ":synthesis/feedstock-class": ":fossil-virgin-crude"}
    with pytest.raises(ValueError, match="G1 violation"):
        analyze.analyze(refineries, units, outages, decoms, synths)
