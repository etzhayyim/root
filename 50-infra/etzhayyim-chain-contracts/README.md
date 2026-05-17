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
| `src/KishaStream.sol` | geth-private | Per-adherent rate, accrual, claim ticket issuance (S2: Phenotype-aware) | **S1+S2** |
| `src/AnchorBridge.sol` | geth-private | Permissionless state-root commit (relayer → Base anchor) | **S1** |
| `src/base/KishaPayout.sol` | Base L2 | M-of-N relayer-signed claim fulfillment; pulls USDC from Treasury Safe | **S1** |
| `src/Phenotype.sol` | geth-private | Per-adherent multiplier (0.5×–2.0×) populated by cell-signed updates from `EligibilityCell` | **S2** |
| `src/TreasuryMirror.sol` | geth-private | Oracle-signed 3-tier NAV mirror; 156-slot weekly ring buffer; κ-band envelope calc | **S3** |
| `src/Governance.sol` | geth-private | Minimal in-house Governor; 1 SBT = 1 vote; quorum + 72h timelock + 14d grace | **S3** |
| `src/CorpusRegistry.sol` | geth-private | Soulbound NFT registry for 本財 corpus assets; governance-gated mint / lock / dispose | **S4 (legal-review-contingent)** |
| `src/HoldingAttestation.sol` | geth-private | Representative-officer signed commitment that they hold legal title in trust for the association | **S4 (legal-review-contingent)** |

## Design rules (inherited)

From ADR-2605172000 + ADR-2605172100 (and reiterated in ADR-2605172300):

- **No upgrade path on constitutional constants.** Some `Constitution.sol` keys are immutable forever; others are `Governance.sol`-mutable. There is no "admin" key — `Constitution.sol` only accepts changes from the deployed `Governance.sol` address.
- **No fiat path.** Nothing here knows about Stripe / banks / cards.
- **No centralized DB dependency.** Contracts read only on-chain state. Off-chain inputs (event evidence) arrive via signed transactions or via `Phenotype.sol` cell-signed updates.
- **DID-bound.** Every `AdherentRegistry` SBT is bound 1:1 to a DID (did:web / did:plc / did:etzhayyim). Address ↔ DID linkage is established via signed attestation, not a registry lookup.
- **License: Apache 2.0** for every file in this directory.

## Build

```bash
# First-time setup (per checkout):
forge install foundry-rs/forge-std --no-commit

forge build
forge test -vvv
```

Tests live under `test/` and depend on `forge-std`. `_helpers/Fixture.sol` deploys the full Constitution → Registry → KishaStream → Phenotype → Governance → TreasuryMirror stack with S0/S1/S2/S3 defaults; individual `*.t.sol` files exercise behavior on top.

## Deploy (later, not in S0)

Deployment scripts will live under `script/` and target `etzhayyim_private` (RPC injected via env). S0 is contracts-only; no deploy yet.

## Status

**S4 — Corpus tier (legal-review-contingent)**. `CorpusRegistry.sol` lands a soulbound NFT per 本財 asset (real property / IP / facility / RWA token reference), with governance-only `mint` / `updateMetadata` / `setLock` / `flagDisposed`. `HoldingAttestation.sol` lands a representative-officer signed commitment that they hold legal title in trust for the association, with EIP-191 signature verification, template-CID snapshot per attestation, and governance-only revoke. **These two contracts are structurally complete but legally contingent — production deployment requires Japan-jurisdiction lawfirm review of the attestation document template.** S3 surface (`Governance.sol` + `TreasuryMirror.sol`) is unchanged.
