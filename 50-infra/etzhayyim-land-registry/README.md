# etzhayyim-land-registry

Religious-corp Land Trust の Solidity contracts。

**Per [ADR-2605192245](../../90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md)** (Global Land Sovereignty) + [ADR-2605192330](../../90-docs/adr/2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit.md) (Extended) + [ADR-2605192345](../../90-docs/adr/2605192345-etzhayyim-steward-succession.md) (Succession).

## 4-layer substrate

```
L4 Public Title       Base L2 (PublicLandRegistry.sol)
                      — ERC-721 non-transferable, anyone-readable
L3 Constitutional     geth-private (LandRegistry.sol)
                      — Constitutional invariants enforced
L2 Geographic         IPFS (GeoJSON + satellite imagery + deed)
L1 Git Commit         /LANDS.md PR
```

## Contracts

| Contract | Chain | Purpose |
|---|---|---|
| `LandRegistry.sol` | geth-private (chainId 2605) | Constitutional record + Lv5 護 Steward role + biodiversity attestations + dispute resolution |
| `PublicLandRegistry.sol` | Base L2 (chainId 8453) | Public ERC-721 mirror (non-transferable, anyone-readable) |
| `AnchorBridge` (existing) | both | Cross-chain root anchor |

## Constitutional invariants (NOT amendable by governance)

- **No `transfer()` function** — donated land cannot be sold (waqf-equivalent inalienability)
- **No `burn()` / `delete()` function** — donations are permanent record
- **No `setOwner()` / `owner` concept** — only `steward` role exists
- **No `mint()` outside `donate()`** — only valid donation ritual creates land record

## Donation ritual (6 steps, per ADR-2605192245 §2.2)

1. Boundary documentation (WGS84 GeoJSON, ±1m precision)
2. Satellite imagery hash (3+ months time series)
3. Donor oath signing (canonical text)
4. On-chain `donate()` call
5. AT Record `ai.gftd.apps.etzhayyim.land-donation`
6. PR to `/LANDS.md`

## Steward role

Steward is automatically Lv5 護 (per ADR-2605172600 ladder). Duties:

- Annual boundary inspection + attestation
- Annual biodiversity census
- Reasonable access to adherents
- No commercial extraction
- National obligations (property tax, etc.) — dual-recognition

## Succession (per ADR-2605192345)

Donor designates **primary + 2 backup successors** at donation time. Triggers:
- Death
- Incapacitation
- Long-term absence (>1 year)
- Self step-down
- Charter Compliance Non-Aligned status

Fallback paths: `council-appointed` / `corpus-direct` / `community-trust` / `dissolution-to-corpus`.

## Extended land types (per ADR-2605192330)

| Type enum | Status |
|---|---|
| Agricultural / Residential / Forest / ReligiousFacility / Other | S0 (initial) |
| Ocean (territorial + EEZ + high seas) | S3 (S0 後) |
| Water / Riparian | S2 |
| Air / Airspace | S4 |
| Orbital / Space | S5 (symbolic, long-horizon) |

## Foundry layout

```
contracts/
├── LandRegistry.sol            (geth-private)
├── PublicLandRegistry.sol      (Base L2 ERC-721 non-transferable)
└── interfaces/
    ├── IAdherentRegistry.sol
    ├── ICouncil.sol
    └── IChartersComplianceRegistry.sol
test/
├── LandRegistry.t.sol
├── PublicLandRegistry.t.sol
├── Succession.t.sol
└── ConstitutionalInvariants.t.sol  (transfer/burn must always revert)
script/
└── Deploy.s.sol
```

## Pregel cells

- `20-actors/magatama/cells/land_donation_processing/` — donation ritual orchestration
- `20-actors/magatama/cells/land_stewardship_monitoring/` — monthly satellite + biodiversity
- `20-actors/magatama/cells/land_dispute_resolution/` — Council dispute deliberation
- `20-actors/magatama/cells/steward_succession/` — succession activation

## Lexicons

- `00-contracts/lexicons/ai/gftd/apps/etzhayyim/land-donation.json`
- `land-attestation.json` (annual steward attestation)
- `land-biodiversity.json`
- `land-dispute.json`
- `steward-succession-declaration.json`
- `steward-succession-pre-acceptance.json`
- `steward-succession-event.json`
