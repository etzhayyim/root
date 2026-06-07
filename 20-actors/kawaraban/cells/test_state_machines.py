#!/usr/bin/env python3
"""kawaraban — tests for the 5 cell state machines + .solve() R0 guards.

Standalone-runnable (`python3 test_state_machines.py`) AND pytest-compatible. Run from the
cells/ directory (each cell is a package with state_machine.py + cell.py).
"""
from __future__ import annotations

from outlet_ingest.state_machine import ingest
from outlet_ingest.cell import OutletIngestCell
from article_mirror.state_machine import mirror
from article_mirror.cell import ArticleMirrorCell
from section_route.state_machine import route
from section_route.cell import SectionRouteCell
from actor_project.state_machine import project
from actor_project.cell import ActorProjectCell
from issue_compose.state_machine import compose
from issue_compose.cell import IssueComposeCell


def _p(r):  # phase
    return r["cell_state"]["phase"]


def _refusal(r):
    return r["cell_state"]["refusal"]


# ── outlet_ingest ──────────────────────────────────────────────────────────
def test_outlet_ingest_ok():
    r = ingest({"outlet_id": "outlet.nhk", "name": "NHK", "kind": "public-broadcaster", "access": "open"})
    assert _p(r) == "ingested"


def test_outlet_ingest_refuses_paywall():
    r = ingest({"outlet_id": "o", "name": "X", "access": "paywall"})
    assert _p(r) == "refused" and "G4" in _refusal(r)


# ── article_mirror ─────────────────────────────────────────────────────────
def test_article_mirror_ok():
    r = mirror({"article_id": "a", "section": "sec.international", "outlet": "outlet.ap",
                "url": "https://apnews.com/x", "headline": "h", "excerpt": "short"})
    assert _p(r) == "mirrored"


def test_article_mirror_refuses_verdict():
    r = mirror({"article_id": "a", "outlet": "o", "url": "u", "verdict": True})
    assert _p(r) == "refused" and "G1" in _refusal(r)


def test_article_mirror_refuses_full_text():
    r = mirror({"article_id": "a", "outlet": "o", "url": "u", "full_text": True})
    assert _p(r) == "refused" and "G4" in _refusal(r)


def test_article_mirror_refuses_speak_as():
    r = mirror({"article_id": "a", "outlet": "o", "url": "u", "speak_as": True})
    assert _p(r) == "refused" and "G9" in _refusal(r)


def test_article_mirror_refuses_missing_url():
    r = mirror({"article_id": "a", "outlet": "o"})
    assert _p(r) == "refused" and "url" in _refusal(r).lower()


# ── section_route ──────────────────────────────────────────────────────────
def test_section_route_ok():
    r = route({"article_id": "a", "men": "economy", "rank_signals": ["recency", "source-diversity"],
               "mentions": [{"target": "did:web:...:kanjo", "targetKind": "actor", "role": "mentioned"}]})
    assert _p(r) == "routed"


def test_section_route_refuses_paid_rank():
    r = route({"article_id": "a", "men": "front", "rank_signals": ["paid-placement"]})
    assert _p(r) == "refused" and "G2" in _refusal(r)


def test_section_route_refuses_bad_role():
    r = route({"article_id": "a", "men": "front", "mentions": [{"target": "x", "role": "accused"}]})
    assert _p(r) == "refused" and "G11" in _refusal(r)


# ── actor_project (the medium) ─────────────────────────────────────────────
def test_actor_project_ok():
    r = project({"article_id": "a", "source_actor": "did:web:...:danjo", "source_tid": "danjo:obs:1",
                 "men": "politics", "member_signed": True, "server_held_key": False})
    assert _p(r) == "projected"


def test_actor_project_refuses_server_key():
    r = project({"article_id": "a", "source_actor": "did", "source_tid": "t",
                 "member_signed": True, "server_held_key": True})
    assert _p(r) == "refused" and "G7" in _refusal(r)


def test_actor_project_refuses_unsigned():
    r = project({"article_id": "a", "source_actor": "did", "source_tid": "t", "member_signed": False})
    assert _p(r) == "refused" and "G7" in _refusal(r)


def test_actor_project_refuses_missing_provenance():
    r = project({"article_id": "a", "source_actor": "did", "member_signed": True})
    assert _p(r) == "refused" and "G11" in _refusal(r)


# ── issue_compose ──────────────────────────────────────────────────────────
def test_issue_compose_unpublished_by_default():
    r = compose({"issue_id": "i", "rank_signals": ["recency", "actor-relevance"], "lead_ids": ["a", "b"]})
    assert _p(r) == "composed"
    assert r["cell_state"]["payload"]["published"] is False  # G7/G8 — unsigned/ungated


def test_issue_compose_publishes_only_when_signed_and_gated():
    r = compose({"issue_id": "i", "member_signed": True, "operator_gated": True})
    assert r["cell_state"]["payload"]["published"] is True


def test_issue_compose_refuses_final():
    r = compose({"issue_id": "i", "final": True})
    assert _p(r) == "refused" and "G10" in _refusal(r)


def test_issue_compose_refuses_paid_rank():
    r = compose({"issue_id": "i", "rank_signals": ["engagement"]})
    assert _p(r) == "refused" and "G2" in _refusal(r)


def test_issue_compose_refuses_server_key():
    r = compose({"issue_id": "i", "server_held_key": True})
    assert _p(r) == "refused" and "G7" in _refusal(r)


# ── .solve() R0 guards ─────────────────────────────────────────────────────
def test_all_cells_solve_raises_at_r0():
    for C in (OutletIngestCell, ArticleMirrorCell, SectionRouteCell, ActorProjectCell, IssueComposeCell):
        try:
            C().solve({})
            assert False, f"{C.__name__}.solve() must raise at R0"
        except RuntimeError as e:
            assert "R0 scaffold" in str(e), e


if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"cells: {len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
