"""test_weave.py — 系図 (keizu) weave validation + concentration. ADR-2606066000."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import expect_raises, run
from weave import (concentration, validate_money, validate_node, validate_rel,
                   weave)

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-relation-graph.kotoba.edn"


def _g():
    return weave(load_edn(SEED))


def test_seed_weaves_clean():
    g = _g()
    assert len(g["nodes"]) >= 15, g["nodes"]
    assert len(g["committees"]) == 3
    assert len(g["rels"]) >= 14
    assert len(g["money"]) == 6


def test_g1_private_person_rejected():
    expect_raises(lambda: validate_node({":node/id": "x", ":node/scope": ":private-person",
                                         ":node/sourcing": ":representative"}), contains="G1")


def test_g4_power_score_rejected():
    expect_raises(lambda: validate_node({":node/id": "x", ":node/scope": ":public-role",
                                         ":node/power-score": 9, ":node/sourcing": ":representative"}),
                  contains="G4")


def test_g2_verdict_rel_kind_rejected():
    bad = {":rel/id": "r", ":rel/source": "a", ":rel/target": "b", ":rel/kind": ":corruption",
           ":rel/non-adjudicating-notice": True, ":rel/sourcing": ":representative",
           ":rel/sources": ["u1", "u2"]}
    expect_raises(lambda: validate_rel(bad), contains="G2")


def test_g2_notice_must_be_true():
    bad = {":rel/id": "r", ":rel/source": "a", ":rel/target": "b", ":rel/kind": ":funding-tie",
           ":rel/non-adjudicating-notice": False, ":rel/sourcing": ":representative",
           ":rel/sources": ["u1", "u2"]}
    expect_raises(lambda: validate_rel(bad), contains="non-adjudicating")


def test_g3_rel_needs_two_sources():
    bad = {":rel/id": "r", ":rel/source": "a", ":rel/target": "b", ":rel/kind": ":funding-tie",
           ":rel/non-adjudicating-notice": True, ":rel/sourcing": ":representative",
           ":rel/sources": ["only-one"]}
    expect_raises(lambda: validate_rel(bad), contains="G3")


def test_g2_bribe_money_rejected():
    bad = {":money/id": "m", ":money/payer": "a", ":money/payee": "b", ":money/kind": ":bribe",
           ":money/sourcing": ":representative", ":money/sources": ["u1", "u2"]}
    expect_raises(lambda: validate_money(bad), contains="G2")


def test_g3_money_needs_two_sources():
    bad = {":money/id": "m", ":money/payer": "a", ":money/payee": "b", ":money/kind": ":subsidy",
           ":money/sourcing": ":representative", ":money/sources": ["u1"]}
    expect_raises(lambda: validate_money(bad), contains="G3")


def test_cross_committee_seat_detected():
    c = concentration(_g())
    seats = {x["seat"] for x in c["cross_committee_seats"]}
    assert "jp-fsc-biz-1" in seats, c["cross_committee_seats"]


def test_committee_cross_organ():
    c = concentration(_g())
    fsc = next(x for x in c["committee_cross_organ"] if x["committee"] == "jp-fiscal-system-council")
    assert fsc["member_count"] == 3
    assert fsc["distinct_organs"] >= 2


def test_money_hhi_in_range():
    c = concentration(_g())
    hhi = c["money_concentration"]["hhi"]
    assert 0.0 < hhi <= 1.0, hhi
    # jp-vendor-x receives the most flows → should be the top share
    assert c["money_concentration"]["shares"][0][0] == "jp-vendor-x"


def test_revolving_door_detected():
    c = concentration(_g())
    assert any(r["from"] == "jp-meti" for r in c["revolving_door"]), c["revolving_door"]


if __name__ == "__main__":
    run("weave", [(k, v) for k, v in sorted(globals().items())
                  if k.startswith("test_") and callable(v)])
