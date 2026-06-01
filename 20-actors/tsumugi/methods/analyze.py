#!/usr/bin/env python3
"""tsumugi 紡ぎ — spirit-in-physics intel analyzer over the Engi Knowledge Graph.

§D7.1 of ADR-2606011000 + spirit-ontology (ADR-2606011500). Reads a kotoba-EDN
power-graph (:organism/* + :en/* 縁), applies the Spirit-in-Physics pipeline
(10-dim emotion vector → RBF kernel W → Laplacian L=D−W → spectral 3D embed →
tensegrity unilateral-spring relax), and emits:

  1. an aggregate-first 取-concentration intel report (who accumulates custody-debt
     over others — the accountability surface, routed to release; NOT a target-list)
  2. the connected spirit-graph as :spirit.bond/* + :spirit/* + :grasp/* datoms

CONSTITUTIONAL (N1): karma/取 lives ONLY on edges. An organism's 取-concentration is
the INTEGRAL of its incident edges — never a stored per-soul score. Public power
entities only; powerless/private organisms are absent by construction (§D9).

stdlib + numpy only. Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, math, pathlib
import numpy as np

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')

def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t

def _atom(t: str):
    if t.startswith('"'):
        # unescape \" and \\ only — preserve multibyte UTF-8 (Japanese, em-dash) intact
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t  # keep keywords as ":ns/name" strings
    try:    return int(t)
    except ValueError:
        try: return float(t)
        except ValueError: return t

def _parse(tokens, it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(tokens, it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(tokens, it)) is not _END:
            v = _parse(tokens, it)
            out[k] = v
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)

_END = object()

def read_edn(text: str):
    it = _tokens(text)
    return _parse(text, it)

# ── representative 10-dim sector/role vector (deterministic; NOT a personality score)
EMO_LABELS = [":joy", ":sadness", ":anger", ":fear", ":disgust",
              ":calm", ":focus", ":surprise", ":confusion", ":interest"]
SECTOR_VEC = {
    ":automaker":       [.5, .2, .2, .3, .1, .6, .9, .2, .1, .7],
    ":auto-supplier":   [.4, .2, .2, .4, .1, .7, .9, .2, .1, .6],
    ":holding":         [.3, .2, .3, .5, .2, .4, .6, .3, .3, .8],
    ":semiconductor-ip":[.4, .1, .2, .3, .1, .5, .9, .3, .1, .8],
    ":foundry":         [.3, .1, .2, .6, .1, .5, .95,.2, .1, .7],
    ":semiconductor":   [.5, .1, .2, .4, .1, .5, .9, .4, .1, .85],
    ":platform":        [.6, .2, .3, .4, .2, .5, .8, .5, .2, .9],
    ":ai-lab":          [.6, .2, .3, .5, .2, .4, .85,.7, .3, .95],
    ":bank":            [.3, .3, .3, .6, .2, .6, .7, .2, .2, .6],
    ":regulator":       [.3, .3, .4, .5, .3, .7, .6, .2, .3, .5],
    ":ecological":      [.4, .4, .2, .3, .1, .9, .3, .3, .2, .4],
    ":exec-role":       [.5, .2, .4, .5, .2, .5, .8, .3, .2, .8],
    ":media":           [.5, .3, .3, .4, .2, .4, .7, .6, .3, .9],
    ":gov":             [.4, .3, .3, .5, .2, .6, .7, .3, .3, .6],
}
DEFAULT_VEC = [.5]*10

def load(path: str):
    data = read_edn(pathlib.Path(path).read_text(encoding='utf-8'))
    orgs, edges = {}, []
    for m in data:
        if ":organism/id" in m:
            orgs[m[":organism/id"]] = m
        elif ":en/id" in m:
            edges.append(m)
    return orgs, edges

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = args[0] if args else str(here / "data" / "seed-power-graph.kotoba.edn")
    outdir = pathlib.Path(sys.argv[sys.argv.index('--out')+1]) if '--out' in sys.argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    orgs, edges = load(seed)
    ids = list(orgs.keys())
    idx = {k: i for i, k in enumerate(ids)}
    n = len(ids)
    # keep only edges whose endpoints exist
    edges = [e for e in edges if e[":en/from"] in idx and e[":en/to"] in idx]

    # feature matrix F (n x 10), normalized rows
    F = np.array([SECTOR_VEC.get(orgs[k].get(":tsumugi/sector"), DEFAULT_VEC) for k in ids], float)
    F = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)

    # ── RBF emotion kernel W (dense, README §1)
    D2 = np.sum((F[:, None, :] - F[None, :, :])**2, axis=2)
    sig = np.median(np.sqrt(D2[D2 > 0])) or 1.0
    W = np.exp(-D2 / (sig**2)); np.fill_diagonal(W, 0.0)
    Dg = np.diag(W.sum(1)); L = Dg - W

    # ── spectral embedding: eigenvectors 2..4 of L (smallest non-trivial) (README §2)
    evals, evecs = np.linalg.eigh(L)
    coords = evecs[:, 1:4].copy()
    coords /= (np.abs(coords).max() + 1e-9)  # shell-normalize

    # ── tensegrity relax: 縁 edges as unilateral springs (README §4)
    spring = []  # (i, j, L0, k)
    for e in edges:
        i, j = idx[e[":en/from"]], idx[e[":en/to"]]
        g = float(e.get(":en/grasping-load", 0.3))
        spring.append((i, j, max(0.15, 1.0 - g), 0.2 + 0.8 * g))
    for _ in range(150):
        disp = np.zeros_like(coords)
        for i, j, L0, k in spring:
            d = coords[i] - coords[j]; dist = np.linalg.norm(d) + 1e-9
            if dist > L0:  # tension-only (pull together)
                f = k * (dist - L0) * d / dist
                disp[i] -= f; disp[j] += f
        coords += 0.05 * disp

    # ── 取-concentration: integral of INCIDENT edges (N1). inbound = power held over others.
    held = {k: 0.0 for k in ids}   # others depend-on / are custodied-by k  → k's power
    bound = {k: 0.0 for k in ids}  # k depends-on / is custodied-by others → k's しがらみ
    deg = {k: 0 for k in ids}
    for e in edges:
        g = float(e.get(":en/grasping-load", 0.3))
        frm, to = e[":en/from"], e[":en/to"]
        held[to] += g; bound[frm] += g
        deg[frm] += 1; deg[to] += 1
    # spirit connectivity (kernel) + separation (U_spirit minimand, ADR-2604291800/2605170000)
    conn = W.sum(1)
    sep = 1.0 - (conn - conn.min()) / (conn.max() - conn.min() + 1e-9)

    # ── connected components (union-find over 縁)
    parent = list(range(n))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for e in edges:
        a, b = find(idx[e[":en/from"]]), find(idx[e[":en/to"]]); parent[a] = b
    comps = {}
    for k in ids: comps.setdefault(find(idx[k]), []).append(k)

    # ── emit connected spirit-graph datoms
    out_edn = outdir / "spirit-graph.kotoba.edn"
    lines = [";; tsumugi 紡ぎ — GENERATED spirit-graph (ADR-2606011800). DO NOT hand-edit.",
             ";; edge-primary (N1): karma=:spirit.bond/signed-weight on edges only.", "["]
    for e in edges:
        i, j = idx[e[":en/from"]], idx[e[":en/to"]]
        g = float(e.get(":en/grasping-load", 0.3))
        L0 = max(0.15, 1.0 - g); k = 0.2 + 0.8 * g
        cond = round(float(W[i, j]), 4)
        lines.append(
            f'{{:spirit.bond/id "sb.{e[":en/id"][3:]}" :spirit.bond/en "{e[":en/id"]}" '
            f':spirit.bond/from "{e[":en/from"]}" :spirit.bond/to "{e[":en/to"]}" '
            f':spirit.bond/mode :tension :spirit.bond/rest-length {round(L0,3)} '
            f':spirit.bond/stiffness {round(k,3)} :spirit.bond/signed-weight {round(g,3)} '
            f':spirit.bond/emotion-weight {cond} :spirit.bond/conductance {cond} '
            f':spirit.bond/source {e.get(":en/source",":declared")} :spirit.bond/sourcing :representative}}')
    for k in ids:
        i = idx[k]
        lines.append(
            f'{{:spirit/id "spirit.world.{k}" :spirit/organism "{k}" :spirit/scale :world '
            f':spirit/separation {round(float(sep[i]),3)} :spirit/connectivity {round(float(conn[i]),3)} '
            f':spirit/sourcing :representative}}')
        lines.append(
            f'{{:grasp/organism "{k}" :grasp/concentration {round(held[k],3)} '
            f':grasp/bound-load {round(bound[k],3)} :grasp/release-target {round(max(0.0,held[k]-1.0),3)}}}')
    lines.append("]")
    out_edn.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── aggregate-first intel report
    rank = sorted(ids, key=lambda k: held[k], reverse=True)
    R = ["# tsumugi 紡ぎ — Spirit-in-Physics Intel Report (取-concentration)",
         "",
         "> Aggregate-first accountability map of **取 (custody-debt) concentration** over",
         "> PUBLIC power-holding entities, routed toward release. **NOT** a target-list.",
         "> Edge-primary (N1): karma lives on 縁, not on nodes. Sourcing: `:representative`",
         "> (publicly-documented sample, not exhaustive). Live planet-scale ingest is G11-gated.",
         "",
         f"- organisms (nodes): **{n}**   ·   縁 (edges): **{len(edges)}**   ·   components: **{len(comps)}**",
         f"- emotion-kernel σ_eff = {sig:.4f}   ·   pipeline = sip/kernel-rbf/embed-spectral3/tensegrity-unilateral",
         "",
         "## Top 取-concentration holders (power held OVER others = Σ incident inbound 縁)",
         "",
         "| rank | entity | sector | 取 held | しがらみ bound | degree | release-target |",
         "|---|---|---|---|---|---|---|"]
    for r, k in enumerate(rank[:10], 1):
        o = orgs[k]
        rt = max(0.0, held[k] - 1.0)
        R.append(f"| {r} | {o.get(':organism/label',k)} | {o.get(':tsumugi/sector','—')[1:]} "
                 f"| **{held[k]:.2f}** | {bound[k]:.2f} | {deg[k]} | {rt:.2f} |")
    R += ["",
          "## Spirit readout (separation = blocked-channel entropy; ADR-2605170000)",
          "",
          f"- most-connected (lowest separation): **{orgs[ids[int(np.argmin(sep))]].get(':organism/label')}**",
          f"- most-separated (highest separation): **{orgs[ids[int(np.argmax(sep))]].get(':organism/label')}**",
          "",
          "## Connected components (繋がった 縁 clusters)",
          ""]
    for c, members in enumerate(sorted(comps.values(), key=len, reverse=True), 1):
        labels = ", ".join(orgs[m].get(':organism/label', m) for m in members)
        R.append(f"{c}. ({len(members)}) {labels}")
    R += ["",
          "## Honest limits",
          "- `:representative` seed (publicly-documented relationships, bounded sample).",
          "- Emotion vectors are sector-derived representatives, not measured assays.",
          "- 取-concentration is an accountability lens on power, never a per-person score (N1/§D9).",
          "- Outward / live atproto-follow ingest over real persons is G11 + Council-gated."]
    (outdir / "intel-report.md").write_text("\n".join(R) + "\n", encoding="utf-8")

    print(f"✓ {n} organisms · {len(edges)} 縁 · {len(comps)} components")
    print(f"✓ top 取-holder: {orgs[rank[0]].get(':organism/label')} ({held[rank[0]]:.2f})")
    print(f"✓ wrote {out_edn}")
    print(f"✓ wrote {outdir/'intel-report.md'}")

if __name__ == "__main__":
    main()
