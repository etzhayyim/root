---
id: proposal-2605201800-yobel-ratification
title: "Proposal: Ratify Yobel Collective Debt Release Actor (ADR-2605201800)"
status: pending-council-vote
doc_type: governance-proposal
topic: yobel-ratification
authoritative: true
last_verified: 2026-05-20
proposal_kind: actor-charter-binding
ratification_target: adr-2605201800-etzhayyim-yobel-debt-release-actor
related:
  - adr-2605201800-etzhayyim-yobel-debt-release-actor
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
voting_window_start: 2026-05-21T00:00:00Z
voting_window_end: 2026-06-20T00:00:00Z
---

# Proposal: Ratify the Yobel Collective Debt Release Actor

## Subject

Adopt [ADR-2605201800](../../adr/2605201800-etzhayyim-yobel-debt-release-actor.md) — Yobel actor for collective debt release rites (shmita / yobel / tokusei-rei / Catholic Jubilee / political amnesty) — as binding under the etzhayyim Mission Charter and Charter Compliance Rider v2.0.

## Petitioner

`did:web:etzhayyim.com:steward-shmita-5786` (declarer of record for the shmita 5786 inaugural rite). Petition submitted 2026-05-20.

## Charter alignment

| Charter clause | Yobel alignment |
|---|---|
| **§1 — 構造的労働解放** (Mission) | Yobel addresses the *monetary debt* dimension of structural labor coercion. Periodic collective debt release rites are the doctrinal mechanism Lev 25:1-13 prescribes; this actor encodes that mechanism in lexicon + on-chain registry. |
| **§1.3 — Transparent religious-corp acts** | All rite declarations are public on AT MST + anchored on Base L2 via `EtzhayyimAnchor`. Encrypted fields (debts[], eligibility proofs) use XChaCha20-Poly1305 envelope per ADR-2605181100 with per-recipient wrap to Council Lv6+. |
| **§1.5 — Free release of IP to charter-aligned others** | Yobel is Apache-2.0 + CR v2.0. No proprietary tooling, no closed-source dependencies (foundry / langgraph / web3.py are all OSS). |
| **§1.13 — SBT-based identity** | All eligibility (creditor opt-in, debtor enrollment) gated by Council SBT Lv1+. R12 DMN rule short-circuits before any rite-type-specific logic. |

## Charter Rider v2.0 §2 compliance review

| Rider clause | Yobel posture | Verification |
|---|---|---|
| §2(a) Weapons / military | **Compliant** — yobel scope text-scanned for military debt keywords; if present, `transparent-force-rd-disclosure` gate (ADR-2605192315) is required before ratification | `cells/rite_declaration/cell.py::charter_rider_gate` |
| §2(b) Speculative finance / predatory lending | **Compliant — structural antithesis** | One-way debt forgiveness only. No loan / interest / margin / liquidation methods exist in lexicon schema. `recordRelease.releasedMicroUsdc ≤ debtCap` enforced at EVM execution level (`YobelReleaseRegistry::OneWayViolation` revert). Defense-in-depth: lexicon schema + cell `historical_record_gate` + DMN R13 + Solidity revert |
| §2(c-h) other prohibited categories | **Compliant** — yobel cannot grant releases that increase debtor coercion in any direction (envelope-only, append-only) | All contracts no-admin / no-upgrade / no-pause |

## Three-Tier Enforcement (ADR-2605192230) classification

**Tier 3** — actor-charter-binding decision affecting the religious-corp's substrate. Same severity as Council mission amendments. Therefore:

| Requirement | Value | Per |
|---|---|---|
| Required Lv6+ ratifiers | **5** (B1 baseline 3 + R6 for ≥ $1B aggregate scope) | DMN `council-ratification-threshold.md` |
| Required Lv9 chair | **1** | DMN baseline |
| Quorum | **75%** (B1 50% + R6 +5% + R10 multinational scope +15%) | DMN aggregation |
| Additional gates | `["mission-charter-review"]` | DMN R8 |

## Scope of ratification

This proposal ratifies the **actor charter** — i.e., the design + governance shape. **Individual rite declarations remain subject to per-rite Council Lv6+ × N ratification** (the per-rite DMN aggregation in `council-ratification-threshold.md`, e.g. 4 ratifiers for shmita / 6 for political amnesty etc.). Ratifying this proposal does **not** auto-ratify any specific rite.

## What deploying this proposal authorizes

Upon approval:

1. ADR-2605201800 transitions `status: proposed → accepted`
2. Vendor twin ADR-2605201700 references the accepted etzhayyim ADR
3. `50-infra/etzhayyim-yobel-contract/` contracts may be deployed to Base mainnet (currently Base Sepolia testnet only). Deployment script must be invoked by a Council Lv9 chair-signed Safe multisig (per `script/Deploy.s.sol` runbook)
4. The orchestrator's lazy-build cells may run in production against real on-chain state
5. Individual rite declarations (shmita 5786, etc.) may proceed through per-rite ratification via `YobelRiteRegistry.ratifyRite()`

