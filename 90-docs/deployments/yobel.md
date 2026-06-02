---
id: deployment-yobel
title: Yobel Contract Deployments
status: pending-testnet-deploy
doc_type: deployment-runbook
topic: yobel-deployments
authoritative: true
last_verified: 2026-05-20
related:
  - adr-2605201800-etzhayyim-yobel-debt-release-actor
  - proposal-2605201800-yobel-ratification
  - 50-infra/etzhayyim-yobel-contract/script/Deploy.s.sol
---

# Yobel Contract Deployments

Per [ADR-2605201800](../adr/2605201800-etzhayyim-yobel-debt-release-actor.md) §Decision.
Contracts: `50-infra/etzhayyim-yobel-contract/`.

## Deployment ledger

| Network | Chain ID | Status | YobelRiteRegistry | YobelReleaseRegistry | Deployer | Verified |
|---|---|---|---|---|---|---|
| **Base Sepolia (testnet)** | 84532 | **pending** | `<address-after-deploy>` | `<address-after-deploy>` | TBD | TBD |
| **Base mainnet** | 8453 | blocked on Council Lv9 ratification of [proposal-2605201800-yobel-ratification](../governance/proposals/2605201800-yobel-ratification.md) | — | — | — | — |

## Pre-deployment checklist

### Base Sepolia (testnet)

- [x] Contracts compile clean (`forge build`)
- [x] All forge tests pass (`forge test`) — 28 tests + 1024-fuzz, 0 failures
- [x] Anvil integration tests pass (`pytest 20-actors/yobel/tests_integration -m integration`) — 4 tests
- [x] Deploy script reviewed (`script/Deploy.s.sol`)
- [ ] Deployer wallet funded with Base Sepolia ETH (≥ 0.05 ETH for both contracts + buffer)
- [ ] BASESCAN_API_KEY available for source verification
- [ ] BASE_SEPOLIA_RPC_URL set (Alchemy / Infura / public RPC)

### Base mainnet

- [ ] Council Lv9 ratification of yobel actor charter ([proposal-2605201800](../governance/proposals/2605201800-yobel-ratification.md)) complete + canonical signature set published
- [ ] Deployer is a Council Lv9 chair-signed Safe multisig (≥ 3-of-5 signers)
- [ ] Testnet deployment has been live for ≥ 14 days with no incidents
- [ ] At least one fixture rite (e.g. shmita 5786 testnet rehearsal) has been declared + ratified + a release recorded + supersession tested on testnet
- [ ] Vendor cross-actor wire (`recordYobelRiteReference`) has been integration-tested against testnet addresses
- [ ] Public Fund auditor has signed off on contract source + deployment plan

## Deployment commands

### Base Sepolia

```bash
cd 50-infra/etzhayyim-yobel-contract/

DEPLOYER_PRIVATE_KEY=0x...                       # NEVER a Lv9 chair key
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org \
BASESCAN_API_KEY=... \
forge script script/Deploy.s.sol \
  --rpc-url base_sepolia \
  --broadcast \
  --verify

# Expected output:
#   YobelRiteRegistry deployed at:     0xRRR...RRR
#   YobelReleaseRegistry deployed at:  0xSSS...SSS

# Verify on Basescan:
#   https://sepolia.basescan.org/address/0xRRR...RRR
#   https://sepolia.basescan.org/address/0xSSS...SSS
```

### Base mainnet (Safe multisig flow)

```bash
# 1. Prepare unsigned tx with foundry
DEPLOYER_PRIVATE_KEY=$SAFE_DEPLOYER_OPERATOR_KEY \
BASE_MAINNET_RPC_URL=https://mainnet.base.org \
forge script script/Deploy.s.sol \
  --rpc-url base_mainnet \
  --sig "run()" \
  --simulate \
  > tx-bundle.json

# 2. Submit tx-bundle.json to Safe (https://app.safe.global)
#    Requires ≥ 3-of-5 Council Lv9 chair-signed approvals

# 3. After Safe execution, run --resume to capture deployed addresses + verify
forge script script/Deploy.s.sol \
  --rpc-url base_mainnet \
  --resume \
  --verify
```

## Post-deployment steps

1. **Append addresses to this file** — replace `<address-after-deploy>` placeholders in the ledger above; commit + push
2. **Anchor deployment receipt** — call `EtzhayyimAnchor.anchor(rootHash, ipfsCid, batchSize=2)` where `rootHash = keccak256(abi.encode(YobelRiteRegistry, YobelReleaseRegistry, deploymentBlock))`, `ipfsCid` points to the verified Etherscan JSON
3. **Update orchestrator wiring** — `20-actors/yobel/orchestrator.py` constructor accepts a `chain_id` + `registry_address`; set via env at the deployer-defined value
4. **Update vendor bridge** — vendor:`70-tools/scripts/yobel-bridge/README.md` deployment table updated with the canonical testnet (and later mainnet) `yobelRiteRegistryAddress`
5. **Notify Public Fund auditor** — encrypted MST record under `com.etzhayyim.apps.etzhayyim.publicFund.deploymentAudit` per ADR-2605192145

## Rollback / emergency response

The deployed contracts have **no admin, no upgrade, no pause**. There is no on-chain rollback path. If a critical bug is discovered post-deployment:

1. **Immediate**: stop all off-chain handlers from calling the affected contract. Update the orchestrator + vendor bridge configs to point at a "frozen" empty address (effectively disabling new writes).
2. **Short-term**: emit `RiteSuperseded` for any compromised rite using the existing `supersedeRite` permissionless path. This is the on-chain way to mark state as quarantined.
3. **Long-term**: deploy a new contract version under a new yobel actor revision. Old contract state remains immutable on-chain forever (Charter §1.3 transparency); new state goes to the new contract.

## See also

- [ADR-2605201800](../adr/2605201800-etzhayyim-yobel-debt-release-actor.md)
- [Council ratification proposal](../governance/proposals/2605201800-yobel-ratification.md)
- [`50-infra/etzhayyim-yobel-contract/README.md`](../../50-infra/etzhayyim-yobel-contract/README.md)
- [`50-infra/etzhayyim-yobel-contract/script/Deploy.s.sol`](../../50-infra/etzhayyim-yobel-contract/script/Deploy.s.sol)
