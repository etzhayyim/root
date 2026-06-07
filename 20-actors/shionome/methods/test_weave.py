"""test_weave.py — 潮目 (shionome) weave + concentration + gates. ADR-2606072200. Standalone."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import expect_raises, run
from weave import (CAPITAL_MOVEMENT_KINDS, TRADE_TOKENS, by_asset_class, by_region,
                   concentration, correlation_clusters, inflow_concentration,
                   net_flow_by_bucket, regime, rotation_pairs, source_denied,
                   trade_token_in, validate_bucket, validate_flow, validate_snapshot, weave)

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-capital-flow-graph.kotoba.edn"


def _g():
    return weave(load_edn(SEED))


def _bucket(**kw):
    base = {":bucket/id": "x", ":bucket/scope": ":asset-class", ":bucket/sourcing": ":representative"}
    base.update(kw)
    return base


def _flow(**kw):
    base = {":flow/id": "f", ":flow/source": "a", ":flow/target": "b", ":flow/kind": ":rotation",
            ":flow/magnitude": 1.0, ":flow/no-trade-notice": True, ":flow/sourcing": ":representative",
            ":flow/sources": ["s1", "s2"]}
    base.update(kw)
    return base


def _snap(**kw):
    base = {":snap/id": "s", ":snap/bucket": "b", ":snap/metric": ":return-pct", ":snap/value": 1.0,
            ":snap/sourcing": ":representative", ":snap/sources": ["s1"]}
    base.update(kw)
    return base


# ── bucket gates (G1/G4/G9/G11) ─────────────────────────────────────────────────
def test_bucket_ok():
    validate_bucket(_bucket())


def test_bucket_bad_scope_g1():
    expect_raises(lambda: validate_bucket(_bucket(**{":bucket/scope": ":individual"})), contains="G1")


def test_bucket_person_scope_g1():
    expect_raises(lambda: validate_bucket(_bucket(**{":bucket/scope": ":portfolio"})), contains="G1")


def test_bucket_rating_unrepresentable_g2g4():
    expect_raises(lambda: validate_bucket(_bucket(**{":bucket/rating": "A"})), contains="trade instruction")


def test_bucket_signal_unrepresentable():
    expect_raises(lambda: validate_bucket(_bucket(**{":bucket/signal": "x"})), contains="trade instruction")


def test_bucket_target_unrepresentable():
    expect_raises(lambda: validate_bucket(_bucket(**{":bucket/target": 100})), contains="trade instruction")


def test_bucket_pii_account_g9():
    expect_raises(lambda: validate_bucket(_bucket(**{":bucket/account": "1234"})), contains="no-doxxing")


def test_bucket_pii_investor_g9():
    expect_raises(lambda: validate_bucket(_bucket(**{":bucket/investor": "x"})), contains="no-doxxing")


def test_bucket_missing_sourcing_g11():
    b = _bucket(); del b[":bucket/sourcing"]
    expect_raises(lambda: validate_bucket(b), contains="G11")


# ── flow gates (G2/G3/G11) ──────────────────────────────────────────────────────
def test_flow_ok():
    validate_flow(_flow())


def test_flow_bad_kind_g2():
    expect_raises(lambda: validate_flow(_flow(**{":flow/kind": ":teleport"})), contains="G2")


def test_flow_trade_token_buy_g2():
    expect_raises(lambda: validate_flow(_flow(**{":flow/kind": ":buy"})), contains="トレードはしない")


def test_flow_trade_token_sell_g2():
    expect_raises(lambda: validate_flow(_flow(**{":flow/kind": ":sell"})), contains="トレードはしない")


def test_flow_no_trade_notice_required():
    expect_raises(lambda: validate_flow(_flow(**{":flow/no-trade-notice": False})), contains="G2")


def test_flow_undersourced_g3():
    expect_raises(lambda: validate_flow(_flow(**{":flow/sources": ["only-one"]})), contains="G3")


def test_flow_denied_source():
    expect_raises(lambda: validate_flow(_flow(**{":flow/sources": ["bloomberg terminal feed", "x"]})),
                  contains="Rider")


def test_flow_negative_magnitude():
    expect_raises(lambda: validate_flow(_flow(**{":flow/magnitude": -3.0})), contains="finite")


def test_flow_nan_magnitude():
    expect_raises(lambda: validate_flow(_flow(**{":flow/magnitude": float("nan")})), contains="finite")


def test_flow_missing_sourcing_g11():
    f = _flow(); del f[":flow/sourcing"]
    expect_raises(lambda: validate_flow(f), contains="G11")


# ── snapshot gates ──────────────────────────────────────────────────────────────
def test_snapshot_ok():
    validate_snapshot(_snap())


def test_snapshot_bad_metric():
    expect_raises(lambda: validate_snapshot(_snap(**{":snap/metric": ":alpha"})), contains="G2")


def test_snapshot_undersourced():
    expect_raises(lambda: validate_snapshot(_snap(**{":snap/sources": []})), contains="G3")


def test_snapshot_nonfinite_value():
    expect_raises(lambda: validate_snapshot(_snap(**{":snap/value": float("inf")})), contains="finite")


# ── helpers ─────────────────────────────────────────────────────────────────────
def test_trade_token_in_detects():
    assert trade_token_in("recommend a buy") in ("recommend", "buy")
    assert trade_token_in("目標株価 5000") == "目標株価"
    assert trade_token_in("clean observation") == ""


def test_source_denied_detects():
    assert source_denied(["refinitiv eikon"]) == "refinitiv"
    assert source_denied(["https://fred.stlouisfed.org/"]) == ""


def test_trade_tokens_have_core_set():
    for t in ("buy", "sell", "long", "short", "target price", "推奨", "買い", "売り"):
        assert t in TRADE_TOKENS


# ── seed weave + metrics ─────────────────────────────────────────────────────────
def test_seed_weaves():
    g = _g()
    assert len(g["buckets"]) == 13
    assert len(g["flows"]) == 11
    assert len(g["snapshots"]) == 5


def test_net_flow_top_is_us_equities():
    rows = net_flow_by_bucket(_g())
    assert rows[0]["bucket"] == "us-equities"
    assert rows[0]["net"] > 0


def test_net_flow_excludes_external():
    rows = net_flow_by_bucket(_g())
    assert all(r["bucket"] != "external" for r in rows)


def test_net_flow_only_capital_movement():
    # sector-energy receives only a price-move (not capital) → not in net-flow rows
    rows = {r["bucket"] for r in net_flow_by_bucket(_g())}
    assert "sector-energy" not in rows


def test_rotation_pairs_top():
    pairs = rotation_pairs(_g())
    assert pairs[0]["from"] == "us-govt-bonds" and pairs[0]["to"] == "us-equities"


def test_rotation_excludes_correlation():
    pairs = rotation_pairs(_g())
    assert all(not (p["from"] == "sector-tech" and p["to"] == "theme-ai") for p in pairs)


def test_inflow_hhi_in_range():
    ic = inflow_concentration(_g())
    assert 0.0 < ic["hhi"] <= 1.0
    assert ic["total"] > 0


def test_by_asset_class_has_equities():
    rows = {r["asset_class"] for r in by_asset_class(_g())}
    assert "equities" in rows


def test_by_region_has_us():
    rows = {r["region"] for r in by_region(_g())}
    assert "us" in rows


def test_regime_is_risk_on():
    r = regime(_g())
    assert r["regime"] == "risk-on"
    assert r["no_trade_notice"] is True


def test_correlation_cluster_present():
    cl = correlation_clusters(_g())
    assert any("sector-tech" in c["members"] for c in cl)


def test_capital_movement_kinds_subset():
    from weave import FLOW_KINDS
    assert set(CAPITAL_MOVEMENT_KINDS) <= set(FLOW_KINDS)
    assert "cross-correlation" not in CAPITAL_MOVEMENT_KINDS


def test_concentration_full_report():
    c = concentration(_g())
    for k in ("net_flow_by_bucket", "rotation_pairs", "inflow_concentration",
              "by_asset_class", "by_region", "regime", "correlation_clusters", "integrity"):
        assert k in c


def test_integrity_clean_on_seed():
    assert concentration(_g())["integrity"]["dangling_count"] == 0


def test_active_as_of_grows():
    from weave import active_as_of
    g = _g()
    early = active_as_of(g, 20260601)
    late = active_as_of(g, 20260605)
    assert late["active_flows"] >= early["active_flows"]


def test_assert_integrity_raises_on_dangling():
    from weave import assert_integrity
    g = _g()
    g["flows"].append(_flow(**{":flow/id": "bad", ":flow/source": "nonesuch", ":flow/target": "us-equities"}))
    expect_raises(lambda: assert_integrity(g), contains="dangling")


if __name__ == "__main__":
    run("weave", [(n, f) for n, f in sorted(globals().items())
                  if n.startswith("test_") and callable(f)])
