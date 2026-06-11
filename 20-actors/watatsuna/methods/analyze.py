#!/usr/bin/env python3
"""watatsuna 綿津綱 — submarine-cable network resilience analyzer.

ADR-2606012600. Reads a kotoba-EDN cable graph (:cable/* systems, :station/*
landing stations, :cable.link/* incidence, :cable.seg/* chokepoint-traversing
segments, :cable.fault/* observed bulletins) and emits:

  1. an AGGREGATE-FIRST resilience report (out/intel-report.md) — where the
     world's submarine capacity concentrates onto a chokepoint / single point of
     failure, framed toward redundancy + diversity-routing + faster repair.
  2. the derived resilience datoms (out/cable-criticality.kotoba.edn), flagged
     :derived — never re-ingested as authoritative fact.

CONSTITUTIONAL framing (watatsumi N8 + Charter Rider §2(d)): this is a
RESILIENCE map, NEVER a target-list. Output ranks chokepoints by fragility so
the network can be made MORE robust (add diverse routes, pre-stage repair
ships) — it does NOT identify where to cut. Sabotage intent is never asserted;
fault :kind mirrors only the public bulletin's own classification.

stdlib only (no numpy). Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from tsumugi
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':
        return True
    if t == 'false':
        return False
    if t == 'nil':
        return None
    if t.startswith(':'):
        return t  # keep keywords as ":ns/name" strings
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


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


def load_edn(path: pathlib.Path):
    it = _tokens(path.read_text(encoding='utf-8'))
    return _parse(it)


# ── classify the flat datom vector into entity buckets
def classify(rows):
    cables, stations, links, segs, faults = {}, {}, [], [], []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':cable/id' in r:
            cables[r[':cable/id']] = r
        elif ':station/id' in r:
            stations[r[':station/id']] = r
        elif ':cable.link/id' in r:
            links.append(r)
        elif ':cable.seg/id' in r:
            segs.append(r)
        elif ':cable.fault/id' in r:
            faults.append(r)
    return cables, stations, links, segs, faults


def analyze(cables, stations, links, segs, faults):
    cap = {c: cables[c].get(':cable/design-capacity-tbps', 0.0) for c in cables}

    # per-station: which cables land here
    station_cables = defaultdict(set)
    for lk in links:
        station_cables[lk[':cable.link/station']].add(lk[':cable.link/cable'])

    station_degree = {s: len(station_cables[s]) for s in stations}
    station_capacity = {
        s: round(sum(cap.get(c, 0.0) for c in station_cables[s]), 2) for s in stations
    }

    # per-chokepoint: distinct cables traversing it (via segments) + via station tags
    choke_cables = defaultdict(set)
    for sg in segs:
        for cp in (sg.get(':cable.seg/traverses') or []):
            choke_cables[cp].add(sg[':cable.seg/cable'])
    # also fold station chokepoint tags: a cable landing behind a chokepoint depends on it
    for s, meta in stations.items():
        for cp in (meta.get(':station/chokepoint') or []):
            for c in station_cables[s]:
                choke_cables[cp].add(c)

    choke_load = {
        cp: round(sum(cap.get(c, 0.0) for c in cs), 2) for cp, cs in choke_cables.items()
    }
    choke_count = {cp: len(cs) for cp, cs in choke_cables.items()}

    # per-cable diversity: # distinct chokepoints it depends on (lower = more brittle)
    cable_chokes = defaultdict(set)
    for cp, cs in choke_cables.items():
        for c in cs:
            cable_chokes[c].add(cp)
    cable_diversity = {c: len(cable_chokes[c]) for c in cables}

    # redundancy gap: landing stations served by a single cable
    redundancy_gap = sorted(s for s in stations if station_degree[s] <= 1)

    return dict(
        cap=cap,
        station_cables=station_cables,
        station_degree=station_degree,
        station_capacity=station_capacity,
        choke_cables=choke_cables,
        choke_load=choke_load,
        choke_count=choke_count,
        cable_diversity=cable_diversity,
        redundancy_gap=redundancy_gap,
    )


def name(d, key, idkey, namekey):
    return d.get(key, {}).get(namekey, key) if isinstance(d.get(key), dict) else key


def render_report(cables, stations, links, segs, faults, a):
    L = []
    P = L.append
    P("# watatsuna 綿津綱 — submarine-cable network resilience report")
    P("")
    P("> ADR-2606012600 · **aggregate-first** · RESILIENCE map (NOT a target-list; "
      "watatsumi N8 + Charter Rider §2(d)). Sabotage intent never asserted. "
      "All sourcing `:representative` — bounded illustrative seed, not exhaustive coverage.")
    P("")
    P(f"- cable systems: **{len(cables)}**  ·  landing stations: **{len(stations)}**  "
      f"·  cable↔station links: **{len(links)}**  ·  chokepoint segments: **{len(segs)}**  "
      f"·  observed faults: **{len(faults)}**")
    total_design = round(sum(a['cap'].values()), 1)
    P(f"- total seeded design capacity: **{total_design} Tbps**")
    P("")

    # ── chokepoint concentration (the headline resilience signal) ──
    P("## Chokepoint concentration — single-point-of-failure surface")
    P("")
    P("Capacity (Σ design Tbps of distinct cables) that depends on each maritime "
      "chokepoint. Higher = more of the world's traffic shares one geographic fate. "
      "**Routed to redundancy + pre-staged repair, never to interdiction.**")
    P("")
    P("| chokepoint | cables | dependent capacity (Tbps) |")
    P("|---|---:|---:|")
    for cp in sorted(a['choke_load'], key=lambda k: -a['choke_load'][k]):
        P(f"| `{cp}` | {a['choke_count'][cp]} | {a['choke_load'][cp]} |")
    P("")

    # ── landing-station hubs ──
    P("## Landing-station hubs — convergence points")
    P("")
    P("| station | country | cables | landed capacity (Tbps) |")
    P("|---|---|---:|---:|")
    for s in sorted(stations, key=lambda k: (-a['station_degree'][k], -a['station_capacity'][k])):
        if a['station_degree'][s] == 0:
            continue
        st = stations[s]
        P(f"| {st.get(':station/name', s)} | {st.get(':station/country','?')} "
          f"| {a['station_degree'][s]} | {a['station_capacity'][s]} |")
    P("")

    # ── brittle cables (low route diversity) ──
    P("## Most brittle systems — low chokepoint diversity")
    P("")
    P("Cables depending on the fewest distinct chokepoints carry the highest "
      "correlated-failure risk; candidates for diverse-route augmentation.")
    P("")
    P("| cable | chokepoints depended on | design (Tbps) | RFS |")
    P("|---|---:|---:|---:|")
    for c in sorted(cables, key=lambda k: (a['cable_diversity'][k], -a['cap'][k])):
        div = a['cable_diversity'][c]
        if div == 0:
            continue  # no charted chokepoint dependency in seed
        cb = cables[c]
        P(f"| {cb.get(':cable/name', c)} | {div} | {a['cap'][c]} | "
          f"{cb.get(':cable/rfs-year','?')} |")
    P("")

    # ── redundancy gaps ──
    P("## Redundancy gaps — single-cable landing stations")
    P("")
    if a['redundancy_gap']:
        for s in a['redundancy_gap']:
            P(f"- {stations[s].get(':station/name', s)} "
              f"({stations[s].get(':station/country','?')}) — routed to redundancy")
    else:
        P("- (none in seed)")
    P("")

    # ── observed faults (as-of history) ──
    P("## Observed fault bulletins (Datom as-of history; 非終末論 — appended, never overwritten)")
    P("")
    P("| fault | cable | kind (bulletin's own) | detected | restored |")
    P("|---|---|---|---|---|")
    for f in faults:
        cb = cables.get(f.get(':cable.fault/cable'), {})
        P(f"| `{f[':cable.fault/id']}` | {cb.get(':cable/name', f.get(':cable.fault/cable'))} "
          f"| `{f.get(':cable.fault/kind')}` | {f.get(':cable.fault/detected-at','?')} "
          f"| {f.get(':cable.fault/restored-at') or 'open'} |")
    P("")
    P("---")
    P("*Generated by `watatsuna/methods/analyze.py`. HONEST: R0 bounded seed; "
      "coordinates rounded to landing town; capacities are public design figures; "
      "chokepoint dependency is charted only for seeded segments. Live planet-scale "
      "ingest is G7 Council+operator gated.*")
    return "\n".join(L) + "\n"


def render_datoms(cables, stations, a):
    L = []
    P = L.append
    P(";; watatsuna — DERIVED resilience datoms (ADR-2606012600). :derived — NOT authoritative fact.")
    P(";; Recomputed from the seed graph; do not re-ingest as :authoritative.")
    P("[")
    for cp in sorted(a['choke_load'], key=lambda k: -a['choke_load'][k]):
        P(f' {{:resilience/chokepoint "{cp}" :resilience/chokepoint-load {a["choke_load"][cp]} '
          f':resilience/cable-count {a["choke_count"][cp]} :resilience/derived true}}')
    for s in sorted(stations, key=lambda k: -a['station_degree'][k]):
        if a['station_degree'][s] == 0:
            continue
        P(f' {{:resilience/station "{s}" :resilience/station-degree {a["station_degree"][s]} '
          f':resilience/station-capacity-tbps {a["station_capacity"][s]} :resilience/derived true}}')
    for c in sorted(cables, key=lambda k: a['cable_diversity'][k]):
        P(f' {{:resilience/cable "{c}" :resilience/cable-diversity {a["cable_diversity"][c]} '
          f':resilience/derived true}}')
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "seed-cable-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    cables, stations, links, segs, faults = classify(rows)
    a = analyze(cables, stations, links, segs, faults)

    (outdir / "intel-report.md").write_text(
        render_report(cables, stations, links, segs, faults, a), encoding='utf-8')
    (outdir / "cable-criticality.kotoba.edn").write_text(
        render_datoms(cables, stations, a), encoding='utf-8')

    print(f"watatsuna: {len(cables)} cables, {len(stations)} stations, "
          f"{len(links)} links, {len(segs)} segments, {len(faults)} faults")
    top = sorted(a['choke_load'], key=lambda k: -a['choke_load'][k])[:3]
    print("top chokepoints by dependent capacity: " +
          ", ".join(f"{cp} {a['choke_load'][cp]}Tbps" for cp in top))
    print(f"wrote {outdir/'intel-report.md'} + {outdir/'cable-criticality.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
