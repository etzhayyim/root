//! Activation quantizer — absmean → q8 packed.
//!
//! BitNet's BitLinear activation quantizer ([1] §3.1) is **absmean**:
//!
//! ```text
//!     γ = max(|x_i|) / 127         (per-block, q8 has 8-bit signed range)
//!     q_i = clamp(round(x_i / γ), -127, +127)   as i8
//! ```
//!
//! Block size matches llama.cpp's `Q8_0_BLOCKSIZE = 32`. Each block
//! emits one `f16` scale plus 32 `i8` packed values — exactly the
//! `q8_0` on-disk layout, so the activation buffer is directly
//! consumable by the matmul kernel without re-arrangement.
//!
//! R0 (this commit): scalar reference loop. The implementation matches
//! the bitnet.cpp upstream `quantize_row_q8_0_ref` signature.
//! R1c will add a v128 SIMD variant gated by `feature = "simd"`.
//!
//! [1] Wang et al. "BitNet b1.58: Pushing the limits of 1-bit LLMs."
//!     arXiv 2402.17764 (2024).

use crate::i2s::Q8_BLOCK_SIZE;
use half::f16;

/// Per-block q8_0 record. 1 × f16 scale + 32 × i8 values = 34 bytes.
///
/// Matches the bitnet.cpp / llama.cpp `block_q8_0` layout — same field
/// order, same byte size. The `#[repr(C)]` attribute is mandatory so
/// the layout is wire-stable for the WGSL shader binding.
#[repr(C)]
#[derive(Clone, Copy)]
pub struct BlockQ8_0 {
    /// Per-block scale γ.
    pub d: f16,
    /// 32 quantized i8 values.
    pub qs: [i8; Q8_BLOCK_SIZE],
}

impl Default for BlockQ8_0 {
    fn default() -> Self {
        Self {
            d: f16::from_f32(0.0),
            qs: [0; Q8_BLOCK_SIZE],
        }
    }
}

/// Quantize a row of `f32` activations into `q8_0` blocks.
///
/// `input.len()` MUST be a multiple of `Q8_BLOCK_SIZE`. `output.len()`
/// MUST equal `input.len() / Q8_BLOCK_SIZE`.
///
/// Returns the number of blocks written, matching the upstream
/// `quantize_row_q8_0_ref` convention.
pub fn quantize_row_q8_0_ref(input: &[f32], output: &mut [BlockQ8_0]) -> usize {
    let n_blocks = input.len() / Q8_BLOCK_SIZE;
    assert_eq!(
        input.len() % Q8_BLOCK_SIZE,
        0,
        "quantize_row_q8_0_ref: input length must be a multiple of {Q8_BLOCK_SIZE}",
    );
    assert_eq!(
        output.len(),
        n_blocks,
        "quantize_row_q8_0_ref: output blocks ({}) must equal input.len()/{} ({})",
        output.len(),
        Q8_BLOCK_SIZE,
        n_blocks,
    );

    for (b, block) in output.iter_mut().take(n_blocks).enumerate() {
        let chunk = &input[b * Q8_BLOCK_SIZE..(b + 1) * Q8_BLOCK_SIZE];

        // Absmean: γ = max(|x_i|) / 127.
        let mut absmax: f32 = 0.0;
        for &x in chunk {
            let a = x.abs();
            if a > absmax {
                absmax = a;
            }
        }
        let scale: f32 = if absmax > 0.0 {
            absmax / 127.0
        } else {
            1.0 // degenerate block — all zeros; pick any non-zero scale.
        };
        let inv_scale: f32 = 1.0 / scale;

        block.d = f16::from_f32(scale);
        for (i, &x) in chunk.iter().enumerate() {
            let q = (x * inv_scale).round();
            // i8 range is [-128, 127], but q8_0 uses [-127, 127] to keep
            // ±symmetric range; clamp accordingly.
            let qc = q.clamp(-127.0, 127.0) as i32;
            block.qs[i] = qc as i8;
        }
    }
    n_blocks
}

/// Dequantize a single q8_0 block back to `f32`. Used by the scalar
/// reference matmul to validate the round-trip; not on the hot path.
pub fn dequantize_block_q8_0_ref(block: &BlockQ8_0, output: &mut [f32; Q8_BLOCK_SIZE]) {
    let scale: f32 = block.d.to_f32();
    for i in 0..Q8_BLOCK_SIZE {
        output[i] = block.qs[i] as f32 * scale;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_within_quantization_error() {
        // Random-ish input; check that |dequant(quant(x)) - x| < scale.
        let mut input: Vec<f32> = (0..Q8_BLOCK_SIZE)
            .map(|i| ((i as f32) * 0.137).sin() * 3.0)
            .collect();
        // Push the absmax to a known value.
        input[7] = 4.0;

        let mut blocks = vec![BlockQ8_0::default(); 1];
        quantize_row_q8_0_ref(&input, &mut blocks);
        let scale = blocks[0].d.to_f32();

        let mut out = [0.0f32; Q8_BLOCK_SIZE];
        dequantize_block_q8_0_ref(&blocks[0], &mut out);

        for i in 0..Q8_BLOCK_SIZE {
            let err = (input[i] - out[i]).abs();
            assert!(
                err < scale + 1e-6,
                "i={} input={} out={} err={} scale={}",
                i,
                input[i],
                out[i],
                err,
                scale
            );
        }
    }

    #[test]
    fn absmax_is_127_after_quant() {
        let input: Vec<f32> = vec![0.0; Q8_BLOCK_SIZE];
        let mut input = input;
        input[3] = 1.0;
        let mut blocks = vec![BlockQ8_0::default(); 1];
        quantize_row_q8_0_ref(&input, &mut blocks);
        // The non-zero element should land at ±127 (or close).
        assert_eq!(blocks[0].qs[3], 127);
    }

    #[test]
    fn zero_input_is_zero_block() {
        let input: Vec<f32> = vec![0.0; Q8_BLOCK_SIZE];
        let mut blocks = vec![BlockQ8_0::default(); 1];
        quantize_row_q8_0_ref(&input, &mut blocks);
        for &q in &blocks[0].qs {
            assert_eq!(q, 0);
        }
    }
}
