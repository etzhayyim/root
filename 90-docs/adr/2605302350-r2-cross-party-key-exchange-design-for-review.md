---
id: adr-2605302350-r2-cross-party-key-exchange-design-for-review
title: "ADR-2605302350: R2 cross-party key exchange for encrypted records — DESIGN FOR REVIEW (signal.ts X25519 ECDH sealed-box)"
status: proposed
doc_type: adr
topic: r2-cross-party-key-exchange
authoritative: false
last_verified: 2026-05-30
priority: 7.0
axis: security
weight: 0.70
priority_note: "DESIGN-ONLY ADR (authoritative:false, status:proposed) for the highest-priority confidentiality gap. The current signal.ts (R1.0) is an in-memory, same-process XChaCha20 PLACEHOLDER — it does NOT perform real cross-party key agreement, so encrypted records are not yet true end-to-end encrypted across distinct parties/PDSes. This ADR specifies the R2 design (per-recipient X25519 ECDH sealed-box / ECIES) so a human cryptographer + Council can review it BEFORE any implementation. It does NOT change code. Crypto correctness ≠ round-trip test success; implementation MUST be gated on review (cryptographer sign-off + Council Lv6+), never landed autonomously. Supersedes nothing; sets the design contract that a future R2 implementation PR must satisfy."
authoritative_for: []
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
related:
  - adr-2605231525-no-server-key-religious-corp-architecture
supersedes: []
superseded_by: []
---

# ADR-2605302350: R2 cross-party key exchange for encrypted records — DESIGN FOR REVIEW

**Status**: proposed (DESIGN-ONLY — not implemented; gated on cryptographer + Council review)
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki (+ pending cryptographer review)

# Context

`@etzhayyim/sdk`'s confidentiality layer (ADR-2605181100 Tahoe-on-MST) encrypts each
private record under a fresh symmetric envelope key, then **wraps that key per recipient**
so only intended recipients can open it. The original implementation used libsignal
(X3DH prekey bundles → real per-recipient session keys).

Commit `a590e7f64` replaced libsignal with a simpler `signal.ts`, and PR #291 completed
the `encrypted.ts` migration so the SDK builds + the E2E tests pass. **But the current
`signal.ts` is an R1.0 placeholder**: `establishSession` generates a random 32-byte key
and stores it in an in-memory `Map`; `wrapKey`/`unwrapKey` XChaCha20-seal/open under that
key. The recipient can only `unwrapKey` if the session (key) is in *their* process memory.

