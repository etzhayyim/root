#!/usr/bin/env python3
"""kadode 門出 — edge-primary resignation-route analyzer over the labour-exit graph.

ADR-2606112238. Reads a kotoba-EDN labour-exit graph (:lx/* nodes + :en/* 縁), and surfaces,
per worker SCENARIO: the lawful escalation ROUTE (self → messenger → union → lawyer), the
labour-law GROUNDS that support the exit, and how well each employer RISK pattern is answered
by a legal ground — routed to a DIGNIFIED EXIT, never to a litigation promise.

CONSTITUTIONAL (read before any change):
  G1 — 使者 not 代理人. kadode RELAYS a worker's already-formed unilateral resignation and
    DRAFTS their documents; it NEVER negotiates (弁護士法72条). The analyzer ENFORCES this: a
    scenario whose goal needs negotiation (:scenario/needs-negotiation true) is NEVER given a
    non-negotiating primary route (:worker-self / :kadode-messenger) — it escalates to
    :labor-union (団体交渉) or :lawyer. recommend_route() raises if the graph violates this.
  N1 / G2 — edge-primary. route fit / ground support live ONLY on :en/weight edges, integrated
    on READ; no stored per-scenario score. The resignation is the WORKER'S own act.
  N3 / G3 — non-adjudicating. grounds/citations are DISCLOSED legal facts, never kadode
    verdicts; kadode never promises an outcome.

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


# routes that may NEGOTIATE (the single load-bearing boundary; mirrors schema)
NEGOTIATING_ACTORS = {":labor-union", ":lawyer"}


def load(path: pathlib.Path):
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":lx/id" in f:
            nodes[f[":lx/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def recommend_route(scenario_id: str, nodes: dict, edges: list) -> dict:
    """The lawful recommended route for a scenario (edge-primary, UPL-enforced).

    Picks the highest-weight :requires-route edge, BUT if the scenario needs negotiation the
    recommendation is constrained to a negotiating actor (union/lawyer) — kadode never relays a
    matter that requires negotiation (G1 / 弁護士法72条). Raises on a graph that violates this.
    """
    sc = nodes.get(scenario_id, {})
    needs_neg = bool(sc.get(":scenario/needs-negotiation"))
    cands = []
    for e in edges:
        if e.get(":en/kind") == ":requires-route" and e.get(":en/from") == scenario_id:
            route = nodes.get(e.get(":en/to"), {})
            actor = route.get(":route/actor")
            can_neg = actor in NEGOTIATING_ACTORS
            cands.append((float(e.get(":en/weight", 0.0) or 0.0), e.get(":en/to"), actor, can_neg))
    if not cands:
        return {"scenario": scenario_id, "route": None, "needs_negotiation": needs_neg,
                "candidates": []}
    # UPL enforcement: a negotiation-needing scenario MUST resolve to a negotiating route
    eligible = [c for c in cands if (c[3] or not needs_neg)]
    if needs_neg and not any(c[3] for c in cands):
        raise AssertionError(
            f"UPL violation in graph: scenario {scenario_id} needs negotiation but has no "
            f"union/lawyer route — a 使者/self route must never be the answer (G1)")
    pick = max(eligible or cands, key=lambda c: c[0])
    return {"scenario": scenario_id, "route": pick[1], "route_actor": pick[2],
            "needs_negotiation": needs_neg, "can_negotiate": pick[3],
            "candidates": sorted([(c[1], c[2], c[0]) for c in cands], key=lambda x: -x[2])}


def analyze(nodes: dict, edges: list):
    """Edge-primary integrals (computed on read; transient — N1/G2)."""
    ground_support = defaultdict(float)   # scenario → Σ supported-by weight
    risk_coverage = defaultdict(float)    # risk → Σ inbound counters weight
    route_use = defaultdict(float)        # route → Σ inbound requires-route weight

    for e in edges:
        k = e.get(":en/kind")
        w = float(e.get(":en/weight", 0.0) or 0.0)
        if k == ":supported-by":
            ground_support[e.get(":en/from")] += w
        elif k == ":counters":
            risk_coverage[e.get(":en/to")] += w
        elif k == ":requires-route":
            route_use[e.get(":en/to")] += w

    scenarios = [nid for nid in nodes if nodes[nid].get(":lx/kind") == ":scenario"]
    routes = {s: recommend_route(s, nodes, edges) for s in scenarios}
    return {"ground_support": dict(ground_support), "risk_coverage": dict(risk_coverage),
            "route_use": dict(route_use), "routes": routes}


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n = lambda k: sum(1 for x in nodes.values() if x.get(":lx/kind") == k)
    L = []
    L.append("# kadode 門出 — labour-exit (退職代行) route report\n")
    L.append("> **G1 — kadode is a 使者 (messenger) + concierge, NEVER a 代理人 (agent) and "
             "NEVER the practice of law.** It relays a worker's already-formed unilateral "
             "resignation (民法627 = a unilateral right; the employer's consent is not required) "
             "and drafts the worker's own documents. It does NOT negotiate (弁護士法72条) — any "
             "matter needing negotiation is routed to a labour union (団体交渉) or a lawyer. "
             "Statute citations are DISCLOSED facts (N3), never a kadode verdict or outcome "
             "promise. Free, worker-authored, worker-submitted.\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n(':scenario')} scenarios · {n(':ground')} "
             f"grounds · {n(':document')} documents · {n(':route')} routes · {n(':risk')} "
             f"employer-risk patterns) · {len(edges)} 縁\n")

    L.append("\n## Recommended lawful route per scenario (UPL-bounded)\n")
    L.append("_Negotiation-needing situations escalate to union/lawyer; kadode relays only "
             "non-negotiating unilateral exits (G1)._\n")
    L.append("| scenario | needs negotiation | route | actor | may negotiate? |")
    L.append("|---|:--:|---|---|:--:|")
    for sid in sorted(res["routes"]):
        r = res["routes"][sid]
        label = nodes.get(sid, {}).get(":lx/label", sid)
        route_label = nodes.get(r["route"], {}).get(":lx/label", r["route"]) if r["route"] else "—"
        L.append(f"| {label} | {'はい' if r['needs_negotiation'] else 'いいえ'} | {route_label} | "
                 f"{str(r.get('route_actor', '—')).lstrip(':')} | "
                 f"{'○' if r.get('can_negotiate') else '×'} |")

    L.append("\n## Ground support per scenario (how well-grounded the exit is in labour law)\n")
    L.append("| scenario | Σ ground support |")
    L.append("|---|---:|")
    for sid, v in sorted(res["ground_support"].items(), key=lambda kv: -kv[1]):
        L.append(f"| {nodes.get(sid, {}).get(':lx/label', sid)} | {v:.2f} |")

    L.append("\n## Employer-risk coverage (how strongly each 引き止め pattern is answered)\n")
    L.append("| employer risk | countering ground strength |")
    L.append("|---|---:|")
    for rid, v in sorted(res["risk_coverage"].items(), key=lambda kv: -kv[1]):
        rn = nodes.get(rid, {})
        L.append(f"| {rn.get(':risk/pattern', rid)} — {rn.get(':lx/label', '')} | {v:.2f} |")

    L.append("\n---\n_kadode 門出 · ADR-2606112238 · 使者-not-agent · non-adjudicating · "
             "edge-primary · dignified-exit-routed. Live relay/sending is G7-gated; worker "
             "self-submits by default._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-resignation-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "route-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"kadode: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'route-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
