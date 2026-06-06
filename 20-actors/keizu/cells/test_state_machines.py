"""test_state_machines.py — 系図 (keizu) cell state machines + R0 .solve() raise. ADR-2606066000.

Standalone-runnable. Adds the cell dirs to sys.path so each cell's state_machine + cell import.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
for d in ("ingest", "committee_graph", "money_graph", "relation_weave", "social_post"):
    sys.path.insert(0, str(HERE / d))
sys.path.insert(0, str(HERE.parent / "methods"))

from _t import run  # noqa: E402

import importlib.util  # noqa: E402


def _load(cell: str, mod: str):
    path = HERE / cell / f"{mod}.py"
    name = f"keizu_{cell}_{mod}"
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m  # @dataclass needs the module registered (Python 3.12+)
    spec.loader.exec_module(m)
    return m


# ── ingest ───────────────────────────────────────────────────────────────────────
def test_ingest_clean_batch_records():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {},
        "nodes": [{"scope": ":public-role"}],
        "rels": [{"kind": ":funding-tie", "sources": ["a", "b"]}],
        "money": [{"kind": ":subsidy", "sources": ["a", "b"]}]})
    assert st["cell_state"]["phase"] == "screened"
    st2 = sm.transition_to_recorded(st)
    assert st2["cell_state"]["phase"] == "recorded"
    assert st2["cell_state"]["recorded"] == 3


def test_ingest_refuses_private_node():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {}, "nodes": [{"scope": ":private-person"}]})
    assert st["cell_state"]["phase"] == "refused"
    assert "G1" in st["cell_state"]["refusal"]


def test_ingest_refuses_verdict_rel():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {},
        "rels": [{"kind": ":bribe", "sources": ["a", "b"]}]})
    assert st["cell_state"]["phase"] == "refused" and "G2" in st["cell_state"]["refusal"]


def test_ingest_refuses_under_sourced():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {},
        "rels": [{"kind": ":funding-tie", "sources": ["a"]}]})
    assert st["cell_state"]["phase"] == "refused" and "G3" in st["cell_state"]["refusal"]


# ── committee_graph ────────────────────────────────────────────────────────────────
def test_committee_co_membership():
    sm = _load("committee_graph", "state_machine")
    st = sm.transition_to_composed({"cell_state": {}, "committees": [
        {"id": "c1", "members": ["s1", "s2"]},
        {"id": "c2", "members": ["s2", "s3"]}]})
    assert st["cell_state"]["phase"] == "composed"
    seats = {x["seat"] for x in st["cell_state"]["co_membership"]}
    assert seats == {"s2"}


# ── money_graph ────────────────────────────────────────────────────────────────────
def test_money_aggregates_hhi():
    sm = _load("money_graph", "state_machine")
    st = sm.transition_to_aggregated({"cell_state": {}, "money": [
        {"payee": "x", "amount": 75}, {"payee": "y", "amount": 25}]})
    assert st["cell_state"]["phase"] == "aggregated"
    assert abs(st["cell_state"]["hhi"] - (0.75**2 + 0.25**2)) < 1e-6
    assert st["cell_state"]["shares"][0][0] == "x"


# ── relation_weave ─────────────────────────────────────────────────────────────────
def test_weave_cross_organ():
    sm = _load("relation_weave", "state_machine")
    st = sm.transition_to_woven({"cell_state": {},
        "nodes": {"s1": {"organ": "A"}, "s2": {"organ": "B"}},
        "committees": [{"id": "c1", "members": ["s1", "s2"]}]})
    assert st["cell_state"]["phase"] == "woven"
    assert st["cell_state"]["findings"][0]["distinct_organs"] == 2


# ── social_post ────────────────────────────────────────────────────────────────────
def test_social_drafts_dry_run():
    sm = _load("social_post", "state_machine")
    st = sm.transition_to_drafted({"cell_state": {}, "subject": "demo委員会", "sources": ["a", "b"]})
    assert st["cell_state"]["phase"] == "drafted"
    p = st["cell_state"]["payload"]
    assert p[":post/status"] == ":dry-run" and p[":post/server-held-key"] is False


def test_social_refuses_published():
    sm = _load("social_post", "state_machine")
    st = sm.transition_to_drafted({"cell_state": {}, "subject": "x", "sources": ["a", "b"],
                                   "requested_status": "published"})
    assert st["cell_state"]["phase"] == "refused" and "G8" in st["cell_state"]["refusal"]


def test_social_refuses_server_key():
    sm = _load("social_post", "state_machine")
    st = sm.transition_to_drafted({"cell_state": {}, "subject": "x", "sources": ["a", "b"],
                                   "server_held_key": True})
    assert st["cell_state"]["phase"] == "refused" and "no-server-key" in st["cell_state"]["refusal"]


def test_social_refuses_under_sourced():
    sm = _load("social_post", "state_machine")
    st = sm.transition_to_drafted({"cell_state": {}, "subject": "x", "sources": ["a"]})
    assert st["cell_state"]["phase"] == "refused" and "G3" in st["cell_state"]["refusal"]


# ── every cell .solve() raises at R0 (G8) ──────────────────────────────────────────
def test_all_cells_solve_raise():
    cases = [("ingest", "IngestCell"), ("committee_graph", "CommitteeGraphCell"),
             ("money_graph", "MoneyGraphCell"), ("relation_weave", "RelationWeaveCell"),
             ("social_post", "SocialPostCell")]
    for cell, cls in cases:
        m = _load(cell, "cell")
        try:
            getattr(m, cls)().solve({})
        except RuntimeError:
            continue
        raise AssertionError(f"{cls}.solve() must raise at R0")


if __name__ == "__main__":
    run("cells", [(k, v) for k, v in sorted(globals().items())
                  if k.startswith("test_") and callable(v)])
