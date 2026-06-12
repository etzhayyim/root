#!/usr/bin/env python3
"""hinagata 雛形 — knowledge-graph query interface over the legal-template commons (ADR-2606111954).

Maturity / usability: the kotoba Datom EDN is a knowledge graph, not just a flat list — this
module exposes the practical drafter queries that prove it (the point of the kotoba Datalog
substrate). All queries are pure graph traversals over the loaded (nodes, edges); nothing is
stored, nothing mutates (N1).

  templates_in_jurisdiction(jx)      — templates governed by a jurisdiction
  statutes_grounding_template(tmpl)  — every public statute a template rests on (clause→statute)
  translations_of(tmpl)              — its other-language versions (:translates, both directions)
  conflicting_clauses(clause)        — clauses a drafter must not combine with it (:conflicts-with)
  jurisdictions_for_concept(concept) — where a legal concept is grounded in real law

Pure stdlib. Usage:
    python3 query.py templates-in jx.jp
    python3 query.py statutes-for tmpl.dpa-gdpr
    python3 query.py translations tmpl.nda-mutual
    python3 query.py conflicts cl.ip-assignment
    python3 query.py jurisdictions-for concept.data-protection
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, CITE_KINDS  # noqa: E402


def _label(nodes, nid):
    return nodes.get(nid, {}).get(":lt/label", nid)


def templates_in_jurisdiction(nodes, edges, jx):
    return sorted({e[":en/from"] for e in edges
                   if e.get(":en/kind") == ":governed-by" and e[":en/to"] == jx
                   and nodes.get(e[":en/from"], {}).get(":lt/kind") == ":template"})


def statutes_grounding_template(nodes, edges, tmpl):
    clauses = {e[":en/to"] for e in edges if e.get(":en/kind") == ":has-clause" and e[":en/from"] == tmpl}
    statutes = set()
    for e in edges:
        if e.get(":en/kind") in CITE_KINDS and e[":en/from"] in clauses:
            statutes.add(e[":en/to"])
    return sorted(statutes)


def translations_of(nodes, edges, tmpl):
    out = set()
    for e in edges:
        if e.get(":en/kind") == ":translates":
            if e[":en/from"] == tmpl:
                out.add(e[":en/to"])
            elif e[":en/to"] == tmpl:
                out.add(e[":en/from"])
    # siblings: other translations of the same original
    originals = {e[":en/to"] for e in edges if e.get(":en/kind") == ":translates" and e[":en/from"] == tmpl}
    for orig in originals:
        for e in edges:
            if e.get(":en/kind") == ":translates" and e[":en/to"] == orig and e[":en/from"] != tmpl:
                out.add(e[":en/from"])
    return sorted(out)


def conflicting_clauses(nodes, edges, clause):
    out = set()
    for e in edges:
        if e.get(":en/kind") == ":conflicts-with":
            if e[":en/from"] == clause:
                out.add(e[":en/to"])
            elif e[":en/to"] == clause:
                out.add(e[":en/from"])
    return sorted(out)


def jurisdictions_for_concept(nodes, edges, concept):
    # clauses that instantiate the concept → statutes they cite → those statutes' jurisdictions
    clauses = {e[":en/from"] for e in edges if e.get(":en/kind") == ":instantiates" and e[":en/to"] == concept}
    jx = set()
    for e in edges:
        if e.get(":en/kind") in CITE_KINDS and e[":en/from"] in clauses:
            j = nodes.get(e[":en/to"], {}).get(":statute/jurisdiction")
            if j:
                jx.add(j)
    return sorted(jx)


# major national jurisdictions used as the gap-analysis denominator (exclude treaty/doctrinal ids)
MAJOR_JURISDICTIONS = ["jx.jp", "jx.us", "jx.eu", "jx.uk", "jx.de", "jx.fr", "jx.in", "jx.cn",
                       "jx.kr", "jx.br", "jx.au", "jx.ca", "jx.es", "jx.sg", "jx.mx", "jx.id",
                       "jx.ng", "jx.ae", "jx.it", "jx.ch", "jx.za", "jx.israel"]


def coverage_gaps(nodes, edges, concept):
    """Major national jurisdictions that do NOT yet ground a concept — a self-documenting worklist.

    Turns the EDN into its own coverage roadmap: the inverse of jurisdictions_for_concept over the
    MAJOR_JURISDICTIONS denominator (treaty / religious / customary ids are not counted as gaps)."""
    have = set(jurisdictions_for_concept(nodes, edges, concept))
    present = [j for j in MAJOR_JURISDICTIONS if j in nodes]
    return sorted(j for j in present if j not in have)


_COMMANDS = {
    "templates-in": ("templates_in_jurisdiction", "templates governed by"),
    "statutes-for": ("statutes_grounding_template", "statutes grounding"),
    "translations": ("translations_of", "translations of"),
    "conflicts": ("conflicting_clauses", "clauses conflicting with"),
    "jurisdictions-for": ("jurisdictions_for_concept", "jurisdictions grounding"),
    "gaps": ("coverage_gaps", "major jurisdictions still lacking grounding for"),
}


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    nodes, edges = load(here / "data" / "seed-legal-template-graph.kotoba.edn")
    if len(argv) < 3 or argv[1] not in _COMMANDS:
        print("usage: query.py <" + "|".join(_COMMANDS) + "> <id>", file=sys.stderr)
        return 2
    fn_name, verb = _COMMANDS[argv[1]]
    res = globals()[fn_name](nodes, edges, argv[2])
    print(f"{verb} {argv[2]} ({_label(nodes, argv[2])}):")
    for nid in res:
        print(f"  {nid}  —  {_label(nodes, nid)}")
    print(f"  [{len(res)} result(s)]")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
