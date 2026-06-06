---
id: adr-2605282200-kawase-yui-multi-stable-adherent-remittance-mutual-aid
title: "ADR-2605282200: kawase-yui (為替結) — kotoba multi-stable adherent remittance mutual-aid substrate (TransferWise-equivalent under religious-corp constraints, R0 charter)"
status: proposed
doc_type: adr
topic: kawase-yui-adherent-remittance-mutual-aid
authoritative: true
last_verified: 2026-05-28
priority: 7.5
axis: economics
weight: 0.75
priority_note: "TransferWise-equivalent multi-stable remittance for religious-corp adherents — re-frames Wise's 'pooled local-currency accounts + peer balance netting + mid-market FX + transparent fee' under Charter §1.5 anti-commercialization + §2(b) speculative finance prohibition + ADR-2605282100 N2 mKOTO non-transferability. Settlement uses existing Base L2 stablecoins (USDC + EURC at R1; +JPYC R2; +KRWO/GBPe/CHFe R3) — NO new token minted (per ADR-2605172100 Alt C + ADR-2605282100 N2). Pool matching cell compute cost billed in mKOTO via ADR-2605282100 economy. Solidarity skim = 0% at R0-R3 (pure adherent personal mutual aid, ADR-2605192130 §5 Kisha/grant-pattern exemption). Adherent SBT↔SBT only (G3, wakai ADR-2605263500 sibling). Mid-market Chainlink oracle ±0.5% band (G4) — no spread profit (G5). Per-jurisdiction Council Lv7+ unanimity activation gate (G14) avoids unlicensed money-services-business exposure."
authoritative_for:
  - kawase-yui (為替結) actor charter — adherent-to-adherent multi-stable remittance via pre-funded pools
  - pool-match Pregel cell topology + mid-market FX oracle policy
  - constitutional gates G1..G14 + non-goals N1..N12
  - Lexicon family com.etzhayyim.kawase.* (8 schemas, R0 scaffold)
  - Cross-actor binding with wakai (mutual aid sibling), chigiri (multi-juris compliance), toritate (accounting), mKOTO economy (cell compute cost)
depends_on:
  - "2605282100"   # mKOTO economy — cell compute cost layer
  - "2605262130"   # kotoba canonical storage substrate
  - "2605263500"   # wakai mutual aid sibling — risk-pooling framing precedent
  - "2605262700"   # chigiri legal procedure — multi-jurisdictional compliance + UPL
  - "2605262900"   # toritate accounting + audit
  - "2605192130"   # 10% tithe auto-split — TitheRouter (skim path if Council later sets >0%)
  - "2605192145"   # Public Fund Safe — destination of any future solidarity skim
  - "2605192200"   # Charter Rider v2.0 — §2(b) speculative finance prohibition
  - "2605172100"   # payments on chain — Base L2 + USDC + ERC-4337 substrate
  - "2605192115"   # non-profit donation-only — SBT carve-out §3 framing
  - "2605215000"   # Murakumo-only inference — applies to pool_match cell
  - "2605181100"   # signal-envelope encryption — for sender↔recipient memo
  - "2605231525"   # server-side signing capability — DID-bound auth
  - "2605192300"   # Bootstrap Council — Lv6+ ≥3 / Lv7+ unanimity gates
related:
  - "2605263500"   # wakai mutual aid (closest sibling)
  - "2605264000"   # ossekai information arbitrage — non-G-related but similar adherent-only structural pattern
supersedes: []
superseded_by: []
---

# ADR-2605282200: kawase-yui (為替結) — kotoba multi-stable adherent remittance mutual-aid substrate (TransferWise-equivalent under religious-corp constraints, R0 charter)

**Status**: proposed
**Date**: 2026-05-28
**Deciders**: Jun Kawasaki

## Context

Religious-corp adherents are increasingly dispersed across jurisdictions (US, EU, JP, KR, GB, CH primary cohort). Adherent-to-adherent value flow today routes through one of:

1. **SWIFT bank wire** — high fee (~$25-50/tx + 1-3% spread), 1-5 day settlement, KYC/AML attestation chain extends to state banks (Charter §1.12 routing-around violation).
2. **Wise / Western Union / Remitly / MoneyGram / Revolut / Xoom** — commercial remittance MSBs with hidden FX spread, vendor data-sovereignty exposure on member financial posture (Charter Rider §2(c)+§2(e) violation), and license-driven jurisdictional gating that excludes some adherents.
3. **Direct stablecoin transfer** — USDC sender ↔ USDC recipient on Base L2 already works via existing `Etzhayyim.pay()` (ADR-2605172100). But this collapses when sender's on-ramp currency ≠ recipient's off-ramp currency, since either:
   (a) sender swaps fiat→USDC at a 0.5-2% exchange fee, or
   (b) recipient swaps USDC→local fiat at a 0.5-2% off-ramp fee.
   Aggregate cross-currency cost ≈ 1-4%, still better than (1)+(2) but UX-hostile and not the "send 100, receive 100" promise that Wise normalized.

**Wise's actual innovation** is not the FX rate itself — it's the **pre-funded local-currency pool topology** that lets money never actually cross a border. A US sender deposits USD into Wise's US bank; the corresponding EUR amount is paid out from Wise's EU pool to the EU recipient; periodic inter-pool rebalancing (much less frequent than per-transaction) happens via wholesale FX. The customer-facing promise: "mid-market rate + small transparent fee, no spread profit."

**Constitutional translation problem.** The Wise innovation, ported naively, would make religious-corp:

