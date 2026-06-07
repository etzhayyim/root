---
id: tsukuroi-authorized-remediation-tier-b-actor-r0
title: "ADR-2605291500: tsukuroi (繕い) — authorized vulnerability-remediation + patch-proposal actor (akuma's constructive sibling) R0"
status: proposed
doc_type: adr
topic: authorized-remediation
authoritative: true
last_verified: 2026-05-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "closes the akuma (ADR-2605151400) finding→remediation loop"
authoritative_for:
  - authorized-remediation
  - remediation-mandate-contract
  - patch-proposal-propose-only-ceiling
  - remediation-audit
depends_on:
  - adr-2605151400-akuma-authorized-redteam-actor
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only
  - adr-2605231525-server-side-signing-capability
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605091800-pruning-protocol
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605240200-kaizen-self-reflection
supersedes: []
superseded_by: []
---

# ADR-2605291500: tsukuroi (繕い) — authorized vulnerability-remediation + patch-proposal actor (akuma's constructive sibling) R0

**Status**: proposed
**Date**: 2026-05-29
**Deciders**: Jun Kawasaki

# Context

ADR-2605151400 introduced `akuma` (悪魔), the platform's authorized active
security-testing actor. akuma diagnoses: it runs scope-bound, dual-signature
probes against owner-attested targets and emits `vertex_akuma_finding` /
`com.etzhayyim.apps.akuma.recordFinding` records. The akuma ADR explicitly
**leaves the loop open at "scored / recorded"** — its own "out of scope"
ceiling states that "automated patch generation/submission is out of scope
for akuma"; findings flow to `yabai` / `malak` / the threat ledger for
**human triage**. akuma can re-probe to *verify* a closure (`closeFinding`),
but it never *produces* the closure.

There is therefore no actor that takes an owner-attested finding and
**proposes a fix patch** back to the authorized target — the constructive
half of the diagnosis→remediation loop. Without an explicit ADR, such work
would either (a) be welded onto akuma (giving an offensive-diagnosis actor
write-access to targets — a strictly worse compromise blast-radius), or
(b) be run as ad-hoc tooling with no mandate contract, no authority chain,
no propose-only ceiling, and no audit substrate.

The general user request — "an actor that, against an authorized server,
performs vulnerability diagnosis and sends a fix patch" — is satisfied by
**akuma (diagnosis) + this ADR's new actor (remediation)** as a deliberately
**separated pair**, not a single dual-purpose tool.

# Decision

Introduce a new Tier-B actor `tsukuroi` (繕い — *to mend / to patch*; the
constructive sibling of `akuma` 悪魔) at `did:web:tsukuroi.etzhayyim.com`,
nanoid `t5kur0i9`, `performer_type = service`, governed by etzhayyim under
the standard operating-entity boundary.

tsukuroi's only purpose is **scope-bound, authorized vulnerability
remediation by patch *proposal***: consume an owner-attested vulnerability
finding, synthesize a candidate defensive fix, validate it in an
egress-restricted sandbox, and **propose** it to the authorized target as a
fork-and-PR (or signed patch bundle). It is **propose-only** — a human owner
merges. tsukuroi performs **no probing** (that is akuma) and **holds no
merge/deploy authority and no platform master key**.

tsukuroi is kotoba-native (ADR-2605262130): datom/EAVT facts on
`kotoba-kqe`, records on MST under `com.etzhayyim.tsukuroi.*`. It does **not**
reuse akuma's older Kotoba/Datomic data plane.

## RemediationMandate contract (parallel to akuma's scope contract)

Each remediation engagement is a datom-backed contract object
(`com.etzhayyim.tsukuroi.remediationMandate`):

- `target_repo`: git remote URL **or** config target the patch is proposed to
- `finding_cid`: the **akuma finding** (or owner-submitted report) being
  remediated — tsukuroi cannot act without an upstream finding reference
- `allowed_paths[]`: explicit file/dir prefixes tsukuroi MAY touch (writes
  outside are denied at policy and at schema)
