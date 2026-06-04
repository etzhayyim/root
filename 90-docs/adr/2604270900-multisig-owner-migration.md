---
id: adr-2604270900-multisig-owner-migration
title: "ADR: Multisig owner migration for geth-private contracts (Phase 3)"
status: proposed
doc_type: adr
topic: multisig-owner-migration
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - geth-private-phase-3-ownership
  - safe-multisig-on-260425
  - sealer-eoa-role-rotation
related:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-2604261717-staked-claim-truth-incentive
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
---

# ADR-2604270900 — Multisig owner migration for `geth-private` contracts (Phase 3)

| | |
|---|---|
| Status     | DRAFT (proposed) |
| Date       | 2026-04-27 |
| Supersedes | — (extends ADR-0074, ADR-2604261717, ADR-2604262100) |
| Owner      | etzhayyim-platform |

## Context

Every privileged on-chain role on `geth-private` (chainId 260425)
currently resolves to a single EOA — the platform sealer
`0xaFed0Cb7633EDBd26aA52658e71528309F562501`. That covers:

| Contract | Privileged roles |
|---|---|
| `GCCStablecoin`              | owner, masterMinter, pauser, blacklister |
| `DeployRegistry`             | owner |
| `etzhayyimActorRegistry`          | owner |
| `etzhayyimRootIdentityRegistry`   | owner |
| `etzhayyimAgentRegistry`          | owner |
| `ActorRuntimeRegistry`       | owner |
| `MurakumoRegistry`           | owner |
| `MurakumoEscrow`             | owner, oracle, treasury |
| `ClaimStakeEscrow`           | owner, arbiter, treasury, rewardPool |
| `RegoArbiter`                | owner, signer (set via `setSigner`) |

Sealer-key custody is 3-tier (`.local-secrets/` + macOS Keychain L2 +
etzhayyim Vault L3 once `vault-investiture.sh` runs). That protects the
**signer** of those roles. It does **not** protect against:

- A compromised operator workstation pushing arbitrary contract
  state changes (e.g. `pauser` → freeze GCC permanently, `oracle` →
  drain MurakumoEscrow at a manipulated cost).
- Single-operator decision-making for emotionally-loaded actions
  (blacklisting an actor, slashing a claim, removing a Murakumo
  operator).
- Bus-factor of one — losing the operator (career change, illness)
  freezes all upgrade and emergency paths.

Phase 3, called out in `ADDRESSES.md` for nearly every contract
(*"Phase 3 → multisig"*), is to replace the sealer EOA with a 2-of-3
Safe (formerly Gnosis Safe) on `geth-private`.

## Decision

1. Deploy a Safe singleton + factory + fallback handler on
   `geth-private`. We do not vendor or fork the Safe contracts —
   we deploy the audited canonical bytecode (`v1.4.1`) using the
   sealer.
2. Create one Safe with three owners and threshold 2. Owner set is
   tracked in `50-infra/vultr/geth-private/.local-secrets/safe-owners.json`
   (gitignored) and mirrored into etzhayyim Vault `etzhayyim-private-chain-safe`.
   See "Owner set" below.
3. For each contract listed in Context, transfer every privileged
   role from sealer → Safe via the role-rotation function the contract
   already exposes (`transferOwnership`, `setMasterMinter`, etc.).
4. Sealer is **not** removed from chain. It retains:
   - `clique` block sealing (genesis-baked, cannot be transferred)
   - the deployer-nonce continuity that future Foundry scripts rely on
5. After migration, every privileged on-chain action goes through
   Safe (UI: `https://app.safe.global/` does **not** support custom
   chains directly, so we run the Safe transaction service docker
   image alongside the cluster, or use the official `safe-cli`).

This is a **per-role transfer**, not a contract upgrade. No proxy
implementation pointers move. No state moves. Only the address
authorised to call privileged functions changes.

## Owner set

Three keys, threshold 2. The keys are not specified in this ADR — the
operator picks the three principals after this ADR is accepted.
Recommended composition:

- **K1**: platform operator (`jun@etzhayyim.com`). macOS Keychain
  + iCloud sync + etzhayyim Vault L3.
- **K2**: a co-owner (etzhayyim Japan board member or co-founder). Same
  custody pattern, separate physical device.
- **K3**: cold-storage hardware wallet (Ledger / Trezor) held in a
  bank safe-deposit box. Threshold 2 means K3 is only used when K1 or
  K2 is lost or compromised; daily ops go through K1 + K2.

