# EtzhayyimPaymaster Deployment Checklist

This document captures the mandatory post-deploy operations for the ERC-4337 Paymaster contract on Base L2 (mainnet and Sepolia).

## Pre-Deploy Requirements

- [ ] `BASE_SEPOLIA_RPC` / `BASE_MAINNET_RPC` endpoints configured
- [ ] `DEPLOYER_PRIVATE_KEY` — deployer EOA (not the owner Safe)
- [ ] `PAYMASTER_OWNER` — 2-of-3 Safe address (set as contract `owner`)
- [ ] `PAYMASTER_VERIFYING_SIGNER` — off-chain operator ECDSA key address
- [ ] `ALLOWED_FACTORY` (optional) — Smart Account factory to pre-seed
- [ ] `BASESCAN_API_KEY` for contract verification

## Deploy Commands

### Testnet (Base Sepolia)

```bash
forge install
forge build
forge test -vv

forge script script/Deploy.s.sol:Deploy \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_API_KEY
```

### Mainnet (Base)

```bash
forge script script/Deploy.s.sol:Deploy \
  --rpc-url $BASE_MAINNET_RPC \
  --broadcast --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_API_KEY
```

## ⚠️ MANDATORY Post-Deploy Steps (Issue #1523)

**The paymaster MUST have stake deposited before it can reliably sponsor UserOperations.** Without stake, the EntryPoint will throttle the paymaster after a small number of validation failures (opsPerTime limit per ERC-4337 §6.2).

### 1. Fund Paymaster Deposit (Gas Balance)

```bash
# Send ETH to paymaster (auto-forwarded to EntryPoint via receive())
cast send $PAYMASTER \
  --value 0.5ether \
  --rpc-url $BASE_MAINNET_RPC \
  --private-key $DEPLOYER_PRIVATE_KEY

# Verify deposit
cast call $PAYMASTER "getDeposit()(uint256)" --rpc-url $BASE_MAINNET_RPC
```

**Target:** ≥ 0.5 ETH (≈7-day runway at expected volume). Top up when `< 0.1 ETH`.

### 2. Add Stake (CRITICAL — Prevents Throttling)

```bash
# Add 0.1 ETH stake with 1-day unstake delay (86400 seconds)
cast send $PAYMASTER "addStake(uint32)" 86400 \
  --value 0.1ether \
  --rpc-url $BASE_MAINNET_RPC \
  --private-key $OWNER_SAFE_PRIVATE_KEY

# Verify stake is locked
cast call $PAYMASTER "hasStake()(bool)" --rpc-url $BASE_MAINNET_RPC
# Should return: true

# Full stake status
cast call $PAYMASTER "getStakeStatus()(bool,uint112,uint32,uint48)" --rpc-url $BASE_MAINNET_RPC
# Returns: (staked, stake, unstakeDelaySec, withdrawTime)
```

**Minimum stake:** 0.1 ETH (EntryPoint default minimum). Recommended: 0.5–1 ETH for production.

### 3. Configure Allowlist

```bash
# Add allowed target contracts (USDC, Splits, Escrow, Anchor, etc.)
cast send $PAYMASTER "setAllowedTarget(address,bool)" $USDC_ADDRESS true \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY

cast send $PAYMASTER "setAllowedTarget(address,bool)" $SPLITS_ADDRESS true \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY

# Verify
cast call $PAYMASTER "allowedTarget(address)" $USDC_ADDRESS --rpc-url $BASE_MAINNET_RPC
```

### 4. Update SDK Config

Update `deps.toml` `[platform.operating_entity].paymaster_contract` with the deployed address.

## Monitoring & Alerts (Required per #1523)

### On-Chain Checks (run via cron / monitoring daemon)

```bash
# 1. Stake health check — ALERT if false
cast call $PAYMASTER "hasStake()(bool)" --rpc-url $BASE_MAINNET_RPC

# 2. Deposit balance — ALERT if < 0.1 ETH
cast call $PAYMASTER "getDeposit()(uint256)" --rpc-url $BASE_MAINNET_RPC

# 3. Stake amount — ALERT if < 0.1 ETH
cast call $PAYMASTER "getStakeStatus()(bool,uint112,uint32,uint48)" --rpc-url $BASE_MAINNET_RPC
```

### Suggested Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| `hasStake()` | false | false |
| Deposit balance | < 0.2 ETH | < 0.1 ETH |
| Stake amount | < 0.2 ETH | < 0.1 ETH |
| Daily gas spend | > 80% of cap | > 95% of cap |

### Grafana / Prometheus (if available)

- Scrape `hasStake()` every 5 min → alert on `false`
- Scrape `getDeposit()` every 5 min → alert on `< 0.1 ether`
- Scrape `getStakeStatus()` every 5 min → alert on `stake < 0.1 ether`

## Unstaking (Emergency / Migration)

```bash
# 1. Unlock stake (starts 1-day cooldown)
cast send $PAYMASTER "unlockStake()" \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY

# 2. Wait 86400 seconds (1 day)

# 3. Withdraw stake
cast send $PAYMASTER "withdrawStake(address)" $WITHDRAW_ADDRESS \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY
```

## Verification Checklist (Post-Deploy)

- [ ] Contract verified on BaseScan
- [ ] `hasStake()` returns `true`
- [ ] `getDeposit()` ≥ 0.5 ETH
- [ ] Allowlist contains all required targets
- [ ] `deps.toml` updated with paymaster address
- [ ] Monitoring alerts configured (stake + deposit)
- [ ] Owner Safe signers confirmed
- [ ] Verifying signer key secured off-chain (HSM / 1Password)

## References

- [ERC-4337 Spec](https://eips.ethereum.org/EIPS/eip-4337) — §6.2 Paymaster Stake & Throttling
- [ADR-2605172100](../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md)
- Issue #1523 — Stake Unchecked (Low)