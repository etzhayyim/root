/**
 * @etzhayyim/ameno/inference/kernels/bitlinear-forward — WGSL BitLinear
 * forward kernel (ADR-2605263200 §5).
 *
 * BitLinear forward computes
 *
 *     Y[m, n] = (Σ_k unpack_i2s(W_packed[m, k]) · unpack_i8(X_q8[k, n]))
 *               · W_scale[m] · X_scale[n / block]
 *
 * where `W_packed` is the i2_s ternary weight tensor (4 weights per u32
 * — see `i2s` layout constants in `40-engine/baien-wasm-ternary/src/i2s.rs`,
 * mirrored bit-for-bit here per gate G3) and `X_q8` is the q8-quantized
 * activation tensor (4 i8 values per u32).
 *
 * R0 (this commit) ships:
 *   - `WGSL_BITLINEAR_FORWARD`  — authoritative WGSL string
 *   - `BitLinearForwardParams`  — Params layout (immutable contract)
 *   - `dispatchBitLinearForward` — throws R1a marker
 *
 * R1a wires the dispatch (bind groups, pipeline, queue submit).
 * R1b wires the transformers.js layer-replacement bridge.
 * R1c replaces the scalar reference matmul in the Rust WASM crate
 * with v128 SIMD; this WGSL kernel is unaffected by R1c.
 *
 * Gate references:
 *   - G3 (i2_s layout drift = revert) — see `I2S_*` constants below;
 *     must match `i2s.rs` exactly.
 *   - G4 (scalar reference is numerical contract) — this shader must
 *     agree with the Rust scalar matmul to ±1 ULP fp16 on the fixed
 *     test vector before R1a passes.
 *   - G9 (no silent fallback) — `dispatchBitLinearForward` throws,
 *     does not silently call transformers.js.
 *   - G14 (zero behaviour change in R0) — this module is unused by
 *     default; the existing `inference.ts` dispatch is untouched.
 */

/**
 * i2_s packed-weight layout constants. **MUST** match
 * `40-engine/baien-wasm-ternary/src/i2s.rs` byte-for-byte (gate G3).
 *
 * Each byte packs 4 weights, little-endian within the byte:
 *
 *     bit  7 6 5 4 3 2 1 0
 *          w3  w2  w1  w0
 *
 * Each 2-bit slot encodes:
 *
 *     2-bit | weight
 *     ------+--------
 *     00    |   0
 *     01    |  +1
 *     10    |  -1
 *     11    |  -1   (reserved/equivalent — upstream maps both 10 and 11 to -1)
 *
 * This matches `microsoft/BitNet:src/ggml-bitnet.h` and the HF
 * `onnx-community/bitnet-b1.58-2B-4T-bf16-ONNX` packed format.
 */
export const I2S_WEIGHTS_PER_BYTE = 4 as const;
export const I2S_BITS_PER_WEIGHT = 2 as const;
export const I2S_WEIGHTS_PER_U32 = 16 as const;

/**
 * Params struct passed via uniform binding 6. Encoded as 6 × u32
 * (24 bytes; WebGPU uniform requires 16-byte alignment so the struct
 * is padded to 32 bytes — the shader's `struct Params { ... }` makes
 * the padding explicit).
 *
 * `kBlocks` is `ceil(K / Q8_BLOCK_SIZE)`. `Q8_BLOCK_SIZE` matches
 * llama.cpp / bitnet.cpp's q8_0 block size of 32 elements — bound at
 * shader compile time via `const Q8_BLOCK_SIZE: u32 = 32u;` in the
 * WGSL source.
 */
export interface BitLinearForwardParams {
  /** Output rows. */
  readonly M: number;
  /** Output cols. */
  readonly N: number;
  /** Inner dim. */
  readonly K: number;
  /** `ceil(K / 32)` — number of q8_0 blocks per output column. */
  readonly kBlocks: number;
  /** Reserved for R1b layer-replacement metadata (e.g. layer index). */
  readonly reserved0: number;
  /** Reserved for R1b. */
  readonly reserved1: number;
}

/**
 * BitLinear forward shader.
 *
 * Bindings:
 *   @group(0) @binding(0)  W_packed  : array<u32>    — i2_s weights (16 / u32)  [M × ceil(K/16)]
 *   @group(0) @binding(1)  X_q8      : array<i32>    — q8 activations (4 i8 / u32) [ceil(K/4) × N]
 *   @group(0) @binding(2)  W_scale   : array<f16>    — per-row weight scale [M]
 *   @group(0) @binding(3)  X_scale   : array<f16>    — per-block activation scale [kBlocks × N]
 *   @group(0) @binding(4)  Y         : array<f16>    — output [M × N]
 *   @group(0) @binding(5)  P         : Params
 *
 * Workgroup: 16 × 16 × 1. One output tile per workgroup.
 *
 * Requires:
 *   - `shader-f16` feature on the GPUAdapter (probed by
 *     `probeBitnetBackend()` — caller MUST NOT submit this shader to
 *     an adapter that does not advertise it).
 */
