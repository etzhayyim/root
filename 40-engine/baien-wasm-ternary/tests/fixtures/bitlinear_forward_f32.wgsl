// Test-only fixture — f32 variant of bitlinear_forward.wgsl.
//
// Why: as of wgpu 24 / naga 24, the `enable f16;` WGSL extension is
// NOT YET IMPLEMENTED by Naga (gfx-rs/wgpu#4384). The production
// shader at `shaders/bitlinear_forward.wgsl` compiles cleanly in real
// browser WebGPU (Chrome 113+ / Safari 17+ / Firefox 121+) but not
// through Naga's WGSL → MSL/SPV translator that wgpu uses on native.
//
// This fixture is the SAME ALGORITHM with `f16` replaced by `f32` for
// the intermediate compute + storage. The R1a test:
//
//   1. Compiles + runs THIS fixture through wgpu/naga.
//   2. Reads back f32 outputs.
//   3. Converts to f16 host-side (matching what the production f16
//      shader would do at the final store).
//   4. Compares against the Rust scalar reference matmul to ±1 ULP fp16.
//
// What this verifies:
//   - i2_s unpack correctness (16 weights per u32, 2-bit slots)
//   - q8 unpack correctness (4 i8 per u32, sign-extension)
//   - i32 partial-sum + block-scaled f32 accumulation
//   - Row-scale × block-scale layout match between WGSL + Rust
//
// What this does NOT verify (covered at R1b via real-browser tests):
//   - f16 intermediate rounding inside the shader
//   - f16 storage rounding at the final `Y[...]` store
//
// When Naga ships the f16 extension (gfx-rs/wgpu#4384 closes), this
// fixture becomes redundant and the test points back to the production
// shader directly. Until then, this is the closest we get to a
// host-side regression net.

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
@group(0) @binding(2) var<storage, read>          W_scale  : array<f32>;
@group(0) @binding(3) var<storage, read>          X_scale  : array<f32>;
@group(0) @binding(4) var<storage, read_write>    Y        : array<f32>;
@group(0) @binding(5) var<uniform>                P        : Params;

fn unpack_i2s(word: u32, idx: u32) -> i32 {
  let shift: u32 = idx * I2S_BITS_PER_WEIGHT;
  let bits: u32 = (word >> shift) & 3u;
  if (bits == 0u) {
    return 0;
  }
  if (bits == 1u) {
    return 1;
  }
  return -1;
}

fn unpack_i8(word: i32, idx: u32) -> i32 {
  let shift: u32 = idx * 8u;
  let byte: i32 = (word >> shift) & 0xff;
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

  var block_acc: i32 = 0;
  var output_acc: f32 = 0.0;

  let w_packed_cols: u32 = (P.K + I2S_WEIGHTS_PER_U32 - 1u) / I2S_WEIGHTS_PER_U32;

  for (var blk: u32 = 0u; blk < P.kBlocks; blk = blk + 1u) {
    let k_start: u32 = blk * Q8_BLOCK_SIZE;
    let k_end: u32 = min(k_start + Q8_BLOCK_SIZE, P.K);
    block_acc = 0;

    for (var k: u32 = k_start; k < k_end; k = k + 1u) {
      let w_word_idx: u32 = m * w_packed_cols + (k / I2S_WEIGHTS_PER_U32);
      let w_word: u32 = W_packed[w_word_idx];
      let w: i32 = unpack_i2s(w_word, k % I2S_WEIGHTS_PER_U32);

      let x_word_idx: u32 = (k / 4u) * P.N + n;
      let x_word: i32 = X_q8[x_word_idx];
      let x: i32 = unpack_i8(x_word, k % 4u);

      block_acc = block_acc + w * x;
    }

    let xs_idx: u32 = blk * P.N + n;
    output_acc = output_acc + f32(block_acc) * X_scale[xs_idx];
  }

  output_acc = output_acc * W_scale[m];
  Y[m * P.N + n] = output_acc;
}
