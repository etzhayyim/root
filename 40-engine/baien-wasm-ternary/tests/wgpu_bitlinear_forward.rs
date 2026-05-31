//! ADR-2605263400 R1a — isolated WGSL BitLinear forward kernel test.
//!
//! Compares a GPU dispatch against the Rust scalar reference matmul
//! (`crate::matmul::mul_mat_i2s_q8_f16_ref`).
//!
//! ## Why this test uses an f32 fixture, not the production f16 shader
//!
//! The production shader at `shaders/bitlinear_forward.wgsl` declares
//! `enable f16;` — which **Naga (the WGSL parser wgpu uses on native)
//! does not yet implement** (gfx-rs/wgpu#4384). Real browsers (Chrome
//! 113+ / Safari 17+ / Firefox 121+) compile the production shader
//! cleanly, but `cargo test` running through native wgpu/naga rejects
//! it with "f16 enable-extension is not yet supported".
//!
//! We therefore run an **algorithm-identical f32 fixture** at
//! `tests/fixtures/bitlinear_forward_f32.wgsl`. The test:
//!
//!   1. Compiles + runs the f32 fixture.
//!   2. Reads back f32 outputs.
//!   3. Converts to f16 host-side (mirrors what the production f16
//!      shader does at its final store).
//!   4. Compares against the Rust scalar reference matmul (which also
//!      ends at f16) to ±1 ULP fp16.
//!
//! What this verifies:
//!   - i2_s unpack (16 weights per u32, 2-bit slots).
//!   - q8 unpack (4 i8 per u32, sign-extension).
//!   - i32 inner accumulation + block-scaled f32 accumulation.
//!   - Row-scale × block-scale layout match between WGSL + Rust.
//!
//! What this does NOT verify (covered at R1b via real-browser tests):
//!   - f16 rounding inside the shader (the f32→f16 conversion happens
//!     host-side here, in a known-good fp16 library).
//!
//! Tolerance: ±1 ULP fp16 element-wise (gate G4).
//!
//! Graceful skip on no GPU adapter (CI-friendly): prints "skipping"
//! and returns. Tests pass on machines without a GPU.

use baien_wasm_ternary::{
    api::ggml_bitnet_init,
    i2s::{pack_i2s_byte, I2S_WEIGHTS_PER_BYTE},
    matmul::mul_mat_i2s_q8_f16_ref,
    quantize::{quantize_row_q8_0_ref, BlockQ8_0},
};
use bytemuck::{Pod, Zeroable};
use half::f16;
use std::borrow::Cow;
use wgpu::util::DeviceExt;

// f32 fixture — see top-of-file docstring for why we don't run the
// production f16 shader here.
const WGSL_BITLINEAR_FORWARD_F32: &str =
    include_str!("fixtures/bitlinear_forward_f32.wgsl");

/// Params struct uploaded as a uniform. Matches the WGSL `struct Params`
/// declaration in `shaders/bitlinear_forward.wgsl` (6 × u32, naturally
/// aligned). `#[repr(C)]` is mandatory so `bytemuck::cast_slice` produces
/// the GPU-side bytes verbatim.
#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable, Debug)]
struct Params {
    m: u32,
    n: u32,
    k: u32,
    k_blocks: u32,
    reserved0: u32,
    reserved1: u32,
}

/// Try to acquire a wgpu adapter + device with the `SHADER_F16`
/// feature. Returns `None` if no suitable adapter exists (CI without
/// a GPU, or the host's adapter doesn't advertise shader-f16).
async fn create_device() -> Option<(wgpu::Device, wgpu::Queue)> {
    let instance = wgpu::Instance::new(&wgpu::InstanceDescriptor {
        backends: wgpu::Backends::PRIMARY,
        ..Default::default()
    });
    let adapter = instance
        .request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            compatible_surface: None,
            force_fallback_adapter: false,
        })
        .await?;
    // We do NOT require SHADER_F16 here — the test fixture is f32-only
    // because Naga doesn't yet parse `enable f16;` (see top-of-file).
    let (device, queue) = adapter
        .request_device(
            &wgpu::DeviceDescriptor {
                label: Some("baien-wasm-ternary bitlinear forward test"),
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::default(),
                memory_hints: wgpu::MemoryHints::default(),
            },
            None,
        )
        .await
        .ok()?;
    Some((device, queue))
}

