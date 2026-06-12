---
id: adr-2606014001-kotoba-passkey-cacao-signal-secrecy
renumbered_from: "2606014000"
title: "ADR-2606014001: kotoba Passkey-Rooted Secrecy — WebAuthn PRF → ARK → CACAO authz + Signal messaging"
status: proposed
doc_type: adr
topic: kotoba-passkey-cacao-signal-secrecy
authoritative: true
last_verified: 2026-06-01
priority: 9.0
axis: architecture
weight: 0.95
priority_note: "Unifies kotoba's at-rest secrecy, authorization, and user↔user messaging under a single passkey-rooted key hierarchy; closes the four live crypto gaps (server KEK, missing AAD, unwired Signal, passkey-as-auth-only) without violating the no-server-key invariant."
authoritative_for:
  - kotoba-secrecy-architecture
  - passkey-key-derivation
  - vault-aead-binding
  - did-signal-binding
depends_on:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605291100-manimani-kotoba-native-reconciliation-gmail-pc-ingest
related:
  - adr-2605240001-kotoba-cleanroom-architecture
  - adr-2605212030-etzhayyim-did-strategy
supersedes: []
superseded_by: []
---

# ADR-2606014001: kotoba Passkey-Rooted Secrecy — WebAuthn PRF → ARK → CACAO authz + Signal messaging

**Status**: proposed
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

kotoba already ships strong, tested cryptographic primitives, but they are not
yet composed into one coherent secrecy architecture. An honest audit of the
live code (2026-06-01) found four gaps between what the ADRs *claim* and what
the code *does*:

1. **Server-held KEK still live.** `60-apps/etzhayyim-project-auth/worker`
   declares `SS_REPO_SIGNING_KEK` (AES-256 envelope KEK) and uses it to wrap
   every per-agent ES256 key in D1. A single platform key unlocks every
   credential — a direct violation of the no-server-key invariant
   (ADR-2605231525).
2. **`SecureVault` seals without AAD.** `kotoba-kse/src/secure_vault.rs` calls
   `aead::seal(key, plaintext)` with no associated data, so a ciphertext blob
   is not cryptographically bound to its content address (CID). Blobs can be
   swapped undetected at the storage layer. This is the manimani PII path
   (ADR-2605291100), so it matters most.
3. **Signal is implemented but not wired.** `kotoba-signal/` has a full
   pure-Rust X3DH + Double Ratchet, but `kotoba-crypto/src/key_wrap.rs` wraps
   per-record keys with a *static* AES-256-GCM key — no forward secrecy, no
   ratchet, no DID↔Signal binding. ADR-2605181100 mandates Signal-wrapped keys
   for user↔user records.
4. **Passkey is authentication-only.** `kotoba-auth/src/passkey.rs` is a clean
   `PasskeyGate` (UP/UV/TTL policy per `KeyOpKind`), but it derives **no key
   material**. Encryption keys are therefore generated elsewhere and — today —
   wrapped by the server KEK (gap 1). The WebAuthn **PRF extension**
   (`hmac-secret`), the one primitive that lets a passkey deterministically
   derive a symmetric secret, is unused.

What kotoba already has and we will *build on*, not replace:

- **CACAO (CAIP-74)** — `kotoba-auth/src/cacao.rs` + `delegation.rs`: EdDSA
  (`did:key`/`did:web`/`did:plc` via resolver) **and** EIP-191 with ERC-1271
  smart-account verification (`verify_signature_eip191_smart`), depth-2
  delegation with capability/graph attenuation, strict-UTC expiry, single-use
  nonce store (DashMap-sharded). Resources already model
  `kotoba://op/{datom:read,datom:transact}` + `kotoba://graph/{cid}` +
  `didcomm://thread/{id}` + `at://…`.
