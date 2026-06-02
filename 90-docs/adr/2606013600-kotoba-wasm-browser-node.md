---
id: adr-2606013600-kotoba-wasm-browser-node
title: "ADR-2606013600: kotoba browser node — WASM read/write node + browser-native Pregel/UDF guests"
status: active
doc_type: adr
topic: kotoba-wasm-browser-node
authoritative: true
last_verified: 2026-06-02
priority: 6.0
axis: architecture
weight: 0.70
priority_note: "Edge implementation of the kotoba canonical Datom log; turns the browser into a first-class substrate replica + compute node."
authoritative_for:
  - kotoba-wasm-browser-node
  - kotoba-guest-runtime-abstraction
depends_on:
  - adr-2606013200-yoro-kotoba-feed-readpath-migration
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605241900-baien-edge-target-invariant
  - adr-2606012100-donation-funded-operation-and-compute-node-donation
related:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606013600: kotoba browser node — WASM read/write node + browser-native Pregel/UDF guests

**Status**: active — P0–P3 shipped + verified (real browser), browser-native /actors deployed
**Date**: 2026-06-01 (impl 2026-06-01..02)
**Deciders**: Jun Kawasaki

# Context

The kotoba canonical Datom log (ADR-2605312345) is today served only by a native
`kotoba serve` process (axum HTTP on `:8077`, Kubo cold tier, wasmtime guests).
ADR-2606013200 made the yoro feed read through that server via the
`com.etzhayyim.apps.kotoba.datomic.datoms` XRPC (`@etzhayyim/yoro-rw-free`). Operationally
this leaves every browser read dependent on a reachable server endpoint (currently a
laptop + CF Tunnel publishing `kotoba.etzhayyim.com`), which is fragile and is *not*
the edge-first posture the charter mandates: the **baien edge-target invariant**
(ADR-2605241900) requires first-party capability to run on WASM-32 / iPhone 12+ /
Android 4 GB, and ADR-2606012100 recognises the browser as a **donated compute node**
(ameno class).

We want the browser itself to be a **kotoba replica node**: it materialises the same
content-addressed blocks, runs the read engine (and eventually writes + guest compute)
locally, and only talks to a remote peer for *block sync*, not for *query execution*.

Grounding facts established from the `40-engine/kotoba` workspace:

- A browser block store **already exists**: `kotoba-store-web::IdbBlockStore`
  (IndexedDB, `cfg(target_arch = "wasm32")`), today positioned as a rolling **cache**.
  The block abstraction is `kotoba_core::async_store::AsyncBlockStore`.
- The read path is `kotoba-kqe` arrangements over the four Datomic roots
  (`ROOT_EAVT / ROOT_AEVT / ROOT_AVET / ROOT_VAET`, `kotoba-datomic::distributed`),
  exposed by `kotoba-datomic::Db::datoms_index(...)`. This is pure async compute over
  the block store — **no `tokio::spawn` / runtime / `block_on`** was found in
  `kotoba-kqe` / `kotoba-datomic` read paths.
- The **primary wasm blocker** is that core crates (`kse`, `kqe`, `datomic`, `graph`,
  `crypto`, `signal`, `store`) depend on `tokio` with `rt-multi-thread` / `full`. The
  actual usage in the read path is `tokio::sync` + `async-trait`; `rt-multi-thread` is
  largely for `#[tokio::test]`.
- Guest compute (Pregel / UDF) is split cleanly: `kotoba-vm::WasmPregelRunner` is a
  **pure-Rust BSP orchestrator** that invokes a guest's `run(ctx_cbor)` *export* once
  per superstep through `kotoba-runtime::WasmExecutor`. Only `WasmExecutor` touches
  `wasmtime` (Component Model + WASI Preview 2 host functions in
  `kotoba-runtime::host`). Guests are `wasm32-wasip2` components (`kotoba-guest`).
- wasmtime does **not** target `wasm32` — so "run wasmtime in the browser" is a
  non-goal. The browser already *has* a WebAssembly engine; the correct move is to run
  the **same Component Model guest** on it via `jco`
  (`@bytecodealliance/jco` transpile + `@bytecodealliance/preview2-shim`).

# Decision

Build a **browser kotoba node** in three architectural pieces, and **refactor guest
execution behind a runtime trait** so Pregel/UDF run on the browser's native
WebAssembly engine — not just server-side.

## D1. Portable core → `wasm32-unknown-unknown`

Feature-gate the core crates so the read/write + storage engine compiles to wasm:

- `tokio` is narrowed on wasm to `features = ["sync","macros"]` via
  `[target.'cfg(target_arch = "wasm32")'.dependencies]`; `rt-multi-thread`/`net`/`time`
  stay native-only. `#[tokio::test]` is gated `cfg(not(wasm32))`; wasm tests use
  `wasm-bindgen-test`.
- `getrandom = { features = ["js"] }` on wasm; `block_on` sites become `await`;
  any `spawn` becomes `wasm_bindgen_futures::spawn_local`.
