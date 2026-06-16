#!/usr/bin/env python3
"""aburi 炙り — edge-primary personal-tracking-exposure analyzer.

ADR-2606161630. Reads a kotoba-EDN tracker-exposure graph (:organism/* nodes + :en/* 縁 over the
tracker-exposure-ontology) and surfaces — for the MEMBER'S OWN surfaces — the answer to:
"when I accept the ToS / grant a permission on Google / Facebook / X / Apple, WHICH ad networks &
data brokers collect my data, and HOW MUCH does each one track me." It computes, on read:

  exposure[collector]   = Σ incident inbound :flows-to load × disclosed permission-sensitivity
                          weight — "how much this company tracks you" (THE headline; the 取-holder)
  relief[collector]     = Σ incident inbound :relieves load — exposure removed once a route is used
  net_exposure[col]     = exposure − relief  (what still tracks you after the opt-outs you have)
  surface_leak[surface] = Σ over :grants(surface→perm) load × permission_leak[perm] — "which
                          platform exposes you most" (Google / Facebook / X / Apple …)
  spread[datatype]      = Σ incident inbound :collects load — "what kinds of your data are most
                          widely harvested"
  route_cov[perm]       = Σ outbound :routes-to load (0 = no opt-out/DSAR route = reciprocity gap)
  unrouted_permissions  = permissions that LEAK (outbound :flows-to > 0) but have NO :routes-to —
                          the asymmetric-surveillance gap, routed to himotoki/kaiyaku/kurashimori/tedai

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. Exposure lives ONLY on edges (:en/load). A collector's tracking-load is
    the INTEGRAL of its incident inbound :flows-to 縁 — computed on READ, never a stored per-
    collector score. There is no :aburi/score-of-collector.
  G1 — OWN-DATA-ONLY. The lens maps the MEMBER'S OWN exposure (this public seed is REPRESENTATIVE
    / aggregate, no real person). NO record of any OTHER person; NO third-party PII; NO biometric;
    NO raw identifier values (the analyzer reads exposure STRUCTURE, never personal values).
  G3 / N3 — non-adjudicating. Collector catalogue membership + collector→data mappings + sensitivity
    bands are DISCLOSED facts (Exodus Privacy / IAB sellers.json / Apple App-Privacy / Play Data-
    safety), never aburi verdicts. Naming an SDK as an ad collector is a public catalogue fact.
  G4 — RECIPROCITY-RESTORING (§2(c) v3.1, ADR-2606082400). aburi makes the asymmetric ad-watcher
    VISIBLE TO THE WATCHED. It itself never tracks, never sells, builds no asymmetric dossier.

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


# ── disclosed permission/data sensitivity → representative weight (NOT a verdict; mirrors schema)
SENSITIVITY_WEIGHT = {":critical": 1.0, ":sensitive": 0.8, ":moderate": 0.5, ":low": 0.25}

GRANT_KINDS = {":grants"}
FLOW_KINDS = {":flows-to"}
COLLECT_KINDS = {":collects"}
ROUTE_KINDS = {":routes-to"}
RELIEVE_KINDS = {":relieves"}


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a tracker-exposure EDN graph."""
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
    """Edge-primary integrals (computed on read; transient — N1/G2). See module docstring."""
    exposure = defaultdict(float)        # collector  ← Σ inbound :flows-to × sensitivity weight
    permission_leak = defaultdict(float)  # permission ← Σ outbound :flows-to (raw)
    spread = defaultdict(float)          # datatype   ← Σ inbound :collects
    route_cov = defaultdict(float)       # permission ← Σ outbound :routes-to
    relief = defaultdict(float)          # collector  ← Σ inbound :relieves
    grants = []                          # (surface, permission, load) for the surface-leak pass

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in FLOW_KINDS:
            sens = nodes.get(src, {}).get(":permission/sensitivity")
            w = SENSITIVITY_WEIGHT.get(sens, 0.5)  # unknown sensitivity → neutral 0.5
            exposure[dst] += load_ * w
            permission_leak[src] += load_
        elif kind in COLLECT_KINDS:
            spread[dst] += load_
        elif kind in ROUTE_KINDS:
            route_cov[src] += load_
        elif kind in RELIEVE_KINDS:
            relief[dst] += load_
        elif kind in GRANT_KINDS:
            grants.append((src, dst, load_))

    # surface-leak = two-hop integral: how much each platform's granted permissions feed collectors
    surface_leak = defaultdict(float)
    for src, perm, load_ in grants:
        surface_leak[src] += load_ * permission_leak.get(perm, 0.0)

    # net exposure after the relief routes already exercised
    net_exposure = {}
    for cid, x in exposure.items():
        net_exposure[cid] = x - relief.get(cid, 0.0)

    # permissions that leak but have no opt-out / DSAR route = the reciprocity gap
    unrouted = sorted(
        nid for nid, n in nodes.items()
        if n.get(":organism/kind") == ":permission"
        and permission_leak.get(nid, 0.0) > 0 and route_cov.get(nid, 0.0) == 0.0
    )

    return {
        "exposure": dict(exposure),
        "relief": dict(relief),
        "net_exposure": net_exposure,
        "permission_leak": dict(permission_leak),
        "surface_leak": dict(surface_leak),
        "spread": dict(spread),
        "route_coverage": dict(route_cov),
        "unrouted_permissions": unrouted,
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: -kv[1])[:limit]
    return [(nid, nodes.get(nid, {}).get(":organism/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_surf = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":surface")
    n_perm = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":permission")
    n_col = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":collector")
    n_dt = sum(1 for n in nodes.values() if n.get(":organism/kind") == ":datatype")
    auth = sum(1 for n in nodes.values() if n.get(":organism/sourcing") == ":authoritative")

    L = []
    L.append("# aburi 炙り — personal-tracking-exposure report (own-data, reciprocity-restoring)\n")
    L.append("> **G1 — OWN-DATA-ONLY / G4 — RECIPROCITY-RESTORING.** This maps the member's OWN "
             "exposure (public seed is REPRESENTATIVE — no real person). No record of any other "
             "person, no third-party PII, no biometric, no raw identifier values. Collector "
             "catalogue membership + data mappings are DISCLOSED facts (Exodus Privacy / IAB "
             "sellers.json / Apple App-Privacy / Play Data-safety), NEVER an accusation (N3). "
             "aburi makes the asymmetric ad-watcher visible to the watched (§2(c) v3.1) — it never "
             "tracks, sells, or builds a dossier. Exposure lives only on edges, integrated on read (N1).\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_surf} surfaces · {n_perm} permissions · "
             f"{n_col} collectors · {n_dt} data-types) · {len(edges)} 縁 · "
             f"{auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Who tracks you most — ad networks & data brokers collecting your data\n")
    L.append("_Σ inbound :flows-to load × DISCLOSED permission-sensitivity, minus relief already "
             "exercised. The 取-holders — routed to sukashi / kabuto / tsumugi for supply-chain "
             "transparency, never a target-list._\n")
    L.append("| rank | collector | kind | catalogue | net-exposure |")
    L.append("|---:|---|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["net_exposure"], nodes, 14), 1):
        n = nodes.get(nid, {})
        kind = str(n.get(":collector/kind") or "—").lstrip(":")
        cat = str(n.get(":collector/catalog") or "—").lstrip(":")
        L.append(f"| {i} | {label} | {kind} | {cat} | {v:.3f} |")

    L.append("\n## Which platform exposes you most — surface leak (Google / Facebook / X / Apple …)\n")
    L.append("_Σ over granted permissions of grant-load × the permission's downstream flow to "
             "collectors — which consent venue leaks the most of you._\n")
    L.append("| rank | surface | operator | leak |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["surface_leak"], nodes, 10), 1):
        op = str(nodes.get(nid, {}).get(":surface/operator") or "—")
        L.append(f"| {i} | {label} | {op} | {v:.3f} |")

    L.append("\n## What kinds of your data are most widely harvested\n")
    L.append("| rank | data-type | spread |")
    L.append("|---:|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["spread"], nodes, 10), 1):
        L.append(f"| {i} | {label} | {v:.3f} |")

    L.append("\n## Reciprocity gap — exposures with NO opt-out / DSAR route\n")
    L.append("_a permission whose data leaks to collectors but has no :routes-to relief — the next "
             "route to wire, routed to himotoki (DSAR) / kaiyaku (sever) / kurashimori (opt-out) / "
             "tedai (on-device revoke). Never a reason to do nothing._\n")
    if res["unrouted_permissions"]:
        for nid in res["unrouted_permissions"]:
            L.append(f"- **{nodes.get(nid, {}).get(':organism/label', nid)}** — leaks, no relief route")
    else:
        L.append("- _(every leaking permission in the seed has at least one relief route)_")

    L.append("\n---\n_aburi 炙り · ADR-2606161630 · own-data · reciprocity-restoring · "
             "non-adjudicating · no-other-person · edge-primary. Live ingest of the member's own "
             "exports + relief routing are G7/Council + member-sig-gated; aburi proposes, "
             "himotoki/kaiyaku/kurashimori/tedai carry.\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-tracker-exposure.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    (outdir / "tracking-exposure-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"aburi: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'tracking-exposure-report.md'}")
    top = _rank(res["net_exposure"], nodes, 1)
    if top:
        print(f"  top tracker: {top[0][1]} ({top[0][2]:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
