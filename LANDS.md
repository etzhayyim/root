# etzhayyim Land Trust (護持地)

> **地球上の土地は本質的に Tree of Life (生圏) に帰属し、いかなる国家・個人の私有財産でもない。** — ADR-2605192100 §1.11
>
> The land of the Earth essentially belongs to the Tree of Life (the biosphere); it is not the private property of any nation-state or individual.

This file is the **github-side half of the 4-layer permanent land record** per [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md). Each row references:

1. **Base L2 NFT** (PublicLandRegistry.sol, non-transferable ERC-721)
2. **geth-private constitutional record** (LandRegistry.sol, with constitutional invariants)
3. **IPFS GeoJSON + satellite imagery bundle + notarized deed** (CIDs in NFT metadata)
4. **This git commit** (dual-permanent record per [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md))

No admin. No transferable ownership. Anyone reading this can cross-verify any row against Base L2 + IPFS + geth-private + git history.

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

| # | Steward (@github) | DID | Location | Area | Type | On-chain donation tx | Donated | Lv |
|---|---|---|---|---|---|---|---|---|
| _(awaiting first donation — founder will donate symbolic plot after S0-S4 of ADR-2605192415 daemon architecture)_ | | | | | | | | |

## Stewardship duties (Lv5 護)

Each steward annually:

- Verifies land boundary (in-person inspection)
- Records biodiversity census (`ai.gftd.apps.etzhayyim.land-biodiversity`)
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
# 1. Verify Base L2 land title NFT
cast call $PUBLIC_LAND_REGISTRY \
  "tokenURI(uint256)(string)" \
  $LAND_ID \
  --rpc-url https://mainnet.base.org

# 2. Verify geth-private constitutional record
cast call $LAND_REGISTRY_GETH \
  "lands(uint256)((bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint8,address,uint64,uint8))" \
  $LAND_ID \
  --rpc-url https://geth.etzhayyim.com

# 3. Fetch IPFS GeoJSON + imagery + deed bundle
ipfs cat $GEOJSON_CID
ipfs cat $IMAGERY_BUNDLE_CID
ipfs cat $DEED_CID

# 4. Verify AT Record
curl -s https://pds.etzhayyim.com/xrpc/com.atproto.repo.getRecord \
  -G --data-urlencode "repo=$STEWARD_DID" \
  --data-urlencode "collection=ai.gftd.apps.etzhayyim.land-donation" \
  --data-urlencode "rkey=$RKEY"
```

All four substrate-records must resolve to the same `geojsonCid` + `imageryBundleCid` + `deedCid` + `oathHash`.

## See also

- [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md) — Global Land Sovereignty (primary)
- [ADR-2605192330](90-docs/adr/2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit.md) — Ocean/River/Air/Orbit extension
- [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md) — Steward succession
- [ADR-2605192100 §1.11](90-docs/adr/2605192100-etzhayyim-mission-charter.md) — Land doctrine
- [`50-infra/etzhayyim-land-registry/`](50-infra/etzhayyim-land-registry/) — Solidity source
- [`20-actors/magatama/cells/`](20-actors/magatama/cells/) — Land-related Pregel cells
