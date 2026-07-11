---
id: adr-2607101800-narashi-global-inequality-observation-tier-b-actor-r0
title: narashi (均) — Global Inequality Observation Tier-B Actor R0
status: proposed
doc_type: adr
topic: global-inequality-observation
authoritative: true
last_verified: 2026-07-10
authoritative_for:
  - narashi actor scope, constitutional gates, non-goals
  - the boundary between narashi (observation) and the Liberation Ladder (benefit delivery to adherents)
related:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2606032130-displacement-dividend-tenure-weighted-basic-high-income
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605302245-danjo-global-fiscal-flow-extension
  - adr-2605302300-kanae-global-fiscal-flow-visualization-tier-b-actor-r0
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605192100 (Mission Charter §1.8(sub) — 格差アービトラージを埋める情報発信)
  - ADR-2605262130 (kotoba EAVT — no RisingWave/Postgres/Lance)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2605302300 (kanae — read-only cross-reference for aid/loan flows)
---

# ADR-2607101800: narashi (均) — Global Inequality Observation Tier-B Actor R0

**Date**: 2026-07-10
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify), 30-day public objection period
**ADR Hierarchy**: Sibling to ADR-2605301600 (danjo) / ADR-2605302300 (kanae). Reads ADR-2605261000
(Liberation Ladder) as the defining non-goal boundary — narashi does not deliver benefits; it makes
the state of global inequality legible.

## Context

An operator question surfaced a gap: **etzhayyim has no actor whose explicit mission is observing
global economic inequality** (between and within nations — Gini coefficient, poverty headcount ratio,
income-share-held-by-decile, SDG 10 "Reduced Inequalities" indicators). A repository-wide search
confirmed:

1. The **Liberation Ladder** (ADR-2605261000) reduces labor hours via in-kind benefit delivery, but
   its Non-Goals are immutable and narrow its scope on purpose: **N1** rejects fiat-replacement UBI /
   cash redistribution, **N4** is explicitly not a state-welfare replacement, and **N7** restricts all
   benefit flow to Adherent SBT holders only. It is a *members-only labor-liberation* mechanism, not a
   *global inequality* mechanism — the two are related in spirit (both trace to the Mission Charter's
   人類の構造的労働解放) but operationally disjoint.
2. **kanae** (ADR-2605302300) already assembles inter-governmental fund flows (IMF / World Bank / OECD
   / UN aid, loans, transfers) into kotoba EAVT and visualizes them, but it does not ingest or narrate
   *inequality outcome* indicators (Gini, poverty headcount, SDG 10) — its `fundFlowEdge` schema is
   flow-only, not outcome-only.
3. `org.worldbank.api`, `org.un.unstats`, `org.ourworldindata` (DataLad raw datasets) and
   `global-energy-datoms` (the one existing "-datoms" projection repo) currently carry **energy**
   indicators only (SDG 7.1.1 electricity access, 7.2.1 renewables share) — no SDG 10 / Gini / poverty
   projection exists anywhere in the monorepo.
4. Mission Charter §1.8(sub) names "格差アービトラージを埋める情報発信" (closing the disparity-arbitrage
   that expertise/language/institutional-knowledge gaps produce) as a charter-level activity, implemented
   today only by the `open-isco` / `open-naics` / `open-hs` / `open-banking` classification apps — none
   of which touch economic-inequality *outcome* data.

This ADR closes that gap the same way ADR-2605301600 (danjo) and ADR-2605302300 (kanae) closed the
analogous gap for government accountability and fiscal-flow transparency: a **non-adjudicating
observation actor**, not a redistribution mechanism. The Liberation Ladder's Non-Goals (N1/N4/N7)
already foreclose the "etzhayyim itself redistributes the world's wealth" reading of "solve global
inequality" — a religious-corp funded by 10% tithe cannot fund a global UBI, and constitutionally
should not try (N1's own reasoning: cash transfers fund commercial market participation, which is the
substrate etzhayyim routes around). What etzhayyim *can* constitutionally do, consistent with every
other Tier-B observation actor (danjo / kanae / kanjo), is make the state of global inequality
**legible** — factual, source-cited, aggregate, non-adjudicating — as a public good.

## Decision

### 1. Identity

- **Name**: narashi (均) — "to level / make even"; the same neutral-measurement register as kanae's
  鼎の軽重を問う ("weighing," not "judging"). narashi measures the *degree of unevenness*; it does not
  itself level anything.
