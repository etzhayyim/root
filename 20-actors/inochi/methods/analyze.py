#!/usr/bin/env python3
"""inochi 命 — edge-primary ecological 取-concentration analyzer over the biosphere graph.

ADR-2606073000. Reads a kotoba-EDN biosphere graph (:organism/* nodes + :en/* 縁 over
the biosphere-ontology), and surfaces — aggregate-first — where ECOLOGICAL custody-debt
(extinction / degradation pressure) accumulates over the living world, routed to
RESTORATION (release), and where dependency cascades make that debt fragile.

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. karma/取 lives ONLY on edges (:en/grasping-load). A node's
    restoration-priority is the INTEGRAL of its incident inbound :pressures edges
    (severity × disclosed IUCN weight) — computed on READ, never a stored per-organism
    score. There is no :biosphere/score-of-species.
  G1 — RESTORATION map, never a target-list. No precise occurrence coordinates are read
    or emitted; spatial readouts are biome/realm-aggregate only. The 取-holder is the
    PRESSURE; the bearer is the living world; the routing is restoration.
  N3 — non-adjudicating. IUCN categories are DISCLOSED facts, never inochi verdicts.

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
        return t  # keep keywords as ":ns/name" strings
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


# ── disclosed IUCN category → representative threat weight (NOT a verdict; mirrors schema)
IUCN_WEIGHT = {":EX": 1.0, ":EW": 1.0, ":CR": 0.9, ":EN": 0.7, ":VU": 0.5,
               ":NT": 0.3, ":LC": 0.1, ":DD": 0.4}

PRESSURE_KINDS = {":pressures"}
DEPENDENCY_KINDS = {":depends-on", ":keystone-of"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a biosphere EDN graph."""
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

    restoration_priority[node] = Σ incident inbound :pressures load × IUCN weight of bearer
    dependency_fragility[node] = Σ incident :depends-on / :keystone-of load (cascade risk)
    pressure_load[node]        = Σ outbound :pressures load a pressure imposes (the 取-holder)
    """
    restoration = defaultdict(float)
    fragility = defaultdict(float)
    pressure_out = defaultdict(float)

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/grasping-load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in PRESSURE_KINDS:
            bearer = nodes.get(dst, {})
            w = IUCN_WEIGHT.get(bearer.get(":taxon/iucn"), 0.5)  # ecosystems → neutral 0.5
            restoration[dst] += load_ * w
            pressure_out[src] += load_
        elif kind in DEPENDENCY_KINDS:
            # the depender (src) is fragile to the loss of the depended-on (dst);
            # the keystone (src) carries criticality for the ecosystem (dst).
            fragility[src] += load_
            fragility[dst] += load_

    return {
        "restoration": dict(restoration),
        "fragility": dict(fragility),
        "pressure_out": dict(pressure_out),
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: -kv[1])[:limit]
    return [(nid, nodes.get(nid, {}).get(":organism/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_species = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":species")
    n_eco = sum(1 for n in nodes.values() if n.get(":organism/kind") in (":ecosystem", ":biome"))
    n_press = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":pressure")
    auth = sum(1 for n in nodes.values() if n.get(":organism/sourcing") == ":authoritative")

    L = []
    L.append("# inochi 命 — biosphere restoration-priority report (aggregate-first)\n")
    L.append("> **G1 — RESTORATION map, NEVER a target-list.** No occurrence coordinates; "
             "biome/realm-aggregate only. The 取-holder is the pressure; the bearer is the "
             "living world; the routing is restoration. IUCN categories are DISCLOSED, not "
             "inochi verdicts (N3). 取 lives only on edges, integrated on read (N1).\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_species} species · {n_eco} ecosystems/biomes · "
             f"{n_press} pressures) · {len(edges)} 縁 · {auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Restoration priority — living world bearing the most custody-debt\n")
    L.append("_Σ incident inbound pressure-load × disclosed IUCN weight; routed to restoration._\n")
    L.append("| rank | bearer | IUCN | restoration-priority |")
    L.append("|---:|---|:--:|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["restoration"], nodes), 1):
        iucn = nodes.get(nid, {}).get(":taxon/iucn", "—") or "—"
        L.append(f"| {i} | {label} | {iucn.lstrip(':')} | {v:.3f} |")

    L.append("\n## Pressure concentration — 取-holders imposing the most ecological debt\n")
    L.append("_Σ outbound pressure-load; cross-link to tsumugi/danjo power-graph where a "
             "power-entity drives the pressure (accountability, aggregate-first)._\n")
    L.append("| rank | pressure | kind | imposed-load |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["pressure_out"], nodes), 1):
        kind = nodes.get(nid, {}).get(":pressure/kind", "—") or "—"
        L.append(f"| {i} | {label} | {kind.lstrip(':')} | {v:.3f} |")

    L.append("\n## Cascade fragility — dependency / keystone load (loss propagates)\n")
    L.append("| rank | node | fragility |")
    L.append("|---:|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["fragility"], nodes, 12), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n---\n_inochi 命 · ADR-2606073000 · mirror-only · non-adjudicating · "
             "edge-primary · restoration-routed. Live ingest (IUCN/GBIF/IPCC) is "
             "G7/Council-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-biosphere-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "restoration-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"inochi: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'restoration-report.md'}")
    top = _rank(res["restoration"], nodes, 1)
    if top:
        print(f"  top restoration-priority: {top[0][1]} ({top[0][2]:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
