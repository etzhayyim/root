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

## Account write path — member-signed content-addressed blocks (LIVE)

Account publish does NOT write to a central kotoba node: writes there are
intentionally operator-local (`kotoba.etzhayyim.com` is read-only by design,
ADR-2606013200; `kotoba.gftd.ai` is being pruned). Instead the account record is a
**member-signed, content-addressed block** published to the apex
`com.etzhayyim.apps.kotoba.block.put` (main's `kotoba-publish`: verifies the
member Ed25519 sig over the root CID, then **IPFS-pins the block via
`kotobase.net`** as the **canonical content-addressed store**). The block's
identity IS its CID — resolvable + verifiable by CID from any IPFS gateway, with
**NO dependency on a centralized KV** (the apex KV in `kotoba-publish` is only a
fast cache for the social feed's read SW, never the source of truth for account
records — substrate boundary, no centralized DB). The most domain-independent
form: a **CID signed by the member's `did:key`** — dependent on neither the
domain, a central node, nor a KV. **No gated infra — it is LIVE** (proven: the
real `block-publish.ts` module published an account block → `{ok:true, root:bafkrei…}`).

- CID = `sha2-256` raw CIDv1 (`b`+base32), byte-identical to `cid.ts::cidV1Raw`
  (locked by a frontend↔apex cross-impl test).
- `block.put` author DID = `did:key:z`+hex(32B pubkey) (the kotoba-publish
  convention) — the SAME Ed25519 key as the standard `did:key:z6Mk…` login
  identity, carried inside the record as `account/did`.
- Per-member account graph `acct-<pubkeyHex>` (no cross-member root contention).
- Frontend `$lib/auth/block-publish.ts` + `account-ops.ts`
  (`publishAccount` / `enrollDevice` / `rotateKey`).
- (The earlier verify-only `kg.ingest` CACAO relay — `registerAccount` /
  `handleAccountWrite` / `cbor.ts` / `kotoba-write.ts` — remains a tested
  alternative if a central-node write surface is ever exposed; `block.put` is the
  primary live path.)

## Honest R0 / remaining

- The **read side is content-addressed, with NO KV**: fetch the account block
  **by CID from IPFS** (kotobase.net pin / any gateway; the apex trustless
  `/ipfs/<cid>` gateway re-verifies the CID), then
  `identity.ts::resolveAccountFromBlock` — (1) re-computes the CID and asserts it
  matches the bytes (content-address integrity), (2) verifies the self-certifying
  `account/handle-attestation` (`account/did`'s own signature over the handle).
  Trust roots in the content-address + the member's `did:key`, never a KV. The
  read core (`resolveAccountFromBlock` + `verifyAccountBlock`, both KV-agnostic —
  they take block bytes) is **landed + tested**. The only remaining wiring is the
  mutable **handle→CID pointer**, which must live in the kotoba Datom log / DID
  doc / L2 anchor (content-addressed/anchored), **never a centralized KV**
  (substrate boundary, no centralized DB).
- `enrollDevice` + `rotateKey` are implemented + live-capable (same `block.put`
  path) but not yet wired into a settings UI (library API; the wrapped-ARK store +
  recovery UX is the remaining work).
- Non-PRF cross-device login + PDS authenticated-write integration (EdDSA session
  PoP accepted by `atproto.etzhayyim.com`) are follow-ons.
