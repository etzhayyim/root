#!/usr/bin/env python3
"""hokorobi 綻び — edge-primary systemic finance-risk analyzer over the finrisk graph.

ADR-2606073400. Reads a kotoba-EDN finance-risk graph (:organism/* nodes + :en/* 縁 over
the finrisk-ontology) and surfaces — aggregate-first — where SYSTEMIC RISK concentrates
(the resilience surface) vs where RESILIENCE buffers absorb it, routed to RESILIENCE (繕い).

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. karma/risk lives ONLY on edges (:en/risk-load). A node's
    systemic-risk-concentration is the INTEGRAL of its incident inbound risk 縁 (severity ×
    disclosed systemic-importance weight) — computed on READ, never a stored per-institution
    score. There is no :hokorobi/solvency-of-bank.
  G1 — RESILIENCE map, never a panic / bank-run trigger, never a trading / short /
    market-moving signal, never a per-institution solvency verdict. It NEVER trades. The
    取-holder is the RISK-SOURCE; the bearer is the public; the routing is resilience.
  N3 — non-adjudicating. Systemic-importance designations (G-SIB / D-SIB / …) are DISCLOSED
    facts, never hokorobi verdicts; no investment advice / forecast (kanjo discipline).

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


# ── disclosed systemic-importance tier → representative weight (NOT a verdict; mirrors schema)
SII_WEIGHT = {":g-sib": 1.0, ":d-sib": 0.7, ":large": 0.5, ":mid": 0.3, ":small": 0.1}

RISK_KINDS = {":exposes", ":interconnects", ":underfunds", ":protection-gap"}
RESILIENCE_KINDS = {":backstops", ":capitalizes", ":diversifies"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a finrisk EDN graph."""
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

    systemic[node]      = Σ incident inbound risk-load × disclosed systemic-importance weight
    resilience[node]    = Σ incident inbound :backstops/:capitalizes/:diversifies load
    risk_out[source]    = Σ outbound risk-load (the 取-holder risk-source)
    """
    systemic = defaultdict(float)
    resilience = defaultdict(float)
    risk_out = defaultdict(float)

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/risk-load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in RISK_KINDS:
            bearer = nodes.get(dst, {})
            w = SII_WEIGHT.get(bearer.get(":inst/sii"), 0.6)  # bearers (public) → neutral 0.6
            systemic[dst] += load_ * w
            risk_out[src] += load_
        elif kind in RESILIENCE_KINDS:
            resilience[dst] += load_

    return {
        "systemic": dict(systemic),
        "resilience": dict(resilience),
        "risk_out": dict(risk_out),
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: -kv[1])[:limit]
    return [(nid, nodes.get(nid, {}).get(":organism/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_inst = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":institution")
    n_risk = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":risk")
    n_bear = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":bearer")
    auth = sum(1 for n in nodes.values() if n.get(":organism/sourcing") == ":authoritative")

    L = []
    L.append("# hokorobi 綻び — systemic finance-risk report (aggregate-first)\n")
    L.append("> **G1 — RESILIENCE map, NEVER a panic / bank-run / trading signal.** No "
             "market-moving signal, no per-institution solvency verdict; it NEVER trades. The "
             "取-holder is the risk-source; the bearer is the public; the routing is resilience "
             "(繕い). Systemic-importance designations are DISCLOSED, not hokorobi verdicts "
             "(N3); no advice/forecast. Risk lives only on edges, integrated on read (N1).\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_inst} institutions · {n_risk} risk-sources · "
             f"{n_bear} bearers) · {len(edges)} 縁 · {auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Systemic-risk concentration — where fragility accumulates (resilience surface)\n")
    L.append("_Σ incident inbound risk-load × disclosed systemic-importance weight; routed to resilience._\n")
    L.append("| rank | node | SII | systemic-risk |")
    L.append("|---:|---|:--:|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["systemic"], nodes), 1):
        sii = nodes.get(nid, {}).get(":inst/sii", "—") or "—"
        L.append(f"| {i} | {label} | {sii.lstrip(':')} | {v:.3f} |")

    L.append("\n## Risk-source concentration — 取-holders imposing the most systemic fragility\n")
    L.append("_Σ outbound risk-load; the channels of contagion, routed to resilience._\n")
    L.append("| rank | risk-source | kind | imposed-load |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["risk_out"], nodes), 1):
        kind = nodes.get(nid, {}).get(":risk/kind", "—") or "—"
        L.append(f"| {i} | {label} | {kind.lstrip(':')} | {v:.3f} |")

    L.append("\n## Resilience buffers — absorptive capacity (the mending 繕い)\n")
    L.append("| rank | node | resilience-buffer |")
    L.append("|---:|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["resilience"], nodes, 12), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n---\n_hokorobi 綻び · ADR-2606073400 · mirror-only · observation-only · "
             "non-adjudicating · never-trades · edge-primary · resilience-routed. Live ingest "
             "(FSB/IAIS/regulator) is G7/Council-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-finrisk-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "systemic-risk-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"hokorobi: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'systemic-risk-report.md'}")
    top = _rank(res["systemic"], nodes, 1)
    if top:
        print(f"  top systemic-risk concentration: {top[0][1]} ({top[0][2]:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
