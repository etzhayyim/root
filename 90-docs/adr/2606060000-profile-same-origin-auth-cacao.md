---
id: adr-2606060000-profile-same-origin-auth-cacao
title: "ADR-2606060000: /profile Same-Origin Auth — WebAuthn / passkey / SIWE → CACAO, no auth subdomain, no server key"
status: accepted
doc_type: adr
topic: profile-same-origin-auth
authoritative: true
last_verified: 2026-06-06
priority: 8.5
axis: architecture
weight: 0.9
priority_note: "Lets etzhayyim.com/profile authenticate via passkey AND wallet/SIWE on one origin with zero server key — the no-server-key invariant makes the auth subdomain unnecessary, not merely optional."
authoritative_for:
  - profile-same-origin-auth
  - cacao-verify-only-apex-surface
depends_on:
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2606014000-kotoba-passkey-cacao-signal-secrecy
  - adr-2606013800-actor-profile-dynamic-did-json
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605212030-etzhayyim-authz-erc725-root-issuance-design
  - adr-2606014500-etzhayyim-auth-zero-access-proton-alignment
supersedes: []
superseded_by: []
---

# ADR-2606060000: /profile Same-Origin Auth — WebAuthn / passkey / SIWE → CACAO

**Status**: accepted
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

The question: *can `https://etzhayyim.com/profile` authenticate a member via
WebAuthn, passkey, and SIWE (Sign-In-With-Ethereum) **on that same origin**,
without moving auth to `auth.etzhayyim.com`, and kotoba-native?*

A dedicated auth subdomain exists to centralise a **server-held signing key** and
a **session cookie/JWT** behind one origin. etzhayyim has structurally discarded
that premise:

- **No-server-key (ADR-2605231525)** — etzhayyim infrastructure holds zero
  signing capability. Auth is therefore not a server secret but a **client
  signing ceremony + a stateless verify**. With nothing to centralise, the auth
  subdomain is not merely optional — it is *unnecessary*, and same-origin is more
  faithful to the invariant.
- **kotoba already ships the whole stack (ADR-2606014000)** — `kotoba-auth`
  verifies CACAO (CAIP-74) for EdDSA (`did:key`/`did:web`/`did:plc`), EIP-191
  EOA, and ERC-1271 smart accounts (`verify_signature_eip191_smart`); the yoro
  client already lands the passkey-PRF → ARK → `k_session` → Ed25519 session-key
  ceremony.
- **The apex Worker already passes CACAO through unchanged** to the kotoba node
  (`XRPC_KOTOBA_UPSTREAM`, "no server key injected"), and serves `/profile` via
  the same-origin yoro reverse proxy.

The three sign-in methods are not three auth systems. They converge on **one
artifact — a member-signed CACAO**: a passkey signs an `EdDSA` CACAO with the
session `did:key`; a wallet signs an `eip191` CACAO via SIWE/EIP-4361 with a
`did:pkh:eip155` (EOA) or ERC-4337 smart account. So the apex needs exactly one
verifier with three entry points, not an auth subdomain.

# Decision

Add a **same-origin, verify-only CACAO auth gate** on the apex Worker and the
client adapters that feed it. No auth subdomain, no server-held key, no minted
session.

## D1 — apex verify-only surface (`com.etzhayyim.authz.verifyCacao`)

A local short-circuit in `50-infra/etzhayyim-did-web/src/worker.ts` (served
locally, never proxied) accepts `POST /xrpc/com.etzhayyim.authz.verifyCacao`
with `{ cacao }` and returns `{ valid, did, sigType, method, scope, gated,
reason }`.

- **`src/cacao.ts`** — dependency-free CACAO verifier whose wire shape is
  byte-identical to `kotoba-auth/src/cacao.rs` (`Cacao { h, p, s }`) and whose
  `siweMessage()` reconstruction is byte-identical to the Rust `siwe_message()`.
  - **`EdDSA`** (passkey/`did:key`) is verified **locally** via WebCrypto
    Ed25519 (native in the Workers runtime + Node ≥ 20) — zero dependencies, the
    primary path. did:key is decoded from base58btc multibase (`0xed01` + 32
    bytes).
  - **`eip191`** (wallet/SIWE) is **structurally** validated (issuer is
    `did:pkh:eip155:N:0x<addr>`, signature decodes, audience/domain bound to the
    apex, not expired); secp256k1 recovery / ERC-1271 is the audited Rust SSoT
    (`verify_signature_eip191_smart`), so the apex relays the CACAO to the kotoba
    node. The apex bundles **no secp256k1** (it hand-rolls only keccak256 today),
    so the `eip191` leg reports `gated: true` at R0 until the kotoba endpoint is
    enabled — reported honestly, never a false session.
  - Temporal/structural checks (well-formed, strict-UTC expiry with fail-safe
    "malformed ⇒ expired") run for both types, mirroring the Rust verifier.
- **`src/session.ts`** — the handler: binds `aud`+`domain` to the apex origin
  (anti-cross-site replay), requires at least one `kotoba://op/` capability
  resource, and returns the granted scope.

This is **not** the write-authorization point. The actual profile mutation is a
CACAO-authorized `datom:transact` to the kotoba node, whose `DelegationChain`
verify + single-use `NonceStore` (DashMap-sharded, CAIP-74 replay guard) are the
real enforcement. The apex gate only confirms DID control + capability shape so
`/profile` can flip into edit-mode.

## D2 — client adapters (yoro `$lib/auth/`)

- **`cacao.ts`** — builds an apex-bound profile CACAO (`aud =
  did:web:etzhayyim.com`, `domain = etzhayyim.com`, resources `kotoba://op/
  datom:transact` + `kotoba://graph/<cid>`), reconstructs the SIWE plaintext
  byte-identically to the apex/Rust, and signs it two ways: `signCacaoEd25519`
  (passkey session key, building on the landed `session-key.ts`) and
  `signCacaoSiwe` (wallet `personal_sign`, building on `ethereum.ts`).
