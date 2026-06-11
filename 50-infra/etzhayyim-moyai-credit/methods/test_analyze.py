"""Tests: the end-to-end demo runs and its asserted properties hold."""

from __future__ import annotations

from _harness import run_suite

import analyze


def test_run_returns_report():
    r = analyze.run()
    assert "mints" in r and "draws" in r and "invariants" in r


def test_sybil_mints_nothing_honest_mints():
    r = analyze.run()
    assert r["mints"]["did:key:cain"]["minted"] == 0          # sybil
    assert r["mints"]["did:key:abel"]["minted"] == 60         # honest, full batch
    assert r["mints"]["did:key:seth"]["minted"] == 40
    assert r["mints"]["did:key:noah"]["minted"] == 20


def test_invariants_hold():
    r = analyze.run()
    inv = r["invariants"]
    assert inv["cash_zero"] is True
    assert inv["affects_bhi"] is False
    assert inv["conservation_minted>=burned"] is True
    assert inv["floor_equal_for_all"] is True


def test_draw_scenarios_have_expected_shapes():
    r = analyze.run()
    decs = [d["decision"] for d in r["draws"]]
    assert "free-subsistence" in decs   # within floor
    assert "free-idle" in decs          # surplus idle
    assert "charge-surplus" in decs     # surplus + contention + credit
    assert "deferred" in decs           # surplus + contention + no credit
    # freeloader with no credit still got essentials on every draw
    for d in r["draws"]:
        assert d["essential_guaranteed"] is True


run_suite("test_analyze", [
    ("run_returns_report", test_run_returns_report),
    ("sybil_vs_honest", test_sybil_mints_nothing_honest_mints),
    ("invariants_hold", test_invariants_hold),
    ("draw_scenarios", test_draw_scenarios_have_expected_shapes),
])
