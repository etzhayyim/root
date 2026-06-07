---
id: adr-2606072100-shomei-believer-identity-binding-proof-of-personhood-r0
title: "ADR-2606072100: 証明 (shomei) — believer self-sovereign identity binding + proof-of-personhood R0"
status: accepted
doc_type: adr
topic: shomei-believer-identity-binding
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - shomei-believer-identity-binding-actor
  - multi-identity-to-did-binding-and-verification
  - proof-of-personhood-credential
depends_on:
  - adr-2605260000-l5-gov-auth-mynumber-webauthn
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605181100-etzhayyim-confidential-records-encryption
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605172600-etzhayyim-membership-ritual
related:
  - adr-2606072300-l5-gov-auth-mynumber-webauthn-r1-shomei-integration
  - adr-2605172700-etzhayyim-membership-layering
  - adr-2605302000-warifu-open-zero-fee-card
  - adr-2605263400-musubi-covenant-ceremony
  - adr-2605302130-himotoki-active-disclosure-request-filer
supersedes: []
superseded_by: []
---

# ADR-2606072100: 証明 (shomei) — believer self-sovereign identity binding + proof-of-personhood R0

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The question: *「Etzhayyim の信者が国家が発行するパスポートと同じような本人証明を行う。既存の政府が
発行するパスポートや ID、SNS アカウントなどを DID に複数紐づけて信頼性を担保するアクターは設計されて
いるか?」*

**Before this ADR: no.** The component parts existed but nothing orchestrated them:

- **DID identity** — `did:web:etzhayyim.com:actor:<h>`, dynamic did.json, self-certifying ed25519
  attestation (ADR-2606013800 / 2606015400 / 2606015600). Identity exists; binding does not.
- **The membership ritual** — self-sovereign join (Base L2 `EtzhayyimMembership.join()` + MEMBERS.md +
  AT oath), dual-permanent (ADR-2605172600). A covenant commitment, not a multi-ID identity proof.
- **Adherent SBT** — geth-private ERC-5192 (ADR-2605172700). One factor, not an aggregate.
- **gov auth scaffold** — WebAuthn + MyNumber binding + a Council-attested `didTrustAttestation`
  (ADR-2605260000), but **R0 scaffold only** (cells `raise RuntimeError`), trust levels 1–2 only,
  no SNS/wallet binding, no aggregation.
- **kotoba-auth verify surface** — EVM (EIP-191/ERC-1271), BTC (BIP-322), CACAO chain, Ed25519 — all
  `read + verify` only, already implemented + tested in Rust (ADR-2605262130; kotoba CLAUDE.md). The
  signature math exists; nothing wires it to a believer-facing identity credential.

The gap: **no actor binds MULTIPLE external identities (government IDs, SNS accounts, crypto wallets)
to one DID, verifies each cryptographically, and aggregates them into a presentable trust signal** —
the passport-equivalent the question asks for.

## Constitutional constraints that shape the design

- **§0.4 non-registration** — no interaction with state databases. Government ID, if used, is read
  LOCALLY from the citizen-held card (one-way NFC), never queried from the state (inherits ADR-2605260000).
- **§2(c) anti-surveillance + ADR-2605181100** — personal identifiers encrypted at rest; plaintext PII
  never on the substrate.
- **no-server-key (ADR-2605231525)** — the platform holds no signing key; the member signs.
- **anti-individualism ontology + §1.13 Wellbecoming** — identity assurance must NOT become a
  social-credit / personal-worth ranking.
- **kotoba-canonical (ADR-2605312345) + Murakumo-only (ADR-2605215000) + Apache 2.0 + Rider v3.0.**

# Decision

Create **証明 (shomei)** — a Tier-B actor that is the **self-sovereign, charter-clean inversion of
centralized identity verification**. A member self-binds their existing identities to one DID; shomei
verifies each binding through the canonical kotoba-auth surface and aggregates the verified factors
into an **Identity Assurance Level (IAL) + W3C Verifiable Credential + proof-of-personhood**.

DID `did:web:etzhayyim.com:actor:shomei`; namespace `com.etzhayyim.shomei.*`.