Consequence (stated honestly in PR #291): **the encrypted records are NOT real cross-party
E2E**. They round-trip only same-process (the test rig shares one module singleton). A real
recipient on a different node/PDS cannot decrypt, because the wrap key never reaches them.
This is the single highest-priority confidentiality gap.

This ADR specifies the **R2 design** so it can be reviewed *before* code is written. It is
explicitly **not** an implementation; per the security principle that crypto must not be
guessed into a merge, an R2 implementation PR is gated on cryptographer sign-off + Council
Lv6+ and MUST satisfy this contract.

# Decision (proposed design — for review)

## D1. Per-recipient X25519 ECDH sealed-box (ECIES), no shared session state

Replace the in-memory session with a **stateless per-recipient sealed box** (the NaCl
`crypto_box_seal` / ECIES pattern), so the sender needs only the recipient's PUBLIC key
and the recipient needs only their own PRIVATE key — no transmitted session secret.

Recipient long-term identity (published, DID-bound per ADR-2605181100):
- An **X25519** key pair. The public key is the `signalIdentityKey` already carried in
  `com.etzhayyim.encrypted.signalIdentity` and signed by the DID key
  (`signSignalIdentity` / `verifySignalIdentity` — unchanged, the authenticity gate).

Wrap (sender), per recipient, over the envelope symmetric key `K`:
1. generate an ephemeral X25519 pair `(e_priv, e_pub)`;
2. `shared = X25519(e_priv, recipient_pub)`;
3. `wrapKey = HKDF-SHA256(ikm=shared, salt=H(e_pub ‖ recipient_pub), info="etzhayyim/encrypted/keywrap/v2")`;
4. `ct = XChaCha20-Poly1305(key=wrapKey, nonce=random24, aad=senderDid‖recipientDid‖keyId).encrypt(K)`;
5. emit `e_pub` + `nonce` + `ct` in the keyWrap record.

Unwrap (recipient): recompute `shared = X25519(self_priv, e_pub)`, derive `wrapKey` the
same way, AEAD-open. No shared state; works across parties/PDSes.

## D2. keyWrap lexicon change (`com.etzhayyim.encrypted.keyWrap`)

Add `ephemeralPubKey: bytes` (the sender's `e_pub`). The R1.0 fields `signalSessionId`
becomes vestigial (kept for one cycle as optional, then removed). `ciphertext` carries the
nonce-prefixed AEAD output as today. Version bump `v: 2`. A reader MUST reject `v:1`
records once R2 ships (they cannot be opened cross-party and must be re-wrapped).

## D3. SDK API (signal.ts) shape

- `deriveSharedWrapKey({selfPriv | ephemeralPriv, peerPub, e_pub, recipientPub}) -> Uint8Array`
- `sealKey({recipientPub, symKey, aad}) -> { ephemeralPubKey, ciphertext }`
- `openKey({selfPriv, ephemeralPubKey, ciphertext, aad}) -> symKey`
- `establishSession` is removed (no session). `encrypted.ts` calls `sealKey`/`openKey`.
- The recipient's X25519 **private** key re-enters the read path (a `StandaloneReadDeps.selfX25519Priv`), held only by the member (no-server-key ADR-2605231525 — never platform-held).

## D4. Security requirements the implementation MUST meet (review checklist)

- X25519 from an audited library (`@noble/curves/ed25519` → `x25519`); correct clamping
  (the library handles it — do NOT hand-roll).
- HKDF salt binds **both** public keys (`e_pub ‖ recipient_pub`) so a wrap is bound to the
  intended recipient (anti key-reuse / unknown-key-share).
- AEAD `aad` binds `senderDid ‖ recipientDid ‖ keyId` so a keyWrap cannot be replayed onto
  a different envelope or recipient.
- Fresh ephemeral per wrap (no ephemeral reuse across recipients/records).
- Random 24-byte XChaCha20 nonce per wrap; never reused under a derived key.
- DID-binding of the published X25519 key is verified (`verifySignalIdentity`) BEFORE wrap
  — unchanged authenticity gate (already in `encrypted.ts`).
- **Forward secrecy is NOT provided** by sealed-box (recipient long-term key compromise
  reveals all past wraps). If FS is required, the design escalates to X3DH/double-ratchet —
  an explicit R3 decision, out of scope here. State the FS posture in the impl.
- Round-trip + tamper tests are necessary but NOT sufficient: the review MUST include an
  adversarial read (wrong recipient cannot open; tampered `e_pub`/`aad`/`ct` fails;
  cross-envelope replay fails).

## D5. Migration from R1.0

- `signal.ts` R1.0 in-memory functions are removed; `encrypted.ts` `sealKey`/`openKey`.
- keyWrap `v:1` records (placeholder) are non-portable; on R2 deploy, the affected members
  re-wrap (or the records are treated as unreadable). Because R1.0 only ever worked
  same-process, there is no real cross-party `v:1` data at risk.
- The 2 E2E tests gain real cross-party coverage: wrap with recipient PUBLIC key only,
  clear all sender state, open with recipient PRIVATE key only — proving no shared secret.

## D6. Process gate (CONSTITUTIONAL for this change)

An R2 implementation PR MUST NOT be merged without: (a) a cryptographer review against the
D4 checklist; (b) Council Lv6+ approval (confidentiality layer is member-data-critical);
(c) the adversarial test suite of D4 green. It MUST NOT be produced or merged by an
autonomous agent. This ADR is the reviewable contract; it changes no code.

# Consequences

**Positive**
- Closes the headline confidentiality gap: encrypted records become real cross-party E2E.
- Stateless sealed-box is simpler + more auditable than session/ratchet; reuses the existing
  DID-binding authenticity gate and the no-server-key posture (private key stays member-held).
- Reviewable BEFORE code exists — the safe way to evolve a confidentiality layer.

**Negative / costs**
- No forward secrecy (sealed-box limitation) — acceptable for at-rest record wraps; FS is a
  separate R3 escalation if threat model demands it.
- keyWrap `v:1` → `v:2` is a breaking record change; needs a re-wrap path.
- Re-introduces the recipient X25519 private key into the read path (member-held only).

**Risks**
- Subtle crypto errors (HKDF inputs, aad binding, nonce handling) that pass round-trip but
  weaken security. Mitigation: D4 checklist + D6 mandatory cryptographer review; this ADR
  exists precisely so the design is scrutinised before implementation.

# Alternatives Considered

1. **Keep R1.0 in-memory placeholder** — rejected: not real E2E; encrypted records are
   effectively same-process-only. The honest current state, not an end state.
2. **Restore libsignal X3DH + double-ratchet** — heavier (sessions, prekey management,
   ratchet state) and was the thing `a590e7f64` removed; provides forward secrecy. Deferred
   to R3 if the threat model requires FS; sealed-box (R2) is the right next step otherwise.
3. **Autonomous-agent implementation now** — rejected (D6): the confidentiality layer must
   not be evolved by an agent without human cryptographer review. This ADR is the substitute:
   design first, implement under review.

# References

- ADR-2605181100 (MST encrypted records + key-wrap — the layer this evolves)
- ADR-2605181200 (encrypted-record metadata-leak reduction)
- ADR-2605231525 (no-server-key — recipient private key stays member-held)
- PR #291 (signal→XChaCha20 build fix; recorded the R1.0 placeholder limitation) · PR #292 (E2E tests)
- NaCl `crypto_box_seal` / ECIES (the sealed-box pattern); `@noble/curves` x25519 + `@noble/hashes` HKDF
