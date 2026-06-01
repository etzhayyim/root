---
id: adr-2605263800-baien-ameno-r1b-pivot-forward-override
title: "Baien ameno R1b pivot — ORT-Web custom op dead end; switch to forward-override + weight-pack extraction"
status: accepted
status_note: "Accepted 2026-05-27 after session-close. Forward-override commit chain (cycles 3–16, 14 of 15 commits) landed: onnx-proto-min, bitnet-graph-patcher (deprecated post-pivot but `matchTrunkProjection` predicate retained), bitnet-weight-transformer, bitnet-weight-pack, bitnet-config, bitnet-rope, bitnet-kv-cache (+ per-layer accessors), bitnet-rmsnorm, bitnet-silu, bitnet-math, bitnet-bitlinear-dispatch (fp32-fallback), bitnet-attention (GQA + RoPE + KV cache), bitnet-ffn (SwiGLU), bitnet-transformer (pre-norm block + 2 residuals), bitnet-runtime (decode loop). 154/154 node:test cases pass. End-to-end BitNet decode runs in pure TS with fp32-fallback BitLinear; produces deterministic token sequences on synthetic tiny-config weights. **Remaining work — R1b commit 15**: real-weight load from HF `microsoft/bitnet-b1.58-2B-4T-bf16-ONNX` blob (embedding + 30 layers' BitLinear packs + RMSNorm scales + lm_head) + transformers.js fp16 baseline microbench against the 15-prompt verifiable set from ADR-2605092350 + iPhone-12 G1 close attestation. R1c (v128 SIMD inner loop + LUT-expanded matmul + wgpu/wasm pointer marshalling) remains scoped under ADR-2605263300 R-roadmap §10."
doc_type: adr
topic: baien-ameno-r1b-pivot
authoritative: true
last_verified: 2026-05-27
priority: 5.0
axis: architecture
weight: 0.35
priority_note: "Amends ADR-2605263700 §1/§3 — the (B)+(D) hybrid harness was predicated on ORT-Web exposing a JS-side custom-op registration via `env.experimental.customOps`. Inspection of the bundled `@huggingface/transformers@3.8.1` ORT-Web (no separate npm) finds ZERO references to `customOp`, `registerJsepCustomOp`, or `env.experimental`. The (B) graph-rewrite + (D) forward-override hybrid is therefore reduced to (D)-only — full forward override at the transformers.js model layer."
authoritative_for:
  - "the strategy pivot from (B)+(D) hybrid to (D)-only full forward override"
  - "extracted weight-pack design (`BitLinearWeightPack`) — the side-channel store"
  - "what remains useful from R1b commits 1, 2, 3 after the pivot"
  - "estimated cost adjustment for the full forward override (~3000 LoC, not ~1500)"
depends_on:
  - adr-2605263700-baien-ameno-onnx-graph-layer-replacement-r1b
  - adr-2605263300-baien-ameno-per-kernel-inference-r0
  - adr-2605241900-baien-edge-target-invariant
related:
  - 20-actors/ameno/src/inference/onnx-proto-min.ts
  - 20-actors/ameno/src/inference/bitnet-graph-patcher.ts
  - 20-actors/ameno/src/inference/bitnet-weight-transformer.ts
  - 20-actors/ameno/src/inference/bitnet-weight-pack.ts
  - 20-actors/ameno/src/inference/bitnet-config.ts
  - 20-actors/ameno/src/inference/bitnet-rope.ts
  - 20-actors/ameno/src/inference/bitnet-kv-cache.ts
  - 20-actors/ameno/src/inference/bitnet-rmsnorm.ts
  - 20-actors/ameno/src/inference/bitnet-silu.ts
  - 20-actors/ameno/src/inference/bitnet-math.ts
  - 20-actors/ameno/src/inference/bitnet-bitlinear-dispatch.ts
  - 20-actors/ameno/src/inference/bitnet-attention.ts
  - 20-actors/ameno/src/inference/bitnet-ffn.ts
  - 20-actors/ameno/src/inference/bitnet-transformer.ts
  - 20-actors/ameno/src/inference/bitnet-runtime.ts
