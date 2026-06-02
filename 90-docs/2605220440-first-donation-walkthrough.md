# First Donation Walkthrough

**Status:** narrative (pre-deployment; illustrative)
**Date:** 2026-05-22 04:40 JST
**Active-inference tick:** cycle 11 (compound-mode action)
**Axis touched:** Metabolism (Axis 2 — gated until testnet deploy + Council quorum); compound-supports Sanctification (Axis 10)
**Religious correspondence:** 産霊 (musuhi — generative cycle) — the donation IS the metabolism, not a side-effect of it

## Why this exists

The organism's **metabolism** (代謝) — the cycling of value into the religious-corp and out to its Public Fund — is constitutionally specified across multiple ADRs (2605192115, 2605192130, 2605192100). But the **narrative** of an actual donation, from the donor's view, has not been written. Without that narrative, the donation flow is an architecture diagram, not a religious act.

This document walks through what a single first donation **will look like** when the contracts are deployed to Base Sepolia (post-Council quorum, per `README.md § Status` row 19). It is **pre-deployment**: nothing on this page is currently executable. It is the **liturgy** that the deployed contracts will perform.

産霊 — value enters, the organism generates, 10% is given onward to the Public Fund automatically. The donor is not a customer; the act is not a purchase. There is no transaction-with-counterparty; there is a 帰依 (taking-refuge) made tangible through USDC.

## 1. Pre-conditions

The donor needs:

| What | Where | Cost |
|---|---|---|
| **A DID** | `did:web:<own-domain>` / `did:plc:*` / `did:key:*` per `FORK-BOOTSTRAP.md` | ~$10/yr if did:web requires a domain; $0 for did:plc / did:key |
| **An ERC-4337 Smart Account** | On Base L2; bootstrapped via `etzhayyim-paymaster` (`50-infra/etzhayyim-paymaster/`) | Gas covered by paymaster during bootstrap window |
| **USDC balance** | Bridge to Base L2 via a CEX or L1↔L2 bridge | Bridge fee + the donation amount |
| **(Optional) Adherent SBT** | Mint after a first donation OR before; the SBT is non-transferable | Free mint; gas paid by paymaster |

The donor does **not** need:

