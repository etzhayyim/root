#!/usr/bin/env python3
"""tsumugi 紡ぎ — influence-history COVERAGE report (ADR-2606061500).

Institutionalizes the manual coverage analysis: given the diachronic seed it computes,
honestly, how much of the target space is covered — by denominator (figures vs documented
notables / vs all humanity), by ERA, by civilizational TRADITION-stream, and by graph
connectedness — and emits a gap map so each seed wave shows measurable progress.

NOT a claim of completeness: the headline truth is that coverage of *all* past humanity is
~0 by design (a bounded :representative sample); this tool makes the real, useful coverage
(the major influence backbone of recorded thought) measurable, and names what is thin/missing.

stdlib only (reuses analyze_influence's EDN loader). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze_influence import load, node_year  # noqa: E402

# the full era spine (chronological) the seed should eventually populate
ERA_SPINE = [":bronze-age", ":iron-age", ":axial", ":2nd-temple", ":late-antiquity",
             ":early-medieval", ":medieval", ":reformation", ":enlightenment",
             ":modern", ":contemporary"]

# the major civilizational influence-streams (the "backbone" target)
MAJOR_STREAMS = [":abrahamic", ":jewish", ":christian", ":reformed", ":islamic",
                 ":hellenic", ":buddhist", ":mahayana", ":zen", ":hindu", ":vedic",
                 ":daoist", ":confucian", ":jain", ":zoroastrian", ":shinto",
                 ":secular-philosophy"]

# denominators (honest external reference sets for the FIGURE count)
DENOMINATORS = [
    ("MIT Pantheon notable people", 88_937),
    ("Wikidata humans (~)", 10_500_000),
    ("All humans ever (~Population Reference Bureau)", 117_000_000_000),
]

THIN = 2  # a stream/era with < THIN nodes is flagged thin


def components(nodes, flows):
    ids = list(nodes); idx = {k: i for i, k in enumerate(ids)}; par = list(range(len(ids)))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for f in flows:
        if f[":flow/from"] in idx and f[":flow/to"] in idx:
            par[find(idx[f[":flow/from"]])] = find(idx[f[":flow/to"]])
    comp = {}
    for k in ids: comp.setdefault(find(idx[k]), []).append(k)
    return sorted(comp.values(), key=len, reverse=True)


def compute(seed: str) -> dict:
    nodes, flows = load(seed)
    flows = [f for f in flows if f[":flow/from"] in nodes and f[":flow/to"] in nodes]
    sub = Counter(n.get(":hist/subkind") for n in nodes.values())
    era = Counter(n.get(":hist/era") for n in nodes.values())
    stream = Counter()
    for n in nodes.values():
        for t in n.get(":hist/tradition", []):
            stream[t] += 1
    deg = Counter()
    for f in flows:
        deg[f[":flow/from"]] += 1; deg[f[":flow/to"]] += 1
    isolated = [k for k in nodes if deg[k] == 0]
    comps = components(nodes, flows)
    figures = sub.get(":figure", 0)
    n = len(nodes)
    density = len(flows) / (n * (n - 1)) if n > 1 else 0.0
    return {
        "nodes": n, "edges": len(flows), "figures": figures,
        "subkind": dict(sub), "era": dict(era), "stream": dict(stream),
        "isolated": isolated, "components": comps,
        "density": density,
        "era_covered": [e for e in ERA_SPINE if era.get(e, 0) > 0],
        "era_missing": [e for e in ERA_SPINE if era.get(e, 0) == 0],
        "era_thin": [e for e in ERA_SPINE if 0 < era.get(e, 0) < THIN],
        "stream_covered": [s for s in MAJOR_STREAMS if stream.get(s, 0) > 0],
        "stream_missing": [s for s in MAJOR_STREAMS if stream.get(s, 0) == 0],
        "stream_thin": [s for s in MAJOR_STREAMS if 0 < stream.get(s, 0) < THIN],
    }


def render(c: dict) -> str:
    R = ["# tsumugi 紡ぎ — Influence-History Coverage Report",
         "",
         "> Honest coverage of the influence backbone. **Coverage of *all* past humanity is ~0",
         "> by design** (a bounded `:representative` sample); this measures the useful coverage",
         "> (major influence streams of recorded thought) and names what is thin/missing.",
         "",
         f"- nodes **{c['nodes']}** · edges **{c['edges']}** · figures **{c['figures']}** · "
         f"graph density **{100*c['density']:.1f}%** of directed pairs",
         f"- connected components **{len(c['components'])}** "
         f"(largest **{len(c['components'][0]) if c['components'] else 0}**) · "
         f"isolated nodes **{len(c['isolated'])}**"
         + (f" {[i for i in c['isolated']]}" if c['isolated'] else ""),
         f"- node kinds: {c['subkind']}",
         "",
         "## Figure coverage vs external denominators",
         "",
         "| denominator | size | covered |",
         "|---|---:|---:|"]
    for name, size in DENOMINATORS:
        pct = 100 * c["figures"] / size
        shown = f"{pct:.3f}%" if pct >= 0.001 else f"{pct:.2e}%"
        R.append(f"| {name} | {size:,} | {shown} |")
    R += ["",
          f"## Era coverage — {len(c['era_covered'])}/{len(ERA_SPINE)} buckets populated",
          ""]
    for e in ERA_SPINE:
        cnt = c["era"].get(e, 0)
        mark = "—" if cnt == 0 else ("⚠ thin" if cnt < THIN else "ok")
        R.append(f"- `{e[1:]}`: {cnt}  ({mark})")
    if c["era_missing"]:
        R.append(f"\n**Missing eras**: {', '.join(e[1:] for e in c['era_missing'])}")
    R += ["",
          f"## Civilizational-stream coverage — {len(c['stream_covered'])}/{len(MAJOR_STREAMS)} "
          f"streams have ≥1 node",
          ""]
    for s in MAJOR_STREAMS:
        cnt = c["stream"].get(s, 0)
        mark = "—" if cnt == 0 else ("⚠ thin" if cnt < THIN else "ok")
        R.append(f"- `{s[1:]}`: {cnt}  ({mark})")
    if c["stream_missing"]:
        R.append(f"\n**Missing streams**: {', '.join(s[1:] for s in c['stream_missing'])}")
    if c["stream_thin"]:
        R.append(f"**Thin streams** (<{THIN}): {', '.join(s[1:] for s in c['stream_thin'])}")
    R += ["",
          "## Gap map (next-wave priorities)",
          ""]
    gaps = []
    if c["era_missing"]: gaps.append(f"fill empty eras: {', '.join(e[1:] for e in c['era_missing'])}")
    if c["era_thin"]:    gaps.append(f"thicken thin eras: {', '.join(e[1:] for e in c['era_thin'])}")
    if c["stream_missing"]: gaps.append(f"add missing streams: {', '.join(s[1:] for s in c['stream_missing'])}")
    if c["stream_thin"]: gaps.append(f"thicken thin streams: {', '.join(s[1:] for s in c['stream_thin'])}")
    if len(c["components"]) > 1: gaps.append(f"connect {len(c['components'])} components into 1")
    if c["isolated"]: gaps.append(f"wire {len(c['isolated'])} isolated node(s)")
    if not gaps: gaps.append("backbone covered + connected — scale depth via live ingest (G7-gated)")
    for g in gaps:
        R.append(f"- {g}")
    R += ["",
          "## Honest headline",
          f"- Backbone: **{len(c['stream_covered'])}/{len(MAJOR_STREAMS)} streams** · "
          f"**{len(c['era_covered'])}/{len(ERA_SPINE)} eras** · "
          f"**{'fully connected' if len(c['components'])==1 and not c['isolated'] else 'fragmented'}**.",
          "- All-humanity coverage remains effectively 0 (by design). Raising the real count "
          "needs the G7+Council-gated live ingest (`ingest_influence.py`)."]
    return "\n".join(R) + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = args[0] if args else str(here / "data" / "seed-influence-history.kotoba.edn")
    outdir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    c = compute(seed)
    (outdir / "coverage-report.md").write_text(render(c), encoding="utf-8")
    print(f"✓ nodes {c['nodes']} · edges {c['edges']} · figures {c['figures']}")
    print(f"✓ eras {len(c['era_covered'])}/{len(ERA_SPINE)} · streams "
          f"{len(c['stream_covered'])}/{len(MAJOR_STREAMS)} · components {len(c['components'])} · "
          f"isolated {len(c['isolated'])}")
    if c["era_missing"]:    print(f"  gap: missing eras {[e[1:] for e in c['era_missing']]}")
    if c["stream_missing"]: print(f"  gap: missing streams {[s[1:] for s in c['stream_missing']]}")
    print(f"✓ wrote {outdir/'coverage-report.md'}")


if __name__ == "__main__":
    main()