- Native-only transport (`tokio-tungstenite` in `kotoba-graph`, `reqwest` in
  `kotoba-core::foreign-http` / `kotoba-store`) moves behind a `native` feature.

Ported set (the **read/write node**): `kotoba-core`, `kotoba-edn`, `kotoba-crypto`,
`kotoba-kse`, `kotoba-kqe`, `kotoba-datomic`, `kotoba-graph`, `kotoba-store-web`.
Out of the read/write node: `kotoba-net`/`-dht` (libp2p), `kotoba-ipfs` (Kubo),
`kotoba-llm` (Murakumo-only, ADR-2605215000), `kotoba-server` (axum).

## D2. New crate `kotoba-wasm` (cdylib, wasm-bindgen)

Assembles the portable core + `IdbBlockStore` (promoted from cache to a first-class
block backend, with an OPFS journal for writes) and exposes a JS API whose
request/response shapes are **identical to the XRPC NSIDs** so it is an HTTP drop-in:

```rust
#[wasm_bindgen]
impl KotobaNode {
  pub async fn open(graph_cid: String) -> Result<KotobaNode, JsValue>;
  pub async fn datoms(&self, req: JsValue) -> Result<JsValue, JsValue>;   // datomic.datoms
  pub async fn pull(&self, req: JsValue) -> Result<JsValue, JsValue>;     // datomic.pullMany
  pub async fn q(&self, datalog_edn: String) -> Result<JsValue, JsValue>; // datalog query
  pub async fn transact(&self, graph: String, tx_edn: String) -> Result<JsValue, JsValue>; // P2
  pub async fn sync_from(&self, source_url: String) -> Result<JsValue, JsValue>;            // delta block pull
  pub async fn run_pregel(&self, program_cid: String, ctx_cbor: Vec<u8>) -> Result<JsValue, JsValue>; // D4
  pub async fn status(&self) -> Result<JsValue, JsValue>;
}
```

Target `wasm32-unknown-unknown` via `wasm-bindgen` (distinct from the `wasm32-wasip2`
*guest* path). `wasm-opt -Oz`; binary budget bound to the baien edge invariant.

## D3. Transparent integration via a Service Worker shim

A Service Worker intercepts `fetch('/xrpc/com.etzhayyim.apps.kotoba.*')` and dispatches to
`kotoba-wasm`. Therefore **`@etzhayyim/yoro-rw-free` is unchanged** — set its
`KOTOBA_URL` to same-origin (`/`) and the reader cannot tell a local WASM node from a
remote server. On a local miss for a query the node can't satisfy (e.g. a guest the
browser hasn't loaded), the SW **write-throughs to a remote kotoba** (hybrid routing).
This is the durable replacement for the laptop-tunnel read dependency.

## D4. Guest-runtime abstraction — browser-native Pregel/UDF

`WasmPregelRunner` stays pure-Rust; only guest invocation is abstracted:

```rust
#[async_trait(?Send)]
pub trait GuestRuntime {
  async fn run(&self, program: &ComponentRef, ctx_cbor: &[u8], host: HostCaps)
    -> Result<InvokeResult, RuntimeError>;
}
```

- **Native** `WasmtimeRuntime` — the existing `kotoba-runtime::WasmExecutor`
  (wasmtime Component Model + WASI-P2 host fns). Unchanged behaviour.
- **Browser** `BrowserComponentRuntime` — runs the **same `wasm32-wasip2` component**
  on the browser's WebAssembly engine. Build step: `jco transpile guest.wasm` →
  ES module; WASI-P2 imports satisfied by `@bytecodealliance/preview2-shim`; the
  kotoba host interfaces (`kotoba:kais/{kqe.quad, kse, inference, http}` from
  `kotoba-runtime/wit/world.wit`) are implemented in JS/wasm-bindgen and wired back to
  the `KotobaNode` (quad access → `IdbBlockStore`/kqe; `inference` → **disabled in the
  storage node**, Murakumo-only invariant; `http` → `fetch` under the existing
  allow-list + gas).

The Pregel BSP loop, message passing, accumulated-quad collection, and gas accounting
are identical across both runtimes because they live in `kotoba-vm`, not in the
runtime. The guest `.wasm` artifact is the **same component** in both environments —
no fork, no second guest ABI.

## D5. Sync, writes, persistence

- **Seed / delta sync** over the existing `SyncWindow` design (`kotoba-store-web`):
  source priority (1) remote kotoba CAR / `getBlocks` export, (2) IPFS gateway,
  (3) **Phase 3** libp2p-in-browser (WebTransport/WebRTC) = the ameno/donation mesh.
  Every block is **CID-verified on arrival** → trustless replication. IDB scope is
  bound **per graph** (e.g. `yoro-social-v1` only) for the edge invariant.
- **Writes (Phase 2)**: local `transact` appends Datoms to an **OPFS journal**,
  recomputes arrangements, and optionally pushes the commit to a remote kotoba or
  gossips it on the mesh. Offline-first; reconcile on reconnect against the
  content-addressed commit DAG.

