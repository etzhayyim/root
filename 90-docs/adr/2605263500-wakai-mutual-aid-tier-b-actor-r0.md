---
id: adr-2605263500-wakai-mutual-aid-tier-b-actor-r0
title: "ADR-2605263500: wakai (和会) — non-profit religious-corp mutual aid substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: wakai-mutual-aid-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: solidarity
weight: 0.55
priority_note: "Seventh-priority gap-closure actor (gap audit row 7 = 共済 / mutual aid). NOT insurance (no premium-as-contract; no actuarial pricing; no claim adjudication; no policy denial). Member-to-member solidarity pooling per Charter §1.7 反個人主義 + 多世代 + harmony invariant. 任意団体 internal mutual aid substrate at did:web:wakai.etzhayyim.com (20-actors/wakai/). Etymology: 和会 (wakai) = harmony/reconciliation gathering; classical 互助会 mutual aid society; 和 (wa) Charter §1.7 + 会 assembly. Risk-sharing scope: health-event (cross-actor iyashi + hagukumi + yakushi) / disability / death-of-breadwinner / unemployment / disaster (kazaori emergency pool activation). Public Fund (toritate cross-actor) is the backstop when community pool insufficient (Council Lv6+ ≥4/7 approves backstop grant). **Constitutional septad**: (1) NOT insurance G3+N1 (no premium-as-contract; no actuarial pricing; no claim denial; member-to-member solidarity only) / (2) NO commercial insurance software G4+N8 (Guidewire / Duck Creek / Insurity / Sapiens / Majesco / SAP Insurance / Oracle Insurance / Lemonade-as-vendor / Hippo-as-vendor PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty exposing member health/disability/employment posture) / (3) NO commercial re-insurance G5+N6 (Munich Re / Swiss Re / SCOR / Hannover Re / Berkshire Hathaway Re PROHIBITED; risk stays in community + Public Fund backstop) / (4) NO investment return promise G6+N2 (Charter Rider §2(b) speculative finance prohibition; mutual aid pool is solidarity reserve, not investment vehicle; NO ROI promised) / (5) NO discrimination on pre-existing condition G7 (no underwriting; no exclusion; no risk-based rejection) / (6) Contribution voluntary + ability-scaled G8 per Charter §1.7 反個人主義 (no minimum contribution; member self-attests ability) / (7) Distribution by Council Lv6+ ≥3 community discernment G9 (need-based; cross-link to iyashi/hagukumi/yakushi event attestation; NOT claim adjudication). G10 Public Fund backstop via Council Lv6+ ≥4/7 (cross-actor toritate). G11 NO payroll for administrators (vocation-flow L5 stewards). G12 Murakumo-only inference. 6 cells / 5 Lexicons / 12 gates / 12 non-goals / 4-phase R0..R3."
authoritative_for:
  - wakai actor R0 charter
  - religious-corp mutual aid substrate single SoT
  - `com.etzhayyim.wakai.*` Lexicon namespace boundary
  - NOT-insurance invariant (no premium / no actuarial / no claim denial)
  - prohibition on commercial insurance software (Guidewire / Duck Creek / Insurity / Sapiens / Majesco / SAP Insurance / Oracle Insurance / Lemonade / Hippo as vendor)
  - prohibition on commercial re-insurance (Munich Re / Swiss Re / SCOR / Hannover Re / Berkshire Hathaway Re)
  - voluntary ability-scaled contribution per Charter §1.7 反個人主義
  - community discernment distribution (NOT claim adjudication)
  - Public Fund backstop pattern via Council Lv6+ ≥4/7
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261000
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
  - adr-2605263200-kazaori-disaster-response-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2605263500: wakai (和会) — non-profit religious-corp mutual aid substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified mutual aid (共済) as
priority row 7. religious-corp has the on-chain financial primitives
(TitheRouter income split per ADR-2605192130 + Public Fund Safe
Council Lv6+ ≥4/7 disbursement per ADR-2605192145), the steward
classification (Liberation Ladder L0..L6), the accounting transparency
(toritate ADR-2605262900) — but no member-to-member solidarity pool
substrate. The Public Fund grant flow is a religious-corp → member
flow (community-funded); wakai is a member → member solidarity flow
that complements Public Fund.

kazaori (ADR-2605263200) explicitly path-reserved wakai as future
cross-actor for emergency mutual aid pooling. This ADR realizes that
path-reserve and ships wakai as a first-class Tier-B actor.