supersedes: []
superseded_by: []
---

# ADR-2605263800: Baien ameno R1b pivot — ORT-Web custom op dead end; switch to forward-override + weight-pack extraction

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

ADR-2605263700 R1b §1 picked a **(B)+(D) hybrid harness**:

- **(B)** in-browser ONNX graph rewrite — replace `MatMul` nodes
  matching the BitNet trunk-projection pattern with
  `etzhayyim.ai::BitLinear` custom-op nodes.
- **(D)** transformers.js decode-step forward override — direct
  BitLinear dispatch on the decode hot path.

(B) requires ORT-Web to **execute** the rewritten BitLinear nodes,
which in turn requires ORT-Web to expose a JS-side custom-op
registration mechanism. ADR-2605263700 §3 sketched:

```ts
env.experimental.customOps["etzhayyim.ai::BitLinear"] = { compute(...) };
```

This commit (R1b chain commit 4 in the original plan) attempted to
implement that registration. Inspection of the actual ORT-Web bundled
inside `@huggingface/transformers@3.8.1` finds:

```
$ grep -c "customOp\|registerJsepCustomOp\|env\.experimental" \
  node_modules/@huggingface/transformers/dist/transformers.js
0
```

**Zero references.** The bundled ORT-Web has no public JS API for
registering custom ops. ORT-Web's other custom-op paths
(`customOpLibraryPath` for native .so/.dll loading) are Node-only and
do not apply in browsers either.

This is not a version-pinning bug — the standalone
`onnxruntime-web` npm package (~1.20 as of 2026-05-26) likewise has
no documented public JS custom-op registration. The closest thing is
ORT-Web's "JSEP" (JavaScript Execution Provider) hooks which are an
**internal** API used by the WebGPU EP itself, not exposed to ORT
session consumers.

The (B) leg of the hybrid is therefore dead. R1b commit 2
(`bitnet-graph-patcher`) produces a graph that ORT-Web flatly refuses
to load — `etzhayyim.ai::BitLinear` is an unknown op, session creation
throws.

# Decision

## 1. Strategy pivot — (D)-only full forward override

R1b is reduced to the (D) leg: **bypass ORT-Web entirely for the
BitNet trunk forward pass**. transformers.js's
`AutoModelForCausalLM.from_pretrained` no longer loads the ONNX model
at all; instead we write a pure-TS BitNet runtime that consumes:

```
┌─────────────────────────────────────────────────────────────────┐
│ HF tokenizer JSON          (re-used from transformers.js)        │
│ HF generation_config.json  (re-used from transformers.js)        │
│ BitLinearWeightPack        (extracted from the .onnx blob via    │
│                             our R1b commits 1+2+3 chain)         │
│ BitNet attention / RoPE / KV-cache  (NEW — pure-TS forward path) │
│ sampler                    (re-used from transformers.js)        │
│ kernels/dispatch.ts        (R0 — already shipped)                │
└─────────────────────────────────────────────────────────────────┘
```

The transformers.js dependency stays for tokenization + sampler. The
ONNX runtime dependency is dropped from the baien-bitnet-2b path
entirely (other models like Gemma 4 E2B/E4B keep their ONNX path
unchanged).

## 2. What remains useful from R1b commits 1, 2, 3

- **Commit 1 (`onnx-proto-min.ts`)** — still useful. We need it to
  *read* the original .onnx blob's initializers (BitNet weights live
  inside the ONNX model file even though we won't execute the graph).
- **Commit 2 (`bitnet-graph-patcher.ts`)** — partially useful. The
  `matchTrunkProjection` predicate stays (we use it to enumerate
  which initializers to extract into the weight pack). The
  `patchBitNetGraph` orchestrator becomes dead code — we don't
  rewrite the graph, we just walk it to find the weights to extract.
  Mark as deprecated; remove in a follow-up cleanup commit once the
  forward-override runtime lands.
