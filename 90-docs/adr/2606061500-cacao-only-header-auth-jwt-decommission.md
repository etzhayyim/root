---
id: adr-2606061500-cacao-only-header-auth-jwt-decommission
title: "ADR-2606061500: CACAO-only header login — decommission the authn subdomain + server-minted JWT session site-wide"
status: accepted
doc_type: adr
topic: cacao-only-auth
authoritative: true
last_verified: 2026-06-06
priority: 8.6
axis: architecture
weight: 0.92
priority_note: "Extends the /profile same-origin gate (ADR-2606060000) to the WHOLE app: the global header login no longer redirects to authn.etzhayyim.com nor depends on a server-minted accessJwt. The session itself becomes a member-held CACAO ceremony, closing the last no-server-key gap in the interactive auth path."
authoritative_for:
  - cacao-only-header-auth
  - jwt-session-decommission
depends_on:
  - adr-2606060000-profile-same-origin-auth-cacao
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2606014000-kotoba-passkey-cacao-signal-secrecy
  - adr-2606013800-actor-profile-dynamic-did-json
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2606014500-etzhayyim-auth-zero-access-proton-alignment
  - adr-2605212030-etzhayyim-authz-erc725-root-issuance-design
supersedes: []
superseded_by: []
---

# ADR-2606061500: CACAO-only header login — decommission the authn subdomain + server-minted JWT session

**Status**: accepted
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

ADR-2606060000 made `etzhayyim.com/profile` authenticate same-origin via a
member-signed **CACAO** verified by the apex Worker
(`com.etzhayyim.authz.verifyCacao`) — no `authn.etzhayyim.com` hop, no server
key. But that gate was scoped to the **profile edit-mode only**. The **global
header login** (the "ログイン / 新規登録" buttons in `+layout.svelte`, plus
`welcome`, `profile`, `sign-in/+server.ts`, `settings/developer`) still:

1. **full-page redirected** the browser to `https://authn.etzhayyim.com/sign-in`,
   and
2. even the in-app `passkey.ts signIn()` talked to `AUTH_RPC_BASE =
   https://authn.etzhayyim.com` for the WebAuthn challenge **and to mint an
   `accessJwt` / `refreshJwt` session** that the entire XRPC write surface
   (`createRecord` → post/like/follow/DM) carries as `Authorization: Bearer`.

So the interactive auth path still depended on (a) a subdomain that
ADR-2606060000 declared *unnecessary*, and (b) a **server-minted signing token** —
exactly the shape ADR-2605231525 (no-server-key) prohibits for
etzhayyim-operated infrastructure. The `verifyCacao` gate, by contrast, holds no
key and mints no session; it only proves DID control.

**Decision question** (operator-directed, 2026-06-06): *move the header login
onto the same-origin CACAO mechanism too — make CACAO the sole interactive auth,
and decommission the server-minted JWT session.*

# Decision

The interactive session becomes a **member-held CACAO ceremony**, not a
server-minted bearer token. There is **one** auth artifact site-wide — the same
member-signed CACAO ADR-2606060000 already defined — and it is produced on
`etzhayyim.com` itself.

## 1. Session model (client) — `cacao-session.ts`

A signed-in session is `{ accountDid, sessionKey, verifiedCacao, scope, exp }`
held **in memory** (the private session key never persists; it is
deterministically re-derivable from the passkey PRF → ARK per ADR-2606014000):

- **Login** = same-origin passkey assertion → PRF secret → ARK
  (recover from the kotoba zero-access wrap store, already off-authn at
  `kotoba.etzhayyim.com`; first-device enroll) → `k_session` → Ed25519 session
  key → build + `EdDSA`-sign a CACAO bound to the apex
  (`aud=did:web:etzhayyim.com`, `domain=etzhayyim.com`,
  `kotoba://op/datom:transact`) → POST same-origin
  `/xrpc/com.etzhayyim.authz.verifyCacao`. The apex verifies the Ed25519
  signature **locally** (trustless, no key) and returns `valid:true` + the
  resolved DID + scope.
