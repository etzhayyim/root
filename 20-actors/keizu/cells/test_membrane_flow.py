"""test_membrane_flow.py — 系図 (keizu) cell-chain integration. ADR-2606066000.

Unit tests prove each cell in isolation (test_state_machines.py); THIS proves they COMPOSE into
the documented pipeline on the runtime path:

    ingest ─▶ committee_graph ─▶ relation_weave ─▶ social_post (dry-run)
             money_graph ──────┘

One public-source batch is threaded through all five cell state machines in sequence; the finding
that falls out of relation_weave becomes social_post's subject — proving the wire holds end-to-end.
Standalone-runnable (the ake convention). `.solve()` is never called (R0 scaffolds raise).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "methods"))
from _t import run  # noqa: E402


def _load(cell: str, mod: str):
    name = f"keizu_{cell}_{mod}_chain"
    spec = importlib.util.spec_from_file_location(name, HERE / cell / f"{mod}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# one self-contained batch (public seats/organs, ≥2-sourced factual ties + flows)
_NODES = [{"id": "s1", "scope": ":public-role", "organ": "MOF"},
          {"id": "s2", "scope": ":public-role", "organ": "Cabinet"}]
_COMMITTEES = [{"id": "c1", "organ": "MOF", "members": ["s1", "s2"]},
               {"id": "c2", "organ": "Cabinet", "members": ["s2"]}]
_RELS = [{"kind": ":committee-membership", "sources": ["a", "b"]}]
_MONEY = [{"payee": "vendor", "amount": 90.0, "kind": ":procurement-award", "sources": ["a", "b"]},
          {"payee": "other", "amount": 10.0, "kind": ":subsidy", "sources": ["a", "b"]}]


def test_full_membrane_chain_reaches_dry_run_post():
    # 1) ingest — screen + record the batch
    ing = _load("ingest", "state_machine")
    st = ing.transition_to_screened({"cell_state": {}, "nodes": _NODES, "rels": _RELS, "money": _MONEY})
    assert st["cell_state"]["phase"] == "screened"
    st = ing.transition_to_recorded(st)
    assert st["cell_state"]["phase"] == "recorded" and st["cell_state"]["recorded"] > 0

    # 2) committee_graph — compose composition + co-membership
    cg = _load("committee_graph", "state_machine")
    cs = cg.transition_to_composed({"cell_state": {}, "committees": _COMMITTEES})
    assert cs["cell_state"]["phase"] == "composed"
    assert any(x["seat"] == "s2" for x in cs["cell_state"]["co_membership"])  # s2 on c1+c2

    # 3) money_graph — aggregate per-payee HHI
    mg = _load("money_graph", "state_machine")
    ms = mg.transition_to_aggregated({"cell_state": {}, "money": _MONEY})
    assert ms["cell_state"]["phase"] == "aggregated"
    assert ms["cell_state"]["shares"][0][0] == "vendor"  # top payee

    # 4) relation_weave — derive a cross-organ finding from the composition
    rw = _load("relation_weave", "state_machine")
    ws = rw.transition_to_woven({"cell_state": {},
                                 "nodes": {n["id"]: n for n in _NODES},
                                 "committees": _COMMITTEES})
    assert ws["cell_state"]["phase"] == "woven"
    finding = ws["cell_state"]["findings"][0]
    assert finding["distinct_organs"] >= 1

    # 5) social_post — the finding becomes a DRY-RUN post subject (the wire holds)
    sp = _load("social_post", "state_machine")
    ps = sp.transition_to_drafted({"cell_state": {},
                                   "subject": f"committee {finding['committee']} cross-organ",
                                   "sources": ["a", "b"]})
    assert ps["cell_state"]["phase"] == "drafted"
    payload = ps["cell_state"]["payload"]
    assert payload[":post/status"] == ":dry-run"
    assert payload[":post/server-held-key"] is False
    assert finding["committee"] in payload[":post/subject"]


def test_chain_aborts_when_ingest_refuses():
    # a private-person node at the head refuses; the chain must not proceed to a post
    ing = _load("ingest", "state_machine")
    st = ing.transition_to_screened({"cell_state": {}, "nodes": [{"scope": ":private-person"}]})
    assert st["cell_state"]["phase"] == "refused"
    st2 = ing.transition_to_recorded(st)         # cannot record an unscreened batch
    assert st2["cell_state"]["phase"] == "refused"


def test_chain_refuses_published_at_tail():
    # even with a clean head, a 'published' request at the tail is refused (G8)
    sp = _load("social_post", "state_machine")
    ps = sp.transition_to_drafted({"cell_state": {}, "subject": "x", "sources": ["a", "b"],
                                   "requested_status": "published"})
    assert ps["cell_state"]["phase"] == "refused" and "G8" in ps["cell_state"]["refusal"]


if __name__ == "__main__":
    run("membrane-flow", [(k, v) for k, v in sorted(globals().items())
                          if k.startswith("test_") and callable(v)])
