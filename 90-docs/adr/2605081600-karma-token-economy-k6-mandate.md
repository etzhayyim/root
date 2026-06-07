---
id: adr-2605081600-karma-token-economy-k6-mandate
title: "Karma Hegemon — WBT Token Economy (Phase K6 Mandate)"
status: proposed
doc_type: adr
topic: karma-token-economy
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - WBT issuance / faucet policy
  - demurrage rate (year -5%)
  - wealth cap (median × 100)
  - externality pricing function
  - well-becoming labor attestation as issuance source
priority: 8.5
axis: economy
weight: 0.8
priority_note: "K6 mandate — MUST ship before K5 mainnet else plutocratic drift (threat A5)."
depends_on:
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605081400-karma-self-growing-organism-ecosystem
  - adr-2605081500-karma-threat-model-and-counter-design
  - adr-2604291800-well-becoming-spirit-objective-function
related:
  - adr-2604291800-well-becoming-formal-model
supersedes: []
superseded_by: []
---

# Context

The K0-K3 release ships WBT settlement infrastructure
(`vertex_karma_wbt_balance` / `vertex_karma_wbt_transfer` /
`vertex_karma_commons_pool`) but with **zero-balance default** —
no organism receives WBT, demurrage is not applied, no wealth cap
is enforced. This is intentional for K0-K3 because shipping any
one of {issuance, demurrage, cap, externality tax} without the
others creates a plutocratic-drift attack vector (threat model
ADR-2605081500 A5).

This ADR records the **Phase K6 token economy** design that MUST
ship as one atomic release before any mainnet launch (K5).

# Decision

## A. WBT issuance via well-becoming labor attestation

Issuance is **NOT** time-based or stake-based. Instead, WBT enters
circulation when an organism produces a **well-becoming-positive**
edge that is witnessed:

```
issuance_amount(edge) =
  base_rate(axis, tier)
  × witness_count_multiplier
  × well_becoming_floor_pass
```

Where:

- `base_rate(axis, tier)` is the per-axis × per-tier baseline (Phase
  K6 calibration ADR pending).
- `witness_count_multiplier` = 1 + 0.1 × min(witnesses, 5) — bonus
  for community attestation, capped at 5.
- `well_becoming_floor_pass` ∈ {0, 1} — 1 only if the action does
  NOT cause a `child/future floor` violation per ADR-2604291800.

Non-issuance for harm: harm-direction edges produce no WBT.
Forfeit-on-rebirth: organisms entering `karma.rebirth` flow forfeit
balance to commons pool (already wired in K0-K3).

## B. Demurrage (year -5%)

`karma.wbt.demurrageSweep` BPMN (R/PT24H cron) reduces every active
balance by `1 - (1 - 0.05)^(days_since_last_tx / 365)`. Decayed
amount transferred to commons pool. The decay function is
**continuous** (not stepped), so balances don't age in cliffs.

Practical effect: organisms must spend / transfer WBT or it
literally rots. Hoarding penalty matches Gesell + Doughnut economics
(money-as-medium not money-as-store).

## C. Wealth cap (median × 100)

`karma.wbt.wealthCapSweep` BPMN (R/PT24H cron) computes the median
balance across active organisms; any balance > median × 100 has
the excess transferred to commons pool.

The cap is **soft** in implementation (sweep removes excess) but
**hard** in effect: no organism can stably hold more than 100x
the median. As the population grows the median rises, raising the
cap proportionally.

## D. Externality pricing function

Each `recordDependency` call is taxed in WBT proportional to its
externality. Tax flows to commons pool.

```
externality_tax(edge) =
  carbon_tax(magnitude, axis)
  + child_welfare_tax(victim_vul)
  + spirit_separation_tax(direction, axis)
  + future_horizon_tax(future_horizon_years, irreversible)
```

Tax is paid by the edge **author** at recordDependency time. If
the author has insufficient balance, the edge is rejected — this
is the WBT-mediated form of "you can't afford this karmic action".

The exact pricing function is K6 calibration work; placeholder
values:

