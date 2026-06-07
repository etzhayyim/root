# etzhayyim-public-fund

`PublicFundGovernance.sol` + `MilestoneEscrow.sol` — 10% tithe の受け皿としての **grant 評議・配布機構**。

**Per [ADR-2605192145](../../90-docs/adr/2605192145-etzhayyim-public-fund-architecture.md)** (Public Fund Architecture).

## Architecture

```
[tithe 流入 (TitheRouter から)]
  → Public Fund Safe (Base L2 Gnosis Safe, 5-of-7 multisig)
  ↓ propose()
[PublicFundGovernance.sol]
  ↓ 1 SBT = 1 vote (quorum 20% / approval 50%)
  ↓ 48h timelock
  ↓ execute()
[disbursement]
  ├── 0xSplits (simple multi-recipient)
  └── MilestoneEscrow.sol (multi-stage gated by Council Lv6+)
```

## Governance

| Parameter | Value | Source |
|---|---|---|
| Safe signers | 5-of-7 | initial: founder + Bootstrap Council Lv6+ subset |
| Quorum | 20% of active SBTs | ADR-2605192145 §2 |
| Approval | 50% of cast votes | ADR-2605192145 §2 |
| Voting period | 7 days | ADR-2605192145 §2 |
| Timelock | 48 hours | ADR-2605192145 §2 |

## Mission axis hashes

Each grant proposal declares which Mission Charter axis it serves:

| Hash | Axis | Source |
|---|---|---|
| `keccak256("mission.labor_liberation")` | §1 | ADR-2605192100 |
| `keccak256("mission.robotics_universal")` | §1.4 | ADR-2605192100 |
| `keccak256("mission.ip_free_release")` | §1.5 | ADR-2605192100 |
| `keccak256("mission.disintermediation")` | §1.6 | ADR-2605192100 |
| `keccak256("mission.specialist_anti_gatekeeping")` | §1.7 | ADR-2605192100 |
| `keccak256("mission.land_stewardship")` | §1.11 | ADR-2605192100 |

Proposals not matching any axis are rejected by the LLM evaluator (`PublicFundGrantCell`).

## Charter Compliance gate (per ADR-2605192230)

`propose()` requires:
- `!charters.isNonAlignedAddress(recipient)` for every recipient

`vote()` requires:
- `!charters.isNonAlignedTokenId(sbtTokenId)` for the voter

## Foundry layout

```
contracts/
├── PublicFundGovernance.sol
├── MilestoneEscrow.sol
└── interfaces/
    ├── IAdherentRegistry.sol
    ├── ICouncil.sol
    └── IChartersComplianceRegistry.sol
test/
├── PublicFundGovernance.t.sol
└── MilestoneEscrow.t.sol
script/
└── Deploy.s.sol
```

## Pregel cell

`40-engine/kotoba/crates/kotoba-kotodama/cells/public_fund_grant/` — LLM-assisted evaluation of proposals:
- Mission axis match
- Rider compliance check
- Amount reasonableness vs Treasury NAV
- Proposer track record
- Similar past grant outcomes

Output: `com.etzhayyim.apps.public-fund.evaluation` record displayed in voting UI as advisory.

## Lexicons

- `00-contracts/lexicons/com/etzhayyim/apps/public-fund/proposal.json`
- `evaluation.json` (LLM advisory)
- `vote.json`
- `execution.json`
- `milestone-evidence.json`
- `milestone-attestation.json`
- `cancellation.json`

## Yield-bearing tier (S4)

Treasury Safe USDC excess can be tier-rebalanced into USDY / sDAI / aUSDC:

| Tier | Asset | % | Purpose |
|---|---|---|---|
| 流動 (liquid) | USDC | 30% | grant 即時配布 buffer |
| 準備 (reserve) | USDY / sDAI / aUSDC | 70% | yield 生成 |
| 本財 (corpus) | — | 0% | (Public Fund は流動 + 準備のみ。本財は 護持金庫 [ADR-2605172300] と Land Trust [ADR-2605192245] が保有) |

Rebalance proposals go through normal governance (`propose()` with mission axis = `treasury.rebalance`).
