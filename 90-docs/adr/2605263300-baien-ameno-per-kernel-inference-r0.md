---
id: adr-2605263300-baien-ameno-per-kernel-inference-r0
title: "Baien ameno per-kernel inference R0 — WGSL BitLinear + WASM SIMD ternary (bitnet.cpp API mirror)"
status: proposed
doc_type: adr
topic: baien-ameno-per-kernel-inference
authoritative: true
last_verified: 2026-05-26
priority: 5.0
axis: architecture
weight: 0.55
priority_note: "Closes the kernel-level gap left open by ADR-2605092350 §4 (browser runtime kernel table) and ADR-2605190824 (3-kernel axis: webgpu / wasm-ternary / mediapipe-gpu). Until this lands, baien-bitnet-2b in ameno runs as bf16-as-fp16 through transformers.js ORT-Web default EP — the ternary structure is wasted at edge."
authoritative_for:
  - browser-side BitLinear matmul shader (WGSL) sources
  - browser-side BitNet ternary i2_s WASM kernel (Rust + wasm-bindgen, bitnet.cpp API mirror)
  - ameno kernel dispatch ladder (webgpu-bitlinear → wasm-ternary-simd → transformers.js fp16 fallback)
  - per-kernel feature detection + capability probe
  - i2_s data layout on the wire (2-bit signed, 4 weights / byte, little-endian within byte)
  - activation absmean quantizer numerical contract (q8 → i2_s matmul → fp16 accumulate)
depends_on:
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - 2605190824-ameno-mediapipe-llm-browser-runtime
  - adr-2605242630-baien-federated-r1-webgpu-backward-poc
  - adr-2605252100-ameno-webnn-inference-fast-path
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - 20-actors/ameno/src/inference.ts
  - 20-actors/ameno/src/inference/webnn.ts
  - 20-actors/ameno/src/train/kernels.ts
  - 40-engine/baien-wasm-ternary/
  - https://github.com/microsoft/BitNet
supersedes: []
superseded_by: []
---

# ADR-2605263300: Baien ameno per-kernel inference R0 — WGSL BitLinear + WASM SIMD ternary (bitnet.cpp API mirror)

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

`20-actors/ameno/src/inference.ts` already registers a `baien-bitnet-2b`
model entry but the implementation delegates the whole forward pass to
`@huggingface/transformers` (ONNX Runtime Web). The dtype is `"fp16"`
("bf16-as-fp16, ternary structure unused, follow-up TODO" — comment on
line 78). Concretely:

- WebGPU path runs the ONNX graph through ORT-Web's WebGPU EP. Every
  `MatMul` operator allocates fp16 weight tensors and runs a generic
  fp16 GEMM. The 1.58-bit ternary weight blob is **expanded back to
  fp16 at model-load time** — 16× memory bloat for the trunk, and
  the popcount-based ternary matmul fast path is wasted.
- WASM path falls through to ORT-Web's WASM EP, also fp16, also
  generic GEMM.
- The `wasm-ternary` kernel label exists in
  `60-apps/etzhayyim-project-ameno/.../app.ts` MODEL_CATALOG but no
  dispatch code reads it — the only effect is a UI badge.
- ADR-2605092350 §4 specifies what's missing ("custom WebGPU shader,
  i2_s ⇒ packed-int8 dequant in shader", and "wasm-bitnet vendored
  fallback") but neither source file has ever existed in the repo.
- ADR-2605242630 R1a landed three WGSL kernels (LoRA forward / LoRA
  backward / Adam step) at `20-actors/ameno/src/train/kernels.ts`. All
  three are **generic fp32 matmuls** — not BitNet-specific — and the
  dispatch wrappers throw R1b markers. Inference reuses none of them.
- ADR-2605252100 R0 added WebNN feature-detection but inference
  dispatch throws "R0 contract-only" until ORT-Web's WebNN EP wires
  in R1.

