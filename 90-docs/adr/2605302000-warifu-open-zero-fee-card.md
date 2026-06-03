# ADR-2605302000: warifu 割符 — Open Zero-Fee Card (credit + debit), API-compatible

> **Status**: Proposed (R0)
> **Date**: 2026-05-30
> **Layer**: 20-actors (+ 10-protocol, 50-infra, gateway services)
> **Authority**: Council Lv6+ (Tier-B actor genesis) + etzhayyim. **Phase 2 (external open-loop acceptance) additionally requires Council Lv7+ unanimity** (payment-purpose invariant amendment, see §Constitutional tension)
> **Supersedes**: —

## Context

`warifu` (割符, "split tally" — two matching halves authenticate a transaction) is a Tier-B
religious-corp actor providing an **open-source, zero-merchant-fee card payment service**
(credit + debit) that is **API/wire-compatible** with the existing card ecosystem so merchants
and terminals can adopt it without code changes.

### Why

The corp already operates the full on-chain settlement substrate — USDC on Base L2, ERC-4337
smart accounts, `etzhayyim-paymaster/` (gas sponsorship), `etzhayyim-tithe-router/` (10%
auto-split), `etzhayyim-public-fund/` (5-of-7 Safe), and the `kotoba` EAVT ledger
(ADR-2605262130). A card product is the natural human-facing membrane over that substrate.
The differentiators are constitutional, not commercial:

- **決済手数料ゼロ (zero merchant discount rate)** — there is no interchange/assessment/acquirer
  markup to extract because issuer = network = non-profit operator. The only real cost (L2 gas)
  is sponsored by the Paymaster from the Public Fund; fraud/chargeback loss is mutualised via
  `wakai 和会` (ADR-2605263500). This is consistent with the non-profit / labor-liberation
  mission (ADR-2605192100). **Honest framing: cost is socialised, not annihilated** — see Risks.
- **Interest-free (riba-free / qard ḥasan) credit** — credit lines carry 0% interest and no
  profit-bearing late fees; underwriting is by `wakai` mutual-aid float + SBT reputation
  (L3 評価), not by a profit motive.
