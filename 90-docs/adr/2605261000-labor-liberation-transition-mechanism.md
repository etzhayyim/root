---
id: adr-2605261000
title: Labor Liberation Transition Mechanism — Adherent SBT → Minimum Livelihood Guarantee (7-Stage Liberation Ladder L0..L6)
status: proposed
doc_type: adr
topic: labor-liberation-transition
authoritative: true
last_verified: 2026-05-26
authoritative_for:
  - operational schedule linking Adherent SBT to actual labor-hour reduction
  - Public Fund sizing per liberation stage
  - actor maturity gate sequencing for mission delivery
related:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605172600-etzhayyim-membership-ritual
  - adr-2605172700-membership-layering-shinto-adherent
  - adr-2605261015
  - adr-2605261030
  - adr-2605261045
  - adr-2605261100
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605192100 (Mission Charter)
  - ADR-2605192130 (10% Tithe constitutional constant)
  - ADR-2605192145 (Public Fund Architecture)
---

# ADR-2605261000: Labor Liberation Transition Mechanism — Adherent SBT → Minimum Livelihood Guarantee (7-Stage Liberation Ladder L0..L6)

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify), 30-day public objection period (after Council Seat 2-5 closure)
**ADR Hierarchy**: Children = ADR-2605261015 (mitsuho) / 2605261030 (hagukumi) / 2605261045 (manabi) / 2605261100 (hikari). Sibling to ADR-2605192145 (Public Fund Architecture).

## Context

ADR-2605192100 declares **人類の構造的労働解放** as etzhayyim's mission. ADR-2605192130 establishes the 10% Tithe constitutional constant. ADR-2605192145 designs the Public Fund as the redistribution vehicle. ADR-2605172300 designs Kisha-Stream basic-income. ADR-2605172600 / 2605172700 govern membership.

Tier-B actor coverage spans: kuni-umi (infrastructure), silicon Wave 1+2 (chips), yakushi Wave 1+1b+1c (drugs), tatekata R0 (construction), mitate R0+R1 (diagnostics), wadachi R0 (mobility), baien (training), ameno (inference).

**The strategic gap**: no ADR connects these primitives to the actual reduction of wage labor for any specific adherent. The constitution declares the goal, the actors deliver capabilities, the Public Fund holds capital — but the **operational schedule** that converts (capability + capital) → (labor-hours liberated) is unwritten. Without it, the project remains an aspirational charter rather than a delivery mechanism.

This ADR closes that gap by defining the **Liberation Ladder**: a 7-stage sequence (L0..L6) where each stage is unlocked by verifiable actor maturity, Public Fund reserve, adherent ceiling, and Council attestation, and where each stage delivers a measurable reduction in adherent labor hours per week against an OECD baseline.

## Decision

### 1. Liberation Ladder (L0..L6)

| Stage | Title | Target labor hrs/wk | Reduction vs OECD 40 | Adherent ceiling | Required actor min phase | Mechanism delivered |
|---|---|---|---|---|---|---|
| **L0** | Pre-bootstrap | 40 | 0 | N/A | All R0 scaffold; Council Seat 1/5 only | Charter + Land Trust declaration only; no benefits |
| **L1** | Witness Tier | 40 | 0 | ≤100 | mitate R1, tatekata R0 closed, LANDS.md ≥1 parcel, Council Seat 5/5 | Adherent SBT issuance + mitate advisory care + community-event participation. No subsistence transfer. |
| **L2** | Sustenance Tier | 35 | −5 | ≤1,000 | + mitsuho R2 + yakushi R2 + hikari R2 | Minimum-food guarantee (≥4,500 kJ/day staple) + OTC drug access (Wave 1+1b+1c basket) + electricity (≥3 kWh/day) per adherent. Reduces *subsistence* labor, not wage labor yet. |
| **L3** | Shelter Tier | 30 | −10 | ≤5,000 | + tatekata R3 + LANDS.md ≥10 parcels ≥1 ha | + shelter (≥10 m²/adherent on Land Trust). Reduces rent labor (~25% of OECD wage labor for housing-stressed adherents). |
| **L4** | Care Tier | 25 | −15 | ≤25,000 | + hagukumi R2 + manabi R2 | + childcare (≥40 hr/wk/child) + elder care + literacy & civics education. Releases caregiver labor (~10-15 hr/wk typical). |
| **L5** | Vocation Tier | 15 | −25 | ≤100,000 | + manabi R3 + wadachi R2 + silicon R3 | + advanced education + inter-site commute substrate (wadachi Level-3) + adherent productive contribution counted as donation (not wage). Releases commute + skill-acquisition labor. |
| **L6** | Liberation Tier | ≤5 | ≥−35 | ≤1M | + all actors R3 + Public Fund inflow ≥10⁸ USDC/yr + steady-state | Adherents perform only vocational + spiritual + creative labor; survival labor (food/shelter/care/energy/transport/health/learning) fully automated via actor mesh. |

