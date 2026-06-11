"""test_state_machines.py — 潮目 (shionome) cell state machines + R0 .solve() raise. ADR-2606072200.

Standalone-runnable. Adds the cell dirs to sys.path so each cell's state_machine + cell import.
"""
from __future__ import annotations

import importlib.util  # noqa: E402
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
for d in ("ingest", "flow_graph", "rotation_weave", "regime_observer", "social_post"):
    sys.path.insert(0, str(HERE / d))
sys.path.insert(0, str(HERE.parent / "methods"))

from _t import expect_raises, run  # noqa: E402


def _load(cell: str, mod: str):
    path = HERE / cell / f"{mod}.py"
    name = f"shionome_{cell}_{mod}"
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m  # @dataclass needs the module registered (Python 3.12+)
    spec.loader.exec_module(m)
    return m


# ── ingest ───────────────────────────────────────────────────────────────────────
def test_ingest_clean_batch_records():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {},
        "buckets": [{"scope": ":asset-class"}],
        "flows": [{"kind": ":rotation", "sources": ["a", "b"]}],
        "snapshots": []})
    assert st["cell_state"]["phase"] == "screened"
    st2 = sm.transition_to_recorded(st)
    assert st2["cell_state"]["phase"] == "recorded"
    assert st2["cell_state"]["recorded"] == 2


def test_ingest_refuses_person_bucket():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {}, "buckets": [{"scope": ":individual"}]})
    assert st["cell_state"]["phase"] == "refused"
    assert "G1" in st["cell_state"]["refusal"]


def test_ingest_refuses_trade_token_flow_kind():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {},
        "flows": [{"kind": ":buy", "sources": ["a", "b"]}]})
    assert st["cell_state"]["phase"] == "refused"
    assert "G2" in st["cell_state"]["refusal"]


def test_ingest_refuses_undersourced_flow():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_screened({"cell_state": {},
        "flows": [{"kind": ":rotation", "sources": ["a"]}]})
    assert st["cell_state"]["phase"] == "refused"
    assert "G3" in st["cell_state"]["refusal"]


def test_ingest_cannot_record_unscreened():
    sm = _load("ingest", "state_machine")
    st = sm.transition_to_recorded({"cell_state": {"phase": "init"}})
    assert st["cell_state"]["phase"] == "refused"


# ── flow_graph ─────────────────────────────────────────────────────────────────────
def test_flow_graph_indexes_net():
    sm = _load("flow_graph", "state_machine")
    st = sm.transition_to_indexed({"cell_state": {}, "flows": [
        {"kind": ":rotation", "source": "bonds", "target": "eq", "magnitude": 10.0},
        {"kind": ":fund-inflow", "source": "external", "target": "eq", "magnitude": 5.0},
        {"kind": ":cross-correlation", "source": "eq", "target": "tech", "magnitude": 0.9}]})
    net = st["cell_state"]["net"]
    assert net["eq"] == 15.0          # 10 in + 5 in
    assert net["bonds"] == -10.0      # 10 out
    assert "tech" not in net          # correlation excluded from money math


# ── rotation_weave ─────────────────────────────────────────────────────────────────
def test_rotation_weave_ranks_pairs():
    sm = _load("rotation_weave", "state_machine")
    st = sm.transition_to_woven({"cell_state": {}, "flows": [
        {"kind": ":rotation", "source": "bonds", "target": "eq", "magnitude": 12.0},
        {"kind": ":rotation", "source": "cash", "target": "eq", "magnitude": 8.0},
        {"kind": ":cross-correlation", "source": "eq", "target": "tech", "magnitude": 0.9}]})
    pairs = st["cell_state"]["pairs"]
    assert pairs[0] == ["bonds", "eq", 12.0]
    assert all(p[0] != "eq" or p[1] != "tech" for p in pairs)  # correlation not a rotation


# ── regime_observer ────────────────────────────────────────────────────────────────
def test_regime_observer_risk_on():
    sm = _load("regime_observer", "state_machine")
    st = sm.transition_to_observed({"cell_state": {},
        "net": {"eq": 20.0, "bonds": -18.0},
        "risk_tag": {"eq": "risk", "bonds": "safe"}})
    cs = st["cell_state"]
    assert cs["regime"] == "risk-on"
    assert cs["no_trade_notice"] is True


def test_regime_observer_indeterminate():
    sm = _load("regime_observer", "state_machine")
    st = sm.transition_to_observed({"cell_state": {}, "net": {}, "risk_tag": {}})
    assert st["cell_state"]["regime"] == "indeterminate"


# ── social_post ────────────────────────────────────────────────────────────────────
def test_social_post_drafts_dry_run():
    sm = _load("social_post", "state_machine")
    st = sm.transition_to_drafted({"cell_state": {},
        "body": "資金がTreasuriesからequitiesへ回転", "sources": ["a", "b"]})
    assert st["cell_state"]["phase"] == "drafted"
    assert st["cell_state"]["status"] == "dry-run"


def test_social_post_refuses_trade_token_body():
    sm = _load("social_post", "state_machine")
    st = sm.transition_to_drafted({"cell_state": {},
        "body": "推奨: buy equities now", "sources": ["a", "b"]})
    assert st["cell_state"]["phase"] == "refused"
    assert "G2" in st["cell_state"]["refusal"]


def test_social_post_refuses_undersourced():
    sm = _load("social_post", "state_machine")
    st = sm.transition_to_drafted({"cell_state": {}, "body": "観測", "sources": ["a"]})
    assert st["cell_state"]["phase"] == "refused"
    assert "G3" in st["cell_state"]["refusal"]


# ── R0: every cell's .solve() raises (G8) ──────────────────────────────────────────
def test_all_cells_solve_raise():
    for cell, klass in (("ingest", "IngestCell"), ("flow_graph", "FlowGraphCell"),
                        ("rotation_weave", "RotationWeaveCell"),
                        ("regime_observer", "RegimeObserverCell"),
                        ("social_post", "SocialPostCell")):
        m = _load(cell, "cell")
        inst = getattr(m, klass)()
        expect_raises(lambda: inst.solve({}), contains="R0")


if __name__ == "__main__":
    run("cells/state_machines", [(n, f) for n, f in sorted(globals().items())
                                 if n.startswith("test_") and callable(f)])
