# ADR-2605301625 — kotoba actor deploy (WASM + Python LangGraph) + wasmtime 25 + Murakumo inference live

**Status**: Accepted
**Date**: 2026-05-30
**Owner**: etzhayyim ops

Supersedes/extends: ADR-2605262130 (kotoba storage substrate), ADR-2605215000
(Murakumo-only inference), ADR-2605282400 (kotoba × Murakumo fleet verification),
ADR-2605292100 (kotoba v0.1.0 brew tap).

---

## Context

The existing actors in `20-actors/` needed to actually run on the live kotoba
substrate, exercising both the WASM Component Model path and the Python
LangGraph path, and — for agents that need an LLM — the kotoba → Murakumo
inference wiring (ADR-2605215000). This session set out to deploy an actor end
to end and verify each layer against the running node, rather than assume the
design was wired.

Two latent runtime defects surfaced during verification and were fixed
upstream in `etzhayyim/kotoba`.

## Decision

### What was verified (live, against the running node)

1. **kotoba server `:8077`** is up; `/health` reports all subsystems ready.
   **Datomic compatibility** is provided *inside* kotoba as `kotoba-datomic`
   (17 XRPC endpoints under `com.etzhayyim.apps.kotoba.datomic.*`) — there is no
   separate Cognitect Datomic process. Confirmed correct.

2. **Rust WASM actor** — `examples/kotoba-hello` built for `wasm32-wasip2`,
   deployed via `invoke.run` / `kotoba_wasm_run` (operator-JWT gated), executed
   in-WASM (`gas_used=1030`, real EVM balance fetched).

3. **Python LangGraph actor** — kotodama's **aria** (6-signal parallel ingest +
   Von Neumann minimax) ported to the WASM-native `kotoba_langgraph` API,
   compiled with `componentize-py 0.23` (18 MB component), executed in-WASM on
   the server. Output `area_integral=3.3, eta_global=0.55, minimax=emotion`,
   byte-identical to a host-Python run.

4. **kotoba → Murakumo inference** — a WASM guest calling `kotoba:kais/llm.infer`
   routes through `HostState.inference_engine` → `HttpInferEngine`
   (`KOTOBA_INFERENCE_URL` → LAN Ollama node, model `gemma4:e4b`) and returns
   the model's answer (`"4"` for "What is 2+2?"). Verified on a test node and
   then on production `:8077`.

### Fixes shipped to etzhayyim/kotoba

- **PR #4** (merged, main `c9d0810`): bump `wasmtime 22 → 25`. componentize-py
  ≥0.23 emits extended-const expressions (`i32.add` in WASM global
  initialisers); wasmtime 22 rejected them with `CompileFailed` and exposed no
  `Config` toggle. wasmtime 25 implements extended-const (on by default);
  `config.wasm_extended_const(true)` is set explicitly for intent. This is the
  prerequisite for *any* Python LangGraph agent to load.

- **PR #5** (merged): qualify `serde_json::json!` in `xrpc.rs` so
  `--features wasm-runtime` compiles. The two `json!` calls in the `invoke.run`
  graph-snapshot / graph-head error paths are feature-gated, but `json` was only
  imported inside the test module — so the default (`http-inference`) build
  stayed green while any `wasm-runtime` build broke.

### Production rollout

- Built a `wasmtime-25 + wasm-runtime` release binary, installed to
  `~/.local/bin/kotoba` (old wasmtime-22 binary preserved as
  `kotoba.bak-wasmtime22-*` for rollback).
- launchd plist `com.etzhayyim.kotoba` gained `KOTOBA_INFERENCE_URL` +
  `KOTOBA_INFERENCE_MODEL=gemma4:e4b`; service reloaded under KeepAlive.
- Persistence (`KOTOBA_STORE_PATH` + IPFS pin) preserved across the restart;
  DID stable from Keychain.

### Example actor note

`examples/kotoba-langgraph-hello/aria_kotoba.py` must explicitly
`import kotoba_langgraph._cbor` / `._entry` because `_entry.handle_invoke`
imports `_cbor` lazily inside a function body, which componentize-py's static
module analysis does not follow (otherwise the component compiles but traps at
call time with `ModuleNotFoundError`). A follow-up to hoist that import to
module scope in `_entry.py` is noted on PR #4.

## Consequences

- Python LangGraph and Rust WASM actors are both deployable on the live kotoba
  node; LLM-using agents reach the Murakumo fleet via the constitutional
  Murakumo-only path (ADR-2605215000) with no commercial-GPU route.
- Production `:8077` now runs wasmtime 25 with inference enabled; reversible via
  the preserved backup binary + launchd reload.
- root submodule pointer `40-engine/kotoba` advanced to upstream main including
  PR #4 and #5.

## Verification

| Layer | Result |
|---|---|
| kotoba `/health` (`:8077`) | all subsystems ready; `wasm_executor: ready` |
| Datomic-compat XRPC | 17 endpoints under `com.etzhayyim.apps.kotoba.datomic.*` live |
| Rust WASM actor | ran in-WASM, `gas_used=1030` |
| Python LangGraph aria | ran in-WASM, output == host-Python |
| kotoba → Murakumo `llm.infer` | `gemma4:e4b` → `"4"`, on prod `:8077` |
| `cargo build --features kotoba-server/wasm-runtime` | green |