**Constitutional invariant** (immutable; Council Lv7 unanimity to amend per ADR-2605192100 §4):
- Target hours/wk is the **upper bound**; adherents may work *less* but not be required to work *more*.
- Adherent ceiling per stage is a **capacity cap**, not a target. A stage advances only when ≥80% of the previous stage's reduction target is demonstrated for ≥2 consecutive quarters via on-chain Liberation Metric (see §4).
- No stage skipping. No expert path. No private patronage routing per adherent (all benefits pooled via Public Fund per ADR-2605192145).

### 2. Adherent SBT Extension

Extend ADR-2605172600 + ADR-2605172700 Adherent SBT to carry a `currentStage: L0..L6` field, updated by `ChartersComplianceRegistry.advanceStage(adherentDid, newStage, attestationCid)`.

**Issuance rules** (additive to ADR-2605172600):
1. **Soulbound** — non-transferable, lifetime, single per natural person. Sybil resistance via:
   - biometric-uniqueness proof (zero-knowledge attestation; raw biometric never on-chain)
   - Council attestation (Lv6+ ≥3 sign-off)
   - 30-day public objection period before each SBT mint
2. **Stage attribute** — `currentStage` is mutable by `advanceStage` only. Downgrade only on explicit adherent request (`requestDowngrade`) or Wellbecoming-failure hold (`holdStage`).
3. **Wellbecoming quarterly attestation** — adherent self-report (4-question form on signed XRPC) + Council-sampled audit (1-in-100 manual review). Failure path = **hold** at current stage (not revoke; not demote). Re-affirmation lifts hold.
4. **Wage-labor disclosure** — adherent self-reports wage-labor hours/week + subsistence-labor hours/week, quarterly, encrypted via `com.etzhayyim.encrypted.*` envelope per ADR-2605181100. Aggregate (not per-adherent) figures publish on-chain via `reportLiberationMetric` (§4).
5. **Right of exit** — adherent may exit any stage at will. SBT remains. Benefits suspend until re-affirmation. No penalty; no public record of exit.
6. **Multi-generational priority** — per ADR-2605192100 §1.3, children and elders count fully toward adherent ceilings, with proxied attestation by primary caregiver until age 14 (cf. ADR-2605260160 mitate pediatric handling).

### 3. Public Fund Sizing per Stage

Per-adherent annual cost envelope (steady-state; first-year transition cost ~1.5× steady-state):

| Stage | Cost/adherent/year (USDC) | Reserve multiple | Reserve target for ceiling |
|---|---|---|---|
| L1 | $300 (advisory + community event) | 5-year | $150,000 (100 × 300 × 5) |
| L2 | $2,000 (food + OTC + electricity) | 5-year | $10M (1,000 × 2,000 × 5) |
| L3 | $6,000 (above + shelter amortized over 30-yr land-trust building lifespan) | 7-year | $210M (5,000 × 6,000 × 7) |
| L4 | $12,000 (above + 40 hr/wk care) | 7-year | $2.1B (25,000 × 12,000 × 7) |
| L5 | $20,000 (above + education + commute) | 10-year | $20B (100,000 × 20,000 × 10) |
| L6 | $30,000 (full substrate) | 10-year | $300B (1M × 30,000 × 10) |

