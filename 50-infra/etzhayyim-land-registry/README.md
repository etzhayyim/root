# etzhayyim-land-registry

> **NOTE (2026-05-20)**: `LandRegistry.sol` was moved to
> [`../etzhayyim-chain-contracts/src/LandRegistry.sol`](../etzhayyim-chain-contracts/src/LandRegistry.sol)
> for unified Foundry project / deploy script integration. Build / test /
> deploy live there. This directory retained as the canonical design
> reference + future PublicLandRegistry.sol (Base L2 ERC-721 mirror) home.

Religious-corp Land Trust の Solidity contracts.

**Per [ADR-2605192245](../../90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md)** (Global Land Sovereignty) + [ADR-2605192330](../../90-docs/adr/2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit.md) (Extended) + [ADR-2605192345](../../90-docs/adr/2605192345-etzhayyim-steward-succession.md) (Succession).

## 4-layer substrate

```
L4 Public Title       Base L2 (PublicLandRegistry.sol)
                      — ERC-721 non-transferable, anyone-readable
                      — TODO: deploy as a sibling to LandRegistry on Base
L3 Constitutional     geth-private (LandRegistry.sol — IMPLEMENTED)
                      — Constitutional invariants enforced
L2 Geographic         IPFS (GeoJSON + satellite imagery + deed)
L1 Git Commit         /LANDS.md PR
```

## Contracts

| Contract | Chain | Status | Purpose |
|---|---|---|---|
| `LandRegistry.sol` | geth-private (chainId 2605) | ✅ deployed locally | Constitutional record + Lv5 護 Steward role + biodiversity attestations + dispute resolution |
| `PublicLandRegistry.sol` | Base L2 (chainId 8453) | ⏳ TODO | Public ERC-721 mirror (non-transferable, anyone-readable) |
| `AnchorBridge` (existing) | both | ✅ deployed | Cross-chain root anchor |

## Constitutional invariants (NOT amendable by governance)

- **No `transfer()` function** — donated land cannot be sold (waqf-equivalent inalienability)
- **No `burn()` / `delete()` function** — donations are permanent record
- **No `setOwner()` / `owner` concept** — only `steward` role exists
- **No `mint()` outside `donate()`** — only valid donation ritual creates land record

Verified by the absence of these functions in `LandRegistry.sol`.

## Donation ritual (6 steps, per ADR-2605192245 §2.2)

1. Boundary documentation (WGS84 GeoJSON, ±1m precision)
2. Satellite imagery hash (3+ months time series)
3. Donor oath signing (canonical text)
4. On-chain `donate()` call
5. AT Record `com.etzhayyim.apps.etzhayyim.land-donation`
6. PR to `/LANDS.md`

## Steward role

Steward is automatically Lv5 護 (per [ADR-2605172600](../../90-docs/adr/2605172600-etzhayyim-membership-ritual.md) ladder). Duties:

- Annual boundary inspection + attestation
- Annual biodiversity census
- Reasonable access to adherents
- No commercial extraction
- National obligations (property tax, etc.) — dual-recognition

## Build + Test + Deploy

All under [`../etzhayyim-chain-contracts/`](../etzhayyim-chain-contracts/):

```bash
cd ../etzhayyim-chain-contracts
forge build   # includes LandRegistry
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "runLocal()" --rpc-url http://localhost:8545 --broadcast --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

## Pregel cells

- [`40-engine/kotoba/crates/kotoba-kotodama/cells/land_donation_processing/`](../../40-engine/kotoba/crates/kotoba-kotodama/cells/land_donation_processing/)
- `40-engine/kotoba/crates/kotoba-kotodama/cells/land_stewardship_monitoring/`
- `40-engine/kotoba/crates/kotoba-kotodama/cells/land_dispute_resolution/`
- [`40-engine/kotoba/crates/kotoba-kotodama/cells/steward_succession/`](../../40-engine/kotoba/crates/kotoba-kotodama/cells/steward_succession/)

## Lexicons

- [`00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/land-donation.json`](../../00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/land-donation.json)
- `land-attestation.json` (annual steward attestation)
- `land-biodiversity.json`
- `land-dispute.json`
- `steward-succession-declaration.json`
- `steward-succession-pre-acceptance.json`
- `steward-succession-event.json`
