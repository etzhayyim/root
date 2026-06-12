---
id: adr-2605263701-baien-ameno-onnx-graph-layer-replacement-r1b
renumbered_from: "2605263700"
title: "Baien ameno ONNX graph layer-replacement R1b — transformers.js MatMul → BitLinear interceptor + end-to-end token gen"
status: proposed
doc_type: adr
topic: baien-ameno-onnx-graph-layer-replacement
authoritative: true
last_verified: 2026-05-26
priority: 5.0
axis: architecture
weight: 0.60
priority_note: "First R-step that produces user-observable behaviour change. R0 + R1a are scaffold + harness; R1b is when baien-bitnet-2b in ameno actually loads, runs, and emits tokens through our BitLinear kernel instead of through transformers.js's generic fp16 MatMul. The 3.4 GB iPhone-12 load-peak that's been silently violating ADR-2605241900 §G1 since 2026-05-09 closes here."
authoritative_for:
  - choice of interception layer (model-graph patch vs ORT custom op vs pipeline wrapper)
  - the BitNet-specific subgraph pattern to match + replace
  - load-time ONNX rewrite policy (in-browser vs offline)
  - the `dispatchBitLinearForward` end-to-end signature (R1b finalises)
  - first end-to-end microbench shape (which prompt set, which device class)
  - failure mode taxonomy + fallback ladder when BitLinear dispatch errors mid-token
depends_on:
  - adr-2605263400-baien-ameno-wgsl-bitlinear-numeric-test-r1a
  - adr-2605263300-baien-ameno-per-kernel-inference-r0
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605252100-ameno-webnn-inference-fast-path
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - 20-actors/ameno/src/inference.ts
  - 20-actors/ameno/src/inference/kernels/dispatch.ts
  - 20-actors/ameno/src/inference/bitnet-bridge.ts
  - 40-engine/baien-wasm-ternary/shaders/bitlinear_forward.wgsl
  - https://github.com/huggingface/transformers.js
  - https://github.com/microsoft/onnxruntime/tree/main/js/web
supersedes: []
superseded_by: []
---

# ADR-2605263701: Baien ameno ONNX graph layer-replacement R1b — transformers.js MatMul → BitLinear interceptor + end-to-end token gen

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

R0 (ADR-2605263300) shipped the BitLinear kernel surfaces (WGSL + Rust
WASM) and pinned the bitnet.cpp public-API mirror. R1a
(ADR-2605263400) shipped the isolated wgpu test harness that verifies
the WGSL kernel matches the Rust scalar reference matmul to ±1 ULP
fp16 on synthetic data.

Neither R0 nor R1a touches the production token-generation path. The
HF `onnx-community/bitnet-b1.58-2B-4T-bf16-ONNX` model — loaded by
`AutoModelForCausalLM.from_pretrained` in `inference.ts:191` — runs
through transformers.js → ONNX Runtime Web with the default
WebGPU/WASM EP. Every `MatMul` node in the BitNet ONNX graph
allocates an fp16 dense weight tensor (because ORT-Web dequantizes
the i2_s blob at model load). On iPhone 12 this **pushes peak load
to ~3.4 GB** — a silent G1 violation of the ADR-2605241900 edge
invariant (≤2 GB @ 4 k context) that has been open since baien
landed in ameno.

R1b is the work that finally activates the BitLinear kernel inside
the real BitNet model. The challenge: transformers.js does not
expose a graph-level "replace this op with that op" hook. We have
five candidate interception layers, each with a different cost/
risk profile:

| Layer | What we patch | Pros | Cons |
|---|---|---|---|
| **(A) Offline ONNX rewrite** | Run a Python tool on the HF model once, replace `MatMul` with `Custom(BitLinear)` ops. Ship the patched model. | Browser sees clean graph; no runtime patching | Need to host a fork of the HF model — license OK (MIT) but we now own a forked artifact in B2 / IPFS; users can't auto-update by bumping transformers.js |
| **(B) In-browser ONNX rewrite** | Load the original .onnx blob, run a JS-side `protobufjs` patcher, hand the patched buffer to ORT-Web. | No forked model; pure runtime | Adds 60-100 KB protobuf parser + ~50 ms patch time at every load |
| **(C) ORT-Web custom op (WASM EP only)** | Register a `BitLinear` JS-side custom op; rewrite graph to call it. | First-class ORT-Web feature | WebGPU EP does NOT support JS custom ops as of ORT-Web 1.20 — this path stays WASM-bound, defeating R0's webgpu-bitlinear backend |
| **(D) transformers.js model.forward override** | Subclass `BitNetModel`, override the forward to call our dispatch directly. | Bypasses ORT-Web entirely; cleanest | We write the whole BitNet runtime ourselves — RoPE, attention, KV-cache, sampler. Estimated 1500 LoC; high regression risk |
| **(E) ORT-Web pre-execution graph hook** | Hook `OrtCreateSession` to mutate the graph before kernels are bound. | Closest to "drop-in" | Not a public API surface; we'd patch ORT-Web — brittle across versions |

After review, **(B) in-browser ONNX rewrite + (D)
forward-override-for-the-decode-loop hybrid** is the path R1b takes.
Rationale:

1. **(B) for the encode/prefill matmuls** — works against ORT-Web's
   WebGPU and WASM EPs uniformly (the patched op is still inside the
   ONNX graph, ORT-Web just sees a custom-op node and calls our
   handler).
2. **(D) for the decode-step matmul** — once we control the forward
   loop, we can avoid re-traversing the ORT graph for every token
   and call BitLinear directly with the previous step's hidden state.
   This is where the throughput win lives.

This hybrid keeps the bulk of transformers.js intact (tokenizer,
attention KV-cache, sampler) while replacing only the
performance-critical matmul path.

## What R1b is NOT

- **Not a from-scratch BitNet runtime.** We keep transformers.js as
  the host for tokenisation, KV-cache, RoPE, sampler, attention.
  We only replace the FFN+QKV matmul calls.
- **Not a forked HF model.** No new artifact in B2 / IPFS;
  rewrite happens at load time in the browser.
- **Not encoder kernels.** SigLIP / Whisper-tiny / YAMNet remain
  out of scope; R2 owns them.
- **Not WebNN.** WebNN BitLinear EP is R3.
- **Not training.** Forward only. ADR-2605242630 owns LoRA training.

# Scope

In scope (R1b — this ADR):

- A Python offline tool at
  `70-tools/baien-onnx-bitnet-tools/{patch_graph.py, verify_patched.py}`
  for **inspecting** the HF ONNX graph (decide which `MatMul`
  nodes to replace), with **no runtime artefact**. This is for
  R1b development only.
- An in-browser ONNX patcher at
  `20-actors/ameno/src/inference/bitnet-graph-patcher.ts` that:
  - Loads the model's `.onnx` blob (via the same fetch path
    transformers.js uses).
  - Parses the protobuf with a minimal subset of the `onnx`
    proto schema (we don't need full type-checking, just
    `node.op_type`, `node.attribute`, and the tensor i/o lists).
  - Walks the graph; for each `MatMul` node whose first input is
    one of the BitNet trunk's weight tensors, replaces it with a
    `Custom(BitLinear)` node.
  - Hands the patched bytes to ORT-Web's `InferenceSession.create`.
- An ORT-Web custom-op registration at
  `20-actors/ameno/src/inference/bitnet-custom-op.ts` that:
  - Implements the `BitLinear` op's JS handler — receives
    `(W_ref, X, W_scale, X_scale)` tensors, dispatches to our
    WebGPU shader OR WASM kernel via `probeBitnetBackend()`,
    writes the f16 output tensor back to ORT-Web.
- A `BitNetForwardOverride` class at
  `20-actors/ameno/src/inference/bitnet-forward.ts` that wraps
  transformers.js's `AutoModelForCausalLM` instance and overrides
  the decode-step forward path (encode/prefill stays on ORT-Web's
  custom-op pathway).
