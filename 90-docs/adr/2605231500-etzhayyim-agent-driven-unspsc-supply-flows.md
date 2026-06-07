---
id: adr-2605231500-etzhayyim-agent-driven-unspsc-supply-flows
title: "ADR-2605231500: agent-driven UNSPSC supply flows — business-model wiring for 18,346-actor commodity automation"
status: proposed
doc_type: adr
topic: agent-driven-supply
authoritative: true
last_verified: 2026-05-23
priority: 7.0
axis: substrate-boundary
weight: 0.70
priority_note: "Defines the canonical wiring matrix between (a) the 18,346 UNSPSC LangGraph actors registered 2026-05-23 (commit 9cd4fe73d) and (b) the religious-corp business-model contracts (Charter / Tithe / Public Fund / Force / Sanctions / Council / Surplus Router / Wellbecoming). Without this ADR, agent-driven commodity flows have no canonical authorization chain and risk Charter §2 violations at scale."
authoritative_for:
  - com.etzhayyim.agent.authority lexicon namespace + AgentAuthorityToken contract semantics
  - com.etzhayyim.unspsc.processManifest lexicon namespace
  - extensions to com.etzhayyim.esign.* required for agent-bound signing
  - the canonical wiring matrix between UNSPSC LangGraph actors and religious-corp economic-body contracts
  - agent-vs-human signer distinction (AAT for AI agents, Adherent SBT for humans)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605172700-membership-layering-shinto-adherent
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605211241-etzhayyim-surplus-router-warehouse-bridge
  - adr-2605221411-etzhayyim-artificial-organism-ecosystem
  - adr-2605231230-etzhayyim-esign-actor-did-bound-mst-anchored
related:
  - adr-2605222330-etzhayyim-com-substrate-violation-transition-window
supersedes: []
superseded_by: []
---

# ADR-2605231500: agent-driven UNSPSC supply flows — business-model wiring for 18,346-actor commodity automation

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

2026-05-23 commit `9cd4fe73d` ("feat(unispsc): register 18,342 UNSPSC actors at etzhayyim.com") landed `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/unispsc_agents/c{code}.py` — one LangGraph `StateGraph` per UNSPSC commodity code, totalling 18,346 actor files. Each is a per-commodity workflow definition (e.g., the live-animal code carries health-check + transit-log + facility-routing logic). DIDs follow `did:web:c{code}.etzhayyim.com`.

Earlier in the same session, ADR-2605231230 added `etzhayyim-esign` — a religious-corp-native document-signing actor — and Phase 0 (lexicon stubs + DID Worker deploy) landed in commit `060bc4d7a`. The motivating future work in that ADR's §"Future Work" was wiring esign into the religious-corp catalog actors (UNSPSC / ISCO / APQC).

The previous design pass for that wiring assumed **human-witnessed commodity flows** (donor → Steward, 2-signature donation receipt, optional third-witness). That assumption fails at scale:

- 18,346 commodity actors × even modest activation rates (~50-200 active commodities at once) produce envelope volumes that cannot be human-signed without re-creating the bureaucracy religious-corp explicitly rejects.
- The UNSPSC actors are already encoded as **autonomous LangGraph StateGraphs**, not human-facing forms. They expect to make decisions, route flows, and emit events without human intervention on every step.
- The Charter (ADR-2605192100 §1.16) defines Adherent SBT membership as 1-human-1-SBT-1-vote. **AI agents are not humans**, so they cannot hold Adherent SBT, yet they must be authorized to execute commodity workflows that touch religious-corp economic body decisions (donations, tithe routing, surplus allocation).

This ADR specifies the canonical wiring between the 18,346 UNSPSC LangGraph actors and the existing religious-corp business-model contracts so that **AI agents can drive commodity processes end-to-end** while every step remains Charter-compliant and on-chain auditable.

### Hard constraints (from existing ADRs)