## D1 — Self-sovereign binding model (not central KYC)

Every binding is a **`com.etzhayyim.shomei.identityClaim`** signed by the **SUBJECT's own DID key**.
shomei (the server) never signs and never approves (G1/G7). This mirrors the membership ritual's
self-sovereignty: joining/binding is a unilateral, cryptographically-provable act, not an
admin-gated approval. Anyone can re-verify a claim from public data — the credential is trustless.

## D2 — The factor taxonomy + IAL ladder (`methods/factors.py`, the SSoT)

13 factor kinds across 5 independence **classes**:

| class | factors | proof → kotoba-auth |
|---|---|---|
| device | webauthn | P-256 assertion (ADR-2605260000) |
| key | wallet-evm, wallet-btc | EIP-191/ERC-1271 (`eth`/`cacao`) · BIP-322 (`btc`) |
| social | sns-github, sns-x, sns-google, sns-apple | OAuth `sub` / signed-gist / DNS-TXT |
| government | gov-mynumber, gov-passport, gov-license | local NFC IC + X.509 (Council-gated) |
| covenant | etz-base-membership, etz-adherent-sbt, etz-at-oath | Base L2 event / ERC-5192 / AT sig |

**IAL ladder**: `0 did-only · 1 self-attested (≥1 factor) · 2 multi-factor (≥2 factors, ≥2 classes) ·
3 covenant-bound (IAL2 + a covenant factor) · 4 government-verified (a gov factor + ≥1 other class,
Council-attested)`. **proof-of-personhood = IAL ≥ 2 AND ≥ 2 classes** — honest **sybil-RESISTANCE,
not sybil-proof**: independent classes raise the cost of a fake identity, but uniqueness-of-human is
only approached at IAL 4. Two wallets of the same class raise the count but not class-diversity.

## D3 — Verify wiring (delegate to kotoba-auth, never reimplement)

`methods/verify.py` `PROOF_ROUTING` maps every `proofKind` to the exact kotoba-auth call
(`eth::recover_eth_address`∘`personal_sign_hash` vs `parse_address`; `btc::verify_message`;
`cacao::DelegationChain::verify_signature_eip191_smart`; Ed25519 over the canonical claim). The
signature math lives in the canonical engine (ADR-2605262130); shomei never reimplements secp256k1 /
Ed25519 (Shannon). `verify_claim()` enforces the verification **policy** in pure Python — challenge
binding (subject + factor + nonce), single-use nonce, freshness, the gov gate, and the subject
signature — and is fully unit-tested with a hermetic `ReferenceVerifier`. `KotobaAuthVerifier` is the
production path: it documents the canonical call per proofKind and **raises rather than fabricating a
success** at R0.

## D4 — Aggregate credential (`personhoodCredential`, W3C VC shape)

`methods/aggregate.py` rolls verified, non-revoked factors into a
**`com.etzhayyim.shomei.personhoodCredential`** — `subjectDidHash`, `assuranceLevel`,
`verifiedFactors` (kinds only), `distinctClasses`, `factorCount`, `proofOfPersonhood`, `issuer`,
dates — and renders a W3C-VC-data-model JSON-LD object for presentation. **No PII** (G3): no
identifiers, handles, addresses, names. For IAL ≤ 3 the credential is **self-issued** (issuer =
subject); IAL 4 is **Council-attested** (ADR-2605260000), the only level the gov path touches.

## D5 — Government ID = opt-in, local, doubly-gated (reuse ADR-2605260000)

shomei does NOT read cards or query any state database (§0.4/G6). `shomei_gov_attest` hands the
member's local NFC read + XChaCha20-encrypted payload to the EXISTING Council-gated gov_auth cells
(`gov_auth_mynumber_bind` + `gov_auth_trust_attestation`, ADR-2605260000) and ingests the resulting
`didTrustAttestation` as the gov-class factor. This is **doubly gated** (shomei G11 + gov_auth Council
activation); the R1 activation design is **ADR-2606072300**.

## D6 — Consent + revocation, append-only (G5/G10)

