# etzhayyim Land Trust (護持地)

> **地球上の土地は本質的に Tree of Life (生圏) に帰属し、いかなる国家・個人の私有財産でもない。** — ADR-2605192100 §1.11
>
> 神の王国 (Malkhut Shamayim / Basileia tou Theou / 神の王国) の土地は、blockchain 上に soulbound NFT として記録される。— ADR-2605252300 Charter §0.3 (Preamble)
>
> The land of the Earth essentially belongs to the Tree of Life (the biosphere); it is not the private property of any nation-state or individual. As land of the Kingdom of God, it is recorded on blockchain as a soulbound NFT.

This file is the **github-side half of the 4-layer permanent land record** per [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md), with multi-ERC alignment per [ADR-2605252315](90-docs/adr/2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment.md). Each row references:

1. **Base L2 land NFT** (`PublicLandRegistry.sol` — ERC-721 + ERC-5192 soulbound, `locked()` returns true forever)
2. **geth-private constitutional record** (`LandRegistry.sol` — IERC5192 signaller + custom struct mapping, constitutional invariants enforced by intentional function absence)
3. **Base L2 steward-tenure NFT** (`StewardTenureRegistry.sol` — ERC-7401 nestable child of land NFT, succession via Council ≥3 multisig per [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md))
4. **Base L2 land-class aggregate** (`LandClassRegistry.sol` — ERC-1155 supplementary accounting; balance = area-m², soulbound)
5. **IPFS GeoJSON + satellite imagery bundle + notarized deed** (CIDs in NFT metadata)
6. **This git commit** (dual-permanent record per [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md))

No admin. No transferable ownership. No "owner" — only steward role. Anyone reading this can cross-verify any row against Base L2 + IPFS + geth-private + git history.

## How to donate land

1. Read [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md) (Global Land Sovereignty) in full.
2. Read [ADR-2605192100 §1.11](90-docs/adr/2605192100-etzhayyim-mission-charter.md) (Land as Religious-Corp Trust doctrine).
3. Confirm you are the legal owner (or beneficial owner) of the land in the national registry.
4. Prepare GeoJSON boundary (WGS84, ±1m precision), satellite imagery bundle (Sentinel-2 / Landsat / commercial, 3+ months time series), and notarized deed PDF.
5. Designate primary + 2 backup successor stewards (per [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md)).
6. Read and sign the canonical **land donation oath** (see ADR-2605192245 §2.2 Step 3).
7. Call `LandRegistry.donate(...)` on geth-private + `PublicLandRegistry` mints title NFT on Base L2.
8. Open a PR to this file adding your row.

Once your PR is merged, your land is permanently recorded across four substrates that cannot collude to erase it: Base L2 + geth-private + IPFS + this git history.

## Important: Dual-recognition with state cadastre

This Land Trust does NOT deny state land registries. It operates in **parallel** as a religious-corp doctrinal claim. Donors (now stewards) remain owners-of-record in their national cadastre and continue to fulfill national obligations (property tax, etc.). The etzhayyim claim is religious doctrinal — that the land belongs to Tree of Life and the donor holds stewardship only. See ADR-2605192245 §2.3.

## Land types

| Type | Description | Per ADR |
|---|---|---|
| Agricultural | Farmland, orchards, pasture | 2605192245 |
| Residential | Houses, lots | 2605192245 |
| Forest | Natural / planted forest | 2605192245 |
| Religious Facility | Shrines, temples, prayer spaces | 2605192245 |
| Other | (catch-all for terrestrial) | 2605192245 |
| Ocean / Maritime | Internal waters, territorial sea, EEZ, high seas | 2605192330 |
| Water / Riparian | Rivers, lakes, water rights | 2605192330 |
| Air / Atmosphere | Airspace, GHG stewardship | 2605192330 |
| Orbital / Space | LEO/GEO/Moon/Mars (symbolic, long-horizon) | 2605192330 |

## Roster

Each row references the multi-ERC layer per [ADR-2605252315](90-docs/adr/2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment.md):

- `gethLandId` = `LandRegistry.lands[].landId` (constitutional)
- `pubLandTokenId` = `PublicLandRegistry` ERC-721 tokenId (Base L2 mirror, soulbound, `locked()` = true)
- `tenureNftId` = `StewardTenureRegistry` ERC-7401 child NFT tokenId (current active tenure)
- `classTokenId` = `LandClassRegistry` ERC-1155 token ID (0..8 per LandType enum)

| # | Steward (@github) | DID | Location | Area (m²) | Type | gethLandId | pubLandTokenId | tenureNftId | classTokenId | donation tx | Donated | Lv |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| _(awaiting first donation — founder will donate symbolic plot after Bootstrap Council ratify, Wave 2 ERC activation, and S0-S4 of ADR-2605192415 daemon architecture)_ | | | | | | | | | | | | |

## Stewardship duties (Lv5 護)

Each steward annually:

- Verifies land boundary (in-person inspection)
- Records biodiversity census (`com.etzhayyim.apps.etzhayyim.land-biodiversity`)
- Provides reasonable access to etzhayyim adherents for religious gathering / meditation
- Ensures no commercial extraction (mining / clear-cut / large-scale monoculture)
- Continues national obligations (property tax)

See [ADR-2605192245 §5](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md) for full duties.

## Constitutional invariants (NOT amendable by governance)

- Donated land cannot be sold, transferred, or burned
- No "owner" concept exists — only steward role
- Donations are permanent (no withdraw)
- Steward succession is governed by [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md)

## Verification (any client can run)

```bash
# 1. Verify Base L2 land title NFT (ERC-721 + ERC-5192)
cast call $PUBLIC_LAND_REGISTRY \
  "ownerOf(uint256)(address)" \
  $PUB_LAND_TOKEN_ID \
  --rpc-url https://mainnet.base.org

cast call $PUBLIC_LAND_REGISTRY \
  "tokenURI(uint256)(string)" \
  $PUB_LAND_TOKEN_ID \
  --rpc-url https://mainnet.base.org

cast call $PUBLIC_LAND_REGISTRY \
  "locked(uint256)(bool)" \
  $PUB_LAND_TOKEN_ID \
  --rpc-url https://mainnet.base.org
# MUST return true — constitutional invariant per ADR-2605252315 §2.2

# 2. Verify geth-private constitutional record (also IERC5192 signaller)
cast call $LAND_REGISTRY_GETH \
  "lands(uint256)((bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint8,address,uint64,uint8))" \
  $GETH_LAND_ID \
  --rpc-url https://geth.etzhayyim.com

cast call $LAND_REGISTRY_GETH \
  "locked(uint256)(bool)" \
  $GETH_LAND_ID \
  --rpc-url https://geth.etzhayyim.com
# MUST return true

# 3. Verify steward-tenure child NFT (ERC-7401, nested under land NFT)
cast call $STEWARD_TENURE_REGISTRY \
  "directOwnerOf(uint256)(address,uint256,bool)" \
  $TENURE_NFT_ID \
  --rpc-url https://mainnet.base.org
# MUST return (PUBLIC_LAND_REGISTRY_ADDR, $PUB_LAND_TOKEN_ID, true)

# 4. Verify land-class aggregate (ERC-1155 supplementary)
cast call $LAND_CLASS_REGISTRY \
  "totalAreaByClass(uint256)(uint256)" \
  $CLASS_TOKEN_ID \
  --rpc-url https://mainnet.base.org
# Returns total m² in trust for that class

# 5. Fetch IPFS GeoJSON + imagery + deed bundle
ipfs cat $GEOJSON_CID
ipfs cat $IMAGERY_BUNDLE_CID
ipfs cat $DEED_CID

# 6. Verify AT Record
curl -s https://pds.etzhayyim.com/xrpc/com.atproto.repo.getRecord \
  -G --data-urlencode "repo=$STEWARD_DID" \
  --data-urlencode "collection=com.etzhayyim.apps.etzhayyim.land-donation" \
  --data-urlencode "rkey=$RKEY"
```

All substrate-records must resolve to the same `geojsonCid` + `imageryBundleCid` + `deedCid` + `oathHash`. The ERC-5192 `locked(tokenId) → true` invariant is constitutional: any client observing `locked() → false` for a registered land NFT MUST treat that result as evidence of a constitutional breach (the contract has been tampered with) and refuse to accept the record.

## See also

- [ADR-2605252300](90-docs/adr/2605252300-etzhayyim-charter-preamble-kingdom-of-god-on-blockchain.md) — Charter §0 Preamble (Kingdom of God on blockchain — constitutional self-identification, parent doctrinal source)
- [ADR-2605252315](90-docs/adr/2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment.md) — Land Trust Wave 2 — Multi-ERC alignment (721 + 5192 + 7401 + 1155)
- [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md) — Global Land Sovereignty (primary, Wave 1)
- [ADR-2605192330](90-docs/adr/2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit.md) — Ocean/River/Air/Orbit extension
- [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md) — Steward succession
- [ADR-2605192100 §1.11](90-docs/adr/2605192100-etzhayyim-mission-charter.md) — Land doctrine (Wave 1 elaboration of Preamble §0.2.3 Tree of Life-rooted)
- [`50-infra/etzhayyim-chain-contracts/src/LandRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/LandRegistry.sol) — geth-private constitutional contract
- [`50-infra/etzhayyim-chain-contracts/src/PublicLandRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/PublicLandRegistry.sol) — Base L2 ERC-721 + ERC-5192 mirror (R0 scaffold)
- [`50-infra/etzhayyim-chain-contracts/src/StewardTenureRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/StewardTenureRegistry.sol) — ERC-7401 nestable tenure (R0 scaffold)
- [`50-infra/etzhayyim-chain-contracts/src/LandClassRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/LandClassRegistry.sol) — ERC-1155 aggregate (R0 scaffold)
- [`40-engine/kotoba/crates/kotoba-kotodama/cells/`](40-engine/kotoba/crates/kotoba-kotodama/cells/) — Land-related Pregel cells
