// BitLinear forward shader — ternary × q8 → f16 matmul.
//
// ADR-2605263300 §5 (authoritative WGSL source).
// ADR-2605263400 §1 (relocated from TS string literal to standalone
// .wgsl file — single source of truth shared by:
//   - orgs/etzhayyim/com-etzhayyim-ameno/src/inference/kernels/bitlinear-forward.ts
//     (via Vite `?raw` import)
//   - 40-engine/baien-wasm-ternary/tests/wgpu_bitlinear_forward.rs
//     (via include_str!)
// ).
//
// Gate R1a-G1 (ADR-2605263400 §8): this file is the ONLY source of
// the WGSL text. Inline string duplication is a revert offence.
//
// Bindings:
//   @group(0) @binding(0)  W_packed  : array<u32>    — i2_s (16 weights/u32)
//   @group(0) @binding(1)  X_q8      : array<i32>    — q8 activations (4 i8/u32)
//   @group(0) @binding(2)  W_scale   : array<f16>    — per-row weight scale [M]
//   @group(0) @binding(3)  X_scale   : array<f16>    — per-block activation scale [kBlocks × N]
//   @group(0) @binding(4)  Y         : array<f16>    — output [M × N]
//   @group(0) @binding(5)  P         : Params
//
// Workgroup: 16 × 16 × 1. One output tile per workgroup.
// Requires `shader-f16` GPUAdapter feature.

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
