/**
 * @etzhayyim/ameno/inference/kernels/bitnet-packed-dequant — WGSL
 * i2_s → f16 dequant shader (ADR-2605263300 §5).
 *
 * Standalone shader that takes a tile of i2_s packed weights + the
 * per-row scale and writes a contiguous f16 weight tile. Used as:
 *
 *   1. A debug-only fallback for transformers.js layer-replacement
 *      (R1b) when the WebGPU adapter advertises insufficient
 *      `maxComputeWorkgroupStorageSize` for the fused BitLinear
 *      kernel — we dequant once, then submit a generic fp16 GEMM.
 *
 *   2. A correctness oracle for the SIMD path: dequant a tile in
 *      shader, compare against the scalar Rust dequant in
 *      `40-engine/baien-wasm-ternary/src/i2s.rs`, expect bit-identical
 *      output (gate G4).
 *
 * The i2_s layout constants below MUST match
 * `40-engine/baien-wasm-ternary/src/i2s.rs` and
 * `./bitlinear-forward.ts` (gate G3).
 */

/**
 * Params struct for the dequant shader. Encoded as 4 × u32 (uniform
 * block — 16 bytes, naturally aligned).
 */
export interface BitnetPackedDequantParams {
  /** Output rows. */
  readonly M: number;
  /** Output cols (= K — the inner dim of the BitLinear matmul). */
  readonly K: number;
  /** Reserved for R1b. */
  readonly reserved0: number;
  /** Reserved for R1b. */
  readonly reserved1: number;
}

/**
 * i2_s packed-weight → f16 dequant shader.
 *
 * Bindings:
 *   @group(0) @binding(0)  W_packed : array<u32>   — i2_s (16 weights / u32)
 *   @group(0) @binding(1)  W_scale  : array<f16>   — per-row scale [M]
 *   @group(0) @binding(2)  W_out    : array<f16>   — dense fp16 [M × K]
 *   @group(0) @binding(3)  P        : Params
 *
 * Workgroup: 16 × 16 × 1. One f16 weight per thread.
 */
export const WGSL_BITNET_PACKED_DEQUANT = /* wgsl */ `
enable f16;

struct Params {
  M        : u32,
  K        : u32,
  reserved0: u32,
  reserved1: u32,
};

const I2S_WEIGHTS_PER_U32: u32 = 16u;
const I2S_BITS_PER_WEIGHT: u32 = 2u;

@group(0) @binding(0) var<storage, read>          W_packed : array<u32>;
@group(0) @binding(1) var<storage, read>          W_scale  : array<f16>;
@group(0) @binding(2) var<storage, read_write>    W_out    : array<f16>;
@group(0) @binding(3) var<uniform>                P        : Params;

fn unpack_i2s_f16(word: u32, idx: u32) -> f16 {
  let shift: u32 = idx * I2S_BITS_PER_WEIGHT;
  let bits: u32 = (word >> shift) & 3u;
  // 00 → 0 ; 01 → +1 ; 10/11 → -1
  if (bits == 0u) {
    return f16(0.0);
  }
  if (bits == 1u) {
    return f16(1.0);
  }
  return f16(-1.0);
}

@compute @workgroup_size(16, 16, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let m: u32 = gid.x;
  let k: u32 = gid.y;
  if (m >= P.M || k >= P.K) {
    return;
  }

  let w_packed_cols: u32 = (P.K + I2S_WEIGHTS_PER_U32 - 1u) / I2S_WEIGHTS_PER_U32;
  let w_word_idx: u32 = m * w_packed_cols + (k / I2S_WEIGHTS_PER_U32);
  let w_word: u32 = W_packed[w_word_idx];

  let w_val: f16 = unpack_i2s_f16(w_word, k % I2S_WEIGHTS_PER_U32);
  W_out[m * P.K + k] = w_val * W_scale[m];
}
`;

/**
 * Dispatch the i2_s → f16 dequant shader.
 *
 * R0 throws R1a marker. R1a wires the dispatch + numeric test.
 */
export async function dispatchPackedDequant(
  ..._args: unknown[]
): Promise<void> {
  throw new Error(
    "dispatchPackedDequant: R1a — requires isolated WGSL kernel dispatch + bit-identical comparison against `baien-wasm-ternary/src/i2s.rs` scalar dequant. WGSL_BITNET_PACKED_DEQUANT is ready.",
  );
}
