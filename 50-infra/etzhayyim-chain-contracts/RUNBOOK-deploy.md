# RUNBOOK — etzhayyim chain-contracts deploy + bootstrap

S5 of [ADR-2605172300](../../90-docs/adr/2605172300-etzhayyim-bi-asset-substrate.md). Walkthrough for bringing the full kisha (basic-income) + goji (asset) substrate from cold to live.

**Audience**: deployer with access to a geth-private validator key + a Base RPC + an env where `forge` is installed + the founder Smart Wallet keys.

**Prerequisites**:
- geth-private chain online, ChainID `2605`, Clique PoA, at least 3 validators.
- Base L2 (mainnet or sepolia) RPC + a USDC-funded Treasury Safe (Gnosis Safe, 役員 multisig).
- `forge install foundry-rs/forge-std --no-commit` already run in this directory.
- Founder DIDs resolved (did:web / did:plc) and Smart Account addresses derived per [ADR-2605172100](../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md).

---

## Sequence overview

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Deploy internal stack (geth-private)                      │
│ 2. Deploy KishaPayout (Base)                                 │
│ 3. Constitution.bindGovernance(governance)                   │
│ 4. Founder officers mint their own SBTs                      │
│ 5. Founder officers each attest once (→ isActive true)       │
│ 6. Bootstrap governance proposal (multi-call)                │
│ 7. Vote (founders FOR until quorum)                          │
│ 8. Wait 72h timelock                                         │
│ 9. Execute bootstrap proposal — system live                  │
│ 10. (legal-review-contingent) Corpus tier first holdings     │
└─────────────────────────────────────────────────────────────┘
```

Until step 9 completes, kisha accrual is "live" but the phenotype layer is dormant (multiplier defaults to 1.0×) and the NAV oracle is unregistered (envelope = 0). That is the intended bootstrap-safe state.

---

## Step 1 — Deploy internal stack (geth-private)

```bash
cd 50-infra/etzhayyim-chain-contracts

forge script script/Deploy.s.sol:Deploy \
  --sig "runInternal(address[])" "[<OFFICER_1>, <OFFICER_2>, <OFFICER_3>]" \
  --rpc-url etzhayyim_private \
  --broadcast \
  --private-key $DEPLOYER_KEY
```

`runInternal` deploys:
- `Constitution` (with S0 default constants + mutables; see `script/Deploy.s.sol` `_constants()` and `_mutables()`)
- `AdherentRegistry` with the supplied initial officers
- `KishaStream`, `Phenotype`, `AnchorBridge`, `Governance`, `TreasuryMirror`, `CorpusRegistry`, `HoldingAttestation`

Take note of the addresses printed at the end (`--- etzhayyim chain-contracts (geth-private) ---`). Pipe them to a file:

```bash
forge script ... 2>&1 | tee deploy-internal.log
```

**Genesis defaults** (from `_constants()` / `_mutables()`):
- `kisha_base_rate` = 1 USDC/day (6-decimal base units = 1_000_000)
- `kappa_bps` = 300 (3.00%)
- Tier ratios = 10% liquid / 60% reserve / 30% corpus
- `quorum_bps` = 3_300 (33%); floor = 2_000 (20%)
- `active_window_secs` = 30 days
- `timelock_secs` = 72h
- Phenotype band = 5_000..20_000 bps (0.5x..2.0x)
- κ band = 100..500 bps (1.00%..5.00%)

If any of these need to change at genesis, edit `_constants()` / `_mutables()` before deploying. After deploy, mutables can be changed via governance proposal.

---

## Step 2 — Deploy KishaPayout (Base)

The Base side is independent of the geth-private side. The Treasury Safe must be configured separately (Gnosis Safe with 3-of-5 役員 signers; outside this RUNBOOK).

```bash
forge script script/Deploy.s.sol:Deploy \
  --sig "runBase(address,address,address,address[],uint8)" \
    "<USDC_BASE>" "<TREASURY_SAFE>" "<KISHA_STREAM_ADDR_FROM_STEP_1>" \
    "[<RELAYER_1>, <RELAYER_2>, <RELAYER_3>]" 2 \
  --rpc-url base \
  --broadcast \
  --private-key $DEPLOYER_KEY
