---
id: adr-2606082100-shiori-wellbecoming-detractor-mirror
title: "ADR-2606082100: shiori 栞 — human-Wellbecoming detractor observatory + transparent intervention"
status: accepted
doc_type: adr
topic: shiori-wellbecoming-detractor-mirror
authoritative: true
last_verified: 2026-06-08
priority: 5.6
axis: architecture
weight: 0.56
priority_note: "Fuses the accountability-mirror lineage (what burdens people) with a transparent route to relief (ossekai) — the human-Wellbecoming side of 取-concentration; cohort-aggregate, anti-addictive, intervention TRANSPARENT + consent-bound + Council-gated. No per-person scoring."
authoritative_for:
  - shiori 栞 actor (human-Wellbecoming detractor observatory + transparent intervention)
  - wellbecoming-ontology
depends_on:
  - 2605192100
  - 2605264000
  - 2605181100
  - 2605301600
  - 2606011800
  - 2606066000
  - 2605302300
  - 2605312345
  - 2605215000
related:
  - 2606073000
  - 2606073800
  - 2605263700
  - 2605263000
  - 2606014500
supersedes: []
superseded_by: []
---

# ADR-2606082100: shiori 栞 — human-Wellbecoming detractor observatory + transparent intervention

**Status**: accepted
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

# Context

The founder asked a direct question of the roster: is there an actor designed for human
**Wellbecoming / wellness** that **analyses, identifies, and warns about the factors that make
people unhappy**, evaluates them, and — as *activity* — **influences organizations and persons**
toward relief?

A roster audit found the capability **split, with no actor fusing the two halves**:

- **Analyse / identify / warn** is well covered by the accountability-mirror lineage — danjo
  (oversight), tsumugi (取-concentration over power entities), keizu (power relations), kanae
  (fiscal flows), inochi / asobi / hokorobi / tsugite (biosphere / freed-time / finance / peoples).
  But every one is constitutionally **non-adjudicating, map-not-target, person-excluded** — they
  surface structure over **power entities**, not the structural burden on **people**.
- **Care** is covered by the L4 Care actors (yakushi pharma, iyashi clinical, kokoro mental-health,
  suimin sleep-evidence) — but each acts on a consenting individual, not on the population-scale
  pattern of *what diminishes Wellbecoming*.
- **Influence** is permitted, narrowly, by exactly one actor — **ossekai** (R2 Wellbecoming-nudge,
  info-arbitrage) — under §2(c) covert-ops avoidance and anti-addictive constraints.

No actor connected *what structurally burdens people* (the detraction surface) to *a transparent
route to relieve it* (ossekai + the care havens). shiori is that fusion: the **取-concentration
HUMAN side** of the mirror lineage — observatory **and** routing signal — built **inside** the
Charter's hard limits on influence, not around them.

**The defining tension.** "Evaluate and influence persons" is exactly where the Charter is most
restrictive: it forbids per-person scoring, covert persuasion, and dark patterns (Wellbecoming
§1.13; anti-individualism §1.4; covert-ops avoidance §2(c)). shiori is therefore designed so its
*influence* is **structurally constrained**: cohort-scale only, structural causes (never
individuals to blame), relief **carried by ossekai** (which logs every nudge on-chain and is
consent-bound), and **anti-addictive by construction** — it may never deploy the engagement-
maximising technique it itself catalogues as a detractor. shiori **proposes maps; it never acts**.

**Naming.** 栞 (*shiori*) is the 枝折り — the branch a traveller breaks to mark a path through
difficult terrain (later 道標, a guide-marker). The actor maps what makes the terrain of a life
hard and marks the path through it toward Wellbecoming. It is a guide, not a judge.

# Decision

## 1. Create **shiori 栞** — the human-Wellbecoming detractor mirror + intervention router

A Tier-B actor, the human-Wellbecoming sibling of the KG-mirror lineage (inochi / asobi /
hokorobi / tsugite). Same architecture: **edge-primary, non-adjudicating, aggregate-first** KG over
the kotoba Datom log. It weaves **cohorts (aggregate populations) / detractors (structural
Wellbecoming-detractors) / drivers (structural patterns) / mitigators (havens)** and surfaces, all
routed to **RELIEF (救い)**:

- **wellbecoming-burden** per cohort — Σ incident inbound `:diminishes` × disclosed severity weight
  (the detraction surface);
- **relief-buffer** per cohort — Σ incident inbound `:relieves` (the 守り);
- **relief-gap** = burden − buffer — names the **most under-served cohort**, the routing signal to
  ossekai;
