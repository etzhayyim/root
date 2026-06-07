---
id: adr-2606073400-hokorobi-systemic-finance-risk-mirror
title: "ADR-2606073400: hokorobi 綻び — systemic finance-risk observation mirror (gap D)"
status: accepted
doc_type: adr
topic: hokorobi-finance-risk-mirror
authoritative: true
last_verified: 2026-06-07
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes coverage-gap D (finance-risk observation) of ADR-2606073000 — observation only, production stays Charter-excluded."
authoritative_for:
  - hokorobi 綻び actor (systemic finance-risk observation mirror)
  - finrisk-ontology
depends_on:
  - 2606073000
  - 2606073200
  - 2606032000
  - 2605302300
  - 2606022000
  - 2605301600
  - 2605312345
  - 2605215000
related:
  - 2606011800
  - 2606051800
  - 2606014500
supersedes: []
superseded_by: []
---

# ADR-2606073400: hokorobi 綻び — systemic finance-risk observation mirror (gap D)

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

ADR-2606073000 catalogued the world-coverage blind spots; inochi closed A (biosphere) and
asobi closed C (freed-time). Gap **D — finance-risk observation** is the subtlest: the
Charter **excludes finance production** (non-profit only; insurance/banking/lending are out
of scope by construction — `wakai` is explicitly *not* insurance). But exclusion of the
*product* left the *phenomenon* unobserved. The accountability lineage already mirrors
disclosed corporate financials (`kanjō`), supply-chain concentration (`kabuto`), and
government fiscal flow (`kanae`) — yet world **systemic financial risk** (the fragility that
propagates through banks, insurers, and pension funds and is ultimately borne by the public)
had no mirror. A danjo-style observation actor closes this without re-introducing any
Charter-excluded production capability.

The anti-pattern to invert is the **market-data terminal / trading signal**: a private, paid
feed that turns systemic stress into a profit/short opportunity and can itself trigger runs.
hokorobi must be the opposite — a public, aggregate, **resilience** map that **never trades**
and emits **no market signal**.

# Decision

## 1. Create **hokorobi 綻び** — the systemic finance-risk mirror (closes gap D)

A Tier-B actor, the risk-observation sibling of the disclosure/accountability lineage
(kanjō / kanae / kabuto / danjo). Same architecture as inochi/asobi: edge-primary,
non-adjudicating, aggregate-first KG over the kotoba Datom log. It weaves **institutions /
risk-sources / bearers** across the three pillars (insurance, banking-lending, pensions) and
surfaces **systemic-risk concentration** (the resilience surface) vs **resilience buffers**,
routed to **RESILIENCE** (繕い — the mending of the 綻び).

**Constitutional gates** (full text in `20-actors/hokorobi/CLAUDE.md`):

- **G1 — RESILIENCE map, NEVER a panic / trading signal** (the defining inversion). Never a
  bank-run trigger, never a trading/short/market-moving signal, never a per-institution
  solvency verdict; **it NEVER trades** (the `mitooshi` discipline). Aggregate-first. The
  取-holder is the *risk-source*; the bearer is the *public*; the routing is *resilience*.
- **G2 — edge-primary (N1).** Risk lives only on `:en/risk-load`; systemic-risk is the
  integral on read; no `:hokorobi/solvency-of-bank`.
- **G3 — non-adjudicating (N3).** Systemic-importance designations (G-SIB/D-SIB/IAIS) are
  DISCLOSED facts, never hokorobi verdicts; **no advice/forecast** (the `kanjō` discipline).
- **G4 public venue · G5 sourcing honesty · G6 Murakumo-only · G7 outward-gated · G8
  observation-only (finance production stays Charter-excluded).**

## 2. finrisk-ontology + kotoba Datom-log implementation

- `00-contracts/schemas/finrisk-ontology.kotoba.edn` — nodes (`:institution`/`:risk`/
  `:bearer`), 縁 (`:exposes`/`:interconnects`/`:underfunds`/`:protection-gap` = risk;
  `:backstops`/`:capitalizes`/`:diversifies` = resilience) carrying `:en/risk-load`,
  transient derived readouts; disclosed `:inst/sii` tier → weight.