- **Commit 3 (`bitnet-weight-transformer.ts`)** — fully useful. The
  bf16 → i2_s transform algorithm is still the right way to convert
  HF weights to our kernel format. The orchestrator
  `transformBitNetWeights` becomes "transform and emit to a
  `BitLinearWeightPack`" rather than "transform and rewrite the
  graph."

## 3. New module: `bitnet-weight-pack.ts` (THIS commit lands)

```ts
export interface BitLinearWeightPack {
  /** Stable key matching the original bf16 initializer name. */
  readonly origName: string;
  /** i2_s packed weight bytes — 4 weights / byte, little-endian. */
  readonly packed: Uint8Array;
  /** Per-row fp16 scale, length = rows; encoded as little-endian uint16. */
  readonly scale: Uint8Array;
  /** Shape [rows, cols] of the ORIGINAL weight (cols may not equal packed.cols × 4 due to padding). */
  readonly dims: readonly [number, number];
}

export function extractBitLinearWeightPack(
  modelBytes: Uint8Array,
): {
  /** All extracted packs, keyed by `origName`. */
  packs: ReadonlyMap<string, BitLinearWeightPack>;
  /** Telemetry / verification. */
  countByLayer: ReadonlyMap<number, number>;
};
```

The extractor:

1. Decodes the .onnx blob via `onnx-proto-min`.
2. Walks the graph's initializer list.
3. For each initializer whose name matches
   `BITNET_TRUNK_PROJ_PATTERN`, runs the bf16 → i2_s + f16-scale
   transform from `bitnet-weight-transformer`.
4. Stores the result in a `Map<string, BitLinearWeightPack>` keyed by
   the original bf16 name.

The pack is the **only** thing the forward-override runtime needs
from the ONNX blob. After the pack is built, the .onnx bytes can be
discarded — freeing the ~600 MB bf16 dense weight memory peak that
has been the silent G1 violation since 2026-05-09.

## 4. Cost adjustment

Original ADR-2605263700 §10 estimated ~1500-2000 LoC across 8 commits.
The (D)-only path is more work because we own the forward path:

| Component | Original estimate | Pivoted estimate |
|---|---|---|
| onnx-proto-min | 400 LoC | 530 LoC (shipped) |
| bitnet-graph-patcher | 250 LoC | 210 LoC (shipped; partially defunct) |
| bitnet-weight-transformer | 350 LoC | 410 LoC (shipped) |
| bitnet-weight-pack (NEW) | — | ~200 LoC |
| BitNet attention (NEW) | (existed in transformers.js) | ~400 LoC |
| BitNet RoPE (NEW) | (existed in transformers.js) | ~150 LoC |
| KV-cache (NEW) | (existed in transformers.js) | ~250 LoC |
| Decode loop (NEW) | (existed in transformers.js) | ~200 LoC |
| Sampler (re-used from transformers.js) | 0 LoC | 0 LoC |
| Tests | ~200 LoC | ~500 LoC |
| Microbench harness | ~300 LoC | ~300 LoC |
| **Total** | ~1500-2000 LoC | **~3150 LoC** |

The pivot adds ~1500 LoC of forward-path code that transformers.js
was previously providing. The R1b chain extends from 8 commits to
~12. Each commit remains ~250-500 LoC, the per-cycle scope is unchanged.

## 5. What this commit ships (R1b chain commit 4 in the pivoted plan)

- This ADR amendment (90-docs/adr/2605263800-baien-ameno-r1b-pivot-forward-override.md).
- `20-actors/ameno/src/inference/bitnet-weight-pack.ts` — extractor.
- Tests for the extractor.
- Update to deps.toml + ADR README.

## 6. Subsequent R1b commits (pivoted plan)

- **Commit 5**: `bitnet-config.ts` — reads HF config.json + shape
  inference for hidden_dim / num_layers / num_heads / head_dim.