The constitutional edge target (ADR-2605241900) is **WASM-32 +
iPhone 12+ + Android 4 GB**, ≤4 B BitNet 1.58 trunk, ≤2 GB inference
RAM @ 4 k context, all modality encoders frozen, frontier-beating
explicitly **NOT** a goal. The current implementation fits the RAM
envelope only because transformers.js's WebGPU EP uses fp16 (not
fp32) — but on iPhone 12 the bf16-expansion at load time already
pushes ~3.4 GB peak before the first token, which means the
`baien-bitnet-2b` entry in ameno **cannot actually load on the
constitutional target devices today**. This is a silent
gate-G1-violation of the edge invariant.

This ADR closes that gap at R0 by reserving paths and committing
authoritative WGSL + Rust sources. End-to-end dispatch (replacing
the ONNX `MatMul` nodes with our BitLinear kernel via a transformers.js
layer-replacement bridge) is R1b under a separate ADR — same pattern
as `train/kernels.ts` R1a / R1b split.

The reason this needs an ADR rather than being a routine impl task:

1. **Choice of API mirror is constitutional.** The user decision
   "microsoft bitnet cpp の wasm 版を実装してね. api などは合わせてね"
   (2026-05-26) constrains us to mirror the upstream
   `microsoft/BitNet` (a.k.a. `bitnet.cpp`) public surface, not invent
   a new one. This affects naming, tensor type identifiers (i2_s),
   LUT layout, and the kernel-task signature `ggml_bitnet_mul_mat_*`.
2. **Numerics fallback ladder is observable behaviour.** The order in
   which we try (webgpu-bitlinear → wasm-ternary-simd → transformers.js
   fp16) and the conditions under which we drop have to be specified
   so feature-detect call sites are stable.
3. **Charter Rider §2 applies to baien-wasm-ternary.** The Rust crate
   is first-party Apache-2.0 code; it carries the Rider notice and is
   subject to the SBT-gated distribution rules per ADR-2605192200.
4. **Vendor boundary is non-trivial.** bitnet.cpp upstream is MIT
   (Microsoft). We are NOT vendoring or forking it. We re-implement
   the public surface in Rust so the kernel can target wasm32 with
   v128 SIMD (Emscripten port of the C++ would land us in a separate
   build-tool boundary and a third-party fork directory per the
   "Do not add Charter Rider to 3rd-party vendored code" rule in
   CLAUDE.md). The "API mirror" stance — match the function names,
   tensor types, and numerical contract; re-implement everything else
   — is the same pattern used by the kami-engine nv-compat layer
   (ADR-2605261800 §D11) and is similarly justified under Google v.
   Oracle 2021 API fair use.

# Scope

In scope (R0 — this ADR):

- ADR + path reservation + authoritative WGSL + authoritative Rust
  source for the kernels. Dispatchers throw R1 markers.
- Per-kernel feature-detect contract (`probeBitnetBackend(): Promise<BitnetBackend>`).
- bitnet.cpp public-surface mirror: function names, i2_s tensor
  layout, LUT pre-compute signature, absmean activation quantizer
  contract.
- Capability-only WASM module loader (`load + run a no-op export`
  succeeds; matmul export throws R1).
- WGSL strings + Params layouts + bind-group documentation.
- Cargo + tsc clean.
- 14 immutable gates G1..G14, 12 non-goals N1..N12.

Out of scope (lands in subsequent ADRs / R-numbers):

- **R1a — Standalone WGSL kernel numeric test.** Isolated dispatch
  via node `--experimental-webgpu` / Dawn against a reference fp32
  matmul. No transformers.js touch yet.
- **R1b — Layer-replacement bridge.** Intercept transformers.js's
  ORT graph at `MatMul` op level and replace with our BitLinear
  dispatch. Requires either an ORT-Web custom-op registration path
  or a transformers.js pipeline-level interceptor. Either is novel
  work and gets its own ADR.
- **R1c — WASM SIMD optimization.** Replace the R0 scalar reference
  matmul in the Rust crate with v128 SIMD (`std::simd` or `wide`
  crate). R0 ships a scalar reference for correctness; SIMD is a
  pure performance change that needs a microbench to justify.