- **`PasskeyGate` + `KeyHierarchy`** — `kotoba-auth/src/passkey.rs`: the
  `KeyHierarchy` struct already names the four key references we need
  (`eth_account`, `signal_identity_pub`, `storage_dek_cid`, `recovery_key_cid`)
  and stores **no plaintext key material**.
- **`kotoba-crypto`** — tested AES-256-GCM AEAD, HKDF-SHA256, HPKE (X25519
  ECIES), key-wrap, `AgentCrypto` trait with scope-derived keys.
- **`SovereignCrypto`** — `kotoba-kse/src/sovereign_key.rs`: vault-key
  genesis/rotation, HPKE-wrapped key blobs in the BlockStore.

The missing piece is not primitives — it is **one key hierarchy that ties them
together with the passkey at the root**, so that (a) the server never holds a
wrapping key, (b) every at-rest blob is CID-bound, (c) user↔user messages get
Signal forward secrecy, and (d) the passkey actually *produces* the keys
instead of merely *gating* them.

# Decision

Adopt a single passkey-rooted key hierarchy. One root authenticator (the
WebAuthn passkey) anchors three planes — **secrecy** (data at rest),
**authorization** (CACAO), and **messaging** (Signal) — through a deterministic,
labeled derivation tree. No layer below the device ever sees a wrapping key in
plaintext.

## The key hierarchy (one picture)

```
L0  Root authenticator — hardware-bound, non-extractable
    WebAuthn Passkey  (Secure Enclave / TPM / Android Keystore)
     ├─ assertion(sign)              → authentication + CACAO session binding (L4)
     └─ PRF / hmac-secret extension  → S_prf,i = PRF(credential_i, salt_account)   [32 B, per device]

L1  Account Root Key — random, generated once at enrollment, NEVER stored in plaintext
    ARK  ←  csprng(32)
     • per enrolled passkey i:   wrap_i = AEAD_seal(key=KDF(S_prf,i), pt=ARK, aad=account_did)
                                  → stored as a PUBLIC ciphertext blob (safe: S_prf,i never leaves device i)
     • for recovery:             SSS_t-of-n(ARK)  →  guardian shares (L4-recovery)
    Adding a device  = wrap ARK under the new passkey's PRF.   No server key involved.

L2  Purpose-isolated keys — HKDF-Expand(ARK, label), labels are constants, never reused
    k_storage  = HKDF(ARK, "kotoba/storage/dek-wrap/v1")   # wraps data-encryption keys (L3)
    k_signal   = HKDF(ARK, "kotoba/signal/identity/v1")    # seeds the Signal IdentityKey (L5)
    k_session  = HKDF(ARK, "kotoba/session/sign/v1")       # seeds the CACAO session keypair (L4)

L3  Data keys — at rest in kotoba (SecureVault / manimani intake)
    DEK   ←  csprng(32)                         # per-graph (or per-record for要配慮 PII)
    blob  =  AEAD_seal(key=DEK, pt=plaintext, aad=blob_cid)          # ← CID-bound (closes gap 2)
    wrap  =  AEAD_seal(key=k_storage, pt=DEK,  aad=graph_cid)         # ← wrapped client-side (closes gap 1)
    datom:  only {blob_cid, wrap_ref, non-sensitive metadata} — never plaintext

L4  Authorization plane — CACAO (CAIP-74), server VERIFIES ONLY
    session keypair(from k_session)  OR  wallet(did:pkh / ERC-4337)  signs a CACAO
     → grants kotoba://op/{datom:read|datom:transact} scoped to kotoba://graph/{cid}, exp, single-use nonce
     → kotoba-server checks DelegationChain(depth≤2, capability+graph attenuation). Holds NO signing key.

L5  Messaging plane — user ↔ user, Signal (closes gap 3)
    Signal IdentityKey unlocked under passkey (KeyOpKind::SignalKeyUnlock, UV required)
    DID ↔ Signal binding = CACAO-signed assertion (com.etzhayyim.encrypted.signalIdentity), verified before X3DH
    X3DH session establish → Double Ratchet per-message keys → forward secrecy + post-compromise security
```

