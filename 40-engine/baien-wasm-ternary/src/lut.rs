//! LUT precompute — stub in R0, full in R1c.
//!
//! Mirrors `microsoft/BitNet:src/ggml-bitnet-lut.cpp`. The LUT path
//! amortizes the inner-loop `i2 × i8` multiply by precomputing the
//! sum of every 4-weight ternary tile against every 4-element
//! activation pattern, so the matmul becomes a sequence of LUT
//! gathers + adds rather than packed multiplies. On wasm32 without
//! true SIMD `i8x16.dot_i8x16_i7x16_add_s` (a Wasm SIMD relaxed
//! extension still in proposal), the LUT path is the best route to
//! competitive throughput.
//!
//! R0: the [`Lut`] struct exists but is **uninitialised** — any
//! method that depends on the LUT contents panics with an R1c
//! marker. This file exists at R0 so the public surface (sizes,
//! signatures) is pinned and downstream callers (matmul.rs,
//! api.rs) can wire against a stable type today.

/// Number of distinct 4-weight ternary tiles. With slots `{-1, 0, +1}`,
/// each weight is encoded in 2 bits (00, 01, 10/11), but bitnet.cpp's
/// LUT collapses `10` and `11` to the same `-1` entry, so the
/// effective dictionary size is `3^4 = 81`. Upstream allocates
/// `4^4 = 256` entries so the index is a direct 8-bit unpack;
/// matching that here.
pub const LUT_TILE_ENTRIES: usize = 256;

/// LUT precompute table. R0 = uninitialised (the `init()` method
/// flips the `initialised` flag without populating the table).
#[derive(Clone)]
pub struct Lut {
    initialised: bool,
    // R1c: `tiles: [[i32; LUT_TILE_ENTRIES]; ...]`
    // — sized by activation vocabulary chunk; deferred.
}

impl Default for Lut {
    fn default() -> Self {
        Self::new()
    }
}

impl Lut {
    /// Construct an uninitialised LUT.
    pub fn new() -> Self {
        Self { initialised: false }
    }

    /// Initialise the LUT. R0 sets the flag and returns; R1c populates
    /// the `tiles` table.
    ///
    /// Idempotent. Returns 0 on success.
    pub fn init(&mut self) -> i32 {
        self.initialised = true;
        0
    }

    /// Whether the LUT has been initialised.
    pub fn is_initialised(&self) -> bool {
        self.initialised
    }
}
