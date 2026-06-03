/**
 * Hoge AppView — AssemblyScript WASM execution validation worker.
 *
 * Validates four CF Workers WASM patterns:
 *   1. Static import   : WASM compiled at build time (CompiledWasm rule), instantiated per-request.
 *   2. Dynamic eval    : WASM bytes submitted at runtime, compiled via WebAssembly.compile().
 *   3. WIT manual ABI  : shannonScore(len): f64 — ptr/len memory ABI, WIT-shaped TS glue.
 *   4. Extism          : @extism/as-pdk plugin + extism host SDK, no manual memory management.
 *
 * Patterns 3 & 4 both implement the WIT contract:
 *   shannon-score: func(params: string) -> result<string, string>
 *
 * No business-logic SDK dependencies — plain Hono + CF Workers for minimal validation surface.
 */

import { Hono } from "hono";
import { createPlugin } from "extism";

// Pre-compiled AssemblyScript contract (CompiledWasm rule → WebAssembly.Module at bundle time).
// Exports: add, fib, sum, mul (numeric), inputPtr, shannonScore (Pattern A — WIT manual ABI).
import CONTRACT_MODULE from "./contract.wasm";

// Extism plugin WASM — compiled from @extism/as-pdk AS source.
// Exports: shannonScore() — reads via Host.inputString(), writes via Host.outputString().
import EXTISM_MODULE from "./shannon-extism.wasm";

// Pattern C: WIT Component Model (P2) — Rust + cargo component + jco transpile.
// jco transpile generates ESM JS glue + core WASM (no WASI, no manual ABI).
// Core WASM bundled via CompiledWasm rule; instantiate() wires it at runtime.
import JCO_CORE from "./jco-component/shannon-jco.core.wasm";
import { instantiate as jcoInstantiate } from "./jco-component/shannon-jco.js";

const app = new Hono();

// ── Extism plugin singleton ──────────────────────────────────────────────────
// Instantiated once per Worker isolate; reused across requests.
// useWasi: false — CF Workers only supports fd_read/fd_write/proc_exit; skip WASI.
let _extismPlugin: Awaited<ReturnType<typeof createPlugin>> | null = null;
async function getExtismPlugin() {
  if (!_extismPlugin) {
    _extismPlugin = await createPlugin(EXTISM_MODULE, { useWasi: false });
  }
  return _extismPlugin;
}

/** Decode a base64 string to ArrayBuffer. */
function b64ToBuffer(b64: string): ArrayBuffer {
  const bin = atob(b64);
  const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return u8.buffer;
}

// ── Health ──────────────────────────────────────────────────────────────────

app.get("/health", (c) => c.json({ status: "ok", app: "hoge-appview" }));

// ── Pattern 1: Static WASM import ───────────────────────────────────────────
// Validates: CF Workers can instantiate a WebAssembly.Module imported at bundle time.

app.get("/xrpc/com.etzhayyim.apps.hoge.wasmTest", async (c) => {
  const t0 = Date.now();
  const instance = new WebAssembly.Instance(CONTRACT_MODULE, {});
  const exp = instance.exports as {
    add: (a: number, b: number) => number;
    fib: (n: number) => number;
    sum: (n: number) => number;
    mul: (a: number, b: number) => number;
  };
  return c.json({
    pattern: "static-import",
    add_3_4:  exp.add(3, 4),   // 7
    fib_10:   exp.fib(10),     // 55
    sum_100:  exp.sum(100),    // 5050
    mul_6_7:  exp.mul(6, 7),   // 42
    ms: Date.now() - t0,
  });
});

// ── Pattern 2: Dynamic WASM eval ────────────────────────────────────────────
// Validates: CF Workers supports WebAssembly.compile() from user-supplied ArrayBuffer.
// POST body: { wasmBase64: string, fn: string, args?: number[] }

