#!/usr/bin/env python3
"""tanemaki 種蒔き — edge-primary Public-Fund DD analyzer over the fund-stewardship graph.

ADR-2606122000. Reads a kotoba-EDN stewardship graph (:fs/* nodes + :en/* 縁) and surfaces, per
candidate ORG: the hard SCREEN findings (charter eligibility), the weighted CRITERION fit
(the disclosed rubric, weights public + Σ=1.0), evidence coverage, and the ROUTE —
:excluded | :insufficient-evidence | :propose — routed to a PUBLIC, ADVISORY scorecard,
never to a funding decision.

CONSTITUTIONAL (read before any change):
  G1 — steward not sovereign. tanemaki EVALUATES + DRAFTS; it NEVER decides. Every grant is
    decided by 1 SBT = 1 vote (GrantGovernor, ADR-2605192145). The analyzer ENFORCES the
    structural half: an org with ANY :conflicts screen finding can NEVER route to :propose —
    recommend_route() raises if the computation would. There is no :fund route at all.
  G2 — no investment instrument. The fund GIVES (grant/milestone-escrow/in-kind); equity/debt/
    ROI vocabulary is unrepresentable (see propose.assert_instrument, mirrors fuchi G1).
  N1 / G4 — edge-primary + public. DD-fit lives ONLY on :meets edges, integrated on READ;
    no stored per-org score. Criteria weights are disclosed and must sum to 1.0 (raises if not).
  N3 / G3 — non-adjudicating. A screen finding / evidence weight is a DISCLOSED public fact
    with a named source, never a verdict on an org's worth.
  G5 — evidence honesty. Coverage below the disclosed floor, or any screen :undetermined /
    unevaluated, routes to :insufficient-evidence — tanemaki never proposes on thin DD.

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


# disclosed constants (the honesty floor + route enum; mirror the schema)
COVERAGE_FLOOR = 0.6        # fraction of criteria needing ≥1 evidence edge before :propose
ROUTES = (":excluded", ":insufficient-evidence", ":propose")  # NO :fund — funding is a VOTE


def load(path: pathlib.Path):
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":fs/id" in f:
            nodes[f[":fs/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def criteria(nodes: dict) -> dict:
    """The disclosed rubric. Raises unless the public weights sum to 1.0 (rubric integrity)."""
    crit = {nid: n for nid, n in nodes.items() if n.get(":fs/kind") == ":criterion"}
    total = sum(float(n.get(":criterion/weight", 0.0) or 0.0) for n in crit.values())
    if abs(total - 1.0) > 1e-9:
        raise AssertionError(
            f"rubric integrity violation: disclosed criterion weights sum to {total}, not 1.0 — "
            f"a non-normalized rubric is a hidden re-weighting (G4)")
    return crit


def screen_findings(org_id: str, nodes: dict, edges: list) -> dict:
    """Per-screen DISCLOSED conformance findings for an org (missing screens reported)."""
    screens = sorted(nid for nid, n in nodes.items() if n.get(":fs/kind") == ":screen")
    findings = {}
    for e in edges:
        if e.get(":en/kind") == ":screened" and e.get(":en/from") == org_id:
            findings[e[":en/to"]] = e.get(":en/finding")
    return {s: findings.get(s) for s in screens}  # None = unevaluated


def dd_fit(org_id: str, nodes: dict, edges: list, crit: dict):
    """Edge-primary fit: Σ weight_c × min(1, Σ incident :meets weight) — computed on READ (N1)."""
    per = defaultdict(float)
    evidence = defaultdict(list)
    for e in edges:
        if e.get(":en/kind") == ":meets" and e.get(":en/from") == org_id and e.get(":en/to") in crit:
            per[e[":en/to"]] += float(e.get(":en/weight", 0.0) or 0.0)
            evidence[e[":en/to"]].append(e.get(":en/evidence"))
    fit = sum(float(crit[c].get(":criterion/weight", 0.0)) * min(1.0, per[c]) for c in per)
    coverage = len(per) / len(crit) if crit else 0.0
    return fit, coverage, dict(per), dict(evidence)


def recommend_route(org_id: str, nodes: dict, edges: list) -> dict:
    """The lawful route for a candidate org (edge-primary, G1/G5-enforced).

    :excluded             — ANY screen finding is :conflicts (charter screens are structural)
    :insufficient-evidence — any screen :undetermined/unevaluated, OR coverage < floor
    :propose              — draft an ADVISORY proposal for the 1-SBT-1-vote decision
    Raises if a screen-conflicting org would route to :propose (G1 tripwire) — funding is
    NEVER a route tanemaki can emit.
    """
    org = nodes.get(org_id, {})
    if org.get(":fs/kind") != ":org":
        raise KeyError(f"not an org: {org_id}")
    crit = criteria(nodes)
    findings = screen_findings(org_id, nodes, edges)
    fit, coverage, per, evidence = dd_fit(org_id, nodes, edges, crit)
    conflicts = sorted(s for s, f in findings.items() if f == ":conflicts")
    undetermined = sorted(s for s, f in findings.items() if f in (":undetermined", None))

    if conflicts:
        route = ":excluded"
    elif undetermined or coverage < COVERAGE_FLOOR:
        route = ":insufficient-evidence"
    else:
        route = ":propose"

    # G1 tripwire — structural, test-covered: a conflicted org must never be proposable
    if route == ":propose" and conflicts:
        raise AssertionError(
            f"G1 VIOLATION: org {org_id} has screen conflicts {conflicts} but routed to "
            f":propose — charter screens are structural, not advisory")
    assert route in ROUTES  # no :fund route exists; funding is the members' vote

    return {"org": org_id, "synthetic": bool(org.get(":org/synthetic")), "route": route,
            "screen_findings": findings, "conflicts": conflicts, "undetermined": undetermined,
            "dd_fit": round(fit, 6), "evidence_coverage": round(coverage, 6),
            "per_criterion": per, "evidence": evidence}


def analyze(nodes: dict, edges: list):
    """All orgs through screens + rubric (transient readouts — N1/G4)."""
    orgs = sorted(nid for nid, n in nodes.items() if n.get(":fs/kind") == ":org")
    return {"orgs": {o: recommend_route(o, nodes, edges) for o in orgs},
            "criteria": {c: float(n.get(":criterion/weight", 0.0))
                         for c, n in criteria(nodes).items()}}


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n = lambda k: sum(1 for x in nodes.values() if x.get(":fs/kind") == k)
    L = []
    L.append("# tanemaki 種蒔き — Public Fund stewardship (DD) report\n")
    L.append("> **G1 — tanemaki is a STEWARD, never a sovereign.** This scorecard is a 参考意見 "
             "(advisory): every grant is DECIDED by 1 SBT = 1 vote on the GrantGovernor "
             "(ADR-2605192145) behind a timelock. **G2 — the Public Fund GIVES, never INVESTS**: "
             "instruments are grant / milestone-escrow / in-kind only; equity, ROI and every "
             "investment-return shape are unrepresentable. Screen findings and evidence weights "
             "are DISCLOSED public facts with named sources (N3), never verdicts on an "
             "organization's worth. **All orgs in this report are FICTIONAL (G6)** — evaluating "
             "a real org is a G7-gated live leg from primary disclosure only.\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n(':org')} orgs · {n(':screen')} screens · "
             f"{n(':criterion')} criteria · {n(':source')} sources · {n(':instrument')} "
             f"instruments · {n(':milestone')} milestones) · {len(edges)} 縁\n")

    L.append("\n## The disclosed rubric (public weights, Σ = 1.0)\n")
    L.append("| criterion | weight |")
    L.append("|---|---:|")
    for c, w in sorted(res["criteria"].items(), key=lambda kv: -kv[1]):
        L.append(f"| {nodes.get(c, {}).get(':fs/label', c)} | {w:.2f} |")

    L.append("\n## Route per candidate org (screens fire BEFORE weighting)\n")
    L.append("| org | screens | DD fit | evidence coverage | route |")
    L.append("|---|---|---:|---:|---|")
    for oid in sorted(res["orgs"]):
        r = res["orgs"][oid]
        label = nodes.get(oid, {}).get(":fs/label", oid)
        if r["conflicts"]:
            scr = "✗ conflicts: " + ", ".join(
                nodes.get(s, {}).get(":screen/code", s) for s in r["conflicts"])
        elif r["undetermined"]:
            scr = "△ undetermined: " + ", ".join(
                nodes.get(s, {}).get(":screen/code", s) for s in r["undetermined"])
        else:
            scr = "○ all conform"
        L.append(f"| {label} | {scr} | {r['dd_fit']:.3f} | {r['evidence_coverage']:.0%} | "
                 f"{r['route'].lstrip(':')} |")

    L.append("\n---\n_tanemaki 種蒔き · ADR-2606122000 · steward-not-sovereign · "
             "non-adjudicating · edge-primary · vote-decided (1 SBT = 1 vote). Submitting a "
             "proposal on-chain and evaluating real orgs are G7-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-stewardship-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "dd-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"tanemaki: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'dd-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
