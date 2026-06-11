#!/usr/bin/env python3
"""rasen 螺旋 — PUBLIC genetics ingest → kotoba EDN/Datom → IPFS content-address (ADR-2606101000).

OUTWARD-GATED CELL (G7): this is the only rasen cell that reaches the network. It runs on an
operator / donated mesh node (NOT in-browser WASM — that path has no network). It pulls a
BOUNDED, REPRESENTATIVE slice of PUBLIC reference genetics declared in
`data/ingest-sources.edn` and normalises it into the genome-ontology kotoba graph, then
content-addresses the artifact to a kotoba IPFS CID (and pins it if `ipfs` is present).

CONSTITUTIONAL:
  G1 — PUBLIC reference only. We fetch gene reference models (Ensembl id + COARSE cytoband),
       public variant ids, DISCLOSED ClinVar significance, and gnomAD SUPER-POPULATION
       AGGREGATE allele frequencies. No sample / cohort / individual / family data is ever
       requested or stored — by construction (we never call individual-level endpoints, and
       we only read the aggregate `af_*` super-population fields).
  G3 — non-adjudicating. ClinVar clinical-significance is copied as a DISCLOSED fact onto the
       edge (:en/clinsig); rasen never re-judges it.
  G5 — sourcing honesty. Bounded slice; every record :authoritative; coverage stays ~0 of all
       genes/variants. A provenance manifest records sources, licenses, counts and the CID.

Sources (PUBLIC, no auth): MyGene.info + MyVariant.info (BioThings aggregators of NCBI/Ensembl
+ ClinVar + gnomAD). Pure-stdlib (urllib) — no third-party deps.

Usage:
    python3 ingest.py [--sources data/ingest-sources.edn] [--out OUTDIR] [--offline] [--no-pin]
    # --offline: skip network; re-content-address an existing out/ingested-genome-graph.kotoba.edn
"""
from __future__ import annotations
import sys, json, pathlib, urllib.parse, urllib.request, urllib.error, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze, read_edn  # noqa: E402
import datom_emit  # noqa: E402
import cid as cidlib  # noqa: E402

UA = "etzhayyim-rasen/0.1 (+https://etzhayyim.com; public-reference-genetics ingest)"
TIMEOUT = 20


