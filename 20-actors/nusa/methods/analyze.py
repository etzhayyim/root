#!/usr/bin/env python3
"""nusa 幣 — ritual/industrial hemp heritage analyzer.

ADR-2606039800 · vocabulary: ritual-hemp-ontology.kotoba.edn (00-contracts/schemas/).

Reads a kotoba-EDN ritual-hemp heritage graph (:hemp/* low-THC cultivars, :rite/*
purification artifacts, :rite.event/* ceremonies, :imbe/* provisioning lineage,
:hemp.license/* cultivation-revival design) and emits:

  1. an aggregate-first heritage report (out/heritage-report.md) — the rites, the
     Imbe/aratae tradition, the cultivar THC-class breakdown, and the now-open
     low-THC licensed-cultivation space — framed toward heritage + 祓い/清め, never
     toward recreational use or 解禁 advocacy.
  2. the derived heritage datoms (out/ritual-hemp-graph.kotoba.edn), flagged
     :derived — never re-ingested as authoritative fact.

CONSTITUTIONAL framing:
  G1 — every :hemp/* cultivar MUST be :thc-class :fiber | :low-thc. Any other class
       is REJECTED (raises ValueError); the data model + this analyzer cannot
       represent a recreational catalog. (Enforcement point #3 of 3.)
  G2 — no consumption/dosing output. G3 — non-adjudicating: legislative facts are
       recorded as facts; no 推進/反対 stance. G7 — all sourcing :representative.

stdlib only (no numpy). Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import Counter, defaultdict

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from watatsuna
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()

# G1: the ONLY permitted hemp THC classes. Anything else is a charter violation.
ALLOWED_THC_CLASSES = (":fiber", ":low-thc")


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


def read_edn(text: str):
    return _parse(_tokens(text))


def load_edn(path: pathlib.Path):
    return read_edn(path.read_text(encoding='utf-8'))


# ── classify the flat datom vector into entity buckets
def classify(rows):
    hemp, rites, events, imbe, licenses = {}, {}, {}, {}, {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':hemp/id' in r:
            hemp[r[':hemp/id']] = r
        elif ':rite/id' in r:
            rites[r[':rite/id']] = r
        elif ':rite.event/id' in r:
            events[r[':rite.event/id']] = r
        elif ':imbe/id' in r:
            imbe[r[':imbe/id']] = r
        elif ':hemp.license/id' in r:
            licenses[r[':hemp.license/id']] = r
    return hemp, rites, events, imbe, licenses


def screen_thc(hemp):
    """G1 enforcement point #3: refuse any cultivar that is not fibre/low-THC.

    Returns the cultivar THC-class breakdown. Raises ValueError on a prohibited
    class so the analyzer cannot silently render a recreational catalog.
    """
    breakdown = Counter()
    for hid, h in hemp.items():
        cls = h.get(':hemp/thc-class')
        if cls not in ALLOWED_THC_CLASSES:
            raise ValueError(
                f"G1 violation: cultivar {hid!r} has :thc-class {cls!r}; "
                f"only {ALLOWED_THC_CLASSES} are permitted (nusa is fibre/ritual-only, "
                f"recreational/high-THC excluded by construction)."
            )
        breakdown[cls] += 1
    return breakdown


def analyze(hemp, rites, events, imbe, licenses):
    thc_breakdown = screen_thc(hemp)

    # rite → fibre source coverage
    rite_fiber = {
        rid: [c for c in (r.get(':rite/uses-cultivar') or []) if c in hemp]
        for rid, r in rites.items()
    }
    # which rites each cultivar supplies
    cultivar_rites = defaultdict(set)
    for rid, cs in rite_fiber.items():
        for c in cs:
            cultivar_rites[c].add(rid)

    # licence design: only fibre/low-THC cultivars (must already hold by G1)
    licence_clean = {
        lid: lc for lid, lc in licenses.items()
        if hemp.get(lc.get(':hemp.license/cultivar'), {}).get(':hemp/thc-class') in ALLOWED_THC_CLASSES
    }
    # G4/G5/G8 invariants present on every licence design
    licence_invariants_ok = all(
        lc.get(':hemp.license/licensee-principal') == ':member'
        and lc.get(':hemp.license/funding') == ':member-okaimono'
        and lc.get(':hemp.license/server-held-key') is False
        and lc.get(':hemp.license/outward-gated') is True
        for lc in licence_clean.values()
    )

    purification = sum(1 for r in rites.values() if r.get(':rite/purpose') == ':purification')

    return dict(
        thc_breakdown=thc_breakdown,
        rite_fiber=rite_fiber,
        cultivar_rites=cultivar_rites,
        licence_clean=licence_clean,
        licence_invariants_ok=licence_invariants_ok,
        purification=purification,
    )


def render_report(hemp, rites, events, imbe, licenses, a):
    L = []
    P = L.append
    P("# nusa 幣 — ritual/industrial hemp heritage report")
    P("")
    P("> ADR-2606039800 · **aggregate-first** · heritage + 祓い/清め framing. "
      "Fibre + ritual + low-THC cultivation ONLY — recreational THC excluded by the "
      "`:thc-class` invariant (G1); no 解禁 推進/反対 stance (G3); cannabis-derived "
      "medicine out of scope (G10). All sourcing `:representative` — bounded illustrative "
      "seed; legal references require primary-source (e-Gov 法令 / 官報) verification.")
    P("")
    P(f"- cultivars: **{len(hemp)}**  ·  ritual artifacts: **{len(rites)}**  "
      f"·  ceremonies: **{len(events)}**  ·  provisioning lineage: **{len(imbe)}**  "
      f"·  cultivation-license designs: **{len(licenses)}**")
    P(f"- ritual artifacts whose purpose is `:purification`: **{a['purification']}/{len(rites)}**")
    P("")

    # ── G1: cultivar THC-class breakdown (the headline charter signal) ──
    P("## Cultivar THC-class breakdown (G1 invariant)")
    P("")
    P("Every cultivar is fibre/ritual low-THC. `:psychoactive` is not a representable "
      "class — the data model cannot hold a recreational catalog.")
    P("")
    P("| THC class | cultivars |")
    P("|---|---:|")
    for cls in sorted(a['thc_breakdown']):
        P(f"| `{cls}` | {a['thc_breakdown'][cls]} |")
    P("")
    P("| cultivar | name | THC class | fibre use | region |")
    P("|---|---|---|---|---|")
    for hid in sorted(hemp):
        h = hemp[hid]
        uses = ", ".join(u.lstrip(':') for u in (h.get(':hemp/fiber-use') or []))
        region = ", ".join(h.get(':hemp/region') or [])
        P(f"| `{hid}` | {h.get(':hemp/name', hid)} | `{h.get(':hemp/thc-class')}` | {uses} | {region} |")
    P("")

    # ── rites + the aratae / Imbe tradition ──
    P("## Ritual artifacts (祓い・清め) and their fibre source")
    P("")
    P("| artifact | kind | purpose | material | fibre cultivar(s) |")
    P("|---|---|---|---|---|")
    for rid in sorted(rites):
        r = rites[rid]
        cs = ", ".join(a['rite_fiber'].get(rid, []))
        P(f"| {r.get(':rite/name', rid)} | `{r.get(':rite/kind')}` | "
          f"`{r.get(':rite/purpose')}` | `{r.get(':rite/material')}` | {cs} |")
    P("")

    P("## Imperial / ceremonial heritage (as-of history, 非終末論)")
    P("")
    for eid in sorted(events):
        e = events[eid]
        arts = ", ".join(e.get(':rite.event/uses-artifact') or [])
        lin = ", ".join(e.get(':rite.event/lineage') or [])
        P(f"- **{e.get(':rite.event/name', eid)}** (`as-of {e.get(':rite.event/as-of')}`) — "
          f"artifacts: {arts or '—'}; lineage: {lin or '—'}")
    P("")
    if imbe:
        P("### Provisioning lineage")
        P("")
        for iid in sorted(imbe):
            i = imbe[iid]
            P(f"- **{i.get(':imbe/name', iid)}** (`{i.get(':imbe/role')}`, {i.get(':imbe/region','?')})"
              f" — {i.get(':imbe/note','')}")
        P("")

    # ── now-open licensed cultivation space ──
    P("## Now-open low-THC licensed-cultivation space")
    P("")
    P("The 2023 reform (大麻草の栽培の規制に関する法律, 令和5年法律第84号) reopened a licensed "
      "**低THC 栽培者** pathway for fibre/ritual hemp. Each design below is member-principal "
      "(G4), server-keyless (G5), and outward-gated (G8) — R0 design only, not a filing.")
    P("")
    P(f"- member-principal / member-okaimono / serverHeldKey=false / outward-gated invariants hold "
      f"on all designs: **{a['licence_invariants_ok']}**")
    P("")
    P("| design | cultivar | purpose | licensee | funding | legal basis |")
    P("|---|---|---|---|---|---|")
    for lid in sorted(a['licence_clean']):
        lc = a['licence_clean'][lid]
        P(f"| `{lid}` | {lc.get(':hemp.license/cultivar')} | "
          f"`{lc.get(':hemp.license/purpose')}` | `{lc.get(':hemp.license/licensee-principal')}` | "
          f"`{lc.get(':hemp.license/funding')}` | {lc.get(':hemp.license/legal-basis','—')} |")
    P("")
    P("> Direction 2 (legislative observation + public-comment support) is NOT here — it lives in "
      "**danjo** (non-adjudicating fact trace) and **moushibumi** (neutral 意見公募 support). "
      "nusa records heritage + designs cultivation; it does not advocate (G3).")
    P("")
    return "\n".join(L)


def render_datoms(hemp, rites, events, imbe, licenses, a):
    L = []
    P = L.append
    P(";; nusa 幣 — DERIVED heritage datoms (ADR-2606039800)")
    P(";; :derived — analyzer output, NOT re-ingested as authoritative fact (G7).")
    P("[")
    for cls in sorted(a['thc_breakdown']):
        P(f' {{:nusa.derived/thc-class {cls} :nusa.derived/cultivar-count {a["thc_breakdown"][cls]} :nusa.derived/sourcing :derived}}')
    for hid in sorted(hemp):
        n = len(a['cultivar_rites'].get(hid, ()))
        P(f' {{:nusa.derived/cultivar "{hid}" :nusa.derived/supplies-rites {n} :nusa.derived/sourcing :derived}}')
    P("]")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here.parent / "data" / "seed-ritual-hemp.kotoba.edn"
    out = here / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    hemp, rites, events, imbe, licenses = classify(rows)
    a = analyze(hemp, rites, events, imbe, licenses)

    report = render_report(hemp, rites, events, imbe, licenses, a)
    datoms = render_datoms(hemp, rites, events, imbe, licenses, a)
    (out / "heritage-report.md").write_text(report, encoding='utf-8')
    (out / "ritual-hemp-graph.kotoba.edn").write_text(datoms, encoding='utf-8')

    print(f"nusa: {len(hemp)} cultivars, {len(rites)} rites, {len(events)} ceremonies → {out}")
    print(f"  THC-class breakdown: {dict(a['thc_breakdown'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