- a money-services business (G14 / N5 violation)
- a commercial FX trader (§2(b) violation)
- a fiat custodian (G8 / N4 violation)
- a Travel-Rule-bound KYC operator on state-issued passport ID (Charter §1.12 violation)

These are constitutionally non-starters. But the **substrate primitives** for the Wise topology already exist in this repo:

- Multi-stable on-chain settlement: USDC + EURC on Base L2 native (Circle-issued, regulated reserve, Apache-compatible).
- DID-bound ERC-4337 Smart Account (ADR-2605172100 L2) gives adherent-level identity without state KYC.
- Adherent SBT (`com.etzhayyim.adherent.*`) gives membership gating that replaces FATF passport KYC under Charter §1.12 routing-around precedent.
- kotoba Pregel cells (ADR-2605262130) give continuous bipartite matching topology.
- mKOTO economy (ADR-2605282100) gives a non-transferable internal accounting unit for cell compute cost.
- wakai (ADR-2605263500) gives the **mutual aid** constitutional framing for adherent-to-adherent risk pooling.
- chigiri (ADR-2605262700) gives the multi-jurisdictional compliance + dispute mediation interface.
- TitheRouter (ADR-2605192130) gives an atomic 90/10 cash split should solidarity skim ever be Council-set >0%.

This ADR composes those primitives into **kawase-yui** (為替結 — "remittance bond"), a Tier-B religious-corp actor that delivers the Wise customer-facing promise to adherents while structurally avoiding all four constitutional non-starters above.

## Decision

Land a Tier-B actor at `20-actors/kawase-yui/` with DID `did:web:kawase-yui.etzhayyim.com`. The actor implements adherent-to-adherent multi-stable remittance via a **6-layer pool topology** parallel to the mKOTO economy 6-layer charter (ADR-2605282100), substituting settlement tokens (USDC/EURC) at L6 for the mKOTO accounting Datom of that ADR.