- **DID**: `did:web:narashi.etzhayyim.com`
- **Namespace**: `com.etzhayyim.narashi.*`
- **Tier**: Tier-B. **Parent actor**: null. **Primary upstream**: `org.worldbank.api` (WDI),
  `org.un.unstats` (SDG API), `org.ourworldindata` (OWID) DataLad raw datasets; **read-only
  cross-reference**: kanae's `fundFlowEdge` datoms where `flowClass` ∈
  {`intergovernmental-transfer`, `aid-disbursement`, `loan`} (juxtaposition only — see G-noncausal below).

### 2. Scope (R0)

narashi ingests three indicator families already published by Tier-A sources, normalizes them to one
canonical concept set, and projects them into kotoba EAVT — the same "-datoms" shape as
`global-energy-datoms` and `global-legislation-datoms`, generalized from energy/legislation to
inequality outcomes:

| Indicator family | Canonical concept | Primary source |
|---|---|---|
| Income/consumption inequality | `:ineq/gini` | World Bank WDI (`SI.POV.GINI`), UN SDG 10.4.1 |
| Poverty | `:ineq/poverty-headcount-ratio` (national + $2.15/day intl line) | World Bank WDI (`SI.POV.DDAY`, `SI.POV.NAHC`) |
| Distributional share | `:ineq/income-share-bottom40`, `:ineq/income-share-top10` | World Bank WDI, OWID (World Inequality Database mirror) |
| SDG 10 headline | `:ineq/sdg10-shared-prosperity-premium` | UN SDG API (10.1.1) |

R0 is **scaffold-only**, matching kanae's own R0 baseline: cells are path-reserved and raise on first
invocation until Council ratification; no live fetch; no narrative; no publication.

### 3. Constitutional Gates (G1–G9) — IMMUTABLE, same discipline family as danjo/kanae