/// Pack a row of `i8` weights (each in `{-1, 0, +1}`) into the i2_s
/// byte stream the WGSL shader binding expects. Returns one byte per
/// `I2S_WEIGHTS_PER_BYTE` (= 4) input weights.
fn pack_row_to_i2s(weights: &[i8]) -> Vec<u8> {
    assert_eq!(weights.len() % I2S_WEIGHTS_PER_BYTE, 0);
    let mut out = Vec::with_capacity(weights.len() / I2S_WEIGHTS_PER_BYTE);
    for chunk in weights.chunks_exact(I2S_WEIGHTS_PER_BYTE) {
        let mut tile = [0i8; 4];
        tile.copy_from_slice(chunk);
        out.push(pack_i2s_byte(&tile));
    }
    out
}

/// Compare two f16 values within ±1 ULP. Matches `nextafter`
/// semantics on positive halves and handles the ±0 / signed-zero
/// edge case by special-casing exact bitwise equality first.
fn within_1_ulp_f16(a: f16, b: f16) -> bool {
    if a.to_bits() == b.to_bits() {
        return true;
    }
    let a_bits = a.to_bits() as i32;
    let b_bits = b.to_bits() as i32;
    (a_bits - b_bits).abs() <= 1
}

/// Run the GPU shader and the scalar reference matmul on the same
/// inputs; assert ±1 ULP fp16 agreement element-wise.
///
/// Returns `Ok(())` if everything matches; panics on mismatch (cargo
/// test reports the panic).
async fn run_one_test(
    label: &'static str,
    m_rows: usize,
    k_inner: usize,
    n_cols: usize,
    w_int: &[i8],
    x_f32: &[f32],
) {
    let Some((device, queue)) = create_device().await else {
        eprintln!("[{label}] skipping: no wgpu adapter");
        return;
    };

    assert_eq!(w_int.len(), m_rows * k_inner, "weight shape mismatch");
    assert_eq!(x_f32.len(), k_inner * n_cols, "activation shape mismatch");
    assert_eq!(k_inner % 32, 0, "k_inner must be multiple of Q8_BLOCK_SIZE");

    ggml_bitnet_init();

    // ───── pack weights (row-major i2_s) ─────
    let mut w_packed_bytes: Vec<u8> = Vec::with_capacity(m_rows * k_inner / 4);
    for r in 0..m_rows {
        let row = &w_int[r * k_inner..(r + 1) * k_inner];
        w_packed_bytes.extend(pack_row_to_i2s(row));
    }
    // WGSL reads as `array<u32>` (16 weights / u32 = 4 bytes). Pad to
    // u32 boundary and reinterpret.
    while w_packed_bytes.len() % 4 != 0 {
        w_packed_bytes.push(0);
    }
    let w_packed_u32: Vec<u32> = w_packed_bytes
        .chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();

    // ───── per-row weight scale = 1.0 ─────
    // The Rust scalar reference takes Vec<f16>; the GPU fixture binds
    // f32 storage. Keep both representations so we can feed the
    // scalar matmul AND the GPU dispatch with the same conceptual scale.
    let w_scale_f16: Vec<f16> = vec![f16::from_f32(1.0); m_rows];
    let w_scale_f32: Vec<f32> = vec![1.0; m_rows];

    // ───── quantize activations column-by-column ─────
    let k_blocks = k_inner / 32;
    let mut x_blocks: Vec<BlockQ8_0> = vec![BlockQ8_0::default(); k_blocks * n_cols];
    for n in 0..n_cols {
        // Extract column n from the (k_inner × n_cols) row-major
        // f32 buffer.
        let col_f32: Vec<f32> = (0..k_inner).map(|k| x_f32[k * n_cols + n]).collect();
        let mut blocks_for_col: Vec<BlockQ8_0> = vec![BlockQ8_0::default(); k_blocks];
        quantize_row_q8_0_ref(&col_f32, &mut blocks_for_col);
        for blk in 0..k_blocks {
            x_blocks[blk * n_cols + n] = blocks_for_col[blk];
        }
    }

    // ───── X_q8 GPU buffer: 4 i8 per u32, row-major (k_inner/4 × n_cols) ─────
    let mut x_q8_u32: Vec<u32> = vec![0; (k_inner / 4) * n_cols];
    for n in 0..n_cols {
        for blk in 0..k_blocks {
            let b = &x_blocks[blk * n_cols + n];
            for kk in 0..32 {
                let k_global = blk * 32 + kk;
                let pack_idx = k_global / 4;
                let slot = k_global % 4;
                let qs = b.qs[kk] as u8 as u32;
                x_q8_u32[pack_idx * n_cols + n] |= qs << (slot * 8);
            }
        }
    }

    // ───── X_scale GPU buffer: [kBlocks × n_cols] f32 (test fixture) ─────
    let mut x_scale_f32: Vec<f32> = vec![0.0; k_blocks * n_cols];
    for n in 0..n_cols {
        for blk in 0..k_blocks {
            x_scale_f32[blk * n_cols + n] = x_blocks[blk * n_cols + n].d.to_f32();
        }
    }

    // ───── scalar reference (the contract) ─────
    let mut y_ref: Vec<f16> = vec![f16::from_f32(0.0); m_rows * n_cols];
    mul_mat_i2s_q8_f16_ref(
        &w_packed_bytes,
        &w_scale_f16,
        &x_blocks,
        m_rows,
        k_inner,
        n_cols,
        &mut y_ref,
    );

    // ───── upload GPU buffers ─────
    let buf_w_packed = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("W_packed"),
        contents: bytemuck::cast_slice(&w_packed_u32),
        usage: wgpu::BufferUsages::STORAGE,
    });
    let buf_x_q8 = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("X_q8"),
        contents: bytemuck::cast_slice(&x_q8_u32),
        usage: wgpu::BufferUsages::STORAGE,
    });
    let buf_w_scale = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("W_scale"),
        contents: bytemuck::cast_slice(&w_scale_f32),
        usage: wgpu::BufferUsages::STORAGE,
    });
    let buf_x_scale = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("X_scale"),
        contents: bytemuck::cast_slice(&x_scale_f32),
        usage: wgpu::BufferUsages::STORAGE,
    });
    let output_bytes = (m_rows * n_cols * 4) as u64; // f32 = 4 bytes (test fixture)
    let buf_y = device.create_buffer(&wgpu::BufferDescriptor {
        label: Some("Y"),
        size: output_bytes,
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
        mapped_at_creation: false,
    });
    let buf_readback = device.create_buffer(&wgpu::BufferDescriptor {
        label: Some("readback"),
        size: output_bytes,
        usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
        mapped_at_creation: false,
    });
    let params = Params {
        m: m_rows as u32,
        n: n_cols as u32,
        k: k_inner as u32,
        k_blocks: k_blocks as u32,
        reserved0: 0,
        reserved1: 0,
    };
    let buf_params = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("Params"),
        contents: bytemuck::bytes_of(&params),
        usage: wgpu::BufferUsages::UNIFORM,
    });

    // ───── shader + pipeline ─────
    let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
        label: Some("bitlinear_forward_f32.wgsl (test fixture)"),
        source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(WGSL_BITLINEAR_FORWARD_F32)),
    });
    let pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
        label: Some("bitlinear_forward_pipeline"),
        layout: None,
        module: &shader,
        entry_point: Some("main"),
        compilation_options: wgpu::PipelineCompilationOptions::default(),
        cache: None,
    });

    let bind_group_layout = pipeline.get_bind_group_layout(0);
    let bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
        label: Some("bitlinear_forward_bind_group"),
        layout: &bind_group_layout,
        entries: &[
            wgpu::BindGroupEntry { binding: 0, resource: buf_w_packed.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 1, resource: buf_x_q8.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 2, resource: buf_w_scale.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 3, resource: buf_x_scale.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 4, resource: buf_y.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 5, resource: buf_params.as_entire_binding() },
        ],
    });

    // ───── encode + submit ─────
    let mut encoder = device.create_command_encoder(&wgpu::CommandEncoderDescriptor {
        label: Some("bitlinear_forward_encoder"),
    });
    {
        let mut cpass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
            label: Some("bitlinear_forward_pass"),
            timestamp_writes: None,
        });
        cpass.set_pipeline(&pipeline);
        cpass.set_bind_group(0, &bind_group, &[]);
        // Workgroup is 16×16; dispatch ceil(M/16) × ceil(N/16) workgroups.
        let wg_x = ((m_rows + 15) / 16) as u32;
        let wg_y = ((n_cols + 15) / 16) as u32;
        cpass.dispatch_workgroups(wg_x, wg_y, 1);
    }
    encoder.copy_buffer_to_buffer(&buf_y, 0, &buf_readback, 0, output_bytes);
    queue.submit(Some(encoder.finish()));

    // ───── readback ─────
    let buf_slice = buf_readback.slice(..);
    let (sender, receiver) = futures_intrusive::channel::shared::oneshot_channel();
    buf_slice.map_async(wgpu::MapMode::Read, move |result| {
        let _ = sender.send(result);
    });
    let _ = device.poll(wgpu::Maintain::Wait);
    receiver
        .receive()
        .await
        .expect("oneshot dropped")
        .expect("map_async failed");
    let data = buf_slice.get_mapped_range();
    let y_gpu_f32: Vec<f32> = bytemuck::cast_slice(&data).to_vec();
    drop(data);
    buf_readback.unmap();

    // Host-side f32 → f16 conversion (mirrors what the production f16
    // shader does at its final `Y[...]` store).
    let y_gpu: Vec<f16> = y_gpu_f32.iter().map(|&f| f16::from_f32(f)).collect();

    // ───── compare ±1 ULP fp16 ─────
    for m in 0..m_rows {
        for n in 0..n_cols {
            let idx = m * n_cols + n;
            let g = y_gpu[idx];
            let r = y_ref[idx];
            assert!(
                within_1_ulp_f16(g, r),
                "[{label}] mismatch at ({m},{n}): gpu={} ref={} (bits gpu={:#06x} ref={:#06x})",
                g.to_f32(),
                r.to_f32(),
                g.to_bits(),
                r.to_bits(),
            );
        }
    }
    eprintln!("[{label}] PASS m={m_rows} k={k_inner} n={n_cols}");
}

