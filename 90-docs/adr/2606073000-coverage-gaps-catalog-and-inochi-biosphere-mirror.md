---
id: adr-2606073000-coverage-gaps-catalog-and-inochi-biosphere-mirror
title: "ADR-2606073000: World-coverage gap catalog + inochi 命 biosphere KG mirror"
status: accepted
doc_type: adr
topic: coverage-gaps-and-inochi
authoritative: true
last_verified: 2026-06-07
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Closes the largest mission-integrity gap (the living world) and sets a measured roadmap for the rest."
authoritative_for:
  - world-coverage gap catalog (what etzhayyim does not yet observe/produce)
  - inochi 命 actor (living-world / 生命圏 KG mirror)
  - biosphere-ontology
depends_on:
  - 2606011000
  - 2606011500
  - 2605081300
  - 2605301600
  - 2605302300
  - 2606066000
  - 2605312345
  - 2605215000
related:
  - 2606011800
  - 2606042330
  - 2606014500
supersedes: []
superseded_by: []
---

# ADR-2606073000: World-coverage gap catalog + inochi 命 biosphere KG mirror

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The actor roster is broad — 157 actor directories, 750 ADRs — spanning manufacturing,
robotics, care, accountability KGs, internal-economy commerce inversions, silicon, and
civic concierges. A coverage review of "全世界の事象" (all world phenomena) against the
roster found that the breadth is real but **structured around human/industrial/power
activity**, leaving identifiable blind spots. We separate **deliberate Charter exclusions**
(weapons, fossil-virgin extraction, nuclear, for-profit finance — out of scope *by
construction*) from **genuine blind spots** (domains the Charter would have us observe or
serve, but no actor/ADR touches).

## Coverage-gap catalog (genuine blind spots)

| # | Blind spot | Nature | Mission weight |
|---|---|---|---|
| **A** | **Biosphere — animals/wildlife, forests, oceans/fisheries, biodiversity/ecosystems, climate-as-it-affects-life** | **true gap (zero actors)** | **highest** — directly indexed by Tree of Life / Wellbecoming / anti-individualist ontology (Charter §0.1, §1.13); its absence is the least defensible |
| B | Off-Earth / orbital operations (satellites, space weather, orbital congestion) | claim-only — land sovereignty already extends to orbit (ADR-2605192330), no operating/observing actor | medium |
| C | Human play / body / expression — sport, recreation, music, film, performing arts, museums, the meal-as-experience | true gap | high — the *telos* of labor liberation (the freed time) is unmodelled |
| D | Risk/capital **observation** — insurance, banking, lending, pensions (actors are Charter-excluded, but even a danjo-style **mirror** of world finance-risk is absent) | observation gap | medium |
| E | Human movement — migration / refugees / statelessness; endangered-language & intangible-culture preservation | true gap | medium-high |

This ADR (1) records the catalog as the authoritative gap register, (2) closes blind spot
**A** with a real implementation, and (3) sets a measured roadmap for B–E via the existing
KG-mirror lineage.

## Why A first, and why a mirror (not a producer)

Spot A is the highest mission-weight gap and the cleanest architectural fit: the existing
**power-mirror lineage** (danjo / tsumugi / ooyake / keizu / kanae) already implements
exactly the pattern needed — an edge-primary, non-adjudicating, aggregate-first KG over the
kotoba Datom log that surfaces **取-concentration routed to release**. Applied to the
biosphere, 取-concentration becomes **ecological custody-debt** (extinction/degradation
pressure borne by the living world), routed to **restoration**. Starting from *observation*
(KG) rather than *production* (robotics) is also the Charter-safe entry: it composes with
Transparent-Force, map-not-target, and edge-primary karma without standing up any physical
or outward capability.

# Decision

## 1. Adopt the gap catalog above as authoritative

`authoritative_for: world-coverage gap catalog`. Future actor proposals that claim to
"close a world gap" reference this register. B–E remain open with the roadmap in
Consequences.

## 2. Create **inochi 命** — the living-world (生命圏) KG mirror (closes spot A)

A Tier-B actor, the living-world sibling of the power-mirror lineage. It weaves
**species / ecosystems / biomes** and the **pressures** they bear into the kotoba Datom log
and runs an **edge-primary ecological 取-concentration** pass routed to restoration.

**Constitutional gates** (full text in `20-actors/inochi/CLAUDE.md`):

- **G1 — RESTORATION map, NEVER a target-list** (the defining inversion). No precise
  occurrence coordinates of at-risk taxa; spatial readouts are biome/realm-aggregate only.
  The 取-holder is the *pressure*; the bearer is the *living world*; the routing is
  *restoration* — never a hunting/harvest/exploitation map.
