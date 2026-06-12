---
id: adr-2605263401-baien-ameno-wgsl-bitlinear-numeric-test-r1a
renumbered_from: "2605263400"
title: "Baien ameno WGSL BitLinear numeric test R1a — isolated wgpu dispatch + ±1 ULP fp16 vs scalar reference"
status: proposed
doc_type: adr
topic: baien-ameno-wgsl-bitlinear-numeric-test
authoritative: true
last_verified: 2026-05-26
priority: 5.0
axis: architecture
weight: 0.40
priority_note: "R1a of the R-roadmap pinned by ADR-2605263300 §10. Validates the WGSL BitLinear shader against the Rust scalar reference matmul (the numerical contract per gate G4) without touching transformers.js. R1b layer-replacement and R1c v128 SIMD remain separate ADRs."
authoritative_for:
  - WGSL shader source-of-truth location + duplication policy
  - isolated wgpu dispatch test harness path
  - ±1 ULP fp16 tolerance contract
  - test data shape coverage matrix (single-block / multi-block / non-block-aligned-k)
  - graceful skip when no GPU adapter available (CI-friendly)
depends_on:
  - adr-2605263300-baien-ameno-per-kernel-inference-r0
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - 20-actors/ameno/src/inference/kernels/bitlinear-forward.ts
  - 40-engine/baien-wasm-ternary/src/matmul.rs
  - 40-engine/baien-wasm-ternary/shaders/bitlinear_forward.wgsl
supersedes: []
superseded_by: []
---

# ADR-2605263401: Baien ameno WGSL BitLinear numeric test R1a — isolated wgpu dispatch + ±1 ULP fp16 vs scalar reference

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

ADR-2605263300 R0 landed:

- `WGSL_BITLINEAR_FORWARD` (authoritative WGSL string) at
  `20-actors/ameno/src/inference/kernels/bitlinear-forward.ts`.
- Rust scalar reference matmul `mul_mat_i2s_q8_f16_ref` at
  `40-engine/baien-wasm-ternary/src/matmul.rs` — gate G4 declares
  this **the numerical contract**: every WGSL impl + every R1c SIMD
  impl must agree with it within ±1 ULP fp16.
- `dispatchBitLinearForward` throws `R1a` marker — "requires isolated
  WGSL kernel dispatch via Dawn/node against scalar reference matmul.
  WGSL_BITLINEAR_FORWARD is ready; bind-group + pipeline setup is
  missing."

R1a closes this: stand up a dispatch harness, run the WGSL shader,
compare against the scalar reference. No transformers.js, no end-to-
end token generation, no SIMD.

The R0 ADR pinned R1a's owner ADR as `2605264xxx`-prefixed; this ADR
slots into `2605263400` because the working sequence ran past
midnight in the same wave (the YYMMDDhhmm convention is treated as
monotonically-increasing sortable here, same posture as
2605263000-onward ADRs landed today).

## Choice of harness: wgpu Rust test, NOT node `--experimental-webgpu`

Three candidate harnesses:

