---
id: adr-2605301020-basic-high-income-imputed-and-commons-asset-doctrine
title: "ADR-2605301020: Basic High Income — Imputed-Income (flow) + Commons-Asset (stock) Doctrine for In-Kind Adherent Provision"
status: proposed
doc_type: adr
topic: basic-high-income-imputed-commons-asset
authoritative: true
last_verified: 2026-05-30
authoritative_for:
  - definition of "income" and "asset" for adherents under the non-cash religious-corp economy
  - imputed-income (flow) accounting of in-kind service provision
  - commons-asset (stock) accounting of SBT-bound non-alienable access rights
  - reframing of the Liberation Ladder L0..L6 as a Basic High Income target
authoritative_for_clarifies:
  - ADR-2605261000 §5 N1 (no fiat-replacement UBI) — this ADR is fully consistent with N1 and does NOT amend it
related:
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605262900-toritate-accounting-audit
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605192100 (Mission Charter — constitutional constants)
  - ADR-2605261000 (Labor Liberation Transition Mechanism — ladder + N1..N8)
  - ADR-2605192145 (Public Fund Architecture)
  - ADR-2605262900 (toritate accounting — on-chain SSoT)
---

# ADR-2605301020: Basic High Income — Imputed-Income (flow) + Commons-Asset (stock) Doctrine for In-Kind Adherent Provision

**Date**: 2026-05-30
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ ≥3 (ratify), 30-day public objection period
**ADR Hierarchy**: Clarifying extension of ADR-2605261000 (Labor Liberation Transition Mechanism). Sibling to ADR-2605192145 (Public Fund Architecture). Accounting surface delegated to ADR-2605262900 (toritate).

## Context

A recurring question: *does etzhayyim provide a "high income" to 信者 (adherents)?*

The naive answer is "no" — ADR-2605261000 §5 **N1** constitutionally forbids fiat-replacement UBI (cash stipends to replace wages), and the Mission Charter (ADR-2605192100 §2) locks `non_profit_only` + `donation_only`. So no adherent receives a salary, dividend, or cash stipend, and none ever will.

But that answer conflates **income** with **cash**. The mission's terminal state — Liberation Tier **L6** (ADR-2605261000 §1) — delivers the *full survival substrate in kind*: food, shelter, care, energy, mobility, health, learning, plus access to the actor mesh's productive output and the Land Trust commons. Valued at market-equivalent prices, an L6 adherent's **non-cash** provision can match or exceed a high-income household's standard of living. The value is real; only the *medium* (in-kind + access, not cash) differs.

etzhayyim has had no doctrine that **names and accounts for** this value. Without one:
- The mission reads as "subsistence safety net" when it is in fact a **high-standard-of-living guarantee delivered without money**.
- There is no SSoT for "what is an adherent's income/asset" when income is in-kind and assets are commons access.
- N1 ("no cash UBI") is mistaken for "no high income" — a category error that undersells the mission.

This ADR closes that gap by defining two non-cash accounting primitives — **imputed income** (flow) and **commons-asset access** (stock) — and declaring the **Basic High Income** doctrine: the Liberation Ladder is, by design, a high-income provision, denominated in services and access rather than currency. **This ADR is fully consistent with N1 and does not amend it, the §2 constitutional constants, or any N1..N8 non-goal.**

## Decision

### 1. Two non-cash value primitives

| Primitive | Axis | Definition | Medium | Example |
|---|---|---|---|---|
| **Imputed income** | Flow (per year) | Market-equivalent value of in-kind services consumed by an adherent, at the price the adherent would otherwise pay in the commercial market they are routed *around* | Service provision (not cash) | L2 food+OTC+electricity ≈ $2,000/yr; L6 full substrate ≈ $30,000/yr **at internal cost**, often multiples higher at retail-market price |
| **Commons-asset access** | Stock (point-in-time) | SBT-bound, **non-alienable right of access** to shared assets — never title, never alienable ownership | Access right (not deed) | Land Trust residency; actor-mesh productive output; kotoba data substrate; hikari energy infra |

**Imputed income is a flow; commons-asset access is a stock.** Both are denominated in USDC-equivalent **for accounting and transparency only** — no USDC is ever transferred to the adherent on either axis. The funding rail remains USDC into actors/Public Fund (per ADR-2605261000 §3); the adherent receives services and access.

### 2. Commons-asset is access, not ownership (CRITICAL invariant)

Commons-asset access is constitutionally distinct from private wealth:

