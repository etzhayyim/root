#!/usr/bin/env python3
"""aburi 炙り — analyzer + Datom-emit tests (ADR-2606161630). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, SENSITIVITY_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-tracker-exposure.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 30, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 40, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":surface", ":permission", ":collector", ":datatype", ":relief"} <= kinds, \
        f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_g1_own_data_no_other_person():
    """G1: own-data only — no individual / PII / biometric / raw-identifier attribute anywhere.
    The graph models SURFACES/PERMISSIONS/COLLECTORS/DATA-TYPES, never a person or a raw value."""
    nodes, _ = load(SEED)
    banned = (":person/id", ":user/id", ":email", ":phone", ":imei", ":idfa", ":gaid",
              ":device/serial", ":name/full", ":geo/lat", ":geo/lon", ":biometric",
              ":profile", ":individual", ":raw-value", ":value/raw")
    for nid, n in nodes.items():
        for b in banned:
            assert b not in n, f"G1 violation: per-person / raw-identifier attr {b} on {nid}"


def test_g8_no_credential_or_raw_id_attr_in_emit_schema():
    """G8: the datom emitter can only project a fixed attr allowlist; no credential / raw-identifier
    attribute exists in it, so none can ever be written to the substrate."""
    forbidden = ("password", "token", "secret", "credential", "cookie/value", "idfa", "gaid",
                 "imei", "raw", "pan", "email")
    for a in datom_emit.NODE_ATTRS + datom_emit.EDGE_ATTRS:
        low = a.lower()
        for f in forbidden:
            assert f not in low, f"G8 violation: emit attr {a} looks like a credential / raw id"


def test_g3_collectors_are_catalogued_facts_not_verdicts():
    """G3/N3: every collector carries a PUBLIC catalogue provenance (:collector/catalog) and an
    org — it is a disclosed fact, never an aburi verdict. No collector carries a judgement attr."""
    nodes, _ = load(SEED)
    cols = [n for n in nodes.values() if n.get(":organism/kind") == ":collector"]
    assert cols, "no collectors in seed"
    valid = {":exodus", ":apple-privacy", ":play-data-safety", ":sellers-json", ":iab"}
    for c in cols:
        assert c.get(":collector/catalog") in valid, \
            f"collector {c.get(':organism/id')} lacks a public catalogue provenance (G3/G5)"
        assert c.get(":collector/org"), f"collector {c.get(':organism/id')} lacks a disclosed org"
        for verdict in (":aburi/verdict", ":guilty", ":wrongdoing", ":score-of-collector"):
            assert verdict not in c, f"G3 violation: collector carries a verdict attr {verdict}"


def test_edge_primary_exposure_integral():
    """N1: collector tracking-exposure MUST equal the independent integral of incident inbound
    :flows-to 縁 × disclosed permission-sensitivity weight."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    expect = {}
    for e in edges:
        if e.get(":en/kind") == ":flows-to":
            dst = e[":en/to"]
            sens = nodes[e[":en/from"]].get(":permission/sensitivity")
            w = SENSITIVITY_WEIGHT.get(sens, 0.5)
            expect[dst] = expect.get(dst, 0.0) + float(e[":en/load"]) * w
    for nid, v in expect.items():
        assert abs(res["exposure"][nid] - v) < 1e-9, f"{nid}: {res['exposure'][nid]} != {v}"
    # G2: no stored per-collector score on any ground node
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":aburi/score-of-collector" for k in n)


def test_top_tracker_is_a_real_collector_with_sensitive_inflow():
    """The top net-exposure node must be a collector that receives at least one :sensitive/:critical
    permission's flow (the lens is not mis-weighted toward a low-sensitivity collector)."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["net_exposure"].items(), key=lambda kv: kv[1])[0]
    assert nodes[top].get(":organism/kind") == ":collector", f"top tracker {top} is not a collector"
    incident_sens = {
        nodes[e[":en/from"]].get(":permission/sensitivity")
        for e in edges if e.get(":en/kind") == ":flows-to" and e[":en/to"] == top
    }
    assert incident_sens & {":critical", ":sensitive"}, \
        f"top tracker {top} receives no sensitive/critical flow — lens mis-weighted"


def test_surface_leak_is_two_hop_and_ranks_a_real_surface():
    """surface_leak is the two-hop integral (grant × downstream permission flow); the leakiest
    node must be a surface, and Facebook/Google (heavy ToS/ad-id grants) should rank high."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["surface_leak"], "no surface leak computed"
    top = max(res["surface_leak"].items(), key=lambda kv: kv[1])[0]
    assert nodes[top].get(":organism/kind") == ":surface", f"top leak {top} is not a surface"
    # independent recompute of the two-hop integral
    perm_leak = {}
    for e in edges:
        if e.get(":en/kind") == ":flows-to":
            perm_leak[e[":en/from"]] = perm_leak.get(e[":en/from"], 0.0) + float(e[":en/load"])
    expect = {}
    for e in edges:
        if e.get(":en/kind") == ":grants":
            expect[e[":en/from"]] = expect.get(e[":en/from"], 0.0) + \
                float(e[":en/load"]) * perm_leak.get(e[":en/to"], 0.0)
    for nid, v in expect.items():
        assert abs(res["surface_leak"][nid] - v) < 1e-9, f"{nid}: leak mismatch"


def test_reciprocity_gap_are_unrouted_leaking_permissions():
    """A permission that leaks (outbound :flows-to > 0) but has no :routes-to relief is surfaced as
    the reciprocity gap (route coverage = 0)."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    for nid in res["unrouted_permissions"]:
        assert nodes[nid].get(":organism/kind") == ":permission"
        assert res["route_coverage"].get(nid, 0.0) == 0.0
        assert res["permission_leak"].get(nid, 0.0) > 0.0
    # the seed deliberately leaves tos-data-sharing / coarse-location / microphone / photos unrouted
    assert "ax.perm.tos-data-sharing" in res["unrouted_permissions"], \
        "expected the ToS data-sharing clause to be an unrouted reciprocity gap"


def test_net_exposure_is_gross_minus_relief():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    for cid, x in res["exposure"].items():
        assert abs(res["net_exposure"][cid] - (x - res["relief"].get(cid, 0.0))) < 1e-9


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":collector/catalog" in out, "collector provenance missing from datoms (G3/G5)"
    assert ":en/load" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/tracking-exposure" in out
    for line in out.splitlines():
        if line.startswith("[") and ":bond/" in line:
            assert ":derived]" in line, f"derived readout not flagged transient: {line}"
    assert " 7 :add]" in out


def test_determinism():
    nodes, edges = load(SEED)
    a = datom_emit.emit(nodes, edges, analyze(nodes, edges), tx=1)
    nodes2, edges2 = load(SEED)
    b = datom_emit.emit(nodes2, edges2, analyze(nodes2, edges2), tx=1)
    assert a == b, "Datom emit is not deterministic"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