- `submission_mode`: `fork-pr` | `patch-file` | `config-diff`
- `owner_did` + `owner_signature`: target owner DID + detached signature
- `authority_did` + `authority_signature`: etzhayyim approver ∈ authority chain
- `valid_from`, `valid_until`: ISO window (default 14 days)
- `legal_basis`: SOW id / bug-bounty program URL / written-authorization CID
- `delegation_credential_ref`: reference (NOT the secret) to an
  **owner-issued, least-privilege, fork-and-PR-only, expiring** credential
  stored as ciphertext in `vault.etzhayyim.com`. tsukuroi never holds a
  platform-held master/merge credential (G8 / ADR-2605231525).
- `mergeAuthorityHeld`: **const `false`** (structural — propose-only)
- `max_pr_per_window`, `revoked` (one-way, immediate)

A mandate is valid only if both signatures verify, `now ∈ [valid_from,
valid_until)`, `revoked == false`, and the referenced `finding_cid` resolves
to an active akuma finding (or an owner-signed finding report) on the same
owner+target.

## Capability ceiling (CRITICAL — constitutional invariants)

1. **PROPOSE-ONLY (G4)** — tsukuroi opens a PR / emits a patch bundle. It
   MUST NOT merge, self-approve, force-push to a protected branch, deploy, or
   release. The human owner merges. Mirrors the no-server-key invariant
   (ADR-2605231525) and akuma's no-weaponization ceiling.
2. **DEFENSIVE-ONLY (G5)** — generated artifacts are *fixes*. No PoC /
   exploit / offensive payload, even as a test fixture (Charter Rider §2(a)).
3. **SCOPED WRITE (G6)** — `pathsTouched ⊆ allowed_paths`.
4. **NO PROBING (G3)** — vulnerability input comes only via an akuma
   `finding_cid` or an owner-signed finding report. Acquiring any probe
   capability is a critical violation (negative-space discipline, cf. junkan
   G4 / ADR-2605290927).

## Pregel cells (LangGraph; R0 path-reserved)