- Wiring in `inference.ts`:
  - `MODELS["baien-bitnet-2b"]` gains a `useBitLinearBridge: true`
    flag.
  - `loadModel(...)` reads the flag and routes through the
    R1b path when true.
  - `generate(...)` calls into `BitNetForwardOverride` for the
    decode loop instead of `model.generate`.
- A real-model microbench at
  `20-actors/ameno/src/inference/kernels/bench/baien-microbench.ts`:
  - Loads the 15-prompt verifiable set from
    `70-tools/scripts/bench/baien-microbench/` (already exists per
    ADR-2605092350).
  - Runs first-token latency + decode tokens-per-second on each
    backend (`webgpu-bitlinear`, `wasm-ternary-simd`,
    `wasm-ternary-scalar`, `fp16-fallback`).
  - Emits an NDJSON manifest to
    `90-docs/baien/wgpu-bitlinear-microbench-26XXNNNN.jsonl`.
- Memory-budget verification:
  - Document peak heap at model-load + at 1 k context + at 4 k
    context, measured via `performance.memory` (Chromium) on
    each backend.
  - Fail loudly if any backend exceeds ADR-2605241900 §G1 (2 GB
    @ 4 k, 2.5 GB @ 16 k).

Out of scope (lands in subsequent ADRs):

- **R1c — v128 SIMD inner loop + LUT-expanded matmul +
  wasm-bindgen pointer marshalling.** Pure performance; R1b
  shows correctness on the scalar WASM path.
- **R2 — Encoder kernels (SigLIP / Whisper-tiny / YAMNet).**
- **R3 — WebNN BitLinear EP** (NPU via ORT-Web custom op +
  WebNN backend).
- **R4 — q8 KV-cache** for 16 k context.
- **Real-device matrix microbench.** R1b ships the harness; the
  actual iPhone 12 / Pixel 6 / M1 / Linux desktop walk-through is
  a separate ADR with run-log artefacts.
- **`baien-server-*` or `baien-XL-*` integration.** R1b is edge-only.

# Decision

## 1. Hybrid harness — in-browser ONNX rewrite + forward override

```
ameno appview
     │
     ├── transformers.js (tokenizer + KV-cache + sampler) ──────────┐
     │                                                              │
     ├── bitnet-graph-patcher.ts (R1b)                               │
     │     parse .onnx → walk graph → rewrite MatMul → ORT bytes ───┤
     │                                                              │
     ├── ORT-Web Inference Session (encode/prefill)                  │
     │     with custom op `BitLinear` registered ───────────────────┤
     │                                                              │
     ├── BitNetForwardOverride (R1b)                                 │
     │     decode step → directly call probeBitnetBackend's dispatch ┤
     │     skip ORT graph traversal for matmul                      │
     │                                                              │
     ├── kernels/dispatch.ts → backend ────────────────────────────┐│
     │                                                             ││
     ├── kernels/bitlinear-forward.ts dispatchBitLinearForward ────┤│
     │     uses WGSL_BITLINEAR_FORWARD (shaders/.wgsl)             ││
     │                                                             ││
     └── bitnet-bridge.ts                                           ││
           BitnetWasmModule.ggmlBitnetMulMatTaskCompute            ─┘│
           (loads 40-engine/baien-wasm-ternary.wasm)                 │
                                                                     │
                                                                     ▼
                                                          (R1c v128 SIMD lands here)
```

## 2. ONNX graph patch (encode/prefill path)

