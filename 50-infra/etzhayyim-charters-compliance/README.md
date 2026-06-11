# etzhayyim-charters-compliance

> **NOTE (2026-05-20)**: `ChartersComplianceRegistry.sol` was moved to
> [`../etzhayyim-chain-contracts/src/ChartersComplianceRegistry.sol`](../etzhayyim-chain-contracts/src/ChartersComplianceRegistry.sol)
> for unified Foundry project / deploy script integration. Tests, build,
> and deploy live there. This directory is retained as the canonical
> design reference + future AppView home.

`ChartersComplianceRegistry.sol` — Council attestation の単一 source of truth。

**Per [ADR-2605192230](../../90-docs/adr/2605192230-etzhayyim-three-tier-enforcement-implementation.md)** (Three-Tier Enforcement Implementation) + [ADR-2605192200](../../90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md) (Charter Rider v2.0) + [ADR-2605192300](../../90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md) (Bootstrap Council 5名).

## Architecture

```
ChartersComplianceRegistry (Base L2 + geth-private)
  │
  ├── attestationsByAddress[address] → Attestation
  ├── attestationsByTokenId[uint256] → Attestation
  │
  ├── isCouncilMember[address]      ← bootstrap from 5 founder-proposed seats
  ├── councilMemberCount             ← 5 at bootstrap; mutable via setCouncilMember (Phase 2)
  ├── bindGovernance(addr)           ← one-shot binding for Phase 2 mutations
  │
  ├── attestNonAlignedAddress()      ← Council ≥3 multisig
  ├── attestNonAlignedTokenId()      ← Council ≥3 multisig
  ├── acceptAppeal()                 ← Council ≥3 multisig
  ├── rehabilitate()                 ← Council ≥3 (teshuvah, ADR-2605192230 §7)
  ├── finalize()                     ← anyone, after 30-day appeal window
  │
  ├── isNonAlignedAddress(addr)      ← public view (read by other contracts)
  └── isNonAlignedTokenId(id)        ← public view
```

## Status

| Layer | enforcement | Mechanism |
|---|---|---|
| L1 License | software 使用権失効 | Rider §3 + Apache 2.0 §3 termination |
| L2 便益拒否 | Kisha + Public Fund 受給不可 | `Phenotype.effectiveMultiplier() → 0` + `PublicFundGovernance.propose() require !nonAligned` + `TitheRouter.route() require !nonAligned` |
| L3 評価最低 | Phenotype multiplier = 0 | constitutional override in `Phenotype.sol` |

## Build + Test + Deploy

All under [`../etzhayyim-chain-contracts/`](../etzhayyim-chain-contracts/):

```bash
cd ../etzhayyim-chain-contracts
forge build
forge test --match-contract ChartersComplianceRegistry   # 12 tests
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "runLocal()" --rpc-url http://localhost:8545 --broadcast --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

See [`RUNBOOK-deploy.md`](../etzhayyim-chain-contracts/RUNBOOK-deploy.md) §"Religious-Corp Wave Deploy" for the full Base Sepolia + mainnet sequence.

## Bootstrap Council mechanics

Constitutional constraint: exactly 5 council members at deploy time (per ADR-2605192300). Constructor reverts with `BootstrapSizeMismatch` if `bootstrapCouncil.length != 5` or `DuplicateBootstrapMember` if any address appears twice.

Phase 2 (post 1000-member or 12-month trigger per ADR-2605192300 §4) graduates to formal Council via:

1. `Constitution.bindGovernance(governance)` (already done from original wave)
2. `ChartersComplianceRegistry.bindGovernance(governance)` (one-shot)
3. Governance proposal → `setCouncilMember(newAddr, true)` per added member
4. Deprecated members: `setCouncilMember(oldAddr, false)`

## Pregel cells (Tier B per [ADR-2605192415](../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md))

- [`40-engine/kotoba/crates/kotoba-kotodama/cells/charter_attestation_request/`](../../40-engine/kotoba/crates/kotoba-kotodama/cells/charter_attestation_request/) — MST listener → LLM analysis → Council dispatch
- `40-engine/kotoba/crates/kotoba-kotodama/cells/charter_attestation_finalization/` — timer + appeal window
- `40-engine/kotoba/crates/kotoba-kotodama/cells/charter_rehabilitation/` — teshuvah path

## Lexicons

- [`00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/charter-attestation-request.json`](../../00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/charter-attestation-request.json)
- `charter-attestation.json`
- `charter-appeal.json`
- `charter-rehabilitation.json`
- `charter-counsel-vote.json`
