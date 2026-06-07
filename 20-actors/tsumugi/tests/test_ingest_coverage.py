#!/usr/bin/env python3
"""tsumugi 紡ぎ — tests for coverage_report.py + ingest_influence.py (ADR-2606061500).

Run:  python3 tests/test_ingest_coverage.py   (or pytest)
stdlib only.
"""
import sys, os, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "methods"))

import coverage_report as cov          # noqa: E402
import ingest_influence as ing         # noqa: E402

SEED = str(ROOT / "data" / "seed-influence-history.kotoba.edn")
FIXTURES = ROOT / "data" / "ingest-influence"


# ── coverage_report ──────────────────────────────────────────────────────────
def test_coverage_compute_shape():
    c = cov.compute(SEED)
    for k in ("nodes", "edges", "figures", "era_covered", "stream_covered",
              "components", "isolated", "density"):
        assert k in c, k
    assert c["nodes"] >= 79 and c["edges"] >= 125
    assert c["figures"] >= 40


def test_coverage_backbone_full_after_wave2():
    c = cov.compute(SEED)
    # Wave 2 should have filled all eras + all major streams + connected the graph
    assert not c["era_missing"], f"empty eras remain: {c['era_missing']}"
    assert not c["stream_missing"], f"missing streams remain: {c['stream_missing']}"
    assert len(c["components"]) == 1, f"graph not connected: {len(c['components'])} components"
    assert not c["isolated"], f"isolated nodes: {c['isolated']}"


def test_coverage_render_is_honest_about_all_humanity():
    c = cov.compute(SEED)
    md = cov.render(c)
    assert "~0" in md and "by design" in md          # never claims to cover all humanity
    assert "All humans ever" in md                    # the honest denominator is shown


# ── ingest_influence ─────────────────────────────────────────────────────────
def test_ingest_offline_adds_nodes_and_edges():
    nodes, flows, new_nodes, new_flows, dropped = ing.ingest_offline(FIXTURES, SEED)
    assert len(new_nodes) >= 2, "expected new figures (Schopenhauer/Kierkegaard)"
    assert len(new_flows) >= 5, "expected new influence edges"
    ids = {n[":organism/id"] for n in new_nodes}
    assert "fig.schopenhauer" in ids and "fig.kierkegaard" in ids


def test_ingest_N4_refuses_living_person():
    _, _, _, _, dropped = ing.ingest_offline(FIXTURES, SEED)
    reasons = " ".join(why for _, why in dropped)
    assert "N4" in reasons, "living/unsettled person must be refused (N4)"


def test_ingest_N2_all_ingested_nodes_are_mirrors():
    _, _, new_nodes, _, _ = ing.ingest_offline(FIXTURES, SEED)
    for n in new_nodes:
        assert n[":mirror/is-mirror"] is True
        assert n[":mirror/disclaimer"]
        assert n[":mirror/performer-type"] == ":historical-figure"


def test_ingest_G5_sourcing_representative():
    _, _, new_nodes, new_flows, _ = ing.ingest_offline(FIXTURES, SEED)
    for n in new_nodes:
        assert n[":hist/sourcing"] == ":representative"
    for f in new_flows:
        assert f[":flow/sourcing"] == ":representative"
        assert f[":flow/source"] == ":scholarship"


def test_ingest_N5_edges_forward_in_time():
    nodes, flows, new_nodes, new_flows, _ = ing.ingest_offline(FIXTURES, SEED)
    yr = {}
    for nid, nd in nodes.items():
        yr[nid] = (ing.node_year(nd, ":hist/year-from"), ing.node_year(nd, ":hist/year-to"))
    for n in new_nodes:
        yr[n[":organism/id"]] = (n[":hist/year-from"], n[":hist/year-to"])
    for f in new_flows:
        s, d = f[":flow/from"], f[":flow/to"]
        assert yr[s][0] <= yr[d][1], f"N5 violation in ingested edge {f[':flow/id']}"


