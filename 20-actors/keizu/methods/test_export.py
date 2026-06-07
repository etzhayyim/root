"""test_export.py — 系図 (keizu) → kanae render payload + round-trip. ADR-2606066000."""
from __future__ import annotations

import json
import pathlib

from _edn import load_edn
from _t import expect_raises, run
from bridge import bridge_kanae_flow
from export import (KEIZU_KIND_TO_KANAE, render_json, render_payload,
                    to_kanae_flow, to_kanae_flows)
from weave import concentration, weave

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-relation-graph.kotoba.edn"


def _g():
    return weave(load_edn(SEED))


def test_fiscal_money_maps_to_kanae_flow():
    f = to_kanae_flow({":money/id": "m1", ":money/kind": ":procurement-award",
                       ":money/payer": "a", ":money/payee": "b", ":money/amount": 100.0,
                       ":money/currency": "JPY", ":money/sources": ["u", "v"]})
    assert f["flowType"] == "procurement" and f["donor"] == "a" and f["recipient"] == "b"


def test_political_donation_not_a_kanae_flow():
    expect_raises(lambda: to_kanae_flow({":money/id": "m", ":money/kind": ":political-donation"}),
                  contains="not a kanae fiscal flow")


def test_to_kanae_flows_skips_donations():
    kf = to_kanae_flows(_g())
    # the seed has 1 political-donation (m-donation-jp-1) → skipped, the rest exported
    assert kf["skipped_count"] == 1
    assert len(kf["flows"]) == len(_g()["money"]) - 1
    assert all(f["flowType"] in KEIZU_KIND_TO_KANAE.values() for f in kf["flows"])


def test_round_trip_through_bridge_preserves_kind():
    # keizu :money → kanae flow → bridge back → keizu :money, kind + amount preserved
    for kind in ("procurement-award", "subsidy", "grant", "budget-outlay"):
        m = {":money/id": "x", ":money/kind": ":" + kind, ":money/payer": "p",
             ":money/payee": "q", ":money/amount": 42.0, ":money/currency": "JPY",
             ":money/sources": ["u", "v"]}
        flow = to_kanae_flow(m)
        flow["sources"] = ["u", "v"]   # bridge requires ≥2 (already present)
        back = bridge_kanae_flow(flow)
        assert back[":money/kind"] == ":" + kind, (kind, back[":money/kind"])
        assert back[":money/amount"] == 42.0


def test_render_payload_is_json_serializable():
    c = concentration(_g())
    s = render_json(c)
    obj = json.loads(s)           # must round-trip through JSON with no sets/tuples
    assert obj["actor"] == "keizu"
    assert obj["isMirror"] is True and obj["nonAdjudicating"] is True
    assert obj["counts"]["node_count"] >= 15


def test_render_payload_empty_graph_safe():
    s = render_json(concentration(weave({})))
    obj = json.loads(s)
    assert obj["counts"]["money_count"] == 0
    assert obj["money_by_payee"] == [] and obj["statement_index"]["count"] == 0


if __name__ == "__main__":
    run("export", [(k, v) for k, v in sorted(globals().items())
                   if k.startswith("test_") and callable(v)])
