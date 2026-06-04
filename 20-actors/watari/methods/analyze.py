#!/usr/bin/env python3
"""watari 渡り — live moving-craft (ship + aircraft) situational analyzer.

ADR-2606041827. Reads a kotoba-EDN moving-craft graph (:craft/* identities,
:craft.fix/* append-only position fixes, :craft.leg/* voyages/flights, :lane/*
density units) and emits:

  1. an AGGREGATE-FIRST situational report (out/intel-report.md) — where live
     moving traffic concentrates onto a sea-lane / air-corridor / chokepoint /
     port-airport approach, framed toward SAFETY + collision-avoidance +
     congestion-easing + resilience. Couples to watatsuna (ADR-2606012600): a
     vessel's LIVE chokepoint transit composes with watatsuna's STATIC submarine
     cable chokepoint load over the SAME chokepoint keywords.
  2. the derived movement datoms (out/movement-situation.kotoba.edn), flagged
     :derived — never re-ingested as authoritative fact.

The canonical "current position" of a craft is the LATEST :craft.fix (max
observed-at). The full set of fixes IS the trajectory (非終末論 — appended,
never overwritten). ISO-8601 UTC timestamps sort lexically, so "latest" = max
string.

CONSTITUTIONAL framing (Charter Rider §2(a) force-separation + §2(d); mirrors
watatsuna G2): this is a SITUATIONAL-AWARENESS map, NEVER a person-surveillance
feed and NEVER a targeting feed. Output ranks lanes/chokepoints by live
concentration so traffic can be made SAFER and more resilient (ease congestion,
add redundancy, pre-stage response) — it does NOT follow a named individual,
build pattern-of-life, or identify where to intercept. A craft is a craft, not
a person (G4).

stdlib only (no numpy). Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from watatsuna
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
    craft, fixes, legs, lanes = {}, [], [], {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':craft/id' in r:
            craft[r[':craft/id']] = r
        elif ':craft.fix/id' in r:
            fixes.append(r)
        elif ':craft.leg/id' in r:
            legs.append(r)
        elif ':lane/id' in r:
            lanes[r[':lane/id']] = r
    return craft, fixes, legs, lanes


def analyze(craft, fixes, legs, lanes):
    # latest fix per craft (max observed-at; ISO-8601 sorts lexically)
    latest = {}  # craft id -> fix row
    for fx in fixes:
        c = fx[':craft.fix/craft']
        ts = fx.get(':craft.fix/observed-at', '')
        if c not in latest or ts > latest[c].get(':craft.fix/observed-at', ''):
            latest[c] = fx
    dataset_latest = max((fx.get(':craft.fix/observed-at', '') for fx in fixes), default='')

    kind_of = {c: craft[c].get(':craft/kind') for c in craft}

    # per-lane live load = distinct craft whose LATEST fix transits the lane, by kind
    lane_craft = defaultdict(set)
    lane_kind = defaultdict(lambda: defaultdict(set))
    for c, fx in latest.items():
        ln = fx.get(':craft.fix/lane')
        if ln is None:
            continue
        lane_craft[ln].add(c)
        lane_kind[ln][kind_of.get(c, ':unknown')].add(c)

    lane_load = {ln: len(cs) for ln, cs in lane_craft.items()}

    # chokepoint transit: lanes carrying a watatsuna chokepoint keyword (composes
    # with watatsuna static cable load over the same keyword)
    choke_transit = {}
    for ln, meta in lanes.items():
        cp = meta.get(':lane/chokepoint')
        if cp and ln in lane_craft:
            choke_transit[cp] = choke_transit.get(cp, 0) + len(lane_craft[ln])

    # approach congestion: lanes of kind :approach
    approach = {ln: lane_load[ln] for ln, meta in lanes.items()
                if meta.get(':lane/kind') == ':approach' and ln in lane_load}

    # fix-count per craft (trail richness)
    trail = defaultdict(int)
    for fx in fixes:
        trail[fx[':craft.fix/craft']] += 1

    # track freshness: craft whose latest fix is older than the dataset latest = stale tail
    stale = sorted(c for c, fx in latest.items()
                   if fx.get(':craft.fix/observed-at', '') < dataset_latest)

    kind_count = defaultdict(int)
    for c in craft:
        kind_count[kind_of.get(c, ':unknown')] += 1

    return dict(
        latest=latest, dataset_latest=dataset_latest, kind_of=kind_of,
        lane_craft=lane_craft, lane_kind=lane_kind, lane_load=lane_load,
        choke_transit=choke_transit, approach=approach, trail=trail,
        stale=stale, kind_count=kind_count,
    )


def render_report(craft, fixes, legs, lanes, a):
    L = []
    P = L.append
    P("# watari 渡り — live moving-craft (ship + aircraft) situational report")
    P("")
    P("> ADR-2606041827 · **aggregate-first** · SITUATIONAL-AWARENESS map (NOT a "
      "person-surveillance feed, NOT a target-list; Charter Rider §2(a) force-separation "
      "+ §2(d); mirrors watatsuna G2). A craft is a craft, never a person (G4). "
      "All sourcing `:representative` — bounded illustrative seed, NOT live coverage.")
    P("")
    nv = a['kind_count'].get(':vessel', 0)
    na = a['kind_count'].get(':aircraft', 0)
    P(f"- craft: **{len(craft)}** ({nv} vessels · {na} aircraft)  ·  position fixes: "
      f"**{len(fixes)}**  ·  lanes: **{len(lanes)}**  ·  legs: **{len(legs)}**")
    P(f"- dataset latest observation: **{a['dataset_latest']}**  ·  "
      f"craft current as-of this instant: **{len(a['latest']) - len(a['stale'])}** / "
      f"{len(a['latest'])} (freshness tail: {len(a['stale'])})")
    P("")

    # ── chokepoint transit (headline; composes with watatsuna) ──
    P("## Chokepoint transit — live vessel/craft concentration")
    P("")
    P("Distinct craft whose LATEST fix transits each maritime chokepoint. Composes with "
      "watatsuna's STATIC submarine-cable chokepoint load over the same keywords "
      "(ADR-2606012600) → one maritime resilience picture. **Routed to safety + "
      "redundancy, never to interdiction.**")
    P("")
    P("| chokepoint | craft transiting now |")
    P("|---|---:|")
    for cp in sorted(a['choke_transit'], key=lambda k: -a['choke_transit'][k]):
        P(f"| `{cp}` | {a['choke_transit'][cp]} |")
    P("")

    # ── lane load (all lanes, by kind) ──
    P("## Lane / corridor load — live concentration")
    P("")
    P("| lane | kind | craft | vessels | aircraft |")
    P("|---|---|---:|---:|---:|")
    for ln in sorted(a['lane_load'], key=lambda k: -a['lane_load'][k]):
        meta = lanes.get(ln, {})
        vk = len(a['lane_kind'][ln].get(':vessel', set()))
        ak = len(a['lane_kind'][ln].get(':aircraft', set()))
        P(f"| {meta.get(':lane/name', ln)} | `{meta.get(':lane/kind','?')}` "
          f"| {a['lane_load'][ln]} | {vk} | {ak} |")
    P("")

    # ── approach congestion ──
    P("## Port / airport approach congestion")
    P("")
    P("Craft holding in an approach lane — routed to congestion-easing + arrival "
      "sequencing + safety. NEVER a targeting output.")
    P("")
    if a['approach']:
        P("| approach | craft holding |")
        P("|---|---:|")
        for ln in sorted(a['approach'], key=lambda k: -a['approach'][k]):
            P(f"| {lanes.get(ln, {}).get(':lane/name', ln)} | {a['approach'][ln]} |")
    else:
        P("- (none in seed)")
    P("")

    # ── current position snapshot (as-of) ──
    P("## Current position snapshot (latest as-of fix per craft)")
    P("")
    P("| craft | kind | lat | lon | alt (m) | speed (kn) | as-of |")
    P("|---|---|---:|---:|---:|---:|---|")
    for c in sorted(a['latest'], key=lambda k: (a['kind_of'].get(k, ''), k)):
        fx = a['latest'][c]
        cm = craft.get(c, {})
        label = cm.get(':craft/name') or cm.get(':craft/callsign') or c
        alt = fx.get(':craft.fix/alt-m')
        P(f"| {label} | `{cm.get(':craft/kind','?')}` | {fx.get(':craft.fix/lat','?')} "
          f"| {fx.get(':craft.fix/lon','?')} | {alt if alt is not None else '—'} "
          f"| {fx.get(':craft.fix/speed-kn','?')} | {fx.get(':craft.fix/observed-at','?')} |")
    P("")

    # ── freshness tail ──
    P("## Freshness tail — craft NOT seen in the latest wave (honest gaps)")
    P("")
    P("Live coverage is never complete. These craft's latest fix predates the dataset "
      "latest; their position is stale, not current. No fabricated live coverage (G5).")
    P("")
    if a['stale']:
        for c in a['stale']:
            fx = a['latest'][c]
            cm = craft.get(c, {})
            label = cm.get(':craft/name') or cm.get(':craft/callsign') or c
            P(f"- {label} — last seen {fx.get(':craft.fix/observed-at','?')} "
              f"(dataset latest {a['dataset_latest']})")
    else:
        P("- (all craft current in seed)")
    P("")
    P("---")
    P("*Generated by `watari/methods/analyze.py`. HONEST: R0 bounded `:representative` "
      "seed; coordinates rounded to ~0.1°; timestamps illustrative, NOT a live capture; "
      "lane membership is seed-tagged. Live AIS (AISStream) + ADS-B (OpenSky/adsb.fi) "
      "ingest is G7 Council+operator gated. Public transponder broadcasts only; no "
      "person-tracking (G4).*")
    return "\n".join(L) + "\n"


def render_datoms(craft, lanes, a):
    L = []
    P = L.append
    P(";; watari — DERIVED movement-situation datoms (ADR-2606041827). :derived — NOT fact.")
    P(";; Recomputed from the seed graph; do not re-ingest as :authoritative.")
    P("[")
    for cp in sorted(a['choke_transit'], key=lambda k: -a['choke_transit'][k]):
        P(f' {{:movement/chokepoint "{cp}" :movement/chokepoint-transit {a["choke_transit"][cp]} '
          f':movement/derived true}}')
    for ln in sorted(a['lane_load'], key=lambda k: -a['lane_load'][k]):
        vk = len(a['lane_kind'][ln].get(':vessel', set()))
        ak = len(a['lane_kind'][ln].get(':aircraft', set()))
        P(f' {{:movement/lane "{ln}" :movement/lane-load {a["lane_load"][ln]} '
          f':movement/vessels {vk} :movement/aircraft {ak} :movement/derived true}}')
    for c in sorted(a['stale']):
        fx = a['latest'][c]
        P(f' {{:movement/craft "{c}" :movement/stale true '
          f':movement/last-seen "{fx.get(":craft.fix/observed-at","")}" :movement/derived true}}')
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "seed-craft-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    craft, fixes, legs, lanes = classify(rows)
    a = analyze(craft, fixes, legs, lanes)

    (outdir / "intel-report.md").write_text(
        render_report(craft, fixes, legs, lanes, a), encoding='utf-8')
    (outdir / "movement-situation.kotoba.edn").write_text(
        render_datoms(craft, lanes, a), encoding='utf-8')

    print(f"watari: {len(craft)} craft "
          f"({a['kind_count'].get(':vessel',0)} vessels, "
          f"{a['kind_count'].get(':aircraft',0)} aircraft), {len(fixes)} fixes, "
          f"{len(lanes)} lanes; latest {a['dataset_latest']}")
    top = sorted(a['choke_transit'], key=lambda k: -a['choke_transit'][k])[:3]
    if top:
        print("top chokepoint transit: " +
              ", ".join(f"{cp} {a['choke_transit'][cp]}" for cp in top))
    print(f"freshness tail: {len(a['stale'])} craft stale")
    print(f"wrote {outdir/'intel-report.md'} + {outdir/'movement-situation.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
