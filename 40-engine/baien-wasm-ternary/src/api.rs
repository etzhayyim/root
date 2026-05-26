//! bitnet.cpp public API mirror — kernel-task layer.
//!
//! Mirrors the function signatures of:
//!
//! - `ggml_bitnet_init`
//! - `ggml_bitnet_can_mul_mat`
//! - `ggml_bitnet_mul_mat_task_compute`
//! - `ggml_bitnet_transform_tensor`
//! - `ggml_bitnet_get_type_traits`
//!
//! from `microsoft/BitNet:src/ggml-bitnet.{h,cpp}`. The names + the
//! tensor-type tag values + the i2_s layout match upstream
//! byte-for-byte; the implementations are clean-room Rust.
//!
//! Gate G2 (kernel-task level only): we do NOT mirror llama.cpp's
//! `llama_init_from_file` / `llama_eval` / `llama_token_to_str` —
//! ameno owns model loading + tokenization via transformers.js.

use crate::i2s::Q8_BLOCK_SIZE;
use crate::matmul::mul_mat_i2s_q8_f16_ref;
use crate::quantize::BlockQ8_0;
use core::sync::atomic::{AtomicBool, Ordering};
use half::f16;

/// Tensor type tags. Values match `ggml-bitnet.h` byte-for-byte
/// (gate G2). Only the i2_s + q8_0 + f16 + f32 entries are populated
/// — these are the only types the BitLinear kernel touches.
pub const GGML_TYPE_F32: i32 = 0;
pub const GGML_TYPE_F16: i32 = 1;
pub const GGML_TYPE_Q8_0: i32 = 8;
/// `GGML_TYPE_I2_S = 40` — matches
/// `microsoft/BitNet:src/ggml-bitnet.h:GGML_TYPE_I2_S`.
pub const GGML_TYPE_I2_S: i32 = 40;

static INITIALISED: AtomicBool = AtomicBool::new(false);

/// `ggml_bitnet_init` — initialise the LUT precompute table.
///
/// Idempotent. Returns 0 on success.
///
/// R0: sets an internal flag and returns 0. The actual LUT
/// precompute lands in R1c (see [`crate::lut::Lut`]).
pub fn ggml_bitnet_init() -> i32 {
    INITIALISED.store(true, Ordering::SeqCst);
    0
}

/// `ggml_bitnet_can_mul_mat` — returns `true` iff the kernel can
/// handle the `(src0, src1) → dst` type triple.
///
/// For BitNet 1.58 the canonical triple is
/// `(GGML_TYPE_I2_S, GGML_TYPE_Q8_0) → GGML_TYPE_F16`.
pub fn ggml_bitnet_can_mul_mat(src0_ty: i32, src1_ty: i32, dst_ty: i32) -> bool {
    src0_ty == GGML_TYPE_I2_S && src1_ty == GGML_TYPE_Q8_0 && dst_ty == GGML_TYPE_F16
}

/// `ggml_bitnet_get_type_traits` — type-traits query.
///
/// Returns `(block_size_elements, block_size_bytes)`. For unsupported
/// types returns `(0, 0)`.
///
/// Block size for i2_s is 1 element conceptually (each weight is its
/// own packed slot) but 1 byte holds 4 weights, so callers should
/// derive byte size as `n_weights / 4`. Returned tuple uses the
/// upstream convention of `1 element / (1/4) byte` rounded to
/// `(1, 1)` for i2_s (caller-multiplied).
pub fn ggml_bitnet_get_type_traits(ty: i32) -> (usize, usize) {
    match ty {
        GGML_TYPE_F32 => (1, 4),
        GGML_TYPE_F16 => (1, 2),
        GGML_TYPE_Q8_0 => (Q8_BLOCK_SIZE, 2 + Q8_BLOCK_SIZE), // f16 scale + 32 i8
        GGML_TYPE_I2_S => (1, 1), // caller multiplies by 1/4
        _ => (0, 0),
    }
}

/// `ggml_bitnet_mul_mat_task_compute` — the BitLinear kernel-task.
///
/// **R0**: scalar reference matmul (forward only). See
/// [`mul_mat_i2s_q8_f16_ref`] for the layout contract.
///
/// **R1c**: SIMD fast path gated by `feature = "simd"`. Same signature,
/// drop-in replacement.
///
/// # Panics
///
/// - If `INITIALISED` is false (caller forgot `ggml_bitnet_init`).
/// - If any of the slice lengths disagree with `(m_rows, k_inner, n_cols)`.
pub fn ggml_bitnet_mul_mat_task_compute(
    w_packed: &[u8],
    w_scale: &[f16],
    x_blocks: &[BlockQ8_0],
    m_rows: usize,
    k_inner: usize,
    n_cols: usize,
    dst: &mut [f16],
) {
    assert!(
        INITIALISED.load(Ordering::SeqCst),
        "ggml_bitnet_mul_mat_task_compute: call ggml_bitnet_init() first"
    );
    mul_mat_i2s_q8_f16_ref(
        w_packed, w_scale, x_blocks, m_rows, k_inner, n_cols, dst,
    );
}

