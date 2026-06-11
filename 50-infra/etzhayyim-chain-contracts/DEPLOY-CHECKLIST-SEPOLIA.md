# Base Sepolia Testnet Deploy Checklist — Religious-Corp Wave

> Per ADR-2605192415 §10 roadmap (Step 19) and CLAUDE.md status table.
> Target: `ChartersComplianceRegistry.constructor()` called with the 5 Council addresses on Base Sepolia for final verification before mainnet.

## Status snapshot

| Item | State |
|---|---|
| 15 production contracts (`AdherentRegistry`, `ChartersComplianceRegistry`, `Constitution`, `ConstitutionKeys`, `TitheRouter`, `LandRegistry`, `PublicFundGovernance`, `ForceAuthorization`, …) | ✅ implemented |
| 14 Forge test suites / 126 tests | ✅ all passing |
| `DeployReligiousCorp.s.sol` `runLocal()` | ✅ Anvil verified (chainId 31337) per `90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md` |
| `DeployReligiousCorp.s.sol` `run(...)` parameterised | ✅ ready for Sepolia/mainnet |
| Bootstrap Council 5 addresses | 🟡 **1/5 filled** (founder) — RFP open until 2026-06-19, **gating constraint** |
| Public Fund 5-of-7 Safe address | ⏳ deploy before Step 19 |
| Funded Sepolia private key | ⏳ founder supplies |
| `BASESCAN_KEY` env | ⏳ obtain from basescan.org |

## Hard constraint (gate)

`ChartersComplianceRegistry.BOOTSTRAP_COUNCIL_SIZE = 5` (immutable). Deploy requires exactly 5 distinct Council addresses. **Step 19 cannot proceed until either:**

- (a) 4 candidate Council members fill Seats 2-5 via [Discussion #257](https://github.com/etzhayyim/root/discussions/257) before 2026-06-19, OR
- (b) Founder provisionally appoints per RFP §"What happens if all 5 seats don't fill" (Adherent SBT holders, subject to subsequent objection mechanism).

## Pre-deploy environment

```bash
# 1. Funded Sepolia private key (must hold ≥0.1 ETH on Sepolia)
export DEPLOYER_PRIVATE_KEY=0x<hex>

# 2. Base Sepolia RPC (default in foundry.toml works; override for Alchemy/Infura)
export ETZHAYYIM_PRIVATE_RPC=https://sepolia.base.org

# 3. Etherscan/Basescan API key for source verification
export BASESCAN_KEY=<basescan_api_key>

# 4. Addresses for runtime args
export USDC_SEPOLIA=0x036CbD53842c5426634e7929541eC2318f3dCF7e   # Circle USDC on Base Sepolia
export PUBLIC_FUND_SAFE=0x<gnosis_safe_address>                  # deploy 5-of-7 Safe first
export OFFICERS='[0x<officer1>,0x<officer2>,0x<officer3>]'        # AdherentRegistry seed
export COUNCIL_5='[0x<seat1>,0x<seat2>,0x<seat3>,0x<seat4>,0x<seat5>]'   # exactly 5
```

## Deploy command

```bash
cd 50-infra/etzhayyim-chain-contracts

# Dry-run (simulate only, no broadcast)
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "run(address,address[],address[],address)" \
  $USDC_SEPOLIA $OFFICERS $COUNCIL_5 $PUBLIC_FUND_SAFE \
  --rpc-url base_sepolia

# Live deploy + verify on basescan
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "run(address,address[],address[],address)" \
  $USDC_SEPOLIA $OFFICERS $COUNCIL_5 $PUBLIC_FUND_SAFE \
  --rpc-url base_sepolia --broadcast --verify
```

## Post-deploy verification

1. Record deployed addresses in `deps.toml` `[chain.base_sepolia]` section.
2. Verify contracts on https://sepolia.basescan.org for each address.
3. Smoke-test:
   - `cast call $CONSTITUTION 'getConstant(bytes32)' <K.ONE_SBT_ONE_VOTE>` → returns `0x...01`
   - `cast call $CHARTERS_REGISTRY 'councilMemberCount()' → returns 5`
   - `cast call $TITHE_ROUTER 'tithePctBps()' → returns 1000` (10%)
   - `cast call $LAND_REGISTRY 'totalLands()' → returns 0`
4. Bind governance (only after Phase 2 governance contract is also deployed):
   - `cast send $CHARTERS_REGISTRY 'bindGovernance(address)' $GOVERNANCE_ADDR`
5. Run integration test:
   - One donation via `TitheRouter.donate(USDC, amount, "donation")` → verifies 10% auto-split to PublicFund Safe.
6. Open ADR `90-docs/adr/<ts>-etzhayyim-base-sepolia-deploy.md` documenting addresses + tx hashes + verification links.

## Rollback / re-deploy

- Sepolia is throwaway — re-deploy is free. If a contract has a known bug, fix → bump test → re-deploy. Old deployment can be marked deprecated in `deps.toml`.

## Estimated calendar

- Council fill: 2026-06-19 (deadline)
- 5-of-7 Safe deploy: 0.5 day
- Officers + ABI assembly: 0.5 day
- Sepolia deploy + verify: 0.5 day
- Smoke + integration: 1 day
- ADR write-up: 0.5 day
- **Total post-Council: 2-3 days**

## References

- ADR-2605192415 §10 (deploy roadmap)
- ADR-2605192300 (Council Lv6+ mechanics)
- [`COUNCIL-BOOTSTRAP-RFP.md`](../../COUNCIL-BOOTSTRAP-RFP.md)
- `90-docs/adr/2605192100-etzhayyim-mission-charter.md` §1 (constitutional invariants)
- Base Sepolia faucet: https://docs.base.org/tools/network-faucets