| Component | Multiplier |
|---|---|
| Carbon (Venturum + irreversible) | 0.05 WBT per magnitude × horizon-year |
| Child welfare (vul ≥ 2.0) | 0.10 WBT per magnitude |
| Spirit separation (Vinculum + harm) | 0.20 WBT per magnitude |
| Future horizon (irreversible + horizon > 30y) | 0.15 WBT per magnitude × horizon-year |

## E. Commons pool distribution

Commons pool grows via:
1. Demurrage decay
2. Wealth cap sweep
3. Externality tax
4. Forfeit on rebirth

It distributes via:
1. **UBI (Universal Basic Income)**: each active organism
   receives a daily dividend equal to `pool / (active_organism_count
   × 365)`. Phase K7 mandate (not K6 — distribution policy is more
   politically loaded than collection policy).
2. **Cohort genesis grant**: when a new cohort emerges via
   `karma.organism.harvest`, it receives a one-time WBT grant from
   the pool to seed initial member balances. Sized at 50 × median.
3. **Future generation trust**: 30% of commons pool reserves
   (Iroquois 7-generation thinking) earmarked for future organisms
   not yet emerged. Inaccessible to current organisms.

# Consequences

## Positive

- Demurrage + wealth cap + externality tax = **structural
  anti-plutocracy** at protocol layer. No governance vote needed
  to enforce — pure code.
- Issuance tied to well-becoming-positive edges + witness count
  binds the token economy to the well-being objective function
  (ADR-2604291800), not to speculation.
- Forfeit-on-rebirth integrates with K0-K3 rebirth flow — one of
  the four irreversible costs is already in production.
- Commons pool as automatic redistribution mechanism: redistribution
  is not "legislated", it's the emergent consequence of demurrage +
  cap + tax.

## Negative

- The K6 release is **atomic** — issuance + demurrage + cap +
  externality must all ship together. Any subset deployed alone
  creates an attack vector.
- Calibration of base_rate, externality multipliers, demurrage
  rate, and cap multiplier requires economic modeling work
  (separate calibration ADR pending).
- Externality tax may price out small organisms from making any
  edges if multipliers are too aggressive — needs A/B testing
  in pilot cohort before mainnet.

## Reversibility

K6 ships are **not easily reversible**. Once organisms hold balances,
changing demurrage rate (say from -5% to -10%) creates wealth-effect
rebellion. Calibration ADR will pin numerical values via a
governance-amend-required process. Day-to-day operator changes are
forbidden.

# Alternatives Considered

## Alt 1: Stake-based issuance (rejected)

Issuance proportional to current balance ("interest") creates
positive feedback that violates A5 plutocratic drift counter.
Rejected.

## Alt 2: Time-based issuance (UBI from genesis) (rejected)

UBI from organism creation creates Sybil-attack incentive (each
fake organism is a free WBT printer). Rejected; UBI moves to
distribution side via commons pool.

## Alt 3: No demurrage (rejected)

Without decay, hoarded balances are passive forever. Plutocracy
inevitable. Rejected.

## Alt 4: Hard wealth cap (transfers blocked above cap) (rejected)

Hard cap creates UX problem (legitimate transfers blocked) and
requires per-tx checks. Soft cap (sweep removes excess) is
operationally simpler and economically equivalent.

## Alt 5: Externality tax based on actual carbon/social-cost data (deferred)

Real-time externality data (e.g. EU ETS carbon price,
state-of-society indices) is too volatile + politically charged
for protocol-layer integration. K6 uses a curated multiplier
table; K7 may add data-feed updates via DAO vote.

# References

- ADR-2605081300 — constitutional layer (parent)
- ADR-2605081400 — ecosystem layer (parent)
- ADR-2605081500 — threat model (gates this ADR — A5 demurrage
  is part of THIS ADR's mandate)
- ADR-2604291800 — well-becoming objective function (issuance
  source-of-truth for "well-becoming-positive")
- `30-graph/graph-schema/migrations/20260508165000_vertex_karma_wbt.ts` —
  the K1 ledger backing this economy
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/karma_wbt.py` —
  K1 transfer / forfeitToCommons primitives that K6 builds on
