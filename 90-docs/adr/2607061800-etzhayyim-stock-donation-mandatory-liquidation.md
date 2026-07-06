---
id: adr-2607061800-etzhayyim-stock-donation-mandatory-liquidation
title: "ADR-2607061800: Donated Securities (Stock/Equity) — Attestation + Mandatory Prompt Liquidation, No Speculative Holding"
status: proposed
doc_type: adr
topic: stock-donation-mandatory-liquidation
authoritative: true
last_verified: 2026-07-06
priority: 5.0
axis: economics
weight: 0.50
priority_note: "Closes the one complete gap in etzhayyim's 3 named donation-asset classes (land/cash/stock, owner directive 2026-07-06): land already has a mature (if untested) LandRegistry NFT pathway; cash already flows through TitheRouter/USDC; stock/equity donation had zero prior design (no contract, no Lexicon, no ledger category)."
authoritative_for:
  - com.etzhayyim.give.stock.donation Lexicon
  - toritate ledgerEntry category securities-donation-liquidation-proceeds
  - the heldAsEquityPosition=false structural invariant for donated securities
depends_on:
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
related:
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605301020-basic-high-income-imputed-and-commons-asset-doctrine
supersedes: []
superseded_by: []
---

# ADR-2607061800: Donated Securities (Stock/Equity) — Attestation + Mandatory Prompt Liquidation, No Speculative Holding

**Status**: proposed
**Date**: 2026-07-06
**Deciders**: Jun Kawasaki

# Context

etzhayyim names three donation-asset classes it wants to receive "tokenized": land, cash,
and stock. Two already have a designed, working (if incompletely tested) pathway:

- **Land** — `LandRegistry.sol::donate()` mints a soulbound ERC-721/5192 NFT directly
  (ADR-2605192245). Mature contract; presently has **zero Foundry test coverage**
  (a separate, already-flagged follow-up — not this ADR's scope).
- **Cash** — `TitheRouter.sol::route()` + `Etzhayyim.pay()` already tokenize every cash
  donation as USDC on Base L2, 90/10 auto-split (ADR-2605192130).

**Stock/equity had no design at all.** An exhaustive repo search found no contract, no
Lexicon, no ADR, and no `ledgerEntry` category referencing donated securities, DTC
transfer, brokerage, or appreciated-stock gifts — this is a genuine greenfield gap, not a
deferred or rejected idea.

The standard non-profit mechanism for this is well-established: a donor transfers
publicly-traded shares via DTC (or an equivalent transfer-agent process for
non-DTC-eligible securities) into the charity's brokerage account; the charity liquidates
promptly (avoiding market-timing risk and speculative exposure) and uses the cash
proceeds; the donor substantiates a tax deduction at fair market value on the date of
transfer (US IRS Form 8283 is the reference model, though this Lexicon is
jurisdiction-agnostic in shape).

The open design question was **whether to hold donated equity as an on-chain-wrapped
asset** (mint a token representing the shares) **or route it through the existing USDC
rail after liquidation**. This ADR decides the latter.

# Decision

## 1. No new tokenized-equity asset class

Donated securities are **never** represented as a held, custodied, or tradable on-chain
token. `com.etzhayyim.give.stock.donation` (new Lexicon,
`00-contracts/lexicons/com/etzhayyim/give/stock/donation.json`) records:

- `donorDid`, `securityIdentifier` + `securityIdentifierScheme` (ticker/CUSIP/ISIN),
  `shareQuantity`;
- `fairMarketValueUsdMicros` + `valuationDateUtc` (donor tax-substantiation figure — the
  average of the high/low trading price on the transfer date, the standard method);
- `brokerageTransferConfirmationCid` (the DTC/transfer-agent confirmation, encrypted per
  ADR-2605181100 if it carries donor account details);
- `heldAsEquityPosition: const false` — **structural invariant, not a caller input**,
  mirroring the same Charter Rider §2(b) discipline already enforced on wakai's mutual-aid
  pool (`poolAssetClass: "usdc-stable-only"`) and toritate's ledger (`nativeAsset` capped
  to `{usdc, eth, n-a}`, no fiat/no speculative asset).

This is the **land/cash asymmetry, deliberately preserved**: land is a constitutionally
inalienable commons asset (ADR-2605192245 §1.11, Earth as Tree of Life body) — hence a
bespoke soulbound NFT that can never transfer. A donated security is not a commons asset
etzhayyim intends to steward in kind; it is **mission-fungible working capital** the donor
happens to hold in equity form. Minting a wrapped-equity token would be the wrong analogy
(and would additionally require broker-dealer/transfer-agent integration and securities-law
review entirely out of scope for this substrate).

## 2. Liquidation proceeds re-enter the existing USDC rail

