# `baien-wasm-ternary`

BitNet 1.58 ternary i2_s kernel for `wasm32` — a clean-room Rust
re-implementation of the **kernel-task layer** of [`microsoft/BitNet`](https://github.com/microsoft/BitNet)
(`bitnet.cpp`).

**Authoritative ADR**: [`90-docs/adr/2605263300-baien-ameno-per-kernel-inference-r0.md`](../../90-docs/adr/2605263300-baien-ameno-per-kernel-inference-r0.md)

**Consumed by**: [`@etzhayyim/ameno`](../../orgs/etzhayyim/com-etzhayyim-ameno) browser
inference (`inference/bitnet-bridge.ts`).

**License**: Apache 2.0 + Charter Compliance Rider v2.0 (see [`NOTICE`](NOTICE)).

## What this is

bitnet.cpp's public API has two layers:

1. The **llama-wrapper layer** (`llama_init_from_file`, `llama_eval`,
   etc.) — full inference orchestration.
2. The **kernel-task layer** (`ggml_bitnet_mul_mat_task_compute`,
   `ggml_bitnet_init`, etc.) — the BitLinear matmul primitives.

This crate mirrors **only the kernel-task layer**. ameno owns model
loading and tokenization through `@huggingface/transformers`; we
only need the BitLinear primitives to replace the trunk's `MatMul`
ONNX nodes at inference time.

## What this is NOT

- **Not a vendored fork.** Zero source files copied from upstream.
- **Not an Emscripten port.** Clean-room Rust → `wasm32-unknown-unknown`.
- **Not a llama.cpp replacement.** Tokenization + sampler + KV-cache
  stay with transformers.js.
- **Not a training kernel.** Forward only; LoRA training lives in
  `@etzhayyim/ameno/train/kernels.ts` (ADR-2605242630).
- **Not for `baien-server-*` / `baien-XL-*`.** Server-tier inference
  is Murakumo-only per ADR-2605215000.

## API mirror table

| Rust (this crate) | bitnet.cpp upstream |
|---|---|
| `pub const GGML_TYPE_I2_S: i32 = 40` | `#define GGML_TYPE_I2_S 40` |
| `pub fn ggml_bitnet_init() -> i32` | `ggml_bitnet_init()` |
| `pub fn ggml_bitnet_can_mul_mat(...)` | `ggml_bitnet_can_mul_mat()` |
| `pub fn ggml_bitnet_mul_mat_task_compute(...)` | `ggml_bitnet_mul_mat_task_compute()` |
| `pub fn ggml_bitnet_transform_tensor(...)` | `ggml_bitnet_transform_tensor()` |
| `pub fn ggml_bitnet_get_type_traits(ty)` | `ggml_bitnet_get_type_traits()` |

## i2_s data layout (canonical, matches upstream)

Each byte packs 4 ternary weights, little-endian:

```
bit  7 6 5 4 3 2 1 0
     w3| w2| w1| w0
```

| 2-bit | weight |
|---|---|
| `00` | `0` |
| `01` | `+1` |
| `10` | `-1` |
| `11` | `-1` (reserved) |

See [`src/i2s.rs`](src/i2s.rs) constants. **The same layout is
mirrored in the WGSL shader** at
[`orgs/etzhayyim/com-etzhayyim-ameno/src/inference/kernels/bitlinear-forward.ts`](../../orgs/etzhayyim/com-etzhayyim-ameno/src/inference/kernels/bitlinear-forward.ts);
gate G3 (ADR-2605263300 §8) requires the two to never drift.

## R-roadmap (per ADR-2605263300 §10)

| R | What |
|---|---|
| **R0** (this commit) | Scaffold + scalar reference matmul + scalar reference dequant + tests + wasm-bindgen exports for capability probes. **`ggml_bitnet_mul_mat_task_compute` is not yet reachable from the JS side** — the wasm-bindgen pointer marshalling lands in R1c. |
| **R1a** | Standalone WGSL kernel numeric test against this crate's scalar matmul (±1 ULP fp16). Lives in [`orgs/etzhayyim/com-etzhayyim-ameno/src/inference/kernels/`](../../orgs/etzhayyim/com-etzhayyim-ameno/src/inference/kernels/). |
| **R1b** | transformers.js layer-replacement bridge — intercept `MatMul` nodes in the BitNet ONNX graph and dispatch through ameno's bridge. |
| **R1c** | v128 SIMD inner loop (`feature = "simd"`) + LUT-expanded matmul (`feature = "lut"`) + wasm-bindgen pointer marshalling for the matmul kernel-task. |
| **R2** | Modality encoder kernels (SigLIP / Whisper-tiny / YAMNet) — own ADR. |

## Build

```bash
# Host build (rlib + native tests)
cargo test

# wasm32 build (the deployment target)
cargo check --target wasm32-unknown-unknown

# Full build via wasm-pack (R1c — once wasm-bindgen exports are wired)
wasm-pack build --release --target web
```

## Edge invariant (ADR-2605241900)

This crate is part of the baien edge inference path. The target is:

- **WASM-32** runtime
- **iPhone 12+** (Safari, no WebGPU on iOS 14, WebGPU on iOS 18+)
- **Android** with **≥ 4 GB RAM**
- **≤ 2.0 GB peak inference RAM** at 4 k context
- **≤ 2.5 GB peak inference RAM** at 16 k context

Frontier-beating throughput is **explicitly NOT a goal**. Optimisations
that improve throughput at the cost of breaking the memory envelope
are rejected at code review.

## Legal posture

The API names (`ggml_bitnet_*`, `GGML_TYPE_I2_S`) are used under the
rule of **Google v. Oracle America, 593 U.S. ___ (2021)** (API
fair use). Same legal posture as the kami-engine nv-compat layer
per ADR-2605261800 §D11. No upstream source has been copied;
implementations are clean-room Rust.

upstream `microsoft/BitNet` is distributed under the MIT License.
Should upstream change its license, this crate is unaffected (no
derivative work; API names are fair use).