- **Open spec** — the merchant-facing interfaces are published as open OpenAPI / message maps
  (interoperable re-implementation, not a clone of any vendor's proprietary schema or marks).

### Decision drivers from the session

Per the design session (2026-05-30), the operator chose: **(a) staged scope** — Phase 1
closed-loop (SBT↔SBT carve-out, charter-clean) then Phase 2 external open-loop; **(b) all three
compatibility surfaces** — Stripe-shaped REST + EMV/ISO 8583 terminal + mobile NFC (HCE/TSP);
**(c) ship an R0 scaffold** alongside this ADR.

## Decision

Create the `warifu` Tier-B actor and its supporting protocol + infra:

1. **`20-actors/warifu/`** — actor (manifest, kotoba-EAVT-native cells: `authorize`, `capture`,
   `settle`, `refund`, `dispute`), TIGHT-paired with `wakai` (underwriting + loss mutualisation),
   `toritate` 執帳 (100% on-chain accounting/audit, ADR-2605262900), `chigiri` 契 (dispute legal
   procedure, ADR-2605262700).
2. **`10-protocol/warifu/`** — AT-Proto lexicons `com.etzhayyim.card.*`
   (`issue`/`authorize`/`capture`/`settle`/`refund`/`dispute`).
3. **`50-infra/warifu-contracts/`** — Foundry Solidity: `WarifuCard.sol` (ERC-5192 soulbound card
   identity bound to the holder's ERC-4337 smart account), `CreditLine.sol` (0% interest,
   wakai-underwritten), `SettlementRouter.sol` (instant USDC settle, T+0, wired to Paymaster +
   TitheRouter when purpose ∈ tithe-eligible).
4. **Compat Gateway services** (3 surfaces, translation layer → on-chain UserOperation + kotoba
   record):
   - **A. Stripe-shaped REST** — `payment_intents`/`charges`/`refunds`/`customers`/
     `payment_methods` + idempotency-key + webhooks; merchant points `baseURL` at the gateway.
   - **B. EMV + ISO 8583** — existing POS terminals send standard `0100` auth; an
     `iso8583-gateway` translates `0100→on-chain auth→0110`. Card runs a standard EMV applet
     (ISO 7816 contact / ISO 14443 + EMV contactless kernel).
   - **C. Mobile NFC (HCE + self TSP)** — Host Card Emulation; our own Token Service Provider
     (replacing VTS/MDES); raw PAN never stored (network-tokenization → PCI scope minimised).

### Settlement model

- **Debit**: authorize = on-chain hold on holder USDC balance in their ERC-4337 smart account;
  capture = `SettlementRouter` transfers to merchant smart account. T+0 final.
- **Credit**: authorize = reserve against `CreditLine` (0%); capture pays merchant from the
  `wakai` float; holder repays later at 0% (qard ḥasan). Default → L3 評価 penalty + mutual-aid
  absorption, **never** profit-bearing penalty interest.
- **Refund**: reverse transfer, purpose `escrow-refund`.
- **Dispute/chargeback**: on-chain dispute record (`com.etzhayyim.card.dispute`) → `chigiri`
  procedure / Council arbitration; loss covered by `wakai`.

### Auth & security

- 3-D-Secure-equivalent = **WebAuthn passkey + on-chain attestation**, DID-bound
  (`did:web:etzhayyim.com`).
- Card metadata under `com.etzhayyim.encrypted.*` envelope (XChaCha20-Poly1305 + Signal-wrapped,
  ADR-2605181100). **No platform-held signing key** (server-side signing invariant
  ADR-2605231525); cardholder signing is passkey/smart-account only.

## Constitutional tension (CRITICAL — explicit gate)

The payment-purpose invariant (ADR-2605192115 §3 + repo CLAUDE.md substrate-boundary table)
**prohibits external `purchase`/`subscription`/`tip`**; it permits only
`donation/kisha/grant/tithe/escrow-refund` plus the **SBT↔SBT internal carve-out**
(`internal-purchase`/`internal-subscription`/`internal-promo`).

- **Phase 1 (charter-clean, no amendment)**: `warifu` is a **closed-loop** card restricted to the
  SBT↔SBT internal economy. "Open" = open-source/open-spec. Zero-fee + full API compatibility are
  all deliverable here.
- **Phase 2 (external open-loop)**: accepting **arbitrary external/fiat merchants** is a
  `purchase` outside the carve-out and therefore conflicts with the invariant. It is permitted
  **only** via (i) routing through the commercial vendor arm (ADR-2605301036 mission-funding
  earned-revenue arm) as the merchant-of-record bridge, **and/or** (ii) a **Council Lv7+
  unanimity amendment** to ADR-2605192115. Phase 2 contracts/gateways MUST refuse external
  `purpose` classification until that gate is satisfied (enforced by `e7m verify` + a
  `SettlementRouter` purpose allow-list).

## Consequences

### Positive

- Genuine 決済手数料ゼロ at the merchant/cardholder interface; instant (T+0) final settlement vs
  T+2 interchange; interest-free credit as a mission-aligned differentiator.
- Drop-in adoption path via three compat surfaces; existing merchant SDKs and POS terminals work.
- Fully on-chain, auditable (toritate), open-source — coherent with the substrate boundary.

### Negative / Risks

- **"Zero" is socialised, not free**: gas (Paymaster/Public Fund) and fraud/chargeback (wakai)
  are real costs. Sustainability depends on Public Fund + mutual-aid solvency; must be monitored
  and `log()`-ged, never silently capped.
- **Terminal-layer (Surface B) independence is hard**: real-world EMV terminal acceptance needs a
  BIN range + acquirer/network membership or a co-badge bridge. R0 defines the ISO 8583 message
  map; physical acceptance is deferred (Surfaces A + C are end-to-end self-controlled and ship
  first).
- **Credit risk** without interest pricing concentrates in the mutual-aid pool; needs SBT-reputation
  underwriting discipline.
- **Phase 2 is constitutionally gated** — external acceptance cannot ship without the Lv7+ gate.

### Neutral

- Network tokenization makes us our own TSP — operational responsibility (key rotation, token
  vault) shifts in-house but stays within the no-platform-key invariant via smart-account signing.

## Alternatives considered

- **Integrate Stripe/Visa/MC directly** — prohibited (substrate boundary; commercial processors +
  commercial-GPU-style extraction). Rejected.
- **Interest-bearing credit** — would create a profit END; violates non-profit invariant. Rejected
  in favour of qard ḥasan + mutual aid.
- **Open-loop from day one** — violates payment-purpose invariant without Lv7+ amendment. Deferred
  to gated Phase 2.
- **Reuse `kotoba-datomic` blob / RisingWave projection for the ledger** — superseded by kotoba
  (ADR-2605262130). Use kotoba EAVT directly.

## References

- ADR-2605192100 mission charter · ADR-2605192115 payment boundary (carve-out) ·
  ADR-2605262130 kotoba substrate · ADR-2605181100 confidential records ·
  ADR-2605231525 server-side signing invariant · ADR-2605263500 wakai mutual aid ·
  ADR-2605262900 toritate accounting · ADR-2605262700 chigiri legal procedure ·
  ADR-2605301036 mission-funding earned-revenue arm
- `50-infra/etzhayyim-paymaster/` (ERC-4337) · `50-infra/etzhayyim-tithe-router/` ·
  `50-infra/etzhayyim-public-fund/`