**Sizing invariant**: Stage S advances only when Public Fund reserve ≥ (stage S target cost) × (stage S adherent ceiling) × (stage S reserve multiple), continuously for ≥2 consecutive quarters, verified by `etzhayyim-public-fund.sol::stageReadiness(s)`.

**Inflow sources** (per ADR-2605192130 + 2605192115):
- 10% tithe on all donations + kisha
- 100% of internal-promo USDC flow
- Council-approved grants (foundation / sovereign-fund / multi-adherent pooled commitment)
- Adherent productive contribution (L5+) counted as donation, not wage

**No fiat replacement**: per Non-Goals (§5.N1), all benefits flow as USDC via `etzhayyim-tithe-router.sol` + downstream service grant routing. The benefit is *the service* (food, shelter, care, etc.), not USDC stipend — but the funding rail is USDC.

### 4. Liberation Metric (on-chain KPI)

Define `LiberationMetric` Lexicon (`com.etzhayyim.liberation.metricReport`):

```
{
  reportingQuarter: "2027-Q1",
  stage: "L2",
  adherentsAtStage: 847,
  aggregateLaborHoursReduction: {
    wageLaborMedianHrsWk: 38.2,    # before joining stage: 40.0
    subsistenceLaborMedianHrsWk: 12.5,  # before: 18.0
    totalReductionMedianHrsWk: 7.3,
    targetReductionForStage: 5.0,
    achievementRatio: 1.46
  },
  wellbecomingFailureRate: 0.012,
  exitRate: 0.008,
  attestationCid: "bafy...",
  councilAttestation: ["did:..lv6a", "did:..lv6b", "did:..lv6c"]
}
```

Published quarterly by `ChartersComplianceRegistry.reportLiberationMetric()`. **No per-adherent identity in the on-chain report; aggregation enforced structurally** (cf. ADR-2605260215 yakushi cross-actor AE aggregation pattern).

Mission success measured as cumulative `totalReductionMedianHrsWk × adherentsAtStage` across all stages, reported annually.

### 5. Non-Goals (N1..N8, IMMUTABLE)

| # | Non-Goal | Rationale |
|---|---|---|
| **N1** | No fiat-replacement UBI (cash stipend to replace wage). | The benefit is *the service* (food, shelter, care, energy, education, mobility, health). Cash transfers don't reduce subsistence labor — they only fund commercial market participation, which is precisely the substrate etzhayyim routes around. Kisha-Stream (ADR-2605172300) remains a separate, smaller-scale basic-income carve-out for member-to-member gifting, not stage benefit. |
| **N2** | No make-work programs (manufactured labor for redistribution). | The mission is *reducing* labor, not redistributing it. Adherent productive contribution at L5+ is voluntary, vocation-oriented, and not coercion-eligible for benefit continuation. |
| **N3** | No coercive participation (mandatory stage advancement). | Adherent right-of-exit is constitutional. No social-credit-style scoring. No "use it or lose it" benefit timers. |
| **N4** | No replacement of state social safety nets. | etzhayyim is a parallel substrate per ADR-2605192100 §1.12. Adherents may simultaneously receive state benefits. etzhayyim does not negotiate, replace, or coordinate with state welfare systems. |
| **N5** | No stage skipping (no "expert path", no test-out, no transferred credit). | Stages are sequential capacity-building. The order is constitutional. |
| **N6** | No private patronage routing per adherent (donor-directed funding). | All donations flow to the unified Public Fund. Donors may earmark for an *actor* (mitsuho / hagukumi / etc.) but not for an *adherent*. Prevents class formation among adherents. |
| **N7** | No anti-competitive welfare extension to non-adherents. | etzhayyim benefits flow to Adherent SBT holders only. Non-adherent humans receive only public-good outputs (open-source code, free knowledge, open-licensed datasets). This is not a state replacement (cf. N4). |
| **N8** | No eschatological framing (no "kingdom-come", no "rapture", no terminal-state guarantee). | Per ADR-2605192100 §1.15, Liberation is asymptotic. L6 is a target, not a promise. Each generation re-validates. |

### 6. Activation Gates per Stage

