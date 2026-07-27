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

> **⚠️ CRITICAL: Post-deploy stake is mandatory** — without stake, the EntryPoint throttles the paymaster after validation failures (ERC-4337 §6.2). See **[DEPLOY.md](DEPLOY.md)** for the complete checklist including monitoring alerts.

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

After deploy, update [`deps.toml [platform.operating_entity].paymaster_contract`] with the address.

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