# Consequences

- The browser becomes a **first-class kotoba replica + compute node**, not a cache.
  yoro `/search` (and the rest of the feed read path) runs **fully in-browser**;
  remote reachability is needed only for initial block seed and write push.
- Directly delivers the **baien edge invariant** posture and the **ameno donated-node**
  story (ADR-2606012100): joining the substrate is "open a tab".
- **No new substrate**: still the kotoba Datom log, content-addressed blocks
  (ADR-2605312345 / 2605262130). No RW/SQL. **Murakumo-only inference preserved** —
  the storage node exposes no inference; the `inference` host import is disabled there.
- One guest ABI, two runtimes (wasmtime native / browser-native via jco) → Pregel/UDF
  authored once, run server-side **and** in the browser.

# Phases (P0 is the feasibility gate)

- **P0 ✅ (shipped, kotoba PR #14)**: `kotoba-wasm` crate; read core on
  `wasm32-unknown-unknown`. **Gate measured empirically**: the ONLY blocker is
  tokio's `net` feature pulling `mio`; `kotoba-kqe` now feature-gates tokio per
  target (native = full, wasm32 = `sync`). `searchActors` over the kqe arrangement
  returns `tsumugi` (native test green; bundle 87 KiB gzip).
- **P1 ✅ (shipped, kotoba PR #14/#15 + yoro deploy)**: `loadDatoms()` hydration
  from the `datomic.datoms` JSON; **Service-Worker transparent `/xrpc` shim** so
  `@etzhayyim/yoro-rw-free` is unchanged; **IndexedDB persistence** (reseed-free
  reload, verified cold-restart in Chromium); snapshot **delta** refresh. The
  browser node is the durable read path; the SW also **backfills** registered
  actors so `/search` never silently degrades when the live server loses data.
- **P2 ✅ (shipped, kotoba PR #15 + yoro deploy)**: local `transact()` +
  `exportDatoms()` + **OPFS append-only tx journal** (verified in Chromium: write
  lands, journals, survives cold restart).
- **P3 ✅ (shipped, kotoba PR #16 + commits)**: the **real `kotoba-guest`**
  (kotoba-node world) built to `wasm32-wasip2`, transpiled by **jco**, run on the
  browser WebAssembly engine with `kotoba:kais/{kqe,kse,auth}` host imports wired
  to `KotobaNode` (llm disabled — Murakumo-only); `kqe.assert-quad` lands in the
  node. **JS BSP multi-superstep driver** (browser `WasmPregelRunner`) verified in
  a **real browser** (Playwright/Chromium). `GuestRuntime` trait extraction (native
  side) + libp2p-in-browser P2P sync (ameno mesh) remain follow-ons.
- **Browser-native /actors ✅ (deployed)**: `etzhayyim.com/actors` renders every
  referenced actor **client-side** via the in-page kotoba node (no server query for
  the actor data); same-origin CSP, no tracker (CF beacon CSP-blocked). `?static=1`
  no-JS fallback retained.

# Honest risks

- The tokio feature-gate may be more deeply coupled inside `kse` than the read-path
  grep suggests — **P0 measures this empirically** and is the go/no-go.
- Arrangement working-set must fit mobile memory → per-graph scope + lazy/streamed
  arrangements; large graphs stay hybrid (SW miss → remote).
- jco-transpiled Preview-2 components + the kotoba host shims add a JS build step and a
  size cost; guests must stay within the edge budget.
- CACAO signature verification in wasm (ed25519-dalek is wasm-clean; verify the
  `kotoba-crypto` dep set has no native-only transitive deps).

# Alternatives Considered

- **Keep browser as cache only (status quo)** — rejected: leaves reads dependent on a
  remote server, violates the edge-first posture.
- **Port wasmtime into the browser** — infeasible (wasmtime does not target wasm32);
  the browser's own engine + jco is the correct path.
- **Reimplement a second, browser-only guest ABI** — rejected: forks the guest contract.
  D4 keeps a single component artifact.
- **DuckDB-WASM / SQLite-WASM local mirror** — rejected: violates the substrate boundary
  (no SQL projection; the canonical state is the Datom log).

# References

- ADR-2606013200 — yoro kotoba feed read-path migration (the reader this serves)
- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605262130 — kotoba storage substrate unification
- ADR-2605241900 — baien edge-target invariant (WASM-32 / iPhone 12+ / Android 4 GB)
- ADR-2606012100 — donation-funded operation + compute-node donation (ameno class)
- ADR-2605215000 — Murakumo-only inference (no inference in the storage node)
- `40-engine/kotoba/crates/kotoba-store-web` — existing `IdbBlockStore`
- `40-engine/kotoba/crates/kotoba-runtime/{host,executor}.rs` + `wit/world.wit` — guest host ABI
- `40-engine/kotoba/crates/kotoba-vm/src/wasm_pregel.rs` — pure-Rust BSP orchestrator
