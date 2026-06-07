"""test_consistency.py — 潮目 (shionome) seed ↔ manifest ↔ ADR cross-consistency. ADR-2606072200."""
from __future__ import annotations

import json
import pathlib

from _edn import load_edn
from _t import run
from weave import BUCKET_SCOPES, FLOW_KINDS, weave

ACTOR = pathlib.Path(__file__).resolve().parents[1]
SEED = ACTOR / "data" / "seed-capital-flow-graph.kotoba.edn"
MANIFEST = ACTOR / "manifest.jsonld"


def test_seed_validates_cleanly():
    weave(load_edn(SEED))   # raises on any gate


def test_seed_buckets_use_known_scopes():
    g = weave(load_edn(SEED))
    for b in g["buckets"].values():
        assert str(b[":bucket/scope"]).lstrip(":") in BUCKET_SCOPES


def test_seed_flows_use_known_kinds():
    g = weave(load_edn(SEED))
    for f in g["flows"]:
        assert str(f[":flow/kind"]).lstrip(":") in FLOW_KINDS


def test_seed_all_representative_g11():
    g = weave(load_edn(SEED))
    for f in g["flows"]:
        assert str(f[":flow/sourcing"]).lstrip(":") == "representative"


def test_manifest_loads_and_names_shionome():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert m["name"] == "shionome"
    assert m["id"] == "did:web:etzhayyim.com:actor:shionome"


def test_manifest_declares_no_trade_gate():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    blob = json.dumps(m, ensure_ascii=False)
    assert "トレードはしない" in blob or "no-trade" in blob.lower()


def test_manifest_status_r0():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert m["status"].startswith("R0")


if __name__ == "__main__":
    run("consistency", [(n, f) for n, f in sorted(globals().items())
                        if n.startswith("test_") and callable(f)])
