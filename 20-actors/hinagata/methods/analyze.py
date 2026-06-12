#!/usr/bin/env python3
"""hinagata 雛形 — edge-primary statutory-groundedness analyzer over the legal-template commons.

ADR-2606111954. Reads a kotoba-EDN legal-template graph (:lt/* nodes + :en/* 縁 over the
legal-template-ontology), and surfaces — aggregate-first — where integrated STATUTORY
GROUNDING accumulates over a TEMPLATE (how well-anchored in actual public law it is), routed
to PUBLIC RELEASE (free use); which CLAUSES are the most-reused backbone; and which public
STATUTES the commons most rests on.

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. statutory grounding lives ONLY on edges (:en/binding-load weighted
    by the DISCLOSED clause :clause/optionality). A template's groundedness is the INTEGRAL of
    its incident clause :cites-statute / :mandated-by + direct :cites-statute 縁 — computed on
    READ, never a stored per-template score. There is no :lt/score-of-template.
  G1 — COMMONS, never the practice of law. No advice, no opinion on a matter, no representation,
    no enforceability certification. The unit is ALWAYS a template / clause / statute-link.
    A statute citation is a DISCLOSED STRUCTURAL FACT, never a hinagata verdict.
  N3 — non-adjudicating. citations, instrument names, optionality categories are DISCLOSED
    facts sourced from the public instrument or its official guidance, never hinagata verdicts.

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


# ── disclosed clause optionality → grounding weight (NOT a verdict; mirrors schema)
OPTIONALITY_WEIGHT = {":mandatory": 1.0, ":recommended": 0.6, ":optional": 0.3}

CITE_KINDS = {":cites-statute", ":mandated-by"}   # clause/template → statute (statutory anchor)
HAS_CLAUSE_KINDS = {":has-clause"}                 # template → clause (composition / provenance)
INSTANTIATE_KINDS = {":instantiates"}             # clause → concept
GOVERN_KINDS = {":governed-by", ":applies-in"}    # template/statute → jurisdiction
TRANSLATE_KINDS = {":translates", ":supersedes", ":derived-from", ":conflicts-with"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a legal-template-commons EDN graph."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":lt/id" in f:
            nodes[f[":lt/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def analyze(nodes: dict, edges: list):
    """Edge-primary integrals (computed on read; transient — N1/G2).

    groundedness[template] = Σ over (clause c attached via :has-clause) of Σ (c's outbound
                             :cites-statute/:mandated-by binding-load × optionality-weight(c)),
                             PLUS Σ direct template→statute :cites-statute. How well-anchored in
                             actual public law — the publish-readiness surface.
    reusability[clause]    = Σ inbound :has-clause binding-load (the shared backbone).
    statute_pull[statute]  = Σ inbound :cites-statute/:mandated-by binding-load (load-bearing law).
    juris_reach[node]      = Σ incident :governed-by/:applies-in (jurisdictional span).
    """
    # clause → its parent templates (from :has-clause), and per-clause optionality weight
    clause_templates = defaultdict(list)
    for e in edges:
        if e.get(":en/kind") in HAS_CLAUSE_KINDS:
            clause_templates[e.get(":en/to")].append(e.get(":en/from"))

    def opt_weight(clause_id: str) -> float:
        return OPTIONALITY_WEIGHT.get(nodes.get(clause_id, {}).get(":clause/optionality"), 0.6)

    grounded = defaultdict(float)
    reuse = defaultdict(float)
    statute_pull = defaultdict(float)
    juris_reach = defaultdict(float)
    concept_reach = defaultdict(float)

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/binding-load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in CITE_KINDS:
            statute_pull[dst] += load_
            src_kind = nodes.get(src, {}).get(":lt/kind")
            if src_kind == ":clause":
                w = opt_weight(src)
                # attribute the clause's statutory anchor up to every template that uses it
                for tmpl in clause_templates.get(src, []):
                    grounded[tmpl] += load_ * w
            elif src_kind == ":template":
                grounded[src] += load_  # direct template citation
        elif kind in HAS_CLAUSE_KINDS:
            reuse[dst] += load_
        elif kind in GOVERN_KINDS:
            juris_reach[src] += load_
        elif kind in INSTANTIATE_KINDS:
            concept_reach[dst] += load_

    return {
        "grounded": dict(grounded),
        "reuse": dict(reuse),
        "statute_pull": dict(statute_pull),
        "juris_reach": dict(juris_reach),
        "concept_reach": dict(concept_reach),
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [(nid, nodes.get(nid, {}).get(":lt/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_tmpl = sum(1 for n in nodes.values() if n.get(":lt/kind") == ":template")
    n_clause = sum(1 for n in nodes.values() if n.get(":lt/kind") == ":clause")
    n_statute = sum(1 for n in nodes.values() if n.get(":lt/kind") == ":statute")
    n_jx = sum(1 for n in nodes.values() if n.get(":lt/kind") == ":jurisdiction")
    n_concept = sum(1 for n in nodes.values() if n.get(":lt/kind") == ":concept")
    auth = sum(1 for n in nodes.values() if n.get(":lt/sourcing") == ":authoritative")

    L = []
    L.append("# hinagata 雛形 — legal-template-commons groundedness report (aggregate-first)\n")
    L.append("> **G1 — a COMMONS of fair, openly-licensed templates ANYONE may use, NEVER the "
             "practice of law.** No advice, no opinion on a matter, no enforceability "
             "certification. A clause's statute citation is a DISCLOSED structural fact (N3), "
             "not a hinagata verdict. Statutory grounding lives only on edges, integrated on "
             "read (N1). Templates are Apache-2.0 + Charter Rider; anyone may copy + adapt.\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_tmpl} templates · {n_clause} clauses · "
             f"{n_statute} statutes · {n_jx} jurisdictions · {n_concept} concepts) · "
             f"{len(edges)} 縁 · {auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Template statutory-groundedness — templates best anchored in actual public law\n")
    L.append("_Σ incident clause :cites-statute/:mandated-by + direct citation load × disclosed "
             "optionality weight; routed to PUBLIC RELEASE (free use), never to advice._\n")
    L.append("| rank | template | lang | license | stance | groundedness |")
    L.append("|---:|---|:--:|:--:|:--:|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["grounded"], nodes), 1):
        n = nodes.get(nid, {})
        lang = n.get(":template/lang", "—") or "—"
        lic = n.get(":template/license", "—") or "—"
        stance = str(n.get(":template/stance", "—") or "—").lstrip(":")
        L.append(f"| {i} | {label} | {lang} | {lic} | {stance} | {v:.3f} |")

    L.append("\n## Clause reusability — the shared backbone across the commons\n")
    L.append("_Σ inbound :has-clause load; how many templates reuse the clause._\n")
    L.append("| rank | clause | role | optionality | reusability |")
    L.append("|---:|---|:--:|:--:|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["reuse"], nodes, 12), 1):
        n = nodes.get(nid, {})
        role = str(n.get(":clause/role", "—") or "—").lstrip(":")
        opt = str(n.get(":clause/optionality", "—") or "—").lstrip(":")
        L.append(f"| {i} | {label} | {role} | {opt} | {v:.3f} |")

    L.append("\n## Statute pull — the public laws the commons most rests on\n")
    L.append("_Σ inbound :cites-statute/:mandated-by load. DISCLOSED citations only (N3)._\n")
    L.append("| rank | statute | citation | instrument | pull |")
    L.append("|---:|---|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["statute_pull"], nodes, 12), 1):
        n = nodes.get(nid, {})
        cite = n.get(":statute/citation", "—") or "—"
        inst = n.get(":statute/instrument", "—") or "—"
        L.append(f"| {i} | {label} | {cite} | {inst} | {v:.3f} |")

    L.append("\n## Jurisdictional reach — templates spanning the most jurisdictions\n")
    L.append("| rank | template | jurisdiction-reach |")
    L.append("|---:|---|---:|")
    tmpl_reach = {k: v for k, v in res["juris_reach"].items()
                  if nodes.get(k, {}).get(":lt/kind") == ":template"}
    for i, (nid, label, v) in enumerate(_rank(tmpl_reach, nodes, 8), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n---\n_hinagata 雛形 · ADR-2606111954 · commons-not-counsel · non-adjudicating · "
             "edge-primary · public-release-routed. Live legal-corpus binding "
             "(ADR-2605262800) + Council review is G7-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-legal-template-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "groundedness-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"hinagata: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'groundedness-report.md'}")
    top = _rank(res["grounded"], nodes, 1)
    if top:
        print(f"  top groundedness template: {top[0][1]} ({top[0][2]:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