Seven cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/tsukuroi_*/`, each import-time
`RuntimeError("tsukuroi R0 scaffold: activate via Council ADR + R1
ratification")` until R1:

```
finding_intake ──────── consume akuma.finding within an active mandate
patch_synthesis ─────── Murakumo-only LLM drafts candidate defensive diff (G10)
charter_rider_scan ──── §2(a)..(h) scan + offensive/PoC rejection (G1, G5)
patch_validation ────── sandbox build + test (egress-restricted; never the live target) (G9)
pr_submission ───────── fork-and-PR via owner-delegated expiring credential; propose-only (G4, G8)
closure_verification ── request akuma re-probe; close only on owner-merge + re-probe pass (G11)
silen_tsukuroi_review ─ quarterly Council audit; structural zero-counters (G13)
```

## Lexicons (`com.etzhayyim.tsukuroi.*`)

- `remediationMandate` — dual-sig; `submissionMode` closed enum;
  `mergeAuthorityHeld` const `false`
- `patchProposal` — `findingCid` ref; `defensiveOnly` const `true`;
  `autonomousMerge` const `false`; `pathsTouched[] ⊆ allowedPaths`
- `patchValidationResult` — sandbox build/test outcome; `ranAgainstLiveTarget`
  const `false`
- `closureAttestation` — `ownerMerged` + `akumaReprobePass` ⇒ `remediated`
- `silenTsukuroiReview` — structural zero-counters: `autonomousMergeCount`,
  `exploitArtifactCount`, `outOfScopeWriteCount`, `platformHeldKeyCount` — any
  nonzero ⇒ cell halt + `chigiri.disputeMediation` (ADR-2605262700)

## Gates G1..G13

- **G1** Charter Rider §2(a)..(h) scan on every generated patch
  (`sensors.charter_rider.scan`, ADR-2605192200)
- **G2** kotoba datom lineage — append-only EAVT, no soft delete
- **G3** NO PROBING — diagnosis not owned; input via akuma `finding_cid`
  only (negative-space)
- **G4** PROPOSE-ONLY / NO AUTONOMOUS MERGE — `mergeAuthorityHeld` /
  `autonomousMerge` const false; `autonomousMergeCount=0`
- **G5** DEFENSIVE-ONLY / NO EXPLOIT — Charter Rider §2(a);
  `defensiveOnly` const true; `exploitArtifactCount=0`
- **G6** SCOPED WRITE — `pathsTouched ⊆ allowedPaths`;
  `outOfScopeWriteCount=0`
- **G7** dual-signature mandate (owner + authority ∈ etzhayyim chain),
  parallel to akuma scope
- **G8** NO PLATFORM-HELD KEY (ADR-2605231525) — submission uses an
  owner-issued, least-privilege, expiring, fork-PR-only delegated credential
  (vault ciphertext); `platformHeldKeyCount=0`; `// no-server-key` exemption
  marker pattern documented for the credential-handover window
- **G9** sandbox validation egress-restricted — build/test runs in
  `tsukuroi-validate` namespace, NEVER against the live target;
  `ranAgainstLiveTarget` const false
- **G10** Murakumo-only inference (ADR-2605215000) — `patch_synthesis` via
  judah LiteLLM `127.0.0.1:4000`
- **G11** closure requires akuma re-probe pass **and** owner human merge —
  no self-attested closure
- **G12** rate limit — `max_pr_per_window` per mandate
- **G13** Bonsai pruning (ADR-2605091800) — unauthorized write / out-of-mandate
  target → **seed-tier prune** (full actor freeze + human review); out-of-scope
  path blocked at policy → branch-tier prune; rate-limit violation → leaf-tier

## Non-goals N1..N12

N1 NOT a red-teamer/scanner (that is akuma) · N2 NOT autonomous deploy/CD ·
N3 NOT a merge-bot / auto-approver · N4 NOT an exploit/PoC generator ·
N5 NOT a commercial "patch-as-a-service" — Snyk Fix / GitHub Advanced
Security (paid) / Mend / Veracode / Checkmarx / Black Duck PROHIBITED per
Charter Rider §2(e); OSS only (OSV-Scanner / Trivy / Semgrep OSS /
CodeQL under OSS-permitted license) · N6 NOT a platform-key holder ·
N7 NOT operating outside an owner-attested mandate · N8 NOT touching paths
beyond `allowed_paths` · N9 NOT a substitute for human security review
(it proposes; humans decide) · N10 NOT Murakumo-bypass · N11 NOT Charter
Rider §2 bypass · N12 NOT a state-aligned/military patch operation
(Charter §1.12; all remediation logged on-chain + open-source —
Transparent Force discipline)

## Closed loop with akuma

This actor **closes the loop akuma left open**:

1. `akuma.finding` (category `VulnFinding`) → `tsukuroi.finding_intake`,
   only within an active mandate referencing the same owner + target +
   `finding_cid`.
2. `tsukuroi.patchProposal` → owner reviews & **merges** (human) →
   `tsukuroi.closure_verification` requests an akuma re-probe of the same
   finding (akuma's existing `closeFinding` re-probe path).
3. On owner-merge + re-probe pass → `closureAttestation.remediated = true`.

## Topology (kotoba-native)

- **Edge**: SvelteKit CF Worker proxy `tsukuroi.etzhayyim.com` (edge only,
  ADR-2605111200)
- **Runtime**: K8s LangServer pod `tsukuroi-langserver`; external MCP surface
  via the `kotodama` facade only (ADR-2605091400 cytoplasmic demotion)
- **Synthesis + validation**: egress-restricted namespace `tsukuroi-validate`
  with a NetworkPolicy reconciled from active mandates — egress allowed only
  to the owner-attested **git submission endpoint** (a fork remote), never to
  the live runtime target
- **Persistence**: kotoba datom (EAVT) + MST `com.etzhayyim.tsukuroi.*`; raw
  patch payloads + delegated credentials ciphertext in `vault.etzhayyim.com`
  (zero-knowledge invariant)

## R0 → R3 phases

- **R0** (this commit): charter + scaffold; 7 cell paths reserved (import-time
  RuntimeError); 5 Lexicon skeletons; registry row; zero runtime code.
- **R1** (Council Lv6+ ≥3 ratify + ≥1 filled Council seat beyond Founder Seat 1):
  3 core cells (`finding_intake`, `patch_synthesis`, `charter_rider_scan`) +
  kotoba datom schema; `patch-file` mode only (no PR submission); validated
  against a benign owned target / internal lab repo; findings internal.
- **R2** (+30-day public objection): + `patch_validation` + `pr_submission`
  (`fork-pr` mode) + `closure_verification`; first `silenTsukuroiReview`;
  first end-to-end against an internal repo under a signed mandate; first
  external mandate only after a benign owned-target dry run.
- **R3** (+Council Lv7+ for any submission_mode expansion beyond `fork-pr`;
  autonomous merge NEVER permitted): `config-diff` mode for infra; multi-target
  mandates; cross-actor federation — `toritate` (on-chain audit trail) +
  `chigiri` (mandate as covenant / UPL boundary) + `kataribe` (public
  remediation disclosure).

# Consequences

- The akuma diagnosis loop finally closes through a constitutionally-bounded
  remediation **proposer**, with the human owner retained at the merge gate.
- Separation of concerns is preserved as a **security boundary**: akuma
  (offensive-diagnosis, no write) and tsukuroi (defensive-remediation, no
  probe, propose-only) live in distinct egress-restricted namespaces. A
  compromise of either cannot trivially become the other.
- New attack surface: a forged owner/authority signature, or a leaked
  delegated credential, could let tsukuroi open PRs on arbitrary repos.
  Mitigations: dual-sig mandate, least-privilege expiring fork-PR-only
  credentials, the propose-only ceiling (no merge / no deploy), the
  egress-restricted `tsukuroi-validate` namespace, append-only audit, and a
  Bonsai seed-tier prune on any unauthorized write attempt.
- Adds maintenance: mandate lifecycle, credential rotation, sandbox build/test
  infrastructure, NetworkPolicy reconciliation against active mandates.

# Alternatives Considered

- **Extend akuma with patch submission**: rejected. It gives an
  offensive-diagnosis actor write-access to targets; a compromised
  akuma-with-write has a far worse blast radius, and it burns akuma's
  diagnosis identity. Two actors in two egress namespaces is the boundary.
- **Commercial auto-fix SaaS (Snyk Fix / Copilot Autofix / Mend Renovate
  paid)**: rejected — Charter Rider §2(e) anti-gatekeeping + §2(c), they hold
  credentials and ship code to vendor cloud (substrate boundary), and they
  violate Murakumo-only + non-profit-only.
- **Autonomous merge bot**: rejected — violates the no-server-key invariant
  (ADR-2605231525) and the propose-only ceiling; the human owner's merge
  decision is constitutional.
- **Skip the actor; humans author all patches**: viable but leaves akuma's
  loop open. tsukuroi is additive, propose-only, and keeps a human at the
  merge gate; it does not replace human review.

# References

- ADR-2605151400 (akuma — authorized red team actor; the diagnosis sibling)
- ADR-2605192100 (etzhayyim Mission Charter)
- ADR-2605192200 (Charter Compliance Rider v2.0 — §2(a) cyber-offense, §2(e)
  anti-gatekeeping)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2605231525 (server-side signing capability — no platform-held key)
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605091400 (MCP-as-cell-membrane — Lexicon/XRPC demotion)
- ADR-2605091800 (Pruning Protocol)
- ADR-2605262700 (chigiri — dispute mediation sink)
- ADR-2605240200 (Kaizen self-reflection — KaizenObserver health)
- ADR-2605290927 (junkan — negative-space gate precedent)
- `20-actors/tsukuroi/CLAUDE.md`
- `/CHARTER-RIDER.md` · `/COUNCIL.md`