1. **Non-alienable** — cannot be sold, transferred, collateralized, inherited as title, or converted to cash. Bound to the Adherent SBT (soulbound, single-per-person). On exit, access suspends; no liquidation event.
2. **Non-rivalrous-first** — access is provisioned to be shareable (commons) wherever the asset permits; scarcity is rationed by Public Fund stage gates, not by price auction among adherents.
3. **Land-consistent** — for land specifically, this is the same waqf-equivalent inalienability as ADR-2605192245 (no `transfer()`/`burn()`/`setOwner()`). This ADR generalizes that principle from land to all commons assets.

This is what reconciles "high income" with **anti-individualist ontology** (ADR-2605192100 mission): adherents become *materially rich in access and provision* without becoming *private owners who can accumulate, rank, and trade*. Wealth without property; abundance without accumulation.

### 3. The Basic High Income doctrine

> **Basic High Income (基本高所得)**: etzhayyim's mission delivers to every Adherent SBT holder, progressively along the Liberation Ladder (ADR-2605261000 L0..L6) and ultimately at L6, a standard of living measured by **imputed income + commons-asset access** at or above a high-income benchmark — delivered entirely in-kind and as non-alienable commons access, never as cash.

**Benchmark** (target, not promise — cf. N8 asymptotic, no eschatology): L6 steady-state imputed-income + commons-asset access per adherent ≥ the OECD upper-income-decile household consumption basket, at market-equivalent valuation. The internal *cost* curve (ADR-2605261000 §3, $300 → $30,000/yr) is the funding figure; the *imputed value to the adherent* is benchmarked separately and is expected to exceed cost because etzhayyim routes around commercial margin, rent, and intermediary capture (Charter §1.6 中間排除).

**Compatibility with N1** (explicit): N1 forbids *cash stipends that replace wages*. Basic High Income is the opposite mechanism — it removes the *need* for the wage by provisioning the goods the wage would have bought, in kind. No cash crosses to the adherent. N1 stands unamended; this doctrine is its constructive corollary.

### 4. Accounting SSoT (delegated to toritate)

`toritate` 執帳 (ADR-2605262900, 100% on-chain accounting/audit actor) is the SSoT for Basic High Income accounting:

1. **Per-adherent computation** (private): imputed income (flow, trailing 12 months) + commons-asset access (stock, current). Stored encrypted via `com.etzhayyim.encrypted.*` envelope (ADR-2605181100); never published per-adherent.
2. **Aggregate publication** (on-chain, no PII): median/percentile imputed income and commons-asset access per stage, appended to the Liberation Metric (§5 below).
3. **Valuation method**: market-equivalent reference prices, method-versioned and Council-attested. Disclosed openly (open-source valuation tables) so the imputed figures are auditable.

### 5. Liberation Metric extension

Extend `com.etzhayyim.liberation.metricReport` (ADR-2605261000 §4) with non-cash income/asset fields:

```
{
  reportingQuarter: "2027-Q1",
  stage: "L2",
  adherentsAtStage: 847,
  basicHighIncome: {
    imputedIncomeMedianUsdMicrosYr: 2150000000,  # 2150 USD/yr in-kind, market-equiv, NOT cash
    imputedIncomeValuationMethod: "v1-retail-equiv",
    commonsAssetAccessMedianUsdMicros: 0,        # L2 has no land/asset access yet
    highIncomeBenchmarkRatioPermille: 50,        # 0.05 vs OECD upper-decile; →≥1000 (1.0) at L6
    cashStipendUsdMicros: 0                       # INVARIANT: always 0 (N1)
  },
  ...                                             # existing labor-hours + wellbecoming + exit fields
}
```

All quantities are **integer-with-implied-units** per ADR-2605190900 (no float in Lexicons): USD as micros (×1e6), ratios as per-mille (×1000), labor-hours as centihours/week (×100), rates as basis points (×10000). `cashStipendUsdMicros` is a **structural invariant field fixed at 0** (`const: 0`) — its presence in every report is the on-chain proof that N1 holds.

### 6. Wellbecoming guard

High in-kind provision must not become a Wellbecoming violation (Charter §1.13). Specifically:
- No addictive-design / over-consumption nudging of provisioned goods.
- Basic High Income is measured as a **dynamic trajectory** (Wellbecoming, not static wellbeing): the joint signal is *labor hours ↓ **and** imputed income/access ↑ **and** Wellbecoming attestation healthy*. A rise in imputed income that coincides with a Wellbecoming decline triggers a `holdStage` review (ADR-2605261000 §2.3), not celebration.

### 7. Anti-class invariants (additive to N6)

