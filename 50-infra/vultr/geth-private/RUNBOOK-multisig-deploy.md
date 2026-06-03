# RUNBOOK — Phase 3 multisig deploy ceremony

Closes the "Phase 3 → multisig" TODO that's been on every contract's
`ADDRESSES.md` row since Phase 2-A. Pairs with ADR-2604270900 +
`script/DeploySafe.s.sol` + `script/MigrateOwnersToSafe.s.sol`.

**Outcome**:
- A 2-of-3 (or 2-of-N) Safe v1.4.1 lives on `geth-private` (chainId 260425).
- The Safe singleton + SafeProxyFactory + CompatibilityFallbackHandler are
  deployed and recorded in `ADDRESSES.md`.
- **Ownership has NOT moved yet.** This runbook stops at "Safe is alive,
  `simulate(safe)` of MigrateOwnersToSafe returns a clean transcript".
  Pulling the trigger on `execute(safe)` is a separate ceremony — once
  done, every privileged role moves to the Safe in one tx batch.

This split is deliberate. Deploying a Safe is reversible (just don't use
it). Transferring ownership is not (you'd need 2-of-3 to come back, and
if you mistyped the Safe address those keys are nowhere). Treat each
stage as a separate go/no-go.

## Pre-flight

| Item | Verify |
|---|---|
| `forge --version` ≥ 1.0 | `forge --version` |
| `node --version` ≥ 20 (for the npm Safe artifact pull) | `node --version` |
| Sealer `.local-secrets/sealer.priv` reachable | `cast wallet address --private-key "$(cat 50-infra/vultr/geth-private/.local-secrets/sealer.priv)"` → `0xaFed0Cb7633EDBd26aA52658e71528309F562501` |
| RPC reachable | `cast chain-id --rpc-url https://geth.etzhayyim.com` → `260425` |
| Prebuilt Safe v1.4.1 artifacts in place | `cd 50-infra/vultr/geth-private/contracts && npm install && ls node_modules/@safe-global/safe-contracts/build/artifacts/contracts/Safe.sol/Safe.json` |
| Foundry compiles | `cd 50-infra/vultr/geth-private/contracts && forge build` |

> **Why npm, not forge install** — Safe v1.4.1 is solc-0.7.6-pinned. Recompiling from source under our 0.8.23 + via_ir + paris toolchain hits stack-too-deep on `Safe.execTransaction`. The npm package ships hardhat-built JSON artifacts (bytecode + ABI); `script/DeploySafe.s.sol` loads them with `vm.readFile` + `vm.parseJsonBytes` and CREATEs the bytecode directly, bypassing source compilation entirely. `foundry.toml` whitelists the artifact path under `fs_permissions`. `node_modules/` is gitignored — the package-lock pin is what gives us reproducibility.

If any fail: stop. Don't bypass with `--no-verify` — every check protects
against a different bricking vector.

## Stage 1 — pick the owner set

Per ADR-2604270900 §"Owner set", recommended 2-of-3:

| Slot | Recommended principal | Custody |
|---|---|---|
| K1 | platform operator (`jun@etzhayyim.com`) | macOS Keychain `etzhayyim.private-chain` accounts `K1_*` + iCloud sync + etzhayyim Vault L3 |
| K2 | co-owner (etzhayyim Japan board / co-founder) | same pattern, separate physical device |
| K3 | cold-storage hardware wallet (Ledger / Trezor) | bank safe-deposit box |