/// `ggml_bitnet_transform_tensor` — offline bf16 → i2_s packing.
///
/// Used by build-time tools (the HF `bitnet-b1.58-2B-4T-bf16-ONNX`
/// pipeline already does this upstream). Exposed here only to keep
/// the public surface consistent with upstream.
///
/// R0: returns the absmean-derived scale and packs 4 weights per
/// output byte using [`crate::i2s::pack_i2s_byte`]. The weight
/// rounding is a sign quantization with a single threshold at
/// `absmean * 0.5` (matches BitNet 1.58 spec [1] §3.2).
///
/// [1] Wang et al. "BitNet b1.58." arXiv 2402.17764.
pub fn ggml_bitnet_transform_tensor(
    bf16_input: &[f32],
    n_rows: usize,
    n_cols: usize,
    packed_out: &mut [u8],
    scale_out: &mut [f16],
) {
    assert_eq!(
        bf16_input.len(),
        n_rows * n_cols,
        "ggml_bitnet_transform_tensor: input shape mismatch"
    );
    assert_eq!(
        n_cols % crate::i2s::I2S_WEIGHTS_PER_BYTE,
        0,
        "ggml_bitnet_transform_tensor: n_cols must be multiple of {}",
        crate::i2s::I2S_WEIGHTS_PER_BYTE
    );
    assert_eq!(
        packed_out.len(),
        n_rows * n_cols / crate::i2s::I2S_WEIGHTS_PER_BYTE,
        "ggml_bitnet_transform_tensor: packed_out shape mismatch"
    );
    assert_eq!(
        scale_out.len(),
        n_rows,
        "ggml_bitnet_transform_tensor: scale_out length mismatch"
    );

    for r in 0..n_rows {
        let row = &bf16_input[r * n_cols..(r + 1) * n_cols];
        // Absmean: γ = mean(|w_i|). Used as the row scale and as the
        // threshold for sign-quantization (round to {-1, 0, +1}).
        let absmean: f32 = row.iter().map(|w| w.abs()).sum::<f32>() / (n_cols as f32);
        let threshold: f32 = absmean * 0.5;
        scale_out[r] = f16::from_f32(absmean);

        let cols_per_byte = crate::i2s::I2S_WEIGHTS_PER_BYTE;
        for c_pack in 0..(n_cols / cols_per_byte) {
            let mut tile = [0i8; 4];
            for slot in 0..cols_per_byte {
                let c = c_pack * cols_per_byte + slot;
                let w = row[c];
                tile[slot] = if w > threshold {
                    1
                } else if w < -threshold {
                    -1
                } else {
                    0
                };
            }
            packed_out[r * (n_cols / cols_per_byte) + c_pack] =
                crate::i2s::pack_i2s_byte(&tile);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn can_mul_mat_canonical_triple() {
        assert!(ggml_bitnet_can_mul_mat(
            GGML_TYPE_I2_S,
            GGML_TYPE_Q8_0,
            GGML_TYPE_F16
        ));
        // Reject everything else.
        assert!(!ggml_bitnet_can_mul_mat(
            GGML_TYPE_F32,
            GGML_TYPE_F32,
            GGML_TYPE_F32
        ));
        assert!(!ggml_bitnet_can_mul_mat(
            GGML_TYPE_I2_S,
            GGML_TYPE_F16,
            GGML_TYPE_F16
        ));
    }

    #[test]
    fn init_is_idempotent() {
        assert_eq!(ggml_bitnet_init(), 0);
        assert_eq!(ggml_bitnet_init(), 0);
    }

    #[test]
    fn type_traits_q8_block_layout() {
        let (elems, bytes) = ggml_bitnet_get_type_traits(GGML_TYPE_Q8_0);
        assert_eq!(elems, Q8_BLOCK_SIZE);
        // f16 scale (2 bytes) + 32 i8 = 34 bytes per block.
        assert_eq!(bytes, 34);
    }

    #[test]
    fn transform_tensor_roundtrip_sign_threshold() {
        // Row of mixed magnitudes — verify the {-1, 0, +1} threshold.
        let n_cols = 8;
        let row: Vec<f32> = vec![0.0, 0.05, 0.5, -0.5, 1.0, -1.0, 0.0, 0.0];
        // absmean = (0 + 0.05 + 0.5 + 0.5 + 1.0 + 1.0 + 0 + 0) / 8 = 0.38125
        // threshold = 0.190625
        // Expected: [0, 0, +1, -1, +1, -1, 0, 0]
        let mut packed = vec![0u8; n_cols / 4];
        let mut scale = vec![f16::from_f32(0.0); 1];
        ggml_bitnet_transform_tensor(&row, 1, n_cols, &mut packed, &mut scale);

        let expected: [i8; 8] = [0, 0, 1, -1, 1, -1, 0, 0];
        for c in 0..n_cols {
            let byte = packed[c / 4];
            let w = crate::i2s::unpack_i2s_byte(byte, c % 4);
            assert_eq!(w, expected[c], "c={}", c);
        }
    }
}
