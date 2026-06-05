#!/usr/bin/env python3
"""hotaru 蛍 — III-V / InP open-publication substrate-commons analyzer.

ADR-2606051200 · vocabulary: iii-v-substrate-ontology.kotoba.edn (00-contracts/schemas/).

Reads a kotoba-EDN III-V substrate graph (:iiiv.material/* compounds, :iiiv.proc/*
open-publication process knowledge, :iiiv.crystal/* growth DESIGNS, :iiiv.wafer/*
SPECS, :iiiv.precursor/* materials + safety) and emits:

  1. an aggregate-first commons-readiness report (out/commons-readiness.md) — the
     per-stage open-publication coverage of the InP substrate chain
     (synthesis → bulk-growth → wafering → surface-prep), the :epitaxy GAP, the
     precursor-safety + conflict-mineral picture, and an HONEST verdict on the
     ADR-2605265500 §2 R4+ re-evaluation gate (which fabrication still fails).
  2. the derived readiness datoms (out/iii-v-readiness.kotoba.edn), flagged
     :derived — never re-ingested as authoritative fact (G5).

CONSTITUTIONAL framing (the invariants, enforced HERE as enforcement-point #3 of 3):
  G1 — every :iiiv.proc/source-license MUST be in the practiceable-open set
       {:academic-oa :patent-expired :textbook-public :standard-public :own-rnd}.
       Any other value (e.g. :vendor-proprietary) raises ValueError; the model
       cannot hold a proprietary MOCVD recipe → the graph stays a *commons*.
  G2 — every :iiiv.crystal/fabricated and :iiiv.wafer/fabricated MUST be false.
       A true value raises ValueError; the model is design/spec ONLY through R3.
       Live fabrication is unrepresentable until the ADR-2605265500 R4+ gate (Lv7+).
  G4 — any crystal consuming conflict-mineral In/Ga MUST declare :in-sourcing ∈
       {:recycled :conflict-free-attested}; :unverified is flagged (inherits
       hikari/himawari §G2).
  G3 — non-adjudicating: hotaru reports commons coverage; it does NOT decide the
       2605265500 gate (Council does). It states the facts that bear on it.

stdlib only (no numpy). EDN reader ported from nusa. Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import Counter, defaultdict

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from nusa
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()

# G1: the ONLY practiceable-open licenses. Anything else is a charter violation
# (the graph would stop being a commons). Mirrors nusa ALLOWED_THC_CLASSES.
ALLOWED_LICENSES = (
    ":academic-oa", ":patent-expired", ":textbook-public", ":standard-public", ":own-rnd",
)
# G4: conflict-mineral In/Ga sourcing that satisfies the gate.
CLEAN_SOURCING = (":recycled", ":conflict-free-attested")

# The substrate chain hotaru's scope COVERS (生成 + 製造 of the substrate). :epitaxy
# is deliberately NOT here — it is the vendor-IP-dense stage ADR-2605265500 §2 keeps
# prohibited; hotaru tracks it only as a gap.
SUBSTRATE_STAGES = (":synthesis", ":bulk-growth", ":wafering", ":surface-prep")
EPITAXY_STAGE = ":epitaxy"


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
            v = _parse(it)
            out[k] = v
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text: str):
    return _parse(_tokens(text))


def load_edn(path: pathlib.Path):
    return read_edn(path.read_text(encoding='utf-8'))


# ── classify the flat datom vector into entity buckets
def classify(rows):
    materials, procs, crystals, wafers, precursors = {}, {}, {}, {}, {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':iiiv.material/id' in r:
            materials[r[':iiiv.material/id']] = r
        elif ':iiiv.proc/id' in r:
            procs[r[':iiiv.proc/id']] = r
        elif ':iiiv.crystal/id' in r:
            crystals[r[':iiiv.crystal/id']] = r
        elif ':iiiv.wafer/id' in r:
            wafers[r[':iiiv.wafer/id']] = r
        elif ':iiiv.precursor/id' in r:
            precursors[r[':iiiv.precursor/id']] = r
    return materials, procs, crystals, wafers, precursors


def screen_licenses(procs):
    """G1 enforcement point #3: refuse any process whose source-license is not
    practiceable-open. Raises ValueError so the analyzer cannot silently render a
    graph that includes a proprietary recipe (which would void the 'commons' claim)."""
    for pid, p in procs.items():
        lic = p.get(':iiiv.proc/source-license')
        if lic not in ALLOWED_LICENSES:
            raise ValueError(
                f"G1 violation: process {pid!r} has :source-license {lic!r}; only "
                f"{ALLOWED_LICENSES} are permitted (hotaru is an OPEN-PUBLICATION commons; "
                f"vendor-proprietary / patent-active / trade-secret recipes are excluded "
                f"by construction, per ADR-2605265500 §2)."
            )


def screen_fabrication(crystals, wafers):
    """G2 enforcement point #3: refuse any crystal/wafer marked fabricated. Raises
    ValueError — the model is design/spec ONLY through R3; physical fabrication is
    unrepresentable until the ADR-2605265500 R4+ gate (Council Lv7+)."""
    for cid, c in crystals.items():
        if c.get(':iiiv.crystal/fabricated') is not False:
            raise ValueError(
                f"G2 violation: crystal {cid!r} has :fabricated "
                f"{c.get(':iiiv.crystal/fabricated')!r}; only false is permitted "
                f"(III-V fabrication PROHIBITED through R3, ADR-2605265500 §2)."
            )
    for wid, w in wafers.items():
        if w.get(':iiiv.wafer/fabricated') is not False:
            raise ValueError(
                f"G2 violation: wafer {wid!r} has :fabricated "
                f"{w.get(':iiiv.wafer/fabricated')!r}; only false is permitted."
            )


def stage_coverage(procs):
    """Per substrate stage: is it covered by ≥1 :open-mature process? Returns
    (per_stage_dict, covered_count, total_substrate_stages)."""
    by_stage = defaultdict(list)
    for p in procs.values():
        by_stage[p.get(':iiiv.proc/stage')].append(p)
    per_stage = {}
    for st in SUBSTRATE_STAGES:
        ps = by_stage.get(st, [])
        mature = [p for p in ps if p.get(':iiiv.proc/maturity') == ':open-mature']
        emerging = [p for p in ps if p.get(':iiiv.proc/maturity') == ':open-emerging']
        per_stage[st] = {
            'n': len(ps), 'mature': len(mature), 'emerging': len(emerging),
            'covered': len(mature) >= 1,
        }
    covered = sum(1 for st in SUBSTRATE_STAGES if per_stage[st]['covered'])
    epitaxy = by_stage.get(EPITAXY_STAGE, [])
    epitaxy_mature = any(p.get(':iiiv.proc/maturity') == ':open-mature' for p in epitaxy)
    return per_stage, covered, len(SUBSTRATE_STAGES), {
        'n': len(epitaxy), 'open_mature': epitaxy_mature,
    }


def conflict_mineral_screen(crystals, precursors):
    """G4: which precursor elements are conflict-mineral; which crystals consume one
    without a clean :in-sourcing attestation."""
    cm_elements = {p.get(':iiiv.precursor/formula') for p in precursors.values()
                   if p.get(':iiiv.precursor/conflict-mineral') is True}
    # Every crystal in this seed is InP (uses In, a conflict-mineral). Flag any whose
    # in-sourcing is not in CLEAN_SOURCING.
    flagged = {cid: c.get(':iiiv.crystal/in-sourcing')
               for cid, c in crystals.items()
               if c.get(':iiiv.crystal/in-sourcing') not in CLEAN_SOURCING}
    return cm_elements, flagged


def analyze(materials, procs, crystals, wafers, precursors):
    screen_licenses(procs)            # raises on non-open license
    screen_fabrication(crystals, wafers)  # raises on fabricated=true

    per_stage, covered, total, epitaxy = stage_coverage(procs)
    cm_elements, cm_flagged = conflict_mineral_screen(crystals, precursors)

    license_breakdown = Counter(p.get(':iiiv.proc/source-license') for p in procs.values())
    direct_materials = [m for m in materials.values()
                        if m.get(':iiiv.material/bandgap-type') == ':direct']

    # the R4+ gate (ADR-2605265500 §2) is satisfiable only if the WHOLE chain incl.
    # epitaxy is an open-mature commons. hotaru reports; Council decides (G3).
    substrate_commons_ready = (covered == total)
    r4_gate_satisfiable = substrate_commons_ready and epitaxy['open_mature']

    return dict(
        per_stage=per_stage, covered=covered, total=total, epitaxy=epitaxy,
        cm_elements=cm_elements, cm_flagged=cm_flagged,
        license_breakdown=license_breakdown, direct_materials=direct_materials,
        substrate_commons_ready=substrate_commons_ready,
        r4_gate_satisfiable=r4_gate_satisfiable,
    )


def render_report(materials, procs, crystals, wafers, precursors, a):
    L = []
    P = L.append
    P("# hotaru 蛍 — III-V / InP substrate open-commons readiness report")
    P("")
    P("> ADR-2606051200 · **aggregate-first** · open-publication commons framing. "
      "OPEN-PUBLICATION process knowledge ONLY — vendor-proprietary recipes are "
      "unrepresentable (`:source-license` invariant, G1); crystals + wafers are "
      "design/spec only (`:fabricated false`, G2); III-V **fabrication remains "
      "PROHIBITED through R3 per ADR-2605265500 §2** — this report does NOT change "
      "that (G3, non-adjudicating). All sourcing `:representative` (G5/G7).")
    P("")
    P(f"- materials: **{len(materials)}** ({len(a['direct_materials'])} direct-bandgap) "
      f" ·  open-publication processes: **{len(procs)}**  ·  crystal designs: "
      f"**{len(crystals)}**  ·  wafer specs: **{len(wafers)}**  ·  precursors: "
      f"**{len(precursors)}**")
    P("")

    # ── headline: substrate-chain commons coverage ──
    P("## Substrate-chain commons coverage (生成 → 製造)")
    P("")
    P("Each stage is *covered* when ≥1 `:open-mature` process exists in the commons. "
      "`:epitaxy` is deliberately out of hotaru's substrate scope — it is the "
      "vendor-IP-dense device stage ADR-2605265500 §2 keeps prohibited, tracked here "
      "only as a gap.")
    P("")
    P("| stage | processes | open-mature | open-emerging | covered |")
    P("|---|---:|---:|---:|:---:|")
    stage_label = {":synthesis": "synthesis (合成)", ":bulk-growth": "bulk-growth (単結晶育成)",
                   ":wafering": "wafering (ウェハ加工)", ":surface-prep": "surface-prep (エピ面)"}
    for st in SUBSTRATE_STAGES:
        s = a['per_stage'][st]
        P(f"| {stage_label[st]} | {s['n']} | {s['mature']} | {s['emerging']} | "
          f"{'✅' if s['covered'] else '❌'} |")
    ep = a['epitaxy']
    P(f"| epitaxy (エピtaxy — OUT of scope) | {ep['n']} | "
      f"{'≥1' if ep['open_mature'] else '0 (gap)'} | — | "
      f"{'✅' if ep['open_mature'] else '⛔ gap'} |")
    P("")
    P(f"- **substrate commons readiness**: {a['covered']}/{a['total']} stages open-mature → "
      f"**{'READY' if a['substrate_commons_ready'] else 'INCOMPLETE'}**")
    P("")

    # ── the ADR-2605265500 R4+ gate verdict (the honest headline) ──
    P("## ADR-2605265500 §2 R4+ re-evaluation gate")
    P("")
    P("The gate opens III-V *fabrication* re-evaluation only when an open-source III-V "
      "**wafer + epitaxy** IP commons exists. hotaru reports the two legs; Council decides.")
    P("")
    P(f"- substrate (wafer) commons leg: **{'READY' if a['substrate_commons_ready'] else 'INCOMPLETE'}**")
    P(f"- epitaxy commons leg: **{'READY' if a['epitaxy']['open_mature'] else 'GAP — vendor-proprietary'}**")
    P(f"- **R4+ gate satisfiable from the commons alone**: **{a['r4_gate_satisfiable']}** "
      f"→ fabrication stays PROHIBITED through R3 (unchanged). The binding gap is "
      f"**epitaxy/device stack-up**, not substrate growth.")
    P("")

    # ── license provenance (G1 signal) ──
    P("## Process provenance (G1 invariant)")
    P("")
    P("Every process is practiceable-open. `:vendor-proprietary` is not a representable "
      "license — the data model cannot hold a proprietary recipe.")
    P("")
    P("| source-license | processes |")
    P("|---|---:|")
    for lic in sorted(a['license_breakdown']):
        P(f"| `{lic}` | {a['license_breakdown'][lic]} |")
    P("")

    # ── conflict-mineral sourcing (G4) ──
    P("## Conflict-mineral sourcing (G4 — inherits hikari/himawari §G2)")
    P("")
    cm = ", ".join(sorted(e for e in a['cm_elements']))
    P(f"- conflict-mineral elements in precursor set: **{cm or '—'}**")
    P(f"- crystal designs consuming a conflict-mineral element WITHOUT clean "
      f"`:in-sourcing`: **{len(a['cm_flagged'])}**"
      + ("" if not a['cm_flagged'] else f" → {sorted(a['cm_flagged'])}"))
    P("")
    P("| precursor | formula | hazard | conflict-mineral | export-control |")
    P("|---|---|---|:---:|---|")
    for pid in sorted(precursors):
        p = precursors[pid]
        cmf = "⚠️ yes" if p.get(':iiiv.precursor/conflict-mineral') else "no"
        P(f"| {p.get(':iiiv.precursor/name', pid)} | `{p.get(':iiiv.precursor/formula')}` | "
          f"`{p.get(':iiiv.precursor/hazard-class')}` | {cmf} | "
          f"`{p.get(':iiiv.precursor/export-control')}` |")
    P("")
    P("> PH₃ (phosphine) is acute-toxic + pyrophoric; In/Ga are conflict-minerals "
      "(In/Ga explicitly barred from hikari/himawari panel sourcing) and Ga carries "
      "EAR export controls. Any live process is Council Lv7+ + operator gated (G8/G6).")
    P("")
    P("> hotaru builds the commons; it does not grow a crystal. The light-emitting "
      "III-V substrate (蛍, direct-bandgap) is the sibling of the iwakura/fuigo "
      "indirect-bandgap silicon track (ADR-2605242500). Fabrication is the Council's "
      "decision (G3), gated by ADR-2605265500 §2 — not this report.")
    P("")
    return "\n".join(L)


def render_datoms(materials, procs, crystals, wafers, a):
    L = []
    P = L.append
    P(";; hotaru 蛍 — DERIVED readiness datoms (ADR-2606051200)")
    P(";; :derived — analyzer output, NOT re-ingested as authoritative fact (G5).")
    P("[")
    for st in SUBSTRATE_STAGES:
        s = a['per_stage'][st]
        P(f' {{:hotaru.derived/stage {st} :hotaru.derived/covered {str(s["covered"]).lower()} '
          f':hotaru.derived/open-mature {s["mature"]} :hotaru.derived/sourcing :derived}}')
    P(f' {{:hotaru.derived/substrate-commons-ready {str(a["substrate_commons_ready"]).lower()} '
      f':hotaru.derived/r4-gate-satisfiable {str(a["r4_gate_satisfiable"]).lower()} '
      f':hotaru.derived/conflict-flagged {len(a["cm_flagged"])} :hotaru.derived/sourcing :derived}}')
    P("]")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here.parent / "data" / "seed-iii-v-substrate.kotoba.edn"
    out = here / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    materials, procs, crystals, wafers, precursors = classify(rows)
    a = analyze(materials, procs, crystals, wafers, precursors)

    report = render_report(materials, procs, crystals, wafers, precursors, a)
    datoms = render_datoms(materials, procs, crystals, wafers, a)
    (out / "commons-readiness.md").write_text(report, encoding='utf-8')
    (out / "iii-v-readiness.kotoba.edn").write_text(datoms, encoding='utf-8')

    print(f"hotaru: {len(procs)} open processes, substrate {a['covered']}/{a['total']} stages "
          f"open-mature → commons {'READY' if a['substrate_commons_ready'] else 'INCOMPLETE'}; "
          f"epitaxy {'open' if a['epitaxy']['open_mature'] else 'GAP'}; "
          f"R4+ gate satisfiable={a['r4_gate_satisfiable']} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