- **R2 — Modality encoder kernels.** SigLIP / Whisper-tiny / YAMNet
  encoder forwards on WebGPU. ADR-2605092350 §2 says encoders ship
  as int8 ONNX + WebGPU kernels; we have neither.
- **R3 — WebNN BitLinear EP.** If/when ORT-Web exposes a WebNN custom-op
  registration, route BitLinear through NPU on Copilot+ PC / Apple
  Neural Engine / QNN HTP per ADR-2605252100 W4.
- **R4 — KV-cache quantization.** baien's 16 k context budget needs
  q8 KV-cache; out of scope for this ADR.
- **R5 — Speculative decoding.** Out of scope; baien is not
  optimising for frontier latency per ADR-2605241900.
- **Anything baien-server-\* / baien-XL-\*.** This ADR is edge-only.
  Server-tier inference stays on Murakumo per ADR-2605215000.

# Decision

## 1. 5-layer architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ L5  ameno svelte appview                                         │
│       imports @etzhayyim/ameno/inference                         │
├─────────────────────────────────────────────────────────────────┤
│ L4  ameno/src/inference.ts (existing)                            │
│       MODELS["baien-bitnet-2b"] — gains `bitnetBackend?` field   │
│       loadModel + generate dispatch to L3 when backend != "fp16" │
├─────────────────────────────────────────────────────────────────┤
│ L3  ameno/src/inference/kernels/dispatch.ts (NEW)                │
│       probeBitnetBackend()                                       │
│       → BitnetBackend = "webgpu-bitlinear" | "wasm-ternary-simd" │
│                       | "wasm-ternary-scalar" | "fp16-fallback"  │
│       picks ladder, returns active backend handle                │
├─────────────────────────────────────────────────────────────────┤
│ L2  TWO kernel surfaces (NEW)                                    │
│                                                                  │
│   L2a  ameno/src/inference/kernels/bitlinear-forward.ts          │
│         WGSL_BITLINEAR_FORWARD (WGSL string)                     │
│         WGSL_BITNET_PACKED_DEQUANT (WGSL string)                 │
│         dispatchBitLinearForward(...)   → R1a throws             │
│         dispatchPackedDequant(...)      → R1a throws             │
│                                                                  │
│   L2b  ameno/src/inference/bitnet-bridge.ts                      │
│         class BitnetWasmModule (load + capability probe)         │
│         all dispatch methods → R1c throws                        │
├─────────────────────────────────────────────────────────────────┤
│ L1  40-engine/baien-wasm-ternary/ (NEW Rust crate)               │
│       Cargo.toml (wasm-bindgen, wide [optional], no std-by-deflt)│
│       src/lib.rs       — public wasm-bindgen surface             │
│       src/api.rs       — bitnet.cpp API mirror (free fns)        │
│       src/i2s.rs       — i2_s pack/unpack + layout constants     │
│       src/quantize.rs  — absmean activation quantizer (q8)       │
│       src/lut.rs       — LUT pre-compute for ternary × q8 matmul │
│       src/matmul.rs    — scalar reference matmul (R0)            │
│                          v128 SIMD impl (R1c)                    │
│       src/simd.rs      — std::simd / wide intrinsic wrappers     │
│                          (R0 = ALL stubs that panic R1c marker)  │
└─────────────────────────────────────────────────────────────────┘
```

## 2. bitnet.cpp public-API mirror

We mirror the **kernel-task-level** API of microsoft/BitNet, NOT the
full llama.cpp wrapper API. ameno owns model loading (via
transformers.js ONNX) and tokenization; we only need bitnet.cpp's
kernel primitives. The mirrored surface:

| Rust (`baien-wasm-ternary`) | bitnet.cpp upstream | Notes |
|---|---|---|
| `pub const GGML_TYPE_I2_S: TensorType` | `GGML_TYPE_I2_S` (`ggml-bitnet.h`) | 2-bit signed; 4 weights per byte. Tag value `40` (matches upstream). |
| `pub fn ggml_bitnet_init() -> i32` | `ggml_bitnet_init()` | LUT precompute table setup. R0 = sets a "initialised" flag; full LUT in R1c. |
| `pub fn ggml_bitnet_can_mul_mat(src0_ty, src1_ty, dst_ty) -> bool` | `ggml_bitnet_can_mul_mat()` | Returns true iff `(I2_S × Q8_0) → F16`. |
| `pub fn ggml_bitnet_mul_mat_task_compute(...)` | `ggml_bitnet_mul_mat_task_compute()` | The matmul kernel. Signature matches upstream — see §3. |
| `pub fn ggml_bitnet_transform_tensor(...)` | `ggml_bitnet_transform_tensor()` | bf16 → i2_s offline pack (used by build-time tools, not runtime — exposed only to keep the surface consistent). |
| `pub fn ggml_bitnet_get_type_traits(ty) -> TypeTraits` | `ggml_bitnet_get_type_traits()` | Byte-size, block-size queries for i2_s. |

What we do **NOT** mirror:

- `llama_init_from_file`, `llama_eval`, `llama_token_to_str` — ameno
  owns loading + tokenization via transformers.js.
- ggml's general tensor lib (graph, scheduler, ops). Out of scope;
  the only operator we implement is BitLinear matmul.
- bitnet.cpp's `bitnet-quantize` CLI. Quantization happens upstream
  in the HuggingFace `onnx-community/bitnet-b1.58-2B-4T-bf16-ONNX`
  pipeline (or in the R1c offline tool); the runtime is forward-only.

## 3. Kernel signature (matches bitnet.cpp `ggml_bitnet_mul_mat_task_compute`)

```rust
/// Mirrors ggml_bitnet_mul_mat_task_compute from
/// upstream/src/ggml-bitnet-mad.cpp (Microsoft/BitNet, MIT).
///
/// Computes:  dst[i, j] = sum_k W_ternary[i, k] * x_q8[k, j] * w_scale[i] * x_scale
/// W_ternary is i2_s packed (4 weights/byte); each weight ∈ {-1, 0, +1}.
/// x_q8 is q8_0 packed (per-block absmean scale).
///
/// `m` rows of output, `n` cols, `k` inner. `bits = 2` for BitNet 1.58.
///
/// R0: scalar reference. R1c: v128 SIMD via std::simd or wide.
pub fn ggml_bitnet_mul_mat_task_compute(
    src0: *const u8,         // i2_s weight block, length = (m * k) / 4 bytes
    scales: *const f16,      // per-output-row weight scale, length = m
    qlut: *const i8,         // q8-quantized LUT-expanded activation
    lut_scales: *const f16,  // per-block activation scale
    lut_biases: *const f16,  // per-block activation bias
    dst: *mut f16,           // output, length = m * n
    n: usize,
    k: usize,
    m: usize,
    bits: u32,               // 2 for BitNet 1.58
);
```

R0 ships a **scalar reference implementation** that:

1. Unpacks `src0` from i2_s on the fly (no precomputed LUT).
2. Reads `qlut[k, j]` as i8 (already quantized upstream).
3. Multiplies, accumulates in `i32`, applies `w_scale[i] * x_scale[j]`,
   stores to `dst` as `f16`.

This is correct but slow. R1c replaces the inner loop with v128 SIMD
+ a precomputed LUT (per the upstream `src/ggml-bitnet-lut.cpp`
strategy).

## 4. i2_s data layout (canonical — matches upstream)

Each byte packs 4 weights, little-endian within byte:

```
bit  7 6 5 4 3 2 1 0
     w3| w2| w1| w0
