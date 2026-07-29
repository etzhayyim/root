# etzhayyim-paymaster

**ERC-4337 Paymaster contract on Base L2.** Sponsors gas for sender Smart Accounts whose user-ops match the configured policy (allowlisted target contract + per-sender daily cap). Per [ADR-2605172100](../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md).

Foundry Solidity project. Stub-quality v0.0.0; tested logic + deploy script + policy hooks but not yet deployed or independently audited.

## What it sponsors

The paymaster's policy is intentionally narrow:

- ✅ USDC `transfer(...)` to a whitelisted recipient set (etzhayyim app recipients, public-fund splits, etc.)
- ✅ Calls to specific app contracts on Base L2 (EtzhayyimAnchor, public-fund Splits, escrow Safes)
- ❌ Anything else (rejected at `validatePaymasterUserOp`)

**Verifying signature required (fix #1519 — Sybil drain).** Before any policy check,
`validatePaymasterUserOp` verifies a valid ECDSA signature (over the UserOp hash +
`validUntil`/`validAfter`) from the off-chain paymaster **operator key**
(`verifyingSigner`). Without it, *any* address could drain the deposit via allowlisted
targets. The off-chain signing service performs whatever pre-screening it likes, then signs;
the contract only attests *"the operator approved this op"*. The signature is the
`paymasterAndData` trailing bytes (see SDK integration below).

Per-sender daily gas allowance: 0.02 ETH (~$50 worth) by default. Configurable per sender. Prevents one user from draining the paymaster.

## Funding model

```
EtzhayyimAnchor.anchor() txs paid by anchor-cron signing account
                │
                └─ ~5% fee-skim → etzhayyim-paymaster.deposit() (off-chain cron)
                                  │
                                  └─ replenishes paymaster ETH balance

If paymaster.balance < 7d runway → alert (manual top-up from etzhayyim treasury Safe)
```

The skim mechanism is implemented off-chain by `anchor-cron` (next phase) — it watches the anchorer EOA's gas spend and forwards a fraction to the paymaster's `deposit()`. This keeps the anchor contract itself purely on-chain logic with no skim coupling.

## Admin surface

Per ADR-2605172100, the etzhayyim L2 contracts minimize admin functions. For the paymaster specifically:

- **Has owner** (intended to be a 2-of-3 Safe): `setAllowlist`, `setDailyLimit`, `setVerifyingSigner` (rotate the operator signing key), `withdraw`, `setOwner`
- **No pause**: policy is in code; if policy must change, deploy a new paymaster and update the SDK config
- **No proxy**: not upgradeable; replace contract instead of upgrading

This is a slight relaxation vs the anchor contract's pure-immutability, justified by the paymaster's economic exposure (it holds ETH and needs operational adjustment). The owner cannot reverse a sponsored tx or claw back gas — those are still EntryPoint-final.

## Layout

```
etzhayyim-paymaster/
├── README.md
├── foundry.toml
├── src/
│   └── EtzhayyimPaymaster.sol     # IPaymaster impl + policy logic
├── test/
│   └── EtzhayyimPaymaster.t.sol   # unit tests
├── script/
│   └── Deploy.s.sol
└── .gitignore
```

## Deployment

> **⚠️ CRITICAL: Post-deploy stake is mandatory** — without stake, the EntryPoint throttles the paymaster after validation failures (ERC-4337 §6.2). See the **Post-Deploy Checklist** below.

```bash
forge install
forge build
forge test -vv

# Testnet
forge script script/Deploy.s.sol:Deploy \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_KEY

# Mainnet (after testnet validation + initial Safe seed)
forge script script/Deploy.s.sol:Deploy \
  --rpc-url https://mainnet.base.org \
  --broadcast --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_KEY

# Deposit into EntryPoint after deploy (paymaster stake)
cast send $PAYMASTER addStake(uint32) 86400 \
  --value 0.1ether \
  --rpc-url https://mainnet.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY
```

### Post-Deploy Checklist (Mandatory — Issue #1523)

**The paymaster MUST have stake deposited before it can reliably sponsor UserOperations.** Without stake, the EntryPoint will throttle the paymaster after a small number of validation failures (opsPerTime limit per ERC-4337 §6.2).

#### 1. Fund Paymaster Deposit (Gas Balance)

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

#### 2. Add Stake (CRITICAL — Prevents Throttling)

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

#### 3. Configure Allowlist

```bash
# Add allowed target contracts (USDC, Splits, Escrow, Anchor, etc.)
cast send $PAYMASTER "setAllowedTarget(address,bool)" $USDC_ADDRESS true \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY

cast send $PAYMASTER "setAllowedTarget(address,bool)" $SPLITS_ADDRESS true \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY

# Verify
cast call $PAYMASTER "allowedTarget(address)" $USDC_ADDRESS --rpc-url $BASE_MAINNET_RPC
```

#### 4. Update SDK Config

Update `deps.toml` `[platform.operating_entity].paymaster_contract` with the deployed address.

### Monitoring & Alerts (Required per #1523)

#### On-Chain Checks (run via cron / monitoring daemon)

```bash
# 1. Stake health check — ALERT if false
cast call $PAYMASTER "hasStake()(bool)" --rpc-url $BASE_MAINNET_RPC

# 2. Deposit balance — ALERT if < 0.1 ETH
cast call $PAYMASTER "getDeposit()(uint256)" --rpc-url $BASE_MAINNET_RPC

# 3. Stake amount — ALERT if < 0.1 ETH
cast call $PAYMASTER "getStakeStatus()(bool,uint112,uint32,uint48)" --rpc-url $BASE_MAINNET_RPC
```

#### Suggested Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| `hasStake()` | false | false |
| Deposit balance | < 0.2 ETH | < 0.1 ETH |
| Stake amount | < 0.2 ETH | < 0.1 ETH |
| Daily gas spend | > 80% of cap | > 95% of cap |

#### Grafana / Prometheus (if available)

- Scrape `hasStake()` every 5 min → alert on `false`
- Scrape `getDeposit()` every 5 min → alert on `< 0.1 ether`
- Scrape `getStakeStatus()` every 5 min → alert on `stake < 0.1 ether`

### Unstaking (Emergency / Migration)

```bash
# 1. Unlock stake (starts 1-day cooldown)
cast send $PAYMASTER "unlockStake()" \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY

# 2. Wait 86400 seconds (1 day)

# 3. Withdraw stake
cast send $PAYMASTER "withdrawStake(address)" $WITHDRAW_ADDRESS \
  --rpc-url $BASE_MAINNET_RPC --private-key $OWNER_SAFE_PRIVATE_KEY
```

### Verification Checklist (Post-Deploy)

- [ ] Contract verified on BaseScan
- [ ] `hasStake()` returns `true`
- [ ] `getDeposit()` ≥ 0.5 ETH
- [ ] Allowlist contains all required targets
- [ ] `deps.toml` updated with paymaster address
- [ ] Monitoring alerts configured (stake + deposit)
- [ ] Owner Safe signers confirmed
- [ ] Verifying signer key secured off-chain (HSM / 1Password)

## Initial factory allowlist (deploy-time)

Set `ALLOWED_FACTORY` when deploying to pre-seed the factory allowed to create
smart accounts through `initCode`. Without it, deployment starts with an empty
factory allowlist and `initCode` operations are rejected until the owner calls
`setAllowedFactory`.

> **`PAYMASTER_VERIFYING_SIGNER`** (env, address) — the off-chain operator key the paymaster
> trusts to pre-approve sponsored UserOps. Its private key must stay off-chain (the contract
> only stores the address). If it ever leaks, the owner Safe calls `setVerifyingSigner(newKey)`
> to revoke it **without redeploying**.

## SDK integration

The `@etzhayyim/sdk` `pay()` method passes `paymaster: "sponsored"` by default. Internally:

1. Build ERC-4337 UserOperation for the USDC transfer.
2. Have the off-chain operator sign it: `paymasterAndData` =
   `paymaster_addr (20) ++ verificationGasLimit (16) ++ postOpGasLimit (16) ++
   validUntil (32) ++ validAfter (32) ++ operator_ECDSA_sig (65)`. The operator's digest is
   `keccak256` of `{sender, nonce, keccak256(initCode), keccak256(callData), accountGasLimits,
   paymasterGasLimits, preVerificationGas, gasFees, chainid, paymaster, validUntil, validAfter}`
   (every field **except** the trailing signature). Layout matches `account-abstraction` v0.7
   `VerifyingPaymaster`; see `EtzhayyimPaymaster.getHash`.
3. Submit to the EntryPoint bundler on Base.
4. EntryPoint calls `paymaster.validatePaymasterUserOp(...)` → verifies the operator signature
   (rejects if missing/invalid → Sybil-drain mitigation) **then** the allowlist + daily-cap policy.
5. If approved, paymaster pays the gas; user signs but pays nothing.

> The off-chain operator signing service + `@etzhayyim/sdk` `paymasterAndData` builder are
> tracked separately (follow-up to issue #1519) — this repo ships the on-chain verifier only.

## See also

- [ADR-2605172100](../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md)
- [ERC-4337 spec](https://eips.ethereum.org/EIPS/eip-4337)
- [Coinbase Smart Wallet docs](https://www.smartwallet.dev/)
- `../l2-anchor-contract/` — sister contract, similar deploy pattern
- `../anchor-cron/` — fee-skim source