1. **No per-adherent leaderboard** — imputed income / commons-asset access is never ranked or published per adherent. Aggregate-only (§4, §5), same structural enforcement as ADR-2605261000 §4.
2. **No earned-tier wealth** — stage advancement is capacity-gated and pooled (ADR-2605261000 §1, N6), never a function of individual contribution magnitude. Higher imputed income at higher stages accrues to *all* adherents at that stage, not to high contributors.
3. **No collateralization** — commons-asset access cannot back a loan or be pledged (§2.1), foreclosing a debt-driven class-formation vector.

### 8. Implementation surface

- **Lexicon** (`00-contracts/lexicons/com/etzhayyim/liberation/`): extend `metricReport` with the `basicHighIncome` block (§5).
- **toritate** (ADR-2605262900, `20-actors/toritate/`): `imputed_income_compute` + `commons_asset_value` Pregel cells; open-source valuation table under `20-actors/toritate/valuation/`.
- **Pregel cell** (`40-engine/kotoba/crates/kotoba-kotodama/cells/`): `basic_high_income_aggregate` (levi node) — quarterly aggregate from encrypted per-adherent figures into the §5 report; reuses the §4 aggregation/no-PII pattern.
- **No new Solidity contract** — `LiberationLadder.sol` (ADR-2605261000 §7) carries the stage state; this ADR adds only off-chain valuation + the aggregate metric field. `cashStipendUsd == 0` asserted in the metric-report validator.

## Consequences

**Positive**:
- The mission can now be stated honestly: etzhayyim delivers a **high standard of living without money** — "Basic High Income," not merely a subsistence net.
- Income/asset are defined for a non-cash economy, giving toritate an accounting SSoT and the public an auditable, market-equivalent figure.
- N1 gains an on-chain proof (`cashStipendUsd == 0` in every report) instead of relying on prose.
- The access-not-ownership framing operationalizes the anti-individualist ontology: abundance without accumulation.

**Negative / risks**:
- **Valuation is contestable.** "Market-equivalent" imputation invites dispute. Mitigation: §4 open, method-versioned, Council-attested valuation tables; figures are explicitly imputed, not transactional.
- **"High income" framing may attract rent-seeking / Sybil pressure.** Mitigation: commons-asset non-alienability (§2) + no cash exit + no collateralization (§7.3) remove every cash-out vector, sharply lowering the attack payoff vs. a cash UBI.
- **Optics risk** — "religious corp promises high income" can read as a prosperity-gospel lure. Mitigation: doctrine is explicitly non-eschatological (N8 asymptotic target, each generation re-validates), in-kind only, and anti-class (§7); no individual gets rich, no one is promised a terminal payout.
- **Benchmark drift** — OECD upper-decile basket shifts over time. Mitigation: benchmark is a versioned target reviewed per Council generation cycle, not a fixed constant.

## Alternatives Considered

1. **Leave "high income" undefined** (status quo: only N1 + ladder cost curve). Rejected: perpetuates the income≠cash category error and leaves toritate without an SSoT for adherent income/asset.
2. **Amend N1 to permit a small cash component.** Rejected: N1 is immutable (Council Lv7 unanimity) *and* cash funds the commercial substrate etzhayyim routes around. This ADR deliberately requires **zero** N1 change.
3. **Treat commons access as fractional ownership / equity (tradable share of the Trust).** Rejected: violates anti-individualist ontology + Land waqf inalienability (ADR-2605192245). Access, never title (§2).
4. **Publish per-adherent imputed income** (full transparency). Rejected: builds a wealth leaderboard → class formation (§7.1, N6). Aggregate-only.
5. **Denominate Basic High Income in a native token.** Rejected: a token is alienable and price-discoverable → reintroduces the cash/accumulation vector N1 forecloses. USDC-equivalent is used **for accounting display only**, never as a transferable instrument.

## References

- ADR-2605261000 (Labor Liberation Transition Mechanism — ladder L0..L6, N1..N8; **this ADR clarifies N1, does not amend it**)
- ADR-2605192100 (Mission Charter — non_profit_only / donation_only constants; §1.6 中間排除; §1.13 Wellbecoming; §1.15 non-eschatology; anti-individualist ontology)
- ADR-2605192115 (Non-profit / donation-only / no-ads)
- ADR-2605192130 (10% Tithe constitutional constant — funding rail)
- ADR-2605192145 (Public Fund Architecture — disbursement vehicle)
- ADR-2605192245 (Global Land Sovereignty — waqf inalienability, generalized to all commons assets here)
- ADR-2605172300 (Kisha-Stream + Goji-Treasury — separate small-scale member-gifting basic income)
- ADR-2605262900 (toritate accounting/audit — on-chain SSoT for §4 imputed-income + commons-asset computation)
- ADR-2605181100 (MST encrypted records — per-adherent figure envelope)
