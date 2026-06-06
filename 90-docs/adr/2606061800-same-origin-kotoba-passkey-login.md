---
id: adr-2606061800-same-origin-kotoba-passkey-login
title: "ADR-2606061800: Same-Origin Kotoba Passkey Login/Signup — remove authn/mcp from the auth path"
status: accepted
doc_type: adr
topic: same-origin-kotoba-passkey-login
authoritative: true
last_verified: 2026-06-06
priority: 6.0
axis: architecture
weight: 0.70
priority_note: "Primary member login/signup; fixes a live outage (authn→mcp down)."
authoritative_for:
  - member login/signup auth path (etzhayyim.com)
  - passkey → did:key controller identity derivation
depends_on: []
related: []
supersedes: []
superseded_by: []
---

# ADR-2606061800: Same-Origin Kotoba Passkey Login/Signup

**Status**: accepted
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

## Context

Login/signup at `https://etzhayyim.com/` were broken. The header ログイン/新規登録
buttons hard-redirected to `authn.etzhayyim.com/sign-{in,up}`, and the in-app
passkey RPCs (`com.etzhayyim.auth.passkey*`) routed through `authn.etzhayyim.com`
→ MCP router → **`mcp.etzhayyim.com`**, whose origin was **down (502/522)** — so
neither the hosted page nor the in-app flow could complete. Operator directive:
rework auth so it does **not** use `mcp.etzhayyim.com`, kotoba-based, same-origin.

This extends the `/profile` same-origin CACAO gate (ADR-2606060000) — which was
built but only wired into profile-edit re-auth — into the **primary login/signup
path**, and removes `authn`/`mcp` from it entirely. No server-held key is
introduced (ADR-2605231525).

## Decision

**DID model (2-layer):**
- **controller / crypto root = passkey-derived `did:key`** (self-certifying;
  verified LOCALLY on the apex Worker via WebCrypto — no registry, no key).
  - PRIMARY: WebAuthn PRF secret → HKDF → ARK → Ed25519 session key → `did:key`
    (**deterministic**: same passkey ⇒ same DID on any device, no server-side ARK
    store). Salt is RP-bound constant (`accountPrfSalt('etzhayyim.com')`).
  - FALLBACK (no PRF): the credential's own P-256 public key → `did:key`
    (`p256-pub` multicodec `0x1200`), for authenticators without the PRF
    extension (Windows Hello pre-25H2, Windows 10, iOS < 18.4, legacy keys).
- **public handle = `did:web:etzhayyim.com:<handle>`** published to the kotoba
  Datom log, **best-effort** (login NEVER depends on it being reachable).

**Cross-device (same Apple ID / Google account):** because the `did:key` is
deterministically derived from the passkey's PRF output and the PRF output of an
**iCloud-Keychain- / Google-Password-Manager-synced** passkey is stable across
synced devices (PRF-capable: iOS 18.4+ / macOS 15+ / Android GPM), signing in on
another device of the **same** account reproduces the **same `did:key` → same
account**, with zero server-side state. Cross-vendor (Apple↔Android) passkeys do
not sync and are distinct accounts. Non-PRF devices fall back to P-256, which
cannot reproduce the PRF `did:key` offline (single-device until a kotoba lookup
lands).

**Frontend (yoro svelte):** new `$lib/auth/same-origin-auth.ts` runs the WebAuthn
ceremonies + `did:key` derivation + an EdDSA session PoP + a best-effort apex
control-confirm (`verifyCacao`) + account publish (`registerAccount`). The
session is established **client-side** the instant the key is derived, so
login/signup work with zero backend dependency. `passkey.ts` `signIn`/`signUp`
delegate here; the authn ceremony + server-minted JWT are removed from the
login/signup path. The header (`+layout`), `/profile`, `YoroAuthGate`, and
`/sign-in` drive the in-app flow instead of redirecting to `authn.etzhayyim.com`
(the legacy URL is kept only as a last-resort fallback for devices with no
WebAuthn at all).

**Worker (50-infra/etzhayyim-did-web):** `verifyCacao` promoted to the primary
login control-proof (verify-only, no server key); new
`com.etzhayyim.authz.registerAccount` — a verify-only CACAO relay that publishes
the handle↔`did:key` alias + profile to kotoba; honest `gated` (202) when
`KOTOBA_WRITE_ENDPOINT` is unset. CORS + OPTIONS added to both surfaces so
`yoro.etzhayyim.com` / native can reach the apex.

