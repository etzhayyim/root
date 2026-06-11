---
id: adr-2606014600-wasm-actor-runtime-gateway-and-componentize
title: "ADR-2606014600: WASM-actor runtime — trustless IPFS gateway, ameno loader, componentize-py actors"
status: accepted
doc_type: adr
topic: wasm-actor-runtime-gateway-and-componentize
authoritative: true
last_verified: 2026-06-01
priority: 6.2
axis: architecture
weight: 0.63
priority_note: "Makes the one-Worker WASM-actor model runnable end-to-end: gateway + browser loader + real componentize-py actor."
authoritative_for:
  - trustless-ipfs-gateway
  - ameno-wasm-actor-loader
  - componentize-py-actor-tier
depends_on:
  - 2606014500
  - 2606013800
  - 2605231525
  - 2605215000
  - 2605241900
related:
  - 2606011800
  - 2606012600
  - 2605252100
supersedes: []
superseded_by: []
---

# ADR-2606014600: WASM-actor runtime — gateway, ameno loader, componentize-py actors

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

ADR-2606014500 established the "one Worker, many WASM actors" model and shipped the
tsumugi Rust core + a standalone browser loader. Three pieces were needed to make it
runnable end-to-end and to validate it on a *real* Tier-B actor:

- **(b)** somewhere for the browser/mesh to actually *fetch* an actor's WASM — a
  gateway that doesn't have to be trusted;
- **(c)** the loader as a reusable part of **ameno** (the browser runtime), not a
  one-off HTML page;
- **(a)** proof that a real Python Tier-B actor (not just a hand-written Rust core)
  can become a WASM actor — via **componentize-py**.

# Decision

## D1 (b) — Trustless IPFS gateway on the apex Worker
`GET /ipfs/<cid>` on `etzhayyim.com` fetches the content-addressed bytes from
configurable **untrusted** upstream gateways (`IPFS_GATEWAYS`) and **re-hashes them
to the requested CID before serving** — the gateway is never trusted, the CID is the
trust anchor (no server key, ADR-2605231525). Content-addressed → served
`immutable`. Implemented for **raw single-block CIDv1** (`bafkrei…`, `src/cid.ts`);
multi-block UnixFS CIDs (`bafy…`) return `501` (a full IPFS node verifies those —
T2). The gateway stays the only first-party Worker surface; no per-actor host.

## D2 (c) — ameno WASM-actor loader
New module `@etzhayyim/ameno/inference/wasm-actor-loader`:
`resolveActorWasm(did)` → `fetchVerifiedWasm(cid)` (via the apex gateway, **client
re-verifies the CID** independently of the gateway) → `instantiateActor` →
`runCompute` (the `compute()/result_ptr()/memory` ABI). `loadActor(did)` does all
four. It **refuses non-raw CIDs** (browser-local = raw single-block only). Runs
unchanged in browser and Node.

## D3 (a) — componentize-py actor tier + the size boundary it reveals
A real Tier-B actor (**watatsuna** chokepoint criticality) is built to a WASI
Component-Model component with **componentize-py** (`20-actors/watatsuna/wasm`),
transpiled with **jco**, and verified headless (top chokepoint = Malacca). Because a
Python component **bundles CPython (~17.6 MB)**, its CID is **multi-block dag-pb**
(`bafybei…`). This formalizes a two-tier rule:

| tier | artifact | CID | gateway-verifiable | runtime |
|---|---|---|---|---|
| **T1 browser-local** | compact Rust/AS core (tsumugi, 23.5 KB) | raw `bafkrei…` | yes | ameno loader |
| **T2 donated-mesh** | componentize-py component (watatsuna, ~17.6 MB) | dag-pb `bafybei…` | no (full IPFS node) | jco / wasmtime / mesh |

The DID doc encodes the tier: `EtzhayyimWasmComponent` carries
`x-exec: browser-local|donated-mesh` + `x-cid-codec: raw` for raw CIDs, and
`x-exec: donated-mesh` + `x-cid-codec: dag-pb` otherwise (`toDidDoc` + publisher).

# Consequences

- The browser can fetch + integrity-verify + run a compact actor with **no trusted
  server in the loop** (apex gateway untrusted, client re-verifies the CID).
- ameno gains a first-class, tested WASM-actor loader (5/5 `node:test` green,
  including a tamper-rejection case and the full tsumugi pipeline → TSMC).
- componentize-py is proven for a real Python actor (watatsuna → Malacca top), and
  the **size/codec boundary** is now explicit policy: Rust/AS for T1, Python for T2.
- Worker `tsc` clean; the apex `cid.ts` reproduces `ipfs add --cid-version=1` exactly
  (verified against the committed tsumugi CID).

# Honest scope (R0)

- Gateway verifies **raw** CIDs only; dag-pb verification (full UnixFS/CAR
  reconstruction) deferred → those are T2. Default upstreams are public gateways
  (dweb.link/ipfs.io) until the etzhayyim kotoba/IPFS pin is wired via `IPFS_GATEWAYS`.
- watatsuna component (~17.6 MB) + its jco transpilation are **gitignored** (rebuilt
  from `app.py` + `wit/` via `build.sh`); the CID is recorded in
  `watatsuna-actor.meta.json`. Bounded `:representative` seed (reproduces the
  direction, not the exact 940.16 Tbps).
- Live IPFS pinning + mesh (T2) execution are operator-gated. Inference unaffected —
  Murakumo-only / ameno frozen-edge (ADR-2605215000).

# Alternatives Considered

- **Trust a public IPFS gateway directly (no re-verify).** Rejected: the gateway
  would become a trusted party; CID re-hashing makes it untrusted.
- **Ship Python actors as raw CIDs too.** Not possible — multi-MB → multi-block by
  construction; hence the explicit T1/T2 split.
- **One-off loader HTML instead of an ameno module.** Rejected: the loader is core
  runtime; it belongs in ameno where WebGPU/WebNN inference already lives.

# References

- `50-infra/etzhayyim-did-web/src/cid.ts` + `worker.ts` (`/ipfs/<cid>` route)
- `20-actors/ameno/src/inference/wasm-actor-loader.ts` + `tests/wasm-actor-loader.smoke.test.ts`
- `20-actors/watatsuna/wasm/` (app.py, wit/, build.sh, verify.mjs, meta)
- ADR-2606014500 (one-Worker WASM-actor model), ADR-2606013800 (dynamic did.json),
  ADR-2605231525 (no-server-key), ADR-2605215000 (Murakumo-only), ADR-2605241900
  (baien edge target), ADR-2606012600 (watatsuna)