```ts
// 20-actors/ameno/src/inference/bitnet-graph-patcher.ts (R1b sketch)

import { decode as onnxDecode, encode as onnxEncode } from "./onnx-proto-min";

interface BitNetWeightHint {
  /** Tensor name in the ONNX graph (e.g. "model.layers.0.self_attn.q_proj.weight"). */
  readonly tensorName: string;
  /** Layer index for telemetry. */
  readonly layerIdx: number;
}

export interface PatchResult {
  /** Patched ONNX bytes ready for ORT-Web. */
  readonly bytes: Uint8Array;
  /** Diagnostic: how many MatMul nodes we replaced. */
  readonly replacedCount: number;
  /** Diagnostic: names of replaced tensors. */
  readonly replacedTensors: string[];
}

export function patchBitNetGraph(originalBytes: Uint8Array): PatchResult {
  const model = onnxDecode(originalBytes);
  const replacedTensors: string[] = [];

  for (const node of model.graph.nodes) {
    if (node.opType !== "MatMul") continue;
    // node.inputs[1] is the weight tensor for transformers.js's
    // BitNet ONNX export — verify with the heuristic below before
    // rewriting (false positives on attention QKT matmuls would
    // break the decode).
    if (!isBitNetTrunkWeight(node.inputs[1], model)) continue;

    node.opType = "BitLinear";  // custom op name we register
    node.domain = "etzhayyim.ai";
    replacedTensors.push(node.inputs[1]);
  }

  if (!model.opsetImports.find(o => o.domain === "etzhayyim.ai")) {
    model.opsetImports.push({ domain: "etzhayyim.ai", version: 1 });
  }

  return {
    bytes: onnxEncode(model),
    replacedCount: replacedTensors.length,
    replacedTensors,
  };
}

function isBitNetTrunkWeight(tensorName: string, model: OnnxModel): boolean {
  // Replace ONLY weights that are:
  //   - Constants (initializers, not produced by other nodes)
  //   - i2_s packed (the HF model ships them as int8-typed tensors
  //     with packed values; the export tooling decided that for us)
  //   - Named matching the trunk's q_proj/k_proj/v_proj/o_proj/
  //     gate_proj/up_proj/down_proj pattern (NOT attention QK^T,
  //     which is a runtime matmul on activations).
  return BITNET_TRUNK_PROJ_PATTERN.test(tensorName);
}

const BITNET_TRUNK_PROJ_PATTERN =
  /\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)\.weight$/;
```

The full protobuf schema is large; we only need the subset that
covers `ModelProto`, `GraphProto`, `NodeProto`, `TensorProto`. The
`onnx-proto-min` module is ~400 LoC of hand-written
encoders/decoders for those four messages — much smaller than
pulling in `protobufjs` (~150 KB).

## 3. ORT-Web custom op

```ts
// 20-actors/ameno/src/inference/bitnet-custom-op.ts (R1b sketch)

import * as ort from "onnxruntime-web";
import { dispatchBitLinearForward } from "./kernels/bitlinear-forward";

export function registerBitLinearCustomOp(env: typeof ort.env): void {
  env.experimental.customOps = env.experimental.customOps ?? {};
  env.experimental.customOps["etzhayyim.ai::BitLinear"] = {
    compute(inputs, attributes) {
      const [w_packed, x_q8, w_scale, x_scale] = inputs;
      // dispatchBitLinearForward picks backend per probeBitnetBackend
      // ladder. Throws on R0 wired stubs; R1b makes it real.
      return dispatchBitLinearForward({
        w_packed, x_q8, w_scale, x_scale,
        layerHint: attributes.layerIdx as number | undefined,
      });
    },
  };
}
```

ORT-Web's `experimental.customOps` is the public-but-marked-experimental
extension point. Stability across ORT-Web versions is a known risk
(see "Risks" §below).

## 4. Decode-step forward override

```ts
// 20-actors/ameno/src/inference/bitnet-forward.ts (R1b sketch)

export class BitNetForwardOverride {
  private readonly session: ort.InferenceSession;
  private readonly model: PreTrainedModel;

  // Per-layer KV-cache stays in transformers.js's wrapper; we only
  // intercept the matmul of the new token's hidden state.
  async decodeStep(
    hidden: Float16Array,
    layerIdx: number,
    projKind: "q" | "k" | "v" | "o" | "gate" | "up" | "down",
  ): Promise<Float16Array> {
    // ... look up the cached W_packed for (layerIdx, projKind) ...
    return await dispatchBitLinearForward({ w_packed, x_q8, ... });
  }
}
```

This bypasses ORT's session.run for the decode-step matmuls. The
prefill (which has more parallelism) keeps using the patched ORT
graph; the decode (which is bandwidth-bound) takes the direct path.

## 5. Failure mode ladder

