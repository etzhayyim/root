"""test_export.py — 潮目 (shionome) → kanae render export. ADR-2606072200."""
from __future__ import annotations

import json
import pathlib

import export
from _edn import load_edn
from _t import expect_raises, run
from weave import concentration, weave

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-capital-flow-graph.kotoba.edn"


def _g():
    return weave(load_edn(SEED))


def test_to_kanae_flow_ok():
    e = export.to_kanae_flow({":flow/id": "f", ":flow/source": "a", ":flow/target": "b",
                              ":flow/kind": ":rotation", ":flow/magnitude": 5.0, ":flow/unit": "usd-bn",
                              ":flow/sources": ["x", "y"]})
    assert e["flowType"] == "rotation" and e["noTrade"] is True


def test_to_kanae_flow_rejects_observation_kind():
    expect_raises(lambda: export.to_kanae_flow({":flow/kind": ":cross-correlation"}), contains="observation")


def test_to_kanae_flows_skips_observations():
    kf = export.to_kanae_flows(_g())
    assert kf["skipped_count"] == 3   # 2 correlation + 1 price-move
    assert len(kf["flows"]) == 8


def test_render_payload_flags():
    p = export.render_payload(concentration(_g()))
    assert p["isMirror"] is True and p["noTrade"] is True and p["actor"] == "shionome"


def test_render_json_serializable():
    s = export.render_json(concentration(_g()))
    obj = json.loads(s)
    assert obj["regime"]["regime"] == "risk-on"
    assert isinstance(obj["inflow_shares"], list)


def test_render_payload_has_no_per_bucket_score():
    # G4 — the render payload must never expose a per-bucket rating/signal/score
    s = export.render_json(concentration(_g())).lower()
    for forbidden in ('"rating"', '"signal"', '"target_price"', '"recommendation"'):
        assert forbidden not in s


if __name__ == "__main__":
    run("export", [(n, f) for n, f in sorted(globals().items())
                   if n.startswith("test_") and callable(f)])
