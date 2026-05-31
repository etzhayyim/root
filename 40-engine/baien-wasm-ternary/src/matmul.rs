//! BitLinear matmul — scalar reference (R0); v128 SIMD (R1c).
//!
//! Mirrors `microsoft/BitNet:src/ggml-bitnet-mad.cpp`
//! `ggml_bitnet_mul_mat_task_compute`. Forward-only.
//!
//! ```text
//!     Y[m, n] = (Σ_k W_ternary[m, k] · X_q8[k, n] · X_scale[block(k), n])
//!               · W_scale[m]
//! ```
//!
//! where `W_ternary` is i2_s packed (4 weights per byte; each weight
//! ∈ `{-1, 0, +1}`), `X_q8` is q8_0 packed (per-block absmean scale).
//!
//! ## R0: scalar reference (this file)
//!
//! Plain triple loop over (m, n, k) with on-the-fly i2_s unpack. No
//! LUT, no SIMD. **This is the numerical contract** (gate G4) —
//! every R1c SIMD impl + every WGSL impl must agree with it within
//! ±1 ULP fp16 on the fixed test vector in `tests/`.
//!
//! ## R1c: v128 SIMD (deferred)
//!
//! Replaces the inner k-loop with `wide::i8x16` chunks, a popcount-
//! based ternary × q8 partial sum, and a LUT-expanded outer loop.

use crate::i2s::{unpack_i2s_byte, I2S_WEIGHTS_PER_BYTE, Q8_BLOCK_SIZE};
use crate::quantize::BlockQ8_0;
use half::f16;