```
dispatchBitLinearForward throws → caught by custom-op compute
  → log telemetry with (layerIdx, backend, errorMessage)
  → fall back to fp16 dense dequant via WGSL_BITNET_PACKED_DEQUANT
       (write a fp16 weight tile to a temp buffer, run ORT-Web's
        built-in fp16 MatMul on it)
  → if fallback also throws → catastrophic abort, surface as
       generation error; UI shows "BitLinear unavailable;
       reload to retry"
```

Critical invariant: a failed BitLinear dispatch must NOT silently
produce garbage tokens. Either the fallback runs (correct output,
worse RAM) or generation aborts (loud failure). Gate G9 from R0
(no silent fp16 fallback) is upgraded to "no silent fp16 fallback
**WITHOUT TELEMETRY**" — fallback is allowed but must emit a
telemetry record.

## 6. Microbench shape

15 prompts × 4 backends × 3 device classes (M1 / Pixel 6 / iPhone
12) = 180 runs. Each run measures:

- Load time (network excluded; just model parse + ORT setup).
- Peak heap during load.
- First-token latency.
- Tokens / second for the next 256 tokens.
- Peak heap during decode.

Output NDJSON to
`90-docs/baien/wgpu-bitlinear-microbench-260X.jsonl`. Pass criteria:

- All four backends produce **functionally identical token streams**
  on the prompt set (allowing for fp16 rounding non-determinism but
  not divergent tokens beyond position 5).
