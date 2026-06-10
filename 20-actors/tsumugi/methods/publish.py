#!/usr/bin/env python3
"""tsumugi 紡ぎ — PUBLISH the woven power-graph as self-sovereign linked data (ADR-2606092000).

The inversion of dependence: instead of only CONSUMING Wikidata/GLEIF, etzhayyim becomes a
DATA PROVIDER in its own right — it publishes its woven power-graph (and the original layers
nobody else has: 産官学報 cross-sector concentration, vertical integration, scale/sector/
collective-kind enrichment, 旗 banners) under its OWN resolvable vocabulary, so anyone can
load it into a triplestore and federate against it exactly as they would Wikidata.

Self-sovereign (not host-dependent): the dataset is content-addressed (a sha256 over the
canonical N-Triples is the dataset's identity), licensed (Apache-2.0 + Charter Rider), and
provenance-honest (G5): every node declares which upstream sources fed it, and the DERIVED
layers are explicitly marked as etzhayyim's own authored contribution.

Emits (out/, GENERATED):
  - etzhayyim-power-graph.jsonld   linked data, @context over the etzhayyim vocabulary
  - etzhayyim-power-graph.nt        RDF N-Triples (SPARQL/triplestore-loadable)
  - dataset-manifest.json           DCAT/VoID-style: title, license, provenance, counts, CID-hash

Vocabulary (resolvable, etzhayyim is the authority):
  https://etzhayyim.com/ns/power#   — predicates/classes (epw:)
  https://etzhayyim.com/id/power/   — entity IRIs (one per org/seat; like wikidata.org/entity/)

stdlib only. Usage:  python3 publish.py [--out OUTDIR]
"""
from __future__ import annotations
import sys, json, hashlib, pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import analyze_scale as A  # noqa: E402

NS = "https://etzhayyim.com/ns/power#"
ID = "https://etzhayyim.com/id/power/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"
PUBLISHER_DID = "did:web:etzhayyim.com:actor:tsumugi"
LICENSE = "Apache-2.0 + etzhayyim Charter Compliance Rider v3.1 (/CHARTER-RIDER.md)"

SCALE_JA = {":san": "industry/産", ":kan": "government/官", ":gaku": "academia/学",
            ":hou": "press/報", ":min": "civil/民", ":kin": "finance/金"}

# closed map of the seed's relation kinds → epw predicate localnames (S5: factual only)
TIE_PRED = {":custodies": "custodies", ":depends-on": "dependsOn", ":funds": "funds",
            ":awards": "awards", ":seats-on": "seatsOn", ":co-member": "coMemberOf",
            ":supplies": "supplies", ":covers": "covers", ":employs": "employs",
            ":follows": "follows"}


def _ent_iri(pwr_id: str) -> str:
    return ID + pwr_id