- **Commit 6**: `bitnet-rope.ts` — RoPE precompute + apply.
- **Commit 7**: `bitnet-kv-cache.ts` — q8-quantizable KV-cache shape
  (q8 quant is R4; R1b ships fp16 cache).
- **Commit 8**: `bitnet-attention.ts` — multi-head attention forward
  using BitLinear for QKV+O projections.
- **Commit 9**: `bitnet-ffn.ts` — gate/up/down BitLinear + SiLU activation.
- **Commit 10**: `bitnet-transformer.ts` — full transformer block.
- **Commit 11**: `bitnet-runtime.ts` — model loop (prefill + decode).
- **Commit 12**: `inference.ts` wiring + microbench + G1 close.

The chain stays per-cycle-tractable; the destination is unchanged
(end-to-end baien-bitnet-2b inference through our kernels with
silent-G1-violation closed).

# Consequences

**Positive**

- Honest about ORT-Web's actual API surface. The R1b ADR's "(B)+(D)
  hybrid" wishful thinking is corrected before it commits us to dead
  code paths.
- The pure-TS forward path gives us full control of the KV-cache
  layout (relevant to R4 q8 KV-cache) and the attention numerics
  (relevant to iPhone 12 fp16 stability per ADR-2605241900).
- The weight-pack is reusable for future work: WebNN BitLinear EP
  (R3) can also consume `BitLinearWeightPack` once ORT-Web ships
  WebNN custom ops.

**Negative / costs**

- ~1500 additional LoC of forward-path code.
- transformers.js becomes a tokenizer + sampler dependency only;
  any future transformers.js minor version that changes its
  tokenizer/sampler API forces re-validation.
- Numerical-equivalence verification against the original
  transformers.js fp16 fallback path becomes more important
  (we're now running a different forward path, not just a different
  matmul kernel). The microbench at R1b commit 12 must include
  numerical-equivalence checks (top-k token agreement on a fixed
  prompt set).

**Reversibility**

- Fully reversible per-model via the `useBitLinearBridge` flag on
  `MODELS["baien-bitnet-2b"]` (already wired in R1b ADR §5,
  unchanged by this pivot). Setting the flag false routes through
  the legacy transformers.js fp16 path.

# Alternatives Considered

1. **Wait for ORT-Web to ship custom ops.** Rejected. The W3C
   WebGPU compute-shader custom-op proposal has been "experimental"
   since 2024; no public roadmap for stabilization. Waiting blocks
   the silent G1 violation indefinitely.

2. **Monkey-patch ORT-Web's internal kernel registry.** Rejected.
   ORT-Web's kernel dispatch is implemented across multiple
   internal modules (`backend-wasm-core`, `backend-webgpu-jsep`,
   etc.); patching them all is brittle and breaks on every minor
   version. The forward override is a clean public-API approach.

3. **Use MediaPipe LLM Inference Web's BitNet kernel.** Rejected
   per ADR-2605263300 Alternatives §5 — MediaPipe does not
   officially support BitNet 1.58 as of 2026-05-26.

4. **Vendor the bitnet.cpp Emscripten WASM port.** Rejected per
   CLAUDE.md "no third-party vendored code carrying Charter Rider"
   rule. Same posture as ADR-2605263300 G7.

5. **Continue with (B) and accept that R1b never runs end-to-end
   on the browser.** Rejected — the whole point of R1b is to close
   the silent G1 violation. A non-runnable R1b solves nothing.

# References

- ADR-2605263700 — R1b parent ADR (this amendment)
- ADR-2605263300 — R0 per-kernel inference (kernels module
  unchanged)
- ADR-2605241900 — Baien edge-target invariant (G1 the silent
  violation)
- ORT-Web bundled module inside `@huggingface/transformers@3.8.1`
  (inspected 2026-05-26, zero customOp references)
- ORT-Web upstream — https://github.com/microsoft/onnxruntime/tree/main/js/web
  (public API surface as of 2026-05-26; JSEP hooks internal only)
