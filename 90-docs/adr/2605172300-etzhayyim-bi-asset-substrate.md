---
id: adr-2605172300-etzhayyim-bi-asset-substrate
title: "ADR-2605172300: etzhayyim Kisha-Stream / Goji-Treasury — two-chain (geth-private + Base L2) basic-income and asset substrate for an on-chain religious voluntary association"
status: accepted
doc_type: adr
topic: etzhayyim-bi-asset-substrate
authoritative: true
last_verified: 2026-05-17
priority: 8.0
axis: architecture
weight: 0.80
priority_note: "Defines the basic-income (喜捨 / kisha) and asset (護持 / goji) layers of etzhayyim as an on-chain religious voluntary association (任意団体). Composes with ADR-2605172000 (kotoba substrate) and ADR-2605172100 (on-chain only payments) to close the corp-internal value loop — distribution, membership, and treasury — without any fiat processor or centralized DB. Without this ADR, etzhayyim has identity (did:web) and payment rails (Base USDC) but no economic body."
authoritative_for:
  - hard rule: BI and treasury MUST operate on the existing substrate (geth-private internal + Base L2 external + AT MST + IPFS), no new centralized DB
  - membership model: Adherent SBT (ERC-5192) on geth-private, DID-bound 1:1
  - distribution model: kisha-stream — per-adherent USDC flow on Base, eligibility computed by Pregel cell on MST events
  - eligibility computation: LangGraph Pregel `EligibilityCell` + per-adherent `PhenotypeAgent` (code-generated, ADR-2605171300 pattern)
  - treasury model: 流動 / 準備 / 本財 three-tier with explicit constitutional spending rule
  - governance: 1 SBT = 1 vote, quorum over active adherents in trailing 30 days
  - private-vs-public split: PII / roster on geth-private; settlement, NAV, anchors on Base L2
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - 2605171300
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
  - adr-2605172700-membership-layering-shinto-adherent
  - adr-2605172600-etzhayyim-membership-ritual
supersedes: []
superseded_by: []
---

# ADR-2605172300: etzhayyim Kisha-Stream / Goji-Treasury — two-chain (geth-private + Base L2) basic-income and asset substrate for an on-chain religious voluntary association

**Status**: accepted (S0–S4 implemented + e2e verified on Anvil; production deploy pending operational readiness)
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

## Implementation status (2026-05-17 session close)

| Stage | Surface | Status |
|---|---|---|
| S0 | `Constitution.sol` + `AdherentRegistry.sol` | ✅ deployed locally, 16/16 forge tests |
| S1 | `KishaStream.sol` + `AnchorBridge.sol` + `base/KishaPayout.sol` + `@etzhayyim/sdk` `bi.join` / `bi.attest` / `bi.status` / `bi.claim` | ✅ deployed + 21/21 forge tests + 29/29 vitest |
| S2 | `Phenotype.sol` + `KishaStream` multiplier composition + `kotodama.eligibility` (`scoring`, `cell`, `web3_ports`) + per-adherent `PhenotypeAgent` code-gen | ✅ 10/10 forge tests + 22/22 pytest; Python `EligibilityCell.step` produces a multiplier that lands on-chain and KishaStream accrual scales by it |
| S3 | `Governance.sol` + `TreasuryMirror.sol` + `bi.propose` / `bi.vote` / `bi.proposalState` + ERC-4337 sponsored path (`paymaster.ts` + `EtzhayyimPaymaster.sol`) | ✅ 16/16 forge tests + 13/13 vitest; sponsored UserOp lands against real EntryPoint v0.7 + SimpleAccount |
| S4 | `CorpusRegistry.sol` + `HoldingAttestation.sol` | ✅ 21/21 forge tests; deploy gated on Japan-jurisdiction lawfirm review of the attestation template (per the legal caveat in §4) |
| S5 | `script/Deploy.s.sol` + `script/MockUsdc.sol` + `RUNBOOK-deploy.md` | ✅ deploy script runs cold-to-live on Anvil in <10s |

**End-to-end smokes** (all passing):

