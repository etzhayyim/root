# DEPLOY-CHECKLIST — Religious-Corp Wave testnet → mainnet

Operator checklist for taking the religious-corp wave from local Anvil (✅ done 2026-05-20) to Base Sepolia testnet then to Base mainnet. Per ADR-2605192415 §10 + RUNBOOK-deploy.md §"Religious-Corp Wave Deploy".

## Prerequisites (one-time setup)

- [ ] **Foundry installed** — `forge --version` returns >= 1.5.0
- [ ] **`.env` populated** from `.env.example` (cp + edit; never commit)
- [ ] **Funded deployer key** — Base Sepolia: ~0.05 ETH (faucet: https://faucet.quicknode.com/base/sepolia); Base mainnet: ~0.05 ETH
- [ ] **BASESCAN_KEY** obtained from basescan.org (for `--verify`)
- [ ] **PUBLIC_FUND_SAFE_ADDRESS** deployed (see §2 below — MUST precede contract deploy)
- [ ] **BOOTSTRAP_COUNCIL** finalized (5 addresses, post-2026-06-19 RFP per `COUNCIL-BOOTSTRAP-RFP.md`)

## §1 — Local Anvil smoke (verification baseline)

```bash
cd 50-infra/etzhayyim-chain-contracts

# Verify Foundry + tests
forge build
forge test         # should print "110 tests passed"

# Anvil deploy (already-verified pattern from 2026-05-20)
anvil --silent > /tmp/anvil.log 2>&1 &
ANVIL_PID=$!
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "runLocal()" \
  --rpc-url http://localhost:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
kill $ANVIL_PID
```

- [ ] Deploy completes with "ONCHAIN EXECUTION COMPLETE & SUCCESSFUL."
- [ ] 6 addresses logged at end (Constitution / AdherentRegistry / ChartersComplianceRegistry / TitheRouter / LandRegistry / PublicFundSafe)
- [ ] No revert / no compilation error

## §2 — Public Fund Safe deploy on Base

The 5-of-7 Gnosis Safe MUST exist before the religious-corp wave can deploy (TitheRouter takes it as constructor immutable per v0).

### Signer selection (5-of-7)

7 distinct Smart Wallets, 5 required to sign each disbursement transaction:

| # | Role | Selection criteria |
|---|---|---|
| 1 | Founder | Jun Kawasaki (= Council Seat 1) |
| 2-5 | Council Lv6+ subset | 4 of the 5 Bootstrap Council members (Seats 2-5) |
| 6 | External advisor | Adherent SBT holder, Lv5+ 護, recognized religious authority external to founder's network |
| 7 | Emergency multisig | Cold storage key under founder's control, geographic offsite |

Rationale: 5-of-7 means losing 1 founder + 1 Council member still allows quorum. Threshold = ceil(7 * 0.6) = 5 per ADR-2605192145 §1.

### Safe deploy steps

1. Open https://app.safe.global/ in the founder's Smart Wallet context
2. Select chain: **Base Sepolia** (for testnet) or **Base** (mainnet)
3. Click "Create new Safe Account"
4. Owners: paste 7 addresses (in fixed order — record off-chain)
5. Threshold: 5
6. Review + execute (founder's Smart Wallet pays ~$0.50 worth of ETH for Base Sepolia, ~$5 for mainnet)
7. **Record Safe address** in `.env` as `PUBLIC_FUND_SAFE_ADDRESS`

- [ ] Safe deployed on target chain
- [ ] 7 signer addresses confirmed in Safe owners list
- [ ] Threshold = 5 confirmed
- [ ] PUBLIC_FUND_SAFE_ADDRESS env populated

## §3 — Testnet deploy (Base Sepolia)

### 3.1 USDC

For Base Sepolia we recommend using **Circle native USDC** (`0x036CbD53842c5426634e7929541eC2318f3dCF7e`) — request via https://faucet.circle.com/. Alternative: deploy `MockUsdc.sol` via forge for a fully self-contained smoke (no Circle faucet dependency).

```bash
# Option A: use Circle's Sepolia USDC
export USDC_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

# Option B: deploy MockUsdc to Sepolia
forge create script/MockUsdc.sol:MockUsdc \
  --rpc-url base_sepolia --private-key $PRIVATE_KEY
# Use the printed address as USDC_ADDRESS
```

- [ ] USDC_ADDRESS set

### 3.2 Deploy religious-corp wave

```bash
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "run(address,address[],address[],address)" \
  $USDC_ADDRESS \
  "[$INITIAL_OFFICERS]" \
  "[$BOOTSTRAP_COUNCIL]" \
  $PUBLIC_FUND_SAFE_ADDRESS \
  --rpc-url base_sepolia \
  --broadcast \
  --verify
```

- [ ] All 5 contracts deployed
- [ ] All 5 addresses recorded in `.env`
- [ ] Etherscan verification successful for each (Basescan link in output)

### 3.3 Verification on testnet

```bash
# Verify constitutional constants
cast call $CONSTITUTION_ADDRESS \
  "getConstant(bytes32)(bytes32)" \
  $(cast keccak "economic.tithe_to_public_fund_bps") \
  --rpc-url base_sepolia
# expect: 0x...3e8

# Verify council bootstrap
cast call $CHARTERS_COMPLIANCE_REGISTRY_ADDRESS \
  "councilMemberCount()(uint256)" \
  --rpc-url base_sepolia
# expect: 5

# Verify a council member
cast call $CHARTERS_COMPLIANCE_REGISTRY_ADDRESS \
  "isCouncilMember(address)(bool)" \
  <council-1-addr> \
  --rpc-url base_sepolia
# expect: true
```

- [ ] 10+ constitutional constants verified via cast (sample at least 4 from different categories)
- [ ] Council bootstrap state verified
- [ ] PublicFundSafe address persisted to Constitution mutables

### 3.4 First attestation rehearsal (no-cost smoke)

Drive a fake attestation through the contracts:

```bash
# As council member 1: attest a known address as non-aligned
cast send $CHARTERS_COMPLIANCE_REGISTRY_ADDRESS \
  "attestNonAlignedAddress(address,bytes32,bytes32,bytes[],address[])" \
  0xACME...  $(cast keccak "rider.section_2g") $(cast keccak "evidence-rehearsal") \
  "[$SIG1,$SIG2,$SIG3]" \
  "[$COUNCIL1,$COUNCIL2,$COUNCIL3]" \
  --rpc-url base_sepolia --private-key $PRIVATE_KEY

# Verify state
cast call $CHARTERS_COMPLIANCE_REGISTRY_ADDRESS \
  "attestationsByAddress(address)(uint8,bytes32,bytes32,uint64,uint64,bool)" \
  0xACME... --rpc-url base_sepolia
```

- [ ] Attestation tx succeeded
- [ ] Status = UnderReview (uint8 = 2)
- [ ] AppealDeadline = effectiveAt + 30 days

## §4 — Mainnet deploy (Base)

Only after §3 has been completed with no surprises. Time-gate at least 7 days between testnet completion and mainnet deploy to allow operational review.

### 4.1 Mainnet USDC

```bash
export USDC_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913   # Coinbase Bridged USDC on Base
```

### 4.2 Deploy

Same command as §3.2 but `--rpc-url base` (mainnet).

- [ ] Gas estimate confirmed reasonable (`forge script --simulate-only` first)
- [ ] All 5 contracts deployed on Base mainnet
- [ ] Etherscan verification successful

### 4.3 Phase 2 governance wiring

After mainnet contracts are deployed + Governance contract is bound to Constitution (per RUNBOOK Step 3 of the original wave):

```
Governance proposal payload:
  to: Constitution
  calldata: setMutable(keccak256("charters_compliance.registry_address"), bytes32(uint160(CHARTERS_COMPLIANCE_REGISTRY_ADDRESS)))
  + setMutable for tithe_router.address, land_registry.address, force_authorization.address, public_fund.governance_address
```

Submit → vote (1 SBT = 1 vote, quorum 33%) → 72h timelock → execute.

- [ ] Phase 2 references wired (5 mutables)
- [ ] Verified via cast call getMutable

## §5 — Post-deploy operations

- [ ] AppView at religious-corp.etzhayyim.com / fund.etzhayyim.com / lands.etzhayyim.com pointed at mainnet addresses
- [ ] kotodama-cell-runner deployed to Murakumo fleet with mainnet addresses
- [ ] Founder mints first Adherent SBT (AdherentRegistry.join via SDK)
- [ ] First test donation via SDK Etzhayyim.pay() → verify TitheRouter splits 90/10
- [ ] First test Public Fund proposal submission

## Rollback

Religious-corp wave contracts are immutable. To "roll back" testnet, redeploy with corrected constants; the old contracts remain on chain as historical. For mainnet, the same applies but with the added consideration of any Tithe routing or Charter Compliance attestation state that may need to be migrated; Council Lv6+ deliberation required for non-trivial mainnet rollback.
