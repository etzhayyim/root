---
id: adr-2606073800-tsugite-peoples-continuity-mirror
title: "ADR-2606073800: tsugite 継ぎ手 — world peoples-continuity mirror (gap E, catalog complete)"
status: accepted
doc_type: adr
topic: tsugite-peoples-continuity-mirror
authoritative: true
last_verified: 2026-06-07
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes coverage-gap E (human movement + endangered language) of ADR-2606073000 — the FINAL gap; mirror-only, aggregate-only, no person-tracking."
authoritative_for:
  - tsugite 継ぎ手 actor (world peoples-continuity mirror)
  - peoples-ontology
depends_on:
  - 2606073000
  - 2606073200
  - 2606073400
  - 2606073600
  - 2605181100
  - 2605302130
  - 2605312345
  - 2605215000
related:
  - 2606011800
  - 2606014500
  - 2605261045
supersedes: []
superseded_by: []
---

# ADR-2606073800: tsugite 継ぎ手 — world peoples-continuity mirror (gap E, catalog complete)

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

ADR-2606073000 catalogued five world-coverage blind spots; inochi closed A (biosphere), asobi
closed C (freed-time), hokorobi closed D (finance-risk), hoshimori closed B (orbit). Gap **E —
human movement + endangered language** is the last, and the most PII-sensitive: it names two
strands — migration / refugees / statelessness, and endangered-language / intangible-culture
preservation — both about **the continuity and dignity of peoples under pressure**. These align
tightly with the Charter's anti-individualist, multi-generational, Wellbecoming ontology
(continuity of peoples = continuity of the web they live in), yet had no actor.

Because the domain concerns vulnerable human collectives, the **defining inversion is
load-bearing**: the actor must be **aggregate-only**, **never** an individual locator or a
border-enforcement / surveillance tool. It mirrors the same surveillance apparatus it inverts —
routing to refuge and revitalization, never to interdiction.