```

Each 2-bit slot encodes:

| 2-bit value | weight |
|---|---|
| `00` | `0` |
| `01` | `+1` |
| `10` (or `11`) | `-1` (sign bit set) |

This matches `microsoft/BitNet:src/ggml-bitnet.h` upstream and the HF
`bitnet-b1.58-2B-4T` packed format. R0 commits this layout as a
compile-time invariant (`pub const I2S_WEIGHTS_PER_BYTE: usize = 4;`)
so the WGSL shader binding contract and the Rust unpacker can never
drift.

## 5. WGSL kernel surfaces

### `WGSL_BITLINEAR_FORWARD`

```
Inputs:
  @group(0) @binding(0)  W_packed  : array<u32>   // i2_s packed, 16 weights / u32
  @group(0) @binding(1)  X_q8      : array<i32>   // q8 activations packed, 4 per u32 (i8)
  @group(0) @binding(2)  W_scale   : array<f16>   // per-row weight scale (length = M)
  @group(0) @binding(3)  X_scale   : array<f16>   // per-block activation scale
  @group(0) @binding(4)  Y         : array<f16>   // output, length = M * N
  @group(0) @binding(5)  P         : Params       // { M, N, K, kBlocks }

Workgroup: (16, 16, 1)
Per-thread output: Y[m, n] = sum_k unpack_i2s(W_packed[m, k]) * unpack_i8(X_q8[k, n])
                              * W_scale[m] * X_scale[n / block]