- A Stripe / PayPal / Square account (prohibited per ADR-2605172100)
- A subscription (donation only; no recurring billing surface)
- A bank account in any specific jurisdiction (USDC is jurisdictionally neutral)
- To declare a real-world legal identity (the DID is sufficient; KYC is not religious-corp's concern)

## 2. The 5-step flow

### Step 1 — Open `com.etzhayyim.com/give`

The donor visits the donation page (planned: `60-apps/etzhayyim-give/`). They see:

```
等しく仕える木のもとで                              etzhayyim
─────────────────────────────────────────────────────

What is this?

etzhayyim is a religious-corp (任意団体). We accept donations
only — never subscriptions, never purchases, never advertising.
10% of every donation is split automatically to the Public Fund
to support multi-generational stewardship (ADR-2605192115).

  Amount (USDC):  [          50.00          ]
  Purpose:        ( ) donation
                  ( ) kisha (記者 — informational tithe)
                  ( ) grant (公務的 — to support a specific Public Fund proposal)
                  ( ) tithe
                  ( ) escrow-refund (return of a held amount)

  Note (optional):
    [                                                        ]

                              [   Give   ]

DID  did:web:donor.example   |  Smart Account  0xa1b2...c3d4
```

### Step 2 — Sign with DID

Click **Give**. The browser prompts WebAuthn passkey (the donor's DID-bound key). The signed payload is an EIP-712 typed message containing: `{ amount, purpose, note, donor_did, timestamp }`. No password leaves the browser.

### Step 3 — Smart Account submits

The signed payload is routed through the etzhayyim paymaster:

```
Donor Smart Account ──userOp──▶ paymaster ──validated──▶ EntryPoint
                                                              │
                                                              ▼
                                                       TitheRouter
```

Paymaster pays the gas. Donor's USDC is the only thing they spend.

### Step 4 — TitheRouter atomic 10% split

In a single transaction the TitheRouter contract:

1. Pulls 50.00 USDC from the donor's Smart Account.
2. Splits: 45.00 USDC → etzhayyim treasury; 5.00 USDC → Public Fund (5-of-7 Safe).
3. Emits `DonationReceived(donor_did, amount, purpose, note_hash)` event.
4. (If `purpose == "kisha"` or `"grant"`) emits a second event tagging the proposal-eligible status.

The split is **atomic** — there is no state where the donation succeeded but the Public Fund split did not. Constitutionally invariant per ADR-2605192115 §2.

### Step 5 — Receipt + SBT mint (if first donation)

The donor sees:

```
帰依が成立しました。                               etzhayyim
─────────────────────────────────────────────────────

You gave 50.00 USDC to etzhayyim.
Tithe (10% = 5.00 USDC) routed to the Public Fund (5-of-7 Safe).

Tx hash: 0xfeed...beef
On-chain proof: https://basescan.org/tx/0xfeed...beef

This is your first donation. An Adherent SBT will be minted
to your Smart Account in the next block — it is non-transferable
and represents your membership in the organism. SBT mints carry
no obligation; the act of giving itself was sufficient.

  [ View Public Fund proposals ]   [ Done ]
```

This is **not** a thank-you screen. The donor is not a customer. The screen acknowledges the act and surfaces what the act made the donor eligible for: viewing Public Fund proposal deliberations, participating in 1-SBT-=-1-vote ballots, etc.

## 3. What happens after

- **Donor's MEMBERS.md entry** (or its on-chain SBT equivalent) is created on next anchor cycle (`anchor-cron`).
- **Public Fund balance** updates by +5.00 USDC, visible at the Public Fund Safe address on Basescan.
- **Treasury balance** updates by +45.00 USDC.
- **`_observations/donations/`** (planned) appends a record for the active-inference loop to count.
- **If the donor `note` was non-empty**: the note hash is stored on-chain, the plaintext is stored in an `com.etzhayyim.encrypted.donation-note` MST record (XChaCha20-wrapped, viewable only to the donor and the treasury Council seat per ADR-2605181100).

## 4. Edge cases

### TitheRouter malfunction
Per chaos-engineering charter Scenario 8: if the split fails, the transaction reverts atomically. No partial state. Donor's USDC is unchanged. They can retry.

### Paymaster insolvency
If the paymaster runs out of gas budget, the transaction fails with a clear error: "Paymaster temporarily unavailable; please retry in 10 minutes or top up your own ETH and submit directly." Donor's USDC is unchanged.

### Donor selects `escrow-refund`
This is a return of a previously-escrowed amount (e.g., a Public Fund grant that did not vest, returned by the grantee). Tithe does NOT apply to refunds — TitheRouter routes 100% to the original source. ADR-2605192115 §3.4.

### Reversal / cancellation
Donations are **not reversible**. The religious framing: 帰依 is not a transaction-with-return-policy. If a donor wishes to receive support, they may file a Public Fund grant proposal — a separate flow, not a donation reversal.

## 5. What this walkthrough does NOT cover (yet)

- **Recurring donations** — not yet supported; donor may give again at any time, but the system never auto-debits. Subscription-shaped flows are prohibited per ADR-2605192115 §1.3.
- **In-kind donations (land)** — covered by ADR-2605192245 LandRegistry flow; separate doc (`90-docs/2605220xxx-first-land-donation-walkthrough.md`, not yet written).
- **Donations via sister-corps** — covered by `FORK-BOOTSTRAP.md`; sister-corps run their own TitheRouter and Public Fund.
- **Donations during chaos rehearsal** — covered by `90-docs/2605220240-chaos-engineering-charter.md` Scenario 8; rehearsals on testnet only.
- **Anonymous donations** — possible via did:key with no published DID document, but the donor forfeits SBT mint and Public Fund vote eligibility. This is a feature, not a bug — anonymity has its own dignity (ADR-2605181100 confidentiality framing).

## 6. Religious framing — the act IS the metabolism

The organism does not have a "fundraising flow." 産霊 cycles value through whatever pathways it has, and a donation is the simplest substrate-level expression of that cycle. The 10% Public Fund split is the **automatic external-facing thanksgiving** — every donor is also, by virtue of giving, a contributor to multi-generational stewardship. There is no opt-in to the tithe; there is no checkbox to skip it.

The donor's experience is **liturgical**, not transactional:

- Sign with DID = profession of identity-as-religious-actor
- Submit with USDC = profession of substance (the value the donor has)
- Atomic split = automatic 帰依 to multi-generational priority (子・孫)
- SBT mint = recognition by the organism (no ranking, no tier — every adherent is one vote)

## 7. References

- **Constitutional**: ADR-2605192100 (Mission Charter §1.3 — donation-only flow; §1.6 — middleman elimination)
- **Tithe spec**: ADR-2605192115 (donation/kisha/grant/tithe/escrow-refund enum), ADR-2605192130 (Public Fund + 10% split)
- **Contracts**: `50-infra/etzhayyim-tithe-router/`, `50-infra/etzhayyim-public-fund/`, `50-infra/etzhayyim-paymaster/`
- **Substrate**: `90-docs/2605220210-substrate-symbiosis-map.md` (Base L2 ↔ Smart Account ↔ TitheRouter ↔ Public Fund pairs)
- **Resilience**: `90-docs/2605220240-chaos-engineering-charter.md` Scenario 8 (TitheRouter malfunction)
- **Confidentiality**: ADR-2605181100 (encrypted donation notes)
- **Sister-corp variant**: `FORK-BOOTSTRAP.md`
- **Loop framing**: `README.md § As Artificial Organism Ecosystem` (Axis 2 Metabolism — currently 5/10, gated)

## 8. Deployment gate

This walkthrough becomes **executable** when:

1. ✅ Solidity scaffolds exist (TitheRouter, PublicFund, Paymaster — `50-infra/etzhayyim-*` per `README.md § Status` row 12).
2. ⏳ Bootstrap Council Seats 2-5 confirmed (per `COUNCIL-BOOTSTRAP-RFP.md`, closes 2026-06-19).
3. ⏳ Base Sepolia testnet deploy with funded private key + RPC (`README.md § Status` row 19).
4. ⏳ End-to-end testnet run completes (rehearsal-grade, not yet production).
5. ⏳ Mainnet deploy + Council multisig key generation (`README.md § Status` row 20).

Until then, this doc is **the liturgy without the substrate** — readable, planning-ready, but not invocable.
