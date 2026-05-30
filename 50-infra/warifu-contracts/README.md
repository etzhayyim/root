# warifu-contracts (Foundry)

On-chain settlement contracts for the `warifu` 割符 Open Zero-Fee Card (ADR-2605302000).
Apache-2.0 + Charter Compliance Rider v2.0.

| Contract | Purpose |
|---|---|
| `WarifuCard.sol` | Soulbound card identity (ERC-5192) bound to a holder's ERC-4337 smart account. No `transfer`/`burn` of the binding by third parties. |
| `CreditLine.sol` | Interest-free (0% / qard ḥasan) credit line, underwritten by the `wakai` mutual-aid float + SBT reputation. **No interest, no profit-bearing late fee.** |
| `SettlementRouter.sol` | Instant (T+0) USDC settlement holder/wakai → merchant. **Merchant fee = 0.** Gas via `etzhayyim-paymaster` (ERC-4337). Enforces the payment-purpose allow-list (Phase 1 SBT↔SBT carve-out; external `purchase`/`subscription` gated on Council Lv7+). |

## Invariants (constitutional — do not weaken)

- `MERCHANT_FEE_BPS == 0`, `INTERCHANGE_BPS == 0` (決済手数料ゼロ).
- `INTEREST_BPS == 0` on `CreditLine` (riba-free).
- `SettlementRouter` purpose allow-list defaults to Phase 1; `enablePhase2()` is guarded by the
  Council Lv7+ multisig + requires the ADR-2605192115 amendment to be on-chain-recorded.
- No `transfer()`/`burn()`/`setOwner()` that lets a third party seize a cardholder binding.
- Settlement asset is USDC on Base L2 only (substrate boundary).

## Layout

```
50-infra/warifu-contracts/
├── foundry.toml
├── src/{WarifuCard,CreditLine,SettlementRouter}.sol
└── test/   (R1: forge tests — fee==0, interest==0, purpose-gate)
```

Wire to: `etzhayyim-paymaster/` (gas), `etzhayyim-tithe-router/` (10% split for tithe-eligible
purposes only), `etzhayyim-public-fund/` (gas/loss backstop).
