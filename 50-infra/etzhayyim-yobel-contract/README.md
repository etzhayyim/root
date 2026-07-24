# etzhayyim-yobel-contract

On-chain registries for the yobel actor (collective debt release rites). Per [ADR-2605201800](../../90-docs/adr/2605201800-etzhayyim-yobel-debt-release-actor.md). Apache-2.0 + [Charter Compliance Rider v2.0](../../CHARTER-RIDER.md).

## Contracts

| Contract | Purpose | Per |
|---|---|---|
| `src/YobelRiteRegistry.sol` | Immutable append-only registry of declared rites with Council ratification + status state machine (Declared / Active / Completed / Cancelled / Superseded) | ADR-2605201800 §Decision |
| `src/YobelReleaseRegistry.sol` | Immutable append-only registry of individual debt releases. Enforces Charter Rider §2(b) one-way invariant (`cumulative released ≤ debt principal + accrued`) | ADR-2605201800 §Decision + CR v2 §2(b) |

Both contracts follow the etzhayyim constitutional contract pattern: **no admin / no upgrade / no pause / permissionless write / append-only / events for indexers** (matches `EtzhayyimAnchor`, `AnchorBridge`).

## Boundaries (constitutional, NOT amendable)

- **No fiat / no Stripe.** Contracts take no value. USDC transfers happen in the EtzhayyimPaymaster (separate contract) and `baseL2TxHashCrossRef` stores the audit link
- **No loan / interest / margin / liquidation methods.** Schema-level Charter Rider §2(b) enforcement — these methods simply do not exist
- **No upgrade.** To change behavior, deploy a new contract under a new yobel actor version. ADR-2605201800 design SSoT must be amended first via Council Lv9 vote
- **Privacy.** DIDs + signatures + doctrinal text stored as keccak256 hashes only; plaintext lives in encrypted AT MST records (XChaCha20-Poly1305 per ADR-2605181100)
- **Cross-link only.** Contracts emit events; off-chain indexers (yoro, Public Fund audit, vendor:bankruptcy.etzhayyim.com) consume them and cross-correlate

## Build & test

```bash
# Foundry tests (Solidity 0.8.27, optimizer 1M runs, via_ir)
forge test -vv

# Coverage
forge coverage

# Gas report
forge snapshot
```

## Deploy

```bash
# Base Sepolia (testnet — recommended for S1 verification)
DEPLOYER_PRIVATE_KEY=0x... \
BASE_SEPOLIA_RPC_URL=https://... \
BASESCAN_API_KEY=... \
forge script script/Deploy.s.sol --rpc-url base_sepolia --broadcast --verify

# Base mainnet (Council Lv9 chair multisig only)
# Deploy address must be a Safe multisig with ≥ 3-of-5 Council Lv9 signers.
forge script script/Deploy.s.sol --rpc-url base_mainnet --broadcast --verify
```

Output addresses must be appended to `90-docs/deployments/yobel.md` for off-chain indexer + verifier configuration.

## Cross-actor wiring

| Caller | Method | Purpose |
|---|---|---|
| `rite_declaration` cell | `YobelRiteRegistry.declareRite()` | Initial rite write after Council ratification proposal submitted |
| `rite_declaration` cell | `YobelRiteRegistry.ratifyRite()` | After Council Lv6+ × 3 + Lv9 chair sign (canonical ratification hash) |
| `creditor_enrollment` cell | `YobelReleaseRegistry.registerDebtCap()` | Mirror debt principal + accrued (one-way invariant cap source of truth) |
| `release_settlement` cell | `YobelReleaseRegistry.recordRelease()` | Per-debt release record + cumulative cap check |
| `audit_witness` cell (tampering) | `YobelRiteRegistry.supersedeRite()` | Mark rite superseded on confirmed tampering |
| Anyone (post expiry) | `YobelRiteRegistry.completeRite()` | Final status transition for completed rites |

All calls are permissionless on-chain; off-chain DMN + cell logic enforces SBT level, Charter Rider compliance, and eligibility gates **before** the on-chain write.

## Audit anchoring

This bundle does **not** define its own anchor contract. Instead, the `audit_witness` cell's batched anchor calls into the existing [`EtzhayyimAnchor`](../l2-anchor-contract/src/EtzhayyimAnchor.sol) (Base L2) and [`AnchorBridge`](../etzhayyim-chain-contracts/src/AnchorBridge.sol) (geth-private), reusing the constitutional MST anchor pipeline per ADR-2605171800 + ADR-2605172300.

## Threat model

| Threat | Mitigation |
|---|---|
| Hostile party calls `declareRite` with garbage data | Off-chain indexers gate by `declarer` DID resolution + Council SBT level; garbage rites have no off-chain backers and quietly age out without ratification |
| Hostile party calls `ratifyRite` with fabricated hash | Off-chain canonical hash verification against encrypted Council signature MST record exposes the fraud; rite is then `supersedeRite`-d by `audit_witness` |
| Over-release attempted | Reverts on `OneWayViolation` — Charter Rider §2(b) enforced at EVM execution level |
| Debt cap inflation | `registerDebtCap` rejects duplicate registration; original creditor enrollment is canonical |
| Replay attack | `releaseId` uniqueness + `riteId` uniqueness gate; both checked at storage-write time |
| Reorg | All writes are idempotent (revert on duplicate); off-chain indexer re-reads events at finality |

## See also

- ADR-2605201800 — yobel actor design SSoT
- ADR-2605172300 — etzhayyim open telecom fabric (Base L2 substrate boundary)
- ADR-2605181100 — XChaCha20-Poly1305 envelope encryption
- ADR-2605192230 — Three-Tier Enforcement (Council ratification framework)
- `../l2-anchor-contract/` — `EtzhayyimAnchor` (audit anchor reuse target)
- `../etzhayyim-chain-contracts/` — Governance / AnchorBridge / Phenotype (cross-reference contracts)
- `../../orgs/etzhayyim/com-etzhayyim-yobel/` — Python LangGraph cells calling these contracts via web3 ports