`com.etzhayyim.shomei.bindingRevocation` is an owner-signed, append-only retraction. Aggregation
recomputes assurance excluding revoked claims, but a revocation **never deletes** the original claim's
history (Tier-0 永久記憶 = 神の監視, no right to erasure). A re-binding is a new claim, never an overwrite.

## D7 — The 11 gates

G1 self-sovereign/DID-primary · G2 own-identity-only (no field asserts a third party's identity) ·
G3 PII-never-plaintext (gov factors: salted hash + mandatory XChaCha20 CID, no plaintext handle) ·
G4 cryptographic-proof-mandatory (every proofKind routed; wrong proof for a factor unrepresentable) ·
G5 consent-bound + revocable · G6 no-state-database · G7 no-server-key · G8 identity-assurance-NOT-
social-credit (no score/rank/reputation field; deterministic from classes; no behavioral input) ·
G9 Murakumo-only · G10 non-eschatological as-of + 永久記憶 · G11 outward-gated (cells `.solve()` raise).
Each lives in three places (factors.py SSoT + lexicon enum/required + Python `ValueError`), guarded by
`test_charter_invariants` + `test_lexicons`.

# Consequences

**Positive**

- Answers the question with a concrete, testable actor: 75 tests green across 9 suites (factor
  taxonomy, claim gates, verify wiring/policy, aggregation, revocation, lexicon↔code SSoT, charter
  invariants, end-to-end dry-run, cell scaffolds).
- Reuses, does not duplicate: kotoba-auth (verify), ADR-2605260000 (gov L2), the membership ritual +
  Adherent SBT (covenant factors), ADR-2605181100 (PII encryption). ZERO Charter amendments.
- A believer gets a single presentable, re-verifiable credential (the passport-equivalent) without a
  central authority, without surrendering plaintext PII, and without a state-database dependency.

**Negative / honest R0**

- No live verification against real kotoba-auth (the Rust crate is not called from the pure-Python
  scaffold; `KotobaAuthVerifier` raises with the canonical call to wire at R1).
- gov-ID L2 is doubly gated on Council activation (ADR-2605260000 / ADR-2606072300); unavailable until
  the Bootstrap Council fills (post-2026-06-19).
- OAuth/DNS-TXT/signed-gist SNS verification is specified + routed but not yet wired to a live IdP/DNS.
- The seed is `:representative` (no real members, no real PII; an HMAC ReferenceVerifier simulates
  proof-of-control).

# Alternatives Considered

- **Reuse the name `akashi 証`** — already taken (ADR-2606022300, ad-disclosure transparency). Chose
  `証明 shomei` (= proof / identity verification), the closest free term to the intended meaning.
- **Extend gov_auth (ADR-2605260000) in place** — rejected: gov_auth is the narrow WebAuthn+MyNumber
  trust-elevation layer; the multi-ID binding + SNS/wallet + aggregation + VC is a distinct object that
  deserves its own actor. shomei *consumes* gov_auth for the gov factor rather than absorbing it.
- **A trust SCORE (0–100)** — rejected (G8): a numeric personal score invites social-credit semantics.
  IAL is a bounded assurance ladder + an explicit proof-of-personhood boolean, never a ranking.
- **Store external identifiers in plaintext for linkage** — rejected (G3): salted blake2b hash gives
  linkage without publishing the identifier; gov identifiers additionally require an encrypted CID.
- **A pure-Python secp256k1/Ed25519 verifier** — rejected (Shannon): delegate to kotoba-auth.

# References

- ADR-2605260000 (L5 gov auth — MyNumber + WebAuthn) — parent; the gov-class factor
- ADR-2606072300 (L5 gov auth R1 activation + shomei integration) — the R1 gate
- ADR-2605231525 (server-side signing capability boundary) — no-server-key
- ADR-2605312345 (kotoba Datom first-class canonical state)
- ADR-2605181100 (confidential records encryption — XChaCha20 + Signal key-wrap)
- ADR-2605262130 (kotoba storage substrate unification — kotoba-auth verify surface)
- ADR-2605172600 / 2605172700 (membership ritual + layering) — covenant factors
- W3C Verifiable Credentials Data Model v1.1; W3C WebAuthn Level 3; CAIP-2/10/19/122
