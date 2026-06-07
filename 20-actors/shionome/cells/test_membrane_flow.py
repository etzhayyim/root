"""test_membrane_flow.py — 潮目 (shionome) cell-chain integration. ADR-2606072200.

Unit tests prove each cell in isolation (test_state_machines.py); THIS proves they COMPOSE into
the documented pipeline on the runtime path:

    ingest ─▶ flow_graph ─▶ rotation_weave ─▶ regime_observer ─▶ social_post (dry-run)

One public market-data batch is threaded through all five cell state machines in sequence; the
regime that falls out of regime_observer becomes social_post's body — proving the wire holds
end-to-end. Standalone-runnable. `.solve()` is never called (R0 scaffolds raise).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "methods"))
from _t import run  # noqa: E402


def _load(cell: str, mod: str):
    name = f"shionome_{cell}_{mod}_chain"
    spec = importlib.util.spec_from_file_location(name, HERE / cell / f"{mod}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# one self-contained batch (public capital buckets + ≥2-sourced factual flows)
_BUCKETS = [{"scope": ":asset-class"}, {"scope": ":asset-class"}]
_FLOWS = [{"kind": ":rotation", "source": "bonds", "target": "eq", "magnitude": 18.0, "sources": ["a", "b"]},
          {"kind": ":fund-inflow", "source": "external", "target": "eq", "magnitude": 4.0, "sources": ["a", "b"]}]
_RISK_TAG = {"eq": "risk", "bonds": "safe"}


def test_full_membrane_chain_reaches_dry_run_post():
    # 1) ingest — screen + record
    ing = _load("ingest", "state_machine")
    st = ing.transition_to_screened({"cell_state": {}, "buckets": _BUCKETS, "flows": _FLOWS})
    assert st["cell_state"]["phase"] == "screened"
    rec = ing.transition_to_recorded(st)
    assert rec["cell_state"]["phase"] == "recorded"

    # 2) flow_graph — net flow per bucket
    fg = _load("flow_graph", "state_machine")
    g = fg.transition_to_indexed({"cell_state": {}, "flows": _FLOWS})
    net = g["cell_state"]["net"]
    assert net["eq"] == 22.0 and net["bonds"] == -18.0

    # 3) rotation_weave — top pair
    rw = _load("rotation_weave", "state_machine")
    w = rw.transition_to_woven({"cell_state": {}, "flows": _FLOWS})
    assert w["cell_state"]["pairs"][0] == ["bonds", "eq", 18.0]

    # 4) regime_observer — risk-on from net + tags
    ro = _load("regime_observer", "state_machine")
    r = ro.transition_to_observed({"cell_state": {}, "net": net, "risk_tag": _RISK_TAG})
    regime = r["cell_state"]["regime"]
    assert regime == "risk-on"

    # 5) social_post — the regime becomes a dry-run post body (no trade token)
    sp = _load("social_post", "state_machine")
    body = f"クロスアセット観測: {regime}（記述であり助言ではない）"
    p = sp.transition_to_drafted({"cell_state": {}, "body": body, "sources": ["a", "b"]})
    assert p["cell_state"]["phase"] == "drafted"
    assert p["cell_state"]["status"] == "dry-run"


def test_membrane_refuses_trade_token_at_post_stage():
    # even a clean upstream chain refuses if a trade token reaches the post body (トレードはしない)
    sp = _load("social_post", "state_machine")
    p = sp.transition_to_drafted({"cell_state": {}, "body": "buy signal: risk-on",
                                  "sources": ["a", "b"]})
    assert p["cell_state"]["phase"] == "refused"


def test_membrane_refuses_person_bucket_at_ingest():
    ing = _load("ingest", "state_machine")
    st = ing.transition_to_screened({"cell_state": {}, "buckets": [{"scope": ":portfolio"}]})
    assert st["cell_state"]["phase"] == "refused"


if __name__ == "__main__":
    run("cells/membrane_flow", [(n, f) for n, f in sorted(globals().items())
                                if n.startswith("test_") and callable(f)])
