---
id: adr-2605302355-kotoba-langgraph-llm-inference-live-verified-and-durable-murakumo-routing
title: "ADR-2605302355: kotoba LangGraph actor LLM inference — live end-to-end verification, three runtime fixes, macOS Local Network Privacy root-cause, and durable Murakumo LiteLLM-loopback routing (session closure)"
status: active
doc_type: adr
topic: kotoba-actor-llm-inference-verification
authoritative: true
last_verified: 2026-05-30
priority: 6.0
axis: operations
weight: 0.6
priority_note: "Session-closure ADR for the 2026-05-30 investigation 'kotoba で langgraph actor は llm 推論なども行なっている? 動いている?'. Establishes empirically (against the live :8077 node) that a Python LangGraph actor runs in-WASM AND performs LLM inference end-to-end, after fixing three runtime defects and discovering the real production blocker: macOS Local Network Privacy (TCC) silently denies the launchd-spawned kotoba daemon access to the LAN inference node. Records the durable fix — route inference through the loopback Murakumo LiteLLM gateway (127.0.0.1:4000), which is TCC-exempt and holds the LAN access. Corrects the over-stated 'verified on prod :8077' claim in ADR-2605301625."
authoritative_for:
  - empirical status of kotoba LangGraph (Python) actors performing LLM inference on the live node
  - the three kotoba runtime fixes (invoke_run Result, HttpInferEngine runtime/client, langgraph example imports) + the bearer-key addition
  - the macOS Local Network Privacy (TCC) constraint on launchd-spawned kotoba reaching LAN inference nodes, and the loopback-gateway mitigation
  - the canonical inference routing for the local deployment: kotoba -> 127.0.0.1:4000 (Murakumo LiteLLM) -> gemma4-e4b
depends_on:
  - ADR-2605301625 (kotoba actor deploy + wasmtime 25 + Murakumo inference)
  - ADR-2605262130 (kotoba storage substrate unification)
  - ADR-2605215000 (Murakumo-only inference — LiteLLM 127.0.0.1:4000 SSoT)
  - ADR-2605292100 (kotoba v0.1.0 tag + Homebrew tap)
  - ADR-2605301030 (kotoba KG storage session — operator runbook)
related:
  - ADR-2605291100 (manimani kotoba-native — StateGraph + Murakumo)
  - ADR-2605250002 (kotoba StateGraph / LangGraph API)
supersedes: []
superseded_by: []
notes: |
  kotoba submodule fixes shipped on branch fix/wasm-runtime-build-json-macro
  (github.com/etzhayyim/kotoba): a53457e (invoke_run + HttpInferEngine +
  example imports) and 5f9d14c (KOTOBA_INFERENCE_API_KEY bearer support).
  Parent pointer bumps: c1d83789c, 89953d523.
---

# ADR-2605302355: kotoba LangGraph actor LLM inference — live verification + durable Murakumo routing

**Status**: active
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki

# Context

Session question: *"kotoba で langgraph actor は llm 推論なども行なっている?
動いている?"* (Do kotoba LangGraph actors actually run and perform LLM
inference?) ADR-2605301625 claimed this was "✅ verified on prod :8077", but
the claim was tested empirically against the running launchd node and did
**not** reproduce. The investigation drove the path to a genuine working
state and uncovered four issues — three code defects and one OS-level
constraint.

1. **`--features wasm-runtime` did not build.** `invoke_run`
   (`crates/kotoba-server/src/xrpc.rs`) had two graph-snapshot error paths
   returning a bare `.into_response()` (an `axum::Response`) where the
   function returns `Result<impl IntoResponse, (StatusCode, String)>`. The
   default (`http-inference`) build skips this code, so the regression was
   invisible until a `wasm-runtime` rebuild.

2. **The deployed binary lacked the extended-const fix.** The first live
   test of the Python LangGraph component failed with
   `CompileFailed(... non-constant operator: i32.add)` — the exact
   extended-const error ADR-2605301625 PR#4 (wasmtime 22→25) claimed to fix.
   `KotobaEngine::new()` (`host.rs`) sets `wasm_extended_const(true)`, but
   the running binary predated it. A clean wasmtime-25 + `wasm-runtime`
   rebuild resolved it; **aria_kotoba.wasm then ran in-WASM** (gas=15, real
   output) — proving Python LangGraph actors execute on the live node.

3. **The LLM-calling example trapped on un-bundled imports.** `agent.wasm`
   (the chatbot using `KotobaLLM`) trapped at call time because
   componentize-py static analysis does not follow the lazy
   `from kotoba_langgraph._cbor import ...` / `from wit_world.imports import
   llm` imports inside SDK function bodies. Hoisting those imports to module
   scope (mirroring `aria_kotoba.py`) and rebuilding fixed it — the
   LangGraph graph then reached the `chatbot` node and invoked
   `kotoba:kais/llm.infer` (gas jumped to 1005).