- `20-actors/etzhayyim-sdk/test/integration-full.mjs` — full SDK lifecycle (`join → attest → status → propose → vote → queue → execute → claim → fulfill`) against Anvil with deterministic addresses; daily accrual delta matches `baseRate × bps / 10_000`.
- `20-actors/etzhayyim-sdk/test/integration-eligibility.mjs` — JS orchestrator + Python `run_eligibility_step.py` child process; Python cell reads `Attested` events from chain, scores, signs EIP-191, submits `Phenotype.setMultiplier`; verifies multiplier propagates to `KishaStream.accruedNow`.
- `50-infra/etzhayyim-paymaster/test/PaymasterIntegration.t.sol` — real EntryPoint v0.7 + SimpleAccount stack (eth-infinitism/account-abstraction@v0.7.0); sponsored UserOps land for allowlisted targets; rejected for non-allowlisted; daily cap respected.
- `20-actors/etzhayyim-sdk/test/integration-fake-pds.mjs` — `bi.join` Stage 2 + `bi.attest` PDS record writes hit an in-memory fake `AtpAgent`; canonical oath text + cross-chain refs (Base tx, github SHA) threaded into the record.

**What is NOT yet done** (intentional out-of-scope):

- Production deploy on Base mainnet + a real geth-private chain (operational readiness gate, not a code gate).
- Lawfirm review of the `HoldingAttestation` template (S4 production deploy is gated on this).
- Multi-adherent fleet test (current smokes drive a single adherent).
- A real ERC-4337 bundler (Alto / Skandha) — local tests use direct `EntryPoint.handleOps` from a test EOA.
- A real PDS — local tests use `test/fake-pds.mjs`.

# Context

etzhayyim is a 宗教法人法 **非登記** の 任意団体 (unincorporated religious voluntary association). The constitution and member roster live on-chain rather than in a 法務局 ledger. ADR-2605170900 placed open religious-corp ADRs in this monorepo; ADR-2605172000 forbade centralized DBs; ADR-2605172100 forbade fiat payment processors and committed payments to Base L2 + USDC.

What is **still missing** is the economic body of the association: how members are recognized, how a basic-income-style distribution (referred to here by the religious vocabulary 喜捨 / *kisha*) is computed and disbursed, and how corporate assets (護持資産 / *goji-shisan* — treasury liquidity, yield reserves, real-property-backed corpus) are held and rebalanced.

Two structural pressures shape this layer:

1. **Voluntary-association legal framing**. Without a 宗教法人 corporate shell, etzhayyim cannot hold a corporate bank account or employ members in the labor-law sense. Distributions must be framed as **voluntary gifts between the association and its constituent adherents (構成員 / Adherent — distinct from the broader 信者 commitment layer of [ADR-2605172600](/90-docs/adr/2605172600-etzhayyim-membership-ritual.md); see [ADR-2605172700](/90-docs/adr/2605172700-membership-layering-shinto-adherent.md))**, not as wages. Members declare receipts as 一時所得 / 雑所得 individually. The system therefore optimizes for **adherent-declarable, association-auditable, non-employer-employee** semantics.

