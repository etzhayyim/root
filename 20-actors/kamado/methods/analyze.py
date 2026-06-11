#!/usr/bin/env python3
"""kamado 竈 — refining-graph analyzer (observation + transition + carbon).

ADR-2606051500 · vocabulary: refining-ontology.kotoba.edn (00-contracts/schemas/).

Reads a kotoba-EDN refining graph (:refinery/* observed assets, :decommission/* §2(d)
robotics plans, :synthesis/* closed-loop designs) and emits an aggregate-first report:

  1. observation face A — refinery/unit/outage registry + transition-readiness rollup
     (the kotoba-native successor to the legacy `oil-refining` Cypher actor). A
     resilience + transition map, NEVER a target-list (G4).
  2. decommission face B — §2(d) wind-down/convert plans, each screened by the G3
     intervention guard (convert/decommission/remediate/monitor only).
  3. synthesis face C — closed-loop designs, each screened by the G1 feedstock guard and
     scored against D3 (net atmospheric carbon Δ ≤ tolerance) via carbon_balance.

CONSTITUTIONAL framing (the honest thesis, made structural):
  G1 — every :synthesis/feedstock-class is a closed-loop carbon source; a fossil feedstock
       raises ValueError (feedstock_guard) — kamado cannot render a fossil-fed design.
  G2 — every synthesis design must pass D3 (carbon_balance). G3 — interventions on existing
       fossil assets are wind-down/convert only. G4 — non-adjudicating, aggregate-first,
       never a target-list. G7 — all sourcing :representative.

stdlib only. Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import Counter, defaultdict

import carbon_balance as cb
from feedstock_guard import screen_feedstock, screen_intervention

# ── minimal EDN reader (subset) — ported from nusa/watatsuna ─────────────────
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()


def _tokens(s):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t in ('true', 'false'):
        return t == 'true'
    if t == 'nil':
        return None
    if t.startswith(':'):
        return t
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
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text):
    return _parse(_tokens(text))


def load_edn(path):
    return read_edn(pathlib.Path(path).read_text(encoding='utf-8'))


# ── classify the flat datom vector ───────────────────────────────────────────
def classify(rows):
    refineries, units, outages, decoms, synths = {}, {}, {}, {}, {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':refinery/id' in r:
            refineries[r[':refinery/id']] = r
        elif ':unit/id' in r:
            units[r[':unit/id']] = r
        elif ':outage/id' in r:
            outages[r[':outage/id']] = r
        elif ':decommission/id' in r:
            decoms[r[':decommission/id']] = r
        elif ':synthesis/id' in r:
            synths[r[':synthesis/id']] = r
    return refineries, units, outages, decoms, synths


# map the EDN synthesis record → a carbon_balance.Pathway
def _pathway(sid, s):
    apc = s.get(':synthesis/control') in (':supervised-autonomy', ':teleop')
    return cb.Pathway(
        name=sid,
        feedstock=s.get(':synthesis/feedstock-class'),
        energy=s.get(':synthesis/energy'),
        fate=s.get(':synthesis/product-fate'),
        apc=apc,
    )


def analyze(refineries, units, outages, decoms, synths):
    # G3: every decommission plan is a permitted wind-down/convert intervention
    for did, d in decoms.items():
        screen_intervention(d.get(':decommission/intervention'), ctx=did)
    # G5 invariants on every plan
    decom_keyless = all(
        d.get(':decommission/server-held-key') is False
        and d.get(':decommission/outward-gated') is True
        for d in decoms.values()
    )

    # G1 + G2: every synthesis design has a representable feedstock AND passes D3
    syn_results = {}
    for sid, s in synths.items():
        screen_feedstock(s.get(':synthesis/feedstock-class'), ctx=sid)  # G1, raises on fossil
        syn_results[sid] = cb.balance(_pathway(sid, s))

    units_by_ref = defaultdict(list)
    for uid, u in units.items():
        units_by_ref[u.get(':unit/refinery')].append(uid)

    return dict(
        readiness=Counter(r.get(':refinery/transition-readiness') for r in refineries.values()),
        status=Counter(r.get(':refinery/status') for r in refineries.values()),
        units_by_ref=units_by_ref,
        unit_kinds=Counter(u.get(':unit/kind') for u in units.values()),
        decom_keyless=decom_keyless,
        convert_targets=Counter(d.get(':decommission/convert-to') for d in decoms.values()),
        syn_results=syn_results,
        syn_pass=sum(1 for b in syn_results.values() if b['passes_d3']),
    )


def render(refineries, units, outages, decoms, synths, a):
    L = []
    P = L.append
    P("# kamado 竈 — refining observation + transition + carbon report")
    P("")
    P("> ADR-2606051500 · **aggregate-first** · a resilience + **transition** map, NEVER a "
      "target-list (G4). Observation ≠ operation. The kotoba-native successor to the legacy "
      "`oil-refining` Cypher actor (no RisingWave). All sourcing `:representative`.")
    P("")
    P(f"- observed refineries: **{len(refineries)}**  ·  units: **{len(units)}**  "
      f"·  outages: **{len(outages)}**  ·  §2(d) plans: **{len(decoms)}**  "
      f"·  closed-loop synthesis designs: **{len(synths)}**")
    P("")

    P("## A. Observed assets — status + transition-readiness (face A)")
    P("")
    P("| readiness | refineries |")
    P("|---|---:|")
    for k in sorted(a['readiness'], key=lambda x: x or ""):
        P(f"| `{k}` | {a['readiness'][k]} |")
    P("")
    P("| refinery | country | operator | status | readiness | units |")
    P("|---|---|---|---|---|---:|")
    for rid in sorted(refineries):
        r = refineries[rid]
        P(f"| {r.get(':refinery/name', rid)} | {r.get(':refinery/country')} | "
          f"`{r.get(':refinery/operator')}` | `{r.get(':refinery/status')}` | "
          f"`{r.get(':refinery/transition-readiness')}` | {len(a['units_by_ref'].get(rid, []))} |")
    P("")

    P("## B. §2(d) decommission / transition robotics (face B)")
    P("")
    P("Existing fossil assets may only be wound down or converted — the G3 intervention "
      "guard refuses `:expand` / `:restart-fossil`. Every plan is server-keyless (G5) and "
      "outward-gated (G8).")
    P("")
    P(f"- server-keyless + outward-gated on all plans: **{a['decom_keyless']}**")
    P("")
    P("| plan | refinery | intervention | robot | convert-to | principal |")
    P("|---|---|---|---|---|---|")
    for did in sorted(decoms):
        d = decoms[did]
        P(f"| `{did}` | {d.get(':decommission/refinery')} | `{d.get(':decommission/intervention')}` | "
          f"`{d.get(':decommission/robot-class')}` | `{d.get(':decommission/convert-to')}` | "
          f"`{d.get(':decommission/principal')}` |")
    P("")

    P("## C. Closed-loop synthesis — D3 carbon ledger (face C)")
    P("")
    P(f"Every design's feedstock is closed-loop carbon (G1; a fossil feedstock is not "
      f"representable). D3 = net atmospheric Δ ≤ {cb.D3_TOLERANCE} tCO2e/t. "
      f"**{a['syn_pass']}/{len(synths)}** designs pass D3.")
    P("")
    P("| design | feedstock | energy | fate | net tCO2e/t | D3? |")
    P("|---|---|---|---|---:|:---:|")
    for sid in sorted(synths):
        s = synths[sid]
        b = a['syn_results'][sid]
        P(f"| `{sid}` | `{s.get(':synthesis/feedstock-class')}` | "
          f"`{s.get(':synthesis/energy')}` | `{s.get(':synthesis/product-fate')}` | "
          f"**{b['net']:+.2f}** | {'✅' if b['passes_d3'] else '❌'} |")
    P("")
    P("> The fossil baseline (+3.50 tCO2e/t) is **not in this table** — it is not a "
      "representable kamado design. See `carbon_balance.py` for why robotics/control cannot "
      "close that gap (it only trims the ~11% process slice); the feedstock change does.")
    P("")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    seed = argv[1] if len(argv) > 1 and not argv[1].startswith('--') \
        else here.parent / "data" / "seed-refinery-graph.kotoba.edn"
    out = here / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    refineries, units, outages, decoms, synths = classify(rows)
    a = analyze(refineries, units, outages, decoms, synths)
    report = render(refineries, units, outages, decoms, synths, a)
    (out / "intel-report.md").write_text(report, encoding='utf-8')

    print(f"kamado: {len(refineries)} refineries, {len(decoms)} §2(d) plans, "
          f"{len(synths)} synthesis designs ({a['syn_pass']} pass D3) → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