The discipline boundary that wakai must hold is critical:

- wakai is **NOT insurance**. There is no premium-as-contract, no
  actuarial pricing, no claim adjudication, no policy denial.
- wakai is **NOT a financial product**. No investment return
  promised; no ROI; no policy term; no surrender value.
- wakai is **NOT state-licensed**. No insurance commissioner
  registration; 任意団体 internal substrate.
- wakai is **NOT a commercial-insurance-software platform consumer**.
  Guidewire / Duck Creek / Insurity / Sapiens / Majesco / SAP
  Insurance / Oracle Insurance / Lemonade / Hippo PROHIBITED per
  Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-
  sovereignty exposing member health/disability/employment posture.

Constitutional constraints (inherited; not adjustable):

- **Charter Rider §2(b) speculative finance prohibition** is critical
  here. Mutual aid pooling is a community solidarity reserve, not an
  investment vehicle. NO ROI promised; NO investment-return claim;
  pool funds are held in stable-asset form (USDC on Base L2 per
  ADR-2605172100; no DeFi yield farming; no token speculation).
- **Charter §1.7 反個人主義** — voluntary ability-scaled
  contribution; no minimum amount; member self-attests ability;
  contribution variance per member is expected and honored.
- **Public Fund backstop** (ADR-2605192145) — when community pool
  insufficient, Council Lv6+ ≥4/7 approves Public Fund grant; the
  two pools are complementary, not redundant.
- **Murakumo-only inference** (ADR-2605215000) — need-prediction +
  pool-balance forecasting via judah LiteLLM; commercial insurance-
  AI (Lemonade NLP / Tractable / Carpe Data / etc.) PROHIBITED.
- **NO payroll for administrators** (G11) — wakai administrators are
  vocation-flow L5 stewards per Liberation Ladder; cross-actor
  enforcement with chigiri.stewardLaborAttestation + toritate
  ledgerEntry.category enum exclusion.
- **kotoba canonical substrate** (ADR-2605262130) — wakai records
  live in MST + IPFS + Base L2 anchor.

# Decision

Create `wakai` (和会) as a Tier-B religious-corp mutual aid substrate
actor at `20-actors/wakai/`, with DID `did:web:wakai.etzhayyim.com`,
Lexicon namespace `com.etzhayyim.wakai.*`. R0 = scaffold only; all
cells import-time `RuntimeError`.

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `wakai` (和会 — harmony/reconciliation gathering; classical 互助会 mutual aid society) |
| DID | `did:web:wakai.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.wakai.*` |
| Form | 任意団体 internal mutual aid substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格; NOT a state-licensed insurance entity — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| NOT-insurance invariant | No premium-as-contract / no actuarial pricing / no claim adjudication / no policy denial / no investment return promise |
| Cross-actor | kazaori (emergency mutual aid pool activation; path-reserved in ADR-2605263200) / iyashi + hagukumi + yakushi (health-event support routing) / toritate (Public Fund backstop accounting; mutual aid pool transparency) / chigiri (membership verification + procedural attestation) / Public Fund Safe (backstop disbursement) / TitheRouter (income flow read for aggregate solidarity capacity) |

## §2. Scope (5 sections)

### A. Member-to-member mutual aid pool

- Voluntary ability-scaled contribution (member self-attests; no
  minimum); no premium-as-contract;
- Pool held in USDC on Base L2 (stable-asset only per
  ADR-2605172100; NO DeFi yield farming; NO token speculation);
- Aggregate pool state published in `mutualAidPoolStateReport` per
  period (no individual member-contribution amounts public);
- Cross-actor toritate accounting transparency.

### B. Need-based distribution (Community Discernment, NOT Claim Adjudication)

- Member experiences need event (health / disability / death-of-
  breadwinner / unemployment / disaster);
- Member or community-member-on-behalf submits need attestation;
- Council Lv6+ ≥3 + community attestation chain (≥3 community
  members attesting need) → distribution approval;
- NO actuarial pricing / NO claim denial / NO underwriting / NO
  pre-existing condition exclusion (G7);
- Distribution from pool; if pool insufficient, Public Fund
  backstop request triggered (§E).

### C. Emergency pool activation (kazaori cross-actor)

- During Council-Lv6+-declared emergency (kazaori
  emergencyDeclarationAttestation active);
