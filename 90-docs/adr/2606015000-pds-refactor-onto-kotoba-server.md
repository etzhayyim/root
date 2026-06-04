---
id: adr-2606015000-pds-refactor-onto-kotoba-server
title: "ADR-2606015000: refactor the AT Protocol PDS onto kotoba-server (substrate + WASM)"
status: proposed
doc_type: adr
topic: pds-refactor-onto-kotoba-server
authoritative: true
last_verified: 2026-06-02
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "Unifies the AT Protocol PDS onto the canonical kotoba substrate, removing the separate TS PDS worker; lands PDS session auth as Rust PoP verification (zero-access, ADR-2606014000/2606014500 C-3)."
authoritative_for:
  - pds-runtime-home
  - pds-session-auth
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2606014000-kotoba-passkey-cacao-signal-secrecy
  - adr-2606014500-etzhayyim-auth-zero-access-proton-alignment
related:
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
supersedes: []
superseded_by: []
---

# ADR-2606015000: refactor the AT Protocol PDS onto kotoba-server (substrate + WASM)

**Status**: proposed
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

The AT Protocol PDS the browser talks to (`atproto.etzhayyim.com`) was a separate
TypeScript Cloudflare Worker (`50-infra/cloudflare/workers/atproto/src/`),
containerised for k8s via `50-infra/k8s/atproto-pds/` (a thin Bun shim that
`import worker from "./app"` + delegates auth to the auth Worker over
`AUTH_SERVICE`). Two problems:

1. **That worker's source is absent from the working tree** — `bun-entry.ts`
   imports `./app` and the Dockerfile `COPY 50-infra/cloudflare/workers/atproto/`,
   but that directory no longer exists here (relocated/archived). It cannot be
   edited or reviewed in-repo, which blocked wiring PDS-side session-PoP
   verification (ADR-2606014000/2606014500 C-3).
2. **It duplicates substrate concerns.** kotoba-server already serves XRPC, owns
   the canonical Datom state (ADR-2605312345), the MST ingress membrane
   (ADR-2605231902), Signal E2E (`signal_xrpc`), and now the passkey-rooted
   account/key-custody surface (`account_xrpc`, `signal_xrpc` binding). A second
   stateful TS PDS beside it is redundant and a second trust surface.

Per ADR-2605262130 kotoba is the **canonical substrate engine**. The PDS should
run **on** it, not beside it.

# Decision

**Refactor the PDS so its AT Protocol XRPC surface is served by kotoba-server,
and retire the separate TS PDS worker.** Session authentication becomes a Rust
Proof-of-Possession check on kotoba-server (no server-held signing key), aligning
the PDS with the zero-access posture (ADR-2606014000/2606014500).

## D1 — PDS session auth = Rust PoP on kotoba-server (LANDED)

`pds_session.rs::verify_session_pop(token, resolver, now)` verifies the client's
compact EdDSA JWS session PoP against the issuer DID's Ed25519 key, resolved via
the `CompositeDidResolver`: **`did:key` trustlessly** (key is the DID itself),
**`did:web`/`did:plc` from the DID document** (the ERC725 / apex-Worker mirror,
ADR-2606013800). Unresolvable / no-Ed25519-method DIDs are reported unverified —
never falsely vouched. Exposed at `POST /xrpc/com.etzhayyim.pds.session.verify`.
This is the kotoba-server-native equivalent of the auth Worker's
`verifySessionPoP` and the home the PDS forwards to. (kotoba-server pds_session
**5 tests green**: did:key verify, tampered/expired rejected, did:web via resolved
doc, unresolvable not-vouched.)

## D2 — PDS XRPC surface ports onto kotoba-server (phased)

The AT Protocol PDS methods (`com.atproto.server.{createSession,refreshSession,
getSession,deleteSession}`, `com.atproto.repo.*`, `com.atproto.sync.*`,
`com.atproto.identity.*`) are ported to kotoba-server modules
(`pds_xrpc`), reading/writing the canonical Datom state directly instead of a
separate store. The MST ingress membrane (ADR-2605231902) and Signal surface are
already here. This is incremental: D1 (session auth) lands first; record/repo and
sync follow.

## D3 — WASM execution model (honest)

kotoba's execution vehicle is the **WASM Component Model** (`kotoba-runtime`,
WIT worlds `kotoba-node`/`kotoba-udf`) — PDS request handlers and UDFs run as
WASM components on the substrate, which is the "kotoba-server WASM" target.
**Caveat (per `40-engine/kotoba/CLAUDE.md`)**: the full native `kotoba-server`
(axum + tokio + `wasmtime`, which is native-only) does **not** itself compile to
`wasm32`; browser/edge execution requires the planned `kotoba-runtime-web` crate
(browser-native WebAssembly + IdbBlockStore + metered interpreter). So "PDS as
kotoba-server WASM" means: PDS logic as WASM components hosted by kotoba-server
(landable now), with a fully wasm32 edge PDS gated on `kotoba-runtime-web`.

# Consequences

**Positive**
- One substrate, one trust surface: the PDS reads the canonical Datom state
  directly; no second stateful service or duplicated auth.
- PDS session auth is zero-access (client PoP verified in Rust; no server signing
  key) and testable in-repo — unblocking what the missing TS worker prevented.
- did:web PoP verification reuses the same resolver + ERC725-mirror anchor as
  Signal binding resolution (ADR-2606014000), so identity trust is uniform.

**Negative / honest scope**
- **Landed = D1 only** (session-PoP verify endpoint + module, 5 tests green). The
  full XRPC port (D2) is not done — repo/record/sync/identity methods still live
  in the (absent) TS worker until ported.
- The legacy TS PDS source is **not in the working tree**; this ADR supersedes its
  *role* but cannot delete code that isn't here. Migration must re-home or retire
  the container build (`50-infra/k8s/atproto-pds/Dockerfile` still references the
  missing path).
- Full wasm32 edge PDS is gated on `kotoba-runtime-web` (unbuilt). Native
  kotoba-server hosts the PDS today.

# Alternatives Considered

- **Restore + edit the TS PDS worker.** Rejected as the long-term home: keeps a
  second stateful service + trust surface beside kotoba, against ADR-2605262130.
  (A short-term restore may still be needed to retire it cleanly.)
- **PDS keeps delegating all auth to the auth Worker.** Rejected as the end state:
  the PDS-on-kotoba owns verification directly (Rust PoP), removing a hop; the
  auth Worker keeps its own copy for its own surfaces.

# References

- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605312345 (kotoba Datom first-class canonical state)
- ADR-2606014000 (passkey-rooted secrecy) / ADR-2606014500 (auth zero-access, C-3 PoP)
- ADR-2605231902 (feed-post MST membrane on the substrate)
- `40-engine/kotoba/crates/kotoba-server/src/{pds_session,pds_xrpc}.rs`
- `40-engine/kotoba/CLAUDE.md` — WASM component model + `kotoba-runtime-web` note
- `50-infra/k8s/atproto-pds/` — current Bun container (delegates to AUTH_SERVICE)
