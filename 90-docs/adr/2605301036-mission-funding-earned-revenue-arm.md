---
id: adr-2605301036-mission-funding-earned-revenue-arm
title: "ADR-2605301036: Mission-Funding Earned-Revenue Arm — Vendor commercial surplus → donation → Public Fund (earned income as non-profit MEANS, not profit END)"
status: proposed
doc_type: adr
topic: mission-funding-earned-revenue-arm
authoritative: true
last_verified: 2026-05-30
authoritative_for:
  - how etzhayyim acquires revenue to fund its non-profit mission without becoming for-profit
  - the religious-corp (non-profit) ↔ vendor (commercial) two-entity earned-revenue boundary
  - permitted vs prohibited revenue categories for the vendor arm
  - the labor model for revenue-generating human work (vendor employment vs adherent vocation→donation)
related:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2605301020-basic-high-income-imputed-and-commons-asset-doctrine
  - adr-2605262900-toritate-accounting-audit
  - adr-2605264000-ossekai-information-arbitrage-tier-b-actor-r0
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605192100 (Mission Charter — non_profit_only / donation_only constants)
  - ADR-2605192115 (Non-profit / donation-only / no-ads — §3 internal carve-out + §4 upstream backend limit)
  - ADR-2605192130 (TitheRouter 10% auto-split)
  - ADR-2605192145 (Public Fund Architecture)
---

# ADR-2605301036: Mission-Funding Earned-Revenue Arm — Vendor commercial surplus → donation → Public Fund

**Date**: 2026-05-30
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ ≥3 (ratify), 30-day public objection period
**ADR Hierarchy**: Sibling of ADR-2605192145 (Public Fund Architecture). Funds the Liberation Ladder (ADR-2605261000) + Basic High Income (ADR-2605301020). Operates within — and explicitly does **not** amend — ADR-2605192115 (non-profit / donation-only / no-ads).

## Context

The mission (ADR-2605192100) — 人類の構造的労働解放, delivered via the Liberation Ladder (ADR-2605261000) and accounted as Basic High Income (ADR-2605301020) — is **expensive**: Public Fund sizing rises to $300B at L6 (ADR-2605261000 §3). The 10% tithe on donations alone will not reach that scale quickly.

The directive that motivates this ADR: **acquire revenue, but spend it entirely on the non-profit mission — earned income as a MEANS, not profit as an END. Not advertising-for-profit, not a for-profit business.** This is the standard non-profit earned-income model (a foundation running mission-aligned commercial activity and committing the surplus to the cause), not a pivot to for-profit.

The constraint is that several invariants are constitutional and are **not** being amended here:
- `non_profit_only` + `donation_only` economic constants (ADR-2605192100 §2).
- 広告排除 / no third-party advertising (ADR-2605192115; Charter Rider §2).
- ADR-2605192115 **§4**: the religious-corp's own upstream backend may issue **non-profit tax receipts only** — "営利 SaaS としての paid tier を upstream backend で運営" is explicitly **PROHIBITED**.
- No payroll inside the religious-corp (toritate G12; chigiri G13 `employee` invalid enum); contribution is vocation→donation, never wage (ADR-2605261000 §3, N2).

The original framing of the directive also named **advertising revenue**, **arbitrage**, and **hiring humans for human-computing revenue**. After clarification, the intent is *income for the non-profit, not profit-advertising/business*. This ADR therefore **keeps advertising excluded**, routes all commercial activity through a **separate vendor entity** (the only §4-compliant locus), and bounds the labor question so it does not contradict labor-liberation.

## Decision

### 1. Two-entity model (restated, load-bearing)