- **G2 — edge-primary (N1).** 取 lives only on `:en/grasping-load`; node restoration-priority
  is the integral computed on read; no `:biosphere/score-of-species`.
- **G3 — non-adjudicating (N3).** IUCN categories are DISCLOSED facts, never inochi verdicts.
- **G4 public venue · G5 sourcing honesty · G6 Murakumo-only · G7 outward-gated · G8 no git-lfs.**

## 3. biosphere-ontology + kotoba Datom-log implementation

- `00-contracts/schemas/biosphere-ontology.kotoba.edn` — nodes (`:species`/`:ecosystem`/
  `:biome`/`:pressure`), 縁 (`:pressures`/`:depends-on`/`:keystone-of`/`:pollinates`/…)
  carrying `:en/grasping-load`, and transient derived readouts.
- `methods/datom_emit.py` projects the graph into canonical **EAVT Datoms** `[e a v tx op]`
  (ADR-2605312345): ground node/edge datoms are durable (`:add`); derived integrals are
  flagged `:bond/is-transient` (computed on read, never persisted — N1/G2).

## 4. kotoba **pywasm** actor design

inochi's methods are **pure-stdlib (no numpy)** so they compile to a WASM Component via
**componentize-py** (watatsuna pattern, ADR-2606014600) and run browser-local (ameno) or on
the donated mesh (e7m-wasm-runner) with no per-actor server (no-server-key). WIT world,
ABI, build/verify path, and trust model are in `20-actors/inochi/wasm/README.md`.

## 5. R0 deliverables (this ADR, all green)

- actor scaffold: `manifest.jsonld`, `CLAUDE.md`, `wasm/README.md`
- seed Datom graph: 30 nodes (15 species · 10 ecosystems/biomes · 5 pressures) · 43 縁,
  mostly `:authoritative` (IUCN categories + documented trophic/dependency relations)
- methods: `analyze.py`, `datom_emit.py`, `coverage_report.py` (pure stdlib)
- tests: 8 green (edge-primary integral identity, restoration-top sanity, transient-flagging,
  determinism, coverage honesty)

# Consequences

**Positive.** The single largest mission-integrity gap is closed with a working, tested
implementation that reuses a proven architecture. The Charter's Tree of Life / Wellbecoming
ontology now has a living-world substrate. The `:pressure/links` field bridges ecological
debt to the **tsumugi** power-graph (accountability, aggregate-first), unifying the mirror
lineage across power *and* the living world.

**Roadmap for B–E** (measured, mirror-first, each its own ADR):

- **B (off-Earth):** a `watari`-style live mirror of public orbital catalogs (no targeting).
- **C (play/body/expression):** a commons-mirror of cultural/sport/expression events
  (the freed-time telos), mirror-only like `kawaraban`.
- **D (finance-risk observation):** extend the danjo/kanjō lineage to a **risk mirror** of
  world insurance/lending/pension structure — observation only (production stays
  Charter-excluded).
- **E (human movement / language):** a migration & endangered-language mirror, aggregate-first
  and consent-bound (no person-tracking; the `tsumugi`/`himotoki` PII discipline applies).

**Costs / risks.** (1) G1 is load-bearing: any future spatial enrichment must stay
biome/realm-aggregate — a coordinate leak would invert the actor into a poaching map; CI
should assert no `:geo/lat`-class attributes enter inochi graphs. (2) The seed is
`:representative` in extent; `coverage_report.py` keeps that honest (all-life coverage ~0 by
design). (3) Live IUCN/GBIF/IPCC ingest is G7/Council-gated — R0 ships offline only.

# Alternatives Considered

- **One thin scaffold per gap (A–E).** Rejected: breadth without maturity; the user asked to
  raise *both* coverage and maturity. One real, tested actor on the highest-weight gap, plus
  a catalogued roadmap, does both.
- **A biosphere *producer* (conservation robotics) first.** Rejected for R0: production
  implies outward capability and Charter gating; the mirror is the safe, composable entry and
  feeds any future producer with a restoration-priority surface.
- **Fold biosphere into tsumugi.** Rejected: tsumugi is power-scope (§D8/§D9) by construction;
  the living world is a distinct scope with its own defining inversion (G1 restoration-not-target).

# References

- `20-actors/inochi/` — actor (manifest, CLAUDE.md, methods, tests, wasm, seed, out)
- `00-contracts/schemas/biosphere-ontology.kotoba.edn`
- ADR-2606011800 (tsumugi — the power-mirror this is modelled on)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606014500 / 2606014600 (one-Worker many-WASM-actors / componentize-py)
- ADR-2605215000 (Murakumo-only inference)