#[test]
fn t1_alternating_ternary_unit_activations() {
    pollster::block_on(async {
        // M=1, K=32, N=1.
        // Weights = [+1, -1, +1, -1, ...] alternating.
        // Activations = [1.0; 32].
        // Expected ≈ 0.
        let w_int: Vec<i8> = (0..32).map(|i| if i % 2 == 0 { 1 } else { -1 }).collect();
        let x_f32: Vec<f32> = vec![1.0; 32];
        run_one_test("T1", 1, 32, 1, &w_int, &x_f32).await;
    });
}

#[test]
fn t2_all_positive_ramp_activations() {
    pollster::block_on(async {
        // M=1, K=32, N=1.
        // Weights = all +1.
        // Activations = [0, 1, 2, ..., 31].
        // Expected ≈ Σ k = 496 (within q8 quantization error).
        let w_int: Vec<i8> = vec![1; 32];
        let x_f32: Vec<f32> = (0..32).map(|i| i as f32).collect();
        run_one_test("T2", 1, 32, 1, &w_int, &x_f32).await;
    });
}

#[test]
fn t3_multi_row_multi_col_two_blocks() {
    pollster::block_on(async {
        // M=4, K=64, N=4.
        let m_rows = 4;
        let k_inner = 64;
        let n_cols = 4;
        // Deterministic-ish weights ∈ {-1, 0, +1}.
        let w_int: Vec<i8> = (0..m_rows * k_inner)
            .map(|i| (((i as i32 * 37 + 7) % 3) - 1) as i8)
            .collect();
        // Deterministic-ish activations.
        let x_f32: Vec<f32> = (0..k_inner * n_cols)
            .map(|i| ((i as f32 * 0.0173).sin() * 3.0).round() / 8.0)
            .collect();
        run_one_test("T3", m_rows, k_inner, n_cols, &w_int, &x_f32).await;
    });
}

#[test]
fn t4_bitnet_2b_shape_proxy() {
    pollster::block_on(async {
        // M=2, K=128, N=8. Proxy for BitNet 2B inner shape, scaled down
        // 16× to keep the test fast.
        let m_rows = 2;
        let k_inner = 128;
        let n_cols = 8;
        let w_int: Vec<i8> = (0..m_rows * k_inner)
            .map(|i| (((i as i32 * 13 + 5) % 3) - 1) as i8)
            .collect();
        let x_f32: Vec<f32> = (0..k_inner * n_cols)
            .map(|i| ((i as f32 * 0.0091).cos() * 2.5).round() / 4.0)
            .collect();
        run_one_test("T4", m_rows, k_inner, n_cols, &w_int, &x_f32).await;
    });
}