**Naming.** An earlier draft named the actor 民 (*tami*). It was rejected on the founder's
correction: that character's oracle-bone etymology depicts a blinded/subjugated person — the
opposite of a dignity-centered actor. The actor is named **継ぎ手** (*tsugite*, "the one who
carries on"), naming the value (継承, continuity) as inochi names life.

# Decision

## 1. Create **tsugite 継ぎ手** — the peoples-continuity mirror (closes gap E)

A Tier-B actor, the human-collective sibling of the KG-mirror lineage (inochi / asobi /
hokorobi / hoshimori). Same architecture: edge-primary, non-adjudicating, aggregate-first KG
over the kotoba Datom log. It weaves **peoples (collectives) / languages / pressures / havens**
and surfaces **displacement + erasure pressure** (the continuity surface) vs **protection
buffers**, plus the **people↔tongue transmission fragility**, all routed to **CONTINUITY (継承)**.

**Constitutional gates** (full text in `20-actors/tsugite/CLAUDE.md`):

- **G1 — PEOPLES-CONTINUITY map, NEVER person-tracking** (the defining, load-bearing
  inversion). Collective scale only; no individual records, no real-time location, no biometric;
  every `:people` is `:aggregate`. Never a border-enforcement / deportation / surveillance aid;
  routes to refuge + revitalization, never interdiction. A dedicated test asserts no
  person/locator attribute exists.
- **G2 — edge-primary (N1).** Pressure lives only on `:en/peril-load`; continuity-need is the
  integral on read; no `:tsugite/score-of-people`.
- **G3 — non-adjudicating (N3).** Displacement figures + language-vitality categories are
  DISCLOSED facts (UNHCR / IOM / UNESCO / Ethnologue).
- **G4 public venue · G5 sourcing honesty · G6 Murakumo-only · G7 outward-gated · G8
  consent-bound PII** (member-linked data XChaCha20-Poly1305-enveloped, ADR-2605181100; the
  public seed carries none).

## 2. peoples-ontology + kotoba Datom-log implementation

- `00-contracts/schemas/peoples-ontology.kotoba.edn` — nodes (`:people`/`:language`/
  `:pressure`/`:haven`), 縁 (`:displaces`/`:erases` = pressure; `:speaks` = transmission;
  `:shelters`/`:revitalizes`/`:protects` = haven) carrying `:en/peril-load`, transient derived
  readouts; disclosed `:lang/vitality` → weight; `:people/scope :aggregate` marker enforces G1.
- `methods/datom_emit.py` projects to canonical **EAVT Datoms** `[e a v tx op]`
  (ADR-2605312345), collective-aggregate only: ground node/edge datoms durable (`:add`); derived
  continuity/protection/fragility integrals flagged `:bond/is-transient` (N1/G2).

## 3. kotoba **pywasm** actor design

Pure-stdlib (no numpy) → componentize-py WASM Component, browser-local (ameno) / mesh
(e7m-wasm-runner), no-server-key. A read-only, content-addressed, collective-aggregate component
**cannot** be a person-tracking service — the correct posture for G1. WIT world + build/verify +
trust model in `20-actors/tsugite/wasm/README.md`.

## 4. R0 deliverables (this ADR, all green)

- actor scaffold: `manifest.jsonld`, `CLAUDE.md`, `wasm/README.md`
- seed graph: 33 nodes (11 peoples · 9 languages · 8 pressures · 6 havens) · 31 縁; UNHCR/IOM
  aggregate displacement, UNESCO/Ethnologue vitality, and public instruments (1951/1961
  Conventions) + named programs (Kōhanga Reo, Pūnana Leo) `:authoritative`
- methods: `analyze.py`, `datom_emit.py`, `coverage_report.py` (pure stdlib)
- tests: **9 green** including a dedicated **G1 aggregate-only / no-person-tracking** assertion;
  edge-primary continuity integral identity; imperiled-top sanity; transient-flagging; determinism

# Consequences

**Positive — and catalog-completing.** With tsugite, **all five ADR-2606073000 gaps are closed**
(A inochi · C asobi · D hokorobi · B hoshimori · E tsugite). The KG-mirror lineage now spans the
biosphere, the freed-time telos, world finance-risk, Earth orbit, and the world's peoples — each
edge-primary, non-adjudicating, aggregate-first, mirror-only, routed to a restorative value
(restoration / opening / resilience / stewardship / continuity). tsugite's `:speaks` coupling
ties displacement to downstream language risk, and it composes with kataribe (translation/
publishing as revitalization), manabi (mother-tongue education), and hagukumi (care for
displaced families). The seed surfaces **Ainu** as top continuity-need and **Māori/Hawaiian**
revitalization as the forward model.

**Costs / risks.** (1) G1 is the load-bearing invariant and the highest-stakes one in the whole
catalog: any future enrichment must never add a person/locator/biometric attribute — the schema
omits them, the `:people/scope :aggregate` marker is required, and CI
(`test_g1_aggregate_only_no_person_tracking`) asserts their absence. (2) Member-linked data, if
ever added, is consent-bound + PII-enveloped (G8). (3) Live ingest is G7/Council-gated — R0
ships offline only. (4) Seed peril-load values are *representative severities, not individual
data* — G5 + coverage report keep that honest.

**Catalog status.** ADR-2606073000's roadmap is complete. Future work is depth (coverage waves
per actor, gated live ingest) and the WASM deploy wave across the five mirrors — not new gaps.

# Alternatives Considered

- **Name the actor 民 (tami).** Rejected on the founder's correction (blinded-subjugated-person
  etymology); renamed to 継ぎ手.
- **Split into two actors (migration vs language).** Rejected: the catalog framed E as one gap,
  and the `:speaks` coupling makes displacement and language-erasure a single continuity surface;
  one mirror is more coherent and avoids duplicating the aggregate-only gate.
- **Model individuals / a case-management tool.** Rejected outright: that is the person-tracking
  pattern G1 forbids. tsugite serves displaced/endangered peoples by mapping the structure to
  route resources to havens — concrete casework is the consent-bound, member-principal job of
  toritsugi / himotoki / hagukumi, never an aggregate mirror.

# References

- `20-actors/tsugite/` — actor (manifest, CLAUDE.md, methods, tests, wasm, seed, out)
- `00-contracts/schemas/peoples-ontology.kotoba.edn`
- ADR-2606073000 (gap catalog + inochi) · 2606073200 (asobi) · 2606073400 (hokorobi) · 2606073600 (hoshimori)
- ADR-2605181100 (PII envelope) · ADR-2605302130 (himotoki — consent discipline)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606014500 / 2606014600 (one-Worker many-WASM-actors / componentize-py)
- ADR-2605215000 (Murakumo-only inference)