/// Scalar reference BitLinear forward matmul.
///
/// Layout:
///
/// - `w_packed`: row-major i2_s, shape `[m_rows × k_inner / 4]` bytes.
///   `w_packed[m * (k_inner/4) + k_pack]` holds 4 weights at slots
///   `[k_pack*4 .. k_pack*4+4]`.
/// - `w_scale`: per-row weight scale, length `m_rows`.
/// - `x_blocks`: column-major q8_0 blocks, shape
///   `[(k_inner / 32) × n_cols]`. `x_blocks[block * n_cols + n]` is the
///   q8_0 block covering activations `[block*32 .. block*32+32]` at column `n`.
/// - `dst`: row-major output, shape `[m_rows × n_cols]`.
///
/// Asserts on shape mismatch.
pub fn mul_mat_i2s_q8_f16_ref(
    w_packed: &[u8],
    w_scale: &[f16],
    x_blocks: &[BlockQ8_0],
    m_rows: usize,
    k_inner: usize,
    n_cols: usize,
    dst: &mut [f16],
) {
    assert_eq!(
        w_packed.len(),
        m_rows * k_inner / I2S_WEIGHTS_PER_BYTE,
        "mul_mat_i2s_q8_f16_ref: w_packed shape mismatch"
    );
    assert_eq!(
        w_scale.len(),
        m_rows,
        "mul_mat_i2s_q8_f16_ref: w_scale length mismatch"
    );
    assert_eq!(
        k_inner % Q8_BLOCK_SIZE,
        0,
        "mul_mat_i2s_q8_f16_ref: k_inner must be a multiple of {Q8_BLOCK_SIZE}"
    );
    let n_blocks = k_inner / Q8_BLOCK_SIZE;
    assert_eq!(
        x_blocks.len(),
        n_blocks * n_cols,
        "mul_mat_i2s_q8_f16_ref: x_blocks shape mismatch"
    );
    assert_eq!(
        dst.len(),
        m_rows * n_cols,
        "mul_mat_i2s_q8_f16_ref: dst shape mismatch"
    );

    let w_packed_cols = k_inner / I2S_WEIGHTS_PER_BYTE;

    for m in 0..m_rows {
        let row_scale: f32 = w_scale[m].to_f32();
        for n in 0..n_cols {
            // Accumulate per-block, scaled by the block's activation scale,
            // then multiply once by the row's weight scale at the end.
            let mut output_acc: f32 = 0.0;
            for blk in 0..n_blocks {
                let block: &BlockQ8_0 = &x_blocks[blk * n_cols + n];
                let blk_scale: f32 = block.d.to_f32();
                // Inner k-loop over the 32 elements of this block.
                let mut block_acc: i32 = 0;
                for kk in 0..Q8_BLOCK_SIZE {
                    let k = blk * Q8_BLOCK_SIZE + kk;
                    // i2_s unpack: weight at (m, k) is packed in byte
                    // w_packed[m * w_packed_cols + k/4] at slot k%4.
                    let w_byte = w_packed[m * w_packed_cols + (k / I2S_WEIGHTS_PER_BYTE)];
                    let w: i8 = unpack_i2s_byte(w_byte, k % I2S_WEIGHTS_PER_BYTE);
                    let x: i32 = block.qs[kk] as i32;
                    block_acc += (w as i32) * x;
                }
                output_acc += (block_acc as f32) * blk_scale;
            }
            dst[m * n_cols + n] = f16::from_f32(output_acc * row_scale);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::i2s::pack_i2s_byte;
    use crate::quantize::quantize_row_q8_0_ref;

    /// Tiny m=1, k=32 (1 block), n=1 sanity check.
    #[test]
    fn one_block_one_row_one_col() {
        // Weight = [+1, -1, +1, -1, ...] alternating.
        let w_int: Vec<i8> = (0..32).map(|i| if i % 2 == 0 { 1 } else { -1 }).collect();
        // Pack into i2_s bytes.
        let mut w_packed = vec![0u8; 32 / I2S_WEIGHTS_PER_BYTE];
        for (b, byte) in w_packed.iter_mut().enumerate() {
            let mut slice = [0i8; 4];
            slice.copy_from_slice(&w_int[b * 4..b * 4 + 4]);
            *byte = pack_i2s_byte(&slice);
        }
        // Activation = [1.0; 32].
        let x_f32: Vec<f32> = vec![1.0; 32];
        let mut x_blocks = vec![BlockQ8_0::default(); 1];
        quantize_row_q8_0_ref(&x_f32, &mut x_blocks);

        // Expected (in fp32): Σ alternating(+1, -1) · 1.0 = 0.
        let w_scale = vec![f16::from_f32(1.0); 1];
        let mut dst = vec![f16::from_f32(0.0); 1];
        mul_mat_i2s_q8_f16_ref(&w_packed, &w_scale, &x_blocks, 1, 32, 1, &mut dst);

        let got = dst[0].to_f32();
        assert!(got.abs() < 1e-3, "expected ~0, got {got}");
    }

    /// m=1, k=32, n=1 with all-+1 weights against [k for k in 0..32].
    /// Expected: Σ k = 31·32/2 = 496.
    #[test]
    fn all_positive_weights() {
        let w_int: Vec<i8> = vec![1; 32];
        let mut w_packed = vec![0u8; 8];
        for (b, byte) in w_packed.iter_mut().enumerate() {
            let mut slice = [0i8; 4];
            slice.copy_from_slice(&w_int[b * 4..b * 4 + 4]);
            *byte = pack_i2s_byte(&slice);
        }
        let x_f32: Vec<f32> = (0..32).map(|i| i as f32).collect();
        let mut x_blocks = vec![BlockQ8_0::default(); 1];
        quantize_row_q8_0_ref(&x_f32, &mut x_blocks);

        let w_scale = vec![f16::from_f32(1.0); 1];
        let mut dst = vec![f16::from_f32(0.0); 1];
        mul_mat_i2s_q8_f16_ref(&w_packed, &w_scale, &x_blocks, 1, 32, 1, &mut dst);

        let got = dst[0].to_f32();
        // q8 quantization error: scale = 31/127 ≈ 0.244 per element,
        // accumulated over 32 elements → up to ~3.9 absolute error worst-case
        // before applying the scale back; the test allows 4.0.
        assert!((got - 496.0).abs() < 4.0, "expected ~496, got {got}");
    }
}