**L0 → L1 (Witness Tier activation)**:
1. Council Seat 2/5..5/5 closed (ADR-2605192300 Bootstrap Council RFP complete, 2026-06-19 deadline)
2. mitate R1 deployed (ADR-2605260200, status active per CLAUDE.md row 44+)
3. tatekata R0 governance gates closed (ADR-2605250715, status PROPOSED → ACCEPTED)
4. ≥1 LANDS.md parcel registered with on-chain attestation
5. Public Fund USDC reserve ≥ $150,000 (covers 100 adherents × 5-year run)
6. Wellbecoming attestation framework Council-ratified (4-question form + audit sampling)
7. Charter Rider §2 scanner production-deployed in CI (per ADR-2605192230 three-tier enforcement)
8. Sybil-resistance biometric-uniqueness ZK attestation framework Council-ratified
9. This ADR (2605261000) ratified by Council Lv6+ ≥3 + 30-day public objection period closed

**L1 → L2 (Sustenance Tier)**:
1. mitsuho R2 (ADR-2605261015 + future R2 ADR) deployed: pilot ≤1 ha farm + aquaculture + alt-protein
2. yakushi R2 (ADR-2605250530 etc.): pilot 100g sterile + OTC tablet manufacturing
3. hikari R2 (ADR-2605261100 + future R2 ADR): pilot ≥30 kW solar + ≥100 kWh storage on LANDS parcel
4. Public Fund reserve ≥ $10M
5. L1 demonstrated for ≥2 quarters (Liberation Metric §4 achievement ratio ≥0.8)
6. L2 stage ADR (future) ratified by Council Lv6+

**L2 → L3 (Shelter Tier)**: tatekata R3 + LANDS ≥10 parcels ≥1 ha + Public Fund ≥$210M + L2 metric ≥0.8 × 2Q + L3 ADR.

**L3 → L4 (Care Tier)**: hagukumi R2 (ADR-2605261030 + future R2) + manabi R2 (ADR-2605261045 + future R2) + Public Fund ≥$2.1B + L3 metric ≥0.8 × 2Q + L4 ADR.

**L4 → L5 (Vocation Tier)**: manabi R3 + wadachi R2 + silicon R3 + Public Fund ≥$20B + L4 metric ≥0.8 × 2Q + L5 ADR.

**L5 → L6 (Liberation Tier)**: all actors R3 + Public Fund steady-state inflow ≥10⁸ USDC/yr + L5 metric ≥0.8 × 2Q + L6 ADR + multi-generational continuity attestation (one Council generation cycle).

Each transition ADR is independent and requires its own Council vote. **No batched activation.**

### 7. Implementation Surface