4. **`HttpInferEngine` failed to send, then the LAN was unreachable.** With
   the WIT path live, the host inference call first failed instantly
   ("error sending request") because the `reqwest::Client` was built at
   startup (main runtime) but invoked from the WASM execution thread's
   runtime — a reqwest client is bound to the reactor that built it.
   Rewriting `generate()` to run on a dedicated OS thread with its own
   current-thread runtime and a fresh per-call client (plus connect/timeout
   diagnostics) made the request actually go out — and revealed the real
   blocker:

   ```
   ConnectError("tcp connect error", 192.168.1.18:11434,
     Os { code: 65, kind: HostUnreachable, message: "No route to host" })
   ```

   **macOS Local Network Privacy (TCC).** The launchd-spawned `kotoba`
   daemon is denied access to the LAN inference node (`192.168.1.18`), even
   though `curl` from a permitted context (Terminal) reaches it. launchd
   background daemons do not inherit local-network permission, so direct LAN
   inference from the daemon is silently blocked.

# Decision

## 1. Confirmed status (empirical, live `:8077`)

- **Python LangGraph actors run in-WASM** on the live kotoba node
  (`aria_kotoba.wasm`: status ok, gas 15, byte-real output).
- **They perform LLM inference end-to-end**: `agent.wasm` →
  `KotobaLLM` → `kotoba:kais/llm.infer` → host → Murakumo `gemma4-e4b` →
  returns `"4"` (status ok, gas 1015), reproduced after the durable routing
  fix below.

## 2. Three runtime fixes + bearer-key (shipped to etzhayyim/kotoba)

| Fix | File | Commit |
|---|---|---|
| `invoke_run` error paths return `Err((StatusCode, String))` | `kotoba-server/src/xrpc.rs` | a53457e |
| `HttpInferEngine` dedicated-runtime + fresh per-call client + diagnostics | `kotoba-llm/src/http_infer.rs` | a53457e |
| LangGraph example: hoist lazy `_cbor`/`_entry`/`wit_world.imports.llm` imports; rebuild `agent.wasm` | `examples/kotoba-langgraph-hello/agent.py` | a53457e |
| `KOTOBA_INFERENCE_API_KEY` optional bearer for OpenAI-compatible gateways | `kotoba-llm/src/http_infer.rs` | 5f9d14c |

Branch `fix/wasm-runtime-build-json-macro`; parent pointer bumps
`c1d83789c`, `89953d523`.

## 3. Durable inference routing — Murakumo LiteLLM loopback (CANONICAL local)

Route kotoba inference through the **loopback Murakumo LiteLLM gateway**, not
a direct LAN address. Loopback (`127.0.0.1`) is exempt from macOS Local
Network Privacy; the LiteLLM gateway (its own launchd service,
`com.etzhayyim.litellm.jacob`) holds the LAN access and load-balances across nodes.
This is also the ADR-2605215000 SSoT (LiteLLM `127.0.0.1:4000`), so it is
architecture-correct, not a workaround.

`com.etzhayyim.kotoba` launchd env (local, secrets uncommitted):

- `KOTOBA_INFERENCE_URL = http://127.0.0.1:4000`
- `KOTOBA_INFERENCE_MODEL = gemma4-e4b`  (LiteLLM alias for `ollama/gemma4:e4b`)
- `KOTOBA_INFERENCE_API_KEY = <LiteLLM master key>`  (kept only in the local plist; never committed)

Session-independent: survives daemon restarts; no session-bound forwarder.

# Consequences

- The kotoba LangGraph + LLM story is now **true and reproducible** on the
  live node, with the fixes upstreamed.
- **ADR-2605301625's "✅ verified on prod :8077" is corrected**: that wave
  did not build/run on the launchd daemon as-claimed; this ADR records the
  fixes and the OS constraint that made the difference.
- A new operator invariant: **launchd-spawned kotoba cannot reach LAN
  inference nodes directly** (macOS TCC). Always route inference via a
  loopback gateway (Murakumo LiteLLM `127.0.0.1:4000`). Setting
  `KOTOBA_INFERENCE_URL` to a `192.168.x`/LAN address under launchd will fail
  with "No route to host".
- `HttpInferEngine` is now robust to the WASM execution thread context and
  supports authenticated gateways.

# Alternatives Considered

1. **Grant the launchd kotoba local-network (TCC) permission.** Rejected as
   primary: TCC for headless launchd daemons is unreliable and does not
   persist cleanly; loopback-gateway routing is deterministic.
2. **Durable loopback→LAN forwarder as a launchd service.** Rejected: a
   launchd forwarder hits the same TCC block; only a process in a permitted
   context can reach the LAN.
3. **Keep direct LAN address + a session forwarder.** Rejected: session-bound
   (dies with the shell); not durable.
4. **Point at the LiteLLM gateway (chosen).** Architecture-correct
   (ADR-2605215000), durable, loopback-TCC-exempt; required only a small
   bearer-key addition to `HttpInferEngine`.

# References

- `/90-docs/adr/2605301625-kotoba-actor-deploy-wasmtime25-murakumo-live.md` — corrected by this ADR
- `/90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — LiteLLM 127.0.0.1:4000 SSoT
- `/90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — kotoba substrate
- `/90-docs/adr/2605301030-kotoba-kg-storage-session-52-entity-actor-graph.md` — kotoba operator runbook
- `40-engine/kotoba` @ `fix/wasm-runtime-build-json-macro` (a53457e, 5f9d14c)
- `~/Library/LaunchAgents/com.etzhayyim.kotoba.plist` — local inference routing (secrets uncommitted)
- `~/litellm.yaml` + `~/Library/LaunchAgents/com.etzhayyim.litellm.jacob.plist` — Murakumo LiteLLM gateway (gemma4-e4b alias)