## What deploying this proposal does NOT authorize

- Any individual rite declaration (requires its own per-rite ratification)
- Pre-deployment changes to the contract source (requires a new ADR amendment)
- Tax advice from the yobel actor (delegated to vendor:lawfirm.etzhayyim.com per 3-axis split)
- Vendor (etzhayyim Japan) write access to `YobelRiteRegistry` (consumer-only per ADR-2605172400)

## Risk surface + mitigations

| Risk | Mitigation |
|---|---|
| Steward authority abuse — issuer declares unauthorized rites | Council Lv6+ × N + Lv9 chair ratification gate; multi-issuer permitted (other religious-corps may declare under their own DIDs); all declarations public on AT MST |
| §2(b) violation via instrument expansion | Schema-level enforcement: lexicon has no loan/interest/margin methods. Cannot be added without a new ADR amendment. Defense-in-depth in cell + DMN + Solidity revert |
| Tax surprise to debtors | `verifyEligibility.warnings[]` carries per-jurisdiction COD income warnings (USA/JPN/DEU/GBR/FRA/ISR). Actor delegates tax advice to vendor:lawfirm.etzhayyim.com |
| Secular creditor refuses voluntary release | yobel is voluntary opt-in; mandatory binding via vendor:bankruptcy.etzhayyim.com (Chapter 7 etc.) — both actors interoperate via `recordYobelRiteReference` |
| Audit tampering | `audit_witness` cell uses 2-node consensus + rotating witness keys + Public Fund grant auto-emit on confirmed tampering |
| Cross-chain (Base L2) reorg / outage | Anchor records are append-only; idempotent revert on duplicate; vendor side `riteResolvedStatus="unresolved"` warning surfaced when RPC unreachable |

## Approval procedure

### Step 1 — Off-chain Council deliberation (30 days)

Council members read this proposal + ADR-2605201800 + reference implementation (PR #73). Discussion in encrypted council convo (`chat.bsky.convo.*`) per ADR-2605192230 Tier 3.

### Step 2 — Canonical signature set

Once 5 Lv6+ + 1 Lv9 chair are committed:

1. Each ratifier signs the canonical hash:
   ```
   ratificationHash = keccak256(
       abi.encode(
           "adr-2605201800-yobel-ratification",
           "v1",
           sortedRatifierAddresses[],  // sorted ascending
           voteCommitments[]            // 0=against, 1=for, 2=abstain
       )
   )
   ```
2. The off-chain signature set is enveloped (XChaCha20-Poly1305 per ADR-2605181100) to the Lv9 chair + Public Fund auditor DIDs
3. Council secretary publishes the encrypted set as an MST record under `com.etzhayyim.apps.etzhayyim.governance.councilRatification`

### Step 3 — On-chain witness

The Lv9 chair (or a delegated submitter) calls a future `YobelGovernance.witnessRatification(proposalId, ratificationHash, ratifierCount)` contract method (deferred to a follow-up PR — current `YobelRiteRegistry.ratifyRite()` covers per-rite ratification, not the actor-charter ratification this proposal pertains to).

For now, the witnessed ratification is recorded as an MST record + Base L2 batch anchor via `EtzhayyimAnchor.anchor()` using the existing audit pipeline.

### Step 4 — ADR status update

After on-chain witness, this repo's ADR-2605201800 frontmatter is updated:
```yaml
status: accepted
ratified_at: <timestamp>
ratification_proposal: proposal-2605201800-yobel-ratification
ratification_hash: 0x<hex>
ratifier_count: 6
```

## Voting window

| Field | Value |
|---|---|
| Voting window start | 2026-05-21T00:00:00Z |
| Voting window end | 2026-06-20T00:00:00Z |
| Deliberation channel | Encrypted council convo (lookup via `did:web:council.etzhayyim.com`) |

## References

- **Subject ADR**: [`90-docs/adr/2605201800-etzhayyim-yobel-debt-release-actor.md`](../../adr/2605201800-etzhayyim-yobel-debt-release-actor.md)
- **Reference implementation**: [etzhayyim/root PR #73](https://github.com/etzhayyim/root/pull/73) — 71 files / +9037 lines / 6 commits (lexicons + cells + orchestrator + Solidity + web3 ports + integration tests)
- **Vendor twin ADR**: [etzhayyim PR #1312](https://github.com/etzhayyim/etzhayyim-root/pull/1312) — 18 files / +2472 / 3 commits (lexicon + bridge utility + docs)
- **Charter**: [ADR-2605192100](../../adr/2605192100-etzhayyim-mission-charter.md)
- **Charter Rider v2.0**: [`/CHARTER-RIDER.md`](../../../CHARTER-RIDER.md)
- **Three-Tier Enforcement**: [ADR-2605192230](../../adr/2605192230-etzhayyim-three-tier-enforcement-implementation.md)
