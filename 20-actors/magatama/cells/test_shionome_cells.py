"""test_shionome_cells.py — 潮目 (shionome) fleet cell logic + cron-fragment validity. ADR-2606072200.

Tests the PURE cell logic via shionome_core (no kotoba_langgraph dependency, so it runs off-fleet)
and asserts each cell ships a valid cron fragment placed on a real fleet node. The kotoba-WASM
cell.py wrappers (which import kotoba_langgraph) are exercised on the fleet / kotoba runtime.

Standalone-runnable: `python3 test_shionome_cells.py`.
"""
from __future__ import annotations

import os
import sys

try:
    import tomllib
except ModuleNotFoundError:  # py<3.11
    import tomli as tomllib  # type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import shionome_core as sc  # noqa: E402

FLOWS = [
    {"kind": "rotation", "source": "us-govt-bonds", "target": "us-equities", "magnitude": 18.0, "sources": ["a", "b"]},
    {"kind": "fund-inflow", "source": "external", "target": "us-equities", "magnitude": 4.0, "sources": ["a", "b"]},
    {"kind": "cross-correlation", "source": "us-equities", "target": "tech", "magnitude": 0.9, "sources": ["a", "b"]},
]
RISK_TAGS = {"us-equities": "risk", "us-govt-bonds": "safe"}

_passed = 0
_failed = 0


def check(name, fn):
    global _passed, _failed
    try:
        fn()
        _passed += 1
    except Exception as e:  # noqa: BLE001
        _failed += 1
        print(f"  FAIL {name}: {e}")


# ── shionome_core logic ──────────────────────────────────────────────────────────
def t_screen_ok():
    assert sc.screen_flows(FLOWS) == FLOWS


def t_screen_refuses_trade_token():
    try:
        sc.screen_flows([{"kind": "buy", "sources": ["a", "b"]}])
        raise AssertionError("expected refuse")
    except ValueError as e:
        assert "トレードはしない" in str(e)


def t_screen_refuses_undersourced():
    try:
        sc.screen_flows([{"kind": "rotation", "sources": ["a"]}])
        raise AssertionError("expected refuse")
    except ValueError as e:
        assert "G3" in str(e)


def t_net_flow():
    net = {r["bucket"]: r["net"] for r in sc.net_flow(FLOWS)}
    assert net["us-equities"] == 22.0          # 18 rotation in + 4 inflow
    assert net["us-govt-bonds"] == -18.0
    assert "tech" not in net                    # correlation excluded from money math


def t_top_rotation():
    r = sc.top_rotation(FLOWS)
    assert r == {"from": "us-govt-bonds", "to": "us-equities", "magnitude": 18.0}


def t_regime_risk_on():
    net = sc.net_flow(FLOWS)
    reg = sc.regime(net, RISK_TAGS)
    assert reg["regime"] == "risk-on"
    assert reg["no_trade_notice"] is True


def t_post_dry_run():
    p = sc.draft_dry_run_post("クロスアセット観測: risk-on（記述）", ["a", "b"])
    assert p["status"] == "dry-run"
    assert p["is_mirror"] is True and p["no_trade_notice"] is True and p["server_held_key"] is False
    assert "トレードはしない" in p["body"]


def t_post_refuses_trade_body():
    try:
        sc.draft_dry_run_post("buy signal: risk-on", ["a", "b"])
        raise AssertionError("expected refuse")
    except ValueError as e:
        assert "G2" in str(e)


def t_post_refuses_undersourced():
    try:
        sc.draft_dry_run_post("clean body", ["a"])
        raise AssertionError("expected refuse")
    except ValueError as e:
        assert "G3" in str(e)


# ── cron fragment validity (the fleet cron wiring) ────────────────────────────────
CELLS = ["shionome_ingest", "shionome_flow_graph", "shionome_rotation_weave",
         "shionome_regime_observer", "shionome_social_post"]
REAL_NODES = {"naphtali", "simeon", "judah", "zebulun", "levi", "joseph", "issachar", "dan",
              "gad", "asher", "benjamin", "reuben"}


def _frag(cell):
    with open(os.path.join(HERE, cell, "cells.toml.fragment"), "rb") as f:
        return tomllib.load(f)["cell"][0]


def t_every_cell_has_cron_fragment():
    for cell in CELLS:
        c = _frag(cell)
        assert c["name"] == cell
        assert c["module"] == f"{cell}.cell"
        assert c["trigger"]["kind"] == "cron"
        assert c["trigger"]["expression"].strip()


def t_every_cell_on_real_node():
    for cell in CELLS:
        node = _frag(cell)["node"]
        assert node in REAL_NODES, f"{cell} placed on unknown node {node!r}"


def t_healthz_ports_unique():
    ports = [_frag(c)["healthz_port"] for c in CELLS]
    assert len(ports) == len(set(ports))


def t_every_fragment_cites_adr():
    for cell in CELLS:
        assert "2606072200" in _frag(cell)["adr"]


def t_cell_dirs_have_init_and_cell():
    for cell in CELLS:
        assert os.path.exists(os.path.join(HERE, cell, "cell.py"))
        assert os.path.exists(os.path.join(HERE, cell, "__init__.py"))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("t_") and callable(fn):
            check(name, fn)
    total = _passed + _failed
    print(f"[shionome_cells] {_passed}/{total} passed")
    if _failed:
        sys.exit(1)