def _slug(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-").replace("--", "-")


def _get_json(url: str, params: dict) -> dict:
    q = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(q, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8")), q


# ── normalisation ────────────────────────────────────────────────────────────
def gene_node_from_mygene(hit: dict, symbol: str) -> dict:
    ens = (hit.get("ensembl") or {})
    ens_id = ens.get("gene") if isinstance(ens, dict) else None
    if isinstance(ens, list) and ens:
        ens_id = ens[0].get("gene")
    taxid = hit.get("taxid")
    taxon = ":homo-sapiens" if taxid == 9606 else (f":taxid-{taxid}" if taxid else ":homo-sapiens")
    n = {":genome/id": f"gene.{symbol.lower()}", ":genome/kind": ":gene",
         ":genome/label": hit.get("name") or symbol, ":gene/symbol": symbol,
         ":gene/taxon": taxon, ":genome/sourcing": ":authoritative"}
    if hit.get("map_location"):
        n[":gene/cytoband"] = hit["map_location"]   # COARSE band only — never precise coords (G1)
    if ens_id:
        n[":gene/ensembl"] = ens_id
    return n


# GO evidence code → representative confidence weight (modeling weight; the GO annotation
# itself is the DISCLOSED fact, N3). Experimental > author-stated > phylogenetic > computational.
GO_EVIDENCE_WEIGHT = {
    "EXP": 0.9, "IDA": 0.9, "IPI": 0.9, "IMP": 0.9, "IGI": 0.9, "IEP": 0.9, "HDA": 0.9, "HMP": 0.9,
    "TAS": 0.7, "NAS": 0.7, "IC": 0.7,
    "IBA": 0.6, "IBD": 0.6,
    "ISS": 0.5, "ISA": 0.5, "ISO": 0.5, "ISM": 0.5, "IGC": 0.5, "RCA": 0.5,
    "IEA": 0.4,
}


def build_gene_pathways(hit: dict, gene_id: str, category: str = "BP", max_per_gene: int = 6):
    """From a MyGene hit's `go.<category>`, return (pathway_nodes, :participates-in edges).

    PUBLIC GO annotations only (Gene Ontology / EBI-GOA). Bounded: dedupe by GO id, keep the
    best evidence weight per term, cap to `max_per_gene` (G5 honesty — documented in provenance).
    """
    go = hit.get("go") or {}
    terms = go.get(category) or []
    if isinstance(terms, dict):
        terms = [terms]
    best = {}  # GO id → (weight, term)
    for t in terms:
        if not isinstance(t, dict):
            continue
        gid = t.get("id")
        if not gid or not str(gid).startswith("GO:"):
            continue
        w = GO_EVIDENCE_WEIGHT.get(str(t.get("evidence", "")).upper(), 0.4)
        term = t.get("term") or gid
        if gid not in best or w > best[gid][0]:
            best[gid] = (w, term)

    ranked = sorted(best.items(), key=lambda kv: (-kv[1][0], kv[0]))[:max_per_gene]
    pw_nodes, edges = {}, []
    for gid, (w, term) in ranked:
        pw_id = "pw." + gid.lower().replace(":", "-")  # GO:0006281 → pw.go-0006281
        pw_nodes[pw_id] = {":genome/id": pw_id, ":genome/kind": ":pathway",
                           ":genome/label": term, ":pathway/source": ":GO",
                           ":pathway/acc": gid, ":genome/sourcing": ":authoritative"}
        edges.append({":en/from": gene_id, ":en/to": pw_id, ":en/kind": ":participates-in",
                      ":en/grasping-load": w, ":en/sourcing": ":authoritative"})
    return pw_nodes, edges


def build_reactome_pathways(entries, gene_id: str, weight: float = 0.7, max_per_gene: int = 5):
    """From Reactome UniProt-mapping `pathways` (a list of pathway dicts), return
    (pathway_nodes, :participates-in edges).

    PUBLIC curated Reactome pathways only. Bounded: dedupe by stId, prefer TOP-LEVEL pathways
    (lowest maxDepth) then stId, cap `max_per_gene`. Curated membership carries no GO-style
    evidence code, so a fixed representative weight (DISCLOSED Reactome curation, N3, never
    re-judged) is used.
    """
    if isinstance(entries, dict):
        entries = [entries]
    best = {}  # stId → (maxDepth, name)
    for p in entries or []:
        if not isinstance(p, dict):
            continue
        st = p.get("stId")
        if not st or not str(st).startswith("R-"):
            continue
        depth = p.get("maxDepth", 99)
        name = p.get("displayName") or (p.get("name") or [st])[0]
        if st not in best or depth < best[st][0]:
            best[st] = (depth, name)

    ranked = sorted(best.items(), key=lambda kv: (kv[1][0], kv[0]))[:max_per_gene]
    pw_nodes, edges = {}, []
    for st, (depth, name) in ranked:
        pw_id = "pw.react-" + st.lower()  # R-HSA-110312 → pw.react-r-hsa-110312
        pw_nodes[pw_id] = {":genome/id": pw_id, ":genome/kind": ":pathway",
                           ":genome/label": name, ":pathway/source": ":reactome",
                           ":pathway/acc": st, ":genome/sourcing": ":authoritative"}
        edges.append({":en/from": gene_id, ":en/to": pw_id, ":en/kind": ":participates-in",
                      ":en/grasping-load": float(weight), ":en/sourcing": ":authoritative"})
    return pw_nodes, edges


def normalise_variant(rsid: str, hit: dict, clinsig_map: dict, pop_map: dict):
    """Return (variant_node, gene_id_or_None, phenotype_nodes, edges) from a MyVariant hit."""
    vid = f"var.{rsid}"
    vnode = {":genome/id": vid, ":genome/kind": ":variant", ":genome/label": rsid,
             ":variant/rsid": rsid, ":genome/sourcing": ":authoritative"}
    vcf = hit.get("vcf") or {}
    ref, alt = vcf.get("ref"), vcf.get("alt")
    if ref and alt:
        if len(ref) == 1 and len(alt) == 1:
            vnode[":variant/category"] = ":snv"
        else:
            vnode[":variant/category"] = ":indel"

    edges, phenos = [], {}

    # gene linkage (:located-in) from dbsnp.gene.symbol
    dbsnp = hit.get("dbsnp") or {}
    g = dbsnp.get("gene") or {}
    if isinstance(g, list) and g:
        g = g[0]
    gsym = g.get("symbol") if isinstance(g, dict) else None
    gene_id = f"gene.{gsym.lower()}" if gsym else None
    if gene_id:
        edges.append({":en/from": vid, ":en/to": gene_id, ":en/kind": ":located-in",
                      ":en/grasping-load": 1.0, ":en/sourcing": ":authoritative"})

    # ClinVar significance → :associated-with edges (DISCLOSED; N3)
    clinvar = hit.get("clinvar") or {}
    rcvs = clinvar.get("rcv") or []
    if isinstance(rcvs, dict):
        rcvs = [rcvs]
    seen = set()
    for rcv in rcvs:
        sig_raw = (rcv.get("clinical_significance") or "").strip()
        clinsig = clinsig_map.get(sig_raw.lower())
        if not clinsig:
            continue  # skip "not provided" / "other" — keep signal honest
        cond = rcv.get("conditions") or {}
        if isinstance(cond, list):
            cond = cond[0] if cond else {}
        ids = cond.get("identifiers") or {}
        mondo = ids.get("mondo")
        omim = ids.get("omim")
        medgen = ids.get("medgen")
        name = cond.get("name") or "unspecified condition"
        if mondo:
            ph_id = "ph." + mondo.lower().replace(":", "-")
            code = mondo
        elif medgen:
            ph_id = f"ph.medgen-{medgen}"
            code = f"MedGen:{medgen}"
        else:
            ph_id = "ph." + _slug(name)[:48]
            code = None
        if ph_id not in phenos:
            ph = {":genome/id": ph_id, ":genome/kind": ":phenotype",
                  ":genome/label": name, ":genome/sourcing": ":authoritative"}
            if code:
                ph[":phenotype/code"] = code
            phenos[ph_id] = ph
        key = (ph_id, clinsig)
        if key in seen:
            continue
        seen.add(key)
        # grasping-load: representative default keyed to disclosed clinsig (documented modeling weight)
        load_default = {":pathogenic": 0.9, ":likely-pathogenic": 0.7, ":risk-factor": 0.5,
                        ":drug-response": 0.4, ":uncertain": 0.3, ":likely-benign": 0.1,
                        ":benign": 0.05, ":protective": 0.1}.get(clinsig, 0.3)
        edges.append({":en/from": vid, ":en/to": ph_id, ":en/kind": ":associated-with",
                      ":en/clinsig": clinsig, ":en/grasping-load": load_default,
                      ":en/sourcing": ":authoritative"})

    # gnomAD SUPER-POPULATION AGGREGATE allele frequencies (G1: aggregate only)
    af = ((hit.get("gnomad_genome") or {}).get("af")) or {}
    for field, popcode in pop_map.items():
        v = af.get(field)
        if isinstance(v, (int, float)):
            pop_id = "pop." + popcode.lstrip(":").lower()
            edges.append({":en/from": pop_id, ":en/to": vid, ":en/kind": ":allele-frequency",
                          ":en/grasping-load": round(float(v), 6), ":en/sourcing": ":authoritative"})

    return vnode, gene_id, phenos, edges


def population_nodes(pop_map: dict) -> dict:
    labels = {":global": "Global (all super-populations)", ":AFR": "African / African-American (AFR)",
              ":AMR": "Admixed American (AMR)", ":EAS": "East Asian (EAS)",
              ":EUR": "European (non-Finnish, EUR)", ":SAS": "South Asian (SAS)"}
    out = {}
    for popcode in set(pop_map.values()):
        pid = "pop." + popcode.lstrip(":").lower()
        out[pid] = {":genome/id": pid, ":genome/kind": ":population",
                    ":genome/label": labels.get(popcode, popcode),
                    ":population/code": popcode, ":genome/sourcing": ":authoritative"}
    return out


# ── EDN serialisation (mirrors datom_emit._fmt; deterministic key order) ──────
_NODE_KEY_ORDER = [":genome/id", ":genome/kind", ":genome/label", ":gene/symbol",
                   ":gene/cytoband", ":gene/ensembl", ":gene/taxon", ":variant/rsid",
                   ":variant/category", ":phenotype/code", ":phenotype/inheritance",
                   ":population/code", ":genome/links", ":genome/sourcing"]
_EDGE_KEY_ORDER = [":en/from", ":en/to", ":en/kind", ":en/clinsig", ":en/grasping-load", ":en/sourcing"]


def _fmt(v) -> str:
    if v is True: return "true"
    if v is False: return "false"
    if v is None: return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float): return f"{v:g}"
    return str(v)


def _emit_map(m: dict, order: list) -> str:
    keys = [k for k in order if k in m] + [k for k in m if k not in order]
    return "{" + " ".join(f"{k} {_fmt(m[k])}" for k in keys) + "}"


def serialise_graph(nodes: dict, edges: list, prov: dict) -> str:
    L = [";; rasen 螺旋 — GENERATED ingested public-genetics graph (ADR-2606101000). DO NOT hand-edit.",
         ";; PUBLIC reference only — no individual genotypes; gnomAD super-population AGGREGATE freq (G1).",
         f";; sources: {', '.join(s['url'] for s in prov['sources'])}",
         f";; counts: {prov['counts']}",
         "["]
    order_kind = {":gene": 0, ":variant": 1, ":phenotype": 2, ":population": 3, ":pathway": 4}
    for nid in sorted(nodes, key=lambda i: (order_kind.get(nodes[i].get(":genome/kind"), 9), i)):
        L.append(" " + _emit_map(nodes[nid], _NODE_KEY_ORDER))
    L.append("")
    for e in sorted(edges, key=lambda e: (e[":en/kind"], e[":en/from"], e[":en/to"])):
        L.append(" " + _emit_map(e, _EDGE_KEY_ORDER))
    L.append("]")
    return "\n".join(L) + "\n"


# ── pipeline ──────────────────────────────────────────────────────────────────
def ingest(sources: dict, outdir: pathlib.Path, prov: dict):
    pop_map = {k: (v if isinstance(v, str) and v.startswith(":") else v)
               for k, v in sources[":ingest/population-map"].items()}
    clinsig_map = {k: v for k, v in sources[":ingest/clinsig-map"].items()}
    gene_url = next(s[":source/url"] for s in sources[":ingest/sources"] if s[":source/id"] == ":mygene")
    var_url = next(s[":source/url"] for s in sources[":ingest/sources"] if s[":source/id"] == ":myvariant")

    go_cfg = sources.get(":ingest/go") or {}
    go_category = (go_cfg.get(":category") or "BP")
    go_max = int(go_cfg.get(":max-per-gene") or 6)

    react_cfg = sources.get(":ingest/reactome") or {}
    react_on = bool(react_cfg.get(":enabled"))
    react_url = next((s[":source/url"] for s in sources[":ingest/sources"]
                      if s[":source/id"] == ":reactome"), None)
    react_species = str(react_cfg.get(":species") or "9606")
    react_max = int(react_cfg.get(":max-per-gene") or 5)
    react_weight = float(react_cfg.get(":weight") or 0.7)

    nodes, edges = {}, []
    nodes.update(population_nodes(pop_map))

    # genes (+ GO pathway membership + optional Reactome curated pathways)
    for sym in sources[":ingest/genes"]:
        try:
            data, q = _get_json(gene_url, {"q": f"symbol:{sym}", "species": "human",
                                           "fields": "symbol,name,ensembl.gene,map_location,taxid,"
                                                     f"go.{go_category},uniprot.Swiss-Prot", "size": 1})
            hits = data.get("hits") or []
            if hits:
                n = gene_node_from_mygene(hits[0], sym)
                nodes[n[":genome/id"]] = n
                prov["fetched"]["genes"] += 1
                pw_nodes, pw_edges = build_gene_pathways(hits[0], n[":genome/id"], go_category, go_max)
                for pid, pn in pw_nodes.items():
                    nodes.setdefault(pid, pn)
                edges.extend(pw_edges)
                prov["fetched"]["go_edges"] += len(pw_edges)

                # Reactome curated pathways via UniProt accession (operator-authorized, G7)
                if react_on and react_url:
                    up = (hits[0].get("uniprot") or {}).get("Swiss-Prot")
                    if isinstance(up, list):
                        up = up[0] if up else None
                    if up:
                        try:
                            entries, _ = _get_json(f"{react_url}/{up}/pathways",
                                                   {"species": react_species})
                            rp_nodes, rp_edges = build_reactome_pathways(
                                entries, n[":genome/id"], react_weight, react_max)
                            for pid, pn in rp_nodes.items():
                                nodes.setdefault(pid, pn)
                            edges.extend(rp_edges)
                            prov["fetched"]["reactome_edges"] += len(rp_edges)
                        except (urllib.error.URLError, urllib.error.HTTPError,
                                ValueError, TimeoutError) as e:
                            prov["errors"].append(f"reactome {sym}/{up}: {type(e).__name__}: {e}")
            else:
                prov["errors"].append(f"gene {sym}: no hit")
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
            prov["errors"].append(f"gene {sym}: {type(e).__name__}: {e}")

    # variants
    for rsid in sources[":ingest/variants"]:
        try:
            data, q = _get_json(var_url, {"q": f"dbsnp.rsid:{rsid}",
                                          "fields": "dbsnp.rsid,dbsnp.gene.symbol,vcf,"
                                                    "clinvar.rcv.clinical_significance,"
                                                    "clinvar.rcv.conditions,gnomad_genome.af",
                                          "size": 1})
            hits = data.get("hits") or []
            if not hits:
                prov["errors"].append(f"variant {rsid}: no hit")
                continue
            vnode, gene_id, phenos, vedges = normalise_variant(rsid, hits[0], clinsig_map, pop_map)
            nodes[vnode[":genome/id"]] = vnode
            for pid, pn in phenos.items():
                nodes.setdefault(pid, pn)
            # ensure a gene node exists for the located-in target (minimal if not in allowlist)
            if gene_id and gene_id not in nodes:
                sym = gene_id.split(".", 1)[1].upper()
                nodes[gene_id] = {":genome/id": gene_id, ":genome/kind": ":gene",
                                  ":genome/label": sym, ":gene/symbol": sym,
                                  ":gene/taxon": ":homo-sapiens", ":genome/sourcing": ":authoritative"}
            edges.extend(vedges)
            prov["fetched"]["variants"] += 1
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
            prov["errors"].append(f"variant {rsid}: {type(e).__name__}: {e}")

    # drop edges with no resolvable endpoint (defensive; keeps graph clean)
    edges = [e for e in edges if e[":en/from"] in nodes and e[":en/to"] in nodes]
    return nodes, edges


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    src_path = here / "data" / "ingest-sources.edn"
    if "--sources" in argv:
        src_path = pathlib.Path(argv[argv.index("--sources") + 1])
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    offline = "--offline" in argv
    no_pin = "--no-pin" in argv

    graph_path = outdir / "ingested-genome-graph.kotoba.edn"
    sources = read_edn(src_path.read_text(encoding="utf-8"))

    prov = {"ingest_id": sources.get(":ingest/id"), "adr": sources.get(":ingest/adr"),
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "sources": [{"id": s[":source/id"].lstrip(":"), "url": s[":source/url"],
                         "scope": s[":source/scope"], "individual_level": s.get(":source/individual?", False)}
                        for s in sources[":ingest/sources"]],
            "fetched": {"genes": 0, "variants": 0, "go_edges": 0, "reactome_edges": 0},
            "errors": [], "counts": {}}

    if offline:
        if not graph_path.exists():
            print("ingest --offline: no existing graph to re-address", file=sys.stderr)
            return 1
        nodes, edges = load(graph_path)
        prov["offline"] = True
        print(f"rasen ingest (offline): re-addressing existing graph ({len(nodes)} nodes)")
    else:
        nodes, edges = ingest(sources, outdir, prov)
        prov["counts"] = {
            "genes": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":gene"),
            "variants": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":variant"),
            "phenotypes": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":phenotype"),
            "populations": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":population"),
            "edges": len(edges),
        }
        edn = serialise_graph(nodes, edges, prov)
        graph_path.write_text(edn, encoding="utf-8")

    # reload for canonical analysis + datom projection
    nodes, edges = load(graph_path)
    prov["counts"] = {
        "genes": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":gene"),
        "variants": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":variant"),
        "phenotypes": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":phenotype"),
        "populations": sum(1 for n in nodes.values() if n.get(":genome/kind") == ":population"),
        "edges": len(edges),
    }
    res = analyze(nodes, edges)
    datoms = datom_emit.emit(nodes, edges, res, tx=1)
    datom_path = outdir / "ingested-genome-datoms.kotoba.edn"
    datom_path.write_text(datoms, encoding="utf-8")

    # kotoba IPFS content-address (CIDv1 raw) of the canonical graph artifact
    graph_bytes = graph_path.read_bytes()
    cid = cidlib.cidv1_raw(graph_bytes)
    datom_cid = cidlib.cidv1_raw(datom_path.read_bytes())
    (outdir / "ingested.cid").write_text(cid + "\n", encoding="utf-8")

    prov["artifact"] = {"graph_edn": graph_path.name, "bytes": len(graph_bytes),
                        "cid": cid, "datoms_cid": datom_cid,
                        "single_block": len(graph_bytes) <= cidlib.SINGLE_BLOCK_LIMIT}

    # best-effort pin to local ipfs (non-fatal; CID is authoritative either way)
    prov["pin"] = {"attempted": False}
    if not no_pin:
        import shutil, subprocess
        if shutil.which("ipfs"):
            prov["pin"]["attempted"] = True
            try:
                out = subprocess.run(["ipfs", "add", "-Q", "--cid-version=1", "--raw-leaves",
                                      str(graph_path)], capture_output=True, text=True, timeout=30)
                if out.returncode == 0:
                    pinned = out.stdout.strip()
                    prov["pin"].update({"ok": True, "cid": pinned, "matches": pinned == cid})
                else:
                    prov["pin"].update({"ok": False, "error": out.stderr.strip()[:200]})
            except Exception as e:  # noqa: BLE001 — pinning is best-effort
                prov["pin"].update({"ok": False, "error": f"{type(e).__name__}: {e}"})

    (outdir / "ingest-provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")

    print(f"rasen ingest → {graph_path}")
    print(f"  nodes={len(nodes)} edges={len(edges)} | fetched {prov['fetched']} | errors={len(prov['errors'])}")
    print(f"  kotoba IPFS CID (graph) : {cid}")
    print(f"  kotoba IPFS CID (datoms): {datom_cid}")
    if prov["pin"].get("attempted"):
        p = prov["pin"]
        print(f"  ipfs pin: ok={p.get('ok')} matches={p.get('matches')}" +
              (f" pinned={p.get('cid')}" if p.get("cid") else ""))
    if prov["errors"]:
        print(f"  ⚠ {len(prov['errors'])} fetch issue(s) — see out/ingest-provenance.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
