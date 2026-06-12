#!/usr/bin/env python3
"""tanemaki 種蒔き — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

Projects the fund-stewardship graph into append-only kotoba Datoms [e a v tx op] — first-class
canonical state. GROUND (durable, :add) = the org / screen / criterion / source / instrument /
milestone nodes and their :en/* 縁 (incl. every :screened finding — the PUBLIC DD trail — and
the disclosed rubric weights). DERIVED (transient, :bond/is-transient) = dd-fit / evidence-
coverage / route, computed on read (N1/G4), never persisted — there is no stored org score.

Pure stdlib. Usage: python3 datom_emit.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402

NODE_ATTRS = [":fs/kind", ":fs/label", ":fs/sourcing", ":fs/links",
              ":org/form", ":org/synthetic", ":org/mission-axis",
              ":screen/code", ":screen/basis",
              ":criterion/code", ":criterion/weight", ":criterion/axis",
              ":source/actor", ":source/nature",
              ":instrument/kind", ":milestone/evidence"]
EDGE_ATTRS = [":en/from", ":en/to", ":en/kind", ":en/finding", ":en/weight",
              ":en/evidence", ":en/sourcing"]


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
    L.append(";; tanemaki 種蒔き — GENERATED kotoba Datom log (ADR-2606122001). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable (incl. the PUBLIC :screened DD trail + disclosed rubric weights).")
    L.append(";; DERIVED :bond/is-transient = computed on read (N1/G4) — no stored org score, no decision.")
    L.append(";; G1: tanemaki is a steward, never a sovereign; every grant is decided by 1 SBT = 1 vote.")
    L.append("[")
    for nid in nodes:
        nd = nodes[nid]
        for a in NODE_ATTRS:
            if a in nd and nd[a] is not None:
                L.append(f"[{_fmt(nid)} {a} {_fmt(nd[a])} {tx} :add]")
    for e in edges:
        eid = f"en.{e[':en/from']}.{e[':en/kind'].lstrip(':')}.{e[':en/to']}"
        for a in EDGE_ATTRS:
            if a in e and e[a] is not None:
                L.append(f"[{_fmt(eid)} {a} {_fmt(e[a])} {tx} :add]")
    L.append(";; ── DERIVED readouts (transient; integral of incident 縁, computed on read) ──")
    for oid in sorted(res["orgs"]):
        r = res["orgs"][oid]
        L.append(f"[{_fmt(oid)} :bond/dd-fit {r['dd_fit']:g} {tx} :derived] ;; :bond/is-transient true")
        L.append(f"[{_fmt(oid)} :bond/evidence-coverage {r['evidence_coverage']:g} {tx} :derived] ;; :bond/is-transient true")
        L.append(f"[{_fmt(oid)} :bond/route {r['route']} {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-stewardship-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    out = outdir / "stewardship-datoms.kotoba.edn"
    out.write_text(emit(nodes, edges, res, tx), encoding="utf-8")
    print(f"tanemaki datom log → {out} ({len(nodes)} nodes + {len(edges)} 縁, tx={tx})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
