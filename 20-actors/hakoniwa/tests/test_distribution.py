#!/usr/bin/env python3
"""hakoniwa 箱庭 — distribution + forecast-record + Datom-emit tests (ADR-2606111500). Pure stdlib.

Verifies:
  - quantiles are monotone and the histogram sums to the replica count
  - G2: the forecast record is distribution-only — :forecast/point-asserted is false and there
    is NO :forecast/point key anywhere
  - G3: a non-resilience :forecast/use (e.g. :trade / :campaign) is REFUSED
  - the Datom log emits ground :add datoms, marks every persona synthetic, flags the
    distribution transient, and emits no point datom
  - determinism (two runs byte-identical)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import world as W  # noqa: E402
import simulate as S  # noqa: E402
import distribution as D  # noqa: E402
import datom_emit  # noqa: E402

SCENARIO = ACTOR_DIR / "data" / "seed-scenario.kotoba.edn"


def _dist():
    nodes, edges = W.load(SCENARIO)
    results, meta = S.ensemble(nodes, edges, steps=12, replicas=64, seed=7)
    return nodes, edges, D.distribution(results), meta


def test_quantiles_monotone_and_histogram_total():
    _, _, dist, meta = _dist()
    q = dist["quantiles"]
    order = [q[":p10"], q[":p25"], q[":p50"], q[":p75"], q[":p90"]]
    assert order == sorted(order), f"quantiles not monotone: {order}"
    assert sum(dist["histogram"]) == meta["replicas"], "histogram does not sum to replica count"
    assert dist["min"] <= dist["mean"] <= dist["max"]


def test_forecast_record_is_distribution_only():
    nodes, _, dist, meta = _dist()
    rec = D.forecast_record(nodes, dist, meta, as_of="2026-06-11T00:00:00Z")
    assert rec[":forecast/kind"] == ":distribution"
    assert rec[":forecast/point-asserted"] is False, "G2: point-asserted must be false"
    # G2: there is NO point field of any kind
    assert not any("point" in k and k != ":forecast/point-asserted" for k in rec), \
        f"a point field leaked into the forecast record: {list(rec)}"
    assert ":forecast/quantiles" in rec and ":forecast/histogram" in rec


def test_g3_non_resilience_use_refused():
    nodes, _, dist, meta = _dist()
    for bad in (":trade", ":wager", ":position", ":target", ":manipulate", ":campaign"):
        raised = False
        try:
            D.forecast_record(nodes, dist, meta, as_of="t", use=bad)
        except ValueError:
            raised = True
        assert raised, f"G3 breach: forecast accepted non-resilience use {bad}"


def test_forecast_edn_roundtrips_distribution_only():
    nodes, _, dist, meta = _dist()
    rec = D.forecast_record(nodes, dist, meta, as_of="2026-06-11T00:00:00Z")
    edn = D.forecast_edn(rec)
    assert ":forecast/point-asserted false" in edn
    assert ":forecast/kind :distribution" in edn
    # no bare point assertion (ignore ;; comment lines)
    payload = "\n".join(ln for ln in edn.splitlines() if not ln.lstrip().startswith(";;"))
    assert ":forecast/point " not in payload


def test_datom_emit_ground_synthetic_and_transient_distribution():
    nodes, edges, dist, meta = _dist()
    out = datom_emit.emit(nodes, edges, dist, meta, tx=5)
    assert ":add]" in out, "no ground :add datoms"
    assert ":persona/synthetic true" in out, "persona synthetic marker missing from ground datoms (G1)"
    assert ":en/kind :influences" in out, "influence 縁 datoms missing"
    assert " 5 :add]" in out, "tx not threaded into ground datoms"
    # distribution must be transient, and there must be NO point datom
    assert ":bond/is-transient true" in out
    assert ":bond/distribution-p50" in out
    assert ":bond/point-asserted false" in out
    for line in out.splitlines():
        if line.startswith("[") and ":bond/distribution" in line:
            assert ":derived]" in line, f"distribution readout not flagged transient: {line}"


def test_determinism():
    nodes, edges, dist, meta = _dist()
    a = datom_emit.emit(nodes, edges, dist, meta, tx=1)
    nodes2, edges2, dist2, meta2 = _dist()
    b = datom_emit.emit(nodes2, edges2, dist2, meta2, tx=1)
    assert a == b, "Datom emit is not deterministic"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