The elegance is that **multi-device and recovery fall out for free**: because
ARK is a random key wrapped *per passkey-PRF*, enrolling a device is "wrap ARK
under the new PRF", and losing all devices is "reassemble ARK from `t` guardian
shares". The server stores only opaque ciphertext `wrap_i` blobs and guardian
share envelopes — never a key that decrypts anything.

## D1 — WebAuthn PRF derives keys (closes gap 4)

`kotoba-auth` gains a derivation path alongside the existing gate:

- Registration requests the `prf` extension; the RP stores per-credential
  `salt_account` (random, public). The `PasskeyGate` continues to enforce
  UP/UV/TTL exactly as today — **the gate is the authorization check, the PRF
  is the key source; they compose, neither replaces the other.**
- `KeyOpKind::StorageKeyDecrypt` and `KeyOpKind::SignalKeyUnlock` now mean
  "passkey assertion + PRF output present" — the PRF result (`S_prf,i`) is fed
  into `kotoba-crypto::hkdf` to unwrap ARK, then derive L2 keys. The
  `Authorization` grant still bounds *when* the derived key may be used.
- `S_prf,i`, ARK, and all L2/L3 keys are **device-resident, in-memory only**.
  No env var (`KOTOBA_AGENT_ED25519_HEX` is retired from the member path),
  no Keychain plaintext, no D1.

## D2 — `SecureVault` binds ciphertext to its CID (closes gap 2)

`kotoba_crypto::aead::seal_with_aad(key, plaintext, aad)` is threaded through
`SecureVault::put` so that `aad = blob_cid` (or the BlobManifest root CID for
chunked blobs). Decryption recomputes/echoes the CID as AAD, so a swapped or
relocated blob fails AEAD verification rather than returning attacker-chosen
bytes. The existing no-AAD `seal` is kept only for legacy non-PII paths and
marked `#[deprecated]`. DEK-wrap uses `aad = graph_cid` symmetrically.

## D3 — CACAO is the only write capability; server holds no key (closes gap 1)

The `SS_REPO_SIGNING_KEK` path is removed. Member writes to kotoba are
authorized exclusively by a CACAO signed at L4 (session key or wallet). This is
already the kotoba-server hot path — `verify_skip_sig` + Ed25519 verify
benchmarks exist — so D3 is mostly *deletion*: drop the worker-side wrap/unwrap,
delete the secret after a 30-day zero-read quarantine (per ADR-2605231525 Stage
C-4), and route all session signing to the passkey-derived `k_session`.

## D4 — Signal for user↔user, bound to DID (closes gap 3)

`kotoba-signal`'s X3DH/Double Ratchet becomes the wrap transport for
`com.etzhayyim.encrypted.*` records exchanged between members:

- The Signal `IdentityKey` is derived from `k_signal` (L2), so it is recoverable
  on a new device via ARK, and unlockable only behind `SignalKeyUnlock` (UV).
- A new lexicon record `com.etzhayyim.encrypted.signalIdentity` carries the
  Signal identity public key signed as a CACAO by the member's DID key; peers
  **must** verify this binding (`Cacao::verify_with_resolver`) before X3DH.
  This is the DID↔Signal assertion ADR-2605181100 specified but never enforced.
- Per-record symmetric keys are wrapped under the established Signal session
  (ratcheted), not a static key — delivering forward secrecy and
  post-compromise security for messaging. Single-recipient at-rest data (D2)
  keeps the simpler `k_storage` wrap; **Signal is for between-people, the
  passkey hierarchy is for between-devices-of-one-person.** That separation is
  the second piece of the design's symmetry.

## D5 — what stays AES-256-GCM (spec reconciliation)