def _esc(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def build_triples(nodes: dict, ties: list, result: dict):
    """Return N-Triples lines. Org/seat nodes + relations + the etzhayyim-DERIVED layers
    (per-locality concentration). Person-excluded by construction (S2 holds upstream)."""
    nt = []

    def t(s, p, o, lit=False, typ=None):
        obj = (f'"{_esc(o)}"' + (f"^^<{typ}>" if typ else "")) if lit else f"<{o}>"
        nt.append(f"<{s}> <{p}> {obj} .")

    for nid, n in nodes.items():
        s = _ent_iri(nid)
        standing = n.get(":pwr/standing", ":institutional").lstrip(":")
        cls = "PublicSeat" if standing == "public-seat" else "Org"
        t(s, RDF + "type", NS + cls)
        if n.get(":pwr/label"):
            t(s, RDFS + "label", n[":pwr/label"], lit=True)
        for attr, pred in ((":pwr/scale", "scale"), (":pwr/sector", "sector"),
                           (":pwr/locality", "locality"), (":pwr/collective-kind", "collectiveKind")):
            v = n.get(attr)
            if v:
                t(s, NS + pred, str(v).lstrip(":"), lit=True)
        if n.get(":pwr/sourcing"):
            t(s, NS + "sourcing", n[":pwr/sourcing"].lstrip(":"), lit=True)
    for tie in ties:
        f, to = tie.get(":tie/from"), tie.get(":tie/to")
        if f not in nodes or to not in nodes:
            continue
        pred = TIE_PRED.get(tie.get(":tie/kind"))
        if not pred:
            continue
        t(_ent_iri(f), NS + pred, _ent_iri(to))
        # node-level provenance lives in the manifest; per-tie citations stay in the canonical EDN.
    # etzhayyim-DERIVED original layer: per-locality 産官学報 concentration (nobody else has this)
    for x in result["localities"]:
        liri = ID + "locality/" + x["locality"]
        t(liri, RDF + "type", NS + "Locality")
        t(liri, RDFS + "label", x["locality"], lit=True)
        t(liri, NS + "concentration", str(x["concentration"]), lit=True, typ=XSD + "decimal")
        t(liri, NS + "sectorDiversity", str(x["sector_diversity"]), lit=True, typ=XSD + "integer")
        t(liri, NS + "derivedBy", PUBLISHER_DID, lit=True)
    return nt


def build_jsonld(nodes: dict, ties: list, result: dict) -> dict:
    out_edges = {}
    for tie in ties:
        f, to = tie.get(":tie/from"), tie.get(":tie/to")
        pred = TIE_PRED.get(tie.get(":tie/kind"))
        if f in nodes and to in nodes and pred:
            out_edges.setdefault(f, []).append((pred, to))
    graph = []
    for nid, n in nodes.items():
        standing = n.get(":pwr/standing", ":institutional").lstrip(":")
        node = {"@id": _ent_iri(nid),
                "@type": "epw:PublicSeat" if standing == "public-seat" else "epw:Org",
                "rdfs:label": n.get(":pwr/label", nid)}
        for attr, pred in ((":pwr/scale", "scale"), (":pwr/sector", "sector"),
                           (":pwr/locality", "locality"), (":pwr/collective-kind", "collectiveKind"),
                           (":pwr/sourcing", "sourcing")):
            if n.get(attr):
                node["epw:" + pred] = str(n[attr]).lstrip(":")
        for pred, to in out_edges.get(nid, []):
            node.setdefault("epw:" + pred, []).append({"@id": _ent_iri(to)})
        graph.append(node)
    for x in result["localities"]:
        graph.append({"@id": ID + "locality/" + x["locality"], "@type": "epw:Locality",
                      "rdfs:label": x["locality"],
                      "epw:concentration": x["concentration"],
                      "epw:sectorDiversity": x["sector_diversity"],
                      "epw:derivedBy": PUBLISHER_DID})
    return {"@context": {"epw": NS, "rdfs": RDFS,
                         "rdfs:label": {"@id": RDFS + "label"}},
            "@graph": graph}


def build_manifest(nodes, ties, result, nt_lines) -> dict:
    cid_hash = "sha256:" + hashlib.sha256("\n".join(nt_lines).encode("utf-8")).hexdigest()
    sectors = sorted({n.get(":pwr/sector") for n in nodes.values() if n.get(":pwr/sector")})
    return {
        "@type": "dcat:Dataset",
        "title": "etzhayyim power-dynamics knowledge graph (tsumugi 紡ぎ)",
        "description": "A self-sovereign linked-data power-graph: organisations + their custody/"
                       "dependency 縁, enriched with etzhayyim's original 産官学報 cross-sector "
                       "concentration, scale, collective-kind, and vertical-integration layers.",
        "publisher": PUBLISHER_DID,
        "license": LICENSE,
        "vocabulary": NS,
        "entityNamespace": ID,
        "contentHash": cid_hash,
        "counts": {"nodes": len(nodes), "edges": sum(
            1 for t in ties if t.get(":tie/from") in nodes and t.get(":tie/to") in nodes
            and t.get(":tie/kind") in TIE_PRED),
            "localities": len(result["localities"]), "triples": len(nt_lines)},
        "sectors": [SCALE_JA.get(s, s) for s in sectors],
        "provenance": {
            "upstreamSources": ["Wikidata (P749 parent organization, WDQS)",
                                "GLEIF Level-2 Relationship Records (api.gleif.org)",
                                "curated structural-public facts (:representative)"],
            "etzhayyimDerived": ["産官学報 cross-sector concentration (epw:concentration)",
                                 "scale / sector / collective-kind enrichment",
                                 "vertical integration across scales",
                                 "旗 hata ideology/faction (separate dataset)"],
            "note": "Per-edge citations are preserved in the canonical kotoba-EDN seed. "
                    "Derived layers are etzhayyim's authored contribution (not in any upstream)."},
        "gates": "S1 edge-primary · S2 person-excluded (institutional/public-seat only) · "
                 "S5 non-adjudicating (no verdict predicate) · G5 sourcing-honest",
        "interop": {"jsonld": "etzhayyim-power-graph.jsonld", "ntriples": "etzhayyim-power-graph.nt",
                    "canonical": "data/seed-scale-power.kotoba.edn (kotoba Datom EDN)"},
    }


def publish(out: pathlib.Path):
    nodes, ties = A.load()
    result = A.analyze(nodes, ties)
    nt = build_triples(nodes, ties, result)
    jsonld = build_jsonld(nodes, ties, result)
    manifest = build_manifest(nodes, ties, result, nt)
    out.mkdir(parents=True, exist_ok=True)
    (out / "etzhayyim-power-graph.nt").write_text("\n".join(nt) + "\n", encoding="utf-8")
    (out / "etzhayyim-power-graph.jsonld").write_text(
        json.dumps(jsonld, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "dataset-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv):
    out = ACTOR_DIR / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    m = publish(out)
    print(f"[tsumugi/publish] etzhayyim is now a power-data PROVIDER — "
          f"{m['counts']['nodes']} nodes / {m['counts']['triples']} triples / "
          f"{m['contentHash'][:23]}… → out/etzhayyim-power-graph.{{nt,jsonld}} + dataset-manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
