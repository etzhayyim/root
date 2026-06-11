#!/usr/bin/env python3
"""rasen 螺旋 — ingest + content-address tests (ADR-2606101000). Pure stdlib, NETWORK-FREE.

Exercises the ingest normalisation and the kotoba IPFS content-address on a bundled fixture
(a real MyVariant.info response shape) — no network needed, so this runs in CI. The live
fetch path is covered by running `methods/ingest.py` on an operator/mesh node (G7).
"""
import sys
import json
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import cid  # noqa: E402
import ingest  # noqa: E402

FIX = ACTOR_DIR / "tests" / "fixtures" / "myvariant_rs334.json"
GO_FIX = ACTOR_DIR / "tests" / "fixtures" / "mygene_brca1_go.json"
REACT_FIX = ACTOR_DIR / "tests" / "fixtures" / "reactome_brca1.json"
SOURCES = ingest.read_edn((ACTOR_DIR / "data" / "ingest-sources.edn").read_text(encoding="utf-8"))
POP_MAP = SOURCES[":ingest/population-map"]
CLINSIG_MAP = SOURCES[":ingest/clinsig-map"]


def test_go_pathways_deduped_weighted_bounded():
    """GO ingest: dedupe by GO id (best evidence wins), cap per gene, emit :participates-in."""
    hit = json.loads(GO_FIX.read_text(encoding="utf-8"))
    pw_nodes, edges = ingest.build_gene_pathways(hit, "gene.brca1", "BP", max_per_gene=6)
    # 8 BP rows, but GO:0006281 and GO:0000724 each appear twice → 6 distinct terms
    assert len(pw_nodes) == 6, f"expected 6 deduped pathways, got {len(pw_nodes)}"
    assert len(edges) == 6
    # every node is a public GO pathway, every edge is gene→pathway :participates-in
    for pid, n in pw_nodes.items():
        assert n[":genome/kind"] == ":pathway" and n[":pathway/source"] == ":GO"
        assert n[":pathway/acc"].startswith("GO:")
    for e in edges:
        assert e[":en/from"] == "gene.brca1" and e[":en/kind"] == ":participates-in"
        assert e[":en/to"] in pw_nodes
        assert 0.0 < float(e[":en/grasping-load"]) <= 1.0
    # DNA repair (GO:0006281) kept its BEST evidence (IDA experimental 0.9, not IEA 0.4)
    dna_repair = [e for e in edges if e[":en/to"] == "pw.go-0006281"][0]
    assert abs(float(dna_repair[":en/grasping-load"]) - 0.9) < 1e-9, "best-evidence weight not kept"


def test_go_pathways_capped():
    """max_per_gene caps the bounded slice (G5 honesty)."""
    hit = json.loads(GO_FIX.read_text(encoding="utf-8"))
    pw_nodes, edges = ingest.build_gene_pathways(hit, "gene.brca1", "BP", max_per_gene=3)
    assert len(pw_nodes) == 3 and len(edges) == 3
    # the cap keeps the HIGHEST-evidence terms (all returned weights ≥ any dropped term's)
    kept = sorted(float(e[":en/grasping-load"]) for e in edges)
    assert kept[0] >= 0.7, f"cap should keep high-evidence terms first, got {kept}"


def test_reactome_pathways_deduped_topfirst_bounded():
    """Reactome: dedupe by stId (top-level/lowest maxDepth wins), cap, emit :participates-in."""
    entries = json.loads(REACT_FIX.read_text(encoding="utf-8"))
    pw_nodes, edges = ingest.build_reactome_pathways(entries, "gene.brca1", weight=0.7, max_per_gene=5)
    # 6 distinct R-HSA stIds in the fixture (R-HSA-73894 appears twice), 1 row has no stId → 5 capped
    assert len(pw_nodes) == 5 and len(edges) == 5
    for pid, n in pw_nodes.items():
        assert n[":genome/kind"] == ":pathway" and n[":pathway/source"] == ":reactome"
        assert n[":pathway/acc"].startswith("R-HSA-") and pid.startswith("pw.react-")
    for e in edges:
        assert e[":en/from"] == "gene.brca1" and e[":en/kind"] == ":participates-in"
        assert abs(float(e[":en/grasping-load"]) - 0.7) < 1e-9
    # the cap keeps the most TOP-LEVEL pathways: DNA Repair (maxDepth 1) must survive
    assert "pw.react-r-hsa-73894" in pw_nodes


def test_reactome_disabled_or_empty_is_safe():
    """No entries / empty list → no nodes, no edges (defensive)."""
    for empty in ([], None, [{"name": ["x"]}]):
        pw_nodes, edges = ingest.build_reactome_pathways(empty, "gene.x", 0.7, 5)
        assert pw_nodes == {} and edges == []


