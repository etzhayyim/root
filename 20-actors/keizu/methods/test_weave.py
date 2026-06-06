"""test_weave.py — 系図 (keizu) weave validation + concentration. ADR-2606066000."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import expect_raises, run
from weave import (active_as_of, assert_integrity, check_integrity,
                   concentration, connector_seats, statement_index,
                   validate_committee, validate_money, validate_node,
                   validate_rel, validate_statement, weave)

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


def test_g9_no_doxxing_email_rejected():
    expect_raises(lambda: validate_node({":node/id": "x", ":node/scope": ":public-role",
                                         ":node/email": "a@b.jp", ":node/sourcing": ":representative"}),
                  contains="no-doxxing")


def test_g9_no_doxxing_home_address_rejected():
    expect_raises(lambda: validate_node({":node/id": "x", ":node/scope": ":public-role",
                                         ":node/address": "1-2-3", ":node/sourcing": ":representative"}),
                  contains="no-doxxing")


def test_g9_no_doxxing_mynumber_rejected():
    expect_raises(lambda: validate_node({":node/id": "x", ":node/scope": ":public-role",
                                         ":node/mynumber": "999", ":node/sourcing": ":representative"}),
                  contains="no-doxxing")


def test_public_organ_node_still_valid():
    # a normal public-seat node (label/jurisdiction/organ) must NOT trip the PII guard
    validate_node({":node/id": "x", ":node/scope": ":public-role", ":node/label": "会長 (seat)",
                   ":node/jurisdiction": "jp", ":node/organ": "財務省", ":node/sourcing": ":representative"})


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


def test_rider_deny_commercial_gov_intel_source_rel():
    bad = {":rel/id": "r", ":rel/source": "a", ":rel/target": "b", ":rel/kind": ":funding-tie",
           ":rel/non-adjudicating-notice": True, ":rel/sourcing": ":representative",
           ":rel/sources": ["https://about.bloomberg.com/government", "https://x.gov/"]}
    expect_raises(lambda: validate_rel(bad), contains="Rider §2(e)")


def test_rider_deny_commercial_gov_intel_source_money():
    bad = {":money/id": "m", ":money/payer": "a", ":money/payee": "b", ":money/kind": ":subsidy",
           ":money/sourcing": ":representative", ":money/sources": ["fiscalnote feed", "https://x.gov/"]}
    expect_raises(lambda: validate_money(bad), contains="Rider §2(e)")


def test_g2_bribe_money_rejected():
    bad = {":money/id": "m", ":money/payer": "a", ":money/payee": "b", ":money/kind": ":bribe",
           ":money/sourcing": ":representative", ":money/sources": ["u1", "u2"]}
    expect_raises(lambda: validate_money(bad), contains="G2")


def test_g3_money_needs_two_sources():
    bad = {":money/id": "m", ":money/payer": "a", ":money/payee": "b", ":money/kind": ":subsidy",
           ":money/sourcing": ":representative", ":money/sources": ["u1"]}
    expect_raises(lambda: validate_money(bad), contains="G3")


def _money(amount):
    return {":money/id": "m", ":money/payer": "a", ":money/payee": "b", ":money/kind": ":subsidy",
            ":money/sourcing": ":representative", ":money/sources": ["u1", "u2"], ":money/amount": amount}


def test_negative_amount_rejected():
    expect_raises(lambda: validate_money(_money(-1.0)), contains="≥ 0")


def test_nan_amount_rejected():
    expect_raises(lambda: validate_money(_money(float("nan"))), contains="finite")


def test_inf_amount_rejected():
    expect_raises(lambda: validate_money(_money(float("inf"))), contains="finite")


def test_non_numeric_amount_rejected():
    expect_raises(lambda: validate_money(_money("lots")), contains="number")


def test_zero_amount_allowed():
    validate_money(_money(0.0))   # 0 is degenerate but not corrupting; allowed


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


# ── edge branches ────────────────────────────────────────────────────────────────
def test_g11_node_missing_sourcing_rejected():
    expect_raises(lambda: validate_node({":node/id": "x", ":node/scope": ":public-role"}),
                  contains="G11")


def test_g11_rel_missing_sourcing_rejected():
    bad = {":rel/id": "r", ":rel/source": "a", ":rel/target": "b", ":rel/kind": ":funding-tie",
           ":rel/non-adjudicating-notice": True, ":rel/sources": ["u1", "u2"]}
    expect_raises(lambda: validate_rel(bad), contains="G11")


def test_rel_sources_not_a_list_rejected():
    bad = {":rel/id": "r", ":rel/source": "a", ":rel/target": "b", ":rel/kind": ":funding-tie",
           ":rel/non-adjudicating-notice": True, ":rel/sourcing": ":representative",
           ":rel/sources": "u1,u2"}
    expect_raises(lambda: validate_rel(bad), contains="G3")


def test_empty_graph_concentration_is_safe():
    c = concentration(weave({}))
    assert c["node_count"] == 0
    assert c["money_concentration"]["hhi"] == 0.0          # no div-by-zero
    assert c["money_concentration"]["total"] == 0.0
    assert c["cross_committee_seats"] == []
    assert c["revolving_door"] == []


def test_payer_concentration():
    c = concentration(_g())
    pc = c["payer_concentration"]
    assert 0.0 < pc["hhi"] <= 1.0, pc
    # jp-meti disburses the most flows in the seed → top payer share
    assert pc["shares"][0][0] == "jp-meti", pc["shares"]


def test_payer_concentration_empty_safe():
    pc = concentration(weave({}))["payer_concentration"]
    assert pc["hhi"] == 0.0 and pc["total"] == 0.0 and pc["shares"] == []


def test_award_and_fund_co_occurrence():
    c = concentration(_g())
    af = c["award_and_fund"]
    # jp-vendor-x received procurement-award + subsidy AND donated to jp-party-a
    vx = next((r for r in af if r["node"] == "jp-vendor-x"), None)
    assert vx is not None, af
    assert "jp-meti" in vx["received_from"]
    assert "jp-party-a" in vx["donated_to"]
    assert vx["received_total"] > 0 and vx["donated_total"] > 0


def test_award_and_fund_requires_both_legs():
    # us-vendor-y received an award but made no donation → must NOT appear
    nodes = {r["node"] for r in concentration(_g())["award_and_fund"]}
    assert "us-vendor-y" not in nodes
    assert "ec-eg-ind-1" not in nodes   # got a grant, no donation


def test_award_and_fund_empty_safe():
    assert concentration(weave({}))["award_and_fund"] == []


def test_connector_seat_bridges_two_organs():
    c = concentration(_g())
    # jp-fsc-biz-1 sits on 財政制度等審議会 (財務省) + 規制改革推進会議 (内閣府) → bridges 2 organs
    conn = next((r for r in c["connector_seats"] if r["seat"] == "jp-fsc-biz-1"), None)
    assert conn is not None, c["connector_seats"]
    assert conn["organs_bridged"] >= 2


def test_connector_requires_distinct_organs():
    # two committees under the SAME organ → not a cross-organ connector
    g = weave({
        ":nodes": [{":node/id": "s1", ":node/scope": ":public-role", ":node/sourcing": ":representative"}],
        ":committees": [{":committee/id": "c1", ":committee/organ": "X", ":committee/members": ["s1"],
                         ":committee/sources": ["u"], ":committee/sourcing": ":representative"},
                        {":committee/id": "c2", ":committee/organ": "X", ":committee/members": ["s1"],
                         ":committee/sources": ["u"], ":committee/sourcing": ":representative"}],
        ":rels": [
            {":rel/id": "a", ":rel/source": "s1", ":rel/target": "c1", ":rel/kind": ":committee-membership",
             ":rel/non-adjudicating-notice": True, ":rel/sourcing": ":representative", ":rel/sources": ["u", "v"]},
            {":rel/id": "b", ":rel/source": "s1", ":rel/target": "c2", ":rel/kind": ":committee-membership",
             ":rel/non-adjudicating-notice": True, ":rel/sourcing": ":representative", ":rel/sources": ["u", "v"]},
        ],
    })
    assert connector_seats(g) == []   # same organ → no cross-organ bridge


def test_active_as_of_is_monotonic():
    g = _g()
    early = active_as_of(g, 20240101)   # before everything
    mid = active_as_of(g, 20250301)
    late = active_as_of(g, 20260101)    # after everything
    assert early["active_rels"] == 0
    assert early["active_rels"] <= mid["active_rels"] <= late["active_rels"]
    assert late["active_rels"] == late["total_rels"]
    assert late["active_committees"] == late["total_committees"]


def test_active_as_of_partial_window():
    # the revolving-door edge (as-of 20241001) is active by end-2024 but no 2025 memberships are
    g = _g()
    snap = active_as_of(g, 20241101)
    assert 0 < snap["active_rels"] < snap["total_rels"]


# ── statements (発言) ──────────────────────────────────────────────────────────
def test_statement_needs_speaker():
    expect_raises(lambda: validate_statement({":statement/id": "s", ":statement/sources": ["u"],
                                              ":statement/sourcing": ":representative"}),
                  contains="speaker")


def test_statement_needs_source():
    expect_raises(lambda: validate_statement({":statement/id": "s", ":statement/speaker": "a",
                                              ":statement/sources": [], ":statement/sourcing": ":representative"}),
                  contains="G3")


def test_statement_needs_sourcing():
    expect_raises(lambda: validate_statement({":statement/id": "s", ":statement/speaker": "a",
                                              ":statement/sources": ["u"]}), contains="G11")


def _committee(**over):
    base = {":committee/id": "c1", ":committee/members": ["s1"],
            ":committee/sources": ["u"], ":committee/sourcing": ":representative"}
    base.update(over)
    return base


def test_committee_valid():
    validate_committee(_committee())


def test_committee_needs_member():
    expect_raises(lambda: validate_committee(_committee(**{":committee/members": []})), contains="G1")


def test_committee_needs_source():
    expect_raises(lambda: validate_committee(_committee(**{":committee/sources": []})), contains="G3")


def test_committee_needs_sourcing():
    c = _committee()
    del c[":committee/sourcing"]
    expect_raises(lambda: validate_committee(c), contains="G11")


def test_committee_deny_commercial_gov_intel_source():
    expect_raises(lambda: validate_committee(_committee(**{":committee/sources": ["bloomberg gov feed"]})),
                  contains="Rider §2(e)")


def test_seed_committees_validate():
    for c in _g()["committees"].values():
        validate_committee(c)


def test_statement_deny_commercial_gov_intel_source():
    # the SOURCE_DENY list must apply to statements too, not only rels/money
    bad = {":statement/id": "s", ":statement/speaker": "a", ":statement/sourcing": ":representative",
           ":statement/sources": ["https://about.bloomberg.com/government"]}
    expect_raises(lambda: validate_statement(bad), contains="Rider §2(e)")


def test_statement_index_by_speaker_and_topic():
    si = concentration(_g())["statement_index"]
    assert si["count"] == 3
    speakers = dict(si["by_speaker"])
    assert "jp-fsc-chair" in speakers
    topics = {t["topic"] for t in si["by_topic"]}
    assert any("fiscal" in t.lower() for t in topics)


def test_statement_index_empty_safe():
    si = concentration(weave({}))["statement_index"]
    assert si["count"] == 0 and si["by_speaker"] == [] and si["by_topic"] == []


# ── referential integrity ────────────────────────────────────────────────────────
def test_seed_has_no_dangling_refs():
    rep = check_integrity(_g())
    assert rep["dangling_count"] == 0, rep["dangling"]
    assert_integrity(_g())   # strict mode must not raise on a clean seed


def test_dangling_rel_target_detected():
    g = weave({
        ":nodes": [{":node/id": "s1", ":node/scope": ":public-role", ":node/sourcing": ":representative"}],
        ":rels": [{":rel/id": "r", ":rel/source": "s1", ":rel/target": "ghost",
                   ":rel/kind": ":appointment", ":rel/non-adjudicating-notice": True,
                   ":rel/sourcing": ":representative", ":rel/sources": ["u", "v"]}],
    })
    rep = check_integrity(g)
    assert rep["dangling_count"] == 1
    assert rep["dangling"][0]["ref"] == "ghost" and rep["dangling"][0]["field"] == "target"
    expect_raises(lambda: assert_integrity(g), contains="dangling")


def test_dangling_money_payee_detected():
    g = weave({
        ":nodes": [{":node/id": "jp-meti", ":node/scope": ":public-org", ":node/sourcing": ":representative"}],
        ":money": [{":money/id": "m", ":money/payer": "jp-meti", ":money/payee": "nope",
                    ":money/kind": ":subsidy", ":money/sourcing": ":representative",
                    ":money/sources": ["u", "v"]}],
    })
    rep = check_integrity(g)
    assert rep["dangling_count"] == 1 and rep["dangling"][0]["field"] == "payee"


def test_dangling_committee_member_detected():
    g = weave({
        ":committees": [{":committee/id": "c1", ":committee/members": ["ghost-seat"],
                         ":committee/sources": ["u"], ":committee/sourcing": ":representative"}],
    })
    rep = check_integrity(g)
    assert rep["dangling_count"] == 1 and rep["dangling"][0]["field"] == "member"


def test_rel_target_may_be_a_committee():
    # a tie pointing at a committee id (not a node) is NOT dangling — rel id-space includes committees
    g = weave({
        ":nodes": [{":node/id": "s1", ":node/scope": ":public-role", ":node/sourcing": ":representative"}],
        ":committees": [{":committee/id": "c1", ":committee/members": ["s1"],
                         ":committee/sources": ["u"], ":committee/sourcing": ":representative"}],
        ":rels": [{":rel/id": "r", ":rel/source": "s1", ":rel/target": "c1",
                   ":rel/kind": ":committee-membership", ":rel/non-adjudicating-notice": True,
                   ":rel/sourcing": ":representative", ":rel/sources": ["u", "v"]}],
    })
    assert check_integrity(g)["dangling_count"] == 0


def test_unknown_organ_member_is_tolerated():
    g = weave({
        ":nodes": [{":node/id": "s1", ":node/scope": ":public-role",
                    ":node/sourcing": ":representative"}],  # no :node/organ
        ":committees": [{":committee/id": "c1", ":committee/members": ["s1", "ghost"],
                         ":committee/sources": ["u"], ":committee/sourcing": ":representative"}],
    })
    rows = concentration(g)["committee_cross_organ"]
    assert rows[0]["member_count"] == 2          # both counted
    assert "(unknown)" in rows[0]["organs"]       # missing-organ seat folded to (unknown)


if __name__ == "__main__":
    run("weave", [(k, v) for k, v in sorted(globals().items())
                  if k.startswith("test_") and callable(v)])
