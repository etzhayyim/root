#!/usr/bin/env python3
"""maps — static-feature substrate coverage analyzer (kotoba-native, R0).

ADR-2606064500. Reads a kotoba-EDN static-feature graph (:feature/* placed features,
:feature.rel/* topology edges, :geo.alias/* multi-scheme region identity) and emits an
AGGREGATE-FIRST coverage report — directly answering *「地球上の 3D 空間を kami engine で
表示して、いまどれぐらい coverage できているか」*: how many features the kotoba substrate
holds, per label, and what slice of the Earth they actually cover.

The coverage surface is reported two ways:
  1. by H3 res-6 cell (the honest planet-scale unit: ~14.1 M res-6 cells tile the whole Earth,
     so "N res-6 cells touched / 14 117 882" is a literal fraction-of-Earth-loaded). Uses real H3
     when an `h3` python package is importable; otherwise falls back to a documented ~1°
     lat/lon degree-grid approximation, flagged honestly in the report (G3 — no fabricated
     precision).
  2. by geographic bbox + densest-cell hot spot — the localized anchor (Tokyo Station today).

This is the STATIC counterpart to watari's live moving-craft analyzer (ADR-2606041827); both
read the kotoba Datom log, never RisingWave.

stdlib only (real H3 used only if `h3` happens to be installed). Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, math, pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from watari ──
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


# ── classify the flat datom vector into entity buckets ──
def classify(rows):
    features, rels, aliases = {}, [], {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':feature/id' in r:
            features[r[':feature/id']] = r
        elif ':feature.rel/id' in r:
            rels.append(r)
        elif ':geo.alias/id' in r:
            aliases[r[':geo.alias/id']] = r
    return features, rels, aliases


# ── H3 res-6 cell id, real if `h3` is installed else a documented degree-grid stand-in ──
def _cell_r6(lat, lon):
    try:
        import h3  # optional; only present in environments that pip-installed it
        try:
            return ("h3", h3.latlng_to_cell(lat, lon, 6))      # h3 >= 4
        except AttributeError:
            return ("h3", h3.geo_to_h3(lat, lon, 6))           # h3 == 3
    except Exception:
        # ~1° degree grid: NOT an H3 cell — an honest coarse stand-in so coverage still
        # computes stdlib-only. Flagged in the report (G3). res-6 edge ≈3.2 km; a 1° bin is
        # coarser, so this UNDER-counts distinct cells (conservative, never inflates coverage).
        return ("deg", f"deg/{math.floor(lat)}/{math.floor(lon)}")


# ── res-r cells that tile the whole Earth (exact H3 count) — the coverage denominator ──
# H3: res r has 2 + 120*7^r cells (res 6 = 14,117,882). Exact formula → honest at any res.
def _h3_cells_at_res(r):
    return 2 + 120 * (7 ** r)


def analyze(features, rels, aliases):
    label_count = defaultdict(int)
    cells_r6 = set()
    cell_mode = None
    lats, lons = [], []
    # densest res-8-ish hot spot via ~0.01° bin (anchor density, no h3 needed)
    hot = defaultdict(int)
    h3_buildings = 0
    for fid, f in features.items():
        label_count[f.get(':feature/label', ':unknown')] += 1
        lat, lon = f.get(':feature/lat'), f.get(':feature/lon')
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            lats.append(lat)
            lons.append(lon)
            mode, cid = _cell_r6(lat, lon)
            cell_mode = mode
            cells_r6.add(cid)
            hot[(round(lat, 2), round(lon, 2))] += 1
        if f.get(':feature/label') == ':building':
            h3_buildings += 1

    bbox = None
    if lats:
        bbox = dict(south=min(lats), north=max(lats), west=min(lons), east=max(lons))
    densest = max(hot.items(), key=lambda kv: kv[1]) if hot else None

    sourcing = defaultdict(int)
    for f in features.values():
        sourcing[f.get(':feature/sourcing', ':unknown')] += 1

    return dict(
        n_features=len(features), label_count=label_count, n_rels=len(rels),
        n_aliases=len(aliases), cells_r6=cells_r6, cell_mode=cell_mode, bbox=bbox,
        densest=densest, sourcing=sourcing, n_buildings=h3_buildings,
    )


def render_report(features, a):
    L = []
    P = L.append
    P("# maps — static-feature substrate coverage report (kotoba-native)")
    P("")
    P("> ADR-2606064500 · **aggregate-first** · the kotoba Datom log successor to the legacy "
      "RisingWave `vertex_spatial`. Answers *「いまどれぐらい coverage できているか」*: what the "
      "substrate holds and what slice of the Earth it covers. All sourcing `:representative` — "
      "a bounded anchor seed, NOT planet-scale coverage (G3: absence = not-yet-ingested).")
    P("")
    P(f"- features: **{a['n_features']}**  ·  topology edges: **{a['n_rels']}**  ·  "
      f"geo-aliases: **{a['n_aliases']}**  ·  buildings (3D-extrudable): **{a['n_buildings']}**")
    den = _h3_cells_at_res(6)
    mode_note = ("real H3" if a['cell_mode'] == 'h3'
                 else "~1° degree-grid stand-in (h3 not installed — coarse, UNDER-counts; "
                      "install `h3` for true res-6)")
    frac = len(a['cells_r6']) / den
    P(f"- Earth coverage @ res-6: **{len(a['cells_r6'])}** distinct cells touched "
      f"/ {den:,} total ({mode_note}) ≈ **{frac:.2e}** of the planet's res-6 tiling")
    if a['bbox']:
        b = a['bbox']
        P(f"- geographic footprint: lat [{b['south']:.3f}, {b['north']:.3f}] · "
          f"lon [{b['west']:.3f}, {b['east']:.3f}]")
    if a['densest']:
        (la, lo), n = a['densest']
        P(f"- densest hot spot: **{n}** features at ≈({la}, {lo}) — the localized anchor")
    P("")

    # ── by label ──
    P("## Features by label (what the substrate actually holds)")
    P("")
    P("| label | count |")
    P("|---|---:|")
    for lab in sorted(a['label_count'], key=lambda k: -a['label_count'][k]):
        P(f"| `{lab}` | {a['label_count'][lab]} |")
    P("")

    # ── sourcing honesty ──
    P("## Sourcing (G3 honesty)")
    P("")
    P("| sourcing | count |")
    P("|---|---:|")
    for s in sorted(a['sourcing'], key=lambda k: -a['sourcing'][k]):
        P(f"| `{s}` | {a['sourcing'][s]} |")
    P("")

    P("---")
    P("*Generated by `maps/methods/analyze.py` (stdlib; real H3 only if `h3` is installed). "
      "HONEST R0: bounded `:representative` anchor seed (Tokyo Station), NOT a live "
      "planet-scale ingest. The H3 res-6 fraction is literal-but-tiny by design — this seed "
      "demonstrates the kotoba `:feature/*` model + AVET cell index, it does NOT claim Earth "
      "coverage. Backfilling the real `vertex_spatial` export (ingest.py) grows this number; "
      "the 3D walker's loaded extent is unchanged by the substrate swap (ADR-2606064500 §"
      "Honest R0).*")
    return "\n".join(L) + "\n"


def render_datoms(a):
    L = []
    P = L.append
    P(";; maps — DERIVED coverage datoms (ADR-2606064500). :derived — NOT fact.")
    P(";; Recomputed from the seed graph; do not re-ingest as :authoritative.")
    P("[")
    P(f' {{:coverage/feature-count {a["n_features"]} :coverage/derived true}}')
    P(f' {{:coverage/cell-count-r6 {len(a["cells_r6"])} :coverage/cell-mode "{a["cell_mode"]}" '
      f':coverage/derived true}}')
    if a['bbox']:
        b = a['bbox']
        P(f' {{:coverage/bbox-south {b["south"]} :coverage/bbox-north {b["north"]} '
          f':coverage/bbox-west {b["west"]} :coverage/bbox-east {b["east"]} :coverage/derived true}}')
    if a['densest']:
        (la, lo), n = a['densest']
        P(f' {{:coverage/anchor-density {n} :coverage/anchor-lat {la} :coverage/anchor-lon {lo} '
          f':coverage/derived true}}')
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "seed-spatial-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    features, rels, aliases = classify(rows)
    a = analyze(features, rels, aliases)

    (outdir / "coverage-report.md").write_text(render_report(features, a), encoding='utf-8')
    (outdir / "coverage.kotoba.edn").write_text(render_datoms(a), encoding='utf-8')

    print(f"maps: {a['n_features']} features, {a['n_rels']} edges, {a['n_aliases']} aliases; "
          f"{len(a['cells_r6'])} res-6 cells touched ({a['cell_mode']})")
    top = sorted(a['label_count'], key=lambda k: -a['label_count'][k])[:4]
    print("top labels: " + ", ".join(f"{lab} {a['label_count'][lab]}" for lab in top))
    print(f"wrote {outdir/'coverage-report.md'} + {outdir/'coverage.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
