# etzhayyim-paymaster

**ERC-4337 Paymaster contract on Base L2.** Sponsors gas for sender Smart Accounts whose user-ops match the configured policy (allowlisted target contract + per-sender daily cap). Per [ADR-2605172100](../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md).

Foundry Solidity project. Stub-quality v0.0.0; tested logic + deploy script + policy hooks but not yet deployed or independently audited.

## What it sponsors

The paymaster's policy is intentionally narrow:

- ✅ USDC `transfer(...)` to a whitelisted recipient set (etzhayyim app recipients, public-fund splits, etc.)
- ✅ Calls to specific app contracts on Base L2 (EtzhayyimAnchor, public-fund Splits, escrow Safes)
- ❌ Anything else (rejected at `validatePaymasterUserOp`)

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

- **Has owner** (intended to be a 2-of-3 Safe): `setAllowlist`, `setDailyLimit`, `withdraw`, `setOwner`
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

You can pre-seed the paymaster's allowed factory list at deployment time so that
newly-created smart accounts (deployed via `initCode`) are accepted by the
paymaster's factory allowlist check (Issue #1518 mitigation).

Set the `ALLOWED_FACTORY` environment variable to a single factory address when
running the deploy script. Example:

```bash
ALLOWED_FACTORY=0x1234567890abcdef1234567890abcdef12345678 \
  forge script script/Deploy.s.sol:Deploy \
  --rpc-url $BASE_SEPOLIA_RPC --broadcast --private-key $DEPLOYER_PRIVATE_KEY
```

If you do not provide `ALLOWED_FACTORY`, the paymaster is deployed with an
empty factory allowlist and will reject `UserOperation`s that include
`initCode` (i.e. operations that attempt to deploy a new smart account).

Admin operators may also add factories after deploy via the `setAllowedFactory`
owner call (intended for the 2-of-3 Safe owner).

## SDK integration

The `@etzhayyim/sdk` `pay()` method passes `paymaster: "sponsored"` by default. Internally:

1. Build ERC-4337 UserOperation for the USDC transfer.
2. Set `paymasterAndData` = `paymaster_addr ++ encoded_policy_hint`.
3. Submit to the EntryPoint bundler on Base.
4. EntryPoint calls `paymaster.validatePaymasterUserOp(...)` → policy check.
5. If approved, paymaster pays the gas; user signs but pays nothing.

## See also

- [ADR-2605172100](../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md)
- [ERC-4337 spec](https://eips.ethereum.org/EIPS/eip-4337)
- [Coinbase Smart Wallet docs](https://www.smartwallet.dev/)
- `../l2-anchor-contract/` — sister contract, similar deploy pattern
- `../anchor-cron/` — fee-skim source
