# Base Mainnet Deploy Checklist — Religious-Corp Wave

> Per ADR-2605192415 §10 roadmap (Step 20). Mainnet deploy is gated on successful Base Sepolia testnet verification (Step 19) plus an external security review.

## Pre-conditions (all must be ✅)

- [ ] Step 19 Base Sepolia deploy verified (see `DEPLOY-CHECKLIST-SEPOLIA.md`)
- [ ] Sepolia integration runs for ≥ 30 days with no critical findings
- [ ] All 5 Council Lv6+ seats confirmed in `COUNCIL.md`, signers verified
- [ ] Public Fund 5-of-7 Safe deployed on Base mainnet, signer list published
- [ ] External Solidity audit completed (suggested firms aligned with §2(a)-(h): non-VC-aligned, ethical-source-aware — e.g. Spearbit / Code4rena / OpenZeppelin self-audit with public report)
- [ ] All audit High/Critical findings resolved + auditor re-attestation
- [ ] `gh release` cut of audited commit hash on `etzhayyim/root` (immutable reference)
- [ ] L2 anchor + IPFS pin operational (`50-infra/etzhayyim-did-web/` Live since 2026-05-17; `mst-projector` Stage 3)
- [ ] Council multisig key custody documented (each signer holds keys via DID-bound passkey + 1Password mirror, per ADR-2605181100 confidentiality)
- [ ] Phase 2 governance ADR drafted (for transition trigger thresholds per RFP §"Phase 2")

## Hard constraints

- `BOOTSTRAP_COUNCIL_SIZE = 5` (immutable) — same gate as Sepolia
- `MIN_COUNCIL_SIGNERS = 3` — minimum signers per attestation
- `APPEAL_WINDOW = 30 days` — Charter appeals freeze period
- `Constitution.LICENSE = "Apache-2.0"` — non-amendable (Charter Rider invariant)
- Land donations are **inalienable** — no `transfer/burn/setOwner` in `LandRegistry.sol`
- `TitheRouter` 10% auto-split to PublicFund — non-amendable

## Pre-deploy environment

```bash
# 1. Funded mainnet private key (cold storage; one-time use)
export DEPLOYER_PRIVATE_KEY=0x<hex>   # ≥0.2 ETH on Base mainnet

# 2. RPC — production endpoint (Alchemy/Infura recommended; avoid public)
export BASE_RPC=https://base-mainnet.g.alchemy.com/v2/<key>

# 3. Etherscan/Basescan
export BASESCAN_KEY=<key>

# 4. Addresses (all production)
export USDC_MAINNET=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913   # Circle USDC on Base mainnet
export PUBLIC_FUND_SAFE=0x<5_of_7_Safe>
export OFFICERS='[<officer_addresses>]'
export COUNCIL_5='[<5_council_addresses>]'
```

## Deploy command (rehearsed via Sepolia first)

```bash
cd 50-infra/etzhayyim-chain-contracts

# 1. Dry-run against a mainnet fork (Tenderly / Foundry --fork-url)
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "run(address,address[],address[],address)" \
  $USDC_MAINNET $OFFICERS $COUNCIL_5 $PUBLIC_FUND_SAFE \
  --fork-url $BASE_RPC

# 2. Multi-sig protected broadcast (use Foundry --account from hardware-wallet integration if applicable)
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "run(address,address[],address[],address)" \
  $USDC_MAINNET $OFFICERS $COUNCIL_5 $PUBLIC_FUND_SAFE \
  --rpc-url base --broadcast --verify --slow
```

## Post-deploy

1. Record deployed addresses in `deps.toml` `[chain.base_mainnet]` section.
2. Sign + publish a `did:web:etzhayyim.com` JSON-LD release announcement linked from `/.well-known/did.json`.
3. PR to `COUNCIL.md` adding the canonical chain addresses to each Council member's record.
4. Cut a `git tag v1.0.0-mainnet` against the audited commit.
5. ADR `90-docs/adr/<ts>-etzhayyim-base-mainnet-deploy.md` with:
   - All deployed addresses + tx hashes + basescan links
   - Audit report PDF/IPFS CID
   - 30-day Sepolia operational summary
   - Council attestation list (each signer's DID + ERC-4337 Smart Account proof)
6. Bind Phase 2 governance (after the Phase 2 ADR ratification):
   - `cast send $CHARTERS_REGISTRY 'bindGovernance(address)' $GOVERNANCE_MAINNET`
7. First production donation (founder symbolic) → verify TitheRouter behaviour end-to-end.

## Rollback

- Mainnet deploys are immutable. There is no rollback.
- If a contract has a critical bug post-deploy:
  - `Constitution` mutables (16 of 54) can be updated via Council 3-of-5 multisig
  - Constants (38 of 54) require a new constitutional ADR + replacement contract deploy + governance migration
  - Funds in `PublicFundGovernance` can be recovered via 5-of-7 Safe
  - `LandRegistry` records are inalienable — emergency boundary disputes go through Council deliberation per ADR-2605192245

## Estimated calendar

- Sepolia operational 30-day window: 2026-06-19 → 2026-07-19 (post-Council)
- External audit: 4-6 weeks (parallelisable with Sepolia operational window if scoped early)
- Audit finding resolution: 1-2 weeks
- Mainnet deploy + verify + ADR: 1 week
- **Total post-Council: 8-12 weeks**

## References

- ADR-2605192415 §10 (deploy roadmap)
- ADR-2605192100 (Mission Charter, constitutional invariants)
- ADR-2605192200 (Apache 2.0 + Charter Compliance Rider v2.0)
- ADR-2605192300 (Bootstrap Council mechanics)
- `50-infra/etzhayyim-chain-contracts/test/` — 126-test suite (must remain green at deploy commit)
- Base mainnet docs: https://docs.base.org/network-information