```

### `WGSL_BITNET_PACKED_DEQUANT`

A standalone shader that takes the i2_s packed weight buffer + per-row
scale and writes a contiguous **f16** weight tile. Used by:

- A debug-only fallback for transformers.js layer-replacement (R1b) when
  the WebGPU adapter advertises insufficient subgroup-size for the
  fused BitLinear kernel.
- A correctness oracle for the SIMD path: dequantize a tile in shader,
  compare against the scalar Rust dequant, expect bit-identical.

R0 ships the WGSL string; R1a wires the dispatch.

## 6. Backend selection ladder (`probeBitnetBackend()`)

```
1. WebGPU adapter present
   AND adapter.features.has("shader-f16")
   AND adapter.limits.maxComputeWorkgroupSizeX >= 256
   AND probe shader compile succeeds
   → "webgpu-bitlinear"

2. ELSE WebAssembly.SIMD supported
   AND baien-wasm-ternary.wasm loaded
   AND module exports `ggml_bitnet_can_mul_mat`
   → "wasm-ternary-simd"

3. ELSE WebAssembly supported
   AND baien-wasm-ternary.wasm loaded
   → "wasm-ternary-scalar"

4. ELSE → "fp16-fallback"  (current behaviour, transformers.js)
```

R0 ships the probe + the type. The probe **must not throw on any
branch** — caller gets a string. Actual dispatch is gated on the R1
ADRs.

## 7. Memory budget (per ADR-2605241900 §G1 invariant)

| Path | Trunk weight RAM @ load | Notes |
|---|---|---|
| Current (fp16-fallback) | ~3.4 GB | bf16 unpacked to fp16; **exceeds 2 GB ceiling** on iPhone 12 |
| webgpu-bitlinear | ~0.6 GB | i2_s packed on-device; dequant in shader register file |
| wasm-ternary-simd | ~0.6 GB | i2_s packed in linear memory; dequant per-block during matmul |
| wasm-ternary-scalar | ~0.6 GB | same as SIMD; only inner loop differs |

The current path's 3.4 GB load is the silent G1 violation that closes
when this ADR's R1c lands on at least one backend. R0 itself does not
change runtime memory (still fp16-fallback by default); it just
reserves the path.

## 8. 14 immutable gates

| # | Gate |
|---|---|
| G1 | Edge invariant per ADR-2605241900: ≤4 B trunk, ≤2 GB @4k, ≤2.5 GB @16k. New kernel MUST measurably reduce peak RAM, not increase. |
| G2 | bitnet.cpp API mirror is **kernel-task level only** (not llama-wrapper level). Function names, tensor type tags, and layout constants match upstream byte-for-byte. |
| G3 | i2_s layout (`I2S_WEIGHTS_PER_BYTE = 4`, little-endian within byte, 2-bit slot encoding `00 → 0`, `01 → +1`, `10/11 → -1`) is a compile-time invariant in Rust + a documented binding contract in WGSL. Drift between the two = G3 violation = revert. |
| G4 | R0 scalar reference matmul is the **numerical contract**. Every R1c SIMD impl + every WGSL impl must agree with it within `±1 ULP fp16` on a fixed test vector. |
| G5 | Murakumo-only inference (ADR-2605215000) is unaffected: this ADR is about **edge browser inference**, server-tier baien stays on the fleet. No commercial GPU rental introduced. |
| G6 | Charter Rider §2 attestation on the `baien-wasm-ternary` crate via NOTICE + symlink, same pattern as the other 39 first-party Apache-2.0 packages. |
| G7 | The crate is **not** vendored bitnet.cpp. It is a clean-room Rust re-impl of the public surface. No source files copied. No `lib/upstream-bitnet/` directory. |
| G8 | bitnet.cpp's API names are used under Google v. Oracle 2021 API fair use, same legal posture as ADR-2605261800 §D11 (PhysX). The crate's README + ADR cite this. |
| G9 | Dispatchers throw R1 markers in R0. **No silent fallback to fp16** — the backend probe always returns a string, and the dispatcher either succeeds (R1+) or throws with the next-ADR pointer (R0). |
| G10 | `probeBitnetBackend()` must not throw. Capability detection is graceful; only dispatch can throw. |
| G11 | Single-tab single-instance discipline (per ADR-2605191524). The WASM module is loaded **once per tab**; reload-on-model-change is a R1b concern. |
| G12 | Encoders (SigLIP / Whisper-tiny / YAMNet) are out of scope. R0 owns trunk BitLinear only. ADR-2605092350 §2 modality kernels become R2 under their own ADR. |
| G13 | No PII / model-data leaves the device. The kernel runs entirely client-side; the only network call is the WASM module fetch from `ameno.etzhayyim.com` static origin. |
| G14 | R0 commits **zero JS bytes** of behaviour change to existing inference.ts dispatch. The new files are additive and unused by default. fp16-fallback remains the active path until R1b. |

## 9. 12 non-goals

| # | Non-goal |
|---|---|
| N1 | Frontier-beating throughput (per ADR-2605241900 invariant). |
| N2 | Server-tier inference (Murakumo-only per ADR-2605215000). |
| N3 | Backward / training kernels (ADR-2605242630 owns that path; this ADR is forward-only). |
| N4 | KV-cache quantization (R4). |
| N5 | Speculative decoding. |
| N6 | Multi-tab swarm dispatch (ADR-2605191524 owns coordination; per-tab kernel is single-instance per G11). |
| N7 | bitnet.cpp llama-wrapper API mirror (only kernel-task layer). |
| N8 | bitnet.cpp vendoring or forking (clean-room Rust per G7). |
| N9 | WebNN BitLinear EP (R3 — needs upstream ORT-Web hooks). |
| N10 | Modality encoder kernels (R2). |
| N11 | Custom tokenizer or sampler (transformers.js TextStreamer keeps owning that surface). |
| N12 | Any commercial GPU rental for compilation, testing, or shader-cache priming. |

## 10. R0 deliverables (this commit)

1. This ADR.
2. `90-docs/adr/README.md` index row.
3. `deps.toml` `[[adrs]]` + `[[modules]]` entries (`baien-wasm-ternary`,
   `ameno-inference-kernels`).
4. `20-actors/ameno/src/inference/kernels/bitlinear-forward.ts` —
   `WGSL_BITLINEAR_FORWARD` WGSL string + `Params` interface +
   `dispatchBitLinearForward` (throws R1a).
5. `20-actors/ameno/src/inference/kernels/bitnet-packed-dequant.ts` —
   `WGSL_BITNET_PACKED_DEQUANT` WGSL string + `dispatchPackedDequant`
   (throws R1a).
6. `20-actors/ameno/src/inference/kernels/dispatch.ts` —
   `BitnetBackend` type + `probeBitnetBackend()` (real probe, no
   throw).
7. `20-actors/ameno/src/inference/kernels/index.ts` — barrel.
8. `20-actors/ameno/src/inference/bitnet-bridge.ts` —
   `class BitnetWasmModule { load(); capability(); dispose(); }` +
   typed proxies for `ggml_bitnet_*` that throw R1c.
9. `20-actors/ameno/package.json` `exports` additions for
   `./inference/kernels` + `./inference/bitnet-bridge`.
10. `40-engine/baien-wasm-ternary/Cargo.toml` (wasm-bindgen 0.2,
    `wide` optional, `cdylib`).
11. `40-engine/baien-wasm-ternary/src/lib.rs` — wasm-bindgen exports.
12. `40-engine/baien-wasm-ternary/src/api.rs` — `ggml_bitnet_*` free
    functions (R0 = scalar reference matmul + scalar dequant + LUT
    stubs that panic R1c).
13. `40-engine/baien-wasm-ternary/src/i2s.rs` — layout constants +
    pack/unpack.
14. `40-engine/baien-wasm-ternary/src/quantize.rs` — absmean q8 quant.
15. `40-engine/baien-wasm-ternary/src/lut.rs` — R0 = stub, R1c =
    LUT-expanded matmul.
16. `40-engine/baien-wasm-ternary/src/matmul.rs` — scalar reference.
17. `40-engine/baien-wasm-ternary/NOTICE` — Charter Rider §2.0 notice +
    bitnet.cpp API attribution.
18. `40-engine/baien-wasm-ternary/README.md` — API mirror table,
    legal posture, R-roadmap.
19. `tsc --noEmit` clean inside `20-actors/ameno/`.
20. `cargo check --target wasm32-unknown-unknown` clean inside
    `40-engine/baien-wasm-ternary/`.

## 11. R-roadmap (subsequent ADRs)

| R | Owner ADR (planned) | Scope |
|---|---|---|
| R1a | ADR-2605264xxx-baien-ameno-wgsl-bitlinear-numeric-test | Isolated WGSL kernel dispatch via Dawn/node; ±1 ULP vs scalar reference; no transformers.js. |
| R1b | ADR-2605264xxx-baien-ameno-onnx-graph-layer-replacement | Transformers.js / ORT-Web `MatMul` interceptor → BitLinear dispatch. End-to-end token generation on real model. |
| R1c | ADR-2605264xxx-baien-wasm-ternary-v128-simd | Replace scalar inner loop with `std::simd` / `wide` v128; popcount-based ternary × q8 matmul; LUT precompute. |
| R2 | ADR-2605264xxx-baien-ameno-encoder-kernels | SigLIP / Whisper-tiny / YAMNet WebGPU kernels (per ADR-2605092350 §2). |
| R3 | ADR-2605264xxx-baien-ameno-webnn-bitlinear-ep | WebNN custom-op route; ANE / DirectML NPU / QNN HTP. |
| R4 | ADR-2605264xxx-baien-ameno-kv-cache-q8 | q8 KV-cache for 16 k ctx fit. |

# Consequences

**Positive**

- Closes the documented gap from ADR-2605092350 §4 ("custom WebGPU
  shader, i2_s ⇒ packed-int8 dequant in shader") that has been
  outstanding since 2026-05-09.
- Unblocks the silent G1 (edge RAM invariant) violation in
  `baien-bitnet-2b` ameno loading.
- The API mirror choice makes the crate **drop-in replaceable** with
  an Emscripten-built `bitnet.cpp` WASM port — if the Rust impl
  underperforms or the upstream evolves, we can switch the WASM
  artifact without touching the ameno bridge.
- Three independent backend paths (WebGPU, WASM-SIMD, WASM-scalar)
  match the constitutional edge-target diversity (iPhone 12+ has
  WebGPU but Safari WebNN-less; Android Pixel 6+ has WebGPU; older
  Android falls to WASM-SIMD; lowest tier falls to WASM-scalar) per
  ADR-2605241900.

**Negative / costs**

- R0 commits ~1500 LOC across Rust + TS that does **nothing**
  observable end-user (G9: dispatchers throw, G14: zero behaviour
  change). The value is realised only once R1b lands. This is
  acceptable because R0 nails the API surface — every later R-number
  builds on it without re-design.
- Adds a new build target (`wasm32-unknown-unknown` for the Rust
  crate). CI does not yet run cargo across the monorepo; this ADR
  does not add CI either. Manual `cargo check` is the R0 gate.
- The bitnet.cpp legal posture (API fair use, no vendoring) requires
  ongoing audit if upstream changes its license. Today bitnet.cpp
  is MIT — compatible with Apache 2.0. If Microsoft re-licenses,
  G2 may need revisiting.

**Reversibility**

- Fully reversible. R0 commits only new files; the existing
  fp16-fallback dispatch is untouched (G14). Removing the new files
  + reverting the deps.toml entries restores the pre-R0 state with
  no API breakage anywhere.

# Alternatives Considered

1. **Vendor bitnet.cpp into `40-engine/baien-wasm-ternary-fork/` and
   build via Emscripten.** Rejected because (a) the "Do not add
   Charter Rider to 3rd-party vendored code" rule (CLAUDE.md) means
   the Rider can't apply to vendored upstream, (b) Emscripten adds a
   second build toolchain to the religious-corp monorepo (we
   currently have cargo + tsc + py; emcc would be the fourth),
   (c) wasm32-unknown-unknown with Rust is simpler to target across
   the kami-engine fleet, (d) `wide` / `std::simd` give us v128
   without intrinsic-level C++.

2. **AssemblyScript / hand-written WAT for the WASM kernel.**
   Rejected because v128 SIMD intrinsic support is shaky in
   AssemblyScript (no `i8x16.popcnt` lowering), and WAT-by-hand
   loses type safety against the bitnet.cpp API surface we're
   mirroring.

3. **Skip the WASM path, ship WebGPU only.** Rejected because
   ADR-2605241900 (edge invariant) explicitly lists "WASM-32" as a
   first-class target — older iPhones, older Androids, and any
   device where the WebGPU adapter cannot be acquired must still
   load baien.

4. **Skip the WGSL path, ship WASM only.** Rejected because the
   WGSL BitLinear shader gives a ~3-5× throughput improvement on
   any device with a working WebGPU adapter (matches the
   ADR-2605092350 §4 ordering: WebGPU > WASM > server-CPU). Edge
   inference at single-digit tokens/sec is below the
   Wellbecoming-UX threshold; WebGPU is necessary on supported
   devices.

5. **Use MediaPipe LLM Inference Web's BitNet kernel.** Per
   ADR-2605190824, MediaPipe is a third kernel we're already
   wiring. But (a) MediaPipe does not (as of 2026-05-26)
   officially support BitNet b1.58 — only Gemma 3n is listed in
   the `.task` registry, and (b) routing baien through MediaPipe
   would put us on Google's release cadence for our trunk's
   compatibility, a violation of vendor-independence per
   ADR-2605215000 §spirit.

6. **Defer the whole question to R1.** Considered. Rejected
   because the R0 scaffold cost is low (~1500 LOC of dispatchers +
   ADR), and pinning the bitnet.cpp API surface as a constitutional
   commitment **before** anyone writes the actual kernel prevents
   the (very real) risk that R1a's WGSL contract drifts from R1c's
   WASM contract. G3 (layout consistency) is best enforced at R0
   when both surfaces are written by the same hand on the same day.

# References

- ADR-2605241900 — Baien edge-target invariant (WASM-32, iPhone 12+, Android 4 GB)
- ADR-2605092350 — Baien 1-bit multimodal edge / browser / CPU design (§4 runtime target matrix)
- ADR-2605190824 — Ameno MediaPipe LLM Inference Web — third browser kernel
- ADR-2605242630 — Baien federated R1 WebGPU backward PoC (R1a WGSL pattern this ADR mirrors)
- ADR-2605252100 — Ameno WebNN inference fast path R0
- ADR-2605215000 — etzhayyim inference Murakumo-fleet-only (no RunPod)
- ADR-2605192200 — etzhayyim Apache 2.0 + Charter Rider v2.0
- ADR-2605261800 — kami-engine NVIDIA API compat layer (precedent for API-mirror legal posture)
- microsoft/BitNet (`bitnet.cpp`) — upstream MIT C++ reference
- HuggingFace `onnx-community/bitnet-b1.58-2B-4T-bf16-ONNX` — model artifact
- W3C WebGPU 1.0 spec, `shader-f16` extension
- W3C WebNN CR Draft 2026-05-21
- Google v. Oracle America, 593 U.S. ___ (2021) — API fair use posture
