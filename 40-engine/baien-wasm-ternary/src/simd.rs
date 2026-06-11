//! v128 SIMD wrappers (R1c) — gated by `feature = "simd"`.
//!
//! R0: the module exists so the public surface is pinned. The actual
//! intrinsic wrappers + the SIMD-fast matmul replacement land in R1c
//! under a follow-up ADR.
//!
//! Why these wrappers exist as a separate module: the BitNet ternary
//! × q8 inner loop has a popcount-based fast path
//! (`(w_pos - w_neg) · x` where `w_pos = popcount(w_bits & 01010101)`
//! and `w_neg = popcount(w_bits & 10101010)`). On wasm32 the relaxed
//! SIMD `i8x16.dot_i8x16_i7x16_add_s` is still a proposal; until it
//! ships universally we ride `wide::i8x16` portable intrinsics.

#[cfg(feature = "simd")]
pub fn popcount_i2s_partial_sum_stub() {
    // Placeholder: R1c lands the real popcount kernel.
    unimplemented!(
        "popcount_i2s_partial_sum: R1c — wide::i8x16 popcount fast path \
         (see ADR-2605263300 §10 R-roadmap row R1c)"
    );
}

/// Whether this build was compiled with the `simd` feature. Mirrors
/// the same logic exposed via the wasm-bindgen `has_simd()` export.
pub const fn compiled_with_simd() -> bool {
    cfg!(feature = "simd")
}
