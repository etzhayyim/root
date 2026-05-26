// i2_s → f16 dequant shader — standalone tile-dense expansion.
//
// ADR-2605263300 §5 (authoritative WGSL source).
// ADR-2605263400 §1 (relocated from TS string literal to standalone
// .wgsl file — single source of truth).
//
// Used as:
//   1. Debug-only fallback for transformers.js layer-replacement (R1b)
//      when the adapter advertises insufficient
//      maxComputeWorkgroupStorageSize for the fused BitLinear kernel
//      — we dequant once, then submit a generic fp16 GEMM.
//   2. Correctness oracle for the SIMD path: dequant a tile in shader,
//      compare against the scalar Rust dequant, expect bit-identical.
//
// Gate R1a-G1 (ADR-2605263400 §8): single source of truth.

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
