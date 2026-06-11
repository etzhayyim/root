# warifu-contracts — Deployment

ADR-2605302000. Apache-2.0 + Charter Rider v2.0.

## Deploy targets & constitutional gates

| Target | Status | Gate |
|---|---|---|
| **Local (Anvil)** | ✅ available now | none — localhost, reversible |
| **Base Sepolia (testnet)** | ⏳ gated | post-Council (Bootstrap Council Seats RFP closes 2026-06-19) per repo CLAUDE.md; needs a funded deployer that is a **member/Council Safe**, never a platform key (ADR-2605231525) |
| **Base mainnet** | ⛔ blocked | post-testnet **and** post-Council (CLAUDE.md "Live governance") |

`MockUSDC` is deployed **only** on local. Real networks pass the canonical USDC:
- Base mainnet USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Base Sepolia USDC: `0x036CbD53842c5426634e7929541eC2318f3dCF7e`

On real networks `Council` = the Lv6+/Lv7+ Safe and `wakaiFloat` = the wakai mutual-aid pool
address — **not** the deployer EOA used locally.

## Local deploy (verified)

```sh
anvil --silent &                     # localhost:8545
forge script script/DeployLocal.s.sol:DeployLocal \
  --rpc-url http://127.0.0.1:8545 --broadcast \
  --private-key <anvil acct0 key>    # PUBLIC dev key only; never a religious-corp key
```

Deploys + wires `MockUSDC → CreditLine → SettlementRouter` and `WarifuCard`, sets the router on
the credit line, authorizes the issuer, and `require()`s every invariant (fee 0 / interest 0 /
late-fee 0 / soulbound / phase2 default-closed) — the deploy reverts if any is violated.

### Local smoke result (last run)

| Check | Result |
|---|---|
| `MERCHANT_FEE_BPS` / `INTEREST_BPS` / `phase2Enabled` | `0` / `0` / `false` ✅ |
| `card.locked(1)` (soulbound) | `true` ✅ |
| issue → `smartAccountOf(1)` | bound to holder ✅ |
| debit settle 300000 (`internal-purchase`) | holder 700000 / merchant 300000, **fee 0** ✅ |
| external `purchase` (phase2 off) | reverts `PurposeGated()` (`0x9aa1d409`) ✅ |

## Testnet deploy (when ungated)

A `DeployBaseSepolia.s.sol` reads `COUNCIL`, `WAKAI_FLOAT`, and the canonical `USDC` from env,
deploys with `--verify`, and records addresses in `deps.toml`. Requires: Council ratification,
a funded Council Safe deployer, and a Base Sepolia RPC. Not executed (gated).
