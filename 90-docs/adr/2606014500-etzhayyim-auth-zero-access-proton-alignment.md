---
id: adr-2606014500-etzhayyim-auth-zero-access-proton-alignment
title: "ADR-2606014500: etzhayyim-project-auth → zero-access (Proton-aligned) custody"
status: proposed
doc_type: adr
topic: auth-zero-access-proton-alignment
authoritative: true
last_verified: 2026-06-01
priority: 9.0
axis: architecture
weight: 0.9
priority_note: "Moves the live auth Worker off server-held signing-key custody (T1 KEK) toward client-self-custody (Proton-style zero-access), realizing the worker's own Stage C-2/C-3/C-4 plan and ADR-2606014000 D3."
authoritative_for:
  - auth-worker-key-custody-posture
depends_on:
  - adr-2606014000-kotoba-passkey-cacao-signal-secrecy
  - adr-2605231525-no-server-key-religious-corp-architecture
related:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0010-kek-envelope-encryption
supersedes: []
superseded_by: []
---

# ADR-2606014500: etzhayyim-project-auth → zero-access (Proton-aligned) custody

**Status**: proposed
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

`etzhayyim-project-auth` (the live auth Worker, `60-apps/etzhayyim-project-auth/`)
today uses **T1 server-assisted custody**: it generates each identity's ES256
signing keypair server-side and stores the private key in D1 wrapped under a
single server-held KEK (`SS_REPO_SIGNING_KEK`, ADR-0010 envelope encryption).
A compromise of that one secret exposes every signing key — the worker can
impersonate any member or agent. This is **not** a zero-access design: the
server can read what it stores.

A "Proton-style" posture (zero-access / end-to-end) means the server holds
**neither plaintext nor any key that decrypts it** — it stores only ciphertext
and public material, and *verifies* rather than *signs*. ADR-2606014000
established exactly this for the kotoba substrate (passkey-PRF → ARK → purpose
keys, server holds only opaque wrapped blobs). The auth Worker's own
`STAGE-C-IDENTITY-SIGNING-DEVOLUTION.md` already specifies the same target as
three stages:

- **C-2** — client generates the keypair locally (WebCrypto / passkey-derived),
  POSTs only the public half + an attestation; the worker stores public-key-only.
- **C-3** — human session tokens become passkey-derived ES256 PoP (DPoP-style);
  the worker verifies, never signs with a shared secret.
- **C-4** — `SS_REPO_SIGNING_KEK` is deleted after a 30-day zero-read quarantine.

This ADR commits the auth Worker to that target and lands the **C-2 server
side** as an additive, non-breaking capability, so new identities can be
client-self-custodied while the legacy KEK path keeps running until C-4.

# Decision

**Shift `etzhayyim-project-auth` to client-self-custody (zero-access) as the
forward default, KEK custody as legacy fallback until C-4.**

## D1 — public-key-only registration (Stage C-2, landed)

New XRPC `POST /xrpc/com.etzhayyim.auth.registerSigningKey`
(`handleRegisterSigningKey`): a session-authenticated caller registers a
**client-generated** signing key by its public half only. The worker:

- validates the multibase public key and **enforces ownership** (a caller may
  register a key only for their own account DID or a sub-actor DID beneath it);
- stores a row in `vertex_etzhayyim_key_signing` with the private columns **empty**
  and `key_custody_tier = 'human_self_custody'` — **no KEK call, no envelope**;
- thereafter only *verifies* signatures from that key.

The private key is generated and held on the member's device — ideally derived
from the ADR-2606014000 hierarchy (WebAuthn PRF → ARK → `k_session`) — and
**never transmitted to the server**.

Schema: `vertex_etzhayyim_key_signing` gains `key_custody_tier TEXT NOT NULL DEFAULT
'server_assisted'` (additive; the table is `DROP`+`CREATE` on cold start and
every existing INSERT keeps the default, so this is non-breaking).

Posture flag: `SS_KEY_CUSTODY_MODE` (`"server_kek"` default | `"client_self_custody"`)
selects which path new sign-ups take; unset preserves today's behavior exactly.

## D2 — session PoP (Stage C-3)

