# etzhayyim-charters-compliance

`ChartersComplianceRegistry.sol` — Council attestation の単一 source of truth。

**Per [ADR-2605192230](../../90-docs/adr/2605192230-etzhayyim-three-tier-enforcement-implementation.md)** (Three-Tier Enforcement Implementation) + [ADR-2605192200](../../90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md) (Charter Rider v2.0).

## Architecture

```
ChartersComplianceRegistry (Base L2 + geth-private)
  │
  ├── attestationsByAddress[address] → Attestation
  ├── attestationsByTokenId[uint256] → Attestation
  │
  ├── attestNonAligned()         ← Council Lv6+ ≥3 multisig
  ├── appeal()                   ← subject entity, 30 day window
  ├── rehabilitate()             ← Council Lv6+ ≥3 (teshuvah)
  ├── finalize()                 ← anyone, after appeal window expires
  │
  ├── isNonAlignedAddress(addr)  ← public view (read by other contracts)
  └── isNonAlignedTokenId(id)    ← public view
```

## Status

| Layer | enforcement | Mechanism |
|---|---|---|
| L1 License | software 使用権失効 | Rider §3 + Apache 2.0 §3 termination |
| L2 便益拒否 | Kisha + Public Fund 受給不可 | `Phenotype.effectiveMultiplier() → 0` + `PublicFundGovernance.propose() require !nonAligned` + `TitheRouter.route() require !nonAligned` |
| L3 評価最低 | Phenotype multiplier = 0 | constitutional override in `Phenotype.sol` |

## Contracts to amend (per ADR-2605192230)

| Contract | File | Amendment |
|---|---|---|
| Phenotype.sol | `50-infra/etzhayyim-chain-contracts/src/Phenotype.sol` | Add `effectiveMultiplier()`, override `multiplier()` reads |
| KishaStream.sol | `50-infra/etzhayyim-chain-contracts/src/KishaStream.sol` | Read `effectiveMultiplier()` instead of `multiplier()` |
| PublicFundGovernance.sol | `50-infra/etzhayyim-public-fund/contracts/PublicFundGovernance.sol` | Add recipient + voter gate |
| TitheRouter.sol | `50-infra/etzhayyim-tithe-router/src/TitheRouter.sol` | Add recipient + payer gate |

## Lexicons (new — `00-contracts/lexicons/ai/gftd/apps/etzhayyim/`)

- `charter-attestation-request.json` — third-party non-aligned 認定要請
- `charter-attestation.json` — Council Lv6+ による non-aligned 認定 (3 sigs)
- `charter-appeal.json` — subject entity の反論 (30 day window)
- `charter-rehabilitation.json` — 復帰 (teshuvah) 宣言
- `charter-counsel-vote.json` — Council 内部 deliberation 記録

## Pregel cells (Tier B per [ADR-2605192415](../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md))

- `20-actors/magatama/cells/charter_attestation_request/` — MST listener → LLM analysis → Council dispatch
- `20-actors/magatama/cells/charter_attestation_finalization/` — timer + appeal window
- `20-actors/magatama/cells/charter_rehabilitation/` — teshuvah path

## Foundry layout (TODO)

```
src/
├── ChartersComplianceRegistry.sol
└── interfaces/
    ├── IAdherentRegistry.sol  (re-exports from 50-infra/etzhayyim-chain-contracts/)
    └── ICouncil.sol
test/
├── ChartersComplianceRegistry.t.sol
└── integration/
    └── ThreeTierEnforcement.t.sol  (Phenotype + KishaStream + PublicFund + TitheRouter)
script/
└── Deploy.s.sol
```

## Deploy targets

- Base L2 testnet (Sepolia, chainId 84532) — first
- geth-private (chainId 2605) — for constitutional layer
- Base L2 mainnet (chainId 8453) — after S0-S11 of ADR-2605192415
