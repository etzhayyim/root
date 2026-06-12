#!/usr/bin/env python3
"""hinagata 雛形 — legal-template-commons integrity validator (ADR-2606111954).

Maturity tooling: checks the kotoba-EDN graph's internal integrity beyond what the analyzer
needs to run — referential integrity, statute grounding, template completeness, clause usage,
and translation consistency. ERRORS are structural defects that must be fixed; WARNINGS are
honestly-surfaced soft issues (e.g. a registered-but-unused statute) that are allowed but
worth seeing (G5 sourcing honesty).

Pure stdlib. Usage:
    python3 validate.py [seed.edn]        # prints report, exit 1 on any ERROR
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

SIGN_CLAUSE = "cl.signature-esign"


def validate(nodes: dict, edges: list):
    """Return (errors, warnings) — each a list of strings."""
    errors, warnings = [], []
    by_kind = {}
    for nid, n in nodes.items():
        by_kind.setdefault(n.get(":lt/kind"), set()).add(nid)
    templates = by_kind.get(":template", set())
    clauses = by_kind.get(":clause", set())
    statutes = by_kind.get(":statute", set())
    jurisdictions = by_kind.get(":jurisdiction", set())
    concepts = by_kind.get(":concept", set())

    def E(m): errors.append(m)
    def W(m): warnings.append(m)

    # 1. referential integrity — no dangling 縁
    for e in edges:
        if e[":en/from"] not in nodes:
            E(f"dangling :en/from {e[':en/from']} ({e.get(':en/kind')})")
        if e[":en/to"] not in nodes:
            E(f"dangling :en/to {e[':en/to']} ({e.get(':en/kind')})")

    # 2. statute → jurisdiction referential integrity
    for sid in statutes:
        jx = nodes[sid].get(":statute/jurisdiction")
        if jx and jx not in jurisdictions:
            E(f"statute {sid} :statute/jurisdiction {jx} is not a jurisdiction node")
        if not nodes[sid].get(":statute/url", "").startswith("http"):
            E(f"statute {sid} has no public :statute/url")

    # 3. edge-target kind sanity
    cite_kinds = {":cites-statute", ":mandated-by"}
    for e in edges:
        k = e.get(":en/kind")
        to_kind = nodes.get(e[":en/to"], {}).get(":lt/kind")
        if k in cite_kinds and to_kind != ":statute":
            E(f"{k} target {e[':en/to']} is {to_kind}, expected :statute")
        if k == ":instantiates" and to_kind != ":concept":
            E(f":instantiates target {e[':en/to']} is {to_kind}, expected :concept")
        if k in (":governed-by", ":applies-in") and to_kind != ":jurisdiction":
            E(f"{k} target {e[':en/to']} is {to_kind}, expected :jurisdiction")
        if k == ":translates" and to_kind != ":template":
            E(f":translates target {e[':en/to']} is {to_kind}, expected :template")
        from_kind = nodes.get(e[":en/from"], {}).get(":lt/kind")
        if k == ":conflicts-with" and not (from_kind == ":clause" and to_kind == ":clause"):
            E(f":conflicts-with must be clause↔clause, got {from_kind}→{to_kind} ({e[':en/from']})")
        if k == ":derived-from" and not (from_kind == ":template" and to_kind == ":template"):
            E(f":derived-from must be template→template, got {from_kind}→{to_kind} ({e[':en/from']})")
        if k == ":supersedes" and not (from_kind == ":template" and to_kind == ":template"):
            E(f":supersedes must be template→template, got {from_kind}→{to_kind} ({e[':en/from']})")
        if k == ":conflicts-with" and e[":en/from"] == e[":en/to"]:
            E(f":conflicts-with self-loop on {e[':en/from']}")

    # 4. template completeness — clauses, a governing jurisdiction, a signature clause
    has_clause = {}
    for e in edges:
        if e.get(":en/kind") == ":has-clause":
            has_clause.setdefault(e[":en/from"], set()).add(e[":en/to"])
    governed = {e[":en/from"] for e in edges if e.get(":en/kind") == ":governed-by"}
    for tid in templates:
        cls = has_clause.get(tid, set())
        if not cls:
            E(f"template {tid} has no clauses")
        if tid not in governed:
            E(f"template {tid} has no :governed-by jurisdiction")
        if SIGN_CLAUSE not in cls:
            W(f"template {tid} has no signature clause ({SIGN_CLAUSE})")

    # 5. clause usage — every clause used by ≥1 template and instantiating ≥1 concept
    used_clauses = set().union(*has_clause.values()) if has_clause else set()
    instantiated = {e[":en/from"] for e in edges if e.get(":en/kind") == ":instantiates"}
    for cid in clauses:
        if cid not in used_clauses:
            W(f"clause {cid} is not used by any template")
        if cid not in instantiated and cid != "cl.definitions":
            W(f"clause {cid} does not :instantiate any concept")

    # 6. statute grounding — every statute cited by ≥1 clause/template (else registry-only)
    cited = {e[":en/to"] for e in edges if e.get(":en/kind") in cite_kinds}
    for sid in statutes:
        if sid not in cited:
            W(f"statute {sid} is registered but not cited by any clause (registry-only)")

    # 7. translation consistency — a translation's clause-concepts ⊆ its original's
    def concepts_of(tid):
        cs = set()
        for cl in has_clause.get(tid, set()):
            for e in edges:
                if e.get(":en/kind") == ":instantiates" and e[":en/from"] == cl:
                    cs.add(e[":en/to"])
        return cs
    for e in edges:
        if e.get(":en/kind") == ":translates":
            tr, orig = e[":en/from"], e[":en/to"]
            extra = concepts_of(tr) - concepts_of(orig)
            if extra:
                W(f"translation {tr} introduces concepts not in original {orig}: {sorted(extra)}")

    # 8. concept usage — every concept instantiated by ≥1 clause
    used_concepts = {e[":en/to"] for e in edges if e.get(":en/kind") == ":instantiates"}
    for cid in concepts:
        if cid not in used_concepts:
            W(f"concept {cid} is not instantiated by any clause")

    return errors, warnings


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-legal-template-graph.kotoba.edn"
    nodes, edges = load(seed)
    errors, warnings = validate(nodes, edges)
    print(f"hinagata validate: {len(nodes)} nodes, {len(edges)} 縁 — "
          f"{len(errors)} errors, {len(warnings)} warnings")
    for m in errors:
        print(f"  ERROR  {m}")
    for m in warnings:
        print(f"  warn   {m}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
