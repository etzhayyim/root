---
id: adr-2605310030-legal-services-vertical-session-closure
title: "ADR-2605310030: legal-services vertical session closure — non-profit legal aid from law-analysis to in-node WASM, + SDK/CI repair"
status: active
doc_type: adr
topic: legal-services-vertical-session
authoritative: true
last_verified: 2026-05-31
priority: 5.5
axis: operations
weight: 0.5
priority_note: "Session-closure record for the /loop session (2605291222) that built the non-profit legal-services vertical end-to-end and repaired the SDK/CI it surfaced. Nine PRs merged to main (#289-#297). The vertical: premise correction (非営利 ≠ UPL exemption) → 10-jurisdiction UPL/非弁 analysis + universal safe harbor (zero compensation + jurisdiction-licensed-lawyer supervision) → 6 lexicons → 4 lint gates (G15/G18/G19 + jurisdiction drift-guard) → LangGraph cell + ports → 2 in-node kotoba WASM guests (live-verified) → KG ingestion (74 entities incl. 10-jurisdiction routing table) → judiciary corpus sensor → manifest reconcile. Along the way: discovered + fixed a pre-existing broken SDK build (incomplete libsignal→XChaCha20 migration) + rewrote its E2E tests + path-scoped the stale CI matrix. Closed by specifying the R2 cross-party key-exchange design FOR REVIEW (ADR-2605302350) — the headline confidentiality gap, deliberately NOT implemented autonomously. Records the honest residual state (R1.0 placeholder crypto) and the items requiring human involvement."
authoritative_for:
  - legal-services vertical session (2605291222) closure record
  - the 9-PR merge ledger + the residual-state honesty note
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605302200-chigiri-unpaid-legal-aid-lane-multijurisdiction
  - adr-2605302330-chigiri-japan-certified-adr-mediation-lane
  - adr-2605302345-etzhayyim-legal-services-delivery-and-global-judiciary-corpus
  - adr-2605302355-legal-services-kotoba-wasm-in-node-deployment
  - adr-2605302350-r2-cross-party-key-exchange-design-for-review
related:
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605181100-mst-encrypted-records-signal-keywrap
supersedes: []
superseded_by: []
---

# ADR-2605310030: legal-services vertical session closure

**Status**: active
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

A `/loop` session (2605291222) was asked, iteratively, to "raise maturity and coverage."
It built the non-profit legal-services vertical end-to-end and repaired the SDK + CI that
the work surfaced. This ADR is the closure record.

# Decision (what landed — 9 PRs to main, #289-#297)

## The legal-services vertical
- **Law analysis (ADRs)**: ADR-2605302200 (10-jurisdiction UPL/非弁 matrix —
  JP/DE/FR/UK/US/KR/AU/CA-ON/AT/CH — + universal safe harbor: *zero compensation +
  jurisdiction-licensed-lawyer supervision*; corrects the premise 非営利 ≠ UPL exemption);
  ADR-2605302330 (Japan 認証ADR §72-exempt mediation lane); ADR-2605302345 (etzhayyim.com
  counsel-operated delivery + global judiciary corpus); ADR-2605302355 (in-node kotoba WASM
  deployment, status accepted).
- **Contracts**: 6 lexicons — legalAidMatter, jurisdictionPolicy, outboundLegalAct,
  judgeReference, court, judicialDecision.
- **Enforcement**: 4 lint gates — G15 (zero-compensation), G18 (counsel-actuation), G19
  (judge-analytics prohibition; France loi 2019-222 art.33), and the enabled-jurisdiction
  drift-guard (WASM gate ↔ cell port ↔ KG data).
- **Runtime**: `chigiri_legal_aid_clinic` LangGraph cell + ports (Murakumo non-advice
  triage / kotoba / Public-Fund counsel); 2 Rust WASM guests running INSIDE the kotoba node
  (`chigiri-legal-aid-guest` G14/G15/G16, `chigiri-legal-comms-guest` G18) — live-verified
  (gas-metered, journaled; gate violations blocked server-side at assert_count=0).
- **Storage**: legal-services subgraph + the 10-jurisdiction routing table ingested into the
  live kotoba KG (74 entities); program wasm content-addressed via block.put.
- **Ingestion**: `JudiciaryCorpusSensor` (passive, D6 pseudonymization, §D4 sealed/juvenile
  exclusion, G19 no judge-analytics, deterministic).
- **Consistency**: chigiri manifest reconciled with the shipped cell/gates/lexicons.

## SDK + CI repair (incidental, but blocking)
- Found `main` did NOT compile: an incomplete libsignal→XChaCha20 migration in
  `encrypted.ts` (commit a590e7f64). Completed it (PR #291; DID-binding preserved) +
  rewrote the 2 E2E tests (PR #292, 188 tests green) + path-scoped the stale SDK-dependent
  CI matrix so unrelated PRs aren't falsely gated (PR #290).

## Closure: the confidentiality gap, specified not coded
- ADR-2605302350 specifies the **R2** per-recipient X25519 ECDH sealed-box design FOR REVIEW.
  It is design-only; an implementation is gated on cryptographer + Council Lv6+ review and
  MUST NOT be produced autonomously.

# Consequences

- The non-profit legal-services capability is lawful-by-construction (advice/representation
  via jurisdiction-licensed human counsel through the Public Fund; the corp/software never
  practises law), enforced across design → contract → lint → runtime → storage → manifest.
- SDK builds + tests are green; CI reflects the current repo structure.

## Honest residual state (carry-forward)
- **Crypto**: `signal.ts` is an R1.0 **same-process placeholder** — encrypted records are
  NOT yet real cross-party E2E. R2 (ADR-2605302350) is the fix and needs human crypto review.
- **Judiciary sensor**: generic; needs real IPFS-pinned public-decision datasets + per-court
  concrete instances.
- **WASM guests**: invoked by sending wasm_b64 each call (no host call-by-program_cid yet);
  launchd auto-registration is unbuilt.
- **Multi-agent note**: this session ran alongside concurrent agents that repeatedly moved the
  shared working-tree HEAD; all work was pushed to origin and landed via isolated worktrees +
  remote merges, so nothing was lost, but the local branch refs may be stale.

# Alternatives Considered

- **Implement R2 crypto autonomously to "finish" the vertical** — rejected: the confidentiality
  layer must not be evolved by an agent without cryptographer review (crypto correctness ≠
  round-trip success). Specified the design for review instead.

# References

- ADR-2605302200 / 2605302330 / 2605302345 / 2605302355 / 2605302350 (the vertical + R2 design)
- ADR-2605262700 (chigiri R0) · ADR-2605181100 / 2605181200 (confidentiality layer)
- PRs #289-#297 (merged to main); deps.toml [[adrs]] registry updated this session