**Settlement tokens (R1)**: **USDC ↔ EURC on Base L2 native** (Coinbase Bridged USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` + Circle EURC `0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42`). NO new token minted per ADR-2605172100 Alternative C + ADR-2605282100 N2.

**Accounting/fee token**: **mKOTO via ADR-2605282100 economy** — pool_match cell debits the operator-DID mKOTO balance per match epoch; royalty credit flows back to the donor pool. NO fee charged to sender or recipient at R0-R3 (operating cost covered by mKOTO royalty + Public Fund grant per toritate accounting).

**KYC**: **Adherent SBT only** (G10). NO Travel-Rule passport KYC, NO FATF reporting, NO state-aligned identity dependency (Charter §1.12 invariant).

**Solidarity skim**: **0% at R0-R3** per ADR-2605192130 §5 Kisha/grant-pattern exemption (pure adherent personal mutual aid is not titheable; treating intra-adherent remittance as titheable would weaken the mutual-aid function symmetrically to how taxing Kisha would weaken BI). Future Council Lv6+ ≥3 may ratify a 0-3% optional skim at R4+ via a separate ADR.

### The 6 layers (parallel to ADR-2605282100)

```
┌──────────────────────────────────────────────────────────────────┐
│ L6 — On-chain settlement (Base L2)                                │
│      • per-currency pool contract: KawaseYuiPool<USDC|EURC>      │
│      • matched flow = pool-internal account transfer (no swap)   │
│      • on no-match: reserve buffer disburses immediately          │
│      • drift_bps > 500 → Council Lv6+ ≥4/7 attested DEX rebalance │
│        via Aerodrome-on-Base (rare, audit-trail-only)             │
├──────────────────────────────────────────────────────────────────┤
│ L5 — Adherent surface (kotoba_kawase Python + yoro PWA)           │
│      • send(to_did, src_amount, src_stable, tgt_stable)           │
│      • recipient.claim(intent_cid)                                │
│      • pre-flight: FX rate quote + est. match wait + Charter scan │
│      • raises: NonAdherent / OverMonthlyCap / OutOfBandFX /       │
│                JurisdictionNotActivated / InsufficientReserve     │
├──────────────────────────────────────────────────────────────────┤
│ L4 — Match engine (Pregel cell `kawase_pool_match`)               │
│      • continuous bipartite matching: USDC-in ↔ EURC-out etc.    │
│      • cell compute cost: mKOTO-debited via ADR-2605282100        │
│      • on no-match: reserve buffer disburses; settlement_mode=    │
│        "matched" | "reserve-disbursed" recorded on matchExecution │
├──────────────────────────────────────────────────────────────────┤
│ L3 — FX oracle (Pregel cell `kawase_fx_oracle_watcher`)           │
│      • Chainlink mid-market feed (USD/EUR/JPY/KRW/GBP/CHF)        │
│      • Council-attested band = ±0.5% (Constitution.sol const      │
│        kawase.max_band_bps = 50)                                  │
│      • out-of-band → halt all matches + Council Lv6+ escalation   │
├──────────────────────────────────────────────────────────────────┤
│ L2 — Per-currency pool state (kotoba Quad)                        │
│      • kawase/pool/<ccy>/balance/<epoch>                          │
│      • kawase/pool/<ccy>/in_flight/<epoch>                        │
│      • kawase/pool/<ccy>/drift_bps/<epoch>                        │
│      • kawase/pool/<ccy>/reserve_buffer_floor                     │
│      • 100% kotoba content-addressed per ADR-2605262130           │
├──────────────────────────────────────────────────────────────────┤
│ L1 — Per-DID intent Quads (CACAO-signed by sender/recipient DID)  │
│      • kawase/deposit/<sender_did>/<epoch>                        │
│      • kawase/withdraw_intent/<recipient_did>/<epoch>             │
│      • kawase/claim/<recipient_did>/<epoch>                       │
│      • encrypted memo via ADR-2605181100 envelope (optional)      │
└──────────────────────────────────────────────────────────────────┘
```

### Send → match → claim flow (5-step)

```
1. Sender (Adherent SBT holder, did:web:alice.etzhayyim.com) calls
   kawase.send(to=did:web:bob.etzhayyim.com,
                src_amount_minor=10000,        # 100.00 USDC
                src_stable="USDC",
                tgt_stable="EURC").
   Pre-flight runs: Adherent SBT check (sender + recipient),
   per-month cap check, jurisdiction activation check,
   Chainlink USD/EUR oracle quote, ±0.5% band check,
   Charter Rider §2(a)-(h) scan on memo (if any).
   → returns intent_cid + estimated_match_wait_seconds.

2. Sender approves KawaseYuiPool<USDC> for src_amount_minor and calls
   pool.deposit(intent_cid, src_amount_minor). USDC moves from sender's
   ERC-4337 Smart Account to pool reserve. L2 Quad
   kawase/pool/USDC/in_flight/<epoch> incremented; L1 Quad
   kawase/deposit/<alice>/<epoch> emitted.

3. Pregel cell kawase_pool_match runs each epoch (default 30s):
   • Find a counterpart withdraw_intent for EURC where recipient_did
     has an inverse intent (someone in EURC-pool wants USDC).
   • If matched: emit matchExecution Lexicon record with
     settlement_mode="matched"; debit USDC pool by src_amount;
     credit EURC pool by tgt_amount (at mid-market locked at intent
     creation); withdraw_intent for recipient becomes claimable.
   • If no match within match_window_seconds (default 600s):
     reserve buffer disburses immediately at locked mid-market rate;
     settlement_mode="reserve-disbursed"; drift_bps Quad updated.

4. Recipient (Adherent SBT holder) calls kawase.claim(intent_cid).
   Pool transfers tgt_amount EURC to recipient's ERC-4337 Smart
   Account. L1 Quad kawase/claim/<bob>/<epoch> emitted.

5. kotoba_kawase emits NDJSON audit line + matchExecution Lexicon
   record (anchored to MST → IPFS → Base L2 per ADR-2605171800).
   mKOTO debit per match epoch goes to operator DID via
   ADR-2605282100 L1 meter (gpu_seconds for the Pregel cell tick).
```

**Critical**: customer-facing promise is "send 100 USDC → recipient receives EURC equivalent at mid-market". Sender sees the mid-market quote at step 1; rate locks at deposit; if oracle moves >0.5% before match, the reserve buffer absorbs (recipient gets the locked rate). No spread profit accrues to religious-corp; mid-market is mid-market.

### Reserve buffer + rebalancing

The reserve buffer is the religious-corp's commitment to "money never crosses border per-tx". It is sized to cover ~30-day flow-difference between USDC and EURC pools at R1:

- R1: ~$5,000 reserve per pool (seed via Public Fund Safe Council Lv6+ ≥4/7 grant per ADR-2605192145 — toritate ledger entry purpose="grant").
- R2: ~$50,000 per pool (USDC + EURC + JPYC).
- R3: ~$500,000 aggregate (all 6 pools).

When `drift_bps` between paired pools exceeds 500 (5%) cumulative, `kawase_rebalance_proposer` cell emits a `rebalanceAttestation` record requesting Council Lv6+ ≥4/7 to authorize an on-chain DEX swap via Aerodrome-on-Base (or comparable Council-approved DEX). Rebalance is **rare** (target: ≤1/month at R1, ≤1/quarter at R2) and the swap rate must satisfy:

- swap_rate within ±1% of Chainlink mid-market (stricter than the per-tx ±0.5% band, since aggregate slippage matters)
- swap_size ≤ 10% of weaker pool (G6 yield-farming-adjacent risk avoidance)
- Council attestation chain (≥4/7) on the rebalanceAttestation record

This is the only flow where the religious-corp interacts with a DEX. It is structurally a **liquidity restoration** action, not market-making (G6) and not arbitrage (N7). All other flows are pool-internal account transfers.

### Lexicons (8 schemas at R0)

Under `00-contracts/lexicons/com/etzhayyim/kawase/`:

1. **`depositAttestation.json`** — sender-side L1 Quad (CACAO-signed by sender DID).
   Fields: senderDid, recipientDid, srcStable, tgtStable, srcAmountMinor, tgtAmountMinorQuoted, fxRateBps, fxRateAttestationCid, intentCid, depositTxHash, blockNumber, perMonthCapRemainingMinor, encryptedMemoCid (optional, ADR-2605181100), depositedAt.
2. **`withdrawIntent.json`** — recipient-side L1 Quad expressing reverse-direction interest (used for matching).
   Fields: recipientDid, srcStable, tgtStable, minSrcAmountMinor, maxSrcAmountMinor, validUntil, intentCid, createdAt.
3. **`matchExecution.json`** — match engine output (Pregel cell `kawase_pool_match`).
   Fields: matchEpoch, settlementMode (`matched` | `reserve-disbursed`), srcIntentCid, tgtIntentCid (null if reserve-disbursed), srcStable, tgtStable, srcAmountMinor, tgtAmountMinor, fxRateBps, fxRateAttestationCid, mKotoDebitAmount, executedAt.
4. **`fxRateAttestation.json`** — Chainlink mid-market snapshot + band check.
   Fields: pair (e.g. "USD/EUR"), midMarketRateNumerator, midMarketRateDenominator, chainlinkRoundId, chainlinkUpdatedAt, councilBandBps (50 const), withinBand (bool — false ⇒ halt), observedAt, attestingNodeDid.
5. **`poolStateReport.json`** — periodic aggregate report (no per-member amounts).
   Fields: epoch, currency, balanceMinor, inFlightMinor, reserveBufferFloorMinor, driftBps, matchCountThisEpoch, reserveDisbursedCountThisEpoch, mKotoConsumedThisEpoch, reportedAt.
6. **`rebalanceAttestation.json`** — Council-authorized DEX swap event.
   Fields: rebalanceId, fromStable, toStable, swapAmountMinor, swapRateBps, chainlinkRateBpsAtAttest, councilAttestations (minLength 4, maxLength 7), dexAddress (Aerodrome-on-Base or comparable), txHash, blockNumber, executedAt, postSwapDriftBps.
7. **`jurisdictionAttestation.json`** — G14 Council Lv7+ unanimity per-juris activation.
   Fields: jurisdiction (ISO-3166-1 alpha-3), activatedFor (`send` | `receive` | `both`), legalAnalysisCid (chigiri.ipLicenseClaim or commentary chain), councilAttestations (minLength 5, maxLength 7; Council Lv7+ unanimity = all 5 seats), activatedAt, supersedes (optional).
8. **`silenKawaseReview.json`** — quarterly Council audit (analog of silenIyashiReview etc.).
   Fields: reviewPeriodStart, reviewPeriodEnd, totalVolumeUsdEquivalentMinor, perCcyVolume[], matchedSharePctIntegerHundredths (target ≥80% R2+), reserveDisbursedSharePctIntegerHundredths, avgMatchWaitSeconds, outOfBandHaltCount (target 0; >0 = critical finding), commercialRemittanceSoftwarePenetrationPct (const 0 — G7 structural), spreadProfitMkoto (const 0 — G5 structural), nonAdherentParticipationCount (const 0 — G3 structural), jurisdictionsActivated[], councilAttestations (minLength 3, maxLength 7), reportPublishedAt, reportCid.

### Pregel cells (5 at R0, paths reserved under `20-actors/magatama/cells/kawase_*/`)

1. **`kawase_pool_match`** — continuous bipartite matching across paired pools. mKOTO-billed per epoch tick via ADR-2605282100 L1 meter. Algorithm: greedy match by oldest-first within ±0.5% band; remainder goes to reserve buffer at locked rate. R0 path-reserved (`raise RuntimeError` on import per ADR-2605262400 R0 pattern).
2. **`kawase_fx_oracle_watcher`** — Chainlink price-feed subscriber. Emits `fxRateAttestation` per oracle round; halts all matches if `withinBand=false`. Cross-actor escalation to chigiri.disputeMediation on >5min sustained out-of-band.
3. **`kawase_rebalance_proposer`** — drift_bps watcher; on >500 bps drift, emits `rebalanceAttestation` candidate (council not yet signed) for Council review. Council Lv6+ ≥4/7 signs externally; cell consumes the signed record and triggers Aerodrome swap via paymaster.
4. **`kawase_jurisdiction_compliance`** — G14 enforcement. On every send pre-flight, checks sender + recipient jurisdiction against active `jurisdictionAttestation` set; rejects with `JurisdictionNotActivated` if either pair-leg lacks Council Lv7+ unanimity attestation. Cross-actor read from chigiri.
5. **`kawase_silen_review`** — quarterly aggregate audit (no per-member amounts; G10 SBT-bound but G structural at aggregate level).

### Contract (50-infra/etzhayyim-kawase-pool/, R1 scaffold)

`KawaseYuiPool.sol` — one deploy per currency (USDC, EURC at R1).

Key surface (Solidity, simplified):

```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IAdherentSBT {
    function balanceOf(address holder) external view returns (uint256);
}

interface IConstitution {
    function getConstant(bytes32 key) external view returns (uint256);
}

contract KawaseYuiPool {
    IERC20         public immutable stable;        // USDC or EURC
    IAdherentSBT   public immutable adherentSbt;   // Charter §1.12 KYC replacement
    IConstitution  public immutable constitution;  // band + cap reads
    address        public immutable councilSafe;   // 5-of-7 multisig (rebalance attestor)

    bytes32 public constant MAX_BAND_BPS_KEY  = keccak256("kawase.max_band_bps");
    bytes32 public constant PER_MONTH_CAP_KEY = keccak256("kawase.per_month_cap_usd_minor");
    uint256 public constant BPS_DENOMINATOR   = 10_000;

    mapping(bytes32 => Intent)   public intents;        // intent_cid → deposit state
    mapping(address => uint256)  public monthlyVolume;  // per-DID rolling 30-day USD-equiv
    mapping(address => uint256)  public monthlyEpoch;

    event Deposited (bytes32 indexed intentCid, address indexed senderDid, uint256 amountMinor, uint256 fxRateBps);
    event Matched   (bytes32 indexed intentCid, bytes32 indexed counterCid, uint256 srcMinor, uint256 tgtMinor);
    event ReserveDisbursed (bytes32 indexed intentCid, uint256 srcMinor, uint256 tgtMinor);
    event Claimed   (bytes32 indexed intentCid, address indexed recipientDid, uint256 tgtMinor);
    event Rebalanced(uint256 fromMinor, uint256 toMinor, address indexed dex, uint256 swapRateBps);

    modifier onlyAdherent(address holder) {
        require(adherentSbt.balanceOf(holder) > 0, "KawaseYuiPool: not adherent");
        _;
    }

    function deposit(bytes32 intentCid, uint256 amountMinor, uint256 fxRateBps)
        external
        onlyAdherent(msg.sender)
        // ... per-month cap check, band check, etc.
    { /* ... */ }

    function claim(bytes32 intentCid)
        external
        onlyAdherent(msg.sender)
    { /* ... */ }

    // Council-authorized rebalance via Aerodrome-on-Base or comparable DEX
    function rebalance(
        address dex,
        uint256 amountInMinor,
        uint256 minAmountOutMinor,
        bytes32 attestationCid
    )
        external
    {
        require(msg.sender == councilSafe, "KawaseYuiPool: not council");
        // ... swap via dex, emit Rebalanced
    }
}
```

**Hard-coded invariants** (Solidity-level):
- `deposit()` reverts unless `adherentSbt.balanceOf(msg.sender) > 0` (G3 structural)
- `deposit()` reverts unless `|fxRateBps - chainlinkBps| ≤ maxBandBps` (G4 structural)
- Monthly volume cap from `IConstitution.getConstant("kawase.per_month_cap_usd_minor")` (G9)
- `rebalance()` callable only by `councilSafe` (G14 structural via Council Lv6+ ≥4/7 multisig signing requirement at the Safe level)

### Charter compliance map (how each constraint is honored)

| Constraint | How honored |
|---|---|
| Charter §1.5 anti-commercialization | mid-market rate locked at intent; spread profit = 0 (G5 const). Operating cost = mKOTO via donation flow (ADR-2605282100); no fee charged to sender or recipient. |
| Charter §2(b) speculative finance prohibition | NO FX arbitrage (N2); NO yield farming on pool capital (N10); NO DEX aggregation (N7); rebalance restricted to ≤1/month at R1 within ±1% band Council-attested. Pool itself = stablecoin holding, not speculative position. |
| Charter §1.12 routing-around | Adherent SBT replaces FATF passport KYC (G10); no SWIFT / no commercial MSB integration; settlement is fully on-chain Base L2 (ADR-2605172100 L3). |
| ADR-2605282100 N2 mKOTO non-transferability | mKOTO is NOT the settlement token — USDC/EURC is. mKOTO appears only in the operator-DID compute-cost layer (L4 cell). No external party ever holds or transfers mKOTO via kawase-yui. |
| ADR-2605172100 Alt C "no custom token" | NO new ERC-20 minted. Settlement uses canonical Base L2 stablecoins (USDC + EURC R1). |
| ADR-2605172100 payment-category enum | Sender→recipient transfer purpose = new value `kawase-mutual-aid` (Lexicon enum addition; not titheable per ADR-2605192130 §5 — but mappable to existing `internal-purchase` if Council prefers reuse). Decided at R1 Lexicon ratify. |
| ADR-2605192130 10% tithe constitutional constant | NOT applied to kawase flows at R0-R3 (§5 Kisha/grant-pattern exemption: pure adherent personal mutual aid). R4+ ADR may introduce a 0-3% optional skim for sustainability; until then, 0%. |
| ADR-2605192115 §3 SBT carve-out | Sender + recipient MUST both be Adherent SBT holders (G3 structural in Solidity). Non-SBT participants categorically rejected (N3 — routed to wakai or chigiri instead). |
| ADR-2605215000 Murakumo-only | pool_match + fx_oracle_watcher + rebalance_proposer + jurisdiction_compliance + silen_review cells ALL run on Murakumo fleet only (G12 structural via fleet.toml allow-list inherited from ADR-2605282100 N6 pattern). |
| ADR-2605282100 mKOTO economy | pool_match cell compute = gpu_seconds debited per epoch tick; royalty credited to indexer DIDs per Quad write. |
| ADR-2605263500 wakai mutual aid sibling | Same constitutional framing (adherent personal mutual aid, not insurance). kawase-yui covers international transfer; wakai covers health/disability/unemployment/disaster. Together they form the religious-corp mutual-aid network. |
| ADR-2605262700 chigiri multi-juris | jurisdiction_compliance cell reads chigiri.ipLicenseClaim + tax_receipt records to determine which juris pairs are activated; disputes route to chigiri.disputeMediation. |
| ADR-2605262900 toritate accounting | All kawase flows recorded on-chain + MST anchor → toritate ledger entry purpose=`kawase-mutual-aid` (new category); annual silenKawaseReview cross-references toritate.annualReport. |
| Charter Rider §2(c) covert ops | NO surveillance of sender↔recipient relationship beyond what is publicly anchored on Base L2 (which is necessarily public). Encrypted memo via ADR-2605181100 envelope optional; default no memo. |
| Charter Rider §2(e) anti-gatekeeping | Wise / Western Union / MoneyGram / Remitly / WorldRemit / Xoom / Revolut / OFX / Currencies Direct / Ria / Paysend / PayPal-Xoom **PROHIBITED** as vendor or integration partner (G7 structural in jurisdictionAttestation enum DELIBERATE EXCLUSION). |

### 14 immutable gates G1..G14

- **G1**: Charter Rider §2(a)-(h) scan on every send memo + every jurisdictionAttestation legal analysis + every rebalanceAttestation justification.
- **G2**: kotoba-datomic → kotoba attestation lineage MANDATORY (matchExecution + rebalanceAttestation + silenKawaseReview).
- **G3**: Adherent SBT↔SBT only — structural in Solidity `onlyAdherent` modifier on both deposit and claim. Non-SBT participation categorically rejected.
- **G4**: Mid-market Chainlink oracle ±0.5% band — `Constitution.sol` const `kawase.max_band_bps = 50`. Out-of-band halts all matches; Council Lv6+ ≥3 attestation required to resume.
- **G5**: NO spread profit — `silenKawaseReview.spreadProfitMkoto` const 0; structural enforcement. Operator compensation comes from mKOTO economy royalty pool, NOT from FX spread.
- **G6**: Pool capital USDC/EURC/JPYC stable-only — NO yield farming, NO DeFi positions, NO LP tokens, NO perp DEX exposure. Pool token = the stablecoin itself, held in the KawaseYuiPool contract.
- **G7**: NO commercial remittance software — Wise / Western Union / MoneyGram / Remitly / WorldRemit / Xoom / Revolut / PayPal-Xoom / OFX / Currencies Direct / Ria / Paysend / Atlantic Money / Sendwave / Boss Revolution **PROHIBITED** per Charter Rider §2(e) + §2(c). Enforced by build-time lint hook (`70-tools/scripts/lint/verify_no_commercial_remittance.py` — to be added at R1).
- **G8**: NO fiat custody — religious-corp NEVER holds USD/EUR/JPY/etc. fiat bank balance. Adherents on/off-ramp via their own Coinbase/Kraken/local-exchange accounts. The pool holds only stablecoin ERC-20 token positions.
- **G9**: Per-month cap default $1,000 USD-equivalent / member (R1); $5,000 (R2); $25,000 (R3). Higher caps require Council Lv6+ ≥3 per-member ADR. `Constitution.sol` const `kawase.per_month_cap_usd_minor`.
- **G10**: KYC = Adherent SBT, period. NO Travel Rule / FATF passport / state-issued ID. Charter §1.12 routing-around invariant.
- **G11**: NO chargeback / NO fraud reversal — on-chain finality per ADR-2605172100 §"No chargebacks" + ADR-2605263500 wakai N9 inherited. Disputes route to chigiri.disputeMediation (cooperative-first per ADR-2605262700 G10), NOT to settlement reversal.
- **G12**: Murakumo-only inference for ALL pool cells — pool_match / fx_oracle_watcher / rebalance_proposer / jurisdiction_compliance / silen_review. ADR-2605215000 fleet.toml allow-list applies.
- **G13**: 100% kotoba content-addressed substrate per ADR-2605262130. NO Kotoba/Datomic projection, NO off-chain primary ledger, NO commercial DB.
- **G14**: Per-jurisdiction Council Lv7+ unanimity activation. NO send/receive pair activated without explicit `jurisdictionAttestation` Lexicon record signed by all 5 Council seats. R1 launch jurisdictions: US (Founder seat 1) + JP (Founder seat 1) — Council Lv7+ unanimity will gate EU activation pending Bootstrap Council Seats 2-5 (RFP open until 2026-06-19).

### 12 non-goals N1..N12

- **N1**: NOT a commercial money services business — no MSB / MTL / EMI / PI license sought; structurally pinned to adherent mutual aid framing.
- **N2**: NOT FX trading or arbitrage — mid-market locked at intent; no proprietary position-taking; no spread profit.
- **N3**: NOT non-adherent remittance — non-SBT participants categorically rejected; routed to chigiri (procedural) or wakai (mutual aid) instead.
- **N4**: NOT fiat custody — religious-corp NEVER holds fiat bank balances. On/off-ramp is adherent-self-served via their own exchange accounts.
- **N5**: NOT cross-jurisdictional MSB — no SWIFT, no correspondent banking, no NACHA, no SEPA-direct, no Zengin-direct integration.
- **N6**: NOT speculative finance per Charter Rider §2(b) — no yield farming on pool capital, no DeFi positions, no LP, no perp.
- **N7**: NOT a DEX aggregator — rebalance uses ONE Council-approved DEX (Aerodrome-on-Base or comparable) per rebalanceAttestation; no multi-DEX routing optimization.
- **N8**: NOT Travel-Rule / FATF compliant on passport ID — Charter §1.12 invariant; SBT is the structural replacement.
- **N9**: NOT chargeback / NOT fraud reversal — on-chain finality (G11).
- **N10**: NOT yield farming on pool capital — pool sits as plain ERC-20 holding in the contract.
- **N11**: NOT loan / NOT credit issuance — kawase is settlement-only; lending is structurally separate (future actor if Council-ratified, R4+).
- **N12**: NOT minting a new stablecoin / NOT minting a new token. Settlement uses canonical USDC/EURC/JPYC/etc.; accounting uses existing mKOTO; no new token type.

### Implementation ladder R0→R3

| Phase | Scope | Status |
|---|---|---|
| **R0** | This ADR + 8 Lexicons + paths reserved (no code) + deps.toml registry entries | landed this commit |
| **R1** | Solidity scaffold (`50-infra/etzhayyim-kawase-pool/`); kotoba_kawase Python facade scaffold; 2 cells activate (pool_match + fx_oracle_watcher); USDC↔EURC pair only; Chainlink USD-EUR feed wired; ≤50 adherents; ≤$50k aggregate pool; Council Lv6+ ≥3 ratify; build-time lint hook against G7 commercial remittance imports | post-Bootstrap-Council ratify; depends on chigiri R1 + toritate R1 |
| **R2** | +JPYC pair (Polygon-bridged via LayerZero — Charter Rider §2(e) bridge audit Council Lv6+ ≥3 required); 30-day public objection; ≤500 adherents; ≤$500k aggregate; +2 cells (rebalance_proposer + jurisdiction_compliance); chigiri R2 multi-juris prerequisite | post-R1 + 30-day public objection |
| **R3** | +KRWO / +GBPe / +CHFe per-pair Council Lv7+ unanimity attestation; ≤5,000 adherents; ≤$5M aggregate; +1 cell (silen_review); wakai R3 sibling-integration for kawase↔wakai cross-actor mutual-aid bundles (e.g. medical-evacuation transfer = wakai medical-event + kawase international transfer composed) | post-R2 + Council Lv7+ |

### Cross-actor binding

- **wakai** (ADR-2605263500): sibling actor; mutual-aid constitutional framing shared. wakai = health/disability/unemployment/disaster; kawase-yui = international adherent transfer. R3 cross-actor integration enables composite flows (e.g., medical evacuation = wakai medical event + kawase cross-border).
- **chigiri** (ADR-2605262700): multi-jurisdictional compliance + dispute mediation + UPL boundary. kawase-yui jurisdiction_compliance cell reads chigiri.ipLicenseClaim per-juris records. Disputes route to chigiri.disputeMediation (G11 — no settlement reversal, only cooperative mediation).
- **toritate** (ADR-2605262900): all kawase flows recorded; toritate.ledgerEntry purpose `kawase-mutual-aid`; annual silenKawaseReview cross-referenced with toritate.annualReport.
- **TitheRouter** (ADR-2605192130): NOT used at R0-R3 (solidarity skim = 0%). R4+ Council Lv6+ ≥3 may activate 0-3% skim → TitheRouter path.
- **kotoba** (ADR-2605262130): substrate engine for all Quads + Pregel cells.
- **mKOTO economy** (ADR-2605282100): cell compute cost layer; royalty credit to indexer DIDs.
- **Murakumo fleet** (ADR-2605215000): all cell inference.
- **Public Fund Safe** (ADR-2605192145): R1 reserve buffer seed grant (Council Lv6+ ≥4/7).
- **Bootstrap Council** (ADR-2605192300): Lv6+ ≥3 = tariff / rebalance band; Lv6+ ≥4/7 = rebalance authorization; Lv7+ unanimity = per-jurisdiction activation.

## Consequences

**Positive**:

- Adherents in dispersed jurisdictions get Wise-equivalent UX ("send 100, receive 100 minus a transparent mKOTO cost, mid-market rate") without religious-corp becoming an MSB or FX trader.
- The Wise innovation (pre-funded local pool + balance netting) is religious-corp-shaped: pool capital comes from Public Fund grant (mission-aligned), matching is non-profit-aligned (mid-market only), and the structural exclusion of non-adherents preserves Charter §1.5 + §2(b).
- No new token minted → no securities-law exposure, no §2(b) speculative finance issue, no fragmentation of liquidity.
- mKOTO economy gets a major usage axis — pool_match cell is high-volume compute, and the royalty flow back to indexer DIDs validates the L4 cash-routing pattern of ADR-2605282100 across a non-inference use case.
- wakai (mutual aid) + kawase-yui (transfer) + chigiri (procedural) + toritate (accounting) form a coherent "religious-corp financial backbone" that is fully constitutional, fully on-chain, and fully auditable.

**Negative / Tradeoffs**:

- Pre-funded reserve buffer is a Public Fund Safe drain — $5k at R1, $50k at R2, $500k at R3. Council Lv6+ ≥4/7 grant approval needed per pool seed. This is significant capital commitment but is mission-aligned (mutual aid).
- Match wait time can be 5-15 minutes when pool flow is thin (vs. Wise's "few seconds" at scale). Reserve buffer absorbs this UX gap but consumes reserve capital. R2+ as pool flow grows, match share should rise toward ≥80% (target in silenKawaseReview).
- Per-jurisdiction Council Lv7+ unanimity gate (G14) limits R1 launch geography to founder-Council jurisdictions (US + JP at Bootstrap Council pre-ratification; EU pending Council Seats 2-5 close). Other jurisdictions need explicit attestation chain → slower expansion than Wise's commercial license-shopping model.
- DEX rebalance dependency (Aerodrome-on-Base) creates one external counterparty risk. Mitigation: rebalance is rare (≤1/month R1), each instance is Council-attested, and the DEX is open-source and audit-proven.
- Adherent-only structural pin (G3) means non-adherent family members of adherents cannot directly use the system; they must route through their adherent counterpart (sender or recipient) as an intermediary. This is a feature (Charter §1.5 fit) but a UX limit.

**Constitutional**:

- ADR-2605172100 Alt C "no custom token" **preserved** — no new ERC-20.
- ADR-2605282100 N2 mKOTO non-transferability **preserved** — mKOTO appears only in compute-cost layer, not settlement.
- ADR-2605192115 §3 SBT carve-out **strengthened** — kawase-yui is the cleanest example of SBT↔SBT internal-purchase pattern at scale.
- ADR-2605192130 10% tithe constitutional constant **honored via §5 exemption** — kawase-yui is in the Kisha/grant-pattern exemption class (intra-adherent mutual aid not titheable).
- Charter §1.12 routing-around **strengthened** — first major end-user financial flow that fully routes around SWIFT + state-licensed MSBs.

## Alternatives Considered

1. **Mint a new ERC-20 "KAWASE" token as the settlement medium**. Rejected: ADR-2605172100 Alt C + ADR-2605282100 N2 + Charter §2(b). No additional benefit over canonical USDC/EURC; introduces securities-law exposure and liquidity fragmentation.
2. **Use mKOTO as the settlement medium** (not just compute cost). Rejected: ADR-2605282100 N2 mKOTO non-transferability constitutional invariant.
3. **Integrate with Wise / Revolut as a backend** (white-label the commercial MSB). Rejected: Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops avoidance. Vendor closed query-tracking on adherent financial posture structurally unacceptable.
4. **Use Stripe Connect cross-border for fiat sending**. Rejected: ADR-2605172100 prohibits fiat processors entirely.
5. **Skip the pool-match topology; just do direct USDC→USDC (Venmo-equivalent)**. Rejected: collapses the multi-currency use case (sender US sends USD, recipient EU wants EUR — direct USDC transfer leaves the off-ramp problem unsolved). The whole reason to build this actor is the multi-currency case; single-currency case is already covered by `Etzhayyim.pay()` (ADR-2605172100).
6. **Allow non-adherent recipients (relax G3)**. Rejected: collapses to commercial remittance (G3 is the structural pin that distinguishes mutual aid from MSB). Non-adherent remittance routes through wakai (emergency one-time relief, Council Lv6+ ≥3 per-instance) or chigiri (procedural).
7. **Set solidarity skim to 10% (mirror ADR-2605192130 default)**. Rejected: ADR-2605192130 §5 explicitly exempts adherent-personal-mutual-aid analog flows (Kisha/grant pattern). Treating kawase as titheable would weaken the mutual-aid function — same constitutional reasoning that exempts Kisha. R4+ may revisit with a 0-3% Council-set rate after pool flow data exists.
8. **Use a constant-product AMM (Uniswap-style) instead of mid-market oracle + reserve buffer**. Rejected: AMM curve necessarily creates spread (= LP fee), which is structurally market-making (G6 violation) and creates spread profit (G5 violation). Mid-market oracle + reserve buffer is the only structurally-compatible topology.
9. **Set R1 pair to USDC↔JPYC** (Japan adherent cohort priority). Rejected (R1): JPYC is Polygon-native; Base L2 only has bridged versions which add LayerZero/Stargate dependency and a Charter Rider §2(e) vendor-audit hurdle. R2 introduces JPYC after Council Lv6+ ≥3 audits the bridge. R1 stays Base-L2-native (USDC + EURC) for cleanest constitutional fit.

## Open Questions

1. **Payment-category enum** — add new `kawase-mutual-aid` value or reuse existing `internal-purchase`? R1 Lexicon ratify decides. Recommendation: new value, because `internal-purchase` semantically implies a goods/service exchange that kawase does not represent.
2. **Reserve buffer seed funding source** — Public Fund grant is the default; alternative: founding Council seats co-fund 1:1 with Public Fund as proof-of-commitment. R1 Council decides.
3. **Per-jurisdiction Lexicon legal analysis depth** — chigiri.ipLicenseClaim minimum content per jurisdiction (e.g., money-services-business non-applicability memo + securities-law non-applicability memo + AML/CFT non-applicability memo). R1 chigiri-cross-actor template needed.
4. **Match window default** — 600s (10 min) is the R0 default. Real flow data at R1 may justify tightening (e.g., 180s) or loosening (1800s). Quarterly silenKawaseReview reports include avgMatchWaitSeconds for tuning.
5. **EURC liquidity sufficiency on Base L2** — Circle EURC has lower aggregate liquidity than USDC. R1 reserve buffer sizing should account for this. R1 pre-launch check: verify EURC on Base L2 daily volume ≥ $5M (~100× our R1 cap).

## References

- ADR-2605282100 (kotoba mKOTO economy + Modal billing-parity — compute-cost layer)
- ADR-2605262130 (kotoba canonical storage substrate)
- ADR-2605263500 (wakai mutual aid — closest sibling)
- ADR-2605262700 (chigiri legal procedure — multi-juris + UPL boundary)
- ADR-2605262900 (toritate accounting + audit)
- ADR-2605192130 (10% tithe auto-split — TitheRouter + §5 Kisha exemption reasoning)
- ADR-2605192145 (Public Fund Safe — reserve buffer seed source)
- ADR-2605192200 (Charter Rider v2.0 — §2(b) speculative finance prohibition)
- ADR-2605172100 (payments on chain — Base L2 + USDC + ERC-4337 + Alt C "no custom token")
- ADR-2605192115 (non-profit donation-only — §3 SBT carve-out)
- ADR-2605215000 (Murakumo-only inference — pool cells)
- ADR-2605181100 (signal-envelope encryption — optional memo)
- ADR-2605231525 (server-side signing capability — DID-bound auth)
- ADR-2605192300 (Bootstrap Council — Lv6+ ≥3 / Lv6+ ≥4/7 / Lv7+ unanimity gates)
- `00-contracts/lexicons/com/etzhayyim/kawase/` (8 Lexicons landed this commit)
- `50-infra/etzhayyim-kawase-pool/` (R1 Solidity scaffold destination)
- `20-actors/magatama/cells/kawase_*/` (5 Pregel cell paths reserved at R0)
- `20-actors/kawase-yui/` (Tier-B actor root, R1 scaffold destination)
- Wise Group plc public 10-K filings (reference for topology decomposition; NOT integrated as vendor — Charter Rider §2(e))
- Circle EURC on Base L2 — https://www.circle.com/en/eurc
- Aerodrome Finance on Base L2 — https://aerodrome.finance/ (rebalance DEX candidate)
- Chainlink Price Feeds — https://docs.chain.link/data-feeds