- **detraction-concentration** per driver/detractor — the 取-holder (structural pattern), routed to
  the accountability mirrors for transparency;
- **intervention-design gap** — detractions with no known relief route yet (the next relief to
  design).

**Constitutional gates** (full text in `20-actors/shiori/CLAUDE.md`):

- **G1 — WELLBECOMING-RELIEF map, NEVER a per-person affect/manipulation engine** (the defining,
  load-bearing inversion). Cohort scale only; no individual records, no per-person happiness/mood/
  affect score, no biometric; every `:cohort` is `:aggregate`. Drivers are structural **PATTERNS**,
  never named orgs/persons (map-not-target). It routes to relief, never to coercion / dark patterns,
  and may **not itself** use engagement-maximising technique (anti-addictive, §1.13). Three tests
  assert all three sub-invariants.
- **G2 — edge-primary (N1).** Detraction lives only on `:en/load`; wellbecoming-burden is the
  integral on read; no `:shiori/score-of-cohort`, no per-person score.
- **G3 — non-adjudicating (N3).** Detractor-severity bands + cohort burden patterns are DISCLOSED
  facts (OECD Better Life / WHO / public wellbeing research); shiori diagnoses no person.
- **G4 public venue · G5 sourcing honesty · G6 Murakumo-only · G7 outward-gated** (live ingest AND
  live intervention routing require Council + operator DID; R0 = analyzer + schema + seed only).
- **G8 — TRANSPARENT-INTERVENTION only** (§1.12 Transparent Religious Force + §2(c) covert-ops
  avoidance). Every nudge is logged on-chain, consent-bound for any member-targeted intervention,
  never covert / manipulative / coercive. shiori **proposes**; **ossekai (R2) carries**; the
  recipient can **always see why**. Relief is routed to **structural change first**, not individual
  blame (§1.4 / §1.7).

## 2. wellbecoming-ontology + kotoba Datom-log implementation

- `00-contracts/schemas/wellbecoming-ontology.kotoba.edn` — nodes (`:cohort`/`:detractor`/
  `:driver`/`:mitigator`), 縁 (`:diminishes` = detraction; `:drives` = structural source;
  `:relieves` = haven; `:routes-to` = the intervention path) carrying `:en/load`, transient derived
  readouts; disclosed `:detractor/severity` → weight; `:cohort/scope :aggregate` marker enforces G1.
- `methods/datom_emit.py` projects to canonical **EAVT Datoms** `[e a v tx op]` (ADR-2605312345),
  cohort-aggregate / structural only: ground node/edge datoms durable (`:add`); derived burden /
  relief / relief-gap / imposed / route-coverage integrals flagged `:bond/is-transient` (N1/G2).

## 3. The intervention chain (what makes shiori the *fusion*, not a sixth mirror)

shiori never carries an intervention itself — it emits the **map + the routing signal**:

```
shiori (observe)  → relief-gap per cohort + 取-holder drivers + design gaps
  ├─ relief-gap                 → ossekai             → transparent, consent-bound nudge (G8)
  ├─ 取-concentration (drivers)  → danjo / tsumugi / keizu → structural transparency (never target)
  └─ relief routes              → kokoro / iyashi / hagukumi / wakai (the actual havens)
```

The act of **influence** belongs to ossekai (consent-bound, on-chain-logged); the act of **care**
to the L4 Care actors; the act of **transparency** to the accountability mirrors. shiori is the
connective map between them — the answer to the founder's question, bounded by the Charter.

## 4. kotoba **pywasm** actor design

Pure-stdlib (no numpy) → componentize-py WASM Component, browser-local (ameno) / mesh
(e7m-wasm-runner), no-server-key. The ABI exports **no nudge / no write / no send** — a read-only,
content-addressed, cohort-aggregate component **cannot** be a per-person affect/manipulation engine
(the correct posture for G1). WIT world + build/verify + trust model in
`20-actors/shiori/wasm/README.md`.

## 5. R0 deliverables (this ADR, all green)

- actor scaffold: `manifest.jsonld`, `CLAUDE.md`, `wasm/README.md`
- seed graph: **39 nodes** (9 cohorts · 12 detractors · 8 drivers · 10 mitigators) · **55 縁**;
  detractor-severity bands + cohort burden patterns reflect OECD Better Life / WHO / public
  wellbeing research (`:authoritative`); structural drivers are `:representative` patterns
