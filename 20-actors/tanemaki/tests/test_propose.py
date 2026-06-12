#!/usr/bin/env python3
"""tanemaki 種蒔き — scorecard + advisory-proposal tests (ADR-2606122001). Pure stdlib.

The action-layer expression of the gates:
  - G1: build_proposal REFUSES (raises) an :excluded or :insufficient-evidence org; the record
    it does build is structurally advisory (advisory=true, bindsFund=false, decidedBy=vote,
    drafted-unsent)
  - G2: investment instruments raise (equity/debt/convertible/…); investment-return language
    in a justification raises
  - G4: the scorecard is content-addressed (CIDv1+SHA-256) and the proposal carries the CID
  - milestone-escrow requires :watched-by milestones
"""
import sys, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
from analyze import load  # noqa: E402
from propose import (build_proposal, render_scorecard, assert_instrument,  # noqa: E402
                     assert_no_investment_language, FORBIDDEN_INSTRUMENTS)
from cid import cidv1_raw  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-stewardship-graph.kotoba.edn"


def _graph():
    return load(SEED)


def test_proposal_is_structurally_advisory():
    nodes, edges = _graph()
    p = build_proposal("org.foodbank", nodes, edges, amount_usdc_micros=5_000_000_000,
                       instrument=":grant", justification="地域の食料再分配 commons の運営継続")
    assert p["$type"] == "com.etzhayyim.tanemaki.grantProposal"
    assert p["advisory"] is True and p["bindsFund"] is False
    assert p["decidedBy"] == "1-sbt-1-vote" and p["status"] == "drafted-unsent"
    assert p["orgSynthetic"] is True  # G6 — the seed is fictional


def test_g1_refuses_excluded_org():
    nodes, edges = _graph()
    for org in ("org.adfunded-media", "org.surveil-vendor", "org.equity-seeker"):
        try:
            build_proposal(org, nodes, edges)
            raise SystemExit(f"FAIL: proposal built for excluded org {org}")
        except AssertionError as ex:
            assert "REFUSAL" in str(ex)


def test_g1_refuses_under_evidenced_org():
    nodes, edges = _graph()
    for org in ("org.newgroup", "org.opaque-finance"):
        try:
            build_proposal(org, nodes, edges)
            raise SystemExit(f"FAIL: proposal built for under-evidenced org {org}")
        except AssertionError as ex:
            assert "REFUSAL" in str(ex)


def test_g2_investment_instruments_unrepresentable():
    for inst in FORBIDDEN_INSTRUMENTS:
        try:
            assert_instrument(inst)
            raise SystemExit(f"FAIL: {inst} accepted")
        except AssertionError as ex:
            assert "G2" in str(ex)
    nodes, edges = _graph()
    try:
        build_proposal("org.foodbank", nodes, edges, instrument=":equity")
        raise SystemExit("FAIL: equity proposal built")
    except AssertionError as ex:
        assert "G2" in str(ex)


def test_g2_investment_language_rejected():
    for bad in ("運転資金と引き換えに持分10%を取得", "expected ROI of 3x", "revenue share 5%",
                "配当を見込む", "exit 時のキャピタルゲイン"):
        try:
            assert_no_investment_language(bad)
            raise SystemExit(f"FAIL: accepted {bad!r}")
        except AssertionError as ex:
            assert "G2" in str(ex)
    assert assert_no_investment_language("OSS maintainer の持続のための交付") is not None


def test_g4_scorecard_content_addressed():
    nodes, edges = _graph()
    card = render_scorecard("org.osslib", nodes, edges)
    assert "参考意見" in card and "FICTIONAL" in card  # advisory + G6 disclosed on the card
    p = build_proposal("org.osslib", nodes, edges, instrument=":milestone-escrow")
    assert p["scorecardCid"] == cidv1_raw(card.encode("utf-8"))
    assert p["scorecardSha256"].startswith("0x") and len(p["scorecardSha256"]) == 66


def test_milestone_escrow_requires_milestones():
    nodes, edges = _graph()
    p = build_proposal("org.osslib", nodes, edges, instrument=":milestone-escrow")
    assert p["milestones"] == ["ms.osslib-1", "ms.osslib-2"]
    # an eligible org WITHOUT milestones cannot take the escrow rail
    try:
        build_proposal("org.foodbank", nodes, edges, instrument=":milestone-escrow")
        raise SystemExit("FAIL: escrow without milestones")
    except AssertionError as ex:
        assert "milestone" in str(ex)


def test_proposal_deterministic():
    nodes, edges = _graph()
    a = build_proposal("org.foodbank", nodes, edges)
    b = build_proposal("org.foodbank", nodes, edges)
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