app.post("/xrpc/com.etzhayyim.apps.hoge.wasmEval", async (c) => {
  const body    = await c.req.json<{ wasmBase64: string; fn: string; args?: number[] }>();
  const wasmB64 = body.wasmBase64 ?? "";
  const fnName  = body.fn ?? "";
  const fnArgs  = Array.isArray(body.args) ? body.args : [];

  if (!wasmB64) return c.json({ error: "wasmBase64 required" }, 400);
  if (!fnName)  return c.json({ error: "fn required" }, 400);

  const buf    = b64ToBuffer(wasmB64);
  const t0     = Date.now();
  const module = await WebAssembly.compile(buf);
  const inst   = new WebAssembly.Instance(module, {});
  const fn     = (inst.exports as Record<string, unknown>)[fnName];

  if (typeof fn !== "function") {
    return c.json({
      error:     `export '${fnName}' not found`,
      available: Object.keys(inst.exports),
    }, 404);
  }

  const result = (fn as (...a: number[]) => unknown)(...fnArgs);
  return c.json({ pattern: "dynamic-eval", result, fn: fnName, args: fnArgs, ms: Date.now() - t0 });
});

// ── Pattern 3: WIT-shaped manual ABI ────────────────────────────────────────
//
// WIT contract (design-time, etzhayyim wit-gen as-glue pattern):
//   shannon-score: func(params: string) -> result<string, string>
//
// ABI bridge (what etzhayyim wit-gen as-glue generates):
//   AS exports: inputPtr(): i32, shannonScore(len: i32): f64
//   1. Host encodes text → Uint8Array (UTF-8)
//   2. Host writes bytes to wasm.memory[inputPtr()..len]  (ptr always 0)
//   3. Host calls shannonScore(len) → f64 entropy
//   4. Host wraps: JSON.stringify({ score, len, pattern: "manual" })
//
// No allocations, no GC — compiled with --runtime stub --noExportRuntime.

/**
 * WIT-shaped glue for Shannon entropy via manual memory ABI (Pattern A).
 * Maps WIT: shannon-score(params: string) -> result<string, string>
 */
function shannonManual(text: string): { score: number; len: number; pattern: string } {
  const instance = new WebAssembly.Instance(CONTRACT_MODULE, {});
  const exp = instance.exports as {
    memory:       WebAssembly.Memory;
    inputPtr:     () => number;
    shannonScore: (len: number) => number;
  };

  const encoded = new TextEncoder().encode(text.slice(0, 8192));
  const ptr     = exp.inputPtr(); // always 0 — fixed memory layout
  new Uint8Array(exp.memory.buffer).set(encoded, ptr);
  const score = exp.shannonScore(encoded.length);

  return { score, len: encoded.length, pattern: "manual" };
}

app.get("/xrpc/com.etzhayyim.apps.hoge.witShannonManual", (c) => {
  const text = c.req.query("text") ?? "hello world";
  const t0   = Date.now();
  const result = shannonManual(text);
  return c.json({ ...result, ms: Date.now() - t0 });
});

app.post("/xrpc/com.etzhayyim.apps.hoge.witShannonManual", async (c) => {
  const body   = await c.req.json<{ text?: string }>().catch((error) => {
    console.warn("[silent-fail] hoge/index.ts: witShannonManual body parse failed", error);
    return {};
  });
  const text   = body.text ?? "hello world";
  const t0     = Date.now();
  const result = shannonManual(text);
  return c.json({ ...result, ms: Date.now() - t0 });
});

// ── Pattern 4: Extism ────────────────────────────────────────────────────────
//
// Same WIT contract as Pattern 3, implemented via Extism PDK:
//   AS plugin:  @extism/as-pdk Host.inputString() / Host.outputString()
//   TS host:    extism createPlugin(EXTISM_MODULE, { useWasi: false })
//
// Advantage over Pattern 3: zero manual memory management.
// EXTISM_MODULE is a pre-compiled WebAssembly.Module (CompiledWasm rule).
//
// CF Workers constraint satisfied: useWasi: false skips all WASI syscalls.
// Extism host functions (extism:host/env.*) are provided internally by the SDK.