The code uses AES-256-GCM, not the XChaCha20-Poly1305 named in ADR-2605181100.
Both are 256-bit AEADs with a per-seal random nonce from `OsRng`; AES-GCM has
hardware acceleration on every target. We **ratify AES-256-GCM as the kotoba
AEAD** and amend ADR-2605181100's wording rather than rewrite working, tested
code. Nonce-misuse risk is bounded by the existing always-random-nonce
construction; we add `#[deny(unsafe_code)]` to `kotoba-crypto` and a test
asserting two seals of identical plaintext differ.

# Consequences

**Positive**

- The no-server-key invariant becomes *structural*, not aspirational: there is
  no server-side wrapping key to seize, because the only wrap key (`k_storage`)
  is derived from the passkey PRF on the member's device.
- One mental model covers at-rest secrecy, authz, and messaging. A reviewer
  traces any secret to the passkey at L0 and the random ARK at L1.
- manimani PII (Gmail/PC ingest, ADR-2605291100) inherits CID-bound at-rest
  encryption (D2) and client-side DEK wrapping (D3) with no new machinery.
- Multi-device and social recovery are first-class (ARK wrap-per-PRF + SSS),
  not bolted on.
- Builds almost entirely on shipped, tested crates (CACAO, PasskeyGate,
  AEAD/HKDF/HPKE, kotoba-signal); the new surface is small.

**Negative / costs**

- WebAuthn PRF requires platform support (CTAP2.1 `hmac-secret`; Chrome/Safari
  passkey PRF). A non-PRF fallback (password-derived ARK wrap via Argon2id) is
  needed for older authenticators — explicitly weaker, flagged in the UI.
- Losing all passkeys **and** guardian quorum = permanent data loss. This is the
  correct property for a no-server-key system, but it must be stated plainly at
  enrollment.
- Recovery (SSS guardians) introduces a social-trust surface that needs its own
  ceremony design (out of scope here; follow-up ADR).

**Landed (2026-06-01) — what is implemented and tested**

- **Phase 1 (D2/D5)** — `kotoba_crypto::aead::{seal_with_aad,open_with_aad}` +
  `SecureVault::{put_bound,get_bound,put_with_policy_bound}` (aad = caller's
  logical slot, e.g. graph/datom CID); `#![deny(unsafe_code)]` on `kotoba-crypto`;
  AAD-swap + nonce-uniqueness tests. (kotoba-crypto 79, kotoba-kse 137 green)
- **Phase 2 (D1)** — `kotoba_crypto::key_tree`: `passkey_wrap_key` (HKDF over PRF
  output) → `generate_ark` / `wrap_ark` / `unwrap_ark` (AAD = account DID) →
  `derive_storage_key` / `derive_signal_seed` / `derive_session_seed`; multi-device
  enrollment + real Shamir-over-GF(256) guardian recovery (`key_tree::recovery`).
  (tests: wrong-PRF/wrong-DID rejection, 2nd-device recovers same ARK, 3-of-5 SSS,
  below-threshold fails)
- **Phase 4 (D4)** — `kotoba_signal::binding`: `SignalBinding` (sign/verify the
  DID↔Signal assertion against the DID doc key), `matches_bundle` (substitution
  guard before X3DH), `wrap_record_key`/`unwrap_record_key` (per-record key over
  the established Double Ratchet session). Lexicons `signalIdentity` + `keyWrap`
  already existed. (kotoba-signal 109+5 green)

**Gated / not landed (correctly deferred)**

- **Phase 3 (D3)** — the kotoba-side replacement (`k_session`) is implemented;
  physical deletion of `SS_REPO_SIGNING_KEK` from the legacy `etzhayyim-project-auth`
  worker is **gated** behind ADR-2605231525 Stage C-2/C-3 + a 30-day zero-read
  quarantine (sign-up intentionally fails without the KEK today). Only a
  deprecation marker recording the cutover trigger was added; no behavior change.
