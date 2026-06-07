---
id: adr-2606073600-hoshimori-orbital-stewardship-mirror
title: "ADR-2606073600: hoshimori 星守 — off-Earth orbital stewardship mirror (gap B)"
status: accepted
doc_type: adr
topic: hoshimori-orbital-mirror
authoritative: true
last_verified: 2026-06-07
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes coverage-gap B (off-Earth/orbital) of ADR-2606073000 — stewardship mirror, no-targeting, observation only."
authoritative_for:
  - hoshimori 星守 actor (off-Earth orbital stewardship mirror)
  - orbit-ontology
depends_on:
  - 2606073000
  - 2606073200
  - 2606073400
  - 2605192330
  - 2606041827
  - 2606012600
  - 2605312345
  - 2605215000
related:
  - 2606011800
  - 2606014500
supersedes: []
superseded_by: []
---

# ADR-2606073600: hoshimori 星守 — off-Earth orbital stewardship mirror (gap B)

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

ADR-2606073000 catalogued the world-coverage blind spots; inochi closed A (biosphere), asobi
closed C (freed-time), hokorobi closed D (finance-risk). Gap **B — off-Earth / orbital** is
the last structural domain with a standing claim but no observing actor: the Charter's land
sovereignty already **extends to orbit** (ADR-2605192330), and the live/infrastructure
lineage already mirrors ships & aircraft (`watari`) and submarine cables (`watatsuna`), yet
**Earth orbit itself** — its regimes, congestion, debris, and the public services that depend
on it — had no mirror.

Orbit is the most safety-sensitive gap to model because orbital position data is **dual-use**:
the same catalog that enables debris stewardship can, at interception-grade precision, aid an
anti-satellite strike. The actor must therefore be a **stewardship/sustainability** mirror of
**already-public** catalogs, at **shell-aggregate** granularity, that emits **no precise
predictive ephemeris** — the orbital analogue of inochi's "no occurrence coordinates" gate.

# Decision

## 1. Create **hoshimori 星守** — the orbital stewardship mirror (closes gap B)

A Tier-B actor, the orbital sibling of the live/infrastructure-resilience lineage (watari,
watatsuna). Same architecture as inochi/asobi/hokorobi: edge-primary, non-adjudicating,
aggregate-first KG over the kotoba Datom log. It weaves **orbital regimes (shells) /
operators / hazards / services** from public catalogs and surfaces **orbital-congestion
concentration** (the stewardship surface) vs **stewardship buffers**, plus the
**service-dependency fragility** of the public utilities borne on each regime, all routed to
**STEWARDSHIP** (orbital sustainability).

**Constitutional gates** (full text in `20-actors/hoshimori/CLAUDE.md`):

- **G1 — STEWARDSHIP map, NEVER a targeting / interception aid** (the defining, load-bearing
  inversion). Mirrors only already-public catalogs; **no precise predictive ephemeris** (no
  interception-grade state vector); readouts are orbital-shell / regime-aggregate; ASAT /
  kinetic-intercept / collision-causing uses are unrepresentable (Charter §1.12
  Transparent-Force). A dedicated test asserts no per-object lat/lon/alt/velocity/TLE attr.
- **G2 — edge-primary (N1).** Congestion lives only on `:en/orbit-load`; regime congestion is
  the integral on read; no `:hoshimori/threat-of-object`.
- **G3 — non-adjudicating (N3).** Regime defs + named public debris EVENTS are DISCLOSED facts.
- **G4 public venue · G5 sourcing honesty · G6 Murakumo-only · G7 outward-gated · G8
  observation-only (operates no spacecraft, conducts no maneuver).**

## 2. orbit-ontology + kotoba Datom-log implementation

- `00-contracts/schemas/orbit-ontology.kotoba.edn` — nodes (`:shell`/`:operator`/`:hazard`/
  `:service`), 縁 (`:congests`/`:imperils` = hazard; `:depends-on` = service criticality;
  `:remediates`/`:deconflicts`/`:deorbits` = stewardship) carrying `:en/orbit-load`, transient
  derived readouts; disclosed `:shell/regime` → weight; **no per-object ephemeris attribute
  exists in the schema**.
