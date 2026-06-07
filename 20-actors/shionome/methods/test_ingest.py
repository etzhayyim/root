"""test_ingest.py — 潮目 (shionome) offline ingest normalizer + G8 live gate. ADR-2606072200."""
from __future__ import annotations

import os

import ingest
from _t import expect_raises, run


def test_normalize_bucket_ok():
    b = ingest.normalize_bucket({"id": "eq", "scope": "asset-class", "label": "EQ",
                                 "asset_class": "equities", "region": "us", "risk": "risk",
                                 "sources": ["https://www.sec.gov/"]})
    assert b[":bucket/id"] == "eq"
    assert b[":bucket/scope"] == ":asset-class"
    assert b[":bucket/asset-class"] == "equities"


def test_normalize_bucket_refuses_person():
    expect_raises(lambda: ingest.normalize_bucket({"id": "p", "scope": "individual"}), contains="G1")


def test_normalize_bucket_surfaces_pii():
    expect_raises(lambda: ingest.normalize_bucket({"id": "p", "scope": "asset-class",
                                                   "account": "1234"}), contains="no-doxxing")


def test_normalize_bucket_surfaces_rating():
    expect_raises(lambda: ingest.normalize_bucket({"id": "p", "scope": "asset-class",
                                                   "rating": "A"}), contains="trade instruction")


def test_normalize_flow_ok():
    f = ingest.normalize_flow({"id": "f", "source": "a", "target": "b", "kind": "rotation",
                               "magnitude": 2.0, "unit": "usd-bn", "as_of": 20260601,
                               "sources": ["x", "y"]})
    assert f[":flow/kind"] == ":rotation"
    assert f[":flow/no-trade-notice"] is True


def test_normalize_flow_refuses_trade_token():
    expect_raises(lambda: ingest.normalize_flow({"id": "f", "kind": "buy", "magnitude": 1.0,
                                                 "sources": ["x", "y"]}), contains="トレードはしない")


def test_normalize_flow_refuses_undersourced():
    expect_raises(lambda: ingest.normalize_flow({"id": "f", "kind": "rotation", "magnitude": 1.0,
                                                 "sources": ["x"]}), contains="G3")


def test_normalize_flow_default_external_ends():
    f = ingest.normalize_flow({"id": "f", "target": "b", "kind": "fund-inflow", "magnitude": 1.0,
                               "sources": ["x", "y"]})
    assert f[":flow/source"] == "external"


def test_normalize_snapshot_ok():
    s = ingest.normalize_snapshot({"id": "s", "bucket": "b", "metric": "return-pct",
                                   "value": 1.2, "as_of": 20260601, "sources": ["x"]})
    assert s[":snap/metric"] == ":return-pct"


def test_normalize_batch_counts():
    out = ingest.normalize_batch({
        "buckets": [{"id": "eq", "scope": "asset-class", "sources": ["s"]}],
        "flows": [{"id": "f", "source": "external", "target": "eq", "kind": "fund-inflow",
                   "magnitude": 1.0, "sources": ["x", "y"]}],
        "snapshots": [{"id": "s", "bucket": "eq", "metric": "return-pct", "value": 1.0, "sources": ["x"]}]})
    assert len(out["buckets"]) == 1 and len(out["flows"]) == 1 and len(out["snapshots"]) == 1


def test_sourcing_unknown_source_representative():
    f = ingest.normalize_flow({"id": "f", "source": "a", "target": "b", "kind": "rotation",
                               "magnitude": 1.0, "sourceId": "no-such-source", "sources": ["x", "y"]})
    assert f[":flow/sourcing"] == ":representative"


def test_sourcing_registry_wins_over_claim():
    # an unverified-seed registry source forces :representative even if caller claims authoritative
    f = ingest.normalize_flow({"id": "f", "source": "a", "target": "b", "kind": "rotation",
                               "magnitude": 1.0, "sourceId": "us-fred", "sourcing": "authoritative",
                               "sources": ["x", "y"]})
    assert f[":flow/sourcing"] == ":representative"


def test_live_ingest_gated_g8():
    os.environ.pop("SHIONOME_ALLOW_LIVE", None)
    expect_raises(lambda: ingest.ingest_live(), contains="G8")


def test_live_ingest_still_unwired_with_flag():
    os.environ["SHIONOME_ALLOW_LIVE"] = "1"
    try:
        expect_raises(lambda: ingest.ingest_live(), contains="not wired")
    finally:
        os.environ.pop("SHIONOME_ALLOW_LIVE", None)


if __name__ == "__main__":
    run("ingest", [(n, f) for n, f in sorted(globals().items())
                   if n.startswith("test_") and callable(f)])