def test_ingest_N1_no_node_score_from_notability():
    # ingested nodes must NOT carry any influence/karma score (edge-primary)
    _, _, new_nodes, _, _ = ing.ingest_offline(FIXTURES, SEED)
    for n in new_nodes:
        assert ":flow/signed-weight" not in n
        assert ":influence/outbound-reach" not in n
        assert "hpi" not in {k.lower() for k in n}


def test_ingest_live_gate_refused_without_env():
    saved = (os.environ.pop("TSUMUGI_OPERATOR_GATE", None),
             os.environ.pop("TSUMUGI_OPERATOR_DID", None))
    try:
        argv = sys.argv
        sys.argv = ["ingest_influence.py", "--live"]
        try:
            ing.main()
            assert False, "live ingest must be refused without the operator gate (G7)"
        except ing.LiveGateRefused:
            pass
        finally:
            sys.argv = argv
    finally:
        if saved[0] is not None: os.environ["TSUMUGI_OPERATOR_GATE"] = saved[0]
        if saved[1] is not None: os.environ["TSUMUGI_OPERATOR_DID"] = saved[1]


# ── live Wikidata path (hermetic — recorded SPARQL fixture, NO network) ───────
SPARQL_FIXTURE = FIXTURES / "wikidata-live-sample.sparql.json"


def _sparql_obj():
    import json
    return json.loads(SPARQL_FIXTURE.read_text(encoding="utf-8"))


def test_year_parses_ce_bce_and_none():
    assert ing._year("1788-02-22T00:00:00Z") == 1788
    assert ing._year("-0384-01-01T00:00:00Z") == -384   # BCE
    assert ing._year(None) is None
    assert ing._year("") is None


def test_parse_wikidata_sparql_rows():
    rows = ing.parse_wikidata_sparql(_sparql_obj())
    assert len(rows) == 3
    r0 = rows[0]
    assert r0["infLabel"] == "Arthur Schopenhauer" and r0["pLabel"] == "Friedrich Nietzsche"
    assert r0["infBirth"] == 1788 and r0["pDeath"] == 1900
    # BCE row parsed with negative years
    assert rows[1]["pBirth"] == -384 and rows[1]["infBirth"] == -428


def test_normalize_wikidata_rows_membrane():
    rows = ing.parse_wikidata_sparql(_sparql_obj())
    nodes, flows, new_nodes, new_flows, dropped = ing.normalize_wikidata_rows(rows, SEED)
    ids = {n[":organism/id"] for n in new_nodes}
    assert "fig.schopenhauer" in ids, "new dead influencer must be added"
    # Plato→Aristotle already in seed → deduped (not re-added as an edge)
    assert not any(f[":flow/id"] == "fl.plato.aristotle" for f in new_flows)
    # the new Schopenhauer→Nietzsche edge is present (Nietzsche already a seed node)
    assert any(f[":flow/from"] == "fig.schopenhauer" and f[":flow/to"] == "fig.nietzsche"
               for f in new_flows)
    # N4: the undated influencer row is dropped
    assert any("N4" in why for _, why in dropped)
    # N2/N1/G5 on every ingested node
    for n in new_nodes:
        assert n[":mirror/is-mirror"] is True and n[":mirror/disclaimer"]
        assert ":flow/signed-weight" not in n            # N1 edge-primary
        assert n[":hist/sourcing"] == ":representative"  # G5
    # N5 on every ingested edge
    yr = {nid: (ing.node_year(nd, ":hist/year-from"), ing.node_year(nd, ":hist/year-to"))
          for nid, nd in nodes.items()}
    for n in new_nodes:
        yr[n[":organism/id"]] = (n[":hist/year-from"], n[":hist/year-to"])
    for f in new_flows:
        assert yr[f[":flow/from"]][0] <= yr[f[":flow/to"]][1]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"  ✓ {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"  ✗ {fn.__name__}: {e}")
    print(f"\n{len(fns)-failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
