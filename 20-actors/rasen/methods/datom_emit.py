#!/usr/bin/env python3
"""rasen 螺旋 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

Projects the public-genetics graph into append-only kotoba Datoms [e a v tx op] — the
first-class canonical state (NOT a projection cache). Two strata:

  GROUND (durable, op :add) — one datom per (entity, attribute, value): the gene / variant /
    phenotype / population / pathway nodes and the :en/* 縁. This IS the Datom log.

  DERIVED (transient, :bond/is-transient true) — the edge-primary care / burden / pleiotropy
    integrals. Per N1/G2 these are computed on READ and are NOT stored as ground datoms; they
    are emitted in a clearly-flagged transient block so a reader can materialise them without
    mistaking them for persisted state.

Pure stdlib — runnable inside the rasen kotoba pywasm actor (componentize-py).
Usage:
    python3 datom_emit.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze, read_edn  # noqa: F401,E402

# attributes promoted from each node/edge map into ground datoms (stable order = determinism)
NODE_ATTRS = [":genome/kind", ":genome/label", ":genome/sourcing", ":genome/links",
              ":gene/symbol", ":gene/cytoband", ":gene/ensembl", ":gene/taxon",
              ":variant/rsid", ":variant/category",
              ":phenotype/code", ":phenotype/inheritance",
              ":population/code", ":pathway/source", ":pathway/acc"]
EDGE_ATTRS = [":en/from", ":en/to", ":en/kind", ":en/grasping-load", ":en/clinsig", ":en/sourcing"]


def _fmt(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def emit(nodes: dict, edges: list, res: dict, tx: int = 1) -> str:
    L = []
    L.append(";; rasen 螺旋 — GENERATED kotoba Datom log (ADR-2606101000). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
    L.append(";; G1: PUBLIC reference genetics only — no individual genotypes; aggregate frequencies only.")
    L.append("[")

    # ── GROUND: node datoms
    for nid in nodes:  # insertion order (EDN read order) → deterministic
        n = nodes[nid]
        for a in NODE_ATTRS:
            if a in n and n[a] is not None:
                L.append(f"[{_fmt(nid)} {a} {_fmt(n[a])} {tx} :add]")

    # ── GROUND: edge datoms (edge entity id is content-stable: en.<from>.<kind>.<to>)
    for e in edges:
        eid = f"en.{e[':en/from']}.{e[':en/kind'].lstrip(':')}.{e[':en/to']}"
        for a in EDGE_ATTRS:
            if a in e and e[a] is not None:
                L.append(f"{'[' + _fmt(eid)} {a} {_fmt(e[a])} {tx} :add]")

    # ── DERIVED (transient — NOT persisted; N1/G2)
    L.append(";; ── DERIVED readouts (transient; integral of incident 縁, computed on read) ──")
    for nid, v in sorted(res["care"].items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"[{_fmt(nid)} :bond/care-priority {v:g} {tx} :derived] ;; :bond/is-transient true")
    for nid, v in sorted(res["burden"].items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"[{_fmt(nid)} :bond/locus-burden {v:g} {tx} :derived] ;; :bond/is-transient true")
    for nid, v in sorted(res["pleiotropy"].items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"[{_fmt(nid)} :bond/pleiotropy {v:g} {tx} :derived] ;; :bond/is-transient true")

    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-genome-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    out = outdir / "genome-datoms.kotoba.edn"
    out.write_text(emit(nodes, edges, res, tx), encoding="utf-8")
    print(f"rasen datom log → {out} ({len(nodes)} nodes + {len(edges)} 縁, tx={tx})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