def test_cid_matches_ipfs_vector():
    """CIDv1 raw sha2-256 — byte-identical to `ipfs add --cid-version=1 --raw-leaves`."""
    # vector verified against ipfs 0.41.0 for the UTF-8 bytes of "rasen 螺旋\n"
    assert cid.cidv1_raw("rasen 螺旋\n".encode("utf-8")) == \
        "bafkreielxn6z4bf6xlhfe3q57dd6tvgjl6yycsvzifm55lhie4ueup3ova"
    # determinism + sensitivity
    assert cid.cidv1_raw(b"a") == cid.cidv1_raw(b"a")
    assert cid.cidv1_raw(b"a") != cid.cidv1_raw(b"b")
    assert cid.cidv1_raw(b"").startswith("bafkrei")  # CIDv1/raw/sha2-256 multibase prefix


def test_normalise_variant_disclosed_and_bounded():
    hit = json.loads(FIX.read_text(encoding="utf-8"))
    vnode, gene_id, phenos, edges = ingest.normalise_variant("rs334", hit, CLINSIG_MAP, POP_MAP)
    assert vnode[":genome/kind"] == ":variant" and vnode[":variant/rsid"] == "rs334"
    assert gene_id == "gene.hbb"
    # "not provided" significance is skipped; "Pathogenic" + "protective" are kept (N3 disclosed)
    clinsigs = {e[":en/clinsig"] for e in edges if e.get(":en/kind") == ":associated-with"}
    assert ":pathogenic" in clinsigs and ":protective" in clinsigs
    # MONDO condition becomes a coded phenotype node
    assert "ph.mondo-0011382" in phenos
    assert phenos["ph.mondo-0011382"][":phenotype/code"] == "MONDO:0011382"


def test_g1_allele_frequency_is_super_population_aggregate_only():
    """G1: only the 6 declared SUPER-POPULATION aggregates; NEVER _female/_male or individual."""
    hit = json.loads(FIX.read_text(encoding="utf-8"))
    _, _, _, edges = ingest.normalise_variant("rs334", hit, CLINSIG_MAP, POP_MAP)
    af_edges = [e for e in edges if e.get(":en/kind") == ":allele-frequency"]
    assert af_edges, "no aggregate allele-frequency edges produced"
    allowed_pops = {"pop." + v.lstrip(":").lower() for v in POP_MAP.values()}
    for e in af_edges:
        assert e[":en/from"] in allowed_pops, f"non-aggregate population leaked: {e[':en/from']}"
        assert 0.0 <= float(e[":en/grasping-load"]) <= 1.0
    # the sex-stratified fixture fields (af_afr_female/_male) MUST NOT have produced edges
    assert len(af_edges) <= len(POP_MAP), "more freq edges than declared super-populations"


def test_no_individual_level_fields_anywhere():
    hit = json.loads(FIX.read_text(encoding="utf-8"))
    vnode, _, phenos, edges = ingest.normalise_variant("rs334", hit, CLINSIG_MAP, POP_MAP)
    FORBIDDEN = {":sample/id", ":individual/id", ":patient/id", ":genotype/call",
                 ":sequence/raw", ":family/id"}
    for m in [vnode, *phenos.values(), *edges]:
        assert not (set(m) & FORBIDDEN), f"individual-level field leaked: {set(m) & FORBIDDEN}"


def test_serialise_graph_roundtrips_and_addresses():
    """Normalised graph serialises to EDN, reloads, and content-addresses deterministically."""
    hit = json.loads(FIX.read_text(encoding="utf-8"))
    nodes = ingest.population_nodes(POP_MAP)
    vnode, gene_id, phenos, edges = ingest.normalise_variant("rs334", hit, CLINSIG_MAP, POP_MAP)
    nodes[vnode[":genome/id"]] = vnode
    nodes.update(phenos)
    nodes[gene_id] = {":genome/id": gene_id, ":genome/kind": ":gene", ":genome/label": "HBB",
                      ":gene/symbol": "HBB", ":gene/taxon": ":homo-sapiens",
                      ":genome/sourcing": ":authoritative"}
    edges = [e for e in edges if e[":en/from"] in nodes and e[":en/to"] in nodes]
    prov = {"sources": [{"url": "fixture://myvariant"}], "counts": {"variants": 1}}
    edn = ingest.serialise_graph(nodes, edges, prov)
    assert edn == ingest.serialise_graph(nodes, edges, prov), "serialisation not deterministic"
    c1 = cid.cidv1_raw(edn.encode("utf-8"))
    c2 = cid.cidv1_raw(edn.encode("utf-8"))
    assert c1 == c2 and c1.startswith("bafkrei")
    # reloads through the canonical analyzer loader with no dangling edges
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".edn", delete=False, encoding="utf-8") as f:
        f.write(edn)
        tmp = pathlib.Path(f.name)
    n2, e2 = ingest.load(tmp)
    tmp.unlink()
    assert vnode[":genome/id"] in n2
    for e in e2:
        assert e[":en/from"] in n2 and e[":en/to"] in n2, "dangling edge after roundtrip"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