export const WGSL_BITLINEAR_FORWARD = /* wgsl */ `
enable f16;

struct Params {
  M        : u32,
  N        : u32,
  K        : u32,
  kBlocks  : u32,
  reserved0: u32,
  reserved1: u32,
};

const Q8_BLOCK_SIZE: u32 = 32u;
const I2S_WEIGHTS_PER_U32: u32 = 16u;
const I2S_BITS_PER_WEIGHT: u32 = 2u;

@group(0) @binding(0) var<storage, read>          W_packed : array<u32>;
@group(0) @binding(1) var<storage, read>          X_q8     : array<i32>;
@group(0) @binding(2) var<storage, read>          W_scale  : array<f16>;
@group(0) @binding(3) var<storage, read>          X_scale  : array<f16>;
@group(0) @binding(4) var<storage, read_write>    Y        : array<f16>;
@group(0) @binding(5) var<uniform>                P        : Params;

// Unpack one ternary weight from a u32 holding 16 weights.
// idx ∈ [0, 16). Returns -1, 0, or +1 as i32.
fn unpack_i2s(word: u32, idx: u32) -> i32 {
  let shift: u32 = idx * I2S_BITS_PER_WEIGHT;
  let bits: u32 = (word >> shift) & 3u;
  // 00 → 0 ; 01 → +1 ; 10/11 → -1
  if (bits == 0u) {
    return 0;
  }
  if (bits == 1u) {
    return 1;
  }
  return -1;
}

// Unpack one i8 activation from a u32 holding 4 packed i8 values.
// idx ∈ [0, 4). Sign-extends to i32.
fn unpack_i8(word: i32, idx: u32) -> i32 {
  let shift: u32 = idx * 8u;
  let byte: i32 = (word >> shift) & 0xff;
  // Sign-extend: if bit 7 is set, set upper bits.
  if ((byte & 0x80) != 0) {
    return byte | i32(0xffffff00u);
  }
  return byte;
}

@compute @workgroup_size(16, 16, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let m: u32 = gid.x;
  let n: u32 = gid.y;
  if (m >= P.M || n >= P.N) {
    return;
  }

  // Inner accumulator stays i32 — the ternary × q8 partial sum cannot
  // overflow i32 for K ≤ 65k (max BitNet-2B hidden dim is 2048, well
  // under the i32 envelope of ±2^31).
  var block_acc: i32 = 0;
  var output_acc: f16 = f16(0.0);

  let w_packed_cols: u32 = (P.K + I2S_WEIGHTS_PER_U32 - 1u) / I2S_WEIGHTS_PER_U32;
  let x_q8_rows: u32 = (P.K + 3u) / 4u;

  for (var blk: u32 = 0u; blk < P.kBlocks; blk = blk + 1u) {
    let k_start: u32 = blk * Q8_BLOCK_SIZE;
    let k_end: u32 = min(k_start + Q8_BLOCK_SIZE, P.K);
    block_acc = 0;

    for (var k: u32 = k_start; k < k_end; k = k + 1u) {
      // W_packed[m, k/16] holds 16 weights; the (k%16)-th slot is ours.
      let w_word_idx: u32 = m * w_packed_cols + (k / I2S_WEIGHTS_PER_U32);
      let w_word: u32 = W_packed[w_word_idx];
      let w: i32 = unpack_i2s(w_word, k % I2S_WEIGHTS_PER_U32);

      // X_q8[k/4, n] holds 4 i8; the (k%4)-th slot is ours.
      let x_word_idx: u32 = (k / 4u) * P.N + n;
      let x_word: i32 = X_q8[x_word_idx];
      let x: i32 = unpack_i8(x_word, k % 4u);

      block_acc = block_acc + w * x;
    }

    // Apply per-block activation scale; weight scale is per-row.
    let xs_idx: u32 = blk * P.N + n;
    output_acc = output_acc + f16(block_acc) * X_scale[xs_idx];
  }

  output_acc = output_acc * W_scale[m];
  Y[m * P.N + n] = output_acc;
}
`;

/**
 * Dispatch the BitLinear forward shader.
 *
 * R0 (this commit) throws with a clear pointer to R1a (numeric test
 * harness — isolated dispatch via Dawn/node, ±1 ULP vs scalar
 * reference). R1b wires this into the transformers.js layer-replacement
 * bridge so the trunk's `MatMul` nodes route through here.
 *
 * Signature is permissive (`_args: unknown[]`) until R1a fixes it —
 * matches the pattern from `train/kernels.ts:dispatchLoraForward`.
 */
export async function dispatchBitLinearForward(
  ..._args: unknown[]
): Promise<void> {
  throw new Error(
    "dispatchBitLinearForward: R1a — requires isolated WGSL kernel dispatch via Dawn/node against scalar reference matmul. WGSL_BITLINEAR_FORWARD is ready; bind-group + pipeline setup is missing.",
  );
}