**Get the three EVM addresses** (don't broadcast yet — these are public,
the keys aren't):

```bash
K1=0x...   # operator's address (etzhayyim authn whoami → linked ethereum-actor)
K2=0x...   # co-owner's address
K3=0x...   # hardware wallet address
```

Never put any of these private keys on a server. The Safe doesn't need
them at deploy time — it only stores the addresses. Signing happens
later, off-chain, when the Safe transactions are submitted.

## Stage 2 — simulate the deploy

```bash
cd 50-infra/vultr/geth-private/contracts
npm install   # idempotent; pulls @safe-global/safe-contracts@1.4.1 if missing

forge script script/DeploySafe.s.sol \
  --rpc-url https://geth.etzhayyim.com \
  --sig 'simulate(address[],uint256,uint256)' \
  "[$K1,$K2,$K3]" 2 0
```

Expected output: addresses for singleton / factory / handler / safe + the
threshold + saltNonce + owner enumeration. **No tx broadcast.** If
`simulate` reverts:

| Error | Cause | Fix |
|---|---|---|
| `OwnerListEmpty` | empty `[…]` | populate K1/K2/K3 |
| `ThresholdInvalid` | threshold == 0 or > owners | use 2 (or 1<threshold≤N) |
| `DuplicateOwner` | same address twice | de-dup |
| `OwnerIsZero` | `address(0)` in list | replace with real address |
| `OwnerIsSealer` | sealer in list | swap for a non-sealer key — Phase 3 explicitly removes sealer-only authority |

## Stage 3 — broadcast

```bash
MIGRATE_LIVE=true forge script script/DeploySafe.s.sol \
  --rpc-url https://geth.etzhayyim.com \
  --broadcast \
  --legacy \
  --private-key "$(cat 50-infra/vultr/geth-private/.local-secrets/sealer.priv)" \
  --sig 'execute(address[],uint256,uint256)' \
  "[$K1,$K2,$K3]" 2 0
```

Output includes `safe: 0x…`. Capture that value as `$SAFE_ADDR` — it's
the only piece of state you need from this stage.

Sanity:

```bash
cast call "$SAFE_ADDR" 'getThreshold()(uint256)' --rpc-url https://geth.etzhayyim.com
# → 2

cast call "$SAFE_ADDR" 'getOwners()(address[])' --rpc-url https://geth.etzhayyim.com
# → [K1, K2, K3]

cast call "$SAFE_ADDR" 'VERSION()(string)' --rpc-url https://geth.etzhayyim.com
# → "1.4.1"
```

## Stage 4 — record

Append to `50-infra/vultr/geth-private/contracts/ADDRESSES.md`:

```md
| **Safe v1.4.1 (multisig owner)** | `$SAFE_ADDR` | 2-of-3 Safe. Owners: K1=$K1, K2=$K2, K3=$K3. Singleton: 0x… Factory: 0x… FallbackHandler: 0x…. Deployed YYYY-MM-DD. ADR-2604270900. Phase 3 ownership migration target. |
```

And bump `[geth_private]` in `50-infra/vultr/geth-private/deps.toml`:

```toml
[geth_private.multisig]
safe              = "0x…"
threshold         = 2
owners            = ["0x…K1", "0x…K2", "0x…K3"]
singleton         = "0x…"   # Safe v1.4.1 logic
factory           = "0x…"   # SafeProxyFactory
handler           = "0x…"   # CompatibilityFallbackHandler
deployed_at_block = "0x…"
adr               = "90-docs/adr/2604270900-multisig-owner-migration.md"
```

Commit those two file edits, push, merge.

## Stage 5 — STOP and decide

You now have a Safe but **no role has moved to it yet**. Three options:

a. **Park it for review.** Owners review the ADR + transcript. No risk —
   the Safe just sits there. Sealer continues to own all roles.

b. **Run `MigrateOwnersToSafe.s.sol simulate`** — prints the per-role
   transfer plan with the new Safe address. Still no broadcast:

   ```bash
   forge script script/MigrateOwnersToSafe.s.sol \
     --rpc-url https://geth.etzhayyim.com \
     --sig 'simulate(address)' "$SAFE_ADDR"
   ```

   Diff the output against `ADDRESSES.md`. The plan should hit every
   `owner()`, `masterMinter()`, `pauser()`, `blacklister()`, `oracle()`,
   `treasury()`, `arbiter()`, `rewardPool()` listed there.

c. **Pull the trigger** (separate ceremony, requires K1+K2 signatures
   later when the Safe takes over). DO NOT do this in the same shell
   session as the deploy — context-switch first, re-verify the Safe
   address by reading from chain, then:

   ```bash
   MIGRATE_LIVE=true forge script script/MigrateOwnersToSafe.s.sol \
     --rpc-url https://geth.etzhayyim.com \
     --broadcast \
     --legacy \
     --private-key "$(cat 50-infra/vultr/geth-private/.local-secrets/sealer.priv)" \
     --sig 'execute(address)' "$SAFE_ADDR"
   ```

   This is the irreversible step. If `$SAFE_ADDR` is wrong, every
   privileged role on every contract is bricked. The script reverts on
   `safe == 0 | EOA | sealer`, but it can't catch "valid but wrong
   contract". Triple-check the address before running.

## Rollback

| Stage | Rollback |
|---|---|
| 2 (simulate) | nothing happened; rerun |
| 3 (deploy)   | leave the Safe orphaned — deploying a second Safe is a new tx, doesn't conflict |
| 4 (docs)     | revert the doc commit |
| 5b (simulate migrate) | nothing happened; rerun |
| 5c (execute migrate) | **NOT TRIVIALLY REVERSIBLE** — recovery requires 2-of-3 Safe signers calling each role's transfer function back to sealer. If 2 signers can't be assembled, contracts are permanently Safe-owned. This is by design (it's exactly the property we're paying for). |

## Why two stages

A single "deploy + migrate" script would be simpler, but the rollback
table above is the reason we don't write one. Stage 5c locks in
authority transfer; everything before it is undo-able without losing
state. Forcing the operator to shell-out, verify, then re-enter at a
different prompt prevents cargo-culting "yes" through both halves of an
irreversible action.