`com.atproto.server.createSession` moves from an HS256 JWT signed by a
server-held secret to an Ed25519 PoP token the worker verifies against the public
projection. **Client primitive landed** (ADR-2606014000): yoro
`session-key.ts::signSessionPoP` produces a compact EdDSA JWS signed by the
ARK-derived session key (vitest: sign → verify against the registered public key).
**Server-side verification landed (additive)**: `worker/src-ts/session-pop.ts`
(`verifySessionPoP`) base58-decodes the registered Ed25519 multibase from the
public projection and verifies the JWS — read-only, mints nothing, holds no key;
exposed at `POST /xrpc/com.etzhayyim.auth.verifySessionPoP`. Client↔worker interop
cross-verified in Node (token signed client-side verifies server-side; multibase
round-trips; tampered rejected). HS256 issuance is **untouched**.
**Login path landed (additive)**: `POST /xrpc/com.etzhayyim.auth.createSessionFromPoP`
establishes a session from a client PoP — the login proof is the member's own
signature, no passkey round-trip and no server signing-key custody (issues the
standard HS256 session for downstream compat).
**Remaining (gated)**: dropping HS256 in favour of downstream PoP verification.

## D3 — KEK removal (Stage C-4): instrumented, deletion staged

`logKekRead(site)` now fires at all three `SS_REPO_SIGNING_KEK` read sites — the
30-day **zero-read quarantine instrument** ADR-2605231525 C-4 requires. The
execution runbook (migrate server-assisted paths → 30-day `[kek-read]`-zero window
→ drop empty private columns + envelope code → `wrangler secret delete`) is in
`STAGE-C-IDENTITY-SIGNING-DEVOLUTION.md`. The irreversible deletion itself is an
OPERATOR action on live telemetry — **not performed in code**; the KEK stays
fail-closed until the window passes.

## D4 — amend the worker's Prohibited Patterns

The CLAUDE.md invariant *"SS_REPO_SIGNING_KEK なしでの sign-up 禁止"* is **amended**:
sign-up without the KEK is now permitted **iff** it uses client-self-custody
(public-key-only registration). The KEK remains required only for the legacy
`server_assisted` path. The rule *"Signal Identity Key を DID Signing Key から
独立生成禁止"* is unchanged (still satisfied — the binding is DID-signed per
ADR-2606014000 D4).

# Consequences

**Positive**
- A KEK compromise no longer exposes self-custodied keys — there is nothing to
  decrypt. The worker becomes a public-key register + verifier for new identities.
- Realizes the worker's own Stage-C plan and ADR-2606014000 D3 without a flag day.
- Additive: legacy KEK path untouched; default behavior unchanged until opt-in.

**Negative / honest scope**
- **Landed = C-2 server side only** (registration endpoint, schema column, flag,
  ownership check). C-3 (session PoP) and C-4 (KEK deletion) are not done.
- The **client counterpart in yoro** now exists (ADR-2606014000): `$lib/auth/
  session-key.ts` derives a deterministic Ed25519 keypair from `k_session` and
  `registerSessionKey()` posts the public half to this endpoint (session-key
  vitest 6 green, incl. real sign/verify + W3C did:key vector). Still to wire into
  the default sign-in UX: calling `registerSessionKey` automatically after the
  PRF-derived ARK is available, and switching session-token signing to this key
  (C-3). The apex Worker already publishes a registered key as a did:web
  `verificationMethod` (ADR-2606014000 (3)).
- The auth Worker has **no local test/build harness** (zero-npm-dep Cloudflare
  Worker, no tsconfig/tsc here); these changes were written to match existing
  patterns and the confirmed signatures of `requireSessionAccount` / `parseJson`
  / `json` / `jsonErr` / `ensureKeysTables`, but must be typechecked and deployed
  through the project's `wrangler` pipeline before reliance.
- Same residual trust as Proton on **identity key distribution**: the DID
  document that vouches for a public key must be anchored (ERC725 / on-chain
  mirror per ADR-0074) to fully resist substitution; did:web+TLS alone degrades
  to trusting the DID operator.

# Alternatives Considered

- **Rip out the KEK now.** Rejected: breaks live sign-up (intentionally fails
  without the KEK today) and violates the staged-removal discipline; C-4 is gated.
- **Keep T1, rotate KEK.** Rejected: still a single seizable key; not zero-access.
- **Server-side passkey-PRF unwrap-then-sign.** Rejected: the server would touch
  the plaintext private key transiently — not zero-access. Signing must be client-side.

# References

- ADR-2606014000 (kotoba passkey-rooted secrecy) — the hierarchy the client key derives from
- ADR-2605231525 (No-Server-Key Religious-Corp Architecture) — Stage C-4
- `60-apps/etzhayyim-project-auth/STAGE-C-IDENTITY-SIGNING-DEVOLUTION.md` — C-2/C-3/C-4
- `60-apps/etzhayyim-project-auth/worker/src-ts/index.ts` — `handleRegisterSigningKey`, `SS_KEY_CUSTODY_MODE`
- ADR-0074 (Ethereum Identity Bridge) — ERC725 root + on-chain key anchoring
