# etzhayyim-tithe-router

> **NOTE (2026-05-20)**: `TitheRouter.sol` was moved to
> [`../etzhayyim-chain-contracts/src/TitheRouter.sol`](../etzhayyim-chain-contracts/src/TitheRouter.sol)
> for unified Foundry project / deploy script integration. Build / test /
> deploy live there. This directory retained as design reference + future
> SDK-binding home.

`TitheRouter.sol` — donation 受領時に **10% を Public Fund Safe へ atomic split**.

**Per [ADR-2605192130](../../90-docs/adr/2605192130-etzhayyim-tithe-redistribution.md)** (10% Tithe Redistribution).

## Constitutional constant

`economic.tithe_to_public_fund_bps = 1000` (= 10.00%, ADR-2605192100 §2 — never amendable).

## Flow

```
[donor]
  → e.pay({ to: recipient, amount: 100 USDC, purpose: "donation" })
  → SDK: usdc.approve(TitheRouter, 100 USDC)
  → SDK: TitheRouter.route(recipient, 100 USDC, keccak256("donation"))
        ├─ usdc.transferFrom(donor, publicFund, 10 USDC)
        └─ usdc.transferFrom(donor, recipient, 90 USDC)
  → SDK: MST: emit com.etzhayyim.apps.payment.sent + com.etzhayyim.apps.payment.tithe records
```

## v0 deploy quirk

The Public Fund Safe address is passed as a TitheRouter constructor immutable in v0 (rather than read from `Constitution.getMutable("public_fund.safe_address")`) to resolve a deploy-time circular dependency. The Constitution still stores the address as a mutable for downstream reads; v1 will switch TitheRouter to the Constitution lookup once CREATE2-based sequencing wires the address before construction.

## Exceptions (NOT titheable)

The Solidity `_isTitheablePurpose()` accepts only `keccak256("donation")`. All other purposes — `kisha` / `tithe` / `escrow-refund` / `grant` / `internal-purchase` / `internal-subscription` / `internal-promo` — are explicitly rejected. SDK never calls `route()` for them.

## Charter Compliance gate (per [ADR-2605192230](../../90-docs/adr/2605192230-etzhayyim-three-tier-enforcement-implementation.md))

`route()` reverts if:
- `charters.isNonAlignedAddress(msg.sender)` (Non-Aligned payer)
- `charters.isNonAlignedAddress(recipient)` (Non-Aligned recipient)

A Non-Aligned address cannot pay through nor receive through TitheRouter.

## Build + Test + Deploy

All under [`../etzhayyim-chain-contracts/`](../etzhayyim-chain-contracts/):

```bash
cd ../etzhayyim-chain-contracts
forge build   # includes TitheRouter
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "runLocal()" --rpc-url http://localhost:8545 --broadcast --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

## Pregel cell

[`40-engine/kotoba/crates/kotoba-kotodama/cells/tithe_routing/`](../../40-engine/kotoba/crates/kotoba-kotodama/cells/tithe_routing/) — MST listener on `com.etzhayyim.apps.payment.sent` records, validates `route()` was invoked correctly + alerts on SDK bypass.

## Lexicon

[`00-contracts/lexicons/com/etzhayyim/apps/payment/tithe.json`](../../00-contracts/lexicons/com/etzhayyim/apps/payment/tithe.json) — counterpart record emitted alongside payment.sent.