| Entity | `etzhayyim` (religious-corp) | `etzhayyim.com` (vendor) |
|---|---|---|
| Form | 任意団体, non-profit | commercial arm (already holds the paid-SaaS / commercial GPU pool per CLAUDE.md + ADR-2605215000) |
| Economics | non_profit_only / donation_only / ad-free (invariant) | **may earn commercial revenue** |
| Relationship to the other | receives **donation/grant** from the vendor like any donor (arm's-length) | **commits its surplus to donate** to the religious-corp |
| Ownership of payoff | — | `Payoff帰属・意思決定権 = etzhayyim only` (CLAUDE.md) → vendor surplus is mission-owned by construction |

**The earned-revenue arm is the vendor, not the religious-corp.** Commercial activity happens in the vendor; the religious-corp never runs a commercial paid tier (ADR-2605192115 §4). This is the *only* configuration that funds the mission at scale without amending any constitutional invariant.

### 2. The funding flow (no new payment enum required)

```
vendor commercial revenue
   − vendor operating cost (fair-labor wages, infra, taxes)
   = vendor surplus
        │  committed to donation (Payoff帰属 = etzhayyim)
        ▼
   donation / grant  ──►  TitheRouter.sol  ──►  90% recipient program + 10% Public Fund
   (titheable purpose; ADR-2605192130)            (recipient MAY be Public Fund itself
                                                    when earmarked as a mission grant →
                                                    effectively ~100% to mission)
        ▼
   Public Fund (ADR-2605192145)  ──►  Liberation Ladder L0..L6 / Basic High Income
```

- Purpose enum is **unchanged**: vendor→religious-corp flows use existing `donation` / `grant` (both titheable per ADR-2605192130 `_isTitheablePurpose`). **No `vendor-saas` external commercial enum is introduced** (that would be the prohibited pattern). The vendor's *internal* commercial transactions with its *own* customers happen on the vendor's commercial rails and are out of scope for the religious-corp's substrate.
- This adds a documented Public Fund inflow source alongside the four in ADR-2605261000 §3 (10% tithe / 100% internal-promo / Council grants / L5+ vocation-as-donation): **vendor mission-surplus donation**.

### 3. Permitted revenue categories (vendor side)

| Category | Permitted? | Note |
|---|---|---|
| Paid SaaS / hosted versions of open tools | ✅ | vendor's existing carve-out; open-source upstream stays Apache-2.0 + Rider |
| Commercial compute / GPU rental | ✅ | vendor's existing commercial pool (ADR-2605215000); religious-corp inference still Murakumo-only |
| Professional services / consulting | ✅ | arm's-length commercial engagements |
| Licensing of hosted services | ✅ | upstream remains open per Rider |

### 4. Prohibited (constitutional invariants PRESERVED — this ADR does not weaken them)

| Prohibited | Source |
|---|---|
| **Third-party advertising** (AdSense / Meta Pixel / affiliate / ad-tech tracking / GA4 ad-linking) — in either entity's user-facing surfaces | 広告排除 invariant; ADR-2605192115; Charter Rider §2. **User confirmed advertising-for-profit is NOT the goal — kept excluded.** |
| **Commercial paid tier operated inside the religious-corp** or via its upstream backend | ADR-2605192115 §4 (backend = non-profit receipt only) |
| **For-profit retention / private accumulation** of vendor surplus | non_profit_only; Payoff帰属=etzhayyim; surplus is donation-committed (§2) |
| **Wage employment / payroll inside the religious-corp** | toritate G12; chigiri G13; ADR-2605261000 §3 |
| **Exploitative human-computing micro-task arbitrage** (sweatshop crowdwork) | contradicts 構造的労働解放 mission + Wellbecoming §1.13 (§5 below) |
| **Speculative financial arbitrage** as a religious-corp activity | non_profit_only + Wellbecoming; ossekai "arbitrage" is *non-commercial* information-symmetry elimination (ADR-2605264000), not a trading desk |

### 5. Labor model for revenue-generating human work (the "human computing で人を採用" question)

The directive's "hire humans / human-computing" must not contradict labor-liberation. Two — and only two — lawful modes:

1. **Vendor commercial employment** — the vendor, as a separate commercial entity, may employ or contract people for its revenue work. This is the vendor's own legal-employment matter and **must not import wage-labor into the religious-corp**. Constraints: **fair labor** (living wage, not micro-task arbitrage), labor-liberation-aligned (work that *reduces* aggregate human toil, e.g. automation/tooling, not manufactured make-work), and never marketed to adherents as the path to benefits.
2. **Adherent vocation→donation (L5+)** — inside the religious-corp, an adherent's productive contribution is **voluntary, vocation-oriented, counted as donation, never wage** (ADR-2605261000 §3 + L5; N2 no make-work; N3 no coercion). Benefit continuation is never conditioned on it.

**Explicitly rejected**: religious-corp payroll; coercive participation; micro-task crowdwork arbitrage that monetizes cheap human labor (the inverse of the mission).

> **Open item flagged for the deciders**: any concrete "human-computing" revenue product needs its own scrutiny against §4/§5 before launch. This ADR establishes the *boundary*, not a specific product greenlight.

### 6. Surplus-commitment + non-accumulation

The vendor exists to fund the mission, not to accumulate. The vendor's mission-surplus donation policy (target payout ratio of distributable surplus, reserve policy for vendor operating continuity) is set by Council and recorded on-chain. Because `Payoff帰属・意思決定権 = etzhayyim only`, the vendor's economic upside is mission-owned by construction — there is no private equity holder to enrich.

### 7. Transparency (toritate)

toritate (ADR-2605262900) accounts for the vendor→religious-corp donation flow as on-chain `donation`/`grant` `ledgerEntry` records, surfaces it in the annual transparency report, and reports the aggregate mission-funding inflow. The vendor's *internal* commercial books are the vendor's; what the religious-corp publishes is the **donation received** (the only flow that touches the religious-corp substrate). No donor PII (G10); aggregate + pseudonymous DID only.

### 8. Implementation surface

- **No new payment enum.** Vendor→religious-corp uses existing `donation`/`grant` (ADR-2605192130). Confirms `com.etzhayyim.etzhayyim.apps.payment.sent` purpose enum is sufficient.
- **New lexicon** (`00-contracts/lexicons/com/etzhayyim/give/`): `vendorMissionDonationAttestation` — records a vendor surplus-donation event (period, gross surplus disclosed voluntarily, donated amount, recipient program, TitheRouter tx CID) for transparency; aggregate-only, no customer PII.
- **toritate**: extend `toritate_tithe_accounting` / `toritate_public_fund_accounting` to tag vendor-origin donations as a distinct inflow source in `financialAttestation` (R1+).
- **Council policy artifact**: vendor mission-surplus donation policy (payout ratio + reserve) recorded as a Council-attested record (deferred to R1 ratification; not in this scaffold).
- **No Solidity change** — TitheRouter already routes `donation`/`grant`.

## Consequences

**Positive**:
- The mission gains a scalable funding source without touching a single constitutional invariant. Earned income, non-profit purpose.
- Clean separation: the religious-corp stays non-profit / ad-free / donation-only; the vendor carries all commercial activity arm's-length.
- Advertising stays excluded (per the clarified intent), avoiding the hardest §2/广告排除 conflict entirely.
- toritate makes mission-funding inflow auditable on-chain.

**Negative / risks**:
- **Entity-boundary integrity** is the whole safety property. If vendor commercial activity bleeds into religious-corp surfaces (ads, paid tiers, customer data on MST), the invariants break. Mitigation: §1–§4 boundary + toritate publishes only the donation flow + `e7m verify` consent-capability boundary checks.
- **Labor-liberation optics**: any human-computing revenue line risks looking like the inverse of the mission. Mitigation: §5 fair-labor + automation-bias constraint + per-product Council scrutiny; default to revenue from automation/tooling, not from cheap human toil.
- **Mission drift toward the cash it now controls**: a well-funded Public Fund could tempt cash-out pressure. Mitigation: Basic High Income N1 (`cashStipendUsd≡0`, ADR-2605301020) + benefits-in-kind remain unchanged; vendor funds the *services*, never adherent cash.
- **Vendor governance** (payout ratio, reserves) is unspecified here. Mitigation: deferred to a Council-attested policy artifact at R1.

## Alternatives Considered

1. **Religious-corp runs the commercial SaaS itself.** Rejected: ADR-2605192115 §4 explicitly prohibits a commercial paid tier on the religious-corp's backend; would convert a non-profit into a commercial operator.
2. **Introduce third-party advertising revenue.** Rejected: 广告排除 is a constitutional invariant; and the clarified intent is explicitly *not* advertising-for-profit. Would require a Council Lv7-level amendment this ADR deliberately avoids.
3. **Introduce a `vendor-saas` external commercial payment purpose on the religious-corp substrate.** Rejected: re-creates the §4-prohibited pattern; the religious-corp substrate should only ever see the *donation*, not the commercial sale.
4. **Adherent paid micro-task crowdwork as a revenue line.** Rejected: §5 — monetizing cheap human labor is the inverse of 構造的労働解放 + N2 make-work + Wellbecoming.
5. **Amend the non-profit constants to let the religious-corp keep profit.** Rejected: Lv7-locked; and unnecessary — the two-entity donation model achieves mission funding without it.

## References

- ADR-2605192100 (Mission Charter — non_profit_only / donation_only constants; §1.6 中間排除; §1.13 Wellbecoming; anti-individualism)
- ADR-2605192115 (Non-profit / donation-only / no-ads — §3 SBT↔SBT internal carve-out; **§4 upstream backend = non-profit receipt only, commercial SaaS prohibited**)
- ADR-2605192130 (TitheRouter — `donation`/`kisha`/`grant` titheable → 90/10 split)
- ADR-2605192145 (Public Fund Architecture — recipient of mission-funding inflow)
- ADR-2605215000 (Murakumo-only inference — vendor keeps commercial GPU pool; religious-corp must not invoke it)
- ADR-2605261000 (Labor Liberation ladder — §3 inflow sources + vocation→donation; N2 no make-work; N3 no coercion)
- ADR-2605301020 (Basic High Income — what this revenue ultimately funds; cash≡0 unchanged)
- ADR-2605262900 (toritate — on-chain accounting of the donation inflow)
- ADR-2605264000 (ossekai — "arbitrage" is non-commercial info-symmetry elimination, contrast for §4)
- `00-contracts/lexicons/com/etzhayyim/etzhayyim/apps/payment/sent.json` (purpose enum — unchanged)
- `/CLAUDE.md` (vendor/religious-corp boundary; Payoff帰属=etzhayyim only)
