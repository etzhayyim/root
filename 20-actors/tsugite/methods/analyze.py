#!/usr/bin/env python3
"""tsugite 継ぎ手 — edge-primary peoples-continuity analyzer over the peoples graph.

ADR-2606073800. Reads a kotoba-EDN peoples graph (:organism/* nodes + :en/* 縁 over the
peoples-ontology) and surfaces — aggregate-first, at COLLECTIVE scale — where DISPLACEMENT +
ERASURE pressure concentrates on human collectives and the tongues they carry (the continuity
surface), where PROTECTION buffers absorb it, and how fragile each people↔tongue transmission
coupling is, all routed to CONTINUITY (継承) — safe passage + protection + revitalization.

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. karma/pressure lives ONLY on edges (:en/peril-load). A bearer's
    continuity-need is the INTEGRAL of its incident inbound pressure 縁 (severity × disclosed
    vitality weight) — computed on READ, never a stored per-collective score. There is no
    :tsugite/score-of-people.
  G1 — PEOPLES-CONTINUITY map at AGGREGATE / collective scale, NEVER a person-tracking /
    individual-locator / border-enforcement / deportation / surveillance aid. No individual
    records, no real-time location, no biometric. The bearer is ALWAYS a collective. It routes
    to refuge + revitalization, never to interdiction.
  N3 — non-adjudicating. Displacement figures and language-vitality categories are DISCLOSED
    facts (UNHCR/IOM/UNESCO/Ethnologue), never tsugite verdicts.

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text: str):
    return _parse(_tokens(text))


# ── disclosed language-vitality → representative weight (NOT a verdict; mirrors schema)
VITALITY_WEIGHT = {":extinct": 1.0, ":critically-endangered": 0.9, ":severely-endangered": 0.8,
                   ":definitely-endangered": 0.6, ":vulnerable": 0.4, ":safe": 0.1}

PRESSURE_KINDS = {":displaces", ":erases"}
HAVEN_KINDS = {":shelters", ":revitalizes", ":protects"}
TRANSMISSION_KINDS = {":speaks"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a peoples EDN graph."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":organism/id" in f:
            nodes[f[":organism/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def analyze(nodes: dict, edges: list):
    """Edge-primary integrals (computed on read; transient — N1/G2).

    continuity[bearer]  = Σ incident inbound pressure load × disclosed vitality weight
    protection[node]    = Σ incident inbound :shelters/:revitalizes/:protects load
    fragility[node]     = Σ incident :speaks load (people ↔ tongue transmission coupling)
    pressure_out[src]   = Σ outbound pressure load (the 取-holder driver)
    """
    continuity = defaultdict(float)
    protection = defaultdict(float)
    fragility = defaultdict(float)
    pressure_out = defaultdict(float)

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/peril-load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in PRESSURE_KINDS:
            bearer = nodes.get(dst, {})
            w = VITALITY_WEIGHT.get(bearer.get(":lang/vitality"), 0.6)  # peoples → neutral 0.6
            continuity[dst] += load_ * w
            pressure_out[src] += load_
        elif kind in HAVEN_KINDS:
            protection[dst] += load_
        elif kind in TRANSMISSION_KINDS:
            fragility[src] += load_
            fragility[dst] += load_

    return {
        "continuity": dict(continuity),
        "protection": dict(protection),
        "fragility": dict(fragility),
        "pressure_out": dict(pressure_out),
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: -kv[1])[:limit]
    return [(nid, nodes.get(nid, {}).get(":organism/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_ppl = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":people")
    n_lang = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":language")
    n_press = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":pressure")
    auth = sum(1 for n in nodes.values() if n.get(":organism/sourcing") == ":authoritative")

    L = []
    L.append("# tsugite 継ぎ手 — peoples-continuity report (collective-aggregate)\n")
    L.append("> **G1 — PEOPLES-CONTINUITY map, NEVER person-tracking.** Collective scale only; "
             "no individual records, no real-time location, no biometric, no border-enforcement "
             "/ deportation use. The 取-holder is the pressure; the bearer is the collective / "
             "tongue; the routing is continuity (継承) — safe passage + protection + "
             "revitalization, never interdiction. Displacement figures + language vitality are "
             "DISCLOSED (N3). Pressure lives only on edges, integrated on read (N1).\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_ppl} peoples · {n_lang} languages · "
             f"{n_press} pressures) · {len(edges)} 縁 · {auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Continuity need — collectives/tongues bearing the most displacement+erasure\n")
    L.append("_Σ incident inbound pressure-load × disclosed vitality weight; routed to continuity._\n")
    L.append("| rank | bearer | vitality | continuity-need |")
    L.append("|---:|---|:--:|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["continuity"], nodes), 1):
        vit = nodes.get(nid, {}).get(":lang/vitality", "—") or "—"
        L.append(f"| {i} | {label} | {vit.lstrip(':')} | {v:.3f} |")

    L.append("\n## Pressure concentration — drivers of displacement + erasure\n")
    L.append("_Σ outbound pressure-load; the 取-holders, routed to protection + revitalization._\n")
    L.append("| rank | pressure | kind | imposed-load |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["pressure_out"], nodes), 1):
        kind = nodes.get(nid, {}).get(":pressure/kind", "—") or "—"
        L.append(f"| {i} | {label} | {kind.lstrip(':')} | {v:.3f} |")

    L.append("\n## Protection buffers — refuge / revitalization (the 守り)\n")
    L.append("| rank | node | protection-buffer |")
    L.append("|---:|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["protection"], nodes, 12), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n## Transmission fragility — people↔tongue coupling at risk (loss cascades)\n")
    L.append("| rank | node | fragility |")
    L.append("|---:|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["fragility"], nodes, 10), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n---\n_tsugite 継ぎ手 · ADR-2606073800 · mirror-only · continuity-routed · "
             "non-adjudicating · no-person-tracking · edge-primary. Live aggregate ingest is "
             "G7/Council-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-peoples-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "continuity-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"tsugite: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'continuity-report.md'}")
    top = _rank(res["continuity"], nodes, 1)
    if top:
        print(f"  top continuity-need: {top[0][1]} ({top[0][2]:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