- **No purchase** (§1.2 + ADR-2605192115): the only permissible commodity inflow purpose tags are `donation-in-kind` / `internal-allocation` / `surplus-routing` / `operational-supply`. `purchase` / `sale` / `subscription` MUST NOT be valid envelope purposes.
- **No advertising** (§2(c) Charter Rider): UNSPSC actor notification posts MUST be factual; no promotional language, no price-discount, no call-to-action.
- **10% tithe** (ADR-2605192130): every `donation-in-kind` envelope at `anchored` state triggers 1/10 of items routed to Public Fund inventory.
- **Substrate boundary** (ADR-2605172000): no Kotoba/Datomic / Postgres / Kysely in the agent path. All state on MST + IPFS + L2 anchor.
- **Charter Rider** (ADR-2605192200): template documents bundled with esign MUST NOT include for-profit or advertising templates.

### Existing actors / contracts that need wiring

The religious-corp constitutional wave (2026-05-19/20) already shipped most of the contracts that an agent-driven commodity flow depends on:

- `etzhayyim-charters-compliance` (Council attestation single SoT)
- `etzhayyim-tithe-router` (10% donation → Public Fund atomic split)
- `etzhayyim-public-fund` (5-of-7 Safe + 1 SBT = 1 vote)
- `etzhayyim-force-authorization` (Transparent Force, 1 SBT = 1 vote)
- `etzhayyim-land-registry` (4-layer pattern reused for commodity manifest IPFS pin)
- `etzhayyim-organism` ecosystem (ADR-2605221411 — BeliefStore feedback loop)
- `20-actors/sanctions/` (OFAC/EU/UN sanctions list ingest)
- `20-actors/yobel/cells/audit_witness/` (3-party witness primitive)
- ADR-2605211241 Surplus Router (`com.etzhayyim.apps.surplusRouter.*` 7 lexicons)
- ADR-2605231230 etzhayyim-esign (Phase 0 landed this session)

What is **missing** is:

1. An **agent-identity-and-scope** primitive analogous to Adherent SBT but for AI agents (revocable, scoped, delegated by a human Steward who holds Adherent SBT).
2. A **per-UNSPSC process manifest** record declaring the canonical authorization gates per commodity code.
3. An **atomic charter-compliance gate** that combines all per-step pre-checks (charter / sanctions / force / counterparty / eros-gore) into one allow/deny call from agent code.
4. **Extensions to the esign envelope** carrying agent-authority references + classification subjects + manifest pointers.

## Decision

### 1. Four flow types (canonical purpose enum)

Every UNSPSC commodity flow that crosses the religious-corp economic boundary MUST be representable as one of:

| Flow | `purpose` enum | Required signers | Tithe behavior |
|---|---|---|---|
| **F1** — in-kind donation receipt | `donation-in-kind` | donor + Steward (+ witness for high-stakes) | 10% of items routed to Public Fund inventory queue |
| **F2** — internal allocation / transfer | `internal-allocation` | Source Steward + Receiver (Adherent SBT or AAT-bound agent) | no tithe (already inside the corp) |
| **F3** — surplus redistribution | `surplus-routing` | Source Steward + Router agent + Destination Steward | no additional tithe (already routed from earlier tithe split) |
| **F4** — operational ingress | `operational-supply` | Vendor (donation form, NOT purchase) + Steward | 10% inventory tithe (same as F1) |

`purchase` / `sale` / `subscription` / `lease` / `tip` are **not** valid purposes for commodity flows under this ADR. Apps that need fiat-paid commodity acquisition route through the etzhayyim vendor backend per ADR-2605192115 §4 and never touch `com.etzhayyim.esign.*`.

### 2. Agent execution loop (canonical 12-step process)

Each UNSPSC LangGraph actor (`c{code}.py`) implements the same 12-step loop. Step 7 (counter-sign) is the ONLY step where human action MAY be required, and only when the manifest declares a Council-escalation threshold:

```
1. intake     — external trigger (donor email / sensor / IoT / scheduled)
2. classify   — UNSPSC + Counterparty + Sanctions + Eros/Gore + Force-sensitivity
3. authz      — AAT scope check (this agent allowed to handle this commodity?)
4. price/value— Phase 1=item-count, Phase 2=USDC-equivalent oracle
5. assemble   — manifest construction (1 envelope = N commodity batch)
6. sign-req   — esign.requestEnvelope (purpose + subjectClassifications + manifestUri)
7. counter-sign — human/agent counterparty sign or auto-attest
8. complete   — completedEvent
9. anchor     — anchor-cron writes L2 + (high-value) geth-private mirror
10. tithe     — 10% to Public Fund / Surplus queue (purpose-dependent)
11. notify    — wproto.convo fan-out to subject classifications + Council watch list
12. close     — process record + KPI emit to organism BeliefStore
```

### 3. AgentAuthorityToken (AAT) — the agent-identity primitive

A new ERC-721 + ERC-5192 soulbound token at `50-infra/etzhayyim-chain-contracts/src/AgentAuthorityToken.sol`. One AAT per (agent DID, scope) tuple. Minted by a Steward DID that holds an Adherent SBT; revocable by the same Steward OR by Council multisig.

| Field | Type | Purpose |
|---|---|---|
| `tokenId` | uint256 | monotonic, like Adherent SBT |
| `agentDid` | string | the AI agent's DID (e.g., `did:web:c43221501.etzhayyim.com`) |
| `stewardDid` | string | the human Steward delegating authority — MUST hold Adherent SBT |
| `unspscPrefixes` | bytes32[] | which UNSPSC code prefixes this AAT covers (e.g., `0x4322` = lab/medical supplies) |
| `purposes` | bytes32[] | which `purpose` enum values are allowed (e.g., `donation-in-kind`, `internal-allocation`) |
| `valueCap` | uint256 | per-envelope value ceiling (Phase 1=item count, Phase 2=USDC) |
| `expiresAt` | uint256 | unix timestamp at which the AAT auto-revokes |
| `revoked` | bool | manual revocation flag |
| `attestations` | mapping | bag of (key, count, lastAt) for ongoing compliance signal |

Operational invariants (enforced in the contract):

- A Steward DID without an Adherent SBT (verified via `AdherentRegistry.locked(tokenId)`) MUST NOT be allowed to mint AATs.
- Transfer / approve are permanently disabled (ERC-5192 soulbound).
- Mint events emit a canonical `AAT_Minted(tokenId, agentDid, stewardDid, scope)` event consumed by the `com.etzhayyim.agent.authority` record indexer.
- Revocation events emit `AAT_Revoked(tokenId, by, reason)` and force any in-flight envelope referencing the AAT to refuse counter-sign until the requester proves replacement authority.

### 4. UNSPSC process manifest record

A new record at `com.etzhayyim.unispsc.processManifest`. One record per UNSPSC code (18,346 records max, sparse — only populated for actively flowing commodities). Declares per-commodity policy that the LangGraph actor reads at step 3 (authz):

| Field | Purpose |
|---|---|
| `unspscCode` | the code |
| `bpmnProcessDef` | optional AT URI of the BPMN process_def this commodity follows (via Kyber projector) |
| `defaultPurpose` | default `purpose` enum for envelopes emitted by this actor |
| `forceSensitive` | bool — if true, ForceAuthorization.preAttest() required |
| `erosGoreCategory` | optional category requiring Council ruling per ADR-2605192400 |
| `councilEscalationThreshold` | per-envelope value/count at which Council Lv6+ ≥3 multisig required |
| `auditWitnessRequired` | bool — if true, yobel `audit_witness` cell invoked |
| `customsRequired` | bool — physical goods crossing borders need `customsRef` field |
| `chartersAttestation` | AT URI of the most recent `com.etzhayyim.charters.attest` covering this code |

### 5. Charter-compliance gate library

A TypeScript library at `20-actors/etzhayyim-sdk/src/charter-compliance-gate.ts`. Single entry point `combineGate(ctx)` returning `{ allowed: boolean, reasons: string[] }`. Internally fans out to:

- `chartersAttest(ctx)` — `ChartersComplianceRegistry.sol` lookup
- `sanctionsScreen(ctx.counterparty, ctx.jurisdiction)` — sanctions actor query
- `forcePreAttest(ctx)` — `ForceAuthorization.sol` lookup if manifest.forceSensitive
- `counterpartyClassify(ctx.counterparty)` — kuni-umi DMN evaluation
- `erosGoreCategoryCheck(ctx)` — Council ruling proxy if manifest.erosGoreCategory set

All five sub-gates are atomic (called concurrently); the gate returns `allowed=true` only if every sub-gate returns allow. Any deny short-circuits with the union of all deny reasons (audit-grade).

Phase 1 ships **only the function signatures + `NotImplementedError` stubs**. Each sub-gate is filled in as its underlying registry / DMN / actor reaches production readiness. This is intentional: the wiring shape is the SSoT, the implementations follow.

### 6. esign envelope extensions (backward-compatible)

The Phase 0 `com.etzhayyim.esign.*` lexicons gain optional fields. No required field changes — existing envelopes remain valid.

| Lexicon | Added field | Type | Purpose |
|---|---|---|---|
| `envelope` | `subjectClassifications[]` | array of `{scheme, code, did}` | which UNSPSC / ISCO / APQC subject(s) the envelope is about |
| `envelope` | `commodityManifestUri` | at-uri | reference to `com.etzhayyim.esign.commodityManifest` record (multi-commodity batch) |
| `envelope` | `requesterAgentAuthorityRef` | at-uri | reference to `com.etzhayyim.agent.authority` record proving AAT-bound authority |
| `envelope` | `purpose` enum + 4 values | enum | adds `donation-in-kind`, `internal-allocation`, `surplus-routing`, `operational-supply` |
| `envelope` | `charterAttestationRef` | at-uri | snapshot of the `ChartersComplianceRegistry` attestation captured at envelope creation |
| `envelope` | `sanctionsScreenRef` | at-uri | snapshot of the sanctions screening result at envelope creation |
| `envelope` | `councilEscalationRequired` | boolean | derived from manifest threshold; if true, Council ≥3 multisig replaces requester-only signing |
| `requestEnvelope` | `requesterAgentAuthorityRef` | at-uri | required when requester is an AAT-bound agent, absent when requester is a human Adherent |
| `signature` | `signerAgentAuthorityRef` | at-uri | present when signer is an AAT-bound agent; null when signer is a human Adherent |

### 7. Pregel cell additions

Three new cells to add to `40-engine/kotoba/crates/kotoba-kotodama/cells/`, registered in `50-infra/murakumo/fleet.toml`:

| Cell | Role |
|---|---|
| `commodity_process_orchestrator` | Drives the 12-step loop for the 18,346 UNSPSC actors. Runs as a single fleet-wide cell that round-robins or queue-driven across active commodities. |
| `tithe_in_kind_splitter` | Subscribes to `com.etzhayyim.esign.anchoredEvent`; for `donation-in-kind` / `operational-supply` purposes splits 10% of items to Public Fund inventory queue. |
| `aat_lifecycle` | Watches `AAT_Minted` / `AAT_Revoked` events; maintains the AT-Protocol projection of the AAT contract state; emits `com.etzhayyim.agent.authority` records. |

### 8. Business-model wiring matrix (canonical 16-row reference)

The complete mapping from agent execution loop step to business-model contract:

