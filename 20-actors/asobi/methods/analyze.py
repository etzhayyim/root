#!/usr/bin/env python3
"""asobi 遊び — edge-primary participation/enclosure analyzer over the freed-time graph.

ADR-2606073200. Reads a kotoba-EDN play/expression graph (:organism/* nodes + :en/* 縁 over
the asobi-ontology) and surfaces — aggregate-first — where PARTICIPATION is open (the access
surface to widen) and where ENCLOSURE gates the freed-time telos (paywall / attention-platform
/ lock), routed to OPENING.

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. karma lives ONLY on edges (:en/access-load). A node's
    participation-openness is the INTEGRAL of its incident OPENING 縁 — computed on READ,
    never a stored per-work score. There is no :asobi/popularity-of-work.
  G1 — PARTICIPATION / ACCESS map, never an engagement / attention / popularity ranking.
    No retention metric, no recommend-for-time-on-platform. The 取-holder is the ENCLOSURE;
    the bearer is the play; the routing is OPENING.
  N3 — non-adjudicating. Access categories (:public-domain … :proprietary) are DISCLOSED
    facts, never asobi verdicts.

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


# ── disclosed access category → representative openness weight (NOT a verdict; mirrors schema)
ACCESS_WEIGHT = {":public-domain": 1.0, ":open-license": 0.9, ":free-gratis": 0.7,
                 ":ticketed": 0.4, ":paywalled": 0.2, ":proprietary": 0.1}

OPENING_KINDS = {":open-access", ":teaches", ":participates", ":hosts", ":performs"}
ENCLOSURE_KINDS = {":encloses"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from an asobi EDN graph."""
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

    openness[node]        = Σ incident inbound OPENING load × disclosed access weight of bearer
    enclosure[node]       = Σ incident inbound :encloses load (the 取 borne; routed to opening)
    enclosure_out[holder] = Σ outbound :encloses load (the 取-holder gating play)
    """
    openness = defaultdict(float)
    enclosure = defaultdict(float)
    enclosure_out = defaultdict(float)

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/access-load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in OPENING_KINDS:
            bearer = nodes.get(dst, {})
            w = ACCESS_WEIGHT.get(bearer.get(":work/access"), 0.6)  # non-work bearer → neutral 0.6
            openness[dst] += load_ * w
        elif kind in ENCLOSURE_KINDS:
            enclosure[dst] += load_
            enclosure_out[src] += load_

    return {
        "openness": dict(openness),
        "enclosure": dict(enclosure),
        "enclosure_out": dict(enclosure_out),
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: -kv[1])[:limit]
    return [(nid, nodes.get(nid, {}).get(":organism/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_work = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":work")
    n_prac = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":practice")
    n_enc = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":enclosure")
    auth = sum(1 for n in nodes.values() if n.get(":organism/sourcing") == ":authoritative")

    L = []
    L.append("# asobi 遊び — freed-time participation report (aggregate-first)\n")
    L.append("> **G1 — PARTICIPATION / ACCESS map, NEVER an engagement ranking.** No retention "
             "metric, no recommend-for-time, no popularity score. The 取-holder is the "
             "ENCLOSURE; the bearer is the play; the routing is OPENING. Access categories are "
             "DISCLOSED, not asobi verdicts (N3). karma lives only on edges, on read (N1).\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_work} works · {n_prac} practices · "
             f"{n_enc} enclosures) · {len(edges)} 縁 · {auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Participation-openness — the freed-time access surface to widen\n")
    L.append("_Σ incident opening-load × disclosed access weight; the commons to keep open._\n")
    L.append("| rank | node | access | participation-openness |")
    L.append("|---:|---|:--:|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["openness"], nodes), 1):
        acc = nodes.get(nid, {}).get(":work/access", "—") or "—"
        L.append(f"| {i} | {label} | {acc.lstrip(':')} | {v:.3f} |")

    L.append("\n## Enclosure concentration — 取-holders gating the freed-time telos\n")
    L.append("_Σ outbound enclosure-load; cross-link to tsumugi/danjo where a power-entity "
             "operates the enclosure (accountability, aggregate-first). Routed to OPENING._\n")
    L.append("| rank | enclosure | kind | gating-load |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["enclosure_out"], nodes), 1):
        kind = nodes.get(nid, {}).get(":enclosure/kind", "—") or "—"
        L.append(f"| {i} | {label} | {kind.lstrip(':')} | {v:.3f} |")

    L.append("\n## Enclosed play — works/events bearing the most enclosure (open these)\n")
    L.append("| rank | node | enclosure-load |")
    L.append("|---:|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["enclosure"], nodes, 12), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n---\n_asobi 遊び · ADR-2606073200 · mirror-only · non-adjudicating · "
             "edge-primary · opening-routed · no-addictive-design. Live ingest is "
             "G7/Council-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-asobi-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "participation-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"asobi: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'participation-report.md'}")
    top = _rank(res["openness"], nodes, 1)
    if top:
        print(f"  top participation-openness: {top[0][1]} ({top[0][2]:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