- `webgpu-bitlinear` peak heap on iPhone 12 ≤ 2 GB at 4 k context
  (the gate G1 we're closing).
- `webgpu-bitlinear` first-token latency on M1 ≤ 1.5 × `fp16-fallback`
  (proves we're not catastrophically slower; performance is R1c).

## 7. New gates added by R1b

- **R1b-G1**: ONNX graph patcher MUST verify replaced node count
  matches expectation (~7 projection layers × N transformer blocks
  = 7N). Mismatch = abort load; do not silently fall back to
  fp16-fallback because that hides the bug.
- **R1b-G2**: BitLinear custom op MUST validate input tensor
  shapes against `Params` struct before dispatch. Shape mismatch
  = throw, do not corrupt memory.
- **R1b-G3**: Telemetry emit on every fallback. `(layerIdx, backend,
  errorMessage, fallbackKind)` to a session-scoped ring buffer; UI
  shows aggregate when generation completes.
- **R1b-G4**: Microbench manifest MUST include device class
  (iOS-Safari / Android-Chrome / macOS-Chrome / Linux-Firefox /
  Windows-Edge) + adapter info + commit SHA. Reproducibility hook
  per ADR-2605262100 G15 pattern.

## 8. Inherited gates (verified at R1b)

- **G1** (edge invariant): the microbench (§6) closes this; pre-R1b
  it was silently violated.
- **G4** (scalar reference contract): every backend's output is
  compared against the Rust scalar reference matmul's f16 result
  during the smoke part of the microbench.
- **G9** (no silent fp16 fallback): upgraded with telemetry per
  §5.
- **G14** (zero behaviour change): NO LONGER APPLIES. R1b is the
  step where behaviour change happens. Users with
  `MODELS["baien-bitnet-2b"].useBitLinearBridge = true` get the
  new path; users with the flag false stay on legacy fp16-fallback.

## 9. R1b deliverables (across the R1b commit chain)

This ADR scopes R1b; the implementation lands across multiple
commits over multiple loop cycles. Estimated commit chain:

1. ONNX proto-min decoder/encoder (`onnx-proto-min.ts`).
2. `bitnet-graph-patcher.ts` + unit tests against a minimal fixture.
3. `bitnet-custom-op.ts` + ORT-Web wiring.
4. `bitnet-forward.ts` decode override + transformers.js integration.
5. `inference.ts` flag-gating + `useBitLinearBridge` wiring.
6. Microbench harness + first M1 run-log emit.
7. iPhone 12 + Pixel 6 run-log emits (real-device validation).
8. Memory-budget verification + G1 close attestation.

# Consequences

**Positive**

- Closes the silent G1 violation that has been open since
  baien-bitnet-2b landed in ameno (2026-05-09).
- First user-observable effect of the per-kernel inference work.
- The graph patcher + custom op pattern is reusable for R2 encoder
  kernels (SigLIP / Whisper-tiny custom ops register the same way).
- The forward-override pattern is reusable for R4 q8 KV-cache
  (intercept the KV-store at the same hook point).

**Negative / costs**

- ORT-Web's `experimental.customOps` API is marked experimental;
  ORT-Web minor-version bumps can break it. We pin the ORT-Web
  version in package.json and treat upgrades as deliberate
  events (each upgrade re-runs the microbench).
- transformers.js has no formal "decode override" extension point;
  we depend on its `AutoModelForCausalLM` API shape. Same pinning
  strategy.
- The ONNX proto-min module (~400 LoC of protobuf encoders) is
  surface area we own. Documentation has to spell out exactly
  which proto fields we read.
- Estimated 1500-2000 LoC across the R1b commit chain; this is
  a multi-week R-step.

**Reversibility**

- Per-model. Setting
  `MODELS["baien-bitnet-2b"].useBitLinearBridge = false` reverts
  to the R0 fp16-fallback path. Other models (Gemma 4 E2B/E4B)
  are unaffected because the bridge flag is per-model.

# Alternatives Considered

1. **(A) Offline ONNX rewrite + forked HF model.** Rejected
   because we'd own a forked model artefact (license OK but
   provenance/versioning surface area). In-browser rewrite at
   (B) is the same engineering for half the operational burden.

2. **(C) ORT-Web custom op WASM EP only.** Rejected because it
   throws away the webgpu-bitlinear backend (the highest-tier
   path in R0's selection ladder). webgpu-bitlinear has the
   biggest throughput delta on M1 / Pixel 6 (devices with real
   WebGPU adapters).

3. **(D) Full transformers.js model.forward override (no ORT
   graph).** Rejected for R1b because writing the entire BitNet
   runtime from scratch is ~1500 LoC of forward code (attention,
   RoPE, KV-cache, sampler) that already exists in
   transformers.js. Hybrid is cheaper. (D) gets reconsidered at
   R4 when we own the KV-cache anyway.

4. **(E) Patch ORT-Web itself.** Rejected — non-public API
   surface, brittle across versions, would require shipping our
   own ORT-Web fork. Same operational burden as (A) with worse
   visibility.

5. **Defer R1b, jump to R1c v128 SIMD.** Considered. Rejected
   because R1c improves throughput of a backend that is **not
   reachable from production code** until R1b lands. Sequencing
   R1c-before-R1b would mean weeks of SIMD work optimising a
   code path that no real model has reached yet.

6. **Use llama.cpp's BitNet runtime in WASM (the upstream
   ggml-bitnet-mad.cpp Emscripten port).** Rejected per
   ADR-2605263300 G7 + the CLAUDE.md "no third-party vendored
   code carrying Charter Rider" rule — that would put us in
   `lib/upstream-bitnet/` territory and require maintaining a
   port-of-a-port. Clean-room Rust crate (R0) + our own bridge
   (R1b) keep the surface in religious-corp first-party hands.

# References

- ADR-2605263400 — Baien ameno WGSL BitLinear numeric test R1a (parent)
- ADR-2605263300 — Baien ameno per-kernel inference R0 (grand-parent)
- ADR-2605241900 — Baien edge-target invariant (G1 the silent violation)
- ADR-2605252100 — Ameno WebNN inference fast path R0
- ADR-2605215000 — etzhayyim inference Murakumo-fleet-only
- ADR-2605092350 — Baien 1-bit multimodal edge / browser / CPU design
- transformers.js — https://github.com/huggingface/transformers.js
- ONNX Runtime Web — https://github.com/microsoft/onnxruntime/tree/main/js/web
- onnx-community/bitnet-b1.58-2B-4T-bf16-ONNX (HF model artefact)
- ONNX protobuf schema — https://github.com/onnx/onnx/blob/main/onnx/onnx.proto3
