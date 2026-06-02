---
id: adr-2606014500-one-worker-wasm-actor-model
title: "ADR-2606014500: One Worker, many WASM actors — actors as content-addressed WASM on IPFS, executed browser-local"
status: accepted
doc_type: adr
topic: one-worker-wasm-actor-model
authoritative: true
last_verified: 2026-06-01
priority: 6.2
axis: architecture
weight: 0.64
priority_note: "Collapses all first-party CF Workers to etzhayyim.com; actors become content-addressed WASM run browser-local / donated-mesh."
authoritative_for:
  - wasm-actor-execution-model
  - actor-transport-ipfs-libp2p
  - per-actor-host-retirement
depends_on:
  - 2605241800
  - 2606013800
  - 2605241900
  - 2605231525
  - 2605215000
  - 2605262130
related:
  - 2606011800
  - 2606012100
supersedes: []
superseded_by: []
---

# ADR-2606014500: One Worker, many WASM actors

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Question raised: *can etzhayyim run **only one** Cloudflare Worker (`etzhayyim.com`)
and have every other actor run on IPFS / another protocol — ideally as **WASM loaded
and executed locally in the browser**, since kotoba already runs as WASM?*

Current state makes this mostly true already and identifies the residue:

- Per-actor CF Workers were **already collapsed** to the single `etzhayyim-did-web`
  Worker (ADR-2605241800 Phase A). New actors are path-based DIDs, not subdomains.
- BUT the DID `service[]` still carried `https://<actor>.etzhayyim.com`
  `#xrpc-https-legacy` endpoints — the visual residue of "a host per actor".
- The pieces for local execution already exist: **kotoba browser node** (ADR-2606013600,
  WASM read/write + browser-native Pregel + Service-Worker `/xrpc`), **ameno**
  (WebGPU/WebNN browser inference), **baien edge-target** (WASM-32 + iPhone 12 +
  Android 4 GB, ADR-2605241900), DID-doc **libp2p** multiaddrs, and **dynamic
  did.json issuance** from kotoba (ADR-2606013800).

So the missing decision is only: *where does an actor's executable code live, and how
is it addressed and trusted* — not new infrastructure.

# Decision

**`etzhayyim.com` is the only first-party Cloudflare Worker. An actor's executable
face is a content-addressed WASM component on IPFS, resolved via the actor's DID and
executed locally — in the browser (ameno) or on a donated mesh node — with NO
per-actor server.**

## D1 — Role split
- `etzhayyim.com` Worker = **identity + registry + apex routing only**: dynamic
  `did.json` (ADR-2606013800), `/actors`, `/.well-known/*`, `/donate`, thin proxy,
  and (future) a trustless IPFS gateway `etzhayyim.com/ipfs/<cid>`. It hosts **no
  actor compute**.
- Actor **state** = kotoba Datom log (already canonical, ADR-2605312345).
- Actor **logic** = a content-addressed WASM component (IPFS CID).

## D2 — DID document declares the WASM component
A new service entry, listed FIRST so resolvers prefer local execution:
```json
{ "id": "did:web:etzhayyim.com:actor:<h>#wasm",
  "type": "EtzhayyimWasmComponent",
  "serviceEndpoint": "ipfs://<cid>",
  "x-exec": "browser-local|donated-mesh", "x-runtime": "kotoba-wasm" }
```
Sourced from `:actor/wasm-cid` in the kotoba `actors-v1` graph (schema
`actor-profile.kotoba.edn`), emitted by `toDidDoc()` in the apex Worker.

## D3 — Execution tiers (no per-actor server)
- **T1 browser-local (ameno)**: client resolves the DID → fetches the WASM from IPFS
  (gateway / helia) → instantiates → runs locally (+ WebGPU/WebNN for inference). The
  user's "load WASM in the browser, run locally".
- **T2 donated mesh (kotoba / e7m)**: the same WASM runs headless on donated compute
  via libp2p `/x/etzhayyim/xrpc/1.0`, for cron / heavy / availability. A recognized
  in-kind compute donation (ADR-2606012100).
- **T0 removed**: no per-actor CF Worker.

## D4 — Trust model (no server key)
- did:web trust root = **TLS** (the DID doc is fetched over HTTPS from `etzhayyim.com`).
- WASM trust root = **its CID** (content address). The loader recomputes
  `sha256 → CIDv1` and refuses bytes that don't match the DID-doc CID.