- **Wiring (partial — 2026-06-01)** — the PII engine is now sourced from the
  hierarchy: `VaultKeyedCrypto::from_ark` (vault_key = `k_storage`) +
  `AgentCrypto::{encrypt,decrypt}_bound` / `encrypt_blob_bound` (default trait
  methods, work through `Arc<dyn AgentCrypto>` — the manimani/EmailIngestor path).
  A full L0→L5 end-to-end test (`kotoba-signal/tests/passkey_hierarchy_e2e.rs`)
  walks PRF→ARK→k_storage→bound-blob and ARK→Signal-binding→ratchet-keyWrap, plus
  guardian-recovery→resume-storage. The **EmailIngestor** (manimani/Gmail PII
  path) now seals the body blob with `encrypt_blob_bound(aad = owning email CID)`
  and `decrypt_body(email_cid, body_cid)` enforces the same binding, so a body
  blob cannot be swapped between emails (kotoba-ingest 89 green; +wrong-owner
  rejection test). The **`signalIdentity` publish/resolve loop** is now in
  kotoba-server (`com.etzhayyim.signal.{publish,resolve}.identity`): publish stores the
  DID-signed binding (and rejects an invalid did:key signature on publish);
  resolve verifies it by **resolving the issuer DID to its Ed25519 key** (via the
  existing `CompositeDidResolver`: `did:key` trustless + `did:web`/`did:plc`
  HTTP-fetched DID documents) and returns `verified`. So `did:key` is trustless
  (key derived from the DID itself), `did:web`/`did:plc` verify against the
  authoritative DID-document `verificationMethod` (the ERC725/apex-Worker mirror,
  ADR-2606013800 — this is what closes the residual MITM trust on key
  distribution), and a DID that does not resolve / has no Ed25519 method is
  **never falsely vouched** (`verified=false` + reason). kotoba-server signal_xrpc
  28 green (incl. did:web-verifies-against-resolved-doc + wrong-key-rejected +
  unresolvable-not-vouched). The **client WebAuthn-PRF ceremony (L0)** is landed in
  yoro: `$lib/auth/key-tree.ts` (WebCrypto PRF→ARK→k_storage/k_signal/k_session,
  **byte-for-byte interop with the Rust `key_tree`** — verified against Rust
  known-answer vectors) + `$lib/auth/prf.ts` (request PRF at register, eval at
  assertion, extract `S_prf`) + `signUp`/`signIn` request the PRF extension and
  capture `S_prf` (best-effort, falls back to server-assisted if the authenticator
  lacks PRF). yoro key-tree + prf vitest 13 green; svelte-check clean.
  All three remaining legs are now landed: **(1)** the wrapped-ARK store —
  kotoba-server `com.etzhayyim.account.{put,get}.wrapped.ark` persists the opaque
  per-passkey `wrapArk` blob (server holds no key to read it; owner-auth'd;
  account_xrpc 4 green); **(2)** the Ed25519 session key — yoro
  `$lib/auth/session-key.ts` derives a deterministic Ed25519 keypair from
  `k_session` (zero-dep pkcs8 import, verified sign/verify + W3C did:key vector,
  session-key vitest 6 green) and `registerSessionKey` posts the public half to
  the C-2 endpoint; **(3)** the DID-document key — the apex Worker
  `ed25519VerificationMethod()` + `toDidDoc()` now emit a member's registered
  Ed25519 key as `verificationMethod` + `authentication`/`assertionMethod`, so
  `resolve.identity` verifies a did:web binding against it (TypeScript clean).
  The L0→L5 chain is **code-complete and wired end-to-end on the client**:
  `$lib/auth/key-hierarchy.ts` orchestrates enroll/recover/add-device (correct
  multi-device semantics — a recover-miss never silently mints a divergent ARK),
  `$lib/auth/account.ts` is the fetch transport to `account.{put,get}.wrapped.ark`,
  and `signIn` now (guarded, best-effort) recovers-or-enrolls the hierarchy from
  the captured `S_prf` and registers the derived Ed25519 session key (C-2). yoro
  auth vitest **24 green** (key-tree 6 + prf 7 + session-key 6 + key-hierarchy 5,
  incl. enroll→recover→same-keys, add-device re-wraps same ARK, wrong-PRF fails,
  real Ed25519 sign/verify); svelte-check clean. The did:web verification chain is
  now **closed end-to-end**: the publisher `--signing-key` flag (+ apex
  `withVerificationMethod`) writes the registered key into the actor record so
  did.json emits it as `verificationMethod` + `authentication`/`assertionMethod`
  (verified by emit) → `resolve.identity` verifies a did:web binding against it.
  **Add-device** is wired (`addDevicePasskey` + PRF eval-at-register) for the
  same-device additional-authenticator case (re-wraps the SAME ARK). **Cross-device
  ARK transfer** is also landed (`device-transfer.ts`): HPKE-style ephemeral
  X25519 ECDH → HKDF → AES-256-GCM (AAD = account DID) seals the ARK from an
  unlocked device to a new device's transfer key; `acceptTransferredArk` unseals +
  re-wraps under the new device's own PRF, so the ARK never hits the channel/server
  in plaintext (tests: round-trip, wrong-key/AAD/tamper rejection, new device
  independently recovers afterwards). yoro auth vitest **31 green**; svelte-check
  clean. **Only remaining**: the server-side verification + cutover for C-3
  session-token signing — a live-auth-Worker change (the client `signSessionPoP`
  primitive is landed + tested; ADR-2606014500), correctly gated.