```

Canonical values:
- `USDC_BASE` = `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` (Coinbase Bridged on Base, per [ADR-2605172100](../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md))
- `THRESHOLD` = 2 (out of 3 initial relayers)
- The KishaStream address is **a label only** — KishaPayout does not RPC across chains. It is used in `keccak(stream, tokenId, seq)` to derive ticketIds.

**Treasury Safe must then approve KishaPayout for USDC**:

```js
// from a Safe signer wallet on Base, via Safe UI or script:
usdc.approve(kishaPayout, INITIAL_MONTHLY_ENVELOPE);
```

`INITIAL_MONTHLY_ENVELOPE` should be conservative — a single month of the targeted disbursement. The Safe re-approves periodically as the envelope grows.

---

## Step 3 — Bind Governance to Constitution

```bash
forge script script/Deploy.s.sol:Deploy \
  --sig "bindGovernance(address,address)" \
    "<CONSTITUTION>" "<GOVERNANCE>" \
  --rpc-url etzhayyim_private \
  --broadcast \
  --private-key $DEPLOYER_KEY
```

`bindGovernance` is permissionless and one-shot. From this point on, `Constitution.setMutable` and every governance-gated setter (`KishaStream.setBaseRate`, `Phenotype.registerCell`, `TreasuryMirror.registerOracle`, etc.) require a call from the deployed Governance contract — i.e., an executed governance proposal.

---

## Step 4 — Founder officers mint their own SBTs

Each founder needs an SBT to vote. Officers can mint for each other (officer-relayed). Easiest pattern: one officer mints all founder SBTs in a single tx batch.

```js
// from OFFICER_1's wallet, on geth-private:
await adherentRegistry.join(OFFICER_1, "did:web:founder1.etzhayyim.com", joinAttestationCid1);
await adherentRegistry.join(OFFICER_2, "did:web:founder2.etzhayyim.com", joinAttestationCid2);
await adherentRegistry.join(OFFICER_3, "did:web:founder3.etzhayyim.com", joinAttestationCid3);
```

The `joinAttestationCid` is the keccak hash of the IPFS CID pointing at the creed-acceptance document. The document itself follows ADR-2605172600 oath conventions: signed by the founder's DID key, written to their PDS as `com.etzhayyim.apps.etzhayyim.oath`. See [the reconciliation ADR-2605172700](../../90-docs/adr/2605172700-membership-layering-shinto-adherent.md) for the layering between 信者 (172600) and Adherent (172300 S0) tiers — every founder is by definition both.

---

## Step 5 — Founder attestations (→ isActive true)

`AdherentRegistry.isActive(tokenId, 30 days)` returns false until the holder has attested at least once. Each founder calls:

```js
await adherentRegistry.attest(tokenId, keccak256("prayer"), evidenceCid);
```

`evidenceCid` may be `bytes32(0)` if no evidence is published. After this call the founder is voting-eligible.

---

## Step 6 — Bootstrap governance proposal

A single founder proposes a multi-call that wires up the post-deploy state:

```solidity
// rationale: "Bootstrap: bind Phenotype, register the initial eligibility cell,
// register the initial NAV oracle, and acknowledge KishaPayout on Base."

targets[0] = address(kishaStream);
calldatas[0] = abi.encodeWithSelector(KishaStream.setPhenotype.selector, address(phenotype));

targets[1] = address(phenotype);
calldatas[1] = abi.encodeWithSelector(
    Phenotype.registerCell.selector, INITIAL_CELL_ADDR, keccak256("bootstrap-cell-0")
);

targets[2] = address(treasuryMirror);
calldatas[2] = abi.encodeWithSelector(
    TreasuryMirror.registerOracle.selector, INITIAL_ORACLE_ADDR, keccak256("bootstrap-oracle-0")
);