- No platform-held signing key anywhere (ADR-2605231525). `verificationMethod`
  remains the on-chain ERC725 mirror (empty until chain wiring).

## D5 — Retire per-actor HTTPS hosts
Execute ADR-2605241800 Phase C: drop every `#xrpc-https-legacy`
(`https://<actor>.etzhayyim.com`) service entry. Actors keep only the shared PDS
host, libp2p multiaddrs, and (now) the WASM component. No host per actor.

## D6 — Inference stays Murakumo-only
Running an actor's WASM locally does NOT relax the inference invariant: any model
inference inside an actor goes through ameno frozen-edge (browser) or the Murakumo
fleet (mesh) — never commercial GPU (ADR-2605215000, Charter Rider §2(i)).

# Consequences

- One first-party Worker; everything else is content-addressed WASM + kotoba state +
  libp2p/IPFS transport. Adding an actor = publish a WASM CID + an `:actor/*` record;
  no new Worker, no new host.
- DID documents are clean: PDS + libp2p + WASM component; zero per-actor hostnames.
- A browser can run an actor with no server in the loop, verifying integrity by CID.
- **PoC shipped (tsumugi)**: `20-actors/tsumugi/wasm/tsumugi-core` (Rust →
  `wasm32-unknown-unknown`, 23.5 KB) computes edge-primary 取-concentration; real IPFS
  CIDv1 `bafkreidfttpqimwnx4i5a3rswum3orcg3qfa3q7fwts6axgqtcpuokddfi`; `loader/index.html`
  (browser) + `loader/verify.mjs` (headless) both **resolve → recompute-CID-integrity
  → execute locally**, asserting top 取 = TSMC. tsumugi's did.json now carries the
  `EtzhayyimWasmComponent` service; all 10 actors' legacy HTTPS hosts removed; worker
  `tsc` clean.

# Honest scope (R0)

- tsumugi-core embeds a bounded `:representative` seed graph (real deployments read the
  full graph from the kotoba Datom log); it reproduces the *direction* of the finding
  (TSMC top 取), not exact analyze.py numbers.
- `wasm32-unknown-unknown` core module, not yet a full WASI/Component-Model component;
  the kotoba-wasm runtime, libp2p browser dispatch (T2), live IPFS pinning, and the
  `etzhayyim.com/ipfs/<cid>` trustless gateway are operator-gated / future work.
- Most Tier-B actors are Python langgraph cells today → `componentize-py` to WASM is
  the migration path (already used elsewhere for "langgraph py→WASM cell").
- The shared **PDS** (`atproto.etzhayyim.com`) remains one host (shared infra, not
  per-actor); libp2p-ifying it is later work.

# Alternatives Considered

- **Keep per-actor Workers / subdomains.** Rejected: contradicts the single-Worker goal
  and ADR-2605241800; multiplies hosts and deploy surface.
- **Ship actor logic as JS bundles, not WASM.** Rejected: WASM is the portable,
  sandboxed, content-addressable unit that already runs in ameno + kotoba-browser-node
  and meets the baien edge target (ADR-2605241900); CID integrity needs a stable binary.
- **Sign the WASM with a platform key.** Rejected: violates ADR-2605231525. Content
  addressing (CID) provides integrity without a key.
- **Centralize execution on the mesh only (no browser).** Rejected: the explicit goal
  is browser-local execution; the mesh (T2) is the headless complement, not a
  replacement.

# References

- `20-actors/tsumugi/wasm/` — tsumugi-core crate + browser loader + headless verify + build.sh
- `00-contracts/schemas/actor-profile.kotoba.edn` — `:actor/wasm-cid`
- `50-infra/etzhayyim-did-web/src/registry/actor-profiles.ts` — `EtzhayyimWasmComponent` emission
- ADR-2605241800 (single did-web Worker, libp2p, Phase C), ADR-2606013800 (dynamic
  did.json), ADR-2606013600 (kotoba browser node), ADR-2605241900 (baien edge target),
  ADR-2605231525 (no-server-key), ADR-2605215000 (Murakumo-only), ADR-2606012100
  (in-kind compute donation), ADR-2606011800 (tsumugi)