- wakai pool dispatches emergency mutual aid to affected community
  sites via `emergencySupplyDispatch` cross-link with kazaori;
- Distribution prioritizes vulnerable populations (hagukumi
  cross-link).

### D. Health event support (iyashi + hagukumi + yakushi cross-actor)

- Chronic care continuity gap funding (iyashi
  chronicCareContinuityRecord cross-link);
- Medical supply gap funding (yakushi cross-link);
- Daily-living support gap funding (hagukumi cross-link);
- All distributions are need-based + community-discerned, NOT
  claim-adjudicated.

### E. Public Fund backstop (toritate cross-actor)

- When wakai community pool insufficient for distribution;
- Public Fund Safe Council Lv6+ ≥4/7 approves backstop grant;
- Cross-actor toritate.externalAuditorEngagement pattern reused for
  large backstop events;
- Backstop grant recorded as `publicFundBackstopRequest` Lexicon.

## §3. Cells (6 Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/wakai_*/`)

All R0 path-reserved; import-time `RuntimeError("wakai R0 scaffold: activate via Council ADR + R1 ratification + initial pool seed + ≥3 community discernment witness candidates")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `mutual_aid_pool_contribution` | asher | continuous | member voluntary contribution → mutualAidContributionAttestation |
| 2 | `mutual_aid_distribution` | asher | event | need attestation + Council ≥3 discernment → mutualAidDistributionAttestation |
| 3 | `emergency_pool_activation` | asher (kazaori-paired) | event | kazaori emergencyDeclaration active → emergency dispatch coordination |
| 4 | `health_event_support` | asher (iyashi+hagukumi+yakushi-paired) | event | health event cross-link → distribution routing |
| 5 | `public_fund_backstop_request` | asher (toritate-paired) | event | pool insufficient → Council Lv6+ ≥4/7 backstop request |
| 6 | `pool_state_reporting` | asher | continuous (monthly summary) | aggregate pool state → mutualAidPoolStateReport |

R1 activation gates each cell separately + initial pool seed (Public
Fund seed grant Council Lv6+ ≥4/7) + ≥3 community discernment
witness candidates on file.

## §4. Lexicons (5, all under `com.etzhayyim.wakai.*`)

| # | Lexicon | Consumer cell | Description |
|---|---|---|---|
| L1 | `mutualAidContributionAttestation` | mutual_aid_pool_contribution | Per-contribution attestation; G6 STRUCTURAL: investmentReturnPromised const false; G8 voluntary + ability-scaled |
| L2 | `mutualAidDistributionAttestation` | mutual_aid_distribution + emergency + health | Per-distribution; G9 STRUCTURAL: communityDiscernmentAttestations minLength 3 + Council Lv6+ ≥3; G7 noPreExistingConditionExclusion const true |
| L3 | `mutualAidPoolStateReport` | pool_state_reporting | Per-period aggregate pool state; NO individual member-contribution amounts public (aggregate only) |
| L4 | `publicFundBackstopRequest` | public_fund_backstop_request | When pool insufficient; Council Lv6+ ≥4/7 attestations + toritate cross-link |
| L5 | `silenWakaiReview` | (Council attestation scope) | Quarterly Council review; G3/G4/G5/G6/G7/G9/G11 const-field structural enforcement |

## §5. Gates (12, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every wakai document MUST pass `kotodama.organism.sensors.charter_rider.scan()` §2(a)-(h). |
| **G2** | Every record MUST emit `com.etzhayyim.wakai.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **NOT insurance** — no premium-as-contract; no actuarial pricing; no claim adjudication; no policy denial; no underwriting. |
| **G4** | **NO commercial insurance software** — Guidewire / Duck Creek / Insurity / Sapiens / Majesco / SAP Insurance / Oracle Insurance / Lemonade-as-vendor / Hippo-as-vendor PROHIBITED per Charter Rider §2(e) + §2(c). |
| **G5** | **NO commercial re-insurance** — Munich Re / Swiss Re / SCOR / Hannover Re / Berkshire Hathaway Re PROHIBITED; risk stays in community; Public Fund backstop is the only escalation. |
| **G6** | **NO investment return promise** — Charter Rider §2(b) speculative finance prohibition; pool held in stable-asset form (USDC on Base L2); NO DeFi yield farming; NO token speculation; `mutualAidContributionAttestation.investmentReturnPromised` const false. |
| **G7** | **NO discrimination on pre-existing condition** — no underwriting; no exclusion; no risk-based rejection; `mutualAidDistributionAttestation.noPreExistingConditionExclusion` const true. |
| **G8** | **Contribution voluntary + ability-scaled** — Charter §1.7 反個人主義; no minimum contribution; member self-attests ability. |
| **G9** | **Distribution by community discernment** — Council Lv6+ ≥3 + ≥3 community attestation chain; NOT claim adjudication; need-based only. |
| **G10** | **Public Fund backstop** via Council Lv6+ ≥4/7 (cross-actor toritate). |
| **G11** | **NO payroll for administrators** — vocation-flow L5 stewards (cross-actor enforcement). |
| **G12** | Murakumo-only inference per ADR-2605215000 — commercial insurance-AI (Lemonade NLP / Tractable / Carpe Data) PROHIBITED. |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT insurance (premium-based product). |
| N2 | NOT investment fund / no ROI (Charter Rider §2(b)). |
| N3 | NOT pension / retirement product (separate future actor if needed). |
| N4 | NOT medical insurance (iyashi + Public Fund handles healthcare). |
| N5 | NOT speculative finance (Charter Rider §2(b) PROHIBITED). |
| N6 | NOT re-insurance / risk transfer to commercial insurers (G5). |
| N7 | NOT cryptocurrency speculation (Charter Rider §2(b)). |
| N8 | NOT commercial insurance software integrator (G4). |
| N9 | NOT a state-licensed insurance entity. |
| N10 | NOT closed-source. |
| N11 | NOT payroll-based administrators (G11). |
| N12 | NOT actuarial discrimination (G7). |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved. 5 Lexicons schema skeleton. | No deployment |
| **R1** | post-Bootstrap-Council + initial pool seed (Council Lv6+ ≥4/7 Public Fund seed grant) + ≥3 community discernment witness candidates | Activate 3 core cells: `mutual_aid_pool_contribution` + `mutual_aid_distribution` + `pool_state_reporting`. ≤50 members, ≤$50k USDC pool. | asher (single node) |
| **R2** | post-R1 + 30-day public objection + 3 community-site attestations | Activate +2 cells: `health_event_support` (iyashi+hagukumi+yakushi triad) + `public_fund_backstop_request` (toritate cross-actor). ≤500 members, ≤$500k pool. | asher + gad (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + ≥1 real distribution cycle completed + silenWakaiReview cycle established | Activate +1 cell: `emergency_pool_activation` (kazaori cross-actor). Community-scale ≤25,000 members, ≤$5M pool. | asher + gad + zebulun (3 nodes) |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `kazaori.emergency_supply_dispatch` | ↔ | Emergency mutual aid pool activation during declared emergency (kazaori path-reserved wakai cross-actor at ADR-2605263200) |
| `iyashi` | ↔ (health event support) | Chronic care continuity gap funding; clinical event support routing |
| `hagukumi` | ↔ (daily-living support) | Daily-living gap funding; multi-gen support |
| `yakushi` | ↔ (medication support) | Medication supply gap funding |
| `toritate` | ↔ (accounting) | Mutual aid pool transparency + Public Fund backstop accounting + ledgerEntry cross-link |
| `chigiri.member_onboarding` | → (read) | Member Adherent SBT verification |
| `chigiri.stewardLaborAttestation` | → (read) | Administrator L5 vocation-flow classification (G11) |
| Public Fund Safe | ← (backstop disbursement) | Council Lv6+ ≥4/7 backstop when pool insufficient |
| TitheRouter | → (read; aggregate solidarity capacity) | Aggregate solidarity-capacity read (informs pool-balance forecasting) |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605263500-wakai-mutual-aid-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/wakai/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 5 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/wakai/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 74 + Repo Layout entry.

No code activation in R0.

# Consequences

**Positive**:

- Closes gap-audit #7 priority (mutual aid) — religious-corp finally
  has a member-to-member solidarity pool to complement Public Fund
  (religious-corp → member flow);
- G3 NOT-insurance invariant + G4 + G5 + G6 constitutional discipline
  structurally separates wakai from the commercial insurance
  industry — no premium-as-contract creep, no actuarial pricing
  creep, no investment-vehicle drift;
- G7 anti-discrimination invariant (no underwriting / no
  pre-existing condition exclusion) operationalizes Charter §1.7
  反個人主義 + 多世代 + mutual-aid solidarity at the schema layer;
- G8 voluntary ability-scaled contribution preserves member dignity
  (no minimum-contribution coercion);
- G9 community discernment (not claim adjudication) preserves
  religious-corp 1 SBT = 1 vote + Council attestation pattern in
  the financial-solidarity domain;
- Cross-actor kazaori realization (kazaori path-reserved wakai at
  R0; this ADR ships R0) reduces architectural debt;
- Public Fund backstop pattern (G10) provides safety net without
  blurring boundaries between member-to-member solidarity and
  religious-corp → member grant flow.

**Negative / cost**:

- Initial pool seed requires Council Lv6+ ≥4/7 Public Fund seed
  grant; Bootstrap Council Seat 2-5 RFP must surface willing
  council vote for this seed (R1 gating dependency);
- Community discernment scales sublinearly — at R3 community-scale
  ≤25,000 members, ≥3 community attestations per distribution
  becomes a real coordination burden; need discernment-pool
  management framework at R3;
- Pool held in USDC creates dependency on Base L2 + USDC stability;
  during stablecoin de-peg events (rare but observed), pool value
  is at risk; G6 prohibits DeFi yield farming as mitigation
  (correct discipline; cost = no yield to offset de-peg risk);
- G7 anti-discrimination means high-cost-event members are not
  excluded; this is by design but means pool-sustainability is
  community-funded not actuarially-funded.

**Forward-compatibility**:

- Pension / retirement-like long-horizon mutual aid (gap audit row
  not enumerated) integrates as future cell extension if Council
  approves;
- Cross-religious-corp federation potential — mutual aid pool
  cross-referencing via chigiri.stewardLaborAttestation cross-actor
  pattern;
- Pool diversification beyond USDC (if Base L2 stablecoin diversity
  matures) requires Council Lv6+ ≥4/7 approval + Charter Rider
  §2(b) re-affirmation per asset.

# Alternatives Considered

1. **Use Lemonade / Hippo / Sun Life / etc. as the insurance
   product backend**. Rejected per G4 + Charter Rider §2(e)+§2(c).
   Vendor closed query-tracking on member health/disability/
   employment is structurally unacceptable.

2. **Allow re-insurance via Munich Re / Swiss Re for catastrophic
   tail risk**. Rejected per G5. Risk stays in community; Public
   Fund backstop is the only escalation; catastrophic-tail-risk is
   shared via Council Lv6+ ≥4/7 cross-actor toritate audit pattern.

3. **Allow DeFi yield farming on pool funds for sustainability**.
   Rejected per G6 + Charter Rider §2(b). Pool is solidarity reserve,
   not investment vehicle.

4. **Allow actuarial pricing with risk-based contribution scaling**.
   Rejected per G3 + G7 + G8. Voluntary ability-scaled contribution
   per Charter §1.7 反個人主義 is structural; actuarial pricing
   would re-introduce the insurance-product framing wakai
   constitutionally rejects.

5. **Make contribution mandatory for Adherent SBT preservation**.
   Rejected per G8 — voluntary + ability-scaled. Mandatory
   contribution would be a coercive economic structure analogous
   to musubi G7 bride price prohibition.

6. **Defer until Public Fund Council Lv7+ ratifies a dedicated
   wakai charter**. Rejected — R0 scaffold has zero governance cost
   (path-reserved; all cells RuntimeError); R1 activation gates the
   Council Lv6+ ≥4/7 pool seed grant.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap
- ADR-2605192100 — Mission Charter (§1.7 反個人主義 + 多世代 + harmony)
- ADR-2605192130 — 10% Tithe redistribution (TitheRouter cross-link)
- ADR-2605192145 — Public Fund architecture (backstop source)
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2(b) speculative finance + §2(e) + §2(c))
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605215000 — Inference Murakumo-only (G12)
- ADR-2605261000 — Labor Liberation Transition Mechanism (G11 vocation-flow)
- ADR-2605262130 — Kotoba storage substrate
- ADR-2605262700 — chigiri (cross-actor membership + procedural)
- ADR-2605262900 — toritate (cross-actor accounting + Public Fund backstop)
- ADR-2605263000 — iyashi (cross-actor health event support)
- ADR-2605263200 — kazaori (cross-actor emergency pool activation; kazaori path-reserved wakai at R0)
- `/CHARTER-RIDER.md` §2(b) + §2(e) + §2(c) — gate sources
