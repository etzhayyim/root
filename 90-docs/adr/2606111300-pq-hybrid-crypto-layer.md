---
id: adr-2606111300-pq-hybrid-crypto-layer
title: "ADR-2606111300: pqh-v1 post-quantum hybrid cryptography layer in @etzhayyim/sdk"
status: accepted
doc_type: adr
topic: pq-hybrid-crypto-layer
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "harvest-now-decrypt-later exposure on permanently public ciphertext"
authoritative_for:
  - post-quantum hybrid KEM and dual-signature suite (pqh-v1)
depends_on:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
related:
  - security-quantum-singularity-crypto-survivability
  - security-crypto-agility-policy
supersedes: []
superseded_by: []
---

# ADR-2606111300: pqh-v1 post-quantum hybrid cryptography layer in @etzhayyim/sdk

**Status**: accepted
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

The survivability analysis
(`90-docs/security/2606111200-quantum-singularity-crypto-survivability.md`)
established:

1. Every Shor-vulnerable primitive in the substrate (X25519 key agreement,
   Ed25519 DID/binding signatures, secp256k1 governance, P-256 passkeys)
   falls to a cryptographically relevant quantum computer; expert-survey
   median arrival ≈ 2040, ~20–35% cumulative probability by 2035, and
   ECC-256 falls *before* RSA-2048.
2. The symmetric layer (XChaCha20-Poly1305 / AES-256-GCM / SHA-256) is only
   Grover-bounded (proved quadratic limit, BBBV 1997) and thermodynamically
   un-brute-forceable (Landauer); it needs no change.
3. Mosca's inequality is already violated: etzhayyim ciphertext lives
   *permanently and publicly* on MST/IPFS/Base L2 (永久記憶 Tier-0, no right
   to erasure), so shelf-life x is effectively unbounded, migration y ≈ 3–5
   years across 50+ actors, while CRQC arrival z has median ~15 years.
   Harvest-now-decrypt-later collection of today's X25519 handshakes is a
   present-tense exposure, and signature forgery (DID takeover, governance
   forgery) becomes possible at CRQC arrival.
4. Per Charter §1.15 this is risk management, not eschatology: the threat
   window is dated, measurable, and inside the multi-generation (子・孫)
   priority horizon.

The `post_quantum-compat` actor (L4 research frontier) exists as schema-only;
nothing in the production seam was post-quantum.

# Decision

Introduce hybrid suite **pqh-v1** at the SDK seam (`20-actors/etzhayyim-sdk`),
AND-composed so an attacker must break BOTH the classical and the
post-quantum component:

1. **KEM**: X25519 + **ML-KEM-768** (NIST FIPS 203) via `src/pq.ts`
   (`generateHybridKemKeyPair` / `hybridEncapsulate` / `hybridDecapsulate`).
   Shared-secret combiner = HKDF-SHA256 over `ss_x25519 ‖ ss_mlkem` with the
   full transcript hash (ephemeral key, KEM ciphertext, recipient public
   keys) bound into `info` (X-Wing pattern), plus a caller-supplied
   DID-pair context. IND-CCA holds while EITHER component holds.
2. **Sessions**: `signal.ts` gains `establishSessionInitiator` /
   `establishSessionResponder` (pqh-v1). The legacy `establishSession`
   (local-only random key) is `@deprecated`, retained one R-cycle per
   `crypto-agility-policy.md` read-compat.
3. **Signatures**: `did-signal.ts` gains dual signing —
   `signSignalIdentityHybrid` (Ed25519 + **ML-DSA-65**, FIPS 204, over the
   same canonical CBOR bytes) and `verifySignalIdentityHybrid` (Ed25519
   always required; when the verifier knows the DID's PQ verification key,
   the ML-DSA signature is REQUIRED — downgrade-stripping fails closed).
   `SignalIdentityBody` optionally carries the actor's hybrid KEM public
   bundle (`pqSuite` / `pqX25519PublicKey` / `pqMlkemPublicKey`), covered by
   the binding signature(s) so a malicious PDS cannot substitute it.
4. **Seam rule**: apps MUST NOT import `@noble/post-quantum` directly;
   `@etzhayyim/sdk/pq` is the only entry point (mirrors the
   `@noble/ciphers` rule of ADR-2605181100).
5. **Unchanged by design**: XChaCha20-Poly1305 record envelopes, AES-256-GCM
   vault, SHA-256/Keccak/BLAKE2b. Symmetric/hash layers are post-quantum
   adequate; touching them adds risk without benefit.

# Consequences

- New session/key-wrap traffic and identity bindings become
  harvest-now-decrypt-later resistant and quantum-forgery resistant
  (AND-composition: security = max(classical, PQ)).
- Wire/record size grows: +1184 B KEM public key, +1088 B KEM ciphertext,
  +3309 B ML-DSA-65 signature, +1952 B ML-DSA verification key. Acceptable
  inside existing pad buckets ≥4096 (ADR-2605181200).
- New dependency `@noble/post-quantum` (^0.5.2, same noble family/audit
  lineage as existing ciphers/curves/hashes).
- Residual risk (tracked, out of this ADR's scope): secp256k1 governance
  signatures (chain-side constraint; mitigate by rotation + spend-before-z),
  PBKDF2→Argon2id (T3 implementation layer), libsignal PQXDH upstream
  adoption, ML-DSA verification methods in DID documents (enforcement flips
  after one R-cycle), pqh-v2 re-evaluation (ML-KEM-1024 / ML-DSA-87) ~2030.
- 200/200 SDK tests green incl. new `test/pq.test.ts` (roundtrip, implicit
  rejection, context separation, downgrade-strip rejection, cross-handle
  session interop); `tsc --noEmit` clean.

# Alternatives Considered

- **Pure PQ (drop X25519/Ed25519)** — rejected: lattice schemes are young;
  hybrid AND-composition hedges an ML-KEM/ML-DSA break at modest size cost
  (CNSA 2.0 tolerates pure PQ, but BSI/ANSSI recommend hybrid; etzhayyim's
  permanent-public ciphertext favors the conservative composition).
- **Wait for libsignal PQXDH to cover everything** — rejected: covers only
  the optional libsignal path, not the SDK's own session/binding seam, and
  leaves signatures classical.
- **SPHINCS+ (SLH-DSA) for signatures** — deferred: stateless-hash security
  assumptions are the most conservative, but 7.8–17 kB signatures break the
  1024-byte pad bucket economics; reconsider for the Council/governance tier.
- **Do nothing (non-eschatological framing)** — rejected: HNDL makes the
  exposure present-tense; §1.15 forbids eschatology, not risk management
  with dated, measurable windows.

# References

- `90-docs/security/2606111200-quantum-singularity-crypto-survivability.md` (companion paper)
- `90-docs/security/crypto-agility-policy.md` (suite versioning / read-compat)
- ADR-2605181100 (Tahoe-pattern AEAD + Signal binding), ADR-2605181200 (pad buckets)
- NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA); X-Wing (Connolly–Schwabe–Westerbaan 2024); Signal PQXDH
