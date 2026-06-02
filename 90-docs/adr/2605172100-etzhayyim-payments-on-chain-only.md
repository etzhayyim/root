---
id: adr-2605172100-etzhayyim-payments-on-chain-only
title: "ADR-2605172100: etzhayyim payments — Base L2 + USDC + ERC-4337 Smart Account (on-chain only, no fiat processor)"
status: proposed
doc_type: adr
topic: etzhayyim-payments-on-chain-only
authoritative: true
last_verified: 2026-05-17
priority: 8.0
axis: architecture
weight: 0.80
priority_note: "Closes the substrate purity loop opened by ADR-2605172000. RW-free state + on-chain payments together make the etzhayyim ecosystem operable without any centralized intermediary (no DB, no Stripe, no bank). Defines the payment SDK surface, the smart wallet binding, and the paymaster economics."
authoritative_for:
  - hard rule: etzhayyim/root apps MUST NOT integrate fiat payment processors (Stripe / PayPal / Square / Razorpay / credit-card gateways / bank ACH)
  - primary payment substrate: Base L2 + USDC (Coinbase Bridged on Base, contract 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
  - account model: ERC-4337 Smart Account, DID-bound via Coinbase Smart Wallet
  - gas sponsorship: etzhayyim-operated paymaster contract (funded by anchor-batch fee skim)
  - payment record convention: every settled tx → AT Record (NSID com.etzhayyim.apps.payment.*) for verifiability + audit
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605170900-etzhayyim-root-adr-canonical-home
related:
supersedes: []
superseded_by: []
---

# ADR-2605172100: etzhayyim payments — Base L2 + USDC + ERC-4337 Smart Account (on-chain only, no fiat processor)

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

ADR-2605172000 established that etzhayyim apps run on AT MST + IPFS + Base L2 with no centralized DB. That makes **state** decentralized. But if those apps accept payments via Stripe or any fiat processor, the **money layer** still has a single centralized intermediary that can freeze funds, KYC-block users, or take the platform offline by withdrawing service. The verifiability of the state layer is undermined by the trust assumption on the money layer.

To close the loop, **payments must live on the same substrate as state**. The Base L2 anchor that already exists (ADR-2605171800 Stage 5) is also the natural payment rail: it's EVM-compatible, has USDC native, and Coinbase operates it so settlement reliability is comparable to a traditional payment processor.

The upstream identity stack already commits to **ERC-725 Root Identity + Coinbase Smart Wallet** at the identity layer (ADR-0074, ADR-0095). This ADR extends that to the payment layer: the same Smart Wallet that the user signs DIDs with is the same wallet that pays.

# Decision

**Hard rule**: every app under `etzhayyim/root/` that handles value transfer MUST use on-chain settlement via Base L2. **Fiat payment processors (Stripe / PayPal / Square / Razorpay / credit-card gateways / bank ACH / wire transfer) are prohibited in etzhayyim/root.**

If an open app legitimately needs fiat acceptance (regulatory, accessibility), the fiat side lives **upstream** as a separate service exposing a paid-tier XRPC. The open app calls it as progressive enhancement (per ADR-2605172000 upstream carve-out) and remains operational with on-chain-only payments.

## Payment substrate (4 layers)

```
┌────────────────────────────────────────────────────────────┐
│ L4  Audit       — AT Record (com.etzhayyim.apps.payment.*)        │
│                   anchored to MST → IPFS → Base L2          │
├────────────────────────────────────────────────────────────┤
│ L3  Settlement  — USDC on Base L2 (Coinbase Bridged)        │
│                   contract 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 │
├────────────────────────────────────────────────────────────┤
│ L2  Account     — ERC-4337 Smart Account (Coinbase Smart    │
│                   Wallet), DID-bound 1:1 via signed         │
│                   attestation record                        │
├────────────────────────────────────────────────────────────┤
│ L1  UX gas      — etzhayyim-operated Paymaster contract,    │
│                   funded by anchor-batch fee skim;          │
│                   user signs with passkey, never sees gas   │
└────────────────────────────────────────────────────────────┘
```

## Canonical choices

| Slot | Choice | Reason |
|---|---|---|
| **L2 network** | Base (Coinbase L2) | Native USDC, ~$0.001 / tx, 2s blocks, EVM-compatible, regulated operator (Coinbase). Same chain as ADR-2605171800 anchor; one less network to manage. |
| **Stablecoin** | USDC (Coinbase Bridged on Base, `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) | Native to Base, 1:1 reserves, regulated issuer, broad acceptance. Avoids Tether / algorithmic stablecoin risk. |
| **Account model** | ERC-4337 Smart Account via Coinbase Smart Wallet | Per ADR-0095. Social recovery + passkey signing + sponsored gas. EOA prohibited for new accounts. |
| **Signing** | WebAuthn passkey → Smart Wallet validator (P256 verifier on-chain) | No seed phrase. iCloud Keychain / Google Password Manager sync. Recovery via passkey re-enroll. |
| **Gas sponsorship** | etzhayyim Paymaster contract (deployed by etzhayyim, funded by anchor-batch fee skim) | Users never see gas. Onboarding friction = zero. Paymaster solvency monitored by anchor-cron (ADR-2605171800 Stage 5). |
| **Subscription model** | Superfluid streaming (per-second flow) for ongoing, or simple periodic Permit2 pull for monthly | Superfluid = no missed-payment risk; Permit2 = simpler integration. App chooses per use-case. |
| **Recurring revenue split** | 0xSplits (immutable on-chain split contract) | One tx → N recipients. Audit trail on-chain. |
| **Refund / dispute** | Escrow Safe (Gnosis Safe multisig) + on-chain dispute log | Funds held in 2-of-3 Safe with user / merchant / etzhayyim-arbiter; release on signed attestation. |
| **Privacy** | Per-payment ephemeral Smart Account (stealth address pattern), revealed only to recipient via E2E | Trade-off accepted; not all flows need this. Default = direct from user's main Smart Wallet. |
| **Fiat off-ramp** | Coinbase Onchain Verification → bank | Out of etzhayyim/root scope. User self-serves via Coinbase Wallet or Coinbase exchange. |

## SDK extension: `Etzhayyim.pay()`

```typescript
import { Etzhayyim, parseUsdc } from "@etzhayyim/sdk";

const e = new Etzhayyim({ /* ... per ADR-2605172000 ... */ });

// One-shot payment
const receipt = await e.pay({
  to: "did:web:recipient.etzhayyim.com",   // or 0x address
  amount: parseUsdc("10.00"),               // USDC base units (6 decimals)
  token: "USDC",                            // default; only token supported in v0.1
  reason: {                                 // recorded as com.etzhayyim.apps.payment.sent
    collection: "com.etzhayyim.apps.payment.sent",
    purpose: "donation",                    // or "tip", "subscription", "purchase", "refund"
    forUri?: "at://did/coll/rkey",          // links to the thing being paid for
    memo?: "thank you for the open data API",
  },
  paymaster: "sponsored",                   // default — etzhayyim paymaster pays gas
});
// → { txHash, recordUri, blockNumber, atomicBatch: false }

// Streaming subscription (Superfluid)
const stream = await e.payStream({
  to: "did:web:recipient.etzhayyim.com",
  flowRate: parseUsdcPerSecond("10.00 / month"),  // = 3.858e-6 USDC/s
  reason: { collection: "com.etzhayyim.apps.payment.stream", purpose: "subscription" },
});
// → { streamId, startedAt }

await e.payStreamStop(stream.streamId);

// Verify payment (Merkle proof + L2 tx)
const proof = await e.verify(receipt.recordUri);
// → { included: true, anchoredAt: {...}, paymentTx: { txHash, from, to, amount } }
```

## Payment record lexicon (`com.etzhayyim.apps.payment.*`)

New Lexicon under `00-contracts/lexicons/com/etzhayyim/apps/payment/`:

- `sent.json` — one-shot transfer; required: `to`, `amount`, `tokenContract`, `txHash`, `purpose`, `forUri?`, `memo?`
- `received.json` — counterpart record on recipient's PDS (created by their listener)
- `streamStarted.json` — Superfluid stream open; required: `to`, `flowRate`, `tokenContract`, `superfluidStreamId`
- `streamStopped.json` — Superfluid stream close
- `escrowOpened.json` — Safe-based escrow open; required: `safeAddress`, `dueDate`, `arbiter`
- `escrowReleased.json` — escrow release event
- `refundIssued.json` — refund (linked to original `sent` record)
- `split.json` — 0xSplits distribution event

Each record carries the on-chain `txHash` and `blockNumber` so any reader can re-verify via Base L2.

## Per-app payment patterns

| App pattern | Payment use | Pattern |
|---|---|---|
| Open data API (`open-isco`, `open-naics`, `open-hs`, etc.) | per-call micropayment | Paymaster sponsors; quota burns USDC against user's pre-loaded credit. Optional — free tier exists. |
| Public fund (`public-fund`) | grant disbursement | 0xSplits to recipients; on-chain proof of allocation. |
| Public sento (`public-sento`) | community pool donations | Direct USDC transfer; `com.etzhayyim.apps.payment.sent` with purpose=donation. |
| AppView tipping (`yoro`) | content tip | Direct USDC, no escrow. Receiver listens on PDS firehose for `received` events. |
| Open banking (`open-banking`) | core banking primitives | Smart contract on Base for the ledger; off-chain MST projection for the human-readable account view. |
| Religious-corp offerings (`otakiage`, `*-jinja` style) | offering | Direct USDC, AT Record carries blessing/intention text. |
| Subscription (paid features) | recurring | Superfluid stream OR Permit2 monthly pull, user choice. |
| Refund | dispute resolution | Escrow Safe pattern; arbiter = etzhayyim multisig. |

## Hard rules (CI-enforceable)

- **No `stripe`, `paypal`, `square`, `razorpay`, `braintree`, `adyen`** package imports anywhere under `etzhayyim/root/`.
- **No `bank_account`, `ach_credit`, `wire_transfer`, `card_number`** string literals.
- **No fiat currency codes** (`USD`, `EUR`, `JPY`, `INR`, ...) as `currency` field in payment records (USDC base units only; display layer can convert).
- **All payment flows MUST go through `Etzhayyim.pay()` / `.payStream()` / `.payStreamStop()`**. Direct `viem.writeContract` for USDC transfer from app code is prohibited; the SDK is the only seam.
- **All payment events MUST be recorded as AT Records** (in addition to the on-chain tx) so MST traversal can reconstruct payment history without requiring a chain indexer.

# Consequences

## 正の効果

- **Censorship-resistant money.** No Stripe to disable the account, no bank to freeze. Coinbase / Base operator could in principle block (regulated entity), but USDC + Base L2 has the strongest regulated-but-decentralized profile available today.
- **Substrate consistency.** State (ADR-2605172000) + payments are now on the same Base L2 — one chain, one wallet, one verifiability story.
- **Programmable money.** Splits / streams / escrow are native, not bolted-on. Public funds disburse via on-chain split, not via 1099 form workflows.
- **Audit by anyone.** Every payment leaves a public on-chain tx + an AT Record. No "trust our internal Stripe export"; any third party can replay.
- **Onboarding friction = zero gas.** Passkey signs; Paymaster sponsors. User experience matches Stripe Checkout, but with on-chain settlement.
- **DID = identity = wallet.** One signature flow for state writes and for payments. No separate KYC layer needed for open scope (regulated activities use upstream backend per carve-out).

## 負の効果 / コスト

- **USDC dependence.** Coinbase USDC reserves / regulatory status is a single point of failure. Mitigation: monitor stability; have a v1 multi-stablecoin upgrade path (USDC + USDT + PYUSD).
- **Coinbase Smart Wallet dependence.** The wallet abstraction is Coinbase-built. If Coinbase deprecates, migration to alternative ERC-4337 wallet (e.g., Safe-on-Base) is needed. SDK abstracts this enough to make migration mechanical.
- **L2 reorg / outage risk.** Base has had brief outages. Mitigation: payment finality wait (3 blocks ~6s) before AT Record creation; idempotency key in `sent.json` to detect double-spend reconciliation.
- **Privacy of payment graph.** All payments are public on-chain. Mitigation: stealth-address ephemeral Smart Accounts for sensitive flows (out of scope for v0.1; future ADR).
- **Paymaster solvency.** etzhayyim must keep paymaster topped up. anchor-cron (ADR-2605171800) extends to monitor + auto-refill from anchor batch fee skim.
- **Regulatory uncertainty.** Some jurisdictions treat USDC transfers as MSB / money transmission. etzhayyim's religious-corp form gives some shelter for non-commercial flows (donations / offerings); commercial flows route through upstream backend or are scoped to non-restrictive jurisdictions.
- **No chargebacks.** On-chain is final. Refund flow is opt-in via escrow Safe; users must understand the trade-off vs Stripe-style chargeback protection.

## Migration plan

1. **SDK pay() stub** (this commit alongside ADR): `Etzhayyim.pay()` / `.payStream()` / `.payStreamStop()` method signatures + types, throws "not yet implemented" with explicit TODO breakdown.
2. **Payment lexicon** (this commit): `00-contracts/lexicons/com/etzhayyim/apps/payment/{sent,received,streamStarted,streamStopped,escrowOpened,escrowReleased,refundIssued,split}.json` schemas.
3. **Paymaster contract** (follow-up): `50-infra/etzhayyim-paymaster/` — ERC-4337 paymaster, fee-skim funded, Solidity + Foundry deploy script.
4. **Reference impl**: pick the simplest payment flow (donation / `public-sento`) and wire end-to-end through SDK + paymaster + AT Record.
5. **CI hooks**: lint-`stripe-import`, lint-`fiat-currency-code`, lint-`direct-viem-payment` — fail PR on any.
6. **Coinbase Smart Wallet integration**: `@coinbase/wallet-sdk` adapter inside SDK; passkey → P256 validator → on-chain Smart Account.
7. **Superfluid + 0xSplits + Safe**: integration libraries pulled in as SDK sub-modules.

# Alternatives Considered

## A. Stripe (status quo)

Keep using Stripe with on-chain state. 却下: undermines verifiability — operator can be deplatformed; KYC blocks; chargebacks reverse settled state; double source of truth (Stripe ledger + AT records).

## B. Lightning Network (BTC L2)

Bitcoin L1 + Lightning channels. 却下: no native USD stablecoin (no Taproot Assets at scale); UX is harder (channel mgmt); no EVM = no anchor-contract reuse from ADR-2605171800. Not all of these are dealbreakers, but the integration complexity is higher than Base.

## C. Custom token (etzhayyim-issued)

Issue an `ETZ` ERC-20 for in-network value. 却下: regulatory burden (looks like a security), no off-chain conversion path, fragments liquidity. USDC is strictly superior for stablecoin use.

## D. Off-chain ledger with periodic on-chain settlement (rollup pattern)

Net N transactions off-chain, settle the diff on L2. 却下: introduces an off-chain operator (centralization), complicates auditability, and doesn't significantly reduce L2 gas at Base's current price (~$0.001/tx). Skip the optimization.

## E. Multiple L2s (Base + Optimism + Arbitrum + ...)

Multi-chain for redundancy. 却下: not the right time. SDK abstraction will allow this in v1.0+ if Base deteriorates; meanwhile YAGNI.

# References

- ADR-2605172000 [etzhayyim/root open apps MUST be RW-free](./2605172000-etzhayyim-rw-free-substrate.md) — substrate context this ADR extends to money
- ADR-2605171800 [LangGraph Pregel → MST → IPFS → Base L2 anchor pipeline](./2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — same chain, same anchor contract
- ADR-2605170900 [etzhayyim/root canonical home](./2605170900-etzhayyim-root-adr-canonical-home.md)
- ADR-0074 Ethereum Identity Bridge — CACAO + WebAuthn
- ADR-0095 Simplified 3-Layer Identity (ERC-725 + Coinbase Smart Wallet)
- USDC on Base — https://docs.cdp.coinbase.com/onchain-payments/welcome
- ERC-4337 Smart Account spec — https://eips.ethereum.org/EIPS/eip-4337
- Coinbase Smart Wallet — https://www.smartwallet.dev/
- Superfluid streaming — https://docs.superfluid.finance/
- 0xSplits — https://docs.splits.org/
- Permit2 — https://github.com/Uniswap/permit2
- Gnosis Safe — https://docs.safe.global/