| Gate | Rule |
|---|---|
| **G1** | Charter Rider §2(a)-(h) scan on every published narrative + artifact |
| **G2** | kotoba EAVT persistence only — RisingWave / Postgres / Lance / DuckDB / SQLite PROHIBITED as primary store or read backend (ADR-2605262130) |
| **G3** | Passive-only / upstream-only ingestion — reads ONLY the pre-published, IPFS-pinned WDI/SDG/OWID DataLad snapshots (per `global-energy-datoms`'s existing pattern); no live scraping, no per-query API, no non-public sources |
| **G4** | **NON-adjudicating** (UPL-equivalent, mirrors danjo/kanae G4) — narashi reports the disclosed metric value and its trend only. It MUST NOT rank countries as "good/bad," assign blame for a country's Gini level, or recommend a policy fix. No country-ranking-as-verdict; a `metricObservation` is a number with provenance, never a score of merit. |
| **G5** | Source-provenance mandatory — every `metricObservation` cites ≥2 upstream WDI/SDG/OWID record CIDs (or 1 where only one Tier-A source publishes that indicator-country-year triple, explicitly flagged `singleSourced=true`) |
| **G6** | Open method — every normalization/aggregation heuristic (e.g., PPP adjustment, interpolation for missing years) published as an open, versioned `methodNote` |
| **G7** | Murakumo-only inference (ADR-2605215000) — any narrative text on Murakumo fleet only; `murakumoInferenceAttestation` mandatory; vendor-LLM origin unrepresentable at schema layer |
| **G8** | **Non-causal cross-reference** (new; narashi-specific) — when narashi juxtaposes a kanae `aid-disbursement`/`loan` edge against an inequality trend in the same jurisdiction-period, the resulting `crossReferenceNote` MUST carry `causalClaim=false` as a schema const and MUST NOT assert that aid caused (or failed to cause) any change in the metric. Correlation-adjacent display only; causal inference is structurally unrepresentable. |
| **G9** | Aggregate-first, no per-household/per-individual data — narashi operates exclusively on national/sub-national aggregate statistics as published by WDI/SDG/OWID; it never ingests or derives individual-level records (moot by source, but stated as an explicit invariant per the aggregate-first pattern in G10 of danjo/kanae). |

### 4. Non-Goals (N1–N8, IMMUTABLE)

| # | Non-Goal | Rationale |
|---|---|---|
| **N1** | NOT a redistribution / UBI / grant-making mechanism. | That role is already reserved to the Liberation Ladder (ADR-2605261000) for etzhayyim's own Adherent SBT holders, itself bounded by its own N1 (no fiat UBI) and N7 (adherents only). narashi does not move funds, does not have a Public Fund allocation, and does not extend Liberation Ladder benefits to non-adherents. Observation and benefit-delivery are constitutionally separate organs, same split as danjo (finds) / kanae (renders) vs. the actors that actually deliver food/shelter/care (mitsuho/tatekata/hagukumi). |
| **N2** | NOT a policy-prescription engine. | narashi reports what the indicators say; it does not recommend tax policy, aid allocation, or trade policy to any government. |
| **N3** | NOT a country-ranking / shaming tool. | No "best/worst country" leaderboard framing. Aggregate-first, trend-first presentation (cf. kanjo's non-rating discipline for companies). |
| **N4** | NOT a causal-inference engine (G8). | narashi cannot and does not assert that any policy, aid flow, or event caused an inequality-metric change. |
| **N5** | NOT a replacement for the state's own statistical agencies or for the World Bank/UN's own publications. | narashi is a normalized aggregation + narration + persistence layer over what those bodies already publish (same non-replacement posture as kanae N10 vs. GAO/ECA). |
| **N6** | NOT a live-scraping or non-public-source ingester (G3). | WDI/SDG/OWID pre-published snapshots only. |
| **N7** | NOT a vendor-LLM inference path (G7, Murakumo-only). | |
| **N8** | NOT a substrate-engine replacement (G2, kotoba canonical). | |

### 5. Architecture

3 Pregel cells, R0 path-reserved (mirrors kanae's cell-count-scaled-to-scope; narashi has one fewer
domestic-vs-intergov split than kanae since inequality indicators are single-stream per country-year):

```
metric_ingest ──────────────── reuben (continuous; WDI/SDG/OWID snapshot → kotoba EAVT metricObservation)
cross_reference ─────────────── reuben (periodic; reads kanae fundFlowEdge read-only → crossReferenceNote, G8 non-causal)
narrative ────────────────────── gad (periodic; Murakumo-only trend narrative → metricNarrative, G4+G7)
```

No `publish` cell at R0 (mirrors kanae's own R1+ gating of `kanae_publish`); publication is an R2+
trigger requiring the same Council + 30-day public-comment bar as kanae's R3.

### 6. Lexicons (`com.etzhayyim.narashi.*`, 00-contracts/lexicons/com/etzhayyim/narashi/)

1. `metricObservation` — one `(indicator, jurisdiction, period, value, sourceRecordCids[], methodNoteCid)` fact
2. `crossReferenceNote` — narashi-side pairing of a `metricObservation` trend with a kanae `fundFlowEdge` in the same jurisdiction/period; `causalClaim` const `false` (G8)
3. `metricNarrative` — Murakumo-only factual trend description; `nonAdjudicatingNotice` const `true` (G4), `murakumoInferenceAttestation` required (G7)
4. `methodNote` — open, versioned normalization heuristic (G6)

### 7. R1 Activation Triggers

1. ADR ratified by Council Lv6+ ≥3 + 30-day public objection period closed;
2. `org.worldbank.api` / `org.un.unstats` / `org.ourworldindata` DataLad snapshots confirmed pinned and
   accessible (they already exist as raw datasets per the energy-indicator precedent; narashi's R1
   ingest reads the SI.POV.GINI / SI.POV.DDAY / SI.POV.NAHC / 10.1.1 series from the same snapshots);
3. `com.etzhayyim.narashi.metricObservation` + `.methodNote` schemas Council-attestation-reviewed
   (R1 minimum cell = `metric_ingest` only — no cross-reference, no narrative until R2);
4. Charter Rider scanner false-positive rate ≤5% over a 7-day trial on narashi-bound samples.

R2 adds `cross_reference` (G8 non-causal pairing with kanae) + `narrative` (first Murakumo trend
descriptions). R3 adds `publish` (first published aggregate visualization/report), gated identically
to kanae R3 (Council Lv7+ unanimity + 1 SBT = 1 vote for any named-jurisdiction element beyond what the
source already publishes — moot here since WDI/SDG/OWID data is jurisdiction-level by construction,
never named-individual).

## Consequences

**Positive**:
- Closes the gap identified by the operator question: etzhayyim now has a named actor whose subject
  is global economic inequality, consistent with the Mission Charter §1.8(sub) 格差アービトラージ
  activity and extending it from information-asymmetry (open-isco/open-naics/open-hs) to
  inequality-outcome data specifically.
- Reuses existing raw-dataset infrastructure (`org.worldbank.api`, `org.un.unstats`,
  `org.ourworldindata`) with zero new data-sourcing risk — the same Tier-A sources already vetted for
  `global-energy-datoms`.
- The G8 non-causal gate lets narashi cross-reference kanae's aid/loan flow data (answering "how much
  aid flowed to jurisdiction X while its Gini moved from A to B") without ever crossing into policy
  adjudication — same discipline family as danjo/kanae's G4.

**Negative / risks**:
- **Scope-creep risk toward N1/N2** (implicit pressure to "do something" about the inequality it
  observes) is the primary constitutional risk. Mitigation: N1–N4 are IMMUTABLE per this ADR's own
  terms; any future ADR proposing narashi-initiated redistribution must be a *new* ADR under Council
  Lv7+ unanimity, not a narashi extension.
- **Cross-reference misreading** (a reader inferring causality from a `crossReferenceNote` despite
  `causalClaim=false`) — mitigated the same way kanae mitigates flowNarrative misreading: schema-level
  const field + lint enforcement (a follow-up `no-narashi-causal-claim` lint, mirroring
  `no-kanae-adjudication.mjs`, is an R1 implementation task).
- **Indicator staleness** — WDI/SDG Gini and poverty series often lag 2-3 years behind the current
  year for many jurisdictions (a source-side limitation, not a narashi defect); every `metricObservation`
  carries its own `period`, so staleness is visible, not hidden.

## Alternatives Considered

1. **Extend the Liberation Ladder to non-adherents globally.** Rejected: this ADR's N1/N7 in
   ADR-2605261000 are IMMUTABLE (Council Lv7+ unanimity to amend), and doing so would also convert
   the mechanism into exactly the "fiat-replacement UBI" that ADR-2605261000 §5.N1 already rejected
   for adherents on principled (not just capacity) grounds.
2. **Extend kanae to also carry inequality-outcome indicators.** Rejected: kanae's `fundFlowEdge` is a
   flow-typed schema (money moving between endpoints); Gini/poverty-headcount are outcome metrics with
   no flow shape. Bolting outcome metrics onto a flow-edge schema would blur the same
   engine/visualizer-style boundary discipline the danjo/kanae split already protects. A sibling actor
   with its own lexicon, cross-referencing kanae read-only (G8), preserves the pattern.
3. **A single generic "global-inequality-datoms" repo with no actor wrapper** (cf.
   `global-legislation-datoms`, which is explicitly a passive catalog with no owning actor). Rejected
   for this scope: because narashi will eventually add Murakumo narrative + cross-reference + (R3)
   publication — active cells with an inference/publication surface — it needs the actor discipline
   (DID, constitutional gates, Council-gated activation) that a plain "-datoms" catalog repo does not
   carry. A pure "-datoms" projection remains the right shape for `metric_ingest`'s *output* (the raw
   projected EAVT), but the actor wrapper is required once narrative/publication cells exist.

## References

- ADR-2605192100 (Mission Charter — §1.8(sub) 格差アービトラージを埋める情報発信)
- ADR-2605261000 (Labor Liberation Transition Mechanism — Liberation Ladder; defines the N1/N7 boundary
  this ADR's N1 explicitly does not cross)
- ADR-2606032130 (Displacement Dividend — tenure-weighted Basic High Income; narrow automation-coupled
  precedent, not a general redistribution mechanism either)
- ADR-2605301600 (danjo — non-adjudicating cross-reference engine; G4 pattern source)
- ADR-2605302245 (danjo global fiscal-flow extension)
- ADR-2605302300 (kanae — global government fiscal-flow visualization; primary architectural template
  for this ADR, and the read-only upstream for G8 cross-reference)
- ADR-2605262130 (kotoba storage substrate unification — EAVT, no RisingWave)
- ADR-2605215000 (Murakumo-only inference — no vendor LLM, no RunPod)
- `orgs/etzhayyim/global-energy-datoms` (precedent "-datoms" projection repo; WDI/OWID/UN-SDG source
  pattern this ADR's `metric_ingest` reuses)
