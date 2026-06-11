#!/usr/bin/env python3
"""hokorobi 綻び — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

Projects the systemic finance-risk graph into append-only kotoba Datoms [e a v tx op].

  GROUND (durable, op :add) — node + 縁 datoms. This IS the Datom log.
  DERIVED (transient, :bond/is-transient true) — edge-primary systemic-risk / resilience
    integrals; computed on READ, NOT persisted (N1/G2).

Pure stdlib — runnable inside the hokorobi kotoba pywasm actor (componentize-py).
Usage:
    python3 datom_emit.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze, read_edn  # noqa: F401,E402

NODE_ATTRS = [":organism/kind", ":organism/label", ":organism/sourcing",
              ":inst/sector", ":inst/sii", ":inst/jurisdiction",
              ":risk/kind", ":bearer/kind"]
EDGE_ATTRS = [":en/from", ":en/to", ":en/kind", ":en/risk-load", ":en/sourcing"]


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
    L.append(";; hokorobi 綻び — GENERATED kotoba Datom log (ADR-2606073400). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1/G2).")
    L.append("[")

    for nid in nodes:
        n = nodes[nid]
        for a in NODE_ATTRS:
            if a in n and n[a] is not None:
                L.append(f"[{_fmt(nid)} {a} {_fmt(n[a])} {tx} :add]")

    for e in edges:
        eid = f"en.{e[':en/from']}.{e[':en/kind'].lstrip(':')}.{e[':en/to']}"
        for a in EDGE_ATTRS:
            if a in e and e[a] is not None:
                L.append(f"{'[' + _fmt(eid)} {a} {_fmt(e[a])} {tx} :add]")

    L.append(";; ── DERIVED readouts (transient; integral of incident 縁, computed on read) ──")
    for nid, v in sorted(res["systemic"].items(), key=lambda kv: -kv[1]):
        L.append(f"[{_fmt(nid)} :bond/systemic-risk-concentration {v:g} {tx} :derived] ;; :bond/is-transient true")
    for nid, v in sorted(res["resilience"].items(), key=lambda kv: -kv[1]):
        L.append(f"[{_fmt(nid)} :bond/resilience-buffer {v:g} {tx} :derived] ;; :bond/is-transient true")
    for nid, v in sorted(res["risk_out"].items(), key=lambda kv: -kv[1]):
        L.append(f"[{_fmt(nid)} :bond/risk-imposed {v:g} {tx} :derived] ;; :bond/is-transient true")

    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-finrisk-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    out = outdir / "finrisk-datoms.kotoba.edn"
    out.write_text(emit(nodes, edges, res, tx), encoding="utf-8")
    print(f"hokorobi datom log → {out} ({len(nodes)} nodes + {len(edges)} 縁, tx={tx})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
