#!/usr/bin/env python3
"""kadode 門出 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

Projects the labour-exit graph into append-only kotoba Datoms [e a v tx op] — first-class
canonical state. GROUND (durable, :add) = the scenario / ground / document / route / risk nodes
and their :en/* 縁 (incl. every :requires-route + :upl-bound edge that encodes the 弁護士法72条
boundary). DERIVED (transient, :bond/is-transient) = the edge-primary ground-support /
risk-coverage integrals, computed on read (N1/G2), never persisted.

Pure stdlib. Usage: python3 datom_emit.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402

NODE_ATTRS = [":lx/kind", ":lx/label", ":lx/sourcing", ":lx/links",
              ":scenario/employment", ":scenario/needs-negotiation",
              ":ground/citation", ":ground/instrument", ":ground/url",
              ":document/kind", ":document/binding",
              ":route/actor", ":route/can-negotiate", ":risk/pattern"]
EDGE_ATTRS = [":en/from", ":en/to", ":en/kind", ":en/weight", ":en/force", ":en/sourcing"]


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
    L.append(";; kadode 門出 — GENERATED kotoba Datom log (ADR-2606112238). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
    L.append(";; G1: kadode is a 使者 (messenger), never an agent; routes encode the 弁護士法72条 boundary.")
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
                L.append(f"{'[' + _fmt(eid)} {a} {_fmt(e[a])} {tx} :add]")
    L.append(";; ── DERIVED readouts (transient; integral of incident 縁, computed on read) ──")
    for nid, v in sorted(res["ground_support"].items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"[{_fmt(nid)} :bond/ground-support {v:g} {tx} :derived] ;; :bond/is-transient true")
    for nid, v in sorted(res["risk_coverage"].items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"[{_fmt(nid)} :bond/risk-coverage {v:g} {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-resignation-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    out = outdir / "resignation-datoms.kotoba.edn"
    out.write_text(emit(nodes, edges, res, tx), encoding="utf-8")
    print(f"kadode datom log → {out} ({len(nodes)} nodes + {len(edges)} 縁, tx={tx})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
