---
id: adr-2605264400
title: manabi cert_prep — IT audit / infosec knowledge-domain study sub-cell (CISA / CISSP) R0
status: proposed
doc_type: adr
topic: manabi-cert-prep
authoritative: true
last_verified: 2026-05-26
authoritative_for:
  - manabi.cert_prep sub-cell charter (R0)
  - G15..G17 cert-prep-scope additional gates layered onto manabi G1..G14
  - N11..N13 cert-prep-scope additional non-goals layered onto manabi N1..N10
  - 3 lexicons: certPrepSession / personalMaterialImport / domainMasteryAttestation
related:
  - adr-2605261045
  - adr-2605261000
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605261045 (manabi master — G1..G14 + N1..N10 invariants this ADR extends)
  - ADR-2605261000 (Liberation Ladder — L5 vocational pathway)
  - ADR-2605192200 (Charter Rider §2(b) ad-free + §2(e) anti-gatekeeping)
  - ADR-2605181100 (encrypted envelope for adult session history)
  - ADR-2605262400 (Tier-C `internal_only` pattern for user-imported personal materials)
  - ADR-2605215000 (Murakumo-only inference for LLM assistance)
---

# ADR-2605264400: manabi `cert_prep` — IT audit / infosec knowledge-domain study sub-cell (CISA / CISSP) R0

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify R1)
**ADR Hierarchy**: Sub-charter under ADR-2605261045 (manabi master). Adds a sixth Pregel cell `cert_prep` alongside literacy / numeracy / civics_charter / vocational / lifelong_inquiry.

## Context

Adherent steward roles in the religious-corp substrate include (a) **IS audit-style competence** for charters_compliance attestation review + toritate ledger anomaly verification + chigiri.data_privacy DSAR audit, and (b) **information-security competence** for Murakumo fleet operation + encrypted envelope key management (ADR-2605181100) + Transparent Force open-source posture review (ADR-2605192315). These competences map naturally onto the **knowledge domains** covered by external certifications **CISA (ISACA — Certified Information Systems Auditor)** and **CISSP ((ISC)² — Certified Information Systems Security Professional)**.

Adherents preparing for these external credentials currently have no religious-corp-native study substrate. Existing alternatives in the wider market are uniformly **anti-aligned with manabi G3 (anti-addiction UX) and G10 (no-examination-as-coercion)**:

- gamified streak/leaderboard UX (Boson / Wiley / Pocket Prep / LearnZapp)
- ad-supported free tiers + upsell to paid (Pluralsight / Cybrary / Udemy)
- proctored mock exams with countdown timers as default
- pass-rate as the primary KPI displayed to learner ("87% chance of passing!")
- closed-source content licensed exclusively from credential body
- official past-question banks (ISACA Review Manual / (ISC)² Official Practice Tests) protected by strict copyright, not redistributable

Adherents preparing for CISA/CISSP today must use these adversarially-designed surfaces, which contradicts manabi's anti-addiction + anti-credentialism invariants even if the underlying knowledge domains are legitimate.

## Decision

Add a sub-cell `cert_prep` to manabi at `20-actors/manabi/cells/cert_prep/` covering **CISA CBK 5 domains** and **CISSP CBK 8 domains** as **knowledge-domain study substrate only**.

### Constitutional framing — how G7 anti-credentialism is preserved

manabi G7 (§2(e)) forbids manabi itself from issuing credentials, degrees, transcripts, GPA-equivalents. The CISA and CISSP credentials are **issued externally by ISACA / (ISC)²** — not by manabi. manabi `cert_prep` provides:

- **knowledge transmission** on IT audit + infosec domains (legitimately within manabi's scope)
- **practice through self-paced demonstration** (consistent with G10)
- **no credential, no transcript, no pass-rate KPI** (G7 preserved)

The relationship is analogous to manabi.vocational teaching mitsuho farming techniques (which an adherent may use whether or not they ever obtain a state agriculture license). The external credential is the adherent's optional individual choice; manabi's role stops at the knowledge boundary.

### Additional gates (layered on top of manabi G1..G14)

| Gate | Requirement | Rationale |
|---|---|---|
| **G15** | **No pass-rate KPI** — manabi MUST NOT collect, compute, display, or publish CISA/CISSP exam pass rates of `cert_prep` users. `silenEducationReview` cert_prep section reports only `sessionCount` and `domainCoverageBreadth`; pass-rate fields are schema-rejected. | Preserve G7 anti-credentialism; prevent credential-success-as-KPI drift |
| **G16** | **No official past-question reproduction** — schema-level enforcement. `certPrepSession.questionSource` is a closed enum: `synthetic-baien-generated` \| `user-imported-personal-only`. Values `official-isaca-reproduced` / `official-isc2-reproduced` / `commercial-test-bank-reproduced` are NOT valid enum members; any record carrying such source is rejected at PDS write time. | ISACA / (ISC)² official questions are copyright-protected; religious-corp distribution would violate §2(h) (state/proprietary IP infringement); user-purchased materials remain user-private (G17) |
| **G17** | **External credential body partnership PROHIBITED** — manabi shall not enter formal partnership / endorsement / affiliate-revenue / data-sharing agreement with ISACA, (ISC)², CompTIA, EC-Council, SANS, Offensive Security, or any other commercial credentialing body. Adherent's choice to sit for an external exam is their individual matter; religious-corp infrastructure stays uninvolved. | §2(b) ad-free + §2(e) anti-gatekeeping + §1.12 routing-around-state-and-state-aligned-bodies |

### Additional non-goals (layered on top of manabi N1..N10)

| # | Non-Goal | Deferral |
|---|---|---|
| **N11** | Pass guarantee / pass-rate prediction / "you have X% chance of passing" UX | Never (constitutional) |
| **N12** | ISACA / (ISC)² / CompTIA / EC-Council / SANS / Offensive Security formal partnership | Never (G17) |
| **N13** | Using cert_prep completion as an employment gate within religious-corp roles (e.g. requiring CISA for charters_compliance reviewer steward role) — adherent competence is judged by `skillAttestation` (subject-specific demonstration), not external credential possession | Never (reaffirms manabi G7 within cert_prep scope) |

### Question-source pathway (G16 detail)

Only two sources are constitutionally permitted:

1. **`synthetic-baien-generated`** — practice questions composed at request time by baien-moemoekyun (Murakumo fleet, judah LiteLLM gateway, per ADR-2605215000). Grounded in:
   - Public CBK domain outlines (the *outline structure itself* — domain names + topic areas — is published by ISACA / (ISC)² and is fair-use referenceable)
   - Tier-A public-domain specifications already in `e7m-dataset` per ADR-2605262400 / ADR-2605262800: NIST SP 800 series (public domain), ISO 27001 / 27002 / 27005 / 27017 / 27018 (purchasable but cited conceptually, not reproduced), COBIT 5/2019 framework descriptions (cited conceptually), Geneva Convention IHL (already ingested for chigiri), GDPR + APPI + CCPA (already ingested for ossekai)
   - Open-source legal corpus already ingested under ADR-2605262800 W1 (legal-foundations-r1 recipe)
   - Generated questions carry a deterministic `questionSeed` (sha256) so the same question can be regenerated for review without storing the question body persistently.

2. **`user-imported-personal-only`** — adherent uploads their personally-purchased study material (ISACA Review Manual, Wiley CISA/CISSP guide, Sybex official study guide, etc.) to the app. The material is:
   - Client-side XChaCha20-Poly1305 encrypted (per ADR-2605181100)
   - Stored as `personalMaterialImport` with `internalOnly: true` flag (per ADR-2605262400 Tier-C `internal_only` pattern)
   - Decryptable only by owner DID (passkey-derived key)
   - Never projected to public MST feed, never accessible to LLM training data, never shared between users
   - Right-to-erasure: owner-initiated hard delete on MST + IPFS pin release

This deliberately mirrors the **legal-corpus Tier-C carve-out** pattern from ADR-2605262400 W3 — the religious-corp substrate **carries the bytes for the owner** but **does not redistribute or relicense** them. The vendor's commercial relationship is between the adherent and ISACA / (ISC)² / Wiley / Sybex.

### LLM-assistance contract

LLM support routes through judah LiteLLM gateway (127.0.0.1:4000) → `baien-server-moemoekyun-*` (Murakumo fleet, ADR-2605215000). System prompt constitutionally constrains:

- **No praise / variable-reward language** — "正解です" + explanation only. Phrases like "Great job!", "完璧!", "Amazing progress!" are filtered at gateway response layer.
- **No pass-rate prediction** — refuses with "私は合格を予測できません。CBK 概念の理解を一緒に深めることだけ手伝えます。" (G15 + N11).
- **No official past-question reproduction** — refuses with "ISACA / (ISC)² の公式過去問は私は持ちません。CBK domain 概念から練習問題を合成します。" (G16). Even if a user paraphrases an official question into the chat, the LLM declines to confirm whether it matches an official question.
- **Cite the source** — every CBK statement carries reference to NIST SP / ISO XXX / COBIT framework section / Geneva Convention article (drawing on the legal corpus per ADR-2605262800).
- **Acknowledge uncertainty** — defer to external authority on points beyond CBK substrate.
- **Socratic pedagogy** — for "concept confusion" questions, return a question that helps the user reason, not a closed answer (manabi G13 inquiry-based ≥30% applies; cert_prep targets ~50% to bias toward inquiry).

### Data flow + privacy

```
adherent passkey
    │
    │ WebAuthn sign-in → did:web binding
    ↓
manabi-cert-prep PWA (60-apps/manabi-cert-prep/)
    │
    ├─→ concept reader (public CBK outlines, NIST/ISO/COBIT conceptual references, all open-source content)
    │
    ├─→ practice question request → @etzhayyim/sdk consent capability
    │       │
    │       ↓
    │   judah LiteLLM gateway → baien-server-moemoekyun-* (Murakumo, never RunPod / never OpenAI direct)
    │       │
    │       ↓
    │   synthetic question (deterministic seed)
    │
    ├─→ session attestation written via @etzhayyim/sdk
    │       │
    │       ↓
    │   XChaCha20-Poly1305 envelope (ADR-2605181100)
    │       │
    │       ↓
    │   MST as com.etzhayyim.encrypted.envelope wrapping com.etzhayyim.manabi.certPrepSession
    │       │
    │       └─ recipientDids: [owner DID] (only owner can decrypt)
    │
    └─→ personal material upload (R2+) → client-side encryption → personalMaterialImport (internalOnly: true)
```

**Forbidden** at every layer: keystroke tracking, gaze tracking, time-on-question per individual question, comparative ranking, per-user behavioral signals to LLM training, retention of question text bodies (only seeds), retention beyond owner's explicit choice.

### Aggregate review

For Council audit (G4 manabi-master + G14 silenEducationReview), an opt-in aggregate channel emits:
- `sessionCount` per domain
- `domainCoverageBreadth` (count of distinct concepts touched)
- k-anonymity ≥ 10 enforcement before any aggregate publication; if fewer than 10 adherents in any cohort, that cohort suppresses (no per-individual leakage)
- **never** pass-rate, never per-user identifier, never time-on-question, never error-rate

## Design

### Sub-cell layout

```
20-actors/manabi/cells/cert_prep/
├── __init__.py
├── domain_review.py        # CISA/CISSP CBK domain concept review (markdown-content cell)
├── practice_question.py    # baien-moemoekyun synthetic question generation cell
├── self_assessment.py      # self-paced demonstration cell (G10 — never time-limited by default)
└── personal_material.py    # Tier-C internal_only user-imported material cell (R2+)
```

All four cell modules raise `RuntimeError("manabi cert_prep R0 scaffold: ...")` on import per manabi-master R0 convention.

### Lexicons (3 new under `com.etzhayyim.manabi.*`)

1. **`certPrepSession`** — per-session attestation. Adult-only practical use; under-18 path inherits manabi G6 minor-aggregate-only via `learnerAgeBucket` discriminator. Closed enum on `questionSource` enforces G16 at PDS write time. Schema deliberately omits any `passRate` / `predictedScore` / `relativeRanking` field (G15 negative-space enforcement).

2. **`personalMaterialImport`** — user-imported study material record. `internalOnly: true` constant enforced structurally. `ownerDid` is single-recipient (no shared multi-recipient case at R0-R3).

3. **`domainMasteryAttestation`** — subject-specific skillAttestation-family record. Replayable demonstration of competence on a specific CBK domain topic. `credentialClaimedAttested: false` constant enforced structurally (this is NOT a credential — it is a demonstration record).

`silenEducationReview` (existing manabi master Lexicon) gains an optional `certPrepSection` sub-object schema covering only `sessionCount` and `domainCoverageBreadth` per gate G15.

### PWA app (sibling of mitate-pwa)

```
60-apps/manabi-cert-prep/
├── README.md
├── package.json                # apache-2.0 + charter rider notice
├── tsconfig.json
├── wrangler.jsonc              # CF Worker + assets binding
├── kotodama.jsonld             # actor manifest fragment
├── src/
│   └── app.ts                  # thin dispatcher (R0-R1 mostly static; R2+ routes substrate proxy)
├── public/
│   ├── index.html              # calm entry — no streak / no badge / no leaderboard
│   ├── domains.html            # CISA 5 + CISSP 8 flat list (no completion %)
│   ├── study/
│   │   ├── cisa.html           # 5 domain readers, markdown concept content
│   │   └── cissp.html          # 8 domain readers, markdown concept content
│   ├── history.html            # local-storage cumulative log (no chart, no progress bar)
│   ├── calm.css                # calm palette, no animation
│   └── calm.js                 # next/prev navigation, no auto-advance, structural no-streak
└── tests/
    ├── g15-no-pass-rate-kpi.test.ts
    ├── g16-no-official-question-source.test.ts
    ├── g3-no-addiction-ux-tokens.test.ts
    └── w1-no-llm-call-yet.test.ts
```

R0 = scaffold only; R1 adds live LLM via judah gateway (deferred to Wave 2 commit, separate ADR not required if scope unchanged).

## Roadmap

| Phase | Date | Scope | Gate |
|---|---|---|---|
| **R0** (this commit) | 2026-05-26 | ADR + 3 Lexicon schemas + 4 cell stubs + PWA W0/W1 (static UI, no LLM) + tests | This ADR (PROPOSED) |
| **R1** | post-Council ratify | Wire judah LiteLLM gateway + baien-moemoekyun synthetic-question generation; encrypted-envelope session persistence; ≤50 adherent users | manabi master R1 + Council Lv6+ ≥3 ratify of this sub-charter |
| **R2** | post-R1 + 30-day public objection | `personal_material` cell active (Tier-C internal_only); `self_assessment` cell active; ≤500 adherents | 30-day public objection close |
| **R3** | post-R2 + manabi master R3 | Integrated with L5 Vocation pathway: charters_compliance reviewer steward + toritate audit steward + Murakumo operator steward as recognized vocational tracks gated on `domainMasteryAttestation`, never on external credential possession (G7 + N13) | manabi master R3 |

## Consequences

**Positive**:
- Adherent steward competence pathway opens for IS-audit and infosec roles without surrendering manabi's anti-addiction / anti-credentialism invariants.
- The "honest sibling" of Boson / Pluralsight / Cybrary exists — adherents who would otherwise study on adversarial gamified platforms have a calm-UX alternative.
- Knowledge transfer leverages already-ingested Tier-A legal/spec corpus (NIST, ISO citations, GDPR/APPI/CCPA, Geneva Conventions); no new content licensing problem.
- Encrypted-envelope persistence pattern (ADR-2605181100) gains its second adoption (after iyashi clinical-encounter), strengthening the substrate primitive.

**Negative / risks**:
- G15 (no pass-rate KPI) means adherents cannot self-assess "am I ready for the exam?" via the app. Mitigation: external mock-exam services or self-judgment from `domainCoverageBreadth` per-domain coverage count.
- G16 (no official past-question reproduction) is enforceable at our schema but cannot prevent an adherent from copying official questions into a chat session. Mitigation: LLM system-prompt-level refusal (described above); honest framing that adherents using personal material take individual copyright responsibility (`personalMaterialImport.licenseAcknowledgment` field captures this).
- R1 requires Council ratify — until then the app is W0/W1 static (no LLM); adherents wanting practice generation must wait or use synthetic-baien-generated as offline pre-seeded set.

## Alternatives Considered

1. **Stand alone Tier-B actor** (`tameshi`) — rejected: anti-credentialism framing is *easier* as a manabi sub-cell since the master invariants (G3 + G7 + G10) auto-inherit. Standalone actor would force re-stating each invariant and risks divergence.
2. **`70-tools/cert-prep/` as a pure tool, no actor surface** — rejected: encrypted session persistence (ADR-2605181100) requires actor DID for envelope addressing; pure tool path cannot bind to `com.etzhayyim.encrypted.*` recipientDids cleanly.
3. **Reproduce a curated subset of "publicly leaked" past questions** — rejected: §2(h) IP infringement; no fair-use defense for systematic reproduction; reputational risk for the charter as a whole.
4. **Partner with ISACA / (ISC)² for official content** — rejected: G17 — external credential body partnership constitutionally prohibited; would entangle religious-corp infrastructure with for-profit credentialing economics.

## Notes

### Landing path — WIP catch-all sweep precedent

W0+W1 deliverables of this ADR were landed via commit
`67d2d5a0e chore(wip): concurrent session WIP catch-all — energy D-gate ADR wave + 4 Tier-B actor R0 scaffolds + manabi cert-prep + sim scenes + sensor fetchers`
rather than a dedicated `feat(manabi-cert-prep)` commit.

Root cause: a parallel session's lefthook pre-commit hook (`e7m-verify`) was
holding the index when my working tree finished writing; the next concurrent
session's commit swept my staged tree along with its own unrelated work into
one WIP catch-all commit. This is the same pattern documented in
ADR-2605264300 §1 Notes (which canonically named the SDK three.js cutover
content for an analogous WIP sweep).

**Functional outcome correct, commit-message hygiene impacted.** The bytes
attributed to the sweep — under `60-apps/manabi-cert-prep/` (app skeleton +
calm UI + 4 anti-addiction tests) + `20-actors/manabi/cells/cert_prep/`
(4 cell stubs) + `00-contracts/lexicons/com/etzhayyim/manabi/` (3 new lex) +
this ADR + deps.toml + CLAUDE.md row 75 + adr/README.md row + manabi
manifest update — exactly match the W0+W1 scope declared in §Design above.

`git log -- 60-apps/manabi-cert-prep/` correctly attributes all files to
that commit. This §Notes is the canonical reference for the actual content
intent.

R1+ commits should land via normal `feat(manabi-cert-prep)` scopes once the
concurrent-session race window passes.

## References

- ADR-2605261045 (manabi master — invariants extended here)
- ADR-2605261000 (Liberation Ladder L5)
- ADR-2605192100 (Mission Charter §1.6 anti-individualism + §1.12 routing-around)
- ADR-2605192200 (Charter Rider §2(b) + §2(e) + §2(h))
- ADR-2605181100 (encrypted envelope record — adult session history)
- ADR-2605262400 (Tier-C `internal_only` pattern — personal material precedent)
- ADR-2605262800 (legal corpus — NIST/ISO/COBIT/IHL/privacy law substrate)
- ADR-2605215000 (Murakumo-only inference — LLM routing constraint)
- ADR-2605260100 (mitate self-care PWA — sibling app pattern)
- ADR-2605264300 §1 Notes (parallel-session WIP sweep precedent for SDK three.js cutover)