- `methods/datom_emit.py` projects to canonical **EAVT Datoms** `[e a v tx op]`
  (ADR-2605312345): ground node/edge datoms durable (`:add`); derived systemic/resilience
  integrals flagged `:bond/is-transient` (computed on read, never persisted — N1/G2).

## 3. kotoba **pywasm** actor design

Pure-stdlib (no numpy) → componentize-py WASM Component, browser-local (ameno) / mesh
(e7m-wasm-runner), no-server-key. A read-only, content-addressed component holds no live
feed and emits no signal — the right trust posture for G1. WIT world + build/verify + trust
model in `20-actors/hokorobi/wasm/README.md`.

## 4. R0 deliverables (this ADR, all green)

- actor scaffold: `manifest.jsonld`, `CLAUDE.md`, `wasm/README.md`
- seed graph: 28 nodes (18 institutions across bank/insurer/reinsurer/pension/ccp/shadow-bank
  · 6 risk-sources · 5 bearers) · 31 縁; systemic-importance designations `:authoritative`
  (FSB G-SIB / IAIS), risk-load values representative severities
- methods: `analyze.py`, `datom_emit.py`, `coverage_report.py` (pure stdlib)
- tests: 8 green (edge-primary systemic integral identity, systemic-top sanity,
  transient-flagging, determinism, three-pillars coverage)

# Consequences

**Positive.** The finance-risk phenomenon is now observable without any Charter-excluded
production. The contagion (`:interconnects`) 縁 surface linchpin market infrastructure
(clearing CCPs ranked top systemic concentrator in the seed) as resilience targets. hokorobi
composes with kanjō/kabuto/kanae/mitooshi into a complete financial mirror (disclosure →
concentration → systemic fragility), and feeds the Charter's social-security / mutual-aid
work (`wakai`, §1.16) a public-interest read on where the public bears realized risk.

**Coverage roadmap** (B and E of ADR-2606073000 remain, mirror-first, each its own ADR):

- **B (off-Earth):** live mirror of public orbital catalogs (no targeting).
- **E (human movement / language):** migration & endangered-language mirror, aggregate-first,
  no person-tracking.

**Costs / risks.** (1) G1 is load-bearing: any future enrichment must never add a live feed,
a tradeable signal, or a solvency verdict — CI should assert no `:signal/*` or `:solvency/*`
attributes enter hokorobi graphs. (2) The seed risk-load values are *representative
severities, not measured solvency* — `coverage_report.py` + G5 keep that honest. (3) Live
FSB/IAIS/regulator ingest is G7/Council-gated — R0 ships offline only.

# Alternatives Considered

- **A finance product (insurance/lending) for members.** Rejected: finance production is
  Charter-excluded; hokorobi is strictly the observation counterpart.
- **Fold finance-risk into kanjō or kabuto.** Rejected: kanjō is disclosed-financials and
  kabuto is supply-chain concentration; neither carries the systemic-risk/resilience
  inversion or the bearer (public) axis, which is hokorobi's defining structure.
- **A market-risk terminal / signal.** Rejected outright: that is the paid-terminal /
  trading-signal pattern hokorobi exists to invert (G1/G3/G8) — it never trades and emits no
  signal.

# References

- `20-actors/hokorobi/` — actor (manifest, CLAUDE.md, methods, tests, wasm, seed, out)
- `00-contracts/schemas/finrisk-ontology.kotoba.edn`
- ADR-2606073000 (coverage-gap catalog + inochi) · ADR-2606073200 (asobi — sibling pattern)
- ADR-2606032000 (kanjō) · ADR-2606022000 (kabuto) · ADR-2605302300 (kanae) · ADR-2606051800 (mitooshi — never-trades)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606014500 / 2606014600 (one-Worker many-WASM-actors / componentize-py)
- ADR-2605215000 (Murakumo-only inference)