- **Deferred** — non-PRF Argon2id fallback for legacy authenticators; the guardian
  recovery ceremony + guardian-collusion threat model (separate recovery ADR).

# Alternatives Considered

- **Keep the server KEK, rotate weekly.** Rejected: still a single seizable key;
  contradicts ADR-2605231525; rotation hides but does not remove the liability.
- **Passkey-as-auth-only + device-generated keys synced via server.** Rejected:
  requires the server to relay (and thus potentially hold) wrap material; PRF
  derivation removes the server from the key path entirely.
- **Use Signal for at-rest single-recipient data too.** Rejected as
  over-engineering: a Double Ratchet between a user and *their own storage* has
  no second party to ratchet against; `k_storage` wrap is simpler and correct.
  Signal is reserved for genuine user↔user (D4).
- **Rewrite to XChaCha20-Poly1305 to match the old spec text.** Rejected:
  AES-256-GCM is equivalent strength, hardware-accelerated, already tested; we
  amend the spec instead (D5).
- **Derive ARK directly from PRF (no random ARK).** Rejected: PRF output differs
  per credential, so a directly-derived root cannot be shared across devices or
  recovered via guardians. The random-ARK-wrapped-per-PRF indirection is what
  makes multi-device and recovery clean.

# References

- ADR-2605181100 (MST encrypted records + Signal key-wrap) — amended by D4/D5
- ADR-2605231525 (No-Server-Key Religious-Corp Architecture) — D3 realizes Stage C-4
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605312345 (kotoba Datom first-class canonical state)
- ADR-2605291100 (manimani kotoba-native — Gmail/PC ingest) — primary consumer of D2/D3
- ADR-2605240001 (kotoba clean-room architecture)
- `40-engine/kotoba/crates/kotoba-auth/src/{cacao,delegation,passkey,resolver}.rs`
- `40-engine/kotoba/crates/kotoba-crypto/src/{aead,hkdf,hpke,key_wrap,agent_crypto}.rs`
- `40-engine/kotoba/crates/kotoba-kse/src/{secure_vault,sovereign_key}.rs`
- `40-engine/kotoba/crates/kotoba-signal/src/{x3dh,ratchet,session,identity}.rs`
- CAIP-74 (CACAO), WebAuthn Level 3 PRF extension / CTAP2.1 `hmac-secret`
