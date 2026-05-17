# etzhayyim-chain-contracts

**S0 scaffold of [ADR-2605172300](../../90-docs/adr/2605172300-etzhayyim-bi-asset-substrate.md).** Solidity contracts deployed to **geth-private** (ChainID `2605`, Clique PoA) that constitute the on-chain body of the etzhayyim religious voluntary association: constitution, adherent roster, kisha (basic-income) stream, phenotype multipliers, treasury accounting mirror, governance, and the anchor bridge to Base L2.

## Scope of this directory

These contracts live on the **internal** chain (geth-private at `50-infra/vultr/geth-private/`). They MUST NOT be deployed to Base. The Base-side counterparts (Treasury Safe, USDC transfer flow, paymaster) follow ADR-2605172100 and live elsewhere (Safe configured manually + `@etzhayyim/sdk` `pay()` path).

| Layer | Where it runs |
|---|---|
| Constitutional state, adherent roster, kisha accounting, governance | geth-private (this directory) |
| USDC custody, payout settlement | Base L2 (Gnosis Safe, configured outside this repo) |
| Bridging (state roots + claim-fulfillment receipts) | `AnchorBridge.sol` here ↔ existing `50-infra/l2-anchor-contract/` on Base |

## Contract set (per ADR-2605172300 §2)

| File | Chain | Role | Stage |
|---|---|---|---|
| `src/Constitution.sol` | geth-private | Immutable + governance-mutable constitutional parameters | **S0** |
| `src/AdherentRegistry.sol` | geth-private | ERC-5192 SBT, DID-bound, with attestation tracking | **S0** |
| `src/KishaStream.sol` | geth-private | Per-adherent rate, accrual, claim ticket issuance | **S1** |
| `src/AnchorBridge.sol` | geth-private | Permissionless state-root commit (relayer → Base anchor) | **S1** |
| `src/base/KishaPayout.sol` | Base L2 | M-of-N relayer-signed claim fulfillment; pulls USDC from Treasury Safe | **S1** |
| `src/Phenotype.sol` | geth-private | Per-adherent multiplier (0.5×–2.0×) populated by `EligibilityCell` | S2 |
| `src/TreasuryMirror.sol` | geth-private | NAV oracle mirror, envelope computation | S3 |
| `src/Governance.sol` | geth-private | OZ Governor derivative, 1 SBT = 1 vote, 72h timelock | S3 |

## Design rules (inherited)

From ADR-2605172000 + ADR-2605172100 (and reiterated in ADR-2605172300):

- **No upgrade path on constitutional constants.** Some `Constitution.sol` keys are immutable forever; others are `Governance.sol`-mutable. There is no "admin" key — `Constitution.sol` only accepts changes from the deployed `Governance.sol` address.
- **No fiat path.** Nothing here knows about Stripe / banks / cards.
- **No centralized DB dependency.** Contracts read only on-chain state. Off-chain inputs (event evidence) arrive via signed transactions or via `Phenotype.sol` cell-signed updates.
- **DID-bound.** Every `AdherentRegistry` SBT is bound 1:1 to a DID (did:web / did:plc / did:etzhayyim). Address ↔ DID linkage is established via signed attestation, not a registry lookup.
- **License: Apache 2.0** for every file in this directory.

## Build

```bash
forge build
forge test
```

## Deploy (later, not in S0)

Deployment scripts will live under `script/` and target `etzhayyim_private` (RPC injected via env). S0 is contracts-only; no deploy yet.

## Status

**S1 — flat-rate kisha**. `KishaStream` issues fixed-rate accrual tickets on geth-private; `KishaPayout` on Base settles them against the Treasury Safe with M-of-N officer signatures. `AnchorBridge` exposes permissionless state-root commits for the Base anchor relayer. Pregel `EligibilityCell` + per-adherent `PhenotypeAgent` still ship in S2; Governance + Treasury 3-tier ship in S3.
