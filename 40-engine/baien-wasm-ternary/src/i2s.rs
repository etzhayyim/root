//! i2_s tensor type — data layout constants + pack/unpack.
//!
//! Mirrors `microsoft/BitNet:src/ggml-bitnet.h` (`GGML_TYPE_I2_S = 40`)
//! and the HF `onnx-community/bitnet-b1.58-2B-4T-bf16-ONNX` packed
//! format. Each byte holds 4 ternary weights, little-endian:
//!
//! ```text
//! bit  7 6 5 4 3 2 1 0
//!      w3| w2| w1| w0
//! ```
//!
//! Each 2-bit slot encodes:
//!
//! | 2-bit | weight |
//! |---|---|
//! | `00` | `0` |
//! | `01` | `+1` |
//! | `10` | `-1` |
//! | `11` | `-1` (reserved/equivalent — upstream maps both `10` and `11` to `-1`) |
//!
//! Gate G3 (ADR-2605263300): these constants MUST match
//! `orgs/etzhayyim/com-etzhayyim-ameno/src/inference/kernels/bitlinear-forward.ts` and
//! `bitnet-packed-dequant.ts` byte-for-byte.

/// Weights per byte. **Compile-time invariant.**
pub const I2S_WEIGHTS_PER_BYTE: usize = 4;

/// Bits per weight. **Compile-time invariant.**
pub const I2S_BITS_PER_WEIGHT: u32 = 2;

/// Weights per u32 word (used by the WGSL shader binding). **Compile-time invariant.**
pub const I2S_WEIGHTS_PER_U32: usize = 16;

/// q8_0 block size. Matches llama.cpp / bitnet.cpp's `Q8_0_BLOCKSIZE`.
pub const Q8_BLOCK_SIZE: usize = 32;

/// Unpack one ternary weight from a packed byte. `idx ∈ [0, 4)`.
/// Returns `-1`, `0`, or `+1` as `i8` (sign-extended at the caller).
#[inline]
pub fn unpack_i2s_byte(byte: u8, idx: usize) -> i8 {
    debug_assert!(idx < I2S_WEIGHTS_PER_BYTE);
    let shift = (idx as u32) * I2S_BITS_PER_WEIGHT;
    let bits = (byte >> shift) & 0b11;
    match bits {
        0b00 => 0,
        0b01 => 1,
        // 0b10 and 0b11 both → -1 (mirrors upstream behaviour).
        _ => -1,
    }
}

/// Unpack one ternary weight from a packed u32 word. `idx ∈ [0, 16)`.
/// Used by the WGSL shader binding contract.
#[inline]
pub fn unpack_i2s_u32(word: u32, idx: usize) -> i8 {
    debug_assert!(idx < I2S_WEIGHTS_PER_U32);
    let shift = (idx as u32) * I2S_BITS_PER_WEIGHT;
    let bits = (word >> shift) & 0b11;
    match bits {
        0 => 0,
        1 => 1,
        _ => -1,
    }
}

/// Pack a slice of weights (`-1`, `0`, `+1`) into a byte. The slice
/// MUST have length 4; debug-asserts otherwise. Values outside
/// `{-1, 0, +1}` are clamped: positive → `+1`, negative → `-1`, zero → `0`.
///
/// Used by offline tensor transform tools, not on the hot path.
pub fn pack_i2s_byte(weights: &[i8; I2S_WEIGHTS_PER_BYTE]) -> u8 {
    let mut byte: u8 = 0;
    for (idx, &w) in weights.iter().enumerate() {
        let bits: u8 = if w == 0 {
            0b00
        } else if w > 0 {
            0b01
        } else {
            0b10
        };
        byte |= bits << ((idx as u32) * I2S_BITS_PER_WEIGHT);
    }
    byte
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pack_unpack_roundtrip() {
        let weights: [i8; 4] = [0, 1, -1, 1];
        let packed = pack_i2s_byte(&weights);
        for (idx, &expected) in weights.iter().enumerate() {
            assert_eq!(unpack_i2s_byte(packed, idx), expected);
        }
    }

    #[test]
    fn known_encoding() {
        // [0, +1, -1, +1] → bits w3 w2 w1 w0 = 01 10 01 00 = 0b01100100
        let packed = pack_i2s_byte(&[0, 1, -1, 1]);
        assert_eq!(packed, 0b01_10_01_00);
    }

    #[test]
    fn u32_unpack_matches_byte_unpack() {
        // Build a u32 from 4 bytes and verify slot-aligned unpacks agree.
        let weights_4byte: [i8; 16] = [
            0, 1, -1, 1, // byte 0
            -1, 0, 1, -1, // byte 1
            1, 1, -1, 0, // byte 2
            0, -1, 1, 1, // byte 3
        ];
        let mut word: u32 = 0;
        for byte_idx in 0..4 {
            let mut slice = [0i8; 4];
            slice.copy_from_slice(&weights_4byte[byte_idx * 4..byte_idx * 4 + 4]);
            let b = pack_i2s_byte(&slice);
            word |= (b as u32) << (byte_idx * 8);
        }
        for idx in 0..16 {
            assert_eq!(unpack_i2s_u32(word, idx), weights_4byte[idx], "idx={}", idx);
        }
    }
}
