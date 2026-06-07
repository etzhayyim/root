---
id: adr-2606073200-asobi-freed-time-play-expression-mirror
title: "ADR-2606073200: asobi 遊び — freed-time play & cultural-expression KG mirror (gap C)"
status: accepted
doc_type: adr
topic: asobi-freed-time-mirror
authoritative: true
last_verified: 2026-06-07
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes coverage-gap C (the telos of labor liberation — the freed time) of ADR-2606073000."
authoritative_for:
  - asobi 遊び actor (freed-time / play & cultural-expression KG mirror)
  - asobi-ontology
depends_on:
  - 2606073000
  - 2606011000
  - 2605081300
  - 2606061900
  - 2605301600
  - 2605312345
  - 2605215000
related:
  - 2606011800
  - 2606014500
  - 2605261045
supersedes: []
superseded_by: []
---

# ADR-2606073200: asobi 遊び — freed-time play & cultural-expression KG mirror (gap C)

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

ADR-2606073000 catalogued the world-coverage blind spots and closed the highest-weight one
(A — the biosphere) with **inochi 命**. The next-highest-weight blind spot is **C — human
play / body / expression**: sport, recreation, music, film, stage, museums, games, the
meal-as-experience. This is not entertainment trivia — it is the **telos of labor
liberation**. The Charter's mission is *人類の構造的労働解放*; what the freed time is *for*
is the flourishing (Wellbecoming) the mission exists to enable. The roster modelled the
*production* side heavily but had no actor for the freed time itself — only `kawaraban`
(news medium) and `kataribe` (publishing/translation) touched its edges.

The natural anti-pattern to invert is the **entertainment-industrial / attention economy**:
play enclosed behind paywalls, ranked by engagement, optimised for time-on-platform. That is
a direct Wellbecoming violation (Charter §1.13, addictive design). So the actor must be a
**participation/access mirror**, never an engagement ranking.

# Decision

## 1. Create **asobi 遊び** — the freed-time KG mirror (closes gap C)

A Tier-B actor, the freed-time-telos sibling of the KG-mirror lineage (inochi / tsumugi /
danjo / kanae / keizu). Same architecture as inochi: edge-primary, non-adjudicating,
aggregate-first KG over the kotoba Datom log. It weaves **works / events / venues /
practices** and the **enclosures** that gate them, and surfaces **participation-openness**
(the access surface to keep wide) vs **enclosure** (the 取 borne by gated play), routed to
**OPENING**.

**Constitutional gates** (full text in `20-actors/asobi/CLAUDE.md`):

- **G1 — PARTICIPATION / ACCESS map, NEVER an engagement ranking** (the defining inversion).
  No retention metric, no recommend-for-time, no per-work popularity score. The 取-holder is
  the *enclosure*; the bearer is the *play*; the routing is *opening*.
- **G2 — edge-primary (N1).** 取 lives only on `:en/access-load`; openness is the integral on
  read; no `:asobi/popularity-of-work`.
- **G3 — non-adjudicating (N3).** Access categories are DISCLOSED facts, never asobi verdicts.
- **G4 public venue · G5 sourcing honesty · G6 Murakumo-only · G7 outward-gated · G8 no
  addictive design (Wellbecoming §1.13, unrepresentable).**

## 2. asobi-ontology + kotoba Datom-log implementation

- `00-contracts/schemas/asobi-ontology.kotoba.edn` — nodes (`:work`/`:event`/`:venue`/
  `:practice`/`:commons`/`:enclosure`), 縁 (`:open-access`/`:teaches`/`:participates`/
  `:hosts`/`:performs`/`:descends-from`/`:encloses`) carrying `:en/access-load`, transient
  derived readouts.
- `methods/datom_emit.py` projects to canonical **EAVT Datoms** `[e a v tx op]`
  (ADR-2605312345): ground node/edge datoms durable (`:add`); derived openness/enclosure
  integrals flagged `:bond/is-transient` (computed on read, never persisted — N1/G2).

## 3. kotoba **pywasm** actor design

Pure-stdlib (no numpy) → componentize-py WASM Component, browser-local (ameno) / mesh
(e7m-wasm-runner), no-server-key. WIT world + build/verify + trust model in
`20-actors/asobi/wasm/README.md`.

## 4. R0 deliverables (this ADR, all green)

- actor scaffold: `manifest.jsonld`, `CLAUDE.md`, `wasm/README.md`
- seed graph: 35 nodes (9 works · 9 practices · 6 events · 7 venues · 4 enclosures) · 32 縁,
  license/public-record facts mostly `:authoritative`
- methods: `analyze.py`, `datom_emit.py`, `coverage_report.py` (pure stdlib)
- tests: 8 green (edge-primary openness identity, openness-top sanity, transient-flagging,
  determinism, coverage honesty)

# Consequences

**Positive.** The freed-time telos now has a substrate that composes with the rest of the
mirror lineage. `:enclosure/links` bridges gated play to the **tsumugi** power-graph
(accountability). The participation-openness surface is directly actionable by **manabi**
(education) and **okaimono**/**omise** (commons provisioning) — open works are exactly what
those commons should carry. The same architecture (inochi → asobi) is now proven reusable
for the remaining gaps.

**Coverage roadmap** (B, D, E of ADR-2606073000 remain open, mirror-first, each its own ADR):

- **B (off-Earth):** live mirror of public orbital catalogs (no targeting).
- **D (finance-risk observation):** danjo/kanjō-lineage risk mirror of world
  insurance/lending/pension structure — observation only.
- **E (human movement / language):** migration & endangered-language mirror, aggregate-first,
  no person-tracking.

**Costs / risks.** (1) G1 is load-bearing: any future enrichment must never add a
retention/engagement attribute — CI should assert no `:engagement/*` or `:popularity/*`
attributes enter asobi graphs. (2) The seed is `:representative` in extent;
`coverage_report.py` keeps that honest. (3) Live ingest of event/license catalogs is
G7/Council-gated — R0 ships offline only.

# Alternatives Considered

- **Fold play into kawaraban or kataribe.** Rejected: kawaraban is a news *medium* mirror and
  kataribe is publishing/translation; neither carries the participation/enclosure inversion,
  which is asobi's defining axis.
- **A recommendation/discovery engine for culture.** Rejected outright: that is the
  attention-economy pattern asobi exists to invert (G1/G8). asobi surfaces *access*, never
  *engagement*.
- **Do gap D or B next instead of C.** Rejected: C is the higher mission-weight (it is the
  telos the whole mission serves) and the cleanest thematic follow-on to A.

# References

- `20-actors/asobi/` — actor (manifest, CLAUDE.md, methods, tests, wasm, seed, out)
- `00-contracts/schemas/asobi-ontology.kotoba.edn`
- ADR-2606073000 (coverage-gap catalog + inochi — the sibling pattern)
- ADR-2606011800 (tsumugi — the power-mirror lineage)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606014500 / 2606014600 (one-Worker many-WASM-actors / componentize-py)
- ADR-2605215000 (Murakumo-only inference)