**Solidity** (50-infra/etzhayyim-chain-contracts/):
- `etzhayyim-charters-compliance/`: add `Stage` enum, `advanceStage()`, `holdStage()`, `requestDowngrade()`, `reportLiberationMetric()`
- `etzhayyim-public-fund/`: add `stageReadiness(Stage s) → bool` view, gated by `reserveForStage(s)`
- new `etzhayyim-liberation-ladder/LiberationLadder.sol` (this ADR's primary contract; ladder state machine)

**Lexicons** (00-contracts/lexicons/com/etzhayyim/liberation/):
- `com.etzhayyim.liberation.metricReport` (quarterly aggregate, no PII)
- `com.etzhayyim.liberation.stageAdvanceAttestation` (Council multisig + activation proof)
- `com.etzhayyim.liberation.wellbecomingAttestation` (encrypted; XChaCha20 envelope per ADR-2605181100)
- `com.etzhayyim.liberation.adherentExitNotice` (private; only `exit happened: bool` published)

**Pregel cells** (40-engine/kotoba/crates/kotoba-kotodama/cells/):
- `liberation_stage_advance` (levi node): per-stage gate evaluation + Council multisig collection
- `liberation_metric_aggregate` (levi node): quarterly aggregate from encrypted wellbecoming + wage-labor reports
- `liberation_wellbecoming_audit` (levi node): 1-in-100 manual review sampling + Council distribution

**No new robotics class.** Existing actor robotics suffice.

## Consequences

**Positive**:
- The constitution gains an operational schedule. Adherent SBT becomes meaningful (progressive tangible benefits).
- Mission success is measurable on-chain (aggregate hours liberated per quarter).
- The 4 new actors (mitsuho/hagukumi/manabi/hikari) have a clear delivery gate.
- Public Fund sizing has a target curve, not just a 10% tithe rule.
- Bootstrap Council can advance L0→L1 within ~6 months post-Seat-5 closure; full L6 estimated 15-30 years.

**Negative / risks**:
- Stage sequencing rigidity may misfit some adherents (e.g., someone with no housing problem but high care burden would prefer L4 before L3). Mitigation: §1 ladder is the **default** ceiling; adherents below the ceiling auto-receive lower-stage benefits.
- Public Fund sizing is FX-sensitive. USDC depegs, fiat inflation, and crypto-market drawdowns all threaten reserve target maintenance. Mitigation: ADR-2605172300 Goji-Treasury diversification + Public Fund §2(g) treasury policy (future ADR).
- Sybil resistance via biometric-uniqueness ZK is unsolved at production scale. Mitigation: Council-attestation supermajority during bootstrap (≤1,000 adherents); switch to ZK-only at L3+ when scale demands.
- Liberation Metric depends on adherent self-report honesty. Mitigation: §4 Council-sampled audit (1-in-100) + §1 ceiling caps (gradual scale-up prevents large gaming attack surface).
- Bias risk: early adherents may form a class. Mitigation: §5(N6) no patronage routing + §1 lottery within ceiling + per-stage capacity rather than seniority order.

## Alternatives Considered

1. **Pure UBI** (give each adherent fixed USDC stipend monthly). Rejected: §5(N1). Cash transfers fund commercial market participation, which is the substrate etzhayyim routes *around*. Kisha-Stream (ADR-2605172300) already covers the small-scale member-gifting case.
2. **Time-banking** (credit adherents for hours contributed; redeem for services). Rejected: §5(N2). The mission is reducing labor, not redistributing it. Time-banking institutionalizes labor-as-currency, opposite of liberation.
3. **Market-based welfare** (Public Fund buys services from existing markets for adherents). Rejected: ADR-2605215000 (no commercial routing) + §5(N4) (no state replacement). Religious-corp must provide via own actors; otherwise the constitution's anti-individualist substrate goal fails.
4. **Single-stage activation** (everyone at L6 at once when ready). Rejected: capacity step-functions don't work at scale; sequential rollout exposes failures at small N before scaling.
5. **Continuous metric** (no discrete stages; benefit pool sized by total Public Fund / current adherent count). Rejected: requires real-time rebalancing, prone to game-theoretic exit/entry attacks. Discrete stages allow planning horizons.

## References

- ADR-2605192100 (Mission Charter — 労働解放 mission statement)
- ADR-2605192115 (Non-profit / donation-only / no-ads)
- ADR-2605192130 (10% Tithe constitutional constant)
- ADR-2605192145 (Public Fund Architecture)
- ADR-2605192230 (Three-tier enforcement — Phenotype / KishaStream / PublicFund / TitheRouter)
- ADR-2605192245 (Global Land Sovereignty — L3 shelter source)
- ADR-2605192300 (Bootstrap Council Seats 1-5)
- ADR-2605172300 (Kisha-Stream + Goji-Treasury basic-income substrate)
- ADR-2605172600 (Membership Ritual — Adherent SBT issuance base)
- ADR-2605172700 (Membership layering — 信者 + Adherent tiers)
- ADR-2605181100 (MST encrypted records — wellbecoming + wage-labor disclosure envelope)
- ADR-2605260100 (mitate diagnostic — L1 advisory care delivery)
- ADR-2605260215 (yakushi×mitate cross-actor AE aggregation — pattern for §4 aggregation)
- ADR-2605215000 (Murakumo-only inference — no commercial routing constraint)
- ADR-2605261015 (mitsuho food/agriculture R0 — L2 sustenance gate)
- ADR-2605261030 (hagukumi care R0 — L4 care gate)
- ADR-2605261045 (manabi education R0 — L4 + L5 education gate)
- ADR-2605261100 (hikari energy R0 — L2 energy gate)