- **`profile-signin.ts`** — `signInWithPasskey` / `signInWithWallet` orchestrate
  build → sign → `POST` to the **same-origin** `/xrpc/com.etzhayyim.authz.
  verifyCacao`. Clock/nonce/fetch are injected (no `Date.now()` in the library)
  for deterministic tests.
- **`ProfileEditGate.svelte`** — the UI mount on `/profile/[handle]`: two
  buttons (Passkey, Wallet/SIWE) → `onVerified(result)` flips the page into
  edit-mode.

## D3 — kotoba-native state

The profile record is the `:actor/*` SSoT in the public `actors-v1` graph
(ADR-2606013800). Verified edits are CACAO-authorized `datom:transact` writes to
the kotoba Datom log (ADR-2605312345); reads return through the existing
`resolveActorRecord` 3-tier (KV → kotoba → compiled). The CACAO capability is
scoped to `kotoba://graph/<actors-v1-cid>`.

## D4 — empirical verification

- apex: `scripts/cacao.test.mjs` — 16 tests, real WebCrypto Ed25519 (sign →
  verify → tamper-reject → expiry-reject → cross-key impersonation reject →
  audience/domain binding → scope → eip191-gated). Full worker suite **46/46
  green**; `tsc --noEmit` clean.
- client: `cacao.test.ts` + `profile-signin.test.ts` (vitest) — build/sign/
  layout/refusal/orchestration.
- **interop (proven)**: a CACAO built **and signed by the yoro client** verifies
  under the **apex** verifier — byte-identical SIWE plaintext, `valid: true`,
  resolved `did:key`, scope echoed; tamper rejected; the apex `handleVerifyCacao`
  returns `200` for the client token end-to-end.

# Consequences

**Positive**

- One origin, three methods, zero server key. The auth subdomain is removed from
  the critical path for `/profile` sign-in; nothing secret is centralised.
- The primary passkey path works end-to-end **today** with no new dependencies
  (WebCrypto Ed25519) and no kotoba endpoint requirement.
- The SIWE path is fully built client-side; only the server-side secp256k1/
  ERC-1271 recovery is delegated to the audited Rust SSoT — no hand-rolled
  curve crypto on the edge.
- Same token verifies on the apex AND the kotoba node (byte-identical wire +
  SIWE reconstruction), so there is no second auth dialect to maintain.

**Negative / honest R0 limits**

- `eip191`/SIWE returns `gated: true` on the apex until `XRPC_KOTOBA_UPSTREAM`
  (operator-gated) is enabled — the wallet path proves a signature but the apex
  cannot itself recover the address yet. Reported honestly.
- Live member-authored profile *writes* to kotoba remain operator-gated
  (`KOTOBA_ENDPOINT` has no public write surface at R0) and depend on
  ADR-2605231525 Stage C-3 cutover (Council ratify pending).
- Single-use nonce replay protection lives at the kotoba write layer, not the
  apex verify (which is a stateless UI gate by design). A non-PRF Argon2id
  passkey fallback (ADR-2606014000) is still deferred.

**Invariant alignment** — strengthens no-server-key (ADR-2605231525: the gate
holds no key and mints nothing), kotoba-canonical-state (ADR-2605312345),
1 SBT = 1 vote is untouched, and the actor-mirror invariant (ADR-2606013800:
human-member profiles are never hijacked — the gate only proves DID control).
**Zero invariant amendments.**

# Alternatives Considered

1. **Move auth to `auth.etzhayyim.com` (status quo direction).** Rejected: that
   topology exists to centralise a server key + session; with no-server-key there
   is nothing to centralise, and the extra origin only adds a CORS/redirect hop.
2. **Mint a server-side session JWT after verify.** Rejected: reintroduces a
   server-held signing key (ADR-2605231525 violation). The "session" is the
   member's signed CACAO capability, held client-side.
3. **Bundle `@noble` into the apex Worker for local secp256k1.** Rejected for R0:
   the apex is deliberately dependency-light (it hand-rolls keccak256); the
   audited recovery already exists in `kotoba-auth`, so delegate rather than
   re-implement curve crypto on the edge. (Revisitable if a public local SIWE
   verify becomes necessary before the kotoba endpoint is enabled.)
4. **Three separate sign-in code paths (passkey / passkey-PRF / SIWE).**
   Rejected: they converge on one CACAO artifact; one verifier with three entry
   points is less surface and guarantees the same token works on apex + kotoba.

# References

- ADR-2605231525 (No-Server-Key Religious-Corp Architecture)
- ADR-2606014000 (kotoba Passkey-Rooted Secrecy — WebAuthn PRF → ARK → CACAO + Signal)
- ADR-2606013800 (Actor profile + dynamic did.json — `actors-v1` SSoT)
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605312345 (kotoba Datom first-class canonical state)
- ADR-2605212030 (etzhayyim authz ERC725 root issuance) — the on-chain identity
  root, a separate layer from this session-capability gate
- `50-infra/etzhayyim-did-web/src/{cacao,session}.ts` + `scripts/cacao.test.mjs`
- `60-apps/etzhayyim-project-yoro/.../svelte/src/lib/auth/{cacao,profile-signin}.ts`
  + `ProfileEditGate.svelte` + `*.test.ts`
- `00-contracts/lexicons/com/etzhayyim/authz/verifyCacao.json`
- `40-engine/kotoba/crates/kotoba-auth/src/cacao.rs` (CACAO SSoT verifier)
- CAIP-74 (CACAO), EIP-4361 (SIWE), WebAuthn Level 3 PRF / WebCrypto Ed25519