- **The WebAuthn challenge is client-generated.** The assertion's only job here
  is to unlock the passkey PRF (to derive the session key); it is **not** the
  authentication proof presented to a server, so it needs no server-issued
  challenge — removing the `passkeyBeginAuth` authn dependency.
- **`isSignedIn` / DID / user stores** are set from the verified CACAO, not from
  an `accessJwt`. `signOut` drops the in-memory key + verified CACAO.

## 2. Write authorization — CACAO capability, not Bearer JWT

The XRPC write seam is the single function `getBearerToken` in
`atproto-agent.ts`. It is replaced by a **CACAO capability provider**: each
mutating XRPC call (`com.atproto.repo.createRecord` et al.) carries a freshly
session-key-signed CACAO (single-use `nonce`, short `exp`) routed **same-origin**
so `kotoba-sw.js` / the kotoba node verify it (`DelegationChain::verify` resolves
the account↔session-key delegation; `NonceStore` enforces replay protection).
Reads are unaffected.

## 3. authn subdomain + JWT decommission

`authn.etzhayyim.com` is removed from every interactive client path
(`+layout.svelte`, `welcome`, `profile`, `sign-in/+server.ts`,
`settings/developer`). The server-minted `accessJwt`/`refreshJwt` session is
**decommissioned** as the primary credential.

## 4. Honest staging (what is live vs gated)

Faithful to the repo's R0 ethos and the existing `verifyCacao` `gated:true`
honesty for SIWE:

- **LIVE now (fully same-origin, `valid:true` on the apex with no key):**
  returning members (account DID already known on the device) signing in via
  **passkey → EdDSA CACAO**. The apex verifies Ed25519 locally end-to-end.
- **GATED on the kotoba node (honest, no false session):**
  - **First-device / sign-UP account-DID bootstrap** — minting/resolving the
    account `did:web` from the session key without a server needs the kotoba
    delegation-registration + account-DID resolver surface
    (`com.etzhayyim.auth.registerSigningKey` same-origin, ADR-2606014000
    follow-up). Until live, sign-up returns `gated` and points at the kotoba
    bootstrap — it does **not** fall back to authn.
  - **Wallet / SIWE** — secp256k1 / ERC-1271 recovery already runs on the kotoba
    node (`gated:true`, unchanged from ADR-2606060000).
  - **CACAO write verification end-to-end** — the kotoba write node must accept
    the per-write CACAO. Until the node endpoint is enabled, the legacy Bearer
    path is retained behind a **single explicit flag** (`PUBLIC_AUTH_LEGACY_JWT`,
    default off) as a rollback fallback, marked at one removal point. The flag is
    a rollback affordance, **not** an invariant override: when off, no server key
    and no server-minted session exist in the interactive path.

# Consequences

- **+** Closes the last no-server-key gap in the interactive auth path
  (ADR-2605231525): the global session is a member signing ceremony, the apex
  holds no key and mints no token, and `authn.etzhayyim.com` leaves every
  client path.
- **+** One auth artifact site-wide (the CACAO of ADR-2606060000); `/profile`
  edit-mode and global login are now the same mechanism.
- **−** First-device/sign-up and wallet/SIWE remain kotoba-node-gated until the
  delegation-registration + write-verification endpoints are live; reported
  honestly (no false session, no silent authn fallback).
- **−** WebAuthn credentials must be usable under the `etzhayyim.com` rpId. Keys
  registered under an `authn.etzhayyim.com` rpId are re-enrolled on first
  same-origin sign-in (additive; tracked as a migration follow-up).

# Invariants (unchanged / strengthened)

- **No-server-key (ADR-2605231525)** — strengthened: removes the last
  server-minted session token from the interactive path.
- **kotoba canonical Datom state (ADR-2605262130 / 2605312345)** — writes are
  CACAO-authorized `datom:transact`, not opaque JWT-bearer mutations.
- **Same-origin, no auth subdomain (ADR-2606060000)** — extended from `/profile`
  to the whole app.