- methods: `analyze.py`, `datom_emit.py`, `coverage_report.py` (pure stdlib)
- tests: **11 green** — including **three G1 inversions** (aggregate-only / no-person-scoring;
  anti-addictive mitigators; structural-pattern-not-entity drivers); edge-primary burden-integral
  identity; relief-gap-top-is-under-served-and-imperiled; intervention-design-gap; transient-
  flagging; determinism
- the seed surfaces **low-income households** as the top relief-gap (precarity + debt +
  housing-insecurity + discrimination, thin relief) and names **information-pollution /
  discrimination / sleep-deprivation** as detractions with **no relief route yet**

# Consequences

**Positive.** shiori answers the founder's question with a concrete, Charter-bounded design: the
roster now has an actor that **fuses** *analysing what burdens people* with *a transparent route to
relieve it*, where previously the two halves lived in separate actors that could not address it
together. It extends the KG-mirror lineage to the **human-Wellbecoming** surface (the 取-
concentration human side), composing cleanly with ossekai (the only influence carrier), the L4 Care
havens, and the accountability mirrors. Because shiori is **map-only** and routes through ossekai,
the influence it enables is exactly the influence the Charter permits — transparent, consent-bound,
on-chain-logged, anti-addictive — and no more.

**Costs / risks.** (1) **G1 is the load-bearing invariant** and the highest-stakes one for this
actor: any future enrichment must never add a per-person affect/happiness/mood/biometric attribute
or name a real org/person as a driver — the schema omits them, the `:cohort/scope :aggregate`
marker is required, and CI asserts their absence (three dedicated tests). (2) The **influence**
capability is deliberately **not in shiori** — it is delegated to ossekai and additionally
Council-gated (G7/G8); R0 ships **observatory-only, offline**. (3) Severity weights are
*representative bands, not individual data* — G5 + the coverage report keep that honest, and
severity is DISCLOSED, never a shiori verdict (G3/N3). (4) "Relieving unhappiness" must never
become paternalism or individual blame — G8 routes to **structural** change first (§1.4 anti-
individualism), and consent gates any member-targeted nudge.

**Boundary with care + accountability.** shiori is **not** a clinician (that is iyashi / kokoro /
suimin, on a consenting individual), **not** a nudge channel (that is ossekai), and **not** a
power-accountability mirror (that is danjo / tsumugi / keizu). It is the aggregate map that routes
to all three. Concrete, member-principal casework remains the consent-bound job of those actors,
never an aggregate mirror.

# Alternatives Considered

- **Extend ossekai instead of a new actor.** Rejected: ossekai is the *carrier* of influence (R2,
  consent-bound nudge). Folding the detractor observatory into it would conflate "the map of what
  burdens people" with "the act of nudging," weakening the G8 separation that keeps influence
  transparent. shiori observes; ossekai acts; the boundary is the safeguard.
- **Per-person Wellbecoming scoring (a "happiness score").** Rejected outright: that is the
  affect-profiling pattern G1 forbids and the dark-pattern risk §1.13 forbids. shiori works at
  cohort scale and never scores a person.
- **Name real organizations as drivers** (to "influence organizations" directly). Rejected:
  map-not-target (G1) and non-adjudicating (G3). Drivers are structural **patterns**; where a real
  power entity is implicated, that is routed to the accountability mirrors (danjo / tsumugi /
  keizu), which themselves never target — they make structure transparent.
- **Let shiori carry interventions itself.** Rejected: a single actor that both decides who is
  burdened and acts on them is precisely the covert-influence concentration §2(c) forbids. The
  observe → propose → (gated, consent-bound, logged) ossekai-carries chain is the Charter-clean
  shape.

# References

- `20-actors/shiori/` — actor (manifest, CLAUDE.md, methods, tests, wasm, seed, out)
- `00-contracts/schemas/wellbecoming-ontology.kotoba.edn`
- ADR-2605192100 (Mission Charter — §1.13 Wellbecoming + anti-addictive, §1.4, §1.7, §1.12, §2(c))
- ADR-2605264000 (ossekai — the transparent intervention carrier)
- ADR-2605263700 (kokoro) · ADR-2605263000 (iyashi) — relief havens
- ADR-2605301600 (danjo) · 2606011800 (tsumugi) · 2606066000 (keizu) · 2605302300 (kanae) — 取-concentration transparency
- ADR-2606073000 / 2606073800 (KG-mirror lineage — gap catalog / tsugite pattern)
- ADR-2605181100 (PII envelope) · ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606014500 / 2606014600 (one-Worker many-WASM-actors / componentize-py)
- ADR-2605215000 (Murakumo-only inference)