governance.propose(targets, calldatas, keccak256("bootstrap-rationale-cid"));
```

The cell and oracle addresses correspond to:
- **Cell**: the EOA whose private key is held by the Pregel runtime running `kotodama.eligibility.cell.EligibilityCell` (S2).
- **Oracle**: the EOA whose private key is held by the off-chain NAV poller that watches the Treasury Safe on Base and posts updates to `TreasuryMirror.updateNAV` (S3).

---

## Step 7 — Vote

Founders cast votes:

```js
// each founder, on geth-private:
await governance.castVote(proposalId, 1); // 1 = for
```

`Governance.state(proposalId)` transitions to `Succeeded` once the voting period ends (3 days) provided quorum holds (33% of `AdherentRegistry.totalMinted`). With 3 founders, that's 1 voter for quorum and a majority — easy.

---

## Step 8 — Queue + wait 72h

```js
await governance.queue(proposalId); // anyone can call
```

`Governance.state(proposalId)` transitions to `Queued` with `eta = block.timestamp + 72h`. After 72h, any account (including a non-member) may execute the proposal.

---

## Step 9 — Execute

```js
await governance.execute(proposalId);
```

Dispatches the three calls. `KishaStream.phenotype` becomes the deployed `Phenotype` address; the initial cell address is registered; the initial NAV oracle is registered. **System is live**: adherents can now `attest()` → cell computes phenotype → `KishaStream.previewAccrued()` returns multiplier-aware values → adherents `claim()` → relayer fulfills on Base via `KishaPayout`.

---

## Step 10 — Corpus tier (legal-review-contingent)

**Do not execute Step 10 in production until a Japan-jurisdiction lawfirm has reviewed the holding-attestation document template.** See the NatSpec on `CorpusRegistry.sol` + `HoldingAttestation.sol`.

When the legal review clears:

1. Governance proposal sets `HoldingAttestation.docTemplateCid` + `lawfirmReviewCid` to the IPFS CIDs of the approved template and the lawfirm opinion.
2. The 代表者 signs a holding attestation off-chain (the canonical document) and submits it on-chain:
   ```js
   await holdingAttestation.attest(repAddr, repDid, assetUriHash, docHash, sig);
   ```
3. Governance proposal mints the corpus token referencing the attestation:
   ```js
   await corpusRegistry.mint(
     CorpusRegistry.KIND_FACILITY, // or REAL_PROPERTY / IP / RWA_TOKEN
     repDid,
     keccak256("JP-13"),  // jurisdiction
     attestationId,        // = HoldingAttestation.payloadHash returned by step 2
     contentCid            // IPFS CID hash of the notarized document bundle
   );
   ```

Disposition (sale / transfer) requires a separate governance proposal calling `CorpusRegistry.setLock(tokenId, false)` followed by an off-chain transfer + `CorpusRegistry.flagDisposed(tokenId, reasonCid)`.

---

## Verification checklist

After Step 9:

- [ ] `Constitution.governance()` returns the deployed Governance address
- [ ] `AdherentRegistry.totalMinted()` ≥ founder count
- [ ] Each founder's `AdherentRegistry.isActive(tokenId, 30 days)` returns true
- [ ] `KishaStream.phenotype()` returns the deployed Phenotype address (not zero)
- [ ] `Phenotype.isCell(<INITIAL_CELL>)` returns true
- [ ] `TreasuryMirror.isOracle(<INITIAL_ORACLE>)` returns true
- [ ] Base side: `KishaPayout.threshold()` = 2; `KishaPayout.relayerCount()` = 3
- [ ] Base side: `IERC20(USDC).allowance(Treasury Safe, KishaPayout)` ≥ initial envelope
- [ ] Block explorer snapshot saved (geth-private RPC + basescan.org links)

## Rollback

The contracts are immutable. There is no upgrade path or pause. To "roll back", deploy a fresh stack with corrected constants, point external tooling (anchor relayer, eligibility cell, oracle, SDK config) at the new addresses. Old contracts remain as historical record; no funds are at risk on the geth-private side, and on the Base side the Treasury Safe's USDC allowance is the only money exposure (revoke via Safe to fully neuter the old KishaPayout).

---

# Religious-Corp Wave Deploy (ADRs 2605192100..2605192415)

S2 of [ADR-2605192415](../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md) §10 roadmap. Deploys the religious-corp constitutional wave on top of the kisha + goji substrate above.

**Adds to the deploy**:

- **Constitution** loaded with 38 constants + 16 mutables (vs original 8 + 8) including all Mission Charter doctrine
- **ChartersComplianceRegistry**: 5-member bootstrap Council (per ADR-2605192300) + 3-tier enforcement
- **TitheRouter**: 10% atomic split of donations → Public Fund Safe
- **LandRegistry**: 4-layer Land Trust with constitutional inalienability (transfer/burn-disabled)

(Stubs forthcoming: PublicFundGovernance, ForceAuthorization — scheduled for S4–S7.)

## Step R1 — Identify deploy inputs

You need:

```
USDC                 = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913   # Base mainnet USDC
                                                                    # (testnet: deploy MockUsdc)