| Harness | Pros | Cons |
|---|---|---|
| **wgpu Rust test** (chosen) | Same crate already exports `mul_mat_i2s_q8_f16_ref`; bit-exact f16 comparisons via `half::f16`; no JS runtime; runs on cargo CI; uses Vulkan/Metal/DX12 backend (close to browser WebGPU but real GPU) | Need wgpu dev-dependency on `baien-wasm-ternary`; not the actual browser runtime |
| node `--experimental-webgpu` | Closer to browser runtime (Chromium's Dawn) | flag-gated, version-pinned, not on all CI runners; ESM module loader + WGSL string interop more complex; readback to fp16 via Uint16Array is awkward |
| headless Chromium + Playwright | True browser runtime | Heavyweight test environment; flaky on CI; not where reference matmul lives |

wgpu wins because (a) the reference matmul is in Rust and we want
bit-exact comparison without crossing language boundaries, (b) wgpu
exposes the same shader-f16 feature as the browser-side WebGPU, (c)
running the WGSL through wgpu's `wgpu::naga` validator surfaces
syntactic + semantic issues without a browser, (d) cargo test runs
on every contributor's machine without extra tooling.

The harness validates the **shader**, not the **browser runtime**.
End-to-end browser runtime validation is R1b's responsibility
(transformers.js layer-replacement) and ends up running on real
device matrices (iPhone 12, Pixel 6, Mac M1+) per the ADR-2605241900
edge invariant.

## Choice of WGSL source-of-truth: shared .wgsl file

R0 placed the WGSL inside a TypeScript string literal
(`WGSL_BITLINEAR_FORWARD` in `bitlinear-forward.ts`). For R1a to
test the **same** shader source the browser would run, either:

1. The Rust test embeds a duplicate of the WGSL string. Gate G3
   (layout invariant) catches drift, but only at code review.
2. The WGSL moves to a standalone `.wgsl` file. The TS module reads
   it via bundler asset import (Vite `?raw`); the Rust test reads it
   via `include_str!`. **Single source of truth** — no drift possible.

(2) is strictly better and is what R1a ships. The TS file becomes a
thin wrapper around the file content; existing `dispatchBitLinearForward`
signature is unchanged.

# Scope

In scope (R1a — this ADR):

- Move WGSL strings to standalone `.wgsl` files under
  `40-engine/baien-wasm-ternary/shaders/`.
- TS `bitlinear-forward.ts` + `bitnet-packed-dequant.ts` updated to
  load the WGSL via Vite-friendly `?raw` import (with fallback
  inline copy for the test runner — see "Implementation note" §5).
- wgpu Rust integration test at
  `40-engine/baien-wasm-ternary/tests/wgpu_bitlinear_forward.rs`.
- Test data matrix:
  - **T1**: M=1, K=32, N=1, all weights +1, activations `[0..32)`.
    Expected ~496 (matches `matmul::tests::all_positive_weights`).
  - **T2**: M=1, K=32, N=1, alternating ±1, activations `[1.0; 32]`.
    Expected ~0 (matches `matmul::tests::one_block_one_row_one_col`).
  - **T3**: M=4, K=64, N=4 (multi-row, multi-col, 2-block K).
    Random-ish ternary weights + random-ish activations; expect
    bit-identical agreement.
  - **T4**: M=2, K=128, N=8 (BitNet-2B-shape proxy: hidden_dim=2048
    scaled down by 16 to keep the test fast). Bit-identical.
- ±1 ULP fp16 tolerance (element-wise; the comparison decodes both
  outputs from `f16` to `f32`, computes `|a - b| ≤ ulp_f16(a)` where
  `ulp_f16(a)` is the spacing between `a` and its next-representable
  fp16 neighbour).
- Graceful skip on no GPU adapter (returns immediately with a
  `println!("skipping: no wgpu adapter")` — CI without GPU passes).
- `tests/common/mod.rs` factory for the `wgpu::Device` + `Queue` to
  share across future shader tests (R1a + R2 encoders + R1c LUT
  oracle).

Out of scope (lands in subsequent ADRs):

- **R1b — transformers.js layer-replacement bridge.** Owns the real
  trunk's `MatMul` interception + end-to-end token generation.
- **R1c — v128 SIMD inner loop + LUT-expanded matmul +
  wasm-bindgen pointer marshalling.** Pure performance work; same
  numerical contract.
- **R2 — encoder kernels** (SigLIP / Whisper-tiny / YAMNet).
- **WebNN BitLinear EP** (R3, ADR-2605252100 hookup).
- **Real-device microbench** (Geekbench-style throughput on iPhone
  12 / Pixel 6 / M1) — R1b owns this since end-to-end is needed
  to measure useful throughput.

# Decision

## 1. WGSL relocation

Two new files:

- `40-engine/baien-wasm-ternary/shaders/bitlinear_forward.wgsl`
- `40-engine/baien-wasm-ternary/shaders/bitnet_packed_dequant.wgsl`

These contain the verbatim WGSL strings from
`bitlinear-forward.ts:WGSL_BITLINEAR_FORWARD` and
`bitnet-packed-dequant.ts:WGSL_BITNET_PACKED_DEQUANT` respectively.
The TS files keep their public `WGSL_*` exports but the string body
becomes a `?raw` import (Vite + esbuild conventions; documented at
top of file).

## 2. Vite `?raw` import + fallback

```ts
// 20-actors/ameno/src/inference/kernels/bitlinear-forward.ts
import wgslSource from "../../../../40-engine/baien-wasm-ternary/shaders/bitlinear_forward.wgsl?raw";
export const WGSL_BITLINEAR_FORWARD = wgslSource;
```

The `?raw` suffix is the Vite (and bundled by SvelteKit / Nuxt /
Next on file-load-as-string) convention for importing a file
verbatim as a string. For build environments without `?raw` support
(plain `tsc --noEmit`, Node REPL, ts-node) we fall back to an inline
copy guarded behind a build-time conditional.

**Implementation note**: `tsc --noEmit` does NOT understand `?raw`
out-of-the-box. To keep `tsc` clean (gate from R0 §10.19) we add a
TypeScript ambient declaration at
`20-actors/ameno/src/types/wgsl-raw.d.ts`:

```ts
declare module "*.wgsl?raw" {
  const content: string;
  export default content;
}
```

This is a type-only declaration; it does not change runtime semantics.
The actual WGSL load happens at bundler-time when the appview is
built.

## 3. wgpu Rust test harness

New file: `40-engine/baien-wasm-ternary/tests/wgpu_bitlinear_forward.rs`.

```rust
use baien_wasm_ternary::{i2s::*, matmul::*, quantize::*};
use half::f16;
use wgpu::util::DeviceExt;

const SHADER_SOURCE: &str =
    include_str!("../shaders/bitlinear_forward.wgsl");

async fn create_device() -> Option<(wgpu::Device, wgpu::Queue)> {
    let instance = wgpu::Instance::new(&wgpu::InstanceDescriptor::default());
    let adapter = instance
        .request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            ..Default::default()
        })
        .await
        .ok()?;
    if !adapter.features().contains(wgpu::Features::SHADER_F16) {
        return None;
    }
    let (device, queue) = adapter
        .request_device(&wgpu::DeviceDescriptor {
            required_features: wgpu::Features::SHADER_F16,
            ..Default::default()
        })
        .await
        .ok()?;
    Some((device, queue))
}

#[pollster::test]
async fn bitlinear_forward_matches_scalar_reference_t1() {
    let Some((device, queue)) = create_device().await else {
        eprintln!("skipping: no wgpu adapter / no shader-f16 feature");
        return;
    };
    // ... shape T1: M=1, K=32, N=1, all weights +1, activations [0..32)
    // ... build buffers, dispatch, readback, compare ±1 ULP fp16
}

// T2..T4 follow the same pattern.
```

**Why `pollster` for async**: cargo test does not natively support
async fn. `pollster::test` is a minimal proc-macro that runs the
future to completion. wgpu's `request_adapter` / `request_device` /
buffer-mapping callbacks are all async; running them on a real
async runtime (tokio) is overkill for a test that does one
GPU dispatch. `pollster` is ~30 lines of code and is the de facto
standard for wgpu integration tests upstream.

## 4. Buffer layout (matches WGSL bindings byte-for-byte)

```
Binding 0  W_packed : storage<read>       Uint32Array  (i2_s, 16 weights/u32)
Binding 1  X_q8     : storage<read>       Int32Array   (4 i8/u32, q8_0 layout)
Binding 2  W_scale  : storage<read>       Uint16Array  (f16, length M)
Binding 3  X_scale  : storage<read>       Uint16Array  (f16, length kBlocks × N)
Binding 4  Y        : storage<read_write> Uint16Array  (f16, length M × N)
Binding 5  Params   : uniform             6 × u32
```

The packing utilities (`pack_i2s_byte`, `quantize_row_q8_0_ref`)
already produce the right layouts at the byte level. The Rust test
takes the same `&[u8]` weight buffer the WGSL reads and the same
`&[BlockQ8_0]` activation buffer (re-interpreting `BlockQ8_0` as
`(u16, [i8; 32])` for the GPU upload).

## 5. ULP comparison

The test agrees on `±1 ULP fp16` element-wise:

```rust
fn within_1_ulp_f16(a: f16, b: f16) -> bool {
    if a == b {
        return true;
    }
    let a_bits = a.to_bits() as i32;
    let b_bits = b.to_bits() as i32;
    // For different-sign fp16 values straddling zero, ULP distance
    // is measured through ±0 — both are denormal, so the bit gap is
    // small in absolute terms.
    (a_bits - b_bits).abs() <= 1
}
```

This is the canonical fp16 ULP comparison (matches `cmath`
`nextafter` semantics on positive halves; the across-zero edge case
is documented in the comparison helper).

## 6. Test pass criteria

For each (T1..T4):

1. `bitlinear_forward_matches_scalar_reference_t<N>` is annotated
   `#[pollster::test]`.
2. The test allocates buffers per §4, dispatches the WGSL kernel,
   reads back `Y`.
3. Calls `mul_mat_i2s_q8_f16_ref` with identical inputs.
4. For every `(m, n)` in the output, asserts `within_1_ulp_f16(y_gpu, y_ref)`.
5. On no-GPU, prints "skipping" and returns (test passes; cargo
   treats `return` as success).

R1a is **complete** when all four tests pass on at least one
device class:

- macOS M1+ (Metal backend) — primary developer workstation.
- Linux + Vulkan — CI lane.
- iOS Safari (WebGPU on iOS 18+) — deferred to R1b because the
  browser path requires the layer-replacement harness anyway.

## 7. Cargo.toml additions

```toml
[dev-dependencies]
wgpu = { version = "24", default-features = false, features = ["wgsl", "naga", "vulkan", "metal", "dx12"] }
pollster = "0.3"
bytemuck = "1"
```

`wgpu 24` matches the kami-engine fleet (`40-engine/kami-engine/kami-web/Cargo.toml:31`).
`bytemuck` is used for `Pod` / `Zeroable` derive on the host-side
`Params` struct (uniform upload).

## 8. Gates inherited from R0 + new

Inherited (unchanged):

- **G3**: i2_s layout invariant. R1a structurally enforces this by
  the shader-source extraction (only one copy of the layout
  constants exists; the WGSL imports the same byte-for-byte layout
  that Rust uses).
- **G4**: scalar reference is numerical contract. R1a is the **first
  test of this contract** — until R1a, gate G4 was unverified.
- **G14**: zero behaviour change. R1a adds a test; it does not
  change the production code path. `inference.ts` is untouched.

New gate added by R1a:

- **R1a-G1 (WGSL source SSoT)**: The `.wgsl` files under
  `40-engine/baien-wasm-ternary/shaders/` are the **only** source of
  the shader text. TS modules import them via `?raw`. Inline string
  duplication is a revert offence.

# Consequences

**Positive**

- Closes gate G4 verification (was open since R0).
- Establishes the wgpu test harness, reusable for R2 encoder
  kernels.
- WGSL source-of-truth consolidation prevents shader drift between
  ameno + Rust crate (which was a documented risk under R0 G3).

**Negative / costs**

- Adds wgpu + pollster dev-dependencies to the Rust crate
  (compile-time cost for `cargo test`; runtime cost on CI for
  spinning up a software rasterizer if no GPU).
- The Vite `?raw` import + tsc ambient declaration is a small
  build-tooling expansion. Documenting it inline in the affected
  TS files mitigates the surprise factor.
- Tests run faster on Metal (M1) than on Linux Vulkan llvmpipe
  (software rasterizer); CI without a real GPU falls back to
  llvmpipe which can be 30-60s for the 4 tests. Acceptable for
  the once-per-PR cadence.

**Reversibility**

- Fully reversible. Reverting R1a leaves:
  - The two `.wgsl` files in `shaders/` (harmless),
  - The `wgpu_bitlinear_forward.rs` test (harmless),
  - The TS `?raw` imports (replaceable by re-inlining the WGSL
    strings if the `?raw` convention proves problematic).

# Alternatives Considered

1. **Test from JavaScript via node `--experimental-webgpu`.**
   Rejected per Context §"Choice of harness": no clean Rust-Rust
   reference comparison, flag-gated, version-pinned, ESM-WGSL
   interop awkward.

2. **Test via Playwright + headless Chromium.** Rejected: too
   heavyweight, doesn't run on cargo CI, doesn't get us bit-exact
   comparison.

3. **Keep WGSL duplicated between TS + Rust.** Rejected because
   gate G3 (layout invariant) becomes a code-review checklist
   item rather than a structural property. Single-source-of-truth
   is the cheap structural enforcement.

4. **Compute ULP tolerance dynamically from `fma` rounding bounds.**
   Rejected: ±1 ULP is the tightest practical tolerance for fp16
   matmul without going to fp32 accumulation everywhere. The
   scalar reference already accumulates in `i32` (exact for K ≤ 65k)
   and converts to f16 at the end; the WGSL shader does the same.
   They should agree to bit-exact in most cases; ±1 ULP allows
   rounding-direction differences on the final `f16` store.

5. **Defer R1a, jump to R1b.** Considered. Rejected because R1b
   would have no numerical contract to verify against in
   isolation — once you wire transformers.js's full graph in,
   debugging a numeric divergence at the matmul level becomes
   ten times harder. R1a is the cheap baseline that R1b can
   reduce to when it sees a regression.

# References

- ADR-2605263300 — Baien ameno per-kernel inference R0 (parent ADR)
- ADR-2605241900 — Baien edge-target invariant
- ADR-2605192200 — etzhayyim Apache 2.0 + Charter Rider v2.0
- `40-engine/baien-wasm-ternary/src/matmul.rs` —
  `mul_mat_i2s_q8_f16_ref` scalar reference (the numerical contract)
- `20-actors/ameno/src/inference/kernels/bitlinear-forward.ts` —
  WGSL_BITLINEAR_FORWARD authoritative source (becomes a `?raw`
  import in R1a)
- microsoft/BitNet (`bitnet.cpp`) — upstream MIT reference
- wgpu 24 documentation — https://wgpu.rs
- IEEE-754 binary16 — fp16 format specification (used by the
  `half` crate)