- `methods/datom_emit.py` projects to canonical **EAVT Datoms** `[e a v tx op]`
  (ADR-2605312345), shell-aggregate only: ground node/edge datoms durable (`:add`); derived
  congestion/stewardship/fragility integrals flagged `:bond/is-transient` (computed on read,
  never persisted — N1/G2).

## 3. kotoba **pywasm** actor design

Pure-stdlib (no numpy) → componentize-py WASM Component, browser-local (ameno) / mesh
(e7m-wasm-runner), no-server-key. A read-only, content-addressed, shell-aggregate component
**cannot** be a targeting service — the correct posture for G1. WIT world + build/verify +
trust model in `20-actors/hoshimori/wasm/README.md`.

## 4. R0 deliverables (this ADR, all green)

- actor scaffold: `manifest.jsonld`, `CLAUDE.md`, `wasm/README.md`
- seed graph: 28 nodes (6 shells · 11 operators/constellations · 7 hazards · 4 services) · 31
  縁; regime defs, public constellation existence/jurisdiction, and named public debris EVENTS
  `:authoritative`; orbit-load values representative severities
- methods: `analyze.py`, `datom_emit.py`, `coverage_report.py` (pure stdlib)
- tests: **9 green** including a dedicated **G1 no-precise-ephemeris** assertion; edge-primary
  congestion integral identity; LEO-low top-congestion sanity; transient-flagging; determinism

# Consequences

**Positive.** The off-Earth domain is now observable as a public-interest stewardship map
without any targeting capability. The seed surfaces **LEO-low** as the top congestion
concentrator (megaconstellation + debris band) and **PNT-on-MEO** as a top service-dependency
fragility — both routed to deconfliction and active-debris-removal. hoshimori completes the
resilience-map family (watari / watatsuna / hoshimori = sea-surface / sea-floor / orbit), and
gives the orbital land-sovereignty claim (ADR-2605192330) an observational substrate.

**With this, four of the five ADR-2606073000 gaps are closed** (A inochi, C asobi, D
hokorobi, B hoshimori). Only **E (human movement / endangered language)** remains —
mirror-first, aggregate-first, no person-tracking, its own ADR.

**Costs / risks.** (1) G1 is the load-bearing invariant: any future enrichment must never add
a precise-ephemeris / state-vector / TLE attribute — the schema omits them and CI
(`test_g1_no_precise_ephemeris`) asserts their absence. (2) Seed orbit-load values are
*representative severities, not measured conjunction probabilities* — G5 + coverage report
keep that honest. (3) Live catalog ingest is G7/Council-gated — R0 ships offline only.

# Alternatives Considered

- **A precise conjunction-screening / collision-avoidance service.** Rejected for R0: that
  requires interception-grade ephemeris (G1 hazard) and is an operational capability, not a
  mirror. hoshimori observes at shell-aggregate and routes to stewards who hold the precise
  data under their own authority.
- **Fold orbit into watari.** Rejected: watari is live transponder-broadcast surface/air
  tracking; orbit needs its own regime ontology, dual-use gate, and shell-aggregate posture.
- **Model per-object catalogs.** Rejected outright: that is the targeting-grade dataset G1
  forbids; hoshimori models shells (regimes), not objects, by design.

# References

- `20-actors/hoshimori/` — actor (manifest, CLAUDE.md, methods, tests, wasm, seed, out)
- `00-contracts/schemas/orbit-ontology.kotoba.edn`
- ADR-2606073000 (coverage-gap catalog + inochi) · 2606073200 (asobi) · 2606073400 (hokorobi)
- ADR-2605192330 (orbital land-sovereignty claim) · 2606041827 (watari) · 2606012600 (watatsuna)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606014500 / 2606014600 (one-Worker many-WASM-actors / componentize-py)
- ADR-2605215000 (Murakumo-only inference)
