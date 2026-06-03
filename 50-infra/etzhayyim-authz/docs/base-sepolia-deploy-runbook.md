# Base Sepolia Deploy Runbook — EtzhayyimAuthz (Phase α P1)

**Status**: ready for execution
**Prereqs**: funded Base Sepolia private key (≈ 0.005 ETH) + BASESCAN_KEY env var + Council 5-of-7 Safe address on Base Sepolia
**Related**: ADR-2605212030 (Phase α deploy target), ADR-2605211950 (substrate axis)

## Smoke-tested locally

The Phase α P0 contract has been smoke-tested against a local Anvil (chain id 31337) on 2026-05-21:

| Step | Verified result |
|---|---|
| `forge build` | passes (Solidity 0.8.27 + via_ir + optimizer 1M) |
| `forge test` | 17/17 passing |
| `runLocal()` deploy | `EtzhayyimAuthz` deployed at deterministic address (Anvil first-tx slot) |
| Owner read | matches Anvil acct #0 |
| `provisionRoot(dwebHandleHash, activeKey)` | tx success, RootProvisioned event emitted |
| `resolveDwebHandle(dwebHandleHash)` | returns matching rootId + Root struct with `active = true` |

## Pre-flight (one-time)

1. **Fund a deployer key on Base Sepolia.** Faucets:
   - https://www.alchemy.com/faucets/base-sepolia
   - https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet

   Need ≈ 0.005 testnet ETH for deploy + first few txs.

2. **Deploy or identify the Council 5-of-7 Safe on Base Sepolia.** If a testnet Safe does not exist:
   ```bash
   # Use https://app.safe.global/new-safe/create — select "Base Sepolia"
   # Configure 5-of-7 signers from Council bootstrap roster (COUNCIL.md)
   # Record the address as COUNCIL_SAFE_SEPOLIA
   ```

3. **Export env vars** (`~/.etzhayyim/etzhayyim-authz.env`, `chmod 600`):
   ```bash
   export DEPLOYER_PRIVATE_KEY=0x...                       # funded Base Sepolia key
   export COUNCIL_SAFE_SEPOLIA=0x...                       # 5-of-7 Safe address
   export BASESCAN_KEY=...                                  # Basescan API for verification
   export BASE_SEPOLIA_RPC=https://sepolia.base.org         # default; override if needed
   ```

   Load: `set -a; source ~/.etzhayyim/etzhayyim-authz.env; set +a`.

## Deploy

From `50-infra/etzhayyim-authz/contracts/`:

```bash
forge script script/Deploy.s.sol:Deploy \
  --sig "run(address)" "$COUNCIL_SAFE_SEPOLIA" \
  --rpc-url "$BASE_SEPOLIA_RPC" \
  --private-key "$DEPLOYER_PRIVATE_KEY" \
  --broadcast \
  --verify \
  --etherscan-api-key "$BASESCAN_KEY"
```

The `console.log` output reports:
```
EtzhayyimAuthz deployed at: 0x...
owner (Council Safe): 0x...
```

Record both. Save the deployment artifact:
```bash
cp broadcast/Deploy.s.sol/84532/run-latest.json \
   ~/.etzhayyim/etzhayyim-authz/deploy-base-sepolia-$(date +%Y%m%d-%H%M).json
```

## Post-deploy smoke

```bash
AUTHZ=<deployed address>

cast call "$AUTHZ" "owner()(address)" --rpc-url "$BASE_SEPOLIA_RPC"
# Expect: $COUNCIL_SAFE_SEPOLIA
```

(Functional smoke beyond `owner()` requires a tx signed by the Council Safe — see Council SOP.)

## Update the SSoT pointers

After deploy succeeds and the address is recorded:

1. `deps.toml` — add the Base Sepolia EtzhayyimAuthz address under `[platform.etzhayyim.contracts.base_sepolia]`.
2. `50-infra/etzhayyim-authz/README.md` — append the testnet deploy record (block, address, tx hash).
3. The CF Worker config (`50-infra/etzhayyim-authz/wrangler.toml`, future) reads the address from a `var` block.

## Rollback

If the deploy lands but the contract is later determined to be misbehaving:

- The contract has **no upgrade path** by design. Deactivation of individual roots is supported via `deactivateRoot(rootId)`, callable only by the Council Safe.
- To "rollback" the registry as a whole, deploy a new EtzhayyimAuthz contract and update the SSoT pointers. Old roots remain readable on-chain forever; downstream services migrate by reading the new address.

## Base mainnet (Phase α P2+)

The same `forge script` invocation with `--rpc-url base` (not `base_sepolia`) and a mainnet-funded key. Mainnet deploy is **gated** on:

- ≥ 1 month of Base Sepolia operation with no incidents.
- Council Safe on Base mainnet provisioned (5-of-7 from active Council roster).
- ADR-2605212030 reviewed and acknowledged by Council.
- Vendor migration debt (ADR-2605211950 Item 1 cutover plan) on track.

Do not deploy to mainnet before these gates.
