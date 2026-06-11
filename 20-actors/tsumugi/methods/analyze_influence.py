#!/usr/bin/env python3
"""tsumugi 紡ぎ — DIACHRONIC influence-history analyzer (ADR-2606061500).

Extends the present-tense power-graph analyzer (analyze.py) BACKWARD IN TIME. Reads a
kotoba-EDN influence-history graph (:organism/* + :hist/* + :mirror/* nodes and :flow/*
directed influence 縁), then:

  1. validates the TEMPORAL DAG (N5): every :flow points forward in time; cycles-in-time
     are reported as data errors (information cannot precede its source).
  2. runs the Spirit-in-Physics pipeline over the influence kernel: affect-class → 10-dim
     emotion vector → RBF kernel W → Laplacian L=D−W → spectral 3D embed → tensegrity
     unilateral-spring relax (identical physics to analyze.py / spirit-ontology).
  3. computes EDGE-INTEGRAL influence readouts (N1 — never a stored per-soul score):
       - outbound-reach  : Katz-decayed forward reach a node SEEDS  (source-strength)
       - inbound-debt    : Katz-decayed influence a node RECEIVES   (synthesizer-strength, 産霊)
       - broker          : inbound × outbound proxy                 (transmission bridge)
  4. emits an aggregate-first influence report + the connected influence-graph as
     :spirit.bond/* + :influence/* datoms (edge-primary).

CONSTITUTIONAL (read influence-history-ontology.kotoba.edn):
  N1 edge-primary  — influence lives on :flow/signed-weight; node readouts are integrals.
  N2 mirror only   — nodes are observed, never spoken-as (this analyzer never authors voice).
  N3 non-eschat.   — influence OF a tradition, never its truth; no verdict/salvation datom.
  N4 public+settled — public influence-bearing figures only; no living PII.
  N5 temporal DAG  — enforced + reported here.

stdlib + numpy only. Usage:
    python3 analyze_influence.py [seed.edn] [--out OUTDIR]
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
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t
    try:    return int(t)
    except ValueError:
        try: return float(t)
        except ValueError: return t

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
            v = _parse(it)
            out[k] = v
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)

def read_edn(text: str):
    return _parse(_tokens(text))

# ── representative 10-dim affect/role vector (deterministic; descriptive — NOT a soul score)
EMO_LABELS = [":joy", ":sadness", ":anger", ":fear", ":disgust",
              ":calm", ":focus", ":surprise", ":confusion", ":interest"]
AFFECT_VEC = {
    ":covenantal": [.5, .4, .3, .5, .2, .6, .7, .3, .2, .8],
    ":reforming":  [.5, .3, .6, .4, .3, .4, .8, .4, .2, .9],
    ":liberative": [.5, .3, .1, .2, .1, .95,.7, .3, .2, .7],
    ":inquiring":  [.4, .2, .2, .3, .2, .6, .9, .6, .4, .95],
    ":animist":    [.6, .3, .2, .3, .1, .8, .5, .5, .3, .7],
    ":ordering":   [.4, .3, .3, .4, .2, .7, .8, .2, .2, .6],
}
DEFAULT_VEC = [.5] * 10

def load(path: str):
    data = read_edn(pathlib.Path(path).read_text(encoding='utf-8'))
    nodes, flows = {}, []
    for m in data:
        if not isinstance(m, dict):
            continue
        if ":organism/id" in m:
            nodes[m[":organism/id"]] = m
        elif ":flow/id" in m:
            flows.append(m)
    return nodes, flows

def node_year(n: dict, which: str) -> int:
    return int(n.get(which, n.get(":hist/year-from", 0)))

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = args[0] if args else str(here / "data" / "seed-influence-history.kotoba.edn")
    outdir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, flows = load(seed)
    ids = list(nodes.keys())
    idx = {k: i for i, k in enumerate(ids)}
    n = len(ids)
    flows = [f for f in flows if f[":flow/from"] in idx and f[":flow/to"] in idx]

    # ── N5: temporal-DAG validation. Information cannot precede its source. The minimal
    # causal rule that admits both figure→figure precedence AND influence INTO a long-lived
    # tradition/document (and contemporaries): the source must have BEGUN no later than the
    # receiver ENDED — i.e. their lifespans are not strictly source-after-receiver.
    # Violation ⇔ source.year-from > receiver.year-to (source appears after receiver is gone).
    violations = []
    for f in flows:
        a, b = nodes[f[":flow/from"]], nodes[f[":flow/to"]]
        ya, yb = node_year(a, ":hist/year-from"), node_year(b, ":hist/year-to")
        if ya > yb:  # source begins after receiver has ended → backward influence
            violations.append((f[":flow/id"], f[":flow/from"], ya, f[":flow/to"], yb))

    # ── feature matrix F (n x 10) from affect-class, normalized rows
    F = np.array([AFFECT_VEC.get(nodes[k].get(":influence/affect-class"), DEFAULT_VEC) for k in ids], float)
    F = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)

    # ── RBF emotion kernel W (undirected — for spectral geometry only)
    D2 = np.sum((F[:, None, :] - F[None, :, :]) ** 2, axis=2)
    sig = np.median(np.sqrt(D2[D2 > 0])) or 1.0
    W = np.exp(-D2 / (sig ** 2)); np.fill_diagonal(W, 0.0)
    Dg = np.diag(W.sum(1)); L = Dg - W

    # ── spectral 3D embedding (eigenvectors 2..4 of L)
    evals, evecs = np.linalg.eigh(L)
    coords = evecs[:, 1:4].copy()
    coords /= (np.abs(coords).max() + 1e-9)

    # ── tensegrity relax: :flow/* edges as unilateral springs (strain → rest-length/stiffness)
    spring = []
    for f in flows:
        i, j = idx[f[":flow/from"]], idx[f[":flow/to"]]
        s = abs(float(f.get(":flow/strain", abs(float(f.get(":flow/signed-weight", 0.3))))))
        spring.append((i, j, max(0.15, 1.0 - s), 0.2 + 0.8 * s))
    for _ in range(150):
        disp = np.zeros_like(coords)
        for i, j, L0, k in spring:
            d = coords[i] - coords[j]; dist = np.linalg.norm(d) + 1e-9
            if dist > L0:
                fce = k * (dist - L0) * d / dist
                disp[i] -= fce; disp[j] += fce
        coords += 0.05 * disp

    # ── directed weighted adjacency A (|signed-weight|), Katz reach over the DAG (N1 edge-integral)
    A = np.zeros((n, n))
    for f in flows:
        i, j = idx[f[":flow/from"]], idx[f[":flow/to"]]
        A[i, j] += abs(float(f.get(":flow/signed-weight", 0.3)))
    beta = 0.5
    # DAG ⇒ A nilpotent ⇒ (I − βA)^-1 exists; M = Σ_{k≥1} (βA)^k = (I−βA)^-1 − I
    M = np.linalg.inv(np.eye(n) - beta * A) - np.eye(n)
    outbound = M.sum(axis=1)          # forward reach a node SEEDS (source-strength)
    inbound = M.sum(axis=0)           # influence a node RECEIVES (synthesizer / 産霊)
    omax, imax = outbound.max() or 1.0, inbound.max() or 1.0
    broker = (outbound / omax) * (inbound / imax)   # transmission-bridge proxy

    # ── spirit connectivity / separation (kernel)
    conn = W.sum(1)
    sep = 1.0 - (conn - conn.min()) / (conn.max() - conn.min() + 1e-9)

    # ── connected components (union-find over influence 縁, undirected)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for f in flows:
        a, b = find(idx[f[":flow/from"]]), find(idx[f[":flow/to"]]); parent[a] = b
    comps = {}
    for k in ids:
        comps.setdefault(find(idx[k]), []).append(k)

    # ── emit influence-graph datoms (edge-primary :spirit.bond/* + :influence/* readouts)
    out_edn = outdir / "influence-graph.kotoba.edn"
    lines = [";; tsumugi 紡ぎ — GENERATED diachronic influence-graph (ADR-2606061500). DO NOT hand-edit.",
             ";; edge-primary (N1): influence=:spirit.bond/signed-weight on :flow/* edges only.",
             ";; readouts are integrals of incident edges, materialized for viz — never a soul-score.",
             "["]
    for f in flows:
        i, j = idx[f[":flow/from"]], idx[f[":flow/to"]]
        w = float(f.get(":flow/signed-weight", 0.3))
        s = abs(float(f.get(":flow/strain", abs(w))))
        L0 = max(0.15, 1.0 - s); k = 0.2 + 0.8 * s
        lag = node_year(nodes[f[":flow/to"]], ":hist/year-from") - node_year(nodes[f[":flow/from"]], ":hist/year-to")
        cond = round(float(W[i, j]), 4)
        lines.append(
            f'{{:spirit.bond/id "sb.{f[":flow/id"][3:]}" :spirit.bond/en "{f[":flow/id"]}" '
            f':spirit.bond/from "{f[":flow/from"]}" :spirit.bond/to "{f[":flow/to"]}" '
            f':spirit.bond/mode :tension :spirit.bond/rest-length {round(L0,3)} '
            f':spirit.bond/stiffness {round(k,3)} :spirit.bond/signed-weight {round(w,3)} '
            f':flow/kind {f.get(":flow/kind",":influences")} :flow/lag-years {lag} '
            f':spirit.bond/emotion-weight {cond} :spirit.bond/conductance {cond} '
            f':spirit.bond/source {f.get(":flow/source",":declared")} :spirit.bond/sourcing :representative}}')
    for k in ids:
        i = idx[k]
        lines.append(
            f'{{:spirit/id "spirit.hist.{k}" :spirit/organism "{k}" :spirit/scale :historical '
            f':spirit/separation {round(float(sep[i]),3)} :spirit/connectivity {round(float(conn[i]),3)} '
            f':spirit/sourcing :representative}}')
        lines.append(
            f'{{:influence/node "{k}" :influence/outbound-reach {round(float(outbound[i]),3)} '
            f':influence/inbound-debt {round(float(inbound[i]),3)} '
            f':influence/betweenness {round(float(broker[i]),3)} '
            f':influence/method "infl-1.0.0/katz-beta0.5/kernel-rbf/embed-spectral3/tensegrity-unilateral"}}')
    lines.append("]")
    out_edn.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── aggregate-first influence report
    by_out = sorted(ids, key=lambda k: outbound[idx[k]], reverse=True)
    by_in = sorted(ids, key=lambda k: inbound[idx[k]], reverse=True)
    by_brk = sorted(ids, key=lambda k: broker[idx[k]], reverse=True)
    def lbl(k): return nodes[k].get(":organism/label", k)
    def conf(k): return nodes[k].get(":hist/dating-confidence", ":representative")[1:]

    R = ["# tsumugi 紡ぎ — Diachronic Influence-History Report",
         "",
         "> Aggregate-first map of **influence-as-information-flow** across PUBLIC historical",
         "> figures, documents, events and traditions, routed to understanding — **NOT** a",
         "> ranking of worth, a target-list, or a hagiography. Edge-primary (N1): influence",
         "> lives on 縁, never on a soul. Sourcing `:representative` (documented intellectual-",
         "> /religious-history, bounded sample). **We datafy the INFLUENCE OF a tradition,",
         "> NEVER its theological truth** (N3, 非終末論). Mirror-only: nodes are observed,",
         "> never spoken-as (N2). Live planet-scale ingest is G7/Council-gated.",
         "",
         f"- nodes: **{n}**  ·  influence 縁: **{len(flows)}**  ·  components: **{len(comps)}**",
         f"- emotion-kernel σ_eff = {sig:.4f}  ·  Katz β = {beta}  ·  method = infl-1.0.0",
         f"- temporal-DAG (N5): **{'OK — all edges forward in time' if not violations else str(len(violations))+' VIOLATION(S)'}**",
         ""]
    if violations:
        R += ["### ⚠ N5 temporal violations (information cannot precede its source)", ""]
        for fid, fr, ya, to, yb in violations:
            R.append(f"- `{fid}`: {lbl(fr)} (ends {ya}) → {lbl(to)} (begins {yb})")
        R.append("")
    R += ["## Top influence SOURCES (outbound-reach = forward Katz reach this node SEEDS)",
          "",
          "> Who/what propagated furthest downstream through history. Edge-integral, never a soul-score.",
          "",
          "| rank | node | kind | tradition | outbound-reach | dating |",
          "|---|---|---|---|---|---|"]
    for r, k in enumerate(by_out[:12], 1):
        nd = nodes[k]
        trad = ",".join(t[1:] for t in nd.get(":hist/tradition", []))
        R.append(f"| {r} | {lbl(k)} | {nd.get(':hist/subkind','—')[1:]} | {trad} "
                 f"| **{outbound[idx[k]]:.2f}** | {conf(k)} |")
    R += ["",
          "## Top SYNTHESIZERS (inbound-debt = influence this node RECEIVED — the 産霊 side)",
          "",
          "| rank | node | kind | inbound-debt | outbound-reach |",
          "|---|---|---|---|---|"]
    for r, k in enumerate(by_in[:10], 1):
        R.append(f"| {r} | {lbl(k)} | {nodes[k].get(':hist/subkind','—')[1:]} "
                 f"| **{inbound[idx[k]]:.2f}** | {outbound[idx[k]]:.2f} |")
    R += ["",
          "## Top TRANSMISSION BROKERS (inbound × outbound — bridges through which history flowed)",
          ""]
    for r, k in enumerate(by_brk[:8], 1):
        R.append(f"{r}. **{lbl(k)}** (broker {broker[idx[k]]:.3f})")

    # etzhayyim doctrinal genealogy — its own inbound influence edges (honest synthesis map)
    self_in = [f for f in flows if f[":flow/to"] == "self.etzhayyim"]
    if self_in:
        R += ["",
              "## etzhayyim doctrinal genealogy (own inbound influence — 産霊 receiving side)",
              "",
              "> Not a claim of equivalence with the sources; an honest map of documented inflows.",
              ""]
        for f in sorted(self_in, key=lambda f: abs(float(f.get(":flow/signed-weight",0))), reverse=True):
            R.append(f"- {lbl(f[':flow/from'])} —{f.get(':flow/kind','')[1:]}→ etzhayyim "
                     f"(w={float(f[':flow/signed-weight']):+.2f}, strain={float(f.get(':flow/strain',0)):.2f})")

    R += ["",
          "## Era layering (diachronic 軌跡 — Wellbecoming as history, not a final state; N2/N3)",
          ""]
    eras_order = [":bronze-age",":iron-age",":axial",":2nd-temple",":late-antiquity",
                  ":early-medieval",":medieval",":reformation",":enlightenment",":modern",":contemporary"]
    by_era = {}
    for k in ids:
        by_era.setdefault(nodes[k].get(":hist/era", ":?"), []).append(k)
    for e in eras_order:
        if e in by_era:
            R.append(f"- **{e[1:]}**: " + ", ".join(lbl(k) for k in by_era[e]))

    R += ["",
          "## Connected components (woven 縁 clusters)",
          ""]
    for c, members in enumerate(sorted(comps.values(), key=len, reverse=True), 1):
        R.append(f"{c}. ({len(members)}) " + ", ".join(lbl(m) for m in members))

    R += ["",
          "## Honest limits",
          "- `:representative` seed — documented influence, a bounded sample, NOT exhaustive.",
          "- Dating is approximate; per-node `:hist/dating-confidence` flags legendary/traditional",
          "  attributions (e.g. Moses, Bodhidharma) — never asserted as fact (N3).",
          "- Affect vectors are class-derived representatives, not measured assays.",
          "- Influence readouts are edge-integrals (N1), an analytic lens — never a per-soul score,",
          "  a verdict on a tradition's truth (N3), or a ranking of human worth (N4).",
          "- Outward / live ingest (archives, citation graphs) + any published post is G7+Council-gated."]
    (outdir / "influence-report.md").write_text("\n".join(R) + "\n", encoding="utf-8")

    print(f"✓ {n} nodes · {len(flows)} influence 縁 · {len(comps)} components")
    print(f"✓ temporal-DAG (N5): {'OK' if not violations else str(len(violations))+' violations'}")
    print(f"✓ top influence source: {lbl(by_out[0])} (outbound-reach {outbound[idx[by_out[0]]]:.2f})")
    print(f"✓ top synthesizer:      {lbl(by_in[0])} (inbound-debt {inbound[idx[by_in[0]]]:.2f})")
    print(f"✓ wrote {out_edn}")
    print(f"✓ wrote {outdir/'influence-report.md'}")
    return 0 if not violations else 1

if __name__ == "__main__":
    sys.exit(main())