Once the brokerage sells the position, proceeds arrive as fiat/USDC through the ordinary
non-custodial on-ramp (ADR-2606111800 §B) and are recorded as a
`com.etzhayyim.give.usdc.donation` record, cross-linked from the original stock-donation
record via `liquidationDonationRef` (and `liquidationProceedsUsdMicros` +
`liquidatedAtUtc` on the stock-donation record itself). **No new payment rail, no new
smart contract** — the 90/10 TitheRouter split applies identically to liquidated-security
proceeds as to any other cash gift.

## 3. toritate accounts the proceeds under a new ledger category

`ledgerEntry.category` gains one new value: `securities-donation-liquidation-proceeds`
(alongside the existing `donation-income` / `land-trust-acquisition` / `asset-acquisition`
etc.). `20-actors/toritate/methods/imputed_income.cljc`'s `ledger-categories` set and its
own drift-guard test (`test_imputed_income.cljc`) are updated in lock-step — this repo's
now-established pattern (matsurigoto/wakai/kazaori) of cross-checking a module's
hardcoded enum against the Lexicon's own `knownValues` so the two cannot silently drift.

## 4. New pure-function reference-impl: `toritate.methods.securities-donation`

Following the R0 reference-impl pattern used throughout this session (matsurigoto's 5
egov modules, wakai's pool engine, toritate's own imputed-income engine, kazaori's
emergency engine): `validate-securities-donation` constructs + validates the donation
attestation (rejects an attempt to set `heldAsEquityPosition` true, rejects an unknown
`securityIdentifierScheme`, requires a positive `shareQuantity`/`fairMarketValueUsdMicros`);
`record-liquidation` constructs + validates the liquidation cross-link (rejects
`liquidationProceedsUsdMicros` before `liquidatedAtUtc` is set). `solve()` raises — this is
validation + record construction only; no real brokerage integration, no real fund
movement. **This ADR does not open a real brokerage account, does not solicit any real
donor, and does not move any real security or dollar** — it designs the on-chain/Lexicon
recording layer for a real-world transfer the Council/founder would execute through an
actual brokerage relationship, exactly as `LandRegistry.donate()` records a real-world
deed transfer that already happened off-chain.

# Consequences

**Positive**:
- Closes the one complete gap among the three named donation-asset classes.
- Consistent with the repo's own established no-speculation discipline (Charter Rider
  §2(b)) — donated equity cannot become a shadow investment vehicle even by omission.
- Donor fair-market-value substantiation is durably, content-addressably recorded from
  day one, without waiting for a live brokerage integration.

**Negative / risks**:
- **No live brokerage integration exists.** This ADR is Lexicon + pure-function
  reference-impl only; an actual DTC-eligible receiving account, its custodian
  relationship, and the liquidation instruction workflow are Council+operator
  work outside this ADR's scope (same R0→R1 boundary as every other actor).
- Valuation-date methodology (`fairMarketValueUsdMicros`) is donor/Council-attested, not
  independently priced by this substrate — a future jurisdiction-specific pricing-oracle
  cross-check is a reasonable R1+ enhancement, not required at R0.

# Alternatives Considered

## A. Mint a wrapped-equity token representing the donated shares

Rejected: requires custody of real securities inside a smart contract (broker-dealer /
transfer-agent / securities-law integration far beyond this substrate's scope), and
conflicts with the no-speculative-holding doctrine already enforced elsewhere — holding a
wrapped equity position is economically identical to holding the equity position.

## B. Route donated stock through the land-donation NFT pattern (a bespoke non-transferable token)

Rejected: land is inalienable *by mission* (Earth as commons, ADR-2605192245 §1.11); a
donated security is ordinary working capital with no such doctrinal reason to be held
rather than spent. Forcing the land pattern onto stock would be doctrine-shopping, not
principled reuse.

## C. Do nothing — treat stock donations as out-of-scope indefinitely

Rejected: appreciated-securities gifts are one of the two most common non-cash
charitable-giving vehicles (alongside real estate, which land.donation already covers);
leaving zero design here is a real, easily-closed gap given the existing land-donation
attestation pattern to mirror.

# References

- ADR-2605192245 (Global Land Sovereignty — the attestation-record pattern this Lexicon
  mirrors, and the doctrinal contrast that motivates NOT tokenizing equity the same way)
- ADR-2605192115 (Non-profit / donation-only / no-ads)
- ADR-2605192130 (TitheRouter 10% auto-split — the rail liquidation proceeds re-enter)
- ADR-2605262900 (toritate accounting/audit — the new ledger category)
- ADR-2606111800 (Donation media expansion — the non-custodial fiat on-ramp liquidation
  proceeds use)
- ADR-2605301020 (Basic High Income — the sibling Charter Rider §2(b) no-speculation
  discipline this ADR extends to donated securities)
- `00-contracts/lexicons/com/etzhayyim/give/land/donation.json` (the structural analog)
- `00-contracts/lexicons/com/etzhayyim/give/stock/donation.json` (this ADR's artifact)
