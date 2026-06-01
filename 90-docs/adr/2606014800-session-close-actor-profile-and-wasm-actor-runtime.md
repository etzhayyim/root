---
id: adr-2606014800-session-close-actor-profile-and-wasm-actor-runtime
title: "ADR-2606014800: Session close — actor profile, dynamic did.json, one-Worker WASM-actor runtime"
status: active
doc_type: adr
topic: session-close-actor-profile-and-wasm-actor-runtime
authoritative: false
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.40
priority_note: "Documentation-only session-close record; authoritative designs are the three referenced ADRs."
authoritative_for: []
depends_on:
  - 2606013800
  - 2606014500
  - 2606014600
related:
  - 2605212030
  - 2605241800
  - 2606011800
  - 2606012600
supersedes: []
superseded_by: []
---

# ADR-2606014800: Session close — actor profile + WASM-actor runtime

**Status**: active (documentation-only)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Documentation-only closure for the 2026-06-01 session that began with
*「`/profile/did:web:...:tsumugi` で profile が見つからない. また最新の kotoba の設計だと
actor の did は何?」* and evolved into *「CF Worker は etzhayyim.com のみにして、他の
actor は IPFS/他 protocol、kotoba は WASM なのでブラウザで読み込んで local 実行できる?」*.
Three authoritative ADRs were produced and landed on `main`; this record indexes
them and states the next steps.

# What shipped (all merged to main)

1. **ADR-2606013800 — Actor profile + dynamic did.json** (PR #688). New SSoT
   `00-contracts/schemas/actor-profile.kotoba.edn` (`:actor/*`, public `actors-v1`
   graph) backs BOTH the per-actor DID Document AND the `app.bsky.actor.getProfile`
   view. The apex Worker now ISSUES `did.json` dynamically — 3-tier fail-open
   KV → kotoba pull → compiled `INFRA_ACTORS` — through pure `toDidDoc()`;
   `verificationMethod` is an on-chain ERC725 mirror (empty → no server key, TLS
   trust). `/actor/<h>/profile.json` + getProfile short-circuit + yoro SSR resolve
   actor DIDs via apex → `/profile/did:web:...:tsumugi` renders. **Canonical actor
   DID = `did:web:etzhayyim.com:actor:<handle>`.**

2. **ADR-2606014500 — One Worker, many WASM actors** (PR #689). `etzhayyim.com` is
   the ONLY first-party CF Worker (identity / registry / proxy — no actor compute).
   An actor's state = kotoba Datom log; its logic = a content-addressed WASM
   component on IPFS, declared in the DID doc as `EtzhayyimWasmComponent`
   (`ipfs://<cid>`) from `:actor/wasm-cid`. Tiers: T1 browser-local (ameno) / T2
   donated mesh (libp2p); per-actor Worker removed; all `#xrpc-https-legacy` hosts
   retired. PoC: tsumugi-core Rust→wasm (23.5 KB, raw CID), browser + headless
   loaders resolve → CID-verify → run locally → top 取 = TSMC.

3. **ADR-2606014600 — WASM-actor runtime** (PR #693). (b) Apex trustless
   `GET /ipfs/<cid>` gateway (re-hashes bytes to the CID before serving; raw
   verified, dag-pb → 501). (c) `@etzhayyim/ameno/inference/wasm-actor-loader`
   (resolve → client-side CID re-verify → instantiate → run; 5/5 `node:test`). (a)
   watatsuna componentize-py WASI component (jco-transpiled, Malacca top), which
   bundles CPython (~17.6 MB → dag-pb CID) and so formalizes the **T1 raw =
   browser-local / T2 dag-pb = donated-mesh** rule, encoded in the DID doc via
   `x-exec` + `x-cid-codec`.

# Verification (this session)

Worker `tsc` clean across all PRs; `cid.ts` reproduces `ipfs add --cid-version=1`
exactly; ameno `tsc` clean + 5/5 tests (incl. tamper rejection + full tsumugi
pipeline → TSMC); watatsuna component runs via jco (Malacca 865 Tbps); publisher
materializes 10/10 actors. Every substrate pre-commit gate passed; `e7m-verify`
skipped where the local CLI lacked the `verify` subcommand (environment gap, not a
content violation). Large build artifacts (17.6 MB watatsuna component + jco output)
are gitignored and rebuilt from source.

# Next steps

- **componentize-py more Tier-B actors** (okaimono, kanae, danjo…) → T2 mesh
  components; or port hot ones to Rust/AS for T1 browser-local (raw CID).
- **Wire `IPFS_GATEWAYS`** to the etzhayyim kotoba/IPFS pin so the gateway serves
  first-party content (not public dweb.link/ipfs.io); add **dag-pb (UnixFS/CAR)
  verification** so T2 components are also trustless-gateway-verifiable.
- **ameno UI surface** — call `loadActor()` from the ameno appview (a "run this
  actor" panel), and wire the tsumugi `loader/index.html` into ameno proper.
- **Operator enablement** — create the `ACTOR_KV` namespace + run
  `publish-actor-records.mjs --put-kv` / `--ingest-kotoba` so kotoba becomes the
  live did.json source (today: compiled fallback). Provision a public kotoba read
  surface for `KOTOBA_ENDPOINT`.
- **On-chain `verificationMethod`** — populate the ERC725 mirror once
  EtzhayyimAuthz is on Base Sepolia (ADR-2605212030 Phase B).
- **T2 mesh execution** — a kotoba/e7m node that fetches a dag-pb component CID,
  runs it (wasmtime/jco), and returns results over libp2p `/x/etzhayyim/xrpc/1.0`.

# References

- ADR-2606013800, ADR-2606014500, ADR-2606014600 (authoritative designs)
- PRs #688, #689, #693
- `50-infra/etzhayyim-did-web/` (apex Worker + cid.ts + publisher),
  `20-actors/ameno/src/inference/wasm-actor-loader.ts`,
  `20-actors/tsumugi/wasm/`, `20-actors/watatsuna/wasm/`,
  `00-contracts/schemas/actor-profile{,-seed}.kotoba.edn`