## Migration script

`50-infra/vultr/geth-private/contracts/script/MigrateOwnersToSafe.s.sol`
(this PR adds it). The script is **simulate-only by default**:

```bash
forge script script/MigrateOwnersToSafe.s.sol \
  --rpc-url https://geth.etzhayyim.com \
  --sig 'simulate(address)' 0x{SAFE_ADDR}
```

The simulate path enumerates every transfer the script would broadcast
+ prints the new role table. Output is a transcript that can be
diffed against `ADDRESSES.md` before any tx fires.

Live cutover requires the explicit `--broadcast` flag *and*
`MIGRATE_LIVE=true` env var:

```bash
MIGRATE_LIVE=true forge script script/MigrateOwnersToSafe.s.sol \
  --rpc-url https://geth.etzhayyim.com \
  --broadcast \
  --legacy \
  --private-key "$(cat 50-infra/vultr/geth-private/.local-secrets/sealer.priv)" \
  --sig 'execute(address)' 0x{SAFE_ADDR}
```

The double gate (`--broadcast` + env var) is intentional — `forge
script` defaults to a dry-run, but without the env var the Solidity
script `revert`s before any external call. Mistakes that would brick
contracts (passing `address(0)` as `safe`, reusing the sealer EOA as
`safe`, etc.) `revert` deterministically with a named error.

## Failure modes considered

| Mode | Mitigation |
|---|---|
| Wrong Safe address (typo) | `MigrateOwnersToSafe.execute()` reverts if `safe.code.length == 0` (i.e. EOA) or if `safe == sealer` |
| Partial transfer (script crashes mid-flight) | Each role transfer is its own tx. Re-running the script is a no-op for already-transferred roles (each contract checks current owner before re-broadcast). The simulate output names which roles still need to move. |
| Lost K1 | K2 + K3 retain threshold (2-of-3). Use Safe `removeOwner` + `addOwner` to rotate K1 within hours. |
| Lost K1 + K2 | K3 alone cannot meet threshold. **This is the irreversible case** — chain owner is permanently lost. Mitigation = K3 must be in physically separate jurisdiction from K1/K2. |
| Safe singleton bug (audited bytecode) | Safe v1.4.1 has been audited by 5 independent teams + has $100B+ TVL on Ethereum mainnet. Risk is < the single-EOA risk we're moving away from. |
| `geth-private` sealer collusion (sealer can revert blocks) | Out of scope for this ADR. Phase 3.5 (multi-sealer) is required to remove this risk; multisig owner is necessary but not sufficient. |

## Out of scope

- Multi-sealer Clique vote (Phase 3.5 — needs a second region first per
  `50-infra/vultr/geth-private/CLAUDE.md`).
- Safe Module integration (e.g. spending limits on `MurakumoEscrow.oracle`).
  Phase 3 ships plain transfers; Modules are Phase 4.
- Migrating off-chain bots (`rego-arbiter-settler`, `etzhayyim deploy`'s
  `eth_deploy_receipt`) — they continue to use the sealer EOA, which
  retains its block-sealing role and pre-funded balance. Only
  privileged contract roles move.

## Acceptance criteria

After cutover:

```bash
# Every privileged role returns the Safe address, not the sealer
for addr in $(jq -r '.[]' 50-infra/vultr/geth-private/contracts/ADDRESSES.json); do
  cast call "$addr" 'owner()(address)' --rpc-url https://geth.etzhayyim.com
done | sort -u
# → exactly one address: the Safe
```

`50-infra/vultr/geth-private/contracts/ADDRESSES.md` is updated to
list every role's new principal. `[geth_private.contracts].owner_phase`
in `deps.toml` flips from `"phase-2-sealer"` to `"phase-3-multisig"`.

## Why now

- PR #1145 ships Blockscout. Once that's live, every role transfer
  is publicly visible on `https://explorer.etzhayyim.com/` — auditable in
  real time.
- ADR-2604261717 Phase 2-B settler ships in this PR. It assumes the
  sealer signs `settle()` — Phase 3 makes the Safe the new arbiter
  *and* updates the settler's `SEALER_PRIV` to a Safe-controlled
  signer. Doing both at once minimises one-step rollback complexity.
- The longer the sealer is the only owner, the more downstream
  systems (yoro UI, etzhayyim CLI, authz Worker) bake in assumptions about
  it. Phase 3 should land before more callers compound the lock-in.