**kotoba account-publish (c):** root-caused + fixed + proven. `kg.ingest` already
accepts member-CACAO writes; a fresh self-issued root member `did:key` is
accepted. The one blocker was `kotoba-auth::verify_with_resolver` resolving every
EdDSA issuer via the DID resolver — a fresh member `did:key` (no published DID
doc) hangs on an IPNS/IPFS fetch. A `did:key` is self-certifying and must verify
against its embedded key; the ~9-line fix
(`50-infra/etzhayyim-did-web/kotoba-patches/0001-cacao-self-resolve-did-key.patch`)
short-circuits `did:key` issuers to `verify_signature()`. Proven end-to-end on an
isolated build: member `did:key` + self-signed CACAO → `kg.ingest` →
`{ok:true, quadCount:6}`. Verified wire-format (see `kotoba-patches/README.md`):
`aud` = node `operator_did` (keychain-stable `did:key:ze2e1699…`),
`kotoba://op/datom:transact`, **second-precision** timestamps, **base64url**
signature, **CBOR/ciborium** with camelCase `cacaoB64`, `account.<did>` entity.

## Domain-independent identity (did:key canonical, did:web demoted)

`did:web:etzhayyim.com:<handle>` roots trust in **domain/TLS ownership** — if
`etzhayyim.com` changes hands, the new owner could publish a different DID
Document for the same handle and hijack the name. So `did:web` is **NOT** the
identity; it is demoted to a non-authoritative readable alias:

- **Canonical identity = the controller `did:key`** (self-certifying — the key is
  in the DID; domain-independent). Login, control, signing, and the kotoba
  account record (`account.<did:key>`) all key on it. A change of domain owner
  does NOT affect a member's key, login, or records.
- **Handle↔key binding is self-certifying**: the controller `did:key` itself
  signs a compact EdDSA attestation `{ iss, sub, handle, iat }`
  (`$lib/auth/identity.ts::signHandleAttestation`), stored as the
  `account/handle-attestation` claim in the kotoba record. Anyone verifies it
  against the key embedded in the DID — no domain, no TLS, no registry
  (`50-infra/etzhayyim-did-web/src/identity.ts::verifyHandleAttestation`). A
  forged did:web document is detectable: it is not signed by the member's key.
- **The published DID Document is self-certifying** (`selfCertifyingDidDoc`):
  `id` = the `did:key`, `verificationMethod` = the `did:key`, and
  `did:web:etzhayyim.com:<handle>` appears only in `alsoKnownAs`. A resolver
  trusts the key; the domain is just one resolution endpoint.
- The kotoba Datom log (append-only, content-addressed) is the binding's
  provenance, with an optional Base L2 anchor (the constitution's trust-anchor
  layer) — so trust roots in the key + content-address + chain, never the domain.

This same self-certifying record backs **multi-device** (`account/device/<credId>`
= wrapped-ARK, signed by an enrolled device → the new device unwraps the SAME ARK
→ SAME `did:key`) and **key rotation** (`account/controller` = new `did:key` +
append-only `account/rotation/<n>`, signed by the CURRENT key). All three writes
(`account-ops.ts`: `publishAccount` / `enrollDevice` / `rotateKey`) ride the one
verify-only kotoba relay. did:web is unaffected by rotation — it only ever aliased
the controller.

## Verification

- Worker `tsc` clean; 12 same-origin auth tests green (8 `registerAccount` +
  4 cross-impl, incl. a frontend-derived PRF→`did:key` `account:login` CACAO
  verifying on the real worker verifier; P-256 fallback `did:key` encoding).
- `same-origin-auth.ts` typechecks clean under strict + DOM.
- **Live production**: `verifyCacao` signup control-proof `valid:true
  (ed25519-local)`; deterministic re-login (same passkey → same DID);
  tamper→401; cross-origin→403; `registerAccount` 202 gated.
- **Real browser (Chromium 148 + virtual passkey)**: clicking 新規登録 on the live
  site runs the in-app flow (no authn redirect), POSTs `verifyCacao` +
  `registerAccount` same-origin (zero authn/mcp calls), derives a `did:key`, and
  **flips the UI to signed-in**.

## Consequences

- No `authn.etzhayyim.com` / `mcp.etzhayyim.com` in the login/signup path; no
  server-minted session (NSK preserved, ADR-2605231525); kotoba-canonical-state
  preserved (ADR-2605312345).
- **Durability**: the fix is merged into `main` so the deploy pipeline carries
  it; a shared-account auto-deployer was observed reverting un-merged deploys
  within ~1 min — the SPA login buttons + `verifyCacao` survive because both are
  in `main`. `registerAccount` (gated, login-irrelevant) still reverts when a
  stale apex worker is auto-deployed; it activates fully when `main` is deployed
  + the two operator-gated steps land (below).

## Honest R0 / remaining

- `registerAccount` is `gated` until (1) the kotoba `did:key` self-resolve patch
  ships (rebuild `kotoba-server` + restart; identity is keychain-stable so
  `operator_did` survives), and (2) a Worker→node write path is opened past the
  `kotoba.etzhayyim.com` 403 edge gate, then `KOTOBA_WRITE_ENDPOINT` +
  `KOTOBA_OPERATOR_DID` are set. Until then login works without it.
- Non-PRF cross-device login + PDS authenticated-write integration (EdDSA session
  PoP accepted by `atproto.etzhayyim.com`) are follow-ons.