| # | Concern | Existing actor / contract | Connection to envelope | Phase |
|---|---|---|---|---|
| 1 | Agent identity + delegation | AgentAuthorityToken.sol (new) | envelope.requesterAgentAuthorityRef + delegationProof | 1.5 |
| 2 | Authorization scope | etzhayyim-authz + etzhayyim-charters-compliance | pre-mint Charter attestation captured to envelope.charterAttestationRef | 1 |
| 3 | Sanctions screening | 20-actors/sanctions/ + OFAC/EU/UN list ingest | step 2 classify + step 6 sign-req both call sanctions.screen() | 1 |
| 4 | Force-sensitive UNSPSC | etzhayyim-force-authorization + transparent-force-rd | manifest.forceSensitive=true → force.preAttest() blocks unless satisfied | 2 |
| 5 | Eros/Gore content guard | ADR-2605192400 + Council ruling proxy | manifest.erosGoreCategory triggers Council ruling check | 2 |
| 6 | Counterparty classification | 20-actors/kuni-umi/dmn/counterparty-classification.md | DMN evaluation rejects Charter-incompatible counterparties | 1 |
| 7 | Tithe (10%) | etzhayyim-tithe-router (TitheRouter.sol) | tithe_in_kind_splitter cell on `anchoredEvent` | 1 (count-based) / 2 (USDC) |
| 8 | Public Fund destination | etzhayyim-public-fund (5-of-7 Safe + 1 SBT = 1 vote) | F1/F4 envelope completion enqueues to Public Fund inventory | 1 (inventory) / 3 (Safe USDC) |
| 9 | Surplus routing | ADR-2605211241 Surplus Router (7 lexicons) | F3 envelope is the entry point to surplusRouter.proposeRedistribution | 2 |
| 10 | Wellbecoming priority | 20-actors/yoro + JouchoScore graph | scoring input for surplus routing destination selection | 2 |
| 11 | Payment rails (donation USDC only) | etzhayyim-paymaster (ERC-4337) + Smart Account | optional donor USDC co-sign with paymaster gas sponsor | 2 |
| 12 | L2 anchor + Council mirror | anchor-cron + EtzhayyimAnchor.sol + geth-private | esign Phase 2 anchor + Phase 3 Council mirror reused | 2/3 |
| 13 | BPMN process integration | 00-contracts/bpmn/com/etzhayyim/apqc/ + Kyber BPMN projector | UNSPSC actor `signature_required` node fires BPMN signal `Signal:esign:{purpose}` | 2 |
| 14 | Audit witness (high-stakes) | 20-actors/yobel/cells/audit_witness | manifest.auditWitnessRequired=true → 3-party witness cell invoked | 1 |
| 15 | Council escalation | ADR-2605192300 + etzhayyim-charters-compliance Council Lv6+ ≥3 multisig | manifest.councilEscalationThreshold triggers multisig requirement | 3 |
| 16 | KPI + organism feedback | etzhayyim-organism BeliefStore + kotodama cell catalog | step 12 close pushes per-envelope facts to organism | 1 (basic) / 2 (full belief update) |

### 9. Phase plan (UNSPSC supply layer)

| Phase | Scope | Acceptance criteria |
|---|---|---|
| **Phase 1 (this ADR + foundation PR)** | Lexicon namespaces stub (agent.authority + unspsc.processManifest), esign envelope extensions, AAT Foundry scaffold + 1 unit test, charter-compliance-gate skeleton, this ADR registered in deps.toml | All artifacts validate; 9-hook lefthook green; AAT deploys cleanly on Anvil; charter-gate throws NotImplementedError on all sub-gates |
| **Phase 1.5** | AAT contract deployed to Base Sepolia; Steward mints one AAT to a test agent DID; first envelope referencing the AAT round-trips through esign Phase 1 MST + IPFS | one valid AAT-bound envelope with Adherent-attested Steward delegation visible on MST |
| **Phase 2** | First real F1 in-kind donation envelope end-to-end (agent-driven assemble, esign Phase 2 Base Sepolia anchor, count-based tithe split, surplus router queue insert) | one Charter-compliant F1 envelope at `anchored` state with verified tithe split |
| **Phase 3** | Council-escalated F1 with ≥3 Council signatures replacing requester-only authority; geth-private mirror anchor; AAT deployed to Base mainnet | one F1 envelope above escalation threshold with Council multisig + dual-chain anchor |
| **Phase 4** | All five charter-compliance sub-gates implemented (sanctions / force / counterparty / eros-gore / charter); USDC-equivalent valuation; full BPMN signal integration | sample envelope routed through all 5 sub-gates with at least one realistic deny test |

### 10. CLAUDE.md substrate-boundary table delta

The repo-root `CLAUDE.md` substrate-boundary table gains one row:

| Concern | Allowed | Prohibited |
|---|---|---|
| Commodity flow (agent-driven) | AAT-bound agent + ChartersComplianceRegistry attestation + sanctions screening + (for force-sensitive) ForceAuthorization pre-attest + (for high-value) Council Lv6+ ≥3 multisig | uncontrolled agent autonomy on UNSPSC; envelope `purpose` of `purchase` / `sale` / `subscription` / `lease` / `tip`; agent acting without an AAT or with a revoked AAT |

This row will be added after Phase 1 lands.

## Consequences

### Positive

- 18,346 UNSPSC LangGraph actors become canonical participants in the religious-corp economic body without requiring human Adherent SBT each, while every step is still on-chain auditable through the AAT delegation chain.
- The Charter §1.2 (no purchase) and §2(c) (no advertising) prohibitions are enforced at the lexicon + contract level (purpose enum is closed; manifest forces classification; charter gate is atomic), not at the comment level. lefthook hooks (`no-purchase-purpose` + `no-advertising`) extend naturally to envelope and manifest JSON.
- Tithe (10%) becomes automatic and Charter-aligned regardless of whether the donation flow originated from a human or an agent; the same TitheRouter contract handles both paths because the AAT-vs-Adherent distinction is invisible to the tithe-in-kind splitter cell.
- The Bootstrap Council escalation pattern (≥3-of-5 multisig) is preserved for high-stakes envelopes via the `councilEscalationThreshold` manifest field — Council retains constitutional authority at the boundary without being in the loop for routine flows.
- Surplus Router (ADR-2605211241) gains its canonical input pipe: F3 envelopes become the typed entry point to `surplusRouter.proposeRedistribution`.

### Negative / Trade-offs

- The AAT contract adds another SBT-like surface to maintain alongside AdherentRegistry. Operationally these are similar (mint / revoke / locked / attestations) — code duplication is a real cost we accept in exchange for keeping human-membership and agent-authorization in separate semantic domains. A future ADR may extract a shared SBT base contract if the duplication exceeds 80%.
- Charter-compliance gate Phase 1 throws `NotImplementedError` for all five sub-gates. Apps that integrate before Phase 4 MUST design for "gate may not yet enforce" semantics — concretely, they should treat the gate as `allowed=true` only when explicitly opt-in via `EXPECTED_GATE_PHASE>=4` env, otherwise default-deny. This is the inverse of the usual lefthook informational pattern, intentional to avoid silent Charter drift during the build-out.
- 18,346 potential per-commodity process manifest records is a large lexicon-record surface. We accept the sparse-write model: most codes will never have a manifest, and the manifest record's required fields are minimal (only `unspscCode` is required; everything else is optional). For codes with no manifest, the orchestrator uses safe defaults (default purpose `donation-in-kind`, council escalation threshold 0 = always escalate).
- BPMN signal integration (`Signal:esign:{purpose}`) is deferred to Phase 4. This means Phase 1 / Phase 2 envelope creation is driven by LangGraph node code, not by BPMN process_def. Apps that want declarative BPMN-driven signing wait for Phase 4. Acceptable because no existing app actually drives commodity flows via BPMN yet.

### Open questions answered (from previous design pass)

The five OPEN questions from the prior turn are answered as follows:

- **Q1 (in-kind valuation):** (c) Phase 1 uses item-count tithe (no USDC valuation). Phase 2 introduces USDC-equivalent oracle.
- **Q2 (witness threshold):** (c) `manifest.auditWitnessRequired=true` triggers 3-party witness; defaults to false. Per-commodity policy in the manifest replaces a single global threshold.
- **Q3 (UNSPSC actor role):** (a) Phase 1 — passive notification only. (b) Phase 4 — commodity-specific validation via BPMN process_def.
- **Q4 (cross-jurisdiction customs):** (a) envelope carries `customsRef` field (already on envelope per Phase 0 schema if added; if absent, add via lexicon extension). Envelope ≠ customs declaration.
- **Q5 (anchor batching):** (a) 1 envelope = 1 anchor. 4-layer pattern preserved. Future Phase 5+ may introduce Merkle-batched anchors if anchor cost becomes material.