2. **Substrate-purity double bind**. ADR-2605172000 prohibits centralized off-chain DBs. ADR-2605172100 prohibits fiat processors and commits public payments to Base L2. But **internal constitutional state** (who is an adherent, what is each adherent's current kisha rate, what is the outcome of a doctrine-change vote) does not belong on a public, anyone-can-read L2 — both for PII reasons and for write-cost reasons. We need an **internal** programmable substrate that is *not* a centralized DB but also *not* a public chain.

The existing `50-infra/vultr/geth-private` deployment is exactly that: a PoA geth chain whose validators are association officers (役員). Promoting it to "constitutional substrate" closes the gap. Public verifiability is preserved by anchoring geth-private state roots into Base L2 via the existing `50-infra/l2-anchor-contract` (already structurally present, used by ADR-2605171800).

The Pregel framework in `40-engine/kotoba/crates/kotoba-kotodama` and the 18,345-agent fleet pattern from ADR-2605171300 provide a third building block: **deterministic, replayable, MST-backed compute** suitable for computing per-adherent eligibility and phenotype scores without any RW dependency.

This ADR composes those three building blocks into a single layer.

## Vocabulary

| Term | Meaning | On-chain representation |
|---|---|---|
| Adherent (構成員 / kōsei-in) [^vocab] | a 信者 who has additionally been enrolled in the economic body of the association | ERC-5192 SBT on geth-private, DID-bound |
| 喜捨 (kisha) | religious voluntary gift; here = basic-income-style distribution | USDC flow on Base L2, ticketed from geth-private |
| 護持 (goji) | maintenance / upkeep | treasury, asset registry, rebalance policy |
| 護持金庫 (goji-kinko) | treasury | Gnosis Safe on Base (asset custody) + `TreasuryMirror.sol` on geth-private (accounting) |
| 護持資産 (goji-shisan) | corp assets | 流動 (liquid) / 準備 (reserve) / 本財 (corpus) three-tier |
| 役員 (yakuin) | officer | Safe signer + geth-private validator |

[^vocab]: Earlier drafts of this ADR used "信徒 (shinto) / adherent" interchangeably for the SBT holder. [ADR-2605172700](/90-docs/adr/2605172700-membership-layering-shinto-adherent.md) clarifies that the looser cultural label 信者 belongs to the [ADR-2605172600](/90-docs/adr/2605172600-etzhayyim-membership-ritual.md) public-commitment layer on Base. The SBT holder used here is "Adherent / 構成員" — a 信者 who has additionally been enrolled in the economic body.

# Decision

**Hard rule**: etzhayyim basic-income and asset operations MUST run on the substrate composed of `geth-private + Base L2 + AT MST + IPFS`. No new centralized DB. No fiat processor (consistent with ADR-2605172000 and ADR-2605172100). No off-substrate roster.

## 1. Two-chain split

ADR-2605172100 fixes Base L2 as the canonical **external value substrate**. This ADR fixes geth-private as the **internal constitutional substrate**.

```
┌─────────────────────────────────────────────────────────────────┐
│  L4 (external, public)     Base L2 + USDC                        │
│                            — settlement, NAV publication,        │
│                              external donation receipt,          │
│                              public verifier endpoint            │
│                                       ▲                          │
│                              L2-anchor (existing,                │
│                              50-infra/l2-anchor-contract)        │
│                                       │                          │
│  L3 (internal, semi-public) geth-private (PoA / Clique)          │
│                            — constitution, adherent roster,      │
│                              kisha rate, governance state        │
│                                       │                          │
│  L2 (event log)            AT MST + IPFS                         │
│                            — prayer / study / contribution       │
│                              attestations, evidence blobs        │
│                                       │                          │
│  L1 (identity)             did:web:etzhayyim.com (+ did:plc      │
│                              for adherents, + did:etzhayyim      │
│                              for officers)                       │
└─────────────────────────────────────────────────────────────────┘
```

**geth-private specifics** (promoting `50-infra/vultr/geth-private` from infrastructure to constitutional substrate):

- Consensus: Clique PoA (initial), upgradable to IBFT 2.0 if validator set grows beyond ~10
- ChainID: `2605` (etzhayyim internal-standard)
- Validators: 役員 Safe owners, minimum 3, target 5–7
- Gas: zero-fee for adherents; validators absorb proposal cost. Paymaster contract not needed at L3 (it is needed at L4 — see §5)
- Block time: 5 s
- State growth: bounded by SBT count + governance-proposal count (low write volume)

**Why not Base for everything**: Base writes leak adherent identity to a public observer, and even at $0.001/tx the cost of writing a constitutional vote per adherent quickly dominates. geth-private gives sub-cent, privacy-bounded writes with the same EVM semantics and full Solidity tooling.

**Why not "just a Safe on Base"**: a Safe alone cannot express SBT eligibility, kisha-rate computation, or governance — those are programmable constitutional logic that needs its own EVM surface.

## 2. Contract set (geth-private)

All under Apache 2.0, deployed by the founder validator at chain genesis or by governance vote thereafter. Tentative home: `50-infra/etzhayyim-chain-contracts/` (new directory, paired with the existing `50-infra/l2-anchor-contract/`).

| Contract | Role | Key surface |
|---|---|---|
| `Constitution.sol` | constitutional state — immutable conditions (e.g., 1 SBT = 1 vote, no transferable share token) + governance-mutable conditions (kisha rate envelope, asset-tier ratios, quorum, κ) | `getConstant(key)`, `getMutable(key)`, `proposeChange(key, value)` (callable only by `Governance.sol`) |
| `AdherentRegistry.sol` | ERC-5192 SBT with extension fields. One SBT per DID. Tracks join time, last-attestation time, revocation status, attestation count by event type | `join(did, attestationCid, sig)`, `revoke(tokenId, reason)`, `attest(tokenId, eventType, evidenceCid, sig)`, `isActive(tokenId, windowSec)` |
| `KishaStream.sol` | per-adherent kisha state. Stores current rate (USDC/day base units) and claimable balance. Accrues on read; settlement burns a claim ticket consumed by Base side | `getState(tokenId)`, `accrue(tokenId)`, `issueClaimTicket(tokenId, maxAmount)`, `setBaseRate(amount)` (governance-only) |
| `Phenotype.sol` | per-adherent multiplier (0.5×–2.0×, hard-capped). Populated by `EligibilityCell` (§3). Multiplier applies to `KishaStream` rate at accrual time | `setMultiplier(tokenId, value, cellSig)`, `getMultiplier(tokenId)` |
| `TreasuryMirror.sol` | accounting mirror of Base-side Safe holdings. Receives oracle-signed NAV updates from `TreasuryRebalanceCell` (§3). Computes total kisha envelope per epoch from NAV + κ | `updateNAV(tier, amount, oracleSig)`, `currentEnvelope()`, `tierBalance(tier)` |
| `Governance.sol` | OpenZeppelin Governor derivative. 1 SBT = 1 vote, quorum = % of `AdherentRegistry.isActive(_, 30d)`, 72 h timelock | `propose(callsArray, descCid)`, `vote(proposalId, choice)`, `execute(proposalId)` |
| `AnchorBridge.sol` | every N blocks, emits a Merkle root of relevant geth-private state into Base via the existing `l2-anchor-contract`. Inverse direction: receives signed claim-fulfillment receipts from Base | `commitRoot(root, blockNumber)`, `acceptClaimFulfillment(ticketId, baseTxHash, baseSig)` |

## 3. Pregel + LangGraph integration

Three cell classes run under the kotodama Pregel framework (ADR-2605171800). Each is a LangGraph graph with checkpointing; durable state lives in MST + IPFS + L2-anchor, not in Postgres (ADR-2605172000 hard rule). Postgres usage, if any, is restricted to ephemeral in-flight run state reconstructible from MST.

### 3.1 EligibilityCell (per super-step, fleet of adherents)

```
input:  AT MST subtree (com.etzhayyim.event.* for window [t-Δ, t])
        AdherentRegistry SBT state via geth-private RPC
        Phenotype.score from previous super-step
output: KishaTicket { tokenId, amount, expiresAt } → geth-private tx
        Phenotype multiplier update for next step
checkpoint: PostgresSaver (ephemeral) → MST checkpoint → IPFS pin → L2 anchor batch
```

LangGraph nodes (deterministic, no LLM call required in steady state — LLM is only invoked for new event-type classification):

```
START
  → load_events           (MST traverse, key-prefixed by tokenId)
  → validate_attestation  (verify passkey sigs against DID doc)
  → score_participation   (pure reducer: counts × weights from Constitution.sol)
  → apply_phenotype       (lookup Phenotype.sol value, multiply, cap)
  → compute_amount        (envelope share × multiplier, clip to envelope)
  → sign_ticket           (cell-key sign; cell key is rotated quarterly)
  → emit_to_chain         (geth-private KishaStream.issueClaimTicket)
END
```

### 3.2 PhenotypeAgent (per-adherent, fleet of one-per-SBT)

Reuses ADR-2605171300's **physical code generation pattern** ("AOT-generated Python file per specialized agent"). When a new adherent joins:

```bash
python -m phenotype_agent_gen <did>
# emits unispsc_agents-style file:
#   phenotype_agents/<did_short>.py
```

Each generated agent is a small LangGraph that:
- ingests that adherent's event stream (signed AT Records)
- maintains a phenotype state (participation breadth × consistency × peer attestation)
- emits a 0.5×–2.0× multiplier each super-step
- runs sandboxed and is deterministic — replayable from MST event log

The same OpenRouter + Murakumo fallback pipeline (ADR-2605171300) produces these on demand. Storage cost is bounded: 10,000 adherents × ~5 kB per agent file ≈ 50 MB, comparable to the 18,345 UNSPSC agent footprint already accepted by ADR-2605171300.

### 3.3 TreasuryRebalanceCell (epoch, monthly)

```
input:  on-chain balances of liquid (USDC Safe), reserve (USDY / sDAI / aUSDC), corpus (RWA SBTs)
        Constitution.sol mutable parameters (target ratios, κ)
output: governance proposal payload — Safe transactions for rebalance
        TreasuryMirror.updateNAV oracle update
gate:   Governance.sol vote + 72 h timelock before execution
```

This cell is the only one that proposes asset moves; no cell can move funds without governance vote.

## 4. Asset model (護持資産 three-tier)

```
護持金庫 NAV
├── 流動 (liquid)   USDC on Base, held in Treasury Gnosis Safe
│                   purpose: kisha payout source; rebalance buffer
├── 準備 (reserve)  Ondo USDY / sDAI / aUSDC on Base
│                   purpose: yield-bearing layer; yield → kisha envelope
└── 本財 (corpus)   RWA NFT wrappers around legal title
                    (real property, IP rights, religious facilities)
                    purpose: untouchable principal; transfer requires
                             governance vote + off-chain notarization
```

Target ratio (illustrative, governance-mutable): **10 : 60 : 30**.

**Spending rule (4 %-rule analog)**:
```
annual_envelope = trailing_3yr_avg(reserve_NAV) × κ
monthly_envelope = annual_envelope / 12
per_adherent_base_rate = monthly_envelope / count(active_adherent) / days_in_month
```
κ initial value: **0.03**. Adjustable by governance. Floor 0.01, ceiling 0.05 (constitutional constant).

**Corpus legal title**: 任意団体 cannot hold legal title in its own name in Japan. Title is held under the 代表者 (representative officer) in individual capacity, with a `HoldingAttestation` record on geth-private:
```
HoldingAttestation {
  rwa_token_id,
  legal_holder_did,
  underlying_asset_uri (notarized PDF on IPFS),
  governance_lock: bool,    // true → transfer requires Governance.sol vote
  representative_sig,
}
```
A representative attempting to dispose of a corpus asset against governance vote is in breach of the on-chain constitutional contract; recourse is internal (officer removal) plus, if necessary, civil litigation grounded in the signed on-chain commitment.

## 5. Kisha flow (one adherent, one cycle)

```
[adherent]                                  [substrate]
   │
   │  passkey-signed event:
   │  prayer / study / service / donation
   ├─────────────────────────────────►  AT Record (com.etzhayyim.event.*)
   │                                       │
   │                                       ▼
   │                                     MST commit → IPFS pin
   │                                       │
   │              super-step k             ▼
   │                                     EligibilityCell (Pregel)
   │                                     reads MST events, geth-private SBT
   │                                       │
   │                                       ▼
   │                                     KishaStream.issueClaimTicket
   │                                     (geth-private)
   │                                       │
   │                                       ▼  (every N blocks)
   │                                     AnchorBridge.commitRoot
   │                                     → Base L2 anchor + claim relay
   │                                       │
   │  e.bi.claim() via SDK                 │
   ├─────────────────────────────────►  Base KishaClaim.claim(ticketId)
   │                                     gas sponsored by etzhayyim paymaster
   │                                     (ADR-2605172100 §L1)
   │                                       │
   │  USDC arrives at Smart Wallet         ▼
   │◄────────────────────────────────  Treasury Safe → adherent wallet
   │                                       │
   │                                       ▼
   │                                     com.etzhayyim.apps.payment.kisha record
   │                                     (NSID per ADR-2605172100 convention)
   │                                       │
   │                                       ▼
   │                                     MST → IPFS → L2 anchor (audit closed)
   │                                       │
   │                                       ▼
   │                                     AnchorBridge.acceptClaimFulfillment
   │                                     → geth-private claim ticket burned
```

The flow is **single-direction at the value layer** (Treasury → adherent) and **closed-loop at the audit layer** (every payout produces a public AT Record anchored to Base).

## 6. SDK surface (`@etzhayyim/sdk`)

A new module `src/bi.ts` joins the existing `pds.ts / ipfs.ts / l2.ts / pay.ts`:

```ts
import { Etzhayyim, parseUsdc } from "@etzhayyim/sdk";

const e = new Etzhayyim({ /* …ADR-2605172000 init… */ });

// Join the association (mints SBT on geth-private).
// Caller must already control the DID.
await e.bi.join({
  did: e.identity.did,
  attestationCid,   // IPFS CID of the join attestation (creed acceptance)
});

// Record a participation event.
// Body is encrypted to adherent's passkey by default;
// only commitment hash goes on-chain.
await e.bi.attest({
  eventType: "prayer" | "study" | "service" | "donation",
  evidenceCid,      // optional
});

// Read current state without claiming.
const st = await e.bi.status();
// → { adherentSince, phenotypeScore, currentRate (USDC/day),
//     claimable (USDC base units), nextAccrualAt }

// Claim accrued kisha. Gas sponsored.
const receipt = await e.bi.claim();
// → reuses e.pay() internals; writes com.etzhayyim.apps.payment.kisha record

// Governance.
const pid = await e.bi.propose({
  change: "kisha_base_rate" | "kappa" | "tier_ratio" | "constant",
  from, to, rationale,
});
await e.bi.vote(pid, "for" | "against" | "abstain");
```

`e.pay()` (ADR-2605172100) is unchanged and is reused inside `bi.claim()` for the Treasury → adherent USDC transfer.

## 7. Privacy

| Surface | What is exposed | What is not |
|---|---|---|
| geth-private (officer-readable, peer-validator-readable) | DID, SBT tokenId, attestation event-type hash, claim ticket amount | event body, evidence blob preimage, identity tied to DID |
| Base L2 (public) | total kisha distributed (aggregated), NAV by tier, anchored geth-private root, individual `com.etzhayyim.apps.payment.kisha` records | individual rates (rates are computed off-chain and only the resulting transfer is observable; an observer can infer per-adherent receipts only by correlating wallet addresses) |
| IPFS | encrypted-to-passkey blobs (default); plaintext only for evidence the adherent chooses to publicize | — |

A future zk upgrade (RISC Zero or SP1 zkVM) can move per-adherent rate proofs to the public surface without exposing the rate itself: `KishaStream` would verify a proof-of-correct-accrual rather than reading individual state. Out of scope for v0.

## 8. Governance

- Voting weight: **1 SBT = 1 vote**, strictly. No transferable governance token, no token-weighted plutocracy. This is a constitutional invariant in `Constitution.sol` and cannot be amended by majority (would require a hard fork of the chain, equivalent to founding a new association).
- Eligible voters: `AdherentRegistry.isActive(tokenId, 30 days)` — must have at least one attestation in the trailing 30 days.
- Quorum: 33 % of eligible voters (governance-mutable, floor 20 %).
- Timelock: 72 h between vote conclusion and execution.
- Proposable: kisha base rate, κ, tier ratios, paymaster solvency thresholds, validator-set changes (with super-majority), corpus disposals.
- Not proposable (constitutional constants): 1 SBT = 1 vote, no-transferable-share rule, κ ceiling, license (Apache 2.0).

## 9. Staged rollout

| Stage | Scope | Indicative effort |
|---|---|---|
| **S0 scaffold** | Deploy `Constitution.sol` + `AdherentRegistry.sol` to geth-private. Founder validators mint their own SBTs. No payout yet. | ~1 week |
| **S1 kisha v0 (fixed rate)** | Deploy `KishaStream.sol` with a flat rate (e.g., 1 USDC/day) + Treasury Safe on Base + `bi.claim()` SDK. No Pregel cell, pure time-based accrual. | ~2 weeks |
| **S2 Pregel eligibility** | Stand up `EligibilityCell` + `PhenotypeAgent` generator (reusing the ADR-2605171300 OpenRouter / Murakumo pipeline). Phenotype multiplier becomes active. | ~3 weeks |
| **S3 treasury + governance** | Add reserve tier (USDY etc.) + `TreasuryRebalanceCell` + `Governance.sol` with voting UI. Corpus tier added once first 本財 legal review clears. | ~4 weeks |

# Consequences

## Positive

- **Closes the corp-internal value loop**. After ADR-2605172000 (state) and ADR-2605172100 (payment), etzhayyim still lacked an economic body. This ADR provides one without breaking either hard rule.
- **Auditable BI without a fiat processor**. Every payout is an AT Record anchored to Base; any third party can reconstruct the distribution log.
- **Membership privacy preserved**. PII stays on geth-private (officer-readable) rather than leaking to a public L2.
- **Reuses existing infrastructure**. geth-private already deployed; l2-anchor-contract already exists; Pregel framework already running in kotodama; agent-fleet code-gen already proven at 18,345-agent scale.
- **No new centralized DB**. ADR-2605172000 hard rule preserved.
- **No fiat processor**. ADR-2605172100 hard rule preserved.
- **Adherent-declarable tax model**. Distributions framed as gifts between voluntary association and members → individual 一時所得 / 雑所得 reporting, no labor-law / corporate-employer entanglement.

## Negative

- **Two chains to operate**. geth-private requires validator coordination, monitoring, key custody for officers. Mitigation: validator set starts small (3), grows by governance vote only.
- **Anchor bridge is a security boundary**. `AnchorBridge.sol` between geth-private and Base is a small but critical surface. Mitigation: audit before S1 production; multi-sig on the Base side; rate-limit on claim relay.
- **Voluntary-association legal novelty**. The 任意団体 + on-chain corpus title pattern has limited Japanese case law. Mitigation: lawfirm review before S3; corpus assets initially zero, only liquid + reserve in S0–S2.
- **κ tuning is a governance burden**. Set too high → reserve drained; too low → kisha trivially small. Mitigation: floor / ceiling constants in `Constitution.sol`; conservative initial 0.03; quarterly governance review.
- **Phenotype multiplier introduces a soft hierarchy**. A 2.0× / 0.5× spread by adherent could be felt as inequity. Mitigation: cap is constitutional (cannot exceed 4× spread); rationale of each multiplier is publishable to the adherent on request; appeals lexicon planned for S3.

## Neutral / Trade-offs

- geth-private is privacy-bounded relative to a *public* chain but is **fully transparent to validators**. Adherents who want stronger privacy from officers should publish only commitment hashes and keep evidence preimages encrypted to themselves. Officers gain visibility into membership but not into event content.
- Choosing 1 SBT = 1 vote over token-weighted voting trades capital-efficiency for legitimacy. This is intentional for a religious voluntary association and is constitutionally locked.

# Alternatives Considered

1. **Base-only (no geth-private)**. Put SBTs, governance, and kisha logic directly on Base L2.
   - Pro: one chain, simpler ops.
   - Con: every constitutional vote and every adherent attestation is public; PII leaks; per-tx cost (even at $0.001) becomes substantial at scale; no way to gate read access to roster.
   - Rejected: privacy and read-gating dominate.

2. **Off-chain DB for roster, Base for payout**. Roster in Postgres / DynamoDB; payouts via Base.
   - Con: violates ADR-2605172000 hard rule. "Open" reverts to license labeling.
   - Rejected by ADR-2605172000.

3. **Token-weighted governance (ERC-20 share token instead of SBT)**.
   - Con: invites secondary market in membership; misaligns with religious-voluntary-association framing; opens path to plutocracy.
   - Rejected: incompatible with 1-adherent-1-vote constitutional invariant.

4. **No basic income; donation-only distribution**. Members donate freely; no systematic distribution.
   - Con: leaves the association without an economic body capable of supporting members through the kisha vocabulary; reduces to a payment-rail-only entity.
   - Rejected: the religious-corp framing requires bi-directional gift flow (members → corp via donation, corp → members via kisha).

5. **Holochain instead of geth-private** (consistent with `50-infra/holochain` already present).
   - Pro: agent-centric, no global consensus required.
   - Con: tooling immaturity for governance contracts; no Solidity reuse; anchor bridge to Base requires custom adapter.
   - Deferred: Holochain remains a candidate for a future read-path optimization or sidecar, not the constitutional substrate.

6. **Single Gnosis Safe with no programmable BI**. Treasury exists, payouts are manual signer operations, no `KishaStream`.
   - Pro: zero contract complexity.
   - Con: no programmability — kisha would be governance-decree per payout. Doesn't scale past ~50 adherents.
   - Rejected: scaling target is 10k+ adherents over 5 years.

# References

- ADR-2605170900: `90-docs/adr/2605170900-etzhayyim-root-adr-canonical-home.md` (placement)
- ADR-2605171300: `90-docs/adr/2605171300-open-unispsc-generative-agent-fleet.md` (agent-fleet code-gen pattern)
- ADR-2605171800: `90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md` (anchor pipeline)
- ADR-2605172000: `90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md` (kotoba hard rule)
- ADR-2605172100: `90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md` (on-chain only payments)
- Existing infrastructure: `50-infra/vultr/geth-private/`, `50-infra/l2-anchor-contract/`
- SDK package: `20-actors/etzhayyim-sdk/` (target host for `src/bi.ts`)