app.get("/xrpc/com.etzhayyim.apps.hoge.witShannonExtism", async (c) => {
  const text   = c.req.query("text") ?? "hello world";
  const t0     = Date.now();
  const plugin = await getExtismPlugin();
  const raw    = await plugin.call("shannonScore", text);
  const result = JSON.parse(new TextDecoder().decode(raw.buffer)) as {
    score: number; len: number; pattern: string;
  };
  return c.json({ ...result, ms: Date.now() - t0 });
});

app.post("/xrpc/com.etzhayyim.apps.hoge.witShannonExtism", async (c) => {
  const body   = await c.req.json<{ text?: string }>().catch((error) => {
    console.warn("[silent-fail] hoge/index.ts: witShannonExtism body parse failed", error);
    return {};
  });
  const text   = body.text ?? "hello world";
  const t0     = Date.now();
  const plugin = await getExtismPlugin();
  const raw    = await plugin.call("shannonScore", text);
  const result = JSON.parse(new TextDecoder().decode(raw.buffer)) as {
    score: number; len: number; pattern: string;
  };
  return c.json({ ...result, ms: Date.now() - t0 });
});

// ── Pattern C: WIT Component Model (jco) ────────────────────────────────────
//
// WIT contract (enforced at compose time by wasm-tools + jco, not just docs):
//   shannon-score: func(params: string) -> result<string, string>
//
// ABI: jco canonical ABI — no manual memory management, no Extism runtime.
//   getCoreModule: (_path) => JCO_CORE  (CompiledWasm WebAssembly.Module)
//   imports: {}  (no WASI, no host imports)
//   exports.compute.shannonScore(text) → JSON string (throws on err)

type JcoRoot = { compute: { shannonScore: (params: string) => string } };
let _jco: JcoRoot | null = null;
/** Singleton per Worker isolate — instantiate Component Model component once. */
async function getJco(): Promise<JcoRoot> {
  if (!_jco) {
    _jco = await jcoInstantiate((_path) => JCO_CORE, {}) as JcoRoot;
  }
  return _jco;
}

app.get("/xrpc/com.etzhayyim.apps.hoge.witShannonJco", async (c) => {
  const text   = c.req.query("text") ?? "hello world";
  const t0     = Date.now();
  const jco    = await getJco();
  const raw    = jco.compute.shannonScore(text);
  const result = JSON.parse(raw) as { score: number; len: number; pattern: string };
  return c.json({ ...result, ms: Date.now() - t0 });
});

app.post("/xrpc/com.etzhayyim.apps.hoge.witShannonJco", async (c) => {
  const body   = await c.req.json<{ text?: string }>().catch((error) => {
    console.warn("[silent-fail] hoge/index.ts: witShannonJco body parse failed", error);
    return {};
  });
  const text   = body.text ?? "hello world";
  const t0     = Date.now();
  const jco    = await getJco();
  const raw    = jco.compute.shannonScore(text);
  const result = JSON.parse(raw) as { score: number; len: number; pattern: string };
  return c.json({ ...result, ms: Date.now() - t0 });
});

// ── Pattern comparison ───────────────────────────────────────────────────────
// Runs the same text through both WASM patterns and compares results.
// GET /xrpc/com.etzhayyim.apps.hoge.witShannonCompare?text=hello+world

app.get("/xrpc/com.etzhayyim.apps.hoge.witShannonCompare", async (c) => {
  const text  = c.req.query("text") ?? "hello world";
  const t0    = Date.now();

  const manual = shannonManual(text);

  const plugin = await getExtismPlugin();
  const raw    = await plugin.call("shannonScore", text);
  const extism = JSON.parse(new TextDecoder().decode(raw.buffer)) as {
    score: number; len: number; pattern: string;
  };

  const delta = Math.abs(manual.score - extism.score);

  return c.json({
    text:   text.slice(0, 80),
    manual,
    extism,
    match:  delta < 1e-10,
    delta,
    ms:     Date.now() - t0,
  });
});

export default app;
