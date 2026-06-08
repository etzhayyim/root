#!/usr/bin/env python3
"""shiori 栞 — edge-primary wellbecoming-detraction analyzer over the detraction graph.

ADR-2606082100. Reads a kotoba-EDN wellbecoming graph (:organism/* nodes + :en/* 縁 over the
wellbecoming-ontology) and surfaces — aggregate-first, at COHORT scale — where structural
DETRACTION pressure (precarity / overwork / isolation / addictive-design / debt / housing-
insecurity / chronic-pain / discrimination / care-deprivation ...) concentrates on human
cohorts (the detraction surface), where RELIEF buffers absorb it, the RELIEF GAP that names who
is most under-served (the routing signal to ossekai), which structural DRIVERS impose the most
(the 取-holders, routed to transparency), and which detractors still lack a known relief route
(the intervention-design gap) — all routed to RELIEF / 救い via a TRANSPARENT intervention.

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. karma/detraction lives ONLY on edges (:en/load). A cohort's
    wellbecoming-burden is the INTEGRAL of its incident inbound detraction 縁 (load × disclosed
    severity weight) — computed on READ, never a stored per-cohort/per-person score. There is no
    :shiori/score-of-cohort.
  G1 — WELLBECOMING-RELIEF map at AGGREGATE / cohort scale, NEVER a per-person affect / happiness
    / sentiment scoring or manipulation engine. No individual records, no per-person mood/affect
    score, no biometric. The bearer is ALWAYS a cohort. Drivers are structural PATTERNS, never
    named orgs/persons. It routes to relief, never to coercion / dark patterns (anti-addictive).
  N3 — non-adjudicating. Detractor-severity bands + cohort burden patterns are DISCLOSED facts
    (OECD/WHO/public wellbeing research), never shiori verdicts.

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


# ── disclosed detractor-severity → representative weight (NOT a verdict; mirrors schema)
SEVERITY_WEIGHT = {":critical": 1.0, ":severe": 0.8, ":moderate": 0.5, ":mild": 0.25}

DIMINISH_KINDS = {":diminishes"}
DRIVE_KINDS = {":drives"}
RELIEVE_KINDS = {":relieves"}
ROUTE_KINDS = {":routes-to"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a wellbecoming EDN graph."""
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

    burden[cohort]    = Σ incident inbound :diminishes load × disclosed severity weight
    relief[cohort]    = Σ incident inbound :relieves load
    gap[cohort]       = burden − relief   (>0 = under-served; the routing signal to ossekai)
    imposed[src]      = Σ outbound :drives + :diminishes load (the 取-holder driver/detractor)
    route_cov[detr]   = Σ outbound :routes-to load (0 = intervention-design gap)
    """
    burden = defaultdict(float)
    relief = defaultdict(float)
    imposed = defaultdict(float)
    route_cov = defaultdict(float)

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in DIMINISH_KINDS:
            sev = nodes.get(src, {}).get(":detractor/severity")
            w = SEVERITY_WEIGHT.get(sev, 0.5)  # unknown severity → neutral 0.5
            burden[dst] += load_ * w
            imposed[src] += load_
        elif kind in DRIVE_KINDS:
            imposed[src] += load_
        elif kind in RELIEVE_KINDS:
            relief[dst] += load_
        elif kind in ROUTE_KINDS:
            route_cov[src] += load_

    gap = {}
    for cid, b in burden.items():
        gap[cid] = b - relief.get(cid, 0.0)

    # detractors with detraction but no relief route = intervention-design gap
    unrouted = sorted(
        nid for nid, n in nodes.items()
        if n.get(":organism/kind") == ":detractor"
        and imposed.get(nid, 0.0) > 0 and route_cov.get(nid, 0.0) == 0.0
    )

    return {
        "burden": dict(burden),
        "relief": dict(relief),
        "gap": gap,
        "imposed": dict(imposed),
        "route_coverage": dict(route_cov),
        "unrouted_detractors": unrouted,
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: -kv[1])[:limit]
    return [(nid, nodes.get(nid, {}).get(":organism/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_coh = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":cohort")
    n_detr = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":detractor")
    n_drv = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":driver")
    n_mit = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":mitigator")
    auth = sum(1 for n in nodes.values() if n.get(":organism/sourcing") == ":authoritative")

    L = []
    L.append("# shiori 栞 — wellbecoming relief-gap report (cohort-aggregate)\n")
    L.append("> **G1 — WELLBECOMING-RELIEF map, NEVER a per-person affect/manipulation engine.** "
             "Cohort scale only; no individual records, no per-person happiness/mood/affect score, "
             "no biometric. Drivers are structural PATTERNS, never named orgs/persons. The 取-holder "
             "is the detractor/driver; the bearer is the cohort; the routing is RELIEF (救い) — a "
             "TRANSPARENT Wellbecoming intervention carried by ossekai, never coercion / dark "
             "patterns (anti-addictive, §1.13). Severity bands are DISCLOSED (N3). Detraction lives "
             "only on edges, integrated on read (N1).\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_coh} cohorts · {n_detr} detractors · "
             f"{n_drv} drivers · {n_mit} mitigators) · {len(edges)} 縁 · "
             f"{auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Relief gap — cohorts where detraction most exceeds relief (→ ossekai)\n")
    L.append("_burden (Σ inbound :diminishes × disclosed severity) − relief (Σ inbound :relieves); "
             "the routing signal for a transparent intervention._\n")
    L.append("| rank | cohort | burden | relief | relief-gap |")
    L.append("|---:|---|---:|---:|---:|")
    for i, (nid, label, g) in enumerate(_rank(res["gap"], nodes), 1):
        b = res["burden"].get(nid, 0.0)
        r = res["relief"].get(nid, 0.0)
        L.append(f"| {i} | {label} | {b:.3f} | {r:.3f} | {g:+.3f} |")

    L.append("\n## Detraction concentration — drivers + detractors imposing the most\n")
    L.append("_Σ outbound :drives + :diminishes load; the 取-holders (structural patterns), routed "
             "to transparency (danjo / tsumugi / keizu), never a target-list._\n")
    L.append("| rank | source | kind | imposed-load |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["imposed"], nodes, 14), 1):
        n = nodes.get(nid, {})
        kind = (n.get(":driver/kind") or n.get(":detractor/kind") or "—")
        L.append(f"| {i} | {label} | {str(kind).lstrip(':')} | {v:.3f} |")

    L.append("\n## Relief buffers — the 守り (what to scale)\n")
    L.append("| rank | cohort | relief-buffer |")
    L.append("|---:|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["relief"], nodes, 12), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n## Intervention-design gap — detractions with NO known relief route\n")
    L.append("_a detractor that burdens a cohort but has no :routes-to edge — the next relief to "
             "design (never a reason to do nothing)._\n")
    if res["unrouted_detractors"]:
        for nid in res["unrouted_detractors"]:
            L.append(f"- **{nodes.get(nid, {}).get(':organism/label', nid)}** — no relief route")
    else:
        L.append("- _(every detraction in the seed has at least one relief route)_")

    L.append("\n---\n_shiori 栞 · ADR-2606082100 · mirror-only · relief-routed · non-adjudicating · "
             "no-person-scoring · anti-addictive · edge-primary. Live intervention routing is "
             "G7/Council-gated; ossekai carries, the recipient can always see why (G8).\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-wellbecoming-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "relief-gap-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"shiori: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'relief-gap-report.md'}")
    top = _rank(res["gap"], nodes, 1)
    if top:
        print(f"  top relief-gap: {top[0][1]} ({top[0][2]:+.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