initialOfficers      = [0xfounder, ...]                              # founder + co-founders
bootstrapCouncil[5]  = [seat1_founder, seat2_substrate, seat3_legal, seat4_economics, seat5_steward]
publicFundSafe       = 0x...                                         # 5-of-7 Gnosis Safe on Base
                                                                    # (deploy via Safe app first)
```

`bootstrapCouncil` ordering is significant — record it in the deploy log + LANDS-style PR.

## Step R2 — Deploy via script

```bash
cd 50-infra/etzhayyim-chain-contracts

# Base Sepolia (testnet)
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "run(address,address[],address[],address)" \
  $USDC \
  "[$OFFICER1,$OFFICER2]" \
  "[$C1,$C2,$C3,$C4,$C5]" \
  $PUBLIC_FUND_SAFE \
  --rpc-url base_sepolia \
  --broadcast \
  --verify

# Base mainnet (production)
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "run(address,address[],address[],address)" \
  ... \
  --rpc-url base \
  --broadcast \
  --verify
```

Record the 5 deployed addresses + publicFundSafe in `deps.toml [platform.l2.religious_corp_wave]`.

## Step R3 — Local Anvil smoke test

For PR validation before any testnet expenditure:

```bash
anvil --silent &
forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
  --sig "runLocal()" \
  --rpc-url http://localhost:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

**Anvil deterministic deployment** produces fixed addresses (chainId 31337, deployer = Anvil account 0):

```
Constitution                  0x5FbDB2315678afecb367f032d93F642f64180aa3
AdherentRegistry              0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
ChartersComplianceRegistry    0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0
TitheRouter                   0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9
LandRegistry                  0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9
PublicFundSafe                0x976EA74026E726554dB657fA54763abd0C3a0aa9   (Anvil account 6)
```

## Step R4 — Verification

After deploy (any environment), verify the constitutional constants landed correctly:

```bash
# Constitutional constant: 10% tithe to Public Fund
cast call $CONSTITUTION \
  "getConstant(bytes32)(bytes32)" \
  $(cast keccak "economic.tithe_to_public_fund_bps") \
  --rpc-url <rpc>
# expect: 0x...03e8 (= uint256 1000)

# Non-eschatological religion: revelation NOT in canon
cast call $CONSTITUTION \
  "getConstant(bytes32)(bytes32)" \
  $(cast keccak "mission.revelation_in_canon") \
  --rpc-url <rpc>
# expect: 0x...0 (false)

# Religious ontology: anti_individualism
cast call $CONSTITUTION \
  "getConstant(bytes32)(bytes32)" \
  $(cast keccak "mission.anti_individualism") \
  --rpc-url <rpc>
# expect: 0x...1 (true)

# Rider version
cast call $CONSTITUTION \
  "getConstant(bytes32)(bytes32)" \
  $(cast keccak "license.charter_rider_version") \
  --rpc-url <rpc>
# expect: 0x76322e30... (ascii "v2.0" padded)

# Council bootstrap
cast call $CHARTERS_COMPLIANCE \
  "councilMemberCount()(uint256)" \
  --rpc-url <rpc>
# expect: 5
```

All four constants verified ✓ on local Anvil 2026-05-20.

## Step R5 — Phase 2 governance wiring (post-deploy)

The deployed Constitution has the following mutables initialized to address(0):

- `charters_compliance.registry_address`
- `tithe_router.address`
- `land_registry.address`
- `force_authorization.address`
- `public_fund.governance_address`

These are intentionally left zero at deploy time. Phase 2 wiring is via Governance proposal + timelock:

1. After Step 3 (`Constitution.bindGovernance` already complete from the original wave)
2. Submit a multi-call proposal that calls `Constitution.setMutable(key, address)` for each of the 5 references above
3. Vote → wait 48h+ timelock → execute
4. Verify each address now resolves correctly

`public_fund.safe_address` is wired AT CONSTITUTION CONSTRUCTION (Phase 1) since TitheRouter takes it as immutable constructor arg. This pattern resolves the deploy-time circular dependency between Constitution and TitheRouter.

## Religious-corp wave rollback

Same immutability + redeploy policy as the original wave. Charter Compliance attestations would need to be re-attested on the new ChartersComplianceRegistry; this is a heavy operation but possible because the AT Record evidence (per ADR-2605192230 Lexicons) is preserved on MST + IPFS.
