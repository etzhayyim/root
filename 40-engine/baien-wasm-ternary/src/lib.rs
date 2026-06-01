//! `baien-wasm-ternary` — BitNet 1.58 ternary i2_s kernel for `wasm32`.
//!
//! This crate is a **clean-room Rust re-implementation** of the
//! **kernel-task layer** of microsoft/BitNet (`bitnet.cpp`). It
//! mirrors the upstream public surface (`ggml_bitnet_*` free
//! functions, `GGML_TYPE_I2_S` tensor type tag, i2_s on-disk byte
//! layout) so the Rust impl is drop-in replaceable with an
//! Emscripten-built upstream WASM port.
//!
//! Authoritative ADR: `90-docs/adr/2605263300-baien-ameno-per-kernel-inference-r0.md`.
//!
//! ## Layout
//!
//! | Module | Purpose |
//! |---|---|
//! | [`i2s`] | i2_s data layout constants + pack/unpack |
//! | [`quantize`] | absmean activation q8 quantizer |
//! | [`lut`] | LUT precompute (R0 = stub, R1c = full) |
//! | [`matmul`] | scalar reference matmul (R0); v128 SIMD (R1c) |
//! | [`simd`] | optional `wide` / `std::simd` wrappers (R1c) |
//! | [`api`] | bitnet.cpp public API mirror (free functions) |
//!
//! ## Gates (ADR-2605263300 §8)
//!
//! - **G2**: API mirror is kernel-task level only. Function names,
//!   tensor type tags, and layout constants match upstream byte-for-byte.
//! - **G3**: i2_s layout (`I2S_WEIGHTS_PER_BYTE = 4`, little-endian
//!   within byte, 2-bit slot encoding) is a compile-time invariant.
//!   Drift between Rust + WGSL = revert.
//! - **G4**: R0 scalar reference matmul is the numerical contract.
//! - **G7**: No vendored upstream source. Clean-room implementation.
//! - **G8**: API names used under Google v. Oracle 2021 fair use.

pub mod api;
pub mod i2s;
pub mod lut;
pub mod matmul;
pub mod quantize;
pub mod simd;

#[cfg(feature = "wasm-export")]
mod wasm_exports {
    use wasm_bindgen::prelude::*;

    /// Module version string. Matches `Cargo.toml`.
    #[wasm_bindgen]
    pub fn version() -> String {
        env!("CARGO_PKG_VERSION").to_string()
    }

    /// Whether the SIMD inner loop is compiled in. R0 returns 0.
    #[wasm_bindgen]
    pub fn has_simd() -> i32 {
        if cfg!(feature = "simd") { 1 } else { 0 }
    }

    /// Whether the LUT-expanded matmul path is compiled in. R0 returns 0.
    #[wasm_bindgen]
    pub fn has_lut() -> i32 {
        if cfg!(feature = "lut") { 1 } else { 0 }
    }

    /// `ggml_bitnet_init` — LUT precompute table setup. Idempotent.
    /// Returns 0 on success. R0 sets an internal flag and returns 0;
    /// the full LUT precompute lands in R1c.
    #[wasm_bindgen]
    pub fn ggml_bitnet_init() -> i32 {
        crate::api::ggml_bitnet_init()
    }

    /// `ggml_bitnet_can_mul_mat` — returns 1 iff the type triple is
    /// `(I2_S, Q8_0, F16)` (the only triple BitNet 1.58 uses).
    #[wasm_bindgen]
    pub fn ggml_bitnet_can_mul_mat(
        src0_ty: i32,
        src1_ty: i32,
        dst_ty: i32,
    ) -> i32 {
        if crate::api::ggml_bitnet_can_mul_mat(src0_ty, src1_ty, dst_ty) {
            1
        } else {
            0
        }
    }
}