## Alternatives Considered

### A. Skip AAT — let every agent share the Steward's Adherent SBT key

Rejected. The Adherent SBT is constitutionally 1 SBT = 1 vote per ADR-2605192100 §1.16. Sharing the key with N agents creates ambiguity about voting authority, makes revocation of a specific agent impossible without revoking the Steward, and creates a single point of compromise. AAT separation is the smallest cost to keep the human/agent distinction clean.

### B. Use existing `com.etzhayyim.apps.lawfirm.eSign*` for commodity flows

Rejected. ADR-2605231230 §8 already excluded religious-corp documents from the etzhayyim lawfirm DocuSign passthrough. Commodity flows are religious-corp documents. Reverting that boundary would re-introduce centralized SaaS dependency for the largest agent-driven flow class.

### C. Make UNSPSC actors signers directly (no AAT, agent = signer)

Rejected. An agent that signs without delegation chain has no human accountability anchor. The AAT design forces "every agent action traces to a human Steward who can be held accountable" — this is non-negotiable per Charter §1.6 (governance accountability).

### D. Defer agent-driven flows entirely; require human Steward signing for every envelope

Rejected. At 18,346 commodity actors × even modest flows, this re-creates the bureaucratic chokepoint religious-corp explicitly rejects. The Phase 1 design specifically targets agent automation as the default, with human Steward sign-off only at Council-escalation threshold.

### E. Use OpenZeppelin AccessControl roles instead of AAT for agent scope

Rejected. AccessControl is per-contract; we need cross-contract scope (this AAT covers envelope creation + tithe routing + surplus router proposing). An ERC-721/ERC-5192 AAT is portable across contracts via the tokenId reference. Also, soulbound semantics matter — we don't want AATs traded or transferred, which AccessControl roles can't enforce.

### F. Inline charter-compliance gate logic in every UNSPSC actor

Rejected. 18,346 actors × 5 sub-gates = 91,730 code duplication points. The library + atomic combineGate(ctx) pattern centralizes the policy as the religious-corp constitutional invariants evolve — sub-gates change without touching agent code.

## References

- ADR-2605170900 (religious-corp open ADR canonical home)
- ADR-2605171800 (LangGraph MST IPFS L2 anchor pipeline) — 4-layer substrate
- ADR-2605172000 (etzhayyim RW-free substrate) — RW prohibition
- ADR-2605172300 (BI asset substrate) — chain partition pattern
- ADR-2605172700 (membership layering shinto / adherent) — Adherent SBT distinction
- ADR-2605192100 §1.16 (Mission Charter) — 1 SBT = 1 vote
- ADR-2605192115 (non-profit donation-only no-ads) — §1.2 / §2(c) / §3 (SBT↔SBT carve-out) / §4 (fiat receipt exception)
- ADR-2605192130 (Public Fund + Tithe) — 10% obligation
- ADR-2605192200 (Charter Rider v2.0) — §2(b) / §2(c) interpretation
- ADR-2605192230 (three-tier enforcement implementation) — L1 license / L2 benefit / L3 evaluation
- ADR-2605192300 (Bootstrap Council five) — Lv6+ ≥3 multisig escalation source
- ADR-2605192315 (Transparent Force R&D) — force-sensitive UNSPSC gate
- ADR-2605211241 (Surplus Router) — F3 destination
- ADR-2605221411 (etzhayyim organism ecosystem) — BeliefStore feedback
- ADR-2605231230 (etzhayyim-esign actor) — base esign actor that this ADR extends
- `50-infra/etzhayyim-chain-contracts/src/AdherentRegistry.sol` — soulbound ERC-721 + ERC-5192 reference pattern
- `20-actors/etzhayyim-sdk/src/` — SDK home for charter-compliance-gate
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/unispsc_agents/c{code}.py` — 18,346 LangGraph actors registered 2026-05-23
- `50-infra/murakumo/fleet.toml` — Pregel cell placement for the three new cells
