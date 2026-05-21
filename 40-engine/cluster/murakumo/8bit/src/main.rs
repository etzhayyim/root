use std::fs::File;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Instant;

use anyhow::{Context, Result};
use arrow_array::{
    ArrayRef, BooleanArray, Int8Array, Int32Array, RecordBatch, StringArray, UInt32Array,
    UInt8Array,
};
use arrow_ipc::reader::FileReader;
use arrow_ipc::writer::FileWriter;
use arrow_schema::{DataType, Field, Schema};
use bytemuck::{Pod, Zeroable};
use clap::{Parser, Subcommand};
use half::{bf16, f16};
use serde::Serialize;
use wgpu::util::DeviceExt;

#[derive(Parser)]
#[command(name = "murakumo-8bit")]
#[command(about = "Pure int8 fixed-point training sandbox")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    TrainToy {
        #[arg(long, default_value_t = 200)]
        steps: usize,
        #[arg(long, default_value_t = 8)]
        input_dim: usize,
        #[arg(long, default_value_t = 4)]
        output_dim: usize,
        #[arg(long, default_value_t = 32)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value = "stochastic")]
        rounding: String,
        #[arg(long, default_value = "max")]
        scale_mode: String,
        #[arg(long, default_value = "adam")]
        optimizer: String,
        #[arg(long, default_value_t = 5)]
        lr_numerator: i32,
        #[arg(long)]
        out: PathBuf,
    },
    TrainRecurrent {
        #[arg(long, default_value_t = 64)]
        steps: usize,
        #[arg(long, default_value_t = 6)]
        input_dim: usize,
        #[arg(long, default_value_t = 4)]
        hidden_dim: usize,
        #[arg(long, default_value_t = 6)]
        seq_len: usize,
        #[arg(long, default_value_t = 16)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value = "stochastic")]
        rounding: String,
        #[arg(long, default_value = "max")]
        scale_mode: String,
        #[arg(long)]
        state_scale_mode: Option<String>,
        #[arg(long, default_value = "adam")]
        optimizer: String,
        #[arg(long, default_value_t = 5)]
        lr_numerator: i32,
        #[arg(long)]
        out: PathBuf,
    },
    Sweep {
        #[arg(long, default_value_t = 64)]
        steps: usize,
        #[arg(long, default_value_t = 8)]
        input_dim: usize,
        #[arg(long, default_value_t = 4)]
        output_dim: usize,
        #[arg(long, default_value_t = 32)]
        batch_size: usize,
        #[arg(long)]
        out: PathBuf,
    },
    SweepRecurrent {
        #[arg(long, default_value_t = 32)]
        steps: usize,
        #[arg(long, default_value_t = 6)]
        input_dim: usize,
        #[arg(long, default_value_t = 4)]
        hidden_dim: usize,
        #[arg(long, default_value_t = 6)]
        seq_len: usize,
        #[arg(long, default_value_t = 16)]
        batch_size: usize,
        #[arg(long)]
        out: PathBuf,
    },
    Bench {
        #[arg(long, default_value_t = 64)]
        steps: usize,
        #[arg(long, default_value_t = 8)]
        input_dim: usize,
        #[arg(long, default_value_t = 4)]
        output_dim: usize,
        #[arg(long, default_value_t = 32)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value_t = 1)]
        warmup: usize,
        #[arg(long, default_value_t = 3)]
        repeat: usize,
    },
    BenchRecurrent {
        #[arg(long, default_value_t = 32)]
        steps: usize,
        #[arg(long, default_value_t = 6)]
        input_dim: usize,
        #[arg(long, default_value_t = 4)]
        hidden_dim: usize,
        #[arg(long, default_value_t = 6)]
        seq_len: usize,
        #[arg(long, default_value_t = 16)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value_t = 1)]
        warmup: usize,
        #[arg(long, default_value_t = 3)]
        repeat: usize,
    },
    BenchMambaLite {
        #[arg(long, default_value_t = 16)]
        steps: usize,
        #[arg(long, default_value_t = 8)]
        input_dim: usize,
        #[arg(long, default_value_t = 8)]
        state_dim: usize,
        #[arg(long, default_value_t = 8)]
        seq_len: usize,
        #[arg(long, default_value_t = 8)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value_t = 1)]
        warmup: usize,
        #[arg(long, default_value_t = 3)]
        repeat: usize,
    },
    BenchMamba2FullForward {
        #[arg(long, default_value_t = 16)]
        dim: usize,
        #[arg(long, default_value_t = 4)]
        state_dim: usize,
        #[arg(long, default_value_t = 2)]
        expand: usize,
        #[arg(long, default_value_t = 16)]
        seq_len: usize,
        #[arg(long, default_value_t = 8)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value_t = 1)]
        warmup: usize,
        #[arg(long, default_value_t = 3)]
        repeat: usize,
    },
    BenchMamba2FullForwardWgpu {
        #[arg(long, default_value_t = 16)]
        dim: usize,
        #[arg(long, default_value_t = 4)]
        state_dim: usize,
        #[arg(long, default_value_t = 2)]
        expand: usize,
        #[arg(long, default_value_t = 16)]
        seq_len: usize,
        #[arg(long, default_value_t = 8)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value_t = 1)]
        warmup: usize,
        #[arg(long, default_value_t = 3)]
        repeat: usize,
    },
    BenchMamba2FullForwardFp16Wgpu {
        #[arg(long, default_value_t = 16)]
        dim: usize,
        #[arg(long, default_value_t = 4)]
        state_dim: usize,
        #[arg(long, default_value_t = 2)]
        expand: usize,
        #[arg(long, default_value_t = 16)]
        seq_len: usize,
        #[arg(long, default_value_t = 8)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value_t = 1)]
        warmup: usize,
        #[arg(long, default_value_t = 3)]
        repeat: usize,
    },
    BenchMamba2OutprojTrainWgpu {
        #[arg(long, default_value_t = 16)]
        dim: usize,
        #[arg(long, default_value_t = 4)]
        state_dim: usize,
        #[arg(long, default_value_t = 2)]
        expand: usize,
        #[arg(long, default_value_t = 16)]
        seq_len: usize,
        #[arg(long, default_value_t = 8)]
        batch_size: usize,
        #[arg(long, default_value_t = 8)]
        block_size: usize,
        #[arg(long, default_value_t = 3)]
        lr_numerator: i32,
        #[arg(long, default_value_t = 1)]
        warmup: usize,
        #[arg(long, default_value_t = 3)]
        repeat: usize,
    },
    Inspect {
        #[arg(long)]
        input: PathBuf,
    },
}

#[derive(Clone, Copy, Debug, Serialize)]
struct IntScale {
    numerator: i32,
    shift: u8,
}

impl IntScale {
    fn new(numerator: i32, shift: u8) -> Self {
        Self {
            numerator: numerator.max(1),
            shift,
        }
    }

    fn apply_i32(self, value: i32) -> i32 {
        (value * self.numerator) >> self.shift
    }

    fn quantize_i32(self, value: i32, rng: &mut Lcg64, stochastic_rounding: bool) -> i8 {
        let scaled = value << self.shift;
        let mut q = scaled / self.numerator;
        let rem = scaled.saturating_abs() % self.numerator;
        if stochastic_rounding && rem > 0 {
            let threshold = (rem as u64).saturating_mul(u32::MAX as u64) / self.numerator as u64;
            if rng.next_u32() as u64 <= threshold {
                q += scaled.signum();
            }
        }
        q.clamp(i8::MIN as i32, i8::MAX as i32) as i8
    }

    fn dequantize_i8(self, value: i8) -> i32 {
        (value as i32 * self.numerator) >> self.shift
    }

    fn quantize_i32_to_i16(self, value: i32, rng: &mut Lcg64, stochastic_rounding: bool) -> i16 {
        let scaled = value << self.shift;
        let mut q = scaled / self.numerator;
        let rem = scaled.saturating_abs() % self.numerator;
        if stochastic_rounding && rem > 0 {
            let threshold = (rem as u64).saturating_mul(u32::MAX as u64) / self.numerator as u64;
            if rng.next_u32() as u64 <= threshold {
                q += scaled.signum();
            }
        }
        q.clamp(i16::MIN as i32, i16::MAX as i32) as i16
    }

    fn dequantize_i16(self, value: i16) -> i32 {
        (value as i32 * self.numerator) >> self.shift
    }
}

#[derive(Clone, Debug, Serialize)]
struct BlockwiseTensorI8 {
    name: String,
    rows: usize,
    cols: usize,
    block_size: usize,
    scales: Vec<IntScale>,
    values: Vec<i8>,
}

impl BlockwiseTensorI8 {
    fn zeros(name: &str, rows: usize, cols: usize, block_size: usize, scale: IntScale) -> Self {
        let len = rows * cols;
        let blocks = len.div_ceil(block_size);
        Self {
            name: name.to_string(),
            rows,
            cols,
            block_size,
            scales: vec![scale; blocks],
            values: vec![0; len],
        }
    }

    fn from_seeded(
        name: &str,
        rows: usize,
        cols: usize,
        block_size: usize,
        scale: IntScale,
        seed: i32,
    ) -> Self {
        let mut tensor = Self::zeros(name, rows, cols, block_size, scale);
        for (i, value) in tensor.values.iter_mut().enumerate() {
            let raw = (((i as i32 + 1) * 17 + seed * 13) % 41) - 20;
            *value = raw.clamp(-48, 48) as i8;
        }
        tensor
    }

    fn get(&self, row: usize, col: usize) -> i8 {
        self.values[row * self.cols + col]
    }

    fn set(&mut self, row: usize, col: usize, value: i8) {
        self.values[row * self.cols + col] = value;
    }

    fn len(&self) -> usize {
        self.values.len()
    }

    fn block_idx(&self, flat_idx: usize) -> usize {
        flat_idx / self.block_size
    }

    fn scale_for(&self, flat_idx: usize) -> IntScale {
        self.scales[self.block_idx(flat_idx)]
    }

    fn saturation_count(&self) -> usize {
        self.values
            .iter()
            .filter(|&&v| v == i8::MIN || v == i8::MAX)
            .count()
    }
}

#[derive(Clone, Debug)]
struct BlockwiseTensorI16 {
    name: String,
    rows: usize,
    cols: usize,
    block_size: usize,
    scales: Vec<IntScale>,
    values: Vec<i16>,
}

impl BlockwiseTensorI16 {
    fn zeros(name: &str, rows: usize, cols: usize, block_size: usize, scale: IntScale) -> Self {
        let len = rows * cols;
        let blocks = len.div_ceil(block_size);
        Self {
            name: name.to_string(),
            rows,
            cols,
            block_size,
            scales: vec![scale; blocks],
            values: vec![0; len],
        }
    }

    fn len(&self) -> usize {
        self.values.len()
    }

    fn scale_for(&self, flat_idx: usize) -> IntScale {
        self.scales[flat_idx / self.block_size]
    }

    fn saturation_count(&self) -> usize {
        self.values
            .iter()
            .filter(|&&v| v == i16::MIN || v == i16::MAX)
            .count()
    }
}

#[derive(Debug, Serialize)]
struct TrainStats {
    steps: usize,
    block_size: usize,
    stochastic_rounding: bool,
    optimizer: String,
    scale_mode: String,
    v_scale_mode: String,
    grad_sq_scale_numerator: i32,
    grad_sq_scale_shift: u8,
    beta2_numerator: i32,
    beta2_shift: u8,
    v_quant_scheme: String,
    denom_mode: String,
    denom_shift: u8,
    lr_numerator: i32,
    loss_l1_sum: i64,
    nonzero_weight_updates: usize,
    zeroed_weight_updates: usize,
    nonzero_momentum_updates: usize,
    zeroed_momentum_updates: usize,
    nonzero_v_updates: usize,
    zeroed_v_updates: usize,
    grad_saturation: usize,
    weight_saturation: usize,
    momentum_saturation: usize,
    v_saturation: usize,
}

#[derive(Debug, Serialize)]
struct SweepRow {
    experiment: String,
    block_size: usize,
    rounding: String,
    optimizer: String,
    scale_mode: String,
    state_scale_mode: String,
    v_scale_mode: String,
    grad_sq_scale_numerator: i32,
    grad_sq_scale_shift: u8,
    beta2_numerator: i32,
    beta2_shift: u8,
    v_quant_scheme: String,
    denom_mode: String,
    denom_shift: u8,
    lr_numerator: i32,
    loss_l1_sum: i64,
    nonzero_weight_updates: usize,
    zeroed_weight_updates: usize,
    nonzero_momentum_updates: usize,
    zeroed_momentum_updates: usize,
    nonzero_v_updates: usize,
    zeroed_v_updates: usize,
    nonzero_weight_ratio: f32,
    nonzero_momentum_ratio: f32,
    nonzero_v_ratio: f32,
}

#[derive(Debug, Serialize)]
struct SweepBest {
    experiment: String,
    optimizer: String,
    rounding: String,
    block_size: usize,
    scale_mode: String,
    state_scale_mode: String,
    denom_shift: u8,
    lr_numerator: i32,
    loss_l1_sum: i64,
    nonzero_weight_ratio: f32,
    nonzero_momentum_ratio: f32,
    nonzero_v_ratio: f32,
}

#[derive(Debug, Serialize)]
struct SweepReport {
    rows: Vec<SweepRow>,
    best_overall: SweepBest,
    best_by_optimizer: Vec<SweepBest>,
    findings: Vec<String>,
}

#[derive(Debug, Serialize)]
struct BenchRow {
    optimizer: String,
    precision_family: String,
    avg_ms: f64,
    updates_per_sec: f64,
    bytes_per_param: usize,
    state_bytes: usize,
    bytes_per_update: f64,
    updates_per_sec_per_byte: f64,
    relative_time_vs_best: f64,
    loss_l1_sum: i64,
    nonzero_weight_ratio: f32,
    nonzero_v_ratio: f32,
}

#[derive(Debug, Serialize)]
struct BenchReport {
    experiment: String,
    steps: usize,
    input_dim: usize,
    output_dim: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
    rows: Vec<BenchRow>,
}

#[derive(Debug, Serialize)]
struct MambaLiteBenchRow {
    optimizer: String,
    precision_family: String,
    prefill_avg_ms: f64,
    prefill_tokens_per_sec: f64,
    decode_avg_ms_per_token: f64,
    decode_tokens_per_sec: f64,
    train_avg_ms: f64,
    train_tokens_per_sec: f64,
    state_bytes: usize,
    loss_l1_sum: i64,
    nonzero_weight_ratio: f32,
}

#[derive(Debug, Serialize)]
struct MambaLiteBenchReport {
    experiment: String,
    steps: usize,
    input_dim: usize,
    state_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
    rows: Vec<MambaLiteBenchRow>,
}

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
struct Mamba2FullMeta {
    total_tokens: u32,
    batch_size: u32,
    seq_len: u32,
    dim: u32,
    inner: u32,
    state_dim: u32,
    pad0: u32,
    pad1: u32,
}

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
struct UpdateMeta {
    total: u32,
    sign_step: i32,
    pad0: u32,
    pad1: u32,
}

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
struct SubMeta {
    total: u32,
    pad0: u32,
    pad1: u32,
    pad2: u32,
}

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
struct GradMeta {
    tokens: u32,
    dim: u32,
    inner: u32,
    pad0: u32,
}

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
struct InprojGradMeta {
    tokens: u32,
    dim: u32,
    inner: u32,
    pad0: u32,
}

#[derive(Clone, Copy)]
struct Lcg64 {
    state: u64,
}

impl Lcg64 {
    fn new(seed: u64) -> Self {
        Self { state: seed | 1 }
    }

    fn next_u32(&mut self) -> u32 {
        self.state = self
            .state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        (self.state >> 32) as u32
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::TrainToy {
            steps,
            input_dim,
            output_dim,
            batch_size,
            block_size,
            rounding,
            scale_mode,
            optimizer,
            lr_numerator,
            out,
        } => train_toy(
            steps,
            input_dim,
            output_dim,
            batch_size,
            block_size,
            parse_rounding_mode(&rounding)?,
            parse_scale_mode(&scale_mode)?,
            parse_optimizer(&optimizer)?,
            lr_numerator,
            &out,
        ),
        Command::TrainRecurrent {
            steps,
            input_dim,
            hidden_dim,
            seq_len,
            batch_size,
            block_size,
            rounding,
            scale_mode,
            state_scale_mode,
            optimizer,
            lr_numerator,
            out,
        } => train_recurrent(
            steps,
            input_dim,
            hidden_dim,
            seq_len,
            batch_size,
            block_size,
            parse_rounding_mode(&rounding)?,
            parse_scale_mode(&scale_mode)?,
            match state_scale_mode {
                Some(mode) => parse_scale_mode(&mode)?,
                None => parse_scale_mode(&scale_mode)?,
            },
            parse_optimizer(&optimizer)?,
            lr_numerator,
            &out,
        ),
        Command::Sweep {
            steps,
            input_dim,
            output_dim,
            batch_size,
            out,
        } => sweep_toy(steps, input_dim, output_dim, batch_size, &out),
        Command::SweepRecurrent {
            steps,
            input_dim,
            hidden_dim,
            seq_len,
            batch_size,
            out,
        } => sweep_recurrent(steps, input_dim, hidden_dim, seq_len, batch_size, &out),
        Command::Bench {
            steps,
            input_dim,
            output_dim,
            batch_size,
            block_size,
            warmup,
            repeat,
        } => bench_toy(steps, input_dim, output_dim, batch_size, block_size, warmup, repeat),
        Command::BenchRecurrent {
            steps,
            input_dim,
            hidden_dim,
            seq_len,
            batch_size,
            block_size,
            warmup,
            repeat,
        } => bench_recurrent(
            steps,
            input_dim,
            hidden_dim,
            seq_len,
            batch_size,
            block_size,
            warmup,
            repeat,
        ),
        Command::BenchMambaLite {
            steps,
            input_dim,
            state_dim,
            seq_len,
            batch_size,
            block_size,
            warmup,
            repeat,
        } => bench_mamba_lite(
            steps,
            input_dim,
            state_dim,
            seq_len,
            batch_size,
            block_size,
            warmup,
            repeat,
        ),
        Command::BenchMamba2FullForward {
            dim,
            state_dim,
            expand,
            seq_len,
            batch_size,
            block_size,
            warmup,
            repeat,
        } => bench_mamba2_full_forward(
            dim, state_dim, expand, seq_len, batch_size, block_size, warmup, repeat,
        ),
        Command::BenchMamba2FullForwardWgpu {
            dim,
            state_dim,
            expand,
            seq_len,
            batch_size,
            block_size,
            warmup,
            repeat,
        } => bench_mamba2_full_forward_wgpu(
            dim, state_dim, expand, seq_len, batch_size, block_size, warmup, repeat,
        ),
        Command::BenchMamba2FullForwardFp16Wgpu {
            dim,
            state_dim,
            expand,
            seq_len,
            batch_size,
            block_size,
            warmup,
            repeat,
        } => bench_mamba2_full_forward_fp16_wgpu(
            dim, state_dim, expand, seq_len, batch_size, block_size, warmup, repeat,
        ),
        Command::BenchMamba2OutprojTrainWgpu {
            dim,
            state_dim,
            expand,
            seq_len,
            batch_size,
            block_size,
            lr_numerator,
            warmup,
            repeat,
        } => bench_mamba2_outproj_train_wgpu(
            dim,
            state_dim,
            expand,
            seq_len,
            batch_size,
            block_size,
            lr_numerator,
            warmup,
            repeat,
        ),
        Command::Inspect { input } => inspect_arrow(&input),
    }
}

fn parse_rounding_mode(mode: &str) -> Result<bool> {
    match mode {
        "stochastic" => Ok(true),
        "nearest" => Ok(false),
        other => anyhow::bail!("unsupported --rounding {other}; use stochastic or nearest"),
    }
}

#[derive(Clone, Copy)]
enum ScaleMode {
    Max,
    P75,
    P90,
}

#[derive(Clone, Copy)]
enum Optimizer {
    Adam,
    AdamEf,
    AdamV16,
    AdamV16Soft,
    Fp16Adam,
    Bf16Adam,
    Fp16Momentum,
    Bf16Momentum,
    Fp16Nesterov,
    Bf16Nesterov,
    MomentumSgd,
    MomentumSgdEf,
    NesterovSgd,
    SignSgd,
    SignSgdEf,
    SignSgdMajority,
    Qsgd,
}

fn parse_scale_mode(mode: &str) -> Result<ScaleMode> {
    match mode {
        "max" => Ok(ScaleMode::Max),
        "p75" => Ok(ScaleMode::P75),
        "p90" => Ok(ScaleMode::P90),
        other => anyhow::bail!("unsupported --scale-mode {other}; use max, p75, or p90"),
    }
}

fn parse_optimizer(mode: &str) -> Result<Optimizer> {
    match mode {
        "adam" => Ok(Optimizer::Adam),
        "adam-ef" => Ok(Optimizer::AdamEf),
        "adam-v16" => Ok(Optimizer::AdamV16),
        "adam-v16-soft" => Ok(Optimizer::AdamV16Soft),
        "fp16-adam" => Ok(Optimizer::Fp16Adam),
        "bf16-adam" => Ok(Optimizer::Bf16Adam),
        "fp16-momentum" => Ok(Optimizer::Fp16Momentum),
        "bf16-momentum" => Ok(Optimizer::Bf16Momentum),
        "fp16-nesterov" => Ok(Optimizer::Fp16Nesterov),
        "bf16-nesterov" => Ok(Optimizer::Bf16Nesterov),
        "momentum-sgd" => Ok(Optimizer::MomentumSgd),
        "momentum-sgd-ef" => Ok(Optimizer::MomentumSgdEf),
        "nesterov-sgd" => Ok(Optimizer::NesterovSgd),
        "signsgd" => Ok(Optimizer::SignSgd),
        "signsgd-ef" => Ok(Optimizer::SignSgdEf),
        "signsgd-majority" => Ok(Optimizer::SignSgdMajority),
        "qsgd" => Ok(Optimizer::Qsgd),
        other => anyhow::bail!("unsupported --optimizer {other}; use adam, adam-ef, adam-v16, adam-v16-soft, fp16-adam, bf16-adam, fp16-momentum, bf16-momentum, fp16-nesterov, bf16-nesterov, momentum-sgd, momentum-sgd-ef, nesterov-sgd, signsgd, signsgd-ef, signsgd-majority, or qsgd"),
    }
}

fn scale_mode_name(mode: ScaleMode) -> &'static str {
    match mode {
        ScaleMode::Max => "max",
        ScaleMode::P75 => "p75",
        ScaleMode::P90 => "p90",
    }
}

fn default_denom_shift(optimizer: Optimizer) -> u8 {
    match optimizer {
        Optimizer::AdamV16Soft => 2,
        _ => 0,
    }
}

fn optimizer_bytes_per_param(optimizer: Optimizer) -> usize {
    match optimizer {
        Optimizer::SignSgdEf => 3,
        Optimizer::AdamV16Soft => 4,
        Optimizer::AdamV16 => 4,
        Optimizer::Adam | Optimizer::AdamEf => 3,
        Optimizer::MomentumSgd | Optimizer::MomentumSgdEf | Optimizer::NesterovSgd => 2,
        Optimizer::SignSgd | Optimizer::SignSgdMajority | Optimizer::Qsgd => 1,
        Optimizer::Fp16Momentum | Optimizer::Fp16Nesterov | Optimizer::Bf16Momentum | Optimizer::Bf16Nesterov => 4,
        Optimizer::Fp16Adam | Optimizer::Bf16Adam => 6,
    }
}

fn optimizer_precision_family(optimizer: Optimizer) -> &'static str {
    match optimizer {
        Optimizer::SignSgdEf
        | Optimizer::AdamV16Soft
        | Optimizer::AdamV16
        | Optimizer::Adam
        | Optimizer::AdamEf
        | Optimizer::MomentumSgd
        | Optimizer::MomentumSgdEf
        | Optimizer::NesterovSgd
        | Optimizer::SignSgd
        | Optimizer::SignSgdMajority
        | Optimizer::Qsgd => "int8-family",
        Optimizer::Fp16Adam | Optimizer::Fp16Momentum | Optimizer::Fp16Nesterov => "fp16",
        Optimizer::Bf16Adam | Optimizer::Bf16Momentum | Optimizer::Bf16Nesterov => "bf16",
    }
}

fn safe_ratio(nonzero: usize, zeroed: usize) -> f32 {
    let total = nonzero + zeroed;
    if total == 0 {
        0.0
    } else {
        nonzero as f32 / total as f32
    }
}

fn score_row(row: &SweepRow) -> (i64, i64, i64) {
    let weight_score = (row.nonzero_weight_ratio * 1_000_000.0).round() as i64;
    let momentum_score = (row.nonzero_momentum_ratio * 1_000_000.0).round() as i64;
    (-row.loss_l1_sum, weight_score, momentum_score)
}

fn to_sweep_best(row: &SweepRow) -> SweepBest {
    SweepBest {
        experiment: row.experiment.clone(),
        optimizer: row.optimizer.clone(),
        rounding: row.rounding.clone(),
        block_size: row.block_size,
        scale_mode: row.scale_mode.clone(),
        state_scale_mode: row.state_scale_mode.clone(),
        denom_shift: row.denom_shift,
        lr_numerator: row.lr_numerator,
        loss_l1_sum: row.loss_l1_sum,
        nonzero_weight_ratio: row.nonzero_weight_ratio,
        nonzero_momentum_ratio: row.nonzero_momentum_ratio,
        nonzero_v_ratio: row.nonzero_v_ratio,
    }
}

fn train_toy(
    steps: usize,
    input_dim: usize,
    output_dim: usize,
    batch_size: usize,
    block_size: usize,
    stochastic_rounding: bool,
    scale_mode: ScaleMode,
    optimizer: Optimizer,
    lr_numerator: i32,
    out: &PathBuf,
) -> Result<()> {
    let artifacts = train_toy_inner(
        steps,
        input_dim,
        output_dim,
        batch_size,
        block_size,
        stochastic_rounding,
        scale_mode,
        optimizer,
        IntScale::new(1, 0),
        IntScale::new(7, 3),
        default_denom_shift(optimizer),
        lr_numerator,
    );
    write_checkpoint(out, &artifacts.tensors, &artifacts.stats)?;
    println!("{}", serde_json::to_string_pretty(&artifacts.stats)?);
    println!("checkpoint: {}", out.display());
    Ok(())
}

fn train_recurrent(
    steps: usize,
    input_dim: usize,
    hidden_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    stochastic_rounding: bool,
    input_scale_mode: ScaleMode,
    state_scale_mode: ScaleMode,
    optimizer: Optimizer,
    lr_numerator: i32,
    out: &PathBuf,
) -> Result<()> {
    let artifacts = train_recurrent_inner(
        steps,
        input_dim,
        hidden_dim,
        seq_len,
        batch_size,
        block_size,
        stochastic_rounding,
        input_scale_mode,
        state_scale_mode,
        optimizer,
        IntScale::new(1, 0),
        IntScale::new(7, 3),
        default_denom_shift(optimizer),
        lr_numerator,
    );
    write_checkpoint(out, &artifacts.tensors, &artifacts.stats)?;
    println!("{}", serde_json::to_string_pretty(&artifacts.stats)?);
    println!("checkpoint: {}", out.display());
    Ok(())
}

fn bench_toy(
    steps: usize,
    input_dim: usize,
    output_dim: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
) -> Result<()> {
    let candidates = [
        Optimizer::SignSgdEf,
        Optimizer::AdamV16Soft,
        Optimizer::Fp16Momentum,
        Optimizer::Bf16Adam,
    ];
    let params = output_dim * input_dim;
    let updates = (steps * params) as f64;
    let mut rows = Vec::new();

    for optimizer in candidates {
        for _ in 0..warmup {
            let _ = train_toy_inner(
                steps,
                input_dim,
                output_dim,
                batch_size,
                block_size,
                true,
                ScaleMode::Max,
                optimizer,
                IntScale::new(1, 0),
                IntScale::new(7, 3),
                default_denom_shift(optimizer),
                3,
            );
        }

        let mut total_ms = 0.0f64;
        let mut last = None;
        for _ in 0..repeat {
            let started = Instant::now();
            let artifacts = train_toy_inner(
                steps,
                input_dim,
                output_dim,
                batch_size,
                block_size,
                true,
                ScaleMode::Max,
                optimizer,
                IntScale::new(1, 0),
                IntScale::new(7, 3),
                default_denom_shift(optimizer),
                3,
            );
            total_ms += started.elapsed().as_secs_f64() * 1000.0;
            last = Some(artifacts.stats);
        }
        let stats = last.context("bench run missing stats")?;
        let avg_ms = total_ms / repeat as f64;
        let updates_per_sec = if avg_ms > 0.0 {
            updates / (avg_ms / 1000.0)
        } else {
            0.0
        };
        let bytes_per_param = optimizer_bytes_per_param(optimizer);
        let state_bytes = params * bytes_per_param;
        let bytes_per_update = if updates > 0.0 {
            state_bytes as f64 / updates
        } else {
            0.0
        };
        rows.push(BenchRow {
            optimizer: stats.optimizer.clone(),
            precision_family: optimizer_precision_family(optimizer).to_string(),
            avg_ms,
            updates_per_sec,
            bytes_per_param,
            state_bytes,
            bytes_per_update,
            updates_per_sec_per_byte: if state_bytes > 0 {
                updates_per_sec / state_bytes as f64
            } else {
                0.0
            },
            relative_time_vs_best: 0.0,
            loss_l1_sum: stats.loss_l1_sum,
            nonzero_weight_ratio: safe_ratio(
                stats.nonzero_weight_updates,
                stats.zeroed_weight_updates,
            ),
            nonzero_v_ratio: safe_ratio(stats.nonzero_v_updates, stats.zeroed_v_updates),
        });
    }

    let best_ms = rows
        .iter()
        .map(|row| row.avg_ms)
        .fold(f64::INFINITY, f64::min);
    for row in &mut rows {
        row.relative_time_vs_best = if best_ms.is_finite() && best_ms > 0.0 {
            row.avg_ms / best_ms
        } else {
            1.0
        };
    }
    rows.sort_by(|a, b| a.avg_ms.partial_cmp(&b.avg_ms).unwrap_or(std::cmp::Ordering::Equal));

    let report = BenchReport {
        experiment: "linear".to_string(),
        steps,
        input_dim,
        output_dim,
        batch_size,
        block_size,
        warmup,
        repeat,
        rows,
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn bench_recurrent(
    steps: usize,
    input_dim: usize,
    hidden_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
) -> Result<()> {
    let candidates = [
        Optimizer::SignSgdEf,
        Optimizer::AdamV16Soft,
        Optimizer::MomentumSgd,
        Optimizer::Adam,
    ];
    let params = hidden_dim * input_dim + hidden_dim * hidden_dim;
    let updates = (steps * params * 2) as f64;
    let mut rows = Vec::new();

    for optimizer in candidates {
        for _ in 0..warmup {
            let _ = train_recurrent_inner(
                steps,
                input_dim,
                hidden_dim,
                seq_len,
                batch_size,
                block_size,
                true,
                ScaleMode::Max,
                ScaleMode::Max,
                optimizer,
                IntScale::new(1, 0),
                IntScale::new(7, 3),
                default_denom_shift(optimizer),
                3,
            );
        }

        let mut total_ms = 0.0f64;
        let mut last = None;
        for _ in 0..repeat {
            let started = Instant::now();
            let artifacts = train_recurrent_inner(
                steps,
                input_dim,
                hidden_dim,
                seq_len,
                batch_size,
                block_size,
                true,
                ScaleMode::Max,
                ScaleMode::Max,
                optimizer,
                IntScale::new(1, 0),
                IntScale::new(7, 3),
                default_denom_shift(optimizer),
                3,
            );
            total_ms += started.elapsed().as_secs_f64() * 1000.0;
            last = Some(artifacts.stats);
        }

        let stats = last.context("recurrent bench run missing stats")?;
        let avg_ms = total_ms / repeat as f64;
        let updates_per_sec = if avg_ms > 0.0 {
            updates / (avg_ms / 1000.0)
        } else {
            0.0
        };
        let bytes_per_param = optimizer_bytes_per_param(optimizer);
        let state_bytes = params * bytes_per_param;
        let bytes_per_update = if updates > 0.0 {
            state_bytes as f64 / updates
        } else {
            0.0
        };
        rows.push(BenchRow {
            optimizer: stats.optimizer.clone(),
            precision_family: optimizer_precision_family(optimizer).to_string(),
            avg_ms,
            updates_per_sec,
            bytes_per_param,
            state_bytes,
            bytes_per_update,
            updates_per_sec_per_byte: if state_bytes > 0 {
                updates_per_sec / state_bytes as f64
            } else {
                0.0
            },
            relative_time_vs_best: 0.0,
            loss_l1_sum: stats.loss_l1_sum,
            nonzero_weight_ratio: safe_ratio(
                stats.nonzero_weight_updates,
                stats.zeroed_weight_updates,
            ),
            nonzero_v_ratio: safe_ratio(stats.nonzero_v_updates, stats.zeroed_v_updates),
        });
    }

    let best_ms = rows
        .iter()
        .map(|row| row.avg_ms)
        .fold(f64::INFINITY, f64::min);
    for row in &mut rows {
        row.relative_time_vs_best = if best_ms.is_finite() && best_ms > 0.0 {
            row.avg_ms / best_ms
        } else {
            1.0
        };
    }
    rows.sort_by(|a, b| a.avg_ms.partial_cmp(&b.avg_ms).unwrap_or(std::cmp::Ordering::Equal));

    let report = BenchReport {
        experiment: "recurrent".to_string(),
        steps,
        input_dim,
        output_dim: hidden_dim,
        batch_size,
        block_size,
        warmup,
        repeat,
        rows,
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn bench_mamba_lite(
    steps: usize,
    input_dim: usize,
    state_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
) -> Result<()> {
    let candidates = [
        Optimizer::SignSgdEf,
        Optimizer::Fp16Momentum,
        Optimizer::Bf16Adam,
    ];
    let mut rows = Vec::new();

    for optimizer in candidates {
        for _ in 0..warmup {
            let _ = mamba_lite_train_step(
                optimizer,
                input_dim,
                state_dim,
                seq_len,
                batch_size,
                block_size,
                3,
            );
            let _ = mamba_lite_prefill(optimizer, input_dim, state_dim, seq_len, batch_size, block_size);
            let _ = mamba_lite_decode(optimizer, input_dim, state_dim, seq_len, batch_size, block_size, 4);
        }

        let mut prefill_ms = 0.0;
        let mut decode_ms = 0.0;
        let mut train_ms = 0.0;
        let mut last_loss = 0i64;
        let mut last_nonzero_weight_ratio = 0.0f32;
        let state_bytes = mamba_lite_state_bytes(optimizer, input_dim, state_dim);

        for _ in 0..repeat {
            let started = Instant::now();
            let _ = mamba_lite_prefill(optimizer, input_dim, state_dim, seq_len, batch_size, block_size);
            prefill_ms += started.elapsed().as_secs_f64() * 1000.0;

            let started = Instant::now();
            let _ = mamba_lite_decode(optimizer, input_dim, state_dim, seq_len, batch_size, block_size, 4);
            decode_ms += started.elapsed().as_secs_f64() * 1000.0;

            let started = Instant::now();
            let stats = mamba_lite_train_step(
                optimizer,
                input_dim,
                state_dim,
                seq_len,
                batch_size,
                block_size,
                3,
            );
            train_ms += started.elapsed().as_secs_f64() * 1000.0;
            last_loss = stats.loss_l1_sum;
            last_nonzero_weight_ratio =
                safe_ratio(stats.nonzero_weight_updates, stats.zeroed_weight_updates);
        }

        let prefill_avg_ms = prefill_ms / repeat as f64;
        let decode_avg_ms = decode_ms / repeat as f64;
        let train_avg_ms = train_ms / repeat as f64;
        let prefill_tokens = (seq_len * batch_size) as f64;
        let decode_tokens = 4.0f64;
        let train_tokens = (steps * seq_len * batch_size) as f64;
        rows.push(MambaLiteBenchRow {
            optimizer: match optimizer {
                Optimizer::SignSgdEf => "signsgd-ef".to_string(),
                Optimizer::Fp16Momentum => "fp16-momentum".to_string(),
                Optimizer::Bf16Adam => "bf16-adam".to_string(),
                _ => unreachable!(),
            },
            precision_family: optimizer_precision_family(optimizer).to_string(),
            prefill_avg_ms,
            prefill_tokens_per_sec: if prefill_avg_ms > 0.0 {
                prefill_tokens / (prefill_avg_ms / 1000.0)
            } else {
                0.0
            },
            decode_avg_ms_per_token: if decode_tokens > 0.0 {
                decode_avg_ms / decode_tokens
            } else {
                0.0
            },
            decode_tokens_per_sec: if decode_avg_ms > 0.0 {
                decode_tokens / (decode_avg_ms / 1000.0)
            } else {
                0.0
            },
            train_avg_ms,
            train_tokens_per_sec: if train_avg_ms > 0.0 {
                train_tokens / (train_avg_ms / 1000.0)
            } else {
                0.0
            },
            state_bytes,
            loss_l1_sum: last_loss,
            nonzero_weight_ratio: last_nonzero_weight_ratio,
        });
    }

    let report = MambaLiteBenchReport {
        experiment: "mamba-lite".to_string(),
        steps,
        input_dim,
        state_dim,
        seq_len,
        batch_size,
        block_size,
        warmup,
        repeat,
        rows,
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn bench_mamba2_full_forward(
    dim: usize,
    state_dim: usize,
    expand: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
) -> Result<()> {
    let candidates = [Optimizer::SignSgdEf, Optimizer::Fp16Momentum, Optimizer::Bf16Adam];
    let mut rows = Vec::new();
    let inner = dim * expand;
    let state_bytes_base = dim * inner * 2 + inner * inner + inner * inner * state_dim * 2 + dim * inner;

    for optimizer in candidates {
        for _ in 0..warmup {
            let _ = mamba2_full_forward_run(optimizer, dim, state_dim, expand, seq_len, batch_size, block_size);
        }

        let mut total_ms = 0.0;
        let mut sink = 0i64;
        for _ in 0..repeat {
            let started = Instant::now();
            sink ^= mamba2_full_forward_run(optimizer, dim, state_dim, expand, seq_len, batch_size, block_size);
            total_ms += started.elapsed().as_secs_f64() * 1000.0;
        }
        let avg_ms = total_ms / repeat as f64;
        let toks = (seq_len * batch_size) as f64;
        rows.push(MambaLiteBenchRow {
            optimizer: match optimizer {
                Optimizer::SignSgdEf => "signsgd-ef".to_string(),
                Optimizer::Fp16Momentum => "fp16-momentum".to_string(),
                Optimizer::Bf16Adam => "bf16-adam".to_string(),
                _ => unreachable!(),
            },
            precision_family: optimizer_precision_family(optimizer).to_string(),
            prefill_avg_ms: avg_ms,
            prefill_tokens_per_sec: if avg_ms > 0.0 { toks / (avg_ms / 1000.0) } else { 0.0 },
            decode_avg_ms_per_token: if seq_len > 0 { avg_ms / seq_len as f64 } else { 0.0 },
            decode_tokens_per_sec: if avg_ms > 0.0 { seq_len as f64 / (avg_ms / 1000.0) } else { 0.0 },
            train_avg_ms: 0.0,
            train_tokens_per_sec: 0.0,
            state_bytes: state_bytes_base * optimizer_bytes_per_param(optimizer),
            loss_l1_sum: sink,
            nonzero_weight_ratio: 1.0,
        });
    }

    let report = MambaLiteBenchReport {
        experiment: "mamba2-full-forward-cpu-only".to_string(),
        steps: 1,
        input_dim: dim,
        state_dim,
        seq_len,
        batch_size,
        block_size,
        warmup,
        repeat,
        rows,
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn bench_mamba2_full_forward_wgpu(
    dim: usize,
    state_dim: usize,
    expand: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
) -> Result<()> {
    let runtime = pollster::block_on(WgpuMamba2FullForward::new())?;
    for _ in 0..warmup {
        let _ = runtime.run(dim, state_dim, expand, seq_len, batch_size, block_size)?;
    }
    let mut total_ms = 0.0;
    let mut sink = 0i64;
    for _ in 0..repeat {
        let started = Instant::now();
        sink ^= runtime.run(dim, state_dim, expand, seq_len, batch_size, block_size)?;
        total_ms += started.elapsed().as_secs_f64() * 1000.0;
    }
    let avg_ms = total_ms / repeat as f64;
    let toks = (seq_len * batch_size) as f64;
    let inner = dim * expand;
    let state_bytes_base = dim * inner * 2 + inner * inner + inner * inner * state_dim * 2 + dim * inner;
    let row = MambaLiteBenchRow {
        optimizer: "signsgd-ef".to_string(),
        precision_family: "int8-family-webgpu".to_string(),
        prefill_avg_ms: avg_ms,
        prefill_tokens_per_sec: if avg_ms > 0.0 { toks / (avg_ms / 1000.0) } else { 0.0 },
        decode_avg_ms_per_token: if seq_len > 0 { avg_ms / seq_len as f64 } else { 0.0 },
        decode_tokens_per_sec: if avg_ms > 0.0 { seq_len as f64 / (avg_ms / 1000.0) } else { 0.0 },
        train_avg_ms: 0.0,
        train_tokens_per_sec: 0.0,
        state_bytes: state_bytes_base * optimizer_bytes_per_param(Optimizer::SignSgdEf),
        loss_l1_sum: sink,
        nonzero_weight_ratio: 1.0,
    };
    let report = MambaLiteBenchReport {
        experiment: "mamba2-full-forward-gpu-only".to_string(),
        steps: 1,
        input_dim: dim,
        state_dim,
        seq_len,
        batch_size,
        block_size,
        warmup,
        repeat,
        rows: vec![row],
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn bench_mamba2_full_forward_fp16_wgpu(
    dim: usize,
    state_dim: usize,
    expand: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    warmup: usize,
    repeat: usize,
) -> Result<()> {
    let runtime = pollster::block_on(WgpuMamba2FullForwardFp16::new())?;
    for _ in 0..warmup {
        let _ = runtime.run(dim, state_dim, expand, seq_len, batch_size, block_size)?;
    }
    let mut total_ms = 0.0;
    let mut sink = 0i64;
    for _ in 0..repeat {
        let started = Instant::now();
        sink ^= runtime.run(dim, state_dim, expand, seq_len, batch_size, block_size)?;
        total_ms += started.elapsed().as_secs_f64() * 1000.0;
    }
    let avg_ms = total_ms / repeat as f64;
    let toks = (seq_len * batch_size) as f64;
    let inner = dim * expand;
    let state_bytes_base = dim * inner * 2 + inner * inner + inner * inner * state_dim * 2 + dim * inner;
    let row = MambaLiteBenchRow {
        optimizer: "fp16-momentum".to_string(),
        precision_family: "fp16-webgpu".to_string(),
        prefill_avg_ms: avg_ms,
        prefill_tokens_per_sec: if avg_ms > 0.0 { toks / (avg_ms / 1000.0) } else { 0.0 },
        decode_avg_ms_per_token: if seq_len > 0 { avg_ms / seq_len as f64 } else { 0.0 },
        decode_tokens_per_sec: if avg_ms > 0.0 { seq_len as f64 / (avg_ms / 1000.0) } else { 0.0 },
        train_avg_ms: 0.0,
        train_tokens_per_sec: 0.0,
        state_bytes: state_bytes_base * optimizer_bytes_per_param(Optimizer::Fp16Momentum),
        loss_l1_sum: sink,
        nonzero_weight_ratio: 1.0,
    };
    let report = MambaLiteBenchReport {
        experiment: "mamba2-full-forward-fp16-gpu-only".to_string(),
        steps: 1,
        input_dim: dim,
        state_dim,
        seq_len,
        batch_size,
        block_size,
        warmup,
        repeat,
        rows: vec![row],
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn bench_mamba2_outproj_train_wgpu(
    dim: usize,
    state_dim: usize,
    expand: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    lr_numerator: i32,
    warmup: usize,
    repeat: usize,
) -> Result<()> {
    let runtime = pollster::block_on(WgpuMamba2FullForward::new())?;
    for _ in 0..warmup {
        let _ = mamba2_outproj_train_step_wgpu(
            &runtime,
            dim,
            state_dim,
            expand,
            seq_len,
            batch_size,
            block_size,
            lr_numerator,
        )?;
    }
    let mut total_ms = 0.0;
    let mut last = None;
    for _ in 0..repeat {
        let started = Instant::now();
        last = Some(mamba2_outproj_train_step_wgpu(
            &runtime,
            dim,
            state_dim,
            expand,
            seq_len,
            batch_size,
            block_size,
            lr_numerator,
        )?);
        total_ms += started.elapsed().as_secs_f64() * 1000.0;
    }
    let stats = last.context("missing outproj train stats")?;
    let avg_ms = total_ms / repeat as f64;
    let toks = (seq_len * batch_size) as f64;
    let inner = dim * expand;
    let state_bytes_base = dim * inner * 2 + inner * inner + inner * inner * state_dim * 2 + dim * inner;
    let row = MambaLiteBenchRow {
        optimizer: "signsgd-ef-core".to_string(),
        precision_family: "int8-family-webgpu".to_string(),
        prefill_avg_ms: 0.0,
        prefill_tokens_per_sec: 0.0,
        decode_avg_ms_per_token: 0.0,
        decode_tokens_per_sec: 0.0,
        train_avg_ms: avg_ms,
        train_tokens_per_sec: if avg_ms > 0.0 { toks / (avg_ms / 1000.0) } else { 0.0 },
        state_bytes: state_bytes_base * optimizer_bytes_per_param(Optimizer::SignSgdEf),
        loss_l1_sum: stats.loss_l1_sum,
        nonzero_weight_ratio: safe_ratio(stats.nonzero_weight_updates, stats.zeroed_weight_updates),
    };
    let report = MambaLiteBenchReport {
        experiment: "mamba2-outproj-train-gpu-only".to_string(),
        steps: 1,
        input_dim: dim,
        state_dim,
        seq_len,
        batch_size,
        block_size,
        warmup,
        repeat,
        rows: vec![row],
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn sweep_toy(
    steps: usize,
    input_dim: usize,
    output_dim: usize,
    batch_size: usize,
    out: &PathBuf,
) -> Result<()> {
    let pure_optimizers = [
        Optimizer::Adam,
        Optimizer::AdamEf,
        Optimizer::AdamV16,
        Optimizer::AdamV16Soft,
        Optimizer::MomentumSgd,
        Optimizer::MomentumSgdEf,
        Optimizer::NesterovSgd,
        Optimizer::SignSgd,
        Optimizer::SignSgdEf,
        Optimizer::SignSgdMajority,
        Optimizer::Qsgd,
    ];
    let float_baselines = [
        Optimizer::Fp16Adam,
        Optimizer::Bf16Adam,
        Optimizer::Fp16Momentum,
        Optimizer::Bf16Momentum,
        Optimizer::Fp16Nesterov,
        Optimizer::Bf16Nesterov,
    ];
    let block_sizes = [4usize, 8usize, 16usize];
    let rounding_modes = [true, false];
    let scale_modes = [ScaleMode::Max, ScaleMode::P75, ScaleMode::P90];
    let lr_numerators = [3i32, 5i32, 9i32, 13i32];

    let mut rows = Vec::new();
    let mut run_idx = 0usize;
    for optimizer in pure_optimizers {
        for block_size in block_sizes {
            for stochastic_rounding in rounding_modes {
                for scale_mode in scale_modes {
                    for lr_numerator in lr_numerators {
                        let denom_shifts: &[u8] = if matches!(optimizer, Optimizer::AdamV16Soft) {
                            &[1, 2, 3]
                        } else {
                            &[default_denom_shift(optimizer)]
                        };
                        for &denom_shift in denom_shifts {
                        let grad_sq_scale = if matches!(optimizer, Optimizer::Adam | Optimizer::AdamEf) {
                            if block_size <= 4 {
                                IntScale::new(1, 5)
                            } else {
                                IntScale::new(1, 4)
                            }
                        } else {
                            IntScale::new(1, 0)
                        };
                        let beta2_scale = if matches!(optimizer, Optimizer::Adam | Optimizer::AdamEf) {
                            if lr_numerator >= 9 {
                                IntScale::new(6, 3)
                            } else {
                                IntScale::new(7, 3)
                            }
                        } else {
                            IntScale::new(7, 3)
                        };
                        let tmp =
                            out.with_file_name(format!("{}.run-{run_idx}.arrow", out.display()));
                        run_idx += 1;
                        let artifacts = train_toy_inner(
                            steps,
                            input_dim,
                            output_dim,
                            batch_size,
                            block_size,
                            stochastic_rounding,
                            scale_mode,
                            optimizer,
                            grad_sq_scale,
                            beta2_scale,
                            denom_shift,
                            lr_numerator,
                        );
                        rows.push(SweepRow {
                            experiment: "linear".to_string(),
                            block_size,
                            rounding: if stochastic_rounding {
                                "stochastic".to_string()
                            } else {
                                "nearest".to_string()
                            },
                            optimizer: artifacts.stats.optimizer.clone(),
                            scale_mode: scale_mode_name(scale_mode).to_string(),
                            state_scale_mode: scale_mode_name(scale_mode).to_string(),
                            v_scale_mode: artifacts.stats.v_scale_mode.clone(),
                            grad_sq_scale_numerator: artifacts.stats.grad_sq_scale_numerator,
                            grad_sq_scale_shift: artifacts.stats.grad_sq_scale_shift,
                            beta2_numerator: artifacts.stats.beta2_numerator,
                            beta2_shift: artifacts.stats.beta2_shift,
                            v_quant_scheme: artifacts.stats.v_quant_scheme.clone(),
                            denom_mode: artifacts.stats.denom_mode.clone(),
                            denom_shift: artifacts.stats.denom_shift,
                            lr_numerator,
                            loss_l1_sum: artifacts.stats.loss_l1_sum,
                            nonzero_weight_updates: artifacts.stats.nonzero_weight_updates,
                            zeroed_weight_updates: artifacts.stats.zeroed_weight_updates,
                            nonzero_momentum_updates: artifacts.stats.nonzero_momentum_updates,
                            zeroed_momentum_updates: artifacts.stats.zeroed_momentum_updates,
                            nonzero_v_updates: artifacts.stats.nonzero_v_updates,
                            zeroed_v_updates: artifacts.stats.zeroed_v_updates,
                            nonzero_weight_ratio: safe_ratio(
                                artifacts.stats.nonzero_weight_updates,
                                artifacts.stats.zeroed_weight_updates,
                            ),
                            nonzero_momentum_ratio: safe_ratio(
                                artifacts.stats.nonzero_momentum_updates,
                                artifacts.stats.zeroed_momentum_updates,
                            ),
                            nonzero_v_ratio: safe_ratio(
                                artifacts.stats.nonzero_v_updates,
                                artifacts.stats.zeroed_v_updates,
                            ),
                        });
                        write_checkpoint(&tmp, &artifacts.tensors, &artifacts.stats)?;
                        }
                    }
                }
            }
        }
    }
    for optimizer in float_baselines {
        for lr_numerator in lr_numerators {
            let block_size = 8usize;
            let stochastic_rounding = true;
            let scale_mode = ScaleMode::P75;
            let tmp = out.with_file_name(format!("{}.run-{run_idx}.arrow", out.display()));
            run_idx += 1;
            let artifacts = train_toy_inner(
                steps,
                input_dim,
                output_dim,
                batch_size,
                block_size,
                stochastic_rounding,
                scale_mode,
                optimizer,
                IntScale::new(1, 0),
                IntScale::new(7, 3),
                0,
                lr_numerator,
            );
            rows.push(SweepRow {
                experiment: "linear".to_string(),
                block_size,
                rounding: "stochastic".to_string(),
                optimizer: artifacts.stats.optimizer.clone(),
                scale_mode: "float".to_string(),
                state_scale_mode: "float".to_string(),
                v_scale_mode: artifacts.stats.v_scale_mode.clone(),
                grad_sq_scale_numerator: artifacts.stats.grad_sq_scale_numerator,
                grad_sq_scale_shift: artifacts.stats.grad_sq_scale_shift,
                beta2_numerator: artifacts.stats.beta2_numerator,
                beta2_shift: artifacts.stats.beta2_shift,
                v_quant_scheme: artifacts.stats.v_quant_scheme.clone(),
                denom_mode: artifacts.stats.denom_mode.clone(),
                denom_shift: artifacts.stats.denom_shift,
                lr_numerator,
                loss_l1_sum: artifacts.stats.loss_l1_sum,
                nonzero_weight_updates: artifacts.stats.nonzero_weight_updates,
                zeroed_weight_updates: artifacts.stats.zeroed_weight_updates,
                nonzero_momentum_updates: artifacts.stats.nonzero_momentum_updates,
                zeroed_momentum_updates: artifacts.stats.zeroed_momentum_updates,
                nonzero_v_updates: artifacts.stats.nonzero_v_updates,
                zeroed_v_updates: artifacts.stats.zeroed_v_updates,
                nonzero_weight_ratio: safe_ratio(
                    artifacts.stats.nonzero_weight_updates,
                    artifacts.stats.zeroed_weight_updates,
                ),
                nonzero_momentum_ratio: safe_ratio(
                    artifacts.stats.nonzero_momentum_updates,
                    artifacts.stats.zeroed_momentum_updates,
                ),
                nonzero_v_ratio: safe_ratio(
                    artifacts.stats.nonzero_v_updates,
                    artifacts.stats.zeroed_v_updates,
                ),
            });
            write_checkpoint(&tmp, &artifacts.tensors, &artifacts.stats)?;
        }
    }

    rows.sort_by_key(|row| std::cmp::Reverse(score_row(row)));
    let best_overall = to_sweep_best(rows.first().context("sweep produced no rows")?);
    let mut best_by_optimizer = Vec::new();
    let mut seen_optimizers = std::collections::BTreeSet::new();
    for row in &rows {
        if seen_optimizers.insert(row.optimizer.clone()) {
            best_by_optimizer.push(to_sweep_best(row));
        }
    }
    let momentum_best = rows.iter().find(|row| row.optimizer == "momentum-sgd");
    let nesterov_best = rows.iter().find(|row| row.optimizer == "nesterov-sgd");
    let sign_ef_best = rows.iter().find(|row| row.optimizer == "signsgd-ef");
    let adam_best = rows.iter().find(|row| row.optimizer == "adam");
    let adam_v16_best = rows.iter().find(|row| row.optimizer == "adam-v16");
    let adam_v16_soft_best = rows.iter().find(|row| row.optimizer == "adam-v16-soft");
    let mut findings = Vec::new();
    findings.push(format!(
        "best overall: {} {} block={} rounding={} scale={} state_scale={} denom_shift={} lr={} loss={} nonzero_weight_ratio={:.3}",
        best_overall.experiment,
        best_overall.optimizer,
        best_overall.block_size,
        best_overall.rounding,
        best_overall.scale_mode,
        best_overall.state_scale_mode,
        best_overall.denom_shift,
        best_overall.lr_numerator,
        best_overall.loss_l1_sum,
        best_overall.nonzero_weight_ratio,
    ));
    if let (Some(momentum), Some(nesterov)) = (momentum_best, nesterov_best) {
        findings.push(format!(
            "momentum vs nesterov: best momentum loss={} ratio={:.3}, best nesterov loss={} ratio={:.3}",
            momentum.loss_l1_sum,
            momentum.nonzero_weight_ratio,
            nesterov.loss_l1_sum,
            nesterov.nonzero_weight_ratio,
        ));
    }
    if let Some(sign_ef) = sign_ef_best {
        findings.push(format!(
            "signsgd-ef floor: loss={} nonzero_weight_ratio={:.3} momentum_ratio={:.3}",
            sign_ef.loss_l1_sum,
            sign_ef.nonzero_weight_ratio,
            sign_ef.nonzero_momentum_ratio,
        ));
    }
    if let Some(adam) = adam_best {
        findings.push(format!(
            "pure int8 adam ceiling: loss={} nonzero_weight_ratio={:.3} nonzero_v_ratio={:.3}",
            adam.loss_l1_sum,
            adam.nonzero_weight_ratio,
            adam.nonzero_v_ratio,
        ));
    }
    if let (Some(v16), Some(v16_soft)) = (adam_v16_best, adam_v16_soft_best) {
        findings.push(format!(
            "adam-v16 denom softening: v16 loss={} weight_ratio={:.3} v_ratio={:.3}; soft shift={} loss={} weight_ratio={:.3} v_ratio={:.3}",
            v16.loss_l1_sum,
            v16.nonzero_weight_ratio,
            v16.nonzero_v_ratio,
            v16_soft.denom_shift,
            v16_soft.loss_l1_sum,
            v16_soft.nonzero_weight_ratio,
            v16_soft.nonzero_v_ratio,
        ));
    }

    let report = SweepReport {
        rows,
        best_overall,
        best_by_optimizer,
        findings,
    };
    std::fs::write(out, serde_json::to_vec_pretty(&report)?)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn sweep_recurrent(
    steps: usize,
    input_dim: usize,
    hidden_dim: usize,
    seq_len: usize,
    batch_size: usize,
    out: &PathBuf,
) -> Result<()> {
    let pure_optimizers = [
        Optimizer::Adam,
        Optimizer::AdamEf,
        Optimizer::AdamV16,
        Optimizer::AdamV16Soft,
        Optimizer::MomentumSgd,
        Optimizer::MomentumSgdEf,
        Optimizer::NesterovSgd,
        Optimizer::SignSgd,
        Optimizer::SignSgdEf,
        Optimizer::Qsgd,
    ];
    let block_sizes = [4usize, 8usize, 16usize];
    let rounding_modes = [true, false];
    let scale_modes = [ScaleMode::Max, ScaleMode::P75, ScaleMode::P90];
    let state_scale_modes = [ScaleMode::Max, ScaleMode::P75, ScaleMode::P90];
    let lr_numerators = [3i32, 5i32, 9i32];
    let mut rows = Vec::new();
    let mut run_idx = 0usize;

    for optimizer in pure_optimizers {
        for block_size in block_sizes {
            for stochastic_rounding in rounding_modes {
                for scale_mode in scale_modes {
                    for state_scale_mode in state_scale_modes {
                        for lr_numerator in lr_numerators {
                        let denom_shifts: &[u8] = if matches!(optimizer, Optimizer::AdamV16Soft) {
                            &[1, 2, 3]
                        } else {
                            &[default_denom_shift(optimizer)]
                        };
                        for &denom_shift in denom_shifts {
                        let grad_sq_scale = if matches!(optimizer, Optimizer::Adam | Optimizer::AdamEf) {
                            IntScale::new(1, 5)
                        } else {
                            IntScale::new(1, 0)
                        };
                        let beta2_scale = if matches!(optimizer, Optimizer::Adam | Optimizer::AdamEf) {
                            IntScale::new(6, 3)
                        } else {
                            IntScale::new(7, 3)
                        };
                        let tmp =
                            out.with_file_name(format!("{}.run-{run_idx}.arrow", out.display()));
                        run_idx += 1;
                        let artifacts = train_recurrent_inner(
                            steps,
                            input_dim,
                            hidden_dim,
                            seq_len,
                            batch_size,
                            block_size,
                            stochastic_rounding,
                            scale_mode,
                            state_scale_mode,
                            optimizer,
                            grad_sq_scale,
                            beta2_scale,
                            denom_shift,
                            lr_numerator,
                        );
                        rows.push(SweepRow {
                            experiment: "recurrent".to_string(),
                            block_size,
                            rounding: if stochastic_rounding {
                                "stochastic".to_string()
                            } else {
                                "nearest".to_string()
                            },
                            optimizer: artifacts.stats.optimizer.clone(),
                            scale_mode: scale_mode_name(scale_mode).to_string(),
                            state_scale_mode: scale_mode_name(state_scale_mode).to_string(),
                            v_scale_mode: artifacts.stats.v_scale_mode.clone(),
                            grad_sq_scale_numerator: artifacts.stats.grad_sq_scale_numerator,
                            grad_sq_scale_shift: artifacts.stats.grad_sq_scale_shift,
                            beta2_numerator: artifacts.stats.beta2_numerator,
                            beta2_shift: artifacts.stats.beta2_shift,
                            v_quant_scheme: artifacts.stats.v_quant_scheme.clone(),
                            denom_mode: artifacts.stats.denom_mode.clone(),
                            denom_shift: artifacts.stats.denom_shift,
                            lr_numerator,
                            loss_l1_sum: artifacts.stats.loss_l1_sum,
                            nonzero_weight_updates: artifacts.stats.nonzero_weight_updates,
                            zeroed_weight_updates: artifacts.stats.zeroed_weight_updates,
                            nonzero_momentum_updates: artifacts.stats.nonzero_momentum_updates,
                            zeroed_momentum_updates: artifacts.stats.zeroed_momentum_updates,
                            nonzero_v_updates: artifacts.stats.nonzero_v_updates,
                            zeroed_v_updates: artifacts.stats.zeroed_v_updates,
                            nonzero_weight_ratio: safe_ratio(
                                artifacts.stats.nonzero_weight_updates,
                                artifacts.stats.zeroed_weight_updates,
                            ),
                            nonzero_momentum_ratio: safe_ratio(
                                artifacts.stats.nonzero_momentum_updates,
                                artifacts.stats.zeroed_momentum_updates,
                            ),
                            nonzero_v_ratio: safe_ratio(
                                artifacts.stats.nonzero_v_updates,
                                artifacts.stats.zeroed_v_updates,
                            ),
                        });
                        write_checkpoint(&tmp, &artifacts.tensors, &artifacts.stats)?;
                        }
                    }
                    }
                }
            }
        }
    }

    rows.sort_by_key(|row| std::cmp::Reverse(score_row(row)));
    let best_overall = to_sweep_best(rows.first().context("recurrent sweep produced no rows")?);
    let mut best_by_optimizer = Vec::new();
    let mut seen_optimizers = std::collections::BTreeSet::new();
    for row in &rows {
        if seen_optimizers.insert(row.optimizer.clone()) {
            best_by_optimizer.push(to_sweep_best(row));
        }
    }
    let sign_ef_best = rows.iter().find(|row| row.optimizer == "signsgd-ef");
    let momentum_best = rows.iter().find(|row| row.optimizer == "momentum-sgd");
    let adam_best = rows.iter().find(|row| row.optimizer == "adam");
    let adam_v16_best = rows.iter().find(|row| row.optimizer == "adam-v16");
    let adam_v16_soft_best = rows.iter().find(|row| row.optimizer == "adam-v16-soft");
    let mut findings = Vec::new();
    findings.push(format!(
        "best recurrent: {} {} block={} rounding={} scale={} state_scale={} denom_shift={} lr={} loss={} nonzero_weight_ratio={:.3}",
        best_overall.experiment,
        best_overall.optimizer,
        best_overall.block_size,
        best_overall.rounding,
        best_overall.scale_mode,
        best_overall.state_scale_mode,
        best_overall.denom_shift,
        best_overall.lr_numerator,
        best_overall.loss_l1_sum,
        best_overall.nonzero_weight_ratio,
    ));
    if let Some(sign_ef) = sign_ef_best {
        findings.push(format!(
            "recurrent signsgd-ef: loss={} nonzero_weight_ratio={:.3} momentum_ratio={:.3} state_scale={}",
            sign_ef.loss_l1_sum,
            sign_ef.nonzero_weight_ratio,
            sign_ef.nonzero_momentum_ratio,
            sign_ef.state_scale_mode,
        ));
    }
    if let Some(momentum) = momentum_best {
        findings.push(format!(
            "recurrent momentum baseline: loss={} nonzero_weight_ratio={:.3} state_scale={}",
            momentum.loss_l1_sum,
            momentum.nonzero_weight_ratio,
            momentum.state_scale_mode,
        ));
    }
    if let Some(adam) = adam_best {
        findings.push(format!(
            "recurrent pure int8 adam ceiling: loss={} nonzero_weight_ratio={:.3} nonzero_v_ratio={:.3} state_scale={}",
            adam.loss_l1_sum,
            adam.nonzero_weight_ratio,
            adam.nonzero_v_ratio,
            adam.state_scale_mode,
        ));
    }
    if let (Some(v16), Some(v16_soft)) = (adam_v16_best, adam_v16_soft_best) {
        findings.push(format!(
            "recurrent adam-v16 denom softening: v16 loss={} weight_ratio={:.3} v_ratio={:.3}; soft shift={} loss={} weight_ratio={:.3} v_ratio={:.3}",
            v16.loss_l1_sum,
            v16.nonzero_weight_ratio,
            v16.nonzero_v_ratio,
            v16_soft.denom_shift,
            v16_soft.loss_l1_sum,
            v16_soft.nonzero_weight_ratio,
            v16_soft.nonzero_v_ratio,
        ));
    }

    let report = SweepReport {
        rows,
        best_overall,
        best_by_optimizer,
        findings,
    };
    std::fs::write(out, serde_json::to_vec_pretty(&report)?)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

struct TrainArtifacts {
    stats: TrainStats,
    tensors: Vec<BlockwiseTensorI8>,
}

#[derive(Clone, Copy)]
enum FloatPrecision {
    Fp16,
    Bf16,
}

#[derive(Clone, Copy)]
enum FloatBaselineOptimizer {
    Adam,
    Momentum,
    Nesterov,
}

fn train_toy_inner(
    steps: usize,
    input_dim: usize,
    output_dim: usize,
    batch_size: usize,
    block_size: usize,
    stochastic_rounding: bool,
    scale_mode: ScaleMode,
    optimizer: Optimizer,
    grad_sq_scale: IntScale,
    beta2_scale: IntScale,
    denom_shift: u8,
    lr_numerator: i32,
) -> TrainArtifacts {
    if matches!(
        optimizer,
        Optimizer::Fp16Adam
            | Optimizer::Bf16Adam
            | Optimizer::Fp16Momentum
            | Optimizer::Bf16Momentum
            | Optimizer::Fp16Nesterov
            | Optimizer::Bf16Nesterov
    ) {
        return train_float_baseline(
            steps,
            input_dim,
            output_dim,
            batch_size,
            block_size,
            stochastic_rounding,
            match optimizer {
                Optimizer::Fp16Adam => FloatPrecision::Fp16,
                Optimizer::Bf16Adam => FloatPrecision::Bf16,
                Optimizer::Fp16Momentum => FloatPrecision::Fp16,
                Optimizer::Bf16Momentum => FloatPrecision::Bf16,
                Optimizer::Fp16Nesterov => FloatPrecision::Fp16,
                Optimizer::Bf16Nesterov => FloatPrecision::Bf16,
                _ => unreachable!(),
            },
            match optimizer {
                Optimizer::Fp16Adam | Optimizer::Bf16Adam => FloatBaselineOptimizer::Adam,
                Optimizer::Fp16Momentum | Optimizer::Bf16Momentum => {
                    FloatBaselineOptimizer::Momentum
                }
                Optimizer::Fp16Nesterov | Optimizer::Bf16Nesterov => {
                    FloatBaselineOptimizer::Nesterov
                }
                _ => unreachable!(),
            },
            lr_numerator,
        );
    }

    let input_scale = IntScale::new(32, 8);
    let weight_scale = IntScale::new(24, 8);
    let momentum_scale = IntScale::new(16, 8);
    let v_scale = IntScale::new(8, 12);
    let grad_base_scale = IntScale::new(8, 8);
    let lr_scale = IntScale::new(lr_numerator, 10);
    let beta_scale = IntScale::new(7, 3);
    let one_minus_beta_scale = IntScale::new(1, 3);
    let one_minus_beta2_scale = IntScale::new((1_i32 << beta2_scale.shift) - beta2_scale.numerator, beta2_scale.shift);
    let v_scale_mode = ScaleMode::P90;

    let mut rng = Lcg64::new(0x8bad_cafe_u64);
    let mut weights = BlockwiseTensorI8::from_seeded("linear.weight", output_dim, input_dim, block_size, weight_scale, 7);
    let teacher = BlockwiseTensorI8::from_seeded("teacher.weight", output_dim, input_dim, block_size, weight_scale, 19);
    let mut momentum = BlockwiseTensorI8::zeros("linear.momentum", output_dim, input_dim, block_size, momentum_scale);
    let mut v = BlockwiseTensorI8::zeros("linear.v", output_dim, input_dim, block_size, v_scale);
    let mut v16 = BlockwiseTensorI16::zeros("linear.v16", output_dim, input_dim, block_size, v_scale);
    let mut update_error =
        BlockwiseTensorI8::zeros("linear.update_error", output_dim, input_dim, block_size, IntScale::new(1, 0));

    let mut stats = TrainStats {
        steps,
        block_size,
        stochastic_rounding,
        optimizer: match optimizer {
            Optimizer::Adam => "adam".to_string(),
            Optimizer::AdamEf => "adam-ef".to_string(),
            Optimizer::AdamV16 => "adam-v16".to_string(),
            Optimizer::AdamV16Soft => "adam-v16-soft".to_string(),
            Optimizer::Fp16Adam => "fp16-adam".to_string(),
            Optimizer::Bf16Adam => "bf16-adam".to_string(),
            Optimizer::Fp16Momentum => "fp16-momentum".to_string(),
            Optimizer::Bf16Momentum => "bf16-momentum".to_string(),
            Optimizer::Fp16Nesterov => "fp16-nesterov".to_string(),
            Optimizer::Bf16Nesterov => "bf16-nesterov".to_string(),
            Optimizer::MomentumSgd => "momentum-sgd".to_string(),
            Optimizer::MomentumSgdEf => "momentum-sgd-ef".to_string(),
            Optimizer::NesterovSgd => "nesterov-sgd".to_string(),
            Optimizer::SignSgd => "signsgd".to_string(),
            Optimizer::SignSgdEf => "signsgd-ef".to_string(),
            Optimizer::SignSgdMajority => "signsgd-majority".to_string(),
            Optimizer::Qsgd => "qsgd".to_string(),
        },
        scale_mode: match scale_mode { ScaleMode::Max => "max".to_string(), ScaleMode::P75 => "p75".to_string(), ScaleMode::P90 => "p90".to_string() },
        v_scale_mode: match v_scale_mode { ScaleMode::Max => "max".to_string(), ScaleMode::P75 => "p75".to_string(), ScaleMode::P90 => "p90".to_string() },
        grad_sq_scale_numerator: grad_sq_scale.numerator,
        grad_sq_scale_shift: grad_sq_scale.shift,
        beta2_numerator: beta2_scale.numerator,
        beta2_shift: beta2_scale.shift,
        v_quant_scheme: "pow2_blockwise".to_string(),
        denom_mode: if denom_shift == 0 {
            "isqrt".to_string()
        } else {
            format!("isqrt_shift{denom_shift}")
        },
        denom_shift,
        lr_numerator,
        loss_l1_sum: 0,
        nonzero_weight_updates: 0,
        zeroed_weight_updates: 0,
        nonzero_momentum_updates: 0,
        zeroed_momentum_updates: 0,
        nonzero_v_updates: 0,
        zeroed_v_updates: 0,
        grad_saturation: 0,
        weight_saturation: 0,
        momentum_saturation: 0,
        v_saturation: 0,
    };

    for step in 0..steps {
        let batch = make_batch(batch_size, input_dim, step as i32, block_size, input_scale);
        let target = matmul_i8(&batch, &teacher);
        let pred = matmul_i8(&batch, &weights);
        let residual = diff_i32(&pred, &target);
        stats.loss_l1_sum += residual.iter().map(|v| v.abs() as i64).sum::<i64>();
        let grad = outer_product_grad(&batch, &residual, output_dim, input_dim, block_size, grad_base_scale, scale_mode, &mut rng, stochastic_rounding);
        stats.grad_saturation += grad.saturation_count();
        match optimizer {
            Optimizer::Adam => update_adam_i8(
                &mut weights,
                &grad,
                &mut momentum,
                &mut v,
                beta_scale,
                one_minus_beta_scale,
                beta2_scale,
                one_minus_beta2_scale,
                v_scale_mode,
                grad_sq_scale,
                lr_scale,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::AdamEf => update_adam_i8_ef(
                &mut weights,
                &grad,
                &mut momentum,
                &mut v,
                &mut update_error,
                beta_scale,
                one_minus_beta_scale,
                beta2_scale,
                one_minus_beta2_scale,
                v_scale_mode,
                grad_sq_scale,
                lr_scale,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::AdamV16 => update_adam_i16v(
                &mut weights,
                &grad,
                &mut momentum,
                &mut v16,
                beta_scale,
                one_minus_beta_scale,
                beta2_scale,
                one_minus_beta2_scale,
                v_scale_mode,
                grad_sq_scale,
                lr_scale,
                denom_shift,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::AdamV16Soft => update_adam_i16v(
                &mut weights,
                &grad,
                &mut momentum,
                &mut v16,
                beta_scale,
                one_minus_beta_scale,
                beta2_scale,
                one_minus_beta2_scale,
                v_scale_mode,
                grad_sq_scale,
                lr_scale,
                denom_shift,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::MomentumSgd => update_momentum_sgd_i8(
                &mut weights,
                &grad,
                &mut momentum,
                beta_scale,
                one_minus_beta_scale,
                lr_scale,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::MomentumSgdEf => update_momentum_sgd_i8_ef(
                &mut weights,
                &grad,
                &mut momentum,
                &mut update_error,
                beta_scale,
                one_minus_beta_scale,
                lr_scale,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::NesterovSgd => update_nesterov_sgd_i8(
                &mut weights,
                &grad,
                &mut momentum,
                beta_scale,
                one_minus_beta_scale,
                lr_scale,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::SignSgd => update_sign_sgd_i8(
                &mut weights,
                &grad,
                lr_numerator,
                &mut stats,
            ),
            Optimizer::SignSgdEf => update_sign_sgd_ef_i8(
                &mut weights,
                &grad,
                &mut momentum,
                lr_numerator,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::SignSgdMajority => update_sign_sgd_majority_i8(
                &mut weights,
                &batch,
                &residual,
                output_dim,
                input_dim,
                lr_numerator,
                &mut stats,
            ),
            Optimizer::Qsgd => update_qsgd_i8(
                &mut weights,
                &grad,
                lr_scale,
                &mut stats,
                &mut rng,
                stochastic_rounding,
            ),
            Optimizer::Fp16Adam
            | Optimizer::Bf16Adam
            | Optimizer::Fp16Momentum
            | Optimizer::Bf16Momentum
            | Optimizer::Fp16Nesterov
            | Optimizer::Bf16Nesterov => unreachable!(),
        }
    }

    stats.weight_saturation = weights.saturation_count();
    stats.momentum_saturation = momentum.saturation_count();
    stats.v_saturation = match optimizer {
        Optimizer::AdamV16 | Optimizer::AdamV16Soft => v16.saturation_count(),
        _ => v.saturation_count(),
    };
    let v_observed = match optimizer {
        Optimizer::AdamV16 | Optimizer::AdamV16Soft => {
            quantize_i16_to_i8_tensor("linear.v16.observe", &v16)
        }
        _ => v,
    };
    TrainArtifacts { stats, tensors: vec![weights, teacher, momentum, v_observed, update_error] }
}

fn train_recurrent_inner(
    steps: usize,
    input_dim: usize,
    hidden_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    stochastic_rounding: bool,
    input_scale_mode: ScaleMode,
    state_scale_mode: ScaleMode,
    optimizer: Optimizer,
    grad_sq_scale: IntScale,
    beta2_scale: IntScale,
    denom_shift: u8,
    lr_numerator: i32,
) -> TrainArtifacts {
    let input_scale = IntScale::new(32, 8);
    let weight_scale = IntScale::new(24, 8);
    let momentum_scale = IntScale::new(16, 8);
    let v_scale = IntScale::new(8, 12);
    let grad_base_scale = IntScale::new(8, 8);
    let lr_scale = IntScale::new(lr_numerator, 10);
    let beta_scale = IntScale::new(7, 3);
    let one_minus_beta_scale = IntScale::new(1, 3);
    let one_minus_beta2_scale =
        IntScale::new((1_i32 << beta2_scale.shift) - beta2_scale.numerator, beta2_scale.shift);
    let v_scale_mode = ScaleMode::P90;

    let mut rng = Lcg64::new(0x5151_dead_u64);
    let mut weights_in = BlockwiseTensorI8::from_seeded(
        "recurrent.weight_in",
        hidden_dim,
        input_dim,
        block_size,
        weight_scale,
        23,
    );
    let teacher_in = BlockwiseTensorI8::from_seeded(
        "teacher.weight_in",
        hidden_dim,
        input_dim,
        block_size,
        weight_scale,
        31,
    );
    let mut weights_state = BlockwiseTensorI8::from_seeded(
        "recurrent.weight_state",
        hidden_dim,
        hidden_dim,
        block_size,
        weight_scale,
        37,
    );
    let teacher_state = BlockwiseTensorI8::from_seeded(
        "teacher.weight_state",
        hidden_dim,
        hidden_dim,
        block_size,
        weight_scale,
        43,
    );
    let mut momentum_in = BlockwiseTensorI8::zeros(
        "recurrent.momentum_in",
        hidden_dim,
        input_dim,
        block_size,
        momentum_scale,
    );
    let mut momentum_state = BlockwiseTensorI8::zeros(
        "recurrent.momentum_state",
        hidden_dim,
        hidden_dim,
        block_size,
        momentum_scale,
    );
    let mut v_in = BlockwiseTensorI8::zeros("recurrent.v_in", hidden_dim, input_dim, block_size, v_scale);
    let mut v_state =
        BlockwiseTensorI8::zeros("recurrent.v_state", hidden_dim, hidden_dim, block_size, v_scale);
    let mut v16_in = BlockwiseTensorI16::zeros("recurrent.v16_in", hidden_dim, input_dim, block_size, v_scale);
    let mut v16_state =
        BlockwiseTensorI16::zeros("recurrent.v16_state", hidden_dim, hidden_dim, block_size, v_scale);
    let mut update_error_in = BlockwiseTensorI8::zeros(
        "recurrent.update_error_in",
        hidden_dim,
        input_dim,
        block_size,
        IntScale::new(1, 0),
    );
    let mut update_error_state = BlockwiseTensorI8::zeros(
        "recurrent.update_error_state",
        hidden_dim,
        hidden_dim,
        block_size,
        IntScale::new(1, 0),
    );

    let mut stats = TrainStats {
        steps,
        block_size,
        stochastic_rounding,
        optimizer: match optimizer {
            Optimizer::Adam => "adam".to_string(),
            Optimizer::AdamEf => "adam-ef".to_string(),
            Optimizer::AdamV16 => "adam-v16".to_string(),
            Optimizer::AdamV16Soft => "adam-v16-soft".to_string(),
            Optimizer::MomentumSgd => "momentum-sgd".to_string(),
            Optimizer::MomentumSgdEf => "momentum-sgd-ef".to_string(),
            Optimizer::NesterovSgd => "nesterov-sgd".to_string(),
            Optimizer::SignSgd => "signsgd".to_string(),
            Optimizer::SignSgdEf => "signsgd-ef".to_string(),
            Optimizer::Qsgd => "qsgd".to_string(),
            Optimizer::Fp16Adam
            | Optimizer::Bf16Adam
            | Optimizer::Fp16Momentum
            | Optimizer::Bf16Momentum
            | Optimizer::Fp16Nesterov
            | Optimizer::Bf16Nesterov
            | Optimizer::SignSgdMajority => "unsupported-recurrent".to_string(),
        },
        scale_mode: scale_mode_name(input_scale_mode).to_string(),
        v_scale_mode: scale_mode_name(v_scale_mode).to_string(),
        grad_sq_scale_numerator: grad_sq_scale.numerator,
        grad_sq_scale_shift: grad_sq_scale.shift,
        beta2_numerator: beta2_scale.numerator,
        beta2_shift: beta2_scale.shift,
        v_quant_scheme: "pow2_blockwise".to_string(),
        denom_mode: if denom_shift == 0 {
            "isqrt".to_string()
        } else {
            format!("isqrt_shift{denom_shift}")
        },
        denom_shift,
        lr_numerator,
        loss_l1_sum: 0,
        nonzero_weight_updates: 0,
        zeroed_weight_updates: 0,
        nonzero_momentum_updates: 0,
        zeroed_momentum_updates: 0,
        nonzero_v_updates: 0,
        zeroed_v_updates: 0,
        grad_saturation: 0,
        weight_saturation: 0,
        momentum_saturation: 0,
        v_saturation: 0,
    };

    for step in 0..steps {
        let sequence = make_recurrent_batch(seq_len, batch_size, input_dim, step as i32, block_size, input_scale);
        let student = run_recurrent_sequence(
            &sequence,
            &weights_in,
            &weights_state,
            hidden_dim,
            input_dim,
            batch_size,
        );
        let teacher = run_recurrent_sequence(
            &sequence,
            &teacher_in,
            &teacher_state,
            hidden_dim,
            input_dim,
            batch_size,
        );
        let residual: Vec<Vec<i32>> = student
            .outputs
            .iter()
            .zip(teacher.outputs.iter())
            .map(|(pred, target)| diff_i32(pred, target))
            .collect();
        stats.loss_l1_sum += residual
            .iter()
            .flat_map(|step_residual| step_residual.iter())
            .map(|v| i64::from(*v).abs())
            .sum::<i64>();

        let grad_in = recurrent_input_grad(
            &sequence,
            &residual,
            hidden_dim,
            input_dim,
            block_size,
            grad_base_scale,
            input_scale_mode,
            &mut rng,
            stochastic_rounding,
        );
        let grad_state = recurrent_state_grad(
            &student.states,
            &residual,
            hidden_dim,
            block_size,
            grad_base_scale,
            state_scale_mode,
            &mut rng,
            stochastic_rounding,
        );
        stats.grad_saturation += grad_in.saturation_count() + grad_state.saturation_count();

        match optimizer {
            Optimizer::Adam => {
                update_adam_i8(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    &mut v_in,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_adam_i8(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    &mut v_state,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::AdamV16 => {
                update_adam_i16v(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    &mut v16_in,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    denom_shift,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_adam_i16v(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    &mut v16_state,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    denom_shift,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::AdamV16Soft => {
                update_adam_i16v(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    &mut v16_in,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    denom_shift,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_adam_i16v(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    &mut v16_state,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    denom_shift,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::AdamEf => {
                update_adam_i8_ef(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    &mut v_in,
                    &mut update_error_in,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_adam_i8_ef(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    &mut v_state,
                    &mut update_error_state,
                    beta_scale,
                    one_minus_beta_scale,
                    beta2_scale,
                    one_minus_beta2_scale,
                    v_scale_mode,
                    grad_sq_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::MomentumSgd => {
                update_momentum_sgd_i8(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    beta_scale,
                    one_minus_beta_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_momentum_sgd_i8(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    beta_scale,
                    one_minus_beta_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::MomentumSgdEf => {
                update_momentum_sgd_i8_ef(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    &mut update_error_in,
                    beta_scale,
                    one_minus_beta_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_momentum_sgd_i8_ef(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    &mut update_error_state,
                    beta_scale,
                    one_minus_beta_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::NesterovSgd => {
                update_nesterov_sgd_i8(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    beta_scale,
                    one_minus_beta_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_nesterov_sgd_i8(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    beta_scale,
                    one_minus_beta_scale,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::SignSgd => {
                update_sign_sgd_i8(&mut weights_in, &grad_in, lr_numerator, &mut stats);
                update_sign_sgd_i8(&mut weights_state, &grad_state, lr_numerator, &mut stats);
            }
            Optimizer::SignSgdEf => {
                update_sign_sgd_ef_i8(
                    &mut weights_in,
                    &grad_in,
                    &mut momentum_in,
                    lr_numerator,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_sign_sgd_ef_i8(
                    &mut weights_state,
                    &grad_state,
                    &mut momentum_state,
                    lr_numerator,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::Qsgd => {
                update_qsgd_i8(
                    &mut weights_in,
                    &grad_in,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
                update_qsgd_i8(
                    &mut weights_state,
                    &grad_state,
                    lr_scale,
                    &mut stats,
                    &mut rng,
                    stochastic_rounding,
                );
            }
            Optimizer::Fp16Adam
            | Optimizer::Bf16Adam
            | Optimizer::Fp16Momentum
            | Optimizer::Bf16Momentum
            | Optimizer::Fp16Nesterov
            | Optimizer::Bf16Nesterov
            | Optimizer::SignSgdMajority => unreachable!(),
        }
    }

    stats.weight_saturation = weights_in.saturation_count() + weights_state.saturation_count();
    stats.momentum_saturation = momentum_in.saturation_count() + momentum_state.saturation_count();
    stats.v_saturation = match optimizer {
        Optimizer::AdamV16 | Optimizer::AdamV16Soft => {
            v16_in.saturation_count() + v16_state.saturation_count()
        }
        _ => v_in.saturation_count() + v_state.saturation_count(),
    };
    let v_obs_in = match optimizer {
        Optimizer::AdamV16 | Optimizer::AdamV16Soft => {
            quantize_i16_to_i8_tensor("recurrent.v16_in.observe", &v16_in)
        }
        _ => v_in,
    };
    let v_obs_state = match optimizer {
        Optimizer::AdamV16 | Optimizer::AdamV16Soft => {
            quantize_i16_to_i8_tensor("recurrent.v16_state.observe", &v16_state)
        }
        _ => v_state,
    };
    TrainArtifacts {
        stats,
        tensors: vec![
            weights_in,
            teacher_in,
            weights_state,
            teacher_state,
            momentum_in,
            momentum_state,
            v_obs_in,
            v_obs_state,
            update_error_in,
            update_error_state,
        ],
    }
}

struct RecurrentRun {
    states: Vec<Vec<i32>>,
    outputs: Vec<Vec<i32>>,
}

fn run_recurrent_sequence(
    sequence: &[BlockwiseTensorI8],
    weight_in: &BlockwiseTensorI8,
    weight_state: &BlockwiseTensorI8,
    hidden_dim: usize,
    input_dim: usize,
    batch_size: usize,
) -> RecurrentRun {
    let mut prev_state = vec![0i32; batch_size * hidden_dim];
    let mut states = Vec::with_capacity(sequence.len());
    let mut outputs = Vec::with_capacity(sequence.len());
    for token in sequence {
        let mut next_state = vec![0i32; batch_size * hidden_dim];
        for r in 0..batch_size {
            for h in 0..hidden_dim {
                let mut acc = 0i32;
                for c in 0..input_dim {
                    acc += token.get(r, c) as i32 * weight_in.get(h, c) as i32;
                }
                for c in 0..hidden_dim {
                    acc += prev_state[r * hidden_dim + c] * weight_state.get(h, c) as i32;
                }
                next_state[r * hidden_dim + h] = clamp_activation(acc >> 6);
            }
        }
        outputs.push(next_state.clone());
        states.push(prev_state.clone());
        prev_state = next_state;
    }
    RecurrentRun { states, outputs }
}

fn make_recurrent_batch(
    seq_len: usize,
    batch_size: usize,
    input_dim: usize,
    step: i32,
    block_size: usize,
    scale: IntScale,
) -> Vec<BlockwiseTensorI8> {
    (0..seq_len)
        .map(|t| {
            let mut batch =
                BlockwiseTensorI8::zeros(&format!("input.step{t}"), batch_size, input_dim, block_size, scale);
            for r in 0..batch_size {
                for c in 0..input_dim {
                    let raw = ((((r * input_dim + c) as i32 + step * 7 + t as i32 * 13) * 9) % 47) - 23;
                    batch.set(r, c, raw as i8);
                }
            }
            batch
        })
        .collect()
}

fn recurrent_input_grad(
    sequence: &[BlockwiseTensorI8],
    residuals: &[Vec<i32>],
    hidden_dim: usize,
    input_dim: usize,
    block_size: usize,
    fallback_scale: IntScale,
    scale_mode: ScaleMode,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) -> BlockwiseTensorI8 {
    let mut accum = vec![0i32; hidden_dim * input_dim];
    for (token, residual) in sequence.iter().zip(residuals.iter()) {
        for h in 0..hidden_dim {
            for i in 0..input_dim {
                let mut acc = 0i32;
                for r in 0..token.rows {
                    acc += residual[r * hidden_dim + h] * token.get(r, i) as i32;
                }
                accum[h * input_dim + i] += acc >> 11;
            }
        }
    }
    quantize_blockwise(
        "recurrent.grad_in",
        hidden_dim,
        input_dim,
        block_size,
        &accum,
        fallback_scale,
        scale_mode,
        rng,
        stochastic_rounding,
    )
}

fn recurrent_state_grad(
    prev_states: &[Vec<i32>],
    residuals: &[Vec<i32>],
    hidden_dim: usize,
    block_size: usize,
    fallback_scale: IntScale,
    scale_mode: ScaleMode,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) -> BlockwiseTensorI8 {
    let mut accum = vec![0i32; hidden_dim * hidden_dim];
    for (prev_state, residual) in prev_states.iter().zip(residuals.iter()) {
        let batch_size = prev_state.len() / hidden_dim;
        for h in 0..hidden_dim {
            for i in 0..hidden_dim {
                let mut acc = 0i32;
                for r in 0..batch_size {
                    acc += residual[r * hidden_dim + h] * prev_state[r * hidden_dim + i];
                }
                accum[h * hidden_dim + i] += acc >> 11;
            }
        }
    }
    quantize_blockwise(
        "recurrent.grad_state",
        hidden_dim,
        hidden_dim,
        block_size,
        &accum,
        fallback_scale,
        scale_mode,
        rng,
        stochastic_rounding,
    )
}

fn clamp_activation(value: i32) -> i32 {
    value.clamp(-96, 96)
}

fn quantize_float(value: f32, precision: FloatPrecision) -> f32 {
    match precision {
        FloatPrecision::Fp16 => f16::from_f32(value).to_f32(),
        FloatPrecision::Bf16 => bf16::from_f32(value).to_f32(),
    }
}

fn train_float_baseline(
    steps: usize,
    input_dim: usize,
    output_dim: usize,
    batch_size: usize,
    block_size: usize,
    stochastic_rounding: bool,
    precision: FloatPrecision,
    optimizer: FloatBaselineOptimizer,
    lr_numerator: i32,
) -> TrainArtifacts {
    let input_scale = IntScale::new(32, 8);
    let lr = lr_numerator as f32 / 1024.0;
    let beta1: f32 = 7.0 / 8.0;
    let beta2: f32 = 7.0 / 8.0;
    let eps = 1e-4f32;

    let weight_seed =
        BlockwiseTensorI8::from_seeded("linear.weight", output_dim, input_dim, block_size, IntScale::new(1, 0), 7);
    let teacher_seed =
        BlockwiseTensorI8::from_seeded("teacher.weight", output_dim, input_dim, block_size, IntScale::new(1, 0), 19);

    let mut weights: Vec<f32> = weight_seed.values.iter().map(|&v| quantize_float(v as f32, precision)).collect();
    let teacher: Vec<f32> = teacher_seed.values.iter().map(|&v| quantize_float(v as f32, precision)).collect();
    let mut momentum = vec![0.0f32; weights.len()];
    let mut v = vec![0.0f32; weights.len()];

    let mut stats = TrainStats {
        steps,
        block_size,
        stochastic_rounding,
        optimizer: match precision {
            FloatPrecision::Fp16 => match optimizer {
                FloatBaselineOptimizer::Adam => "fp16-adam".to_string(),
                FloatBaselineOptimizer::Momentum => "fp16-momentum".to_string(),
                FloatBaselineOptimizer::Nesterov => "fp16-nesterov".to_string(),
            },
            FloatPrecision::Bf16 => match optimizer {
                FloatBaselineOptimizer::Adam => "bf16-adam".to_string(),
                FloatBaselineOptimizer::Momentum => "bf16-momentum".to_string(),
                FloatBaselineOptimizer::Nesterov => "bf16-nesterov".to_string(),
            },
        },
        scale_mode: "float".to_string(),
        v_scale_mode: "float".to_string(),
        grad_sq_scale_numerator: 0,
        grad_sq_scale_shift: 0,
        beta2_numerator: 7,
        beta2_shift: 3,
        v_quant_scheme: "float".to_string(),
        denom_mode: "sqrt".to_string(),
        denom_shift: 0,
        lr_numerator,
        loss_l1_sum: 0,
        nonzero_weight_updates: 0,
        zeroed_weight_updates: 0,
        nonzero_momentum_updates: 0,
        zeroed_momentum_updates: 0,
        nonzero_v_updates: 0,
        zeroed_v_updates: 0,
        grad_saturation: 0,
        weight_saturation: 0,
        momentum_saturation: 0,
        v_saturation: 0,
    };

    for step in 0..steps {
        let batch = make_batch(batch_size, input_dim, step as i32, block_size, input_scale);
        let pred = matmul_f32(&batch, &weights, output_dim, input_dim, precision);
        let target = matmul_f32(&batch, &teacher, output_dim, input_dim, precision);
        let residual: Vec<f32> = pred
            .iter()
            .zip(target.iter())
            .map(|(p, t)| quantize_float(*p - *t, precision))
            .collect();
        stats.loss_l1_sum += residual.iter().map(|v| v.abs() as i64).sum::<i64>();
        let grad = outer_product_grad_f32(&batch, &residual, output_dim, input_dim, precision);
        let beta1_t = 1.0 - beta1.powi((step + 1) as i32);
        let beta2_t = 1.0 - beta2.powi((step + 1) as i32);
        for idx in 0..weights.len() {
            let g = grad[idx];
            let new_m = quantize_float(beta1 * momentum[idx] + (1.0 - beta1) * g, precision);
            momentum[idx] = new_m;
            if new_m == 0.0 {
                stats.zeroed_momentum_updates += 1;
            } else {
                stats.nonzero_momentum_updates += 1;
            }

            let delta = match optimizer {
                FloatBaselineOptimizer::Adam => {
                    let new_v = quantize_float(beta2 * v[idx] + (1.0 - beta2) * g * g, precision);
                    v[idx] = new_v;
                    if new_v == 0.0 {
                        stats.zeroed_v_updates += 1;
                    } else {
                        stats.nonzero_v_updates += 1;
                    }
                    let m_hat = new_m / beta1_t.max(eps);
                    let v_hat = new_v / beta2_t.max(eps);
                    quantize_float(lr * m_hat / (v_hat.sqrt() + eps), precision)
                }
                FloatBaselineOptimizer::Momentum => {
                    quantize_float(lr * new_m, precision)
                }
                FloatBaselineOptimizer::Nesterov => {
                    let lookahead = beta1 * new_m + (1.0 - beta1) * g;
                    quantize_float(lr * lookahead, precision)
                }
            };
            if delta == 0.0 {
                stats.zeroed_weight_updates += 1;
            } else {
                stats.nonzero_weight_updates += 1;
            }
            weights[idx] = quantize_float(weights[idx] - delta, precision);
        }
    }

    let tensors = vec![
        quantize_f32_to_i8_tensor("linear.weight", output_dim, input_dim, block_size, &weights),
        quantize_f32_to_i8_tensor("teacher.weight", output_dim, input_dim, block_size, &teacher),
        quantize_f32_to_i8_tensor("linear.momentum", output_dim, input_dim, block_size, &momentum),
        quantize_f32_to_i8_tensor("linear.v", output_dim, input_dim, block_size, &v),
    ];
    TrainArtifacts { stats, tensors }
}

fn matmul_f32(
    input: &BlockwiseTensorI8,
    weight: &[f32],
    output_dim: usize,
    input_dim: usize,
    precision: FloatPrecision,
) -> Vec<f32> {
    let mut out = vec![0.0f32; input.rows * output_dim];
    for r in 0..input.rows {
        for o in 0..output_dim {
            let mut acc = 0.0f32;
            for c in 0..input_dim {
                acc += input.get(r, c) as f32 * weight[o * input_dim + c];
            }
            out[r * output_dim + o] = quantize_float(acc, precision);
        }
    }
    out
}

fn outer_product_grad_f32(
    input: &BlockwiseTensorI8,
    residual: &[f32],
    output_dim: usize,
    input_dim: usize,
    precision: FloatPrecision,
) -> Vec<f32> {
    let mut grad = vec![0.0f32; output_dim * input_dim];
    for o in 0..output_dim {
        for i in 0..input_dim {
            let mut acc = 0.0f32;
            for r in 0..input.rows {
                acc += residual[r * output_dim + o] * input.get(r, i) as f32;
            }
            grad[o * input_dim + i] = quantize_float(acc / 4096.0, precision);
        }
    }
    grad
}

fn quantize_f32_to_i8_tensor(
    name: &str,
    rows: usize,
    cols: usize,
    block_size: usize,
    source: &[f32],
) -> BlockwiseTensorI8 {
    let mut tensor = BlockwiseTensorI8::zeros(name, rows, cols, block_size, IntScale::new(1, 0));
    for (idx, value) in source.iter().enumerate() {
        tensor.values[idx] = value.round().clamp(i8::MIN as f32, i8::MAX as f32) as i8;
    }
    tensor
}

fn quantize_i16_to_i8_tensor(name: &str, source: &BlockwiseTensorI16) -> BlockwiseTensorI8 {
    let mut tensor = BlockwiseTensorI8::zeros(name, source.rows, source.cols, source.block_size, IntScale::new(1, 0));
    for (idx, value) in source.values.iter().enumerate() {
        tensor.values[idx] = (*value as i32).clamp(i8::MIN as i32, i8::MAX as i32) as i8;
    }
    tensor
}

fn update_momentum_sgd_i8(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    momentum: &mut BlockwiseTensorI8,
    beta_scale: IntScale,
    one_minus_beta_scale: IntScale,
    lr_scale: IntScale,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let mom_scale = momentum.scale_for(idx);
        let old_m = mom_scale.dequantize_i8(momentum.values[idx]);
        let mixed = beta_scale.apply_i32(old_m) + one_minus_beta_scale.apply_i32(grad_i32);
        let new_m = mom_scale.quantize_i32(mixed, rng, stochastic_rounding);
        momentum.values[idx] = new_m;
        if new_m == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }

        let delta = lr_scale.apply_i32(mom_scale.dequantize_i8(new_m));
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

fn update_momentum_sgd_i8_ef(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    momentum: &mut BlockwiseTensorI8,
    update_error: &mut BlockwiseTensorI8,
    beta_scale: IntScale,
    one_minus_beta_scale: IntScale,
    lr_scale: IntScale,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let mom_scale = momentum.scale_for(idx);
        let old_m = mom_scale.dequantize_i8(momentum.values[idx]);
        let mixed = beta_scale.apply_i32(old_m) + one_minus_beta_scale.apply_i32(grad_i32);
        let new_m = mom_scale.quantize_i32(mixed, rng, stochastic_rounding);
        momentum.values[idx] = new_m;
        if new_m == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }

        let err_scale = update_error.scale_for(idx);
        let carried = err_scale.dequantize_i8(update_error.values[idx]);
        let desired_delta = lr_scale.apply_i32(mom_scale.dequantize_i8(new_m)) + carried;
        let quantized_delta = desired_delta.clamp(i8::MIN as i32, i8::MAX as i32);
        let residual = desired_delta - quantized_delta;
        update_error.values[idx] = err_scale.quantize_i32(residual, rng, stochastic_rounding);
        if quantized_delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let next = (weights.values[idx] as i32 - quantized_delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

fn update_nesterov_sgd_i8(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    momentum: &mut BlockwiseTensorI8,
    beta_scale: IntScale,
    one_minus_beta_scale: IntScale,
    lr_scale: IntScale,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let mom_scale = momentum.scale_for(idx);
        let old_m = mom_scale.dequantize_i8(momentum.values[idx]);
        let mixed = beta_scale.apply_i32(old_m) + one_minus_beta_scale.apply_i32(grad_i32);
        let new_m = mom_scale.quantize_i32(mixed, rng, stochastic_rounding);
        momentum.values[idx] = new_m;
        if new_m == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }

        let lookahead = beta_scale.apply_i32(mom_scale.dequantize_i8(new_m))
            + one_minus_beta_scale.apply_i32(grad_i32);
        let delta = lr_scale.apply_i32(lookahead);
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

fn update_sign_sgd_i8(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    lr_numerator: i32,
    stats: &mut TrainStats,
) {
    let sign_step = lr_numerator.max(1) / 4 + 1;
    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let delta = grad_i32.signum() * sign_step;
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

fn update_sign_sgd_ef_i8(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    error_buf: &mut BlockwiseTensorI8,
    lr_numerator: i32,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    let sign_step = lr_numerator.max(1) / 4 + 1;
    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let err_scale = error_buf.scale_for(idx);
        let corrected = grad_i32 + err_scale.dequantize_i8(error_buf.values[idx]);
        let delta = corrected.signum() * sign_step;
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let residual = corrected - delta;
        let new_err = err_scale.quantize_i32(residual, rng, stochastic_rounding);
        error_buf.values[idx] = new_err;
        if new_err == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }
        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

fn update_sign_sgd_majority_i8(
    weights: &mut BlockwiseTensorI8,
    input: &BlockwiseTensorI8,
    residual: &[i32],
    output_dim: usize,
    input_dim: usize,
    lr_numerator: i32,
    stats: &mut TrainStats,
) {
    let virtual_workers = 4usize.min(input.rows.max(1));
    let vote_sums =
        majority_vote_signs(input, residual, output_dim, input_dim, virtual_workers);
    let sign_step = lr_numerator.max(1) / 4 + 1;
    for (idx, sign_sum) in vote_sums.into_iter().enumerate() {
        let delta = sign_sum.signum() * sign_step;
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

fn majority_vote_signs(
    input: &BlockwiseTensorI8,
    residual: &[i32],
    output_dim: usize,
    input_dim: usize,
    workers: usize,
) -> Vec<i32> {
    let mut vote_sums = vec![0i32; output_dim * input_dim];
    let chunk_rows = input.rows.div_ceil(workers.max(1));
    for worker_idx in 0..workers {
        let row_start = worker_idx * chunk_rows;
        let row_end = (row_start + chunk_rows).min(input.rows);
        if row_start >= row_end {
            continue;
        }
        for o in 0..output_dim {
            for i in 0..input_dim {
                let mut acc = 0i32;
                for r in row_start..row_end {
                    acc += residual[r * output_dim + o] * input.get(r, i) as i32;
                }
                vote_sums[o * input_dim + i] += acc.signum();
            }
        }
    }
    vote_sums
}

fn update_qsgd_i8(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    lr_scale: IntScale,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    let levels = 7i32;
    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let block_scale = grad.scale_for(idx).dequantize_i8(i8::MAX).saturating_abs().max(1);
        let magnitude = grad_i32.saturating_abs();
        let scaled = magnitude * levels;
        let base_level = scaled / block_scale;
        let rem = scaled % block_scale;
        let mut q_level = base_level;
        if stochastic_rounding && rem > 0 {
            let threshold = (rem as u64).saturating_mul(u32::MAX as u64) / block_scale as u64;
            if rng.next_u32() as u64 <= threshold {
                q_level += 1;
            }
        }
        let q_level = q_level.clamp(0, levels);
        let q_grad = grad_i32.signum() * ((q_level * block_scale) / levels.max(1));
        let delta = lr_scale.apply_i32(q_grad);
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

struct MambaLiteRunI8 {
    prev_states: Vec<Vec<i32>>,
    states: Vec<Vec<i32>>,
    outputs: Vec<Vec<i32>>,
}

fn mamba_lite_state_bytes(optimizer: Optimizer, input_dim: usize, state_dim: usize) -> usize {
    let params = state_dim * input_dim + state_dim * state_dim + input_dim * state_dim;
    params * optimizer_bytes_per_param(optimizer)
}

fn make_mamba_lite_sequence(
    seq_len: usize,
    batch_size: usize,
    input_dim: usize,
    step: i32,
    block_size: usize,
    scale: IntScale,
) -> Vec<BlockwiseTensorI8> {
    (0..seq_len)
        .map(|t| {
            let mut batch = BlockwiseTensorI8::zeros(
                &format!("mamba.input.step{t}"),
                batch_size,
                input_dim,
                block_size,
                scale,
            );
            for r in 0..batch_size {
                for c in 0..input_dim {
                    let raw = ((((r * input_dim + c) as i32 + step * 11 + t as i32 * 17) * 7) % 51) - 25;
                    batch.set(r, c, raw as i8);
                }
            }
            batch
        })
        .collect()
}

fn run_mamba_lite_i8(
    sequence: &[BlockwiseTensorI8],
    w_in: &BlockwiseTensorI8,
    w_state: &BlockwiseTensorI8,
    w_out: &BlockwiseTensorI8,
    state_dim: usize,
    input_dim: usize,
    batch_size: usize,
) -> MambaLiteRunI8 {
    let mut prev_state = vec![0i32; batch_size * state_dim];
    let mut prev_states = Vec::with_capacity(sequence.len());
    let mut states = Vec::with_capacity(sequence.len());
    let mut outputs = Vec::with_capacity(sequence.len());
    for token in sequence {
        let mut next_state = vec![0i32; batch_size * state_dim];
        let mut y = vec![0i32; batch_size * input_dim];
        for r in 0..batch_size {
            for h in 0..state_dim {
                let mut acc = 0i32;
                for c in 0..input_dim {
                    acc += token.get(r, c) as i32 * w_in.get(h, c) as i32;
                }
                for c in 0..state_dim {
                    acc += prev_state[r * state_dim + c] * w_state.get(h, c) as i32;
                }
                next_state[r * state_dim + h] = clamp_activation(acc >> 6);
            }
            for o in 0..input_dim {
                let mut acc = 0i32;
                for h in 0..state_dim {
                    acc += next_state[r * state_dim + h] * w_out.get(o, h) as i32;
                }
                y[r * input_dim + o] = clamp_activation(acc >> 6);
            }
        }
        prev_states.push(prev_state.clone());
        states.push(next_state.clone());
        outputs.push(y);
        prev_state = next_state;
    }
    MambaLiteRunI8 {
        prev_states,
        states,
        outputs,
    }
}

fn mamba_lite_prefill(
    optimizer: Optimizer,
    input_dim: usize,
    state_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
) -> i64 {
    let weight_scale = IntScale::new(24, 8);
    let input_scale = IntScale::new(32, 8);
    match optimizer {
        Optimizer::SignSgdEf => {
            let sequence =
                make_mamba_lite_sequence(seq_len, batch_size, input_dim, 0, block_size, input_scale);
            let w_in = BlockwiseTensorI8::from_seeded("mamba.w_in", state_dim, input_dim, block_size, weight_scale, 13);
            let w_state =
                BlockwiseTensorI8::from_seeded("mamba.w_state", state_dim, state_dim, block_size, weight_scale, 17);
            let w_out = BlockwiseTensorI8::from_seeded("mamba.w_out", input_dim, state_dim, block_size, weight_scale, 19);
            run_mamba_lite_i8(&sequence, &w_in, &w_state, &w_out, state_dim, input_dim, batch_size)
                .outputs
                .iter()
                .flatten()
                .map(|v| *v as i64)
                .sum()
        }
        Optimizer::Fp16Momentum | Optimizer::Bf16Adam => {
            let precision = if matches!(optimizer, Optimizer::Fp16Momentum) {
                FloatPrecision::Fp16
            } else {
                FloatPrecision::Bf16
            };
            let sequence =
                make_mamba_lite_sequence(seq_len, batch_size, input_dim, 0, block_size, input_scale);
            let w_in = BlockwiseTensorI8::from_seeded("mamba.w_in", state_dim, input_dim, block_size, weight_scale, 13);
            let w_state =
                BlockwiseTensorI8::from_seeded("mamba.w_state", state_dim, state_dim, block_size, weight_scale, 17);
            let w_out = BlockwiseTensorI8::from_seeded("mamba.w_out", input_dim, state_dim, block_size, weight_scale, 19);
            let outputs = run_mamba_lite_f32(&sequence, &w_in, &w_state, &w_out, state_dim, input_dim, batch_size, precision);
            outputs.iter().flatten().map(|v| *v as i64).sum()
        }
        _ => unreachable!(),
    }
}

fn mamba_lite_decode(
    optimizer: Optimizer,
    input_dim: usize,
    state_dim: usize,
    prompt_len: usize,
    batch_size: usize,
    block_size: usize,
    decode_tokens: usize,
) -> i64 {
    let weight_scale = IntScale::new(24, 8);
    let input_scale = IntScale::new(32, 8);
    let sequence =
        make_mamba_lite_sequence(prompt_len, batch_size, input_dim, 1, block_size, input_scale);
    match optimizer {
        Optimizer::SignSgdEf => {
            let w_in = BlockwiseTensorI8::from_seeded("mamba.w_in", state_dim, input_dim, block_size, weight_scale, 13);
            let w_state =
                BlockwiseTensorI8::from_seeded("mamba.w_state", state_dim, state_dim, block_size, weight_scale, 17);
            let w_out = BlockwiseTensorI8::from_seeded("mamba.w_out", input_dim, state_dim, block_size, weight_scale, 19);
            let prompt = run_mamba_lite_i8(&sequence, &w_in, &w_state, &w_out, state_dim, input_dim, batch_size);
            let mut prev_state = prompt.states.last().cloned().unwrap_or_else(|| vec![0; batch_size * state_dim]);
            let mut sink = 0i64;
            for idx in 0..decode_tokens {
                let token = &make_mamba_lite_sequence(1, batch_size, input_dim, 100 + idx as i32, block_size, input_scale)[0];
                let mut next_state = vec![0i32; batch_size * state_dim];
                for r in 0..batch_size {
                    for h in 0..state_dim {
                        let mut acc = 0i32;
                        for c in 0..input_dim {
                            acc += token.get(r, c) as i32 * w_in.get(h, c) as i32;
                        }
                        for c in 0..state_dim {
                            acc += prev_state[r * state_dim + c] * w_state.get(h, c) as i32;
                        }
                        next_state[r * state_dim + h] = clamp_activation(acc >> 6);
                    }
                    for o in 0..input_dim {
                        let mut acc = 0i32;
                        for h in 0..state_dim {
                            acc += next_state[r * state_dim + h] * w_out.get(o, h) as i32;
                        }
                        sink += clamp_activation(acc >> 6) as i64;
                    }
                }
                prev_state = next_state;
            }
            sink
        }
        Optimizer::Fp16Momentum | Optimizer::Bf16Adam => {
            let precision = if matches!(optimizer, Optimizer::Fp16Momentum) {
                FloatPrecision::Fp16
            } else {
                FloatPrecision::Bf16
            };
            let w_in = BlockwiseTensorI8::from_seeded("mamba.w_in", state_dim, input_dim, block_size, weight_scale, 13);
            let w_state =
                BlockwiseTensorI8::from_seeded("mamba.w_state", state_dim, state_dim, block_size, weight_scale, 17);
            let w_out = BlockwiseTensorI8::from_seeded("mamba.w_out", input_dim, state_dim, block_size, weight_scale, 19);
            let (w_in_f, w_state_f, w_out_f) =
                mamba_lite_weights_f32(&w_in, &w_state, &w_out, precision);
            let prompt =
                run_mamba_lite_f32_with_state(&sequence, &w_in_f, &w_state_f, &w_out_f, state_dim, input_dim, batch_size, precision, None);
            let mut prev_state = prompt.last_state;
            let mut sink = 0i64;
            for idx in 0..decode_tokens {
                let token = &make_mamba_lite_sequence(1, batch_size, input_dim, 100 + idx as i32, block_size, input_scale)[0];
                let out = run_mamba_lite_f32_with_state(
                    std::slice::from_ref(token),
                    &w_in_f,
                    &w_state_f,
                    &w_out_f,
                    state_dim,
                    input_dim,
                    batch_size,
                    precision,
                    Some(prev_state),
                );
                prev_state = out.last_state;
                sink += out.outputs.iter().flatten().map(|v| *v as i64).sum::<i64>();
            }
            sink
        }
        _ => unreachable!(),
    }
}

fn mamba_lite_train_step(
    optimizer: Optimizer,
    input_dim: usize,
    state_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    lr_numerator: i32,
) -> TrainStats {
    let input_scale = IntScale::new(32, 8);
    let weight_scale = IntScale::new(24, 8);
    let mut rng = Lcg64::new(0x8080_dead_beef_u64);
    let sequence = make_mamba_lite_sequence(seq_len, batch_size, input_dim, 0, block_size, input_scale);

    match optimizer {
        Optimizer::SignSgdEf => {
            let mut w_in =
                BlockwiseTensorI8::from_seeded("mamba.w_in", state_dim, input_dim, block_size, weight_scale, 13);
            let teacher_in =
                BlockwiseTensorI8::from_seeded("mamba.teacher_in", state_dim, input_dim, block_size, weight_scale, 23);
            let mut w_state =
                BlockwiseTensorI8::from_seeded("mamba.w_state", state_dim, state_dim, block_size, weight_scale, 17);
            let teacher_state = BlockwiseTensorI8::from_seeded(
                "mamba.teacher_state",
                state_dim,
                state_dim,
                block_size,
                weight_scale,
                29,
            );
            let mut w_out =
                BlockwiseTensorI8::from_seeded("mamba.w_out", input_dim, state_dim, block_size, weight_scale, 19);
            let teacher_out =
                BlockwiseTensorI8::from_seeded("mamba.teacher_out", input_dim, state_dim, block_size, weight_scale, 31);
            let mut err_in = BlockwiseTensorI8::zeros("mamba.err_in", state_dim, input_dim, block_size, IntScale::new(1, 0));
            let mut err_state =
                BlockwiseTensorI8::zeros("mamba.err_state", state_dim, state_dim, block_size, IntScale::new(1, 0));
            let mut err_out =
                BlockwiseTensorI8::zeros("mamba.err_out", input_dim, state_dim, block_size, IntScale::new(1, 0));

            let student = run_mamba_lite_i8(&sequence, &w_in, &w_state, &w_out, state_dim, input_dim, batch_size);
            let teacher =
                run_mamba_lite_i8(&sequence, &teacher_in, &teacher_state, &teacher_out, state_dim, input_dim, batch_size);
            let residuals: Vec<Vec<i32>> = student
                .outputs
                .iter()
                .zip(teacher.outputs.iter())
                .map(|(a, b)| diff_i32(a, b))
                .collect();

            let mut hidden_residuals = Vec::with_capacity(seq_len);
            for (step_idx, residual) in residuals.iter().enumerate() {
                let mut hidden = vec![0i32; batch_size * state_dim];
                for r in 0..batch_size {
                    for h in 0..state_dim {
                        let mut acc = 0i32;
                        for o in 0..input_dim {
                            acc += residual[r * input_dim + o] * w_out.get(o, h) as i32;
                        }
                        hidden[r * state_dim + h] = clamp_activation(acc >> 6);
                    }
                }
                let _ = step_idx;
                hidden_residuals.push(hidden);
            }

            let grad_in = recurrent_input_grad(
                &sequence,
                &hidden_residuals,
                state_dim,
                input_dim,
                block_size,
                IntScale::new(8, 8),
                ScaleMode::Max,
                &mut rng,
                true,
            );
            let grad_state = recurrent_state_grad(
                &student.prev_states,
                &hidden_residuals,
                state_dim,
                block_size,
                IntScale::new(8, 8),
                ScaleMode::Max,
                &mut rng,
                true,
            );
            let grad_out = mamba_output_grad(
                &student.states,
                &residuals,
                input_dim,
                state_dim,
                block_size,
                &mut rng,
            );

            let mut stats = empty_stats("signsgd-ef", block_size, lr_numerator);
            stats.loss_l1_sum = residuals
                .iter()
                .flat_map(|v| v.iter())
                .map(|v| i64::from(*v).abs())
                .sum();
            update_sign_sgd_ef_i8(&mut w_in, &grad_in, &mut err_in, lr_numerator, &mut stats, &mut rng, true);
            update_sign_sgd_ef_i8(
                &mut w_state,
                &grad_state,
                &mut err_state,
                lr_numerator,
                &mut stats,
                &mut rng,
                true,
            );
            update_sign_sgd_ef_i8(&mut w_out, &grad_out, &mut err_out, lr_numerator, &mut stats, &mut rng, true);
            stats
        }
        Optimizer::Fp16Momentum | Optimizer::Bf16Adam => {
            let precision = if matches!(optimizer, Optimizer::Fp16Momentum) {
                FloatPrecision::Fp16
            } else {
                FloatPrecision::Bf16
            };
            mamba_lite_train_step_float(
                precision,
                matches!(optimizer, Optimizer::Bf16Adam),
                input_dim,
                state_dim,
                seq_len,
                batch_size,
                block_size,
                lr_numerator,
            )
        }
        _ => unreachable!(),
    }
}

fn empty_stats(name: &str, block_size: usize, lr_numerator: i32) -> TrainStats {
    TrainStats {
        steps: 1,
        block_size,
        stochastic_rounding: true,
        optimizer: name.to_string(),
        scale_mode: "max".to_string(),
        v_scale_mode: "max".to_string(),
        grad_sq_scale_numerator: 0,
        grad_sq_scale_shift: 0,
        beta2_numerator: 0,
        beta2_shift: 0,
        v_quant_scheme: "n/a".to_string(),
        denom_mode: "n/a".to_string(),
        denom_shift: 0,
        lr_numerator,
        loss_l1_sum: 0,
        nonzero_weight_updates: 0,
        zeroed_weight_updates: 0,
        nonzero_momentum_updates: 0,
        zeroed_momentum_updates: 0,
        nonzero_v_updates: 0,
        zeroed_v_updates: 0,
        grad_saturation: 0,
        weight_saturation: 0,
        momentum_saturation: 0,
        v_saturation: 0,
    }
}

fn mamba_output_grad(
    states: &[Vec<i32>],
    residuals: &[Vec<i32>],
    output_dim: usize,
    state_dim: usize,
    block_size: usize,
    rng: &mut Lcg64,
) -> BlockwiseTensorI8 {
    let mut accum = vec![0i32; output_dim * state_dim];
    for (state, residual) in states.iter().zip(residuals.iter()) {
        let batch_size = state.len() / state_dim;
        for o in 0..output_dim {
            for h in 0..state_dim {
                let mut acc = 0i32;
                for r in 0..batch_size {
                    acc += residual[r * output_dim + o] * state[r * state_dim + h];
                }
                accum[o * state_dim + h] += acc >> 12;
            }
        }
    }
    quantize_blockwise(
        "mamba.grad_out",
        output_dim,
        state_dim,
        block_size,
        &accum,
        IntScale::new(8, 8),
        ScaleMode::Max,
        rng,
        true,
    )
}

struct MambaLiteRunF32 {
    outputs: Vec<Vec<f32>>,
    last_state: Vec<f32>,
}

fn mamba_lite_weights_f32(
    w_in: &BlockwiseTensorI8,
    w_state: &BlockwiseTensorI8,
    w_out: &BlockwiseTensorI8,
    precision: FloatPrecision,
) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
    (
        w_in.values.iter().map(|&v| quantize_float(v as f32, precision)).collect(),
        w_state.values.iter().map(|&v| quantize_float(v as f32, precision)).collect(),
        w_out.values.iter().map(|&v| quantize_float(v as f32, precision)).collect(),
    )
}

fn run_mamba_lite_f32(
    sequence: &[BlockwiseTensorI8],
    w_in: &BlockwiseTensorI8,
    w_state: &BlockwiseTensorI8,
    w_out: &BlockwiseTensorI8,
    state_dim: usize,
    input_dim: usize,
    batch_size: usize,
    precision: FloatPrecision,
) -> Vec<Vec<f32>> {
    let (w_in_f, w_state_f, w_out_f) = mamba_lite_weights_f32(w_in, w_state, w_out, precision);
    run_mamba_lite_f32_with_state(
        sequence,
        &w_in_f,
        &w_state_f,
        &w_out_f,
        state_dim,
        input_dim,
        batch_size,
        precision,
        None,
    )
    .outputs
}

fn run_mamba_lite_f32_with_state(
    sequence: &[BlockwiseTensorI8],
    w_in: &[f32],
    w_state: &[f32],
    w_out: &[f32],
    state_dim: usize,
    input_dim: usize,
    batch_size: usize,
    precision: FloatPrecision,
    initial_state: Option<Vec<f32>>,
) -> MambaLiteRunF32 {
    let mut prev_state = initial_state.unwrap_or_else(|| vec![0.0; batch_size * state_dim]);
    let mut outputs = Vec::with_capacity(sequence.len());
    for token in sequence {
        let mut next_state = vec![0.0f32; batch_size * state_dim];
        let mut y = vec![0.0f32; batch_size * input_dim];
        for r in 0..batch_size {
            for h in 0..state_dim {
                let mut acc = 0.0f32;
                for c in 0..input_dim {
                    acc += token.get(r, c) as f32 * w_in[h * input_dim + c];
                }
                for c in 0..state_dim {
                    acc += prev_state[r * state_dim + c] * w_state[h * state_dim + c];
                }
                next_state[r * state_dim + h] = quantize_float((acc / 64.0).clamp(-96.0, 96.0), precision);
            }
            for o in 0..input_dim {
                let mut acc = 0.0f32;
                for h in 0..state_dim {
                    acc += next_state[r * state_dim + h] * w_out[o * state_dim + h];
                }
                y[r * input_dim + o] = quantize_float((acc / 64.0).clamp(-96.0, 96.0), precision);
            }
        }
        outputs.push(y);
        prev_state = next_state;
    }
    MambaLiteRunF32 { outputs, last_state: prev_state }
}

fn mamba_lite_train_step_float(
    precision: FloatPrecision,
    adam_mode: bool,
    input_dim: usize,
    state_dim: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    lr_numerator: i32,
) -> TrainStats {
    let input_scale = IntScale::new(32, 8);
    let weight_scale = IntScale::new(24, 8);
    let lr = lr_numerator as f32 / 1024.0;
    let beta1 = 7.0f32 / 8.0;
    let beta2 = 7.0f32 / 8.0;
    let eps = 1e-4f32;
    let sequence = make_mamba_lite_sequence(seq_len, batch_size, input_dim, 0, block_size, input_scale);
    let w_in = BlockwiseTensorI8::from_seeded("mamba.w_in", state_dim, input_dim, block_size, weight_scale, 13);
    let w_state = BlockwiseTensorI8::from_seeded("mamba.w_state", state_dim, state_dim, block_size, weight_scale, 17);
    let w_out = BlockwiseTensorI8::from_seeded("mamba.w_out", input_dim, state_dim, block_size, weight_scale, 19);
    let t_in = BlockwiseTensorI8::from_seeded("mamba.teacher_in", state_dim, input_dim, block_size, weight_scale, 23);
    let t_state =
        BlockwiseTensorI8::from_seeded("mamba.teacher_state", state_dim, state_dim, block_size, weight_scale, 29);
    let t_out = BlockwiseTensorI8::from_seeded("mamba.teacher_out", input_dim, state_dim, block_size, weight_scale, 31);
    let (mut w_in_f, mut w_state_f, mut w_out_f) = mamba_lite_weights_f32(&w_in, &w_state, &w_out, precision);
    let (t_in_f, t_state_f, t_out_f) = mamba_lite_weights_f32(&t_in, &t_state, &t_out, precision);
    let student = run_mamba_lite_f32_with_state(
        &sequence,
        &w_in_f,
        &w_state_f,
        &w_out_f,
        state_dim,
        input_dim,
        batch_size,
        precision,
        None,
    );
    let teacher = run_mamba_lite_f32_with_state(
        &sequence,
        &t_in_f,
        &t_state_f,
        &t_out_f,
        state_dim,
        input_dim,
        batch_size,
        precision,
        None,
    );
    let mut stats = empty_stats(if adam_mode { "bf16-adam" } else { "fp16-momentum" }, block_size, lr_numerator);
    let mut grad_out = vec![0.0f32; input_dim * state_dim];
    let mut grad_in = vec![0.0f32; state_dim * input_dim];
    let mut grad_state = vec![0.0f32; state_dim * state_dim];
    let mut m_out = vec![0.0f32; w_out_f.len()];
    let mut m_in = vec![0.0f32; w_in_f.len()];
    let mut m_state = vec![0.0f32; w_state_f.len()];
    let mut v_out = vec![0.0f32; w_out_f.len()];
    let mut v_in = vec![0.0f32; w_in_f.len()];
    let mut v_state = vec![0.0f32; w_state_f.len()];
    let mut prev_state = vec![0.0f32; batch_size * state_dim];

    for t in 0..seq_len {
        let residual: Vec<f32> = student.outputs[t]
            .iter()
            .zip(teacher.outputs[t].iter())
            .map(|(a, b)| quantize_float(*a - *b, precision))
            .collect();
        stats.loss_l1_sum += residual.iter().map(|v| v.abs() as i64).sum::<i64>();
        let mut hidden = vec![0.0f32; batch_size * state_dim];
        for r in 0..batch_size {
            for h in 0..state_dim {
                let mut acc = 0.0f32;
                for o in 0..input_dim {
                    acc += residual[r * input_dim + o] * w_out_f[o * state_dim + h];
                }
                hidden[r * state_dim + h] = quantize_float(acc / 64.0, precision);
            }
        }
        for o in 0..input_dim {
            for h in 0..state_dim {
                let mut acc = 0.0f32;
                for r in 0..batch_size {
                    acc += residual[r * input_dim + o] * student.last_state[r * state_dim + h];
                }
                grad_out[o * state_dim + h] += quantize_float(acc / 4096.0, precision);
            }
        }
        for h in 0..state_dim {
            for i in 0..input_dim {
                let mut acc = 0.0f32;
                for r in 0..batch_size {
                    acc += hidden[r * state_dim + h] * sequence[t].get(r, i) as f32;
                }
                grad_in[h * input_dim + i] += quantize_float(acc / 4096.0, precision);
            }
            for i in 0..state_dim {
                let mut acc = 0.0f32;
                for r in 0..batch_size {
                    acc += hidden[r * state_dim + h] * prev_state[r * state_dim + i];
                }
                grad_state[h * state_dim + i] += quantize_float(acc / 4096.0, precision);
            }
        }
        prev_state = student.last_state.clone();
    }

    update_float_params(&mut w_out_f, &grad_out, &mut m_out, &mut v_out, precision, adam_mode, lr, beta1, beta2, eps, &mut stats);
    update_float_params(&mut w_in_f, &grad_in, &mut m_in, &mut v_in, precision, adam_mode, lr, beta1, beta2, eps, &mut stats);
    update_float_params(&mut w_state_f, &grad_state, &mut m_state, &mut v_state, precision, adam_mode, lr, beta1, beta2, eps, &mut stats);
    stats
}

#[allow(clippy::too_many_arguments)]
fn update_float_params(
    weights: &mut [f32],
    grad: &[f32],
    m: &mut [f32],
    v: &mut [f32],
    precision: FloatPrecision,
    adam_mode: bool,
    lr: f32,
    beta1: f32,
    beta2: f32,
    eps: f32,
    stats: &mut TrainStats,
) {
    for idx in 0..weights.len() {
        let g = quantize_float(grad[idx], precision);
        m[idx] = quantize_float(beta1 * m[idx] + (1.0 - beta1) * g, precision);
        let delta = if adam_mode {
            v[idx] = quantize_float(beta2 * v[idx] + (1.0 - beta2) * g * g, precision);
            quantize_float(lr * m[idx] / (v[idx].sqrt() + eps), precision)
        } else {
            quantize_float(lr * m[idx], precision)
        };
        if delta == 0.0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        weights[idx] = quantize_float(weights[idx] - delta, precision);
    }
}

fn mamba2_full_forward_run(
    optimizer: Optimizer,
    dim: usize,
    state_dim: usize,
    expand: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
) -> i64 {
    let inner = dim * expand;
    let input_scale = IntScale::new(32, 8);
    let weight_scale = IntScale::new(24, 8);
    let sequence = make_mamba_lite_sequence(seq_len, batch_size, dim, 0, block_size, input_scale);

    match optimizer {
        Optimizer::SignSgdEf => {
            let w_in_proj = BlockwiseTensorI8::from_seeded(
                "mamba2.in_proj",
                inner * 2,
                dim,
                block_size,
                weight_scale,
                41,
            );
            let w_dt = BlockwiseTensorI8::from_seeded("mamba2.dt", inner, inner, block_size, weight_scale, 43);
            let w_b = BlockwiseTensorI8::from_seeded(
                "mamba2.B",
                inner * state_dim,
                inner,
                block_size,
                weight_scale,
                47,
            );
            let w_c = BlockwiseTensorI8::from_seeded(
                "mamba2.C",
                inner * state_dim,
                inner,
                block_size,
                weight_scale,
                53,
            );
            let w_out =
                BlockwiseTensorI8::from_seeded("mamba2.out", dim, inner, block_size, weight_scale, 59);
            let mut sink = 0i64;
            for token in &sequence {
                let normed = layer_norm_i8(token);
                let xz = matmul_i8(&normed, &w_in_proj);
                for r in 0..batch_size {
                    let mut x_in = vec![0i32; inner];
                    let mut z = vec![0i32; inner];
                    for i in 0..inner {
                        x_in[i] = xz[r * (inner * 2) + i];
                        z[i] = silu_i32(xz[r * (inner * 2) + inner + i]);
                    }
                    let dt = linear_vec_i8(&x_in, &w_dt, inner, inner);
                    let b_proj = linear_vec_i8(&x_in, &w_b, inner * state_dim, inner);
                    let c_proj = linear_vec_i8(&x_in, &w_c, inner * state_dim, inner);
                    let mut y = vec![0i32; inner];
                    for i in 0..inner {
                        let dt_v = softplus_i32(dt[i]);
                        let mut acc = 0i32;
                        for s in 0..state_dim {
                            let bv = ((dt_v as i64 * b_proj[i * state_dim + s] as i64) >> 6)
                                .clamp(i32::MIN as i64, i32::MAX as i64) as i32;
                            let cv = c_proj[i * state_dim + s];
                            let term = ((cv as i64 * bv as i64) >> 6)
                                .clamp(i32::MIN as i64, i32::MAX as i64) as i32;
                            acc = acc.saturating_add(term);
                        }
                        y[i] = acc + ((x_in[i] * 6) >> 6);
                    }
                    let yz: Vec<i32> = y
                        .iter()
                        .zip(z.iter())
                        .map(|(a, b)| {
                            ((i64::from(*a) * i64::from(*b)) >> 6)
                                .clamp(i32::MIN as i64, i32::MAX as i64) as i32
                        })
                        .collect();
                    let out = linear_vec_i8(&yz, &w_out, dim, inner);
                    for o in 0..dim {
                        sink = sink.saturating_add((out[o] + token.get(r, o) as i32) as i64);
                    }
                }
            }
            sink
        }
        Optimizer::Fp16Momentum | Optimizer::Bf16Adam => {
            let precision = if matches!(optimizer, Optimizer::Fp16Momentum) {
                FloatPrecision::Fp16
            } else {
                FloatPrecision::Bf16
            };
            let w_in_proj = BlockwiseTensorI8::from_seeded(
                "mamba2.in_proj",
                inner * 2,
                dim,
                block_size,
                weight_scale,
                41,
            );
            let w_dt = BlockwiseTensorI8::from_seeded("mamba2.dt", inner, inner, block_size, weight_scale, 43);
            let w_b = BlockwiseTensorI8::from_seeded(
                "mamba2.B",
                inner * state_dim,
                inner,
                block_size,
                weight_scale,
                47,
            );
            let w_c = BlockwiseTensorI8::from_seeded(
                "mamba2.C",
                inner * state_dim,
                inner,
                block_size,
                weight_scale,
                53,
            );
            let w_out =
                BlockwiseTensorI8::from_seeded("mamba2.out", dim, inner, block_size, weight_scale, 59);
            let w_in_proj_f: Vec<f32> =
                w_in_proj.values.iter().map(|&v| quantize_float(v as f32, precision)).collect();
            let w_dt_f: Vec<f32> = w_dt.values.iter().map(|&v| quantize_float(v as f32, precision)).collect();
            let w_b_f: Vec<f32> = w_b.values.iter().map(|&v| quantize_float(v as f32, precision)).collect();
            let w_c_f: Vec<f32> = w_c.values.iter().map(|&v| quantize_float(v as f32, precision)).collect();
            let w_out_f: Vec<f32> = w_out.values.iter().map(|&v| quantize_float(v as f32, precision)).collect();
            let mut sink = 0i64;
            for token in &sequence {
                let normed = layer_norm_i8(token);
                let xz = linear_batch_f32(&normed, &w_in_proj_f, inner * 2, dim, precision);
                for r in 0..batch_size {
                    let mut x_in = vec![0.0f32; inner];
                    let mut z = vec![0.0f32; inner];
                    for i in 0..inner {
                        x_in[i] = xz[r * (inner * 2) + i];
                        z[i] = silu_f32(xz[r * (inner * 2) + inner + i], precision);
                    }
                    let dt = linear_vec_f32(&x_in, &w_dt_f, inner, inner, precision);
                    let b_proj = linear_vec_f32(&x_in, &w_b_f, inner * state_dim, inner, precision);
                    let c_proj = linear_vec_f32(&x_in, &w_c_f, inner * state_dim, inner, precision);
                    let mut y = vec![0.0f32; inner];
                    for i in 0..inner {
                        let dt_v = softplus_f32(dt[i], precision);
                        let mut acc = 0.0f32;
                        for s in 0..state_dim {
                            let bv = quantize_float(dt_v * b_proj[i * state_dim + s], precision);
                            let cv = c_proj[i * state_dim + s];
                            acc = quantize_float(acc + quantize_float(cv * bv, precision), precision);
                        }
                        y[i] = quantize_float(acc + quantize_float(0.1 * x_in[i], precision), precision);
                    }
                    let yz: Vec<f32> = y
                        .iter()
                        .zip(z.iter())
                        .map(|(a, b)| quantize_float(a * b, precision))
                        .collect();
                    let out = linear_vec_f32(&yz, &w_out_f, dim, inner, precision);
                    for o in 0..dim {
                        sink = sink.saturating_add(
                            quantize_float(out[o] + token.get(r, o) as f32, precision) as i64,
                        );
                    }
                }
            }
            sink
        }
        _ => unreachable!(),
    }
}

struct Mamba2FullCpuActivations {
    yz_tokens: Vec<Vec<i32>>,
    outputs: Vec<Vec<i32>>,
}

#[allow(clippy::type_complexity)]
fn build_mamba2_full_seed_tensors(
    dim: usize,
    state_dim: usize,
    expand: usize,
    block_size: usize,
) -> (
    BlockwiseTensorI8,
    BlockwiseTensorI8,
    BlockwiseTensorI8,
    BlockwiseTensorI8,
    BlockwiseTensorI8,
    BlockwiseTensorI8,
) {
    let inner = dim * expand;
    let weight_scale = IntScale::new(24, 8);
    (
        BlockwiseTensorI8::from_seeded("mamba2.in_proj", inner * 2, dim, block_size, weight_scale, 41),
        BlockwiseTensorI8::from_seeded("mamba2.dt", inner, inner, block_size, weight_scale, 43),
        BlockwiseTensorI8::from_seeded("mamba2.B", inner * state_dim, inner, block_size, weight_scale, 47),
        BlockwiseTensorI8::from_seeded("mamba2.C", inner * state_dim, inner, block_size, weight_scale, 53),
        BlockwiseTensorI8::from_seeded("mamba2.out", dim, inner, block_size, weight_scale, 59),
        BlockwiseTensorI8::from_seeded("mamba2.out.teacher", dim, inner, block_size, weight_scale, 67),
    )
}

fn mamba2_full_cpu_activations(
    sequence: &[BlockwiseTensorI8],
    w_in_proj: &BlockwiseTensorI8,
    w_dt: &BlockwiseTensorI8,
    w_b: &BlockwiseTensorI8,
    w_c: &BlockwiseTensorI8,
    w_out: &BlockwiseTensorI8,
    dim: usize,
    state_dim: usize,
    expand: usize,
    batch_size: usize,
) -> Mamba2FullCpuActivations {
    let inner = dim * expand;
    let mut yz_tokens = Vec::with_capacity(sequence.len());
    let mut outputs = Vec::with_capacity(sequence.len());
    for token in sequence {
        let normed = layer_norm_i8(token);
        let xz = matmul_i8(&normed, w_in_proj);
        let mut yz_all = vec![0i32; batch_size * inner];
        let mut out_all = vec![0i32; batch_size * dim];
        for r in 0..batch_size {
            let mut x_in = vec![0i32; inner];
            let mut z = vec![0i32; inner];
            for i in 0..inner {
                x_in[i] = xz[r * (inner * 2) + i];
                z[i] = silu_i32(xz[r * (inner * 2) + inner + i]);
            }
            let dt = linear_vec_i8(&x_in, w_dt, inner, inner);
            let b_proj = linear_vec_i8(&x_in, w_b, inner * state_dim, inner);
            let c_proj = linear_vec_i8(&x_in, w_c, inner * state_dim, inner);
            let mut yz = vec![0i32; inner];
            for i in 0..inner {
                let dt_v = softplus_i32(dt[i]);
                let mut acc = 0i32;
                for s in 0..state_dim {
                    let bv = ((dt_v as i64 * b_proj[i * state_dim + s] as i64) >> 6)
                        .clamp(i32::MIN as i64, i32::MAX as i64) as i32;
                    let cv = c_proj[i * state_dim + s];
                    let term = ((cv as i64 * bv as i64) >> 6)
                        .clamp(i32::MIN as i64, i32::MAX as i64) as i32;
                    acc = acc.saturating_add(term);
                }
                let y = acc + ((x_in[i] * 6) >> 6);
                yz[i] = ((i64::from(y) * i64::from(z[i])) >> 6)
                    .clamp(i32::MIN as i64, i32::MAX as i64) as i32;
            }
            let out = linear_vec_i8(&yz, w_out, dim, inner);
            for i in 0..inner {
                yz_all[r * inner + i] = yz[i];
            }
            for o in 0..dim {
                out_all[r * dim + o] = out[o] + token.get(r, o) as i32;
            }
        }
        yz_tokens.push(yz_all);
        outputs.push(out_all);
    }
    Mamba2FullCpuActivations { yz_tokens, outputs }
}

fn mamba2_outproj_grad(
    yz_tokens: &[Vec<i32>],
    residuals: &[Vec<i32>],
    dim: usize,
    inner: usize,
    block_size: usize,
    rng: &mut Lcg64,
) -> BlockwiseTensorI8 {
    let mut accum = vec![0i32; dim * inner];
    for (yz, residual) in yz_tokens.iter().zip(residuals.iter()) {
        let batch_size = yz.len() / inner;
        for o in 0..dim {
            for i in 0..inner {
                let mut acc = 0i64;
                for r in 0..batch_size {
                    acc += i64::from(residual[r * dim + o]) * i64::from(yz[r * inner + i]);
                }
                let term = (acc >> 12).clamp(i32::MIN as i64, i32::MAX as i64) as i32;
                accum[o * inner + i] = accum[o * inner + i].saturating_add(term);
            }
        }
    }
    quantize_blockwise(
        "mamba2.grad_out",
        dim,
        inner,
        block_size,
        &accum,
        IntScale::new(8, 8),
        ScaleMode::Max,
        rng,
        true,
    )
}

fn mamba2_outproj_train_step_wgpu(
    runtime: &WgpuMamba2FullForward,
    dim: usize,
    state_dim: usize,
    expand: usize,
    seq_len: usize,
    batch_size: usize,
    block_size: usize,
    lr_numerator: i32,
) -> Result<TrainStats> {
    let input_scale = IntScale::new(32, 8);
    let sequence = make_mamba_lite_sequence(seq_len, batch_size, dim, 0, block_size, input_scale);
    let (w_in_proj, w_dt, w_b, w_c, w_out, teacher_out) =
        build_mamba2_full_seed_tensors(dim, state_dim, expand, block_size);
    let input_vals = flatten_sequence_i32(&sequence);
    let w_out_values: Vec<i32> = w_out.values.iter().map(|&v| v as i32).collect();
    let w_in_proj_values: Vec<i32> = w_in_proj.values.iter().map(|&v| v as i32).collect();
    let (student_out, student_yz) = runtime.run_with_tensors_outputs(
        &sequence,
        &w_in_proj,
        &w_dt,
        &w_b,
        &w_c,
        &w_out,
        dim,
        state_dim,
        expand,
        batch_size,
    )?;
    let (teacher_out_gpu, _) = runtime.run_with_tensors_outputs(
        &sequence,
        &w_in_proj,
        &w_dt,
        &w_b,
        &w_c,
        &teacher_out,
        dim,
        state_dim,
        expand,
        batch_size,
    )?;
    let tokens = seq_len * batch_size;
    let residual = runtime.sub_i32(&student_out, &teacher_out_gpu)?;
    let grad_values =
        runtime.outproj_grad_reduce_i32(&student_yz, &residual, tokens, dim, dim * expand)?;
    let inproj_grad_values =
        runtime.inproj_grad_reduce_i32(&input_vals, &residual, &w_out_values, tokens, dim, dim * expand)?;
    let mut stats = empty_stats("signsgd-ef-outproj", block_size, lr_numerator);
    stats.loss_l1_sum = residual.iter().map(|v| i64::from(*v).abs()).sum();
    let out_error = vec![0i32; w_out.values.len()];
    let inproj_error = vec![0i32; w_in_proj.values.len()];
    let (updated_out_weights, updated_out_error) =
        runtime.signsgd_ef_update_i8(&w_out_values, &grad_values, &out_error, lr_numerator)?;
    let (updated_inproj_weights, updated_inproj_error) = runtime.signsgd_ef_update_i8(
        &w_in_proj_values,
        &inproj_grad_values,
        &inproj_error,
        lr_numerator,
    )?;
    for (w_before, w_after) in w_out_values.iter().zip(updated_out_weights.iter()) {
        let delta = *w_before - *w_after;
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
    }
    for (w_before, w_after) in w_in_proj_values.iter().zip(updated_inproj_weights.iter()) {
        let delta = *w_before - *w_after;
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
    }
    for err in updated_out_error.into_iter().chain(updated_inproj_error.into_iter()) {
        if err == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }
    }
    Ok(stats)
}

struct WgpuMamba2FullForward {
    device: wgpu::Device,
    queue: wgpu::Queue,
    forward_pipeline: wgpu::ComputePipeline,
    forward_layout: wgpu::BindGroupLayout,
    sub_pipeline: wgpu::ComputePipeline,
    sub_layout: wgpu::BindGroupLayout,
    grad_pipeline: wgpu::ComputePipeline,
    grad_layout: wgpu::BindGroupLayout,
    inproj_grad_pipeline: wgpu::ComputePipeline,
    inproj_grad_layout: wgpu::BindGroupLayout,
    update_pipeline: wgpu::ComputePipeline,
    update_layout: wgpu::BindGroupLayout,
}

struct WgpuMamba2FullForwardFp16 {
    device: wgpu::Device,
    queue: wgpu::Queue,
    forward_pipeline: wgpu::ComputePipeline,
    forward_layout: wgpu::BindGroupLayout,
}

impl WgpuMamba2FullForward {
    async fn new() -> Result<Self> {
        let instance = wgpu::Instance::default();
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                power_preference: wgpu::PowerPreference::HighPerformance,
                ..Default::default()
            })
            .await
            .context("no wgpu adapter available")?;
        let (device, queue) = adapter
            .request_device(&wgpu::DeviceDescriptor::default(), None)
            .await
            .context("request wgpu device")?;

        let forward_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("mamba2-full-forward-int8"),
            entries: &[
                storage_layout_entry(0, true),
                storage_layout_entry(1, true),
                storage_layout_entry(2, true),
                storage_layout_entry(3, true),
                storage_layout_entry(4, true),
                storage_layout_entry(5, true),
                uniform_layout_entry(6),
                storage_layout_entry(7, false),
                storage_layout_entry(8, false),
            ],
        });
        let module = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("mamba2-full-forward-int8"),
            source: wgpu::ShaderSource::Wgsl(include_str!("mamba2_full_forward_int8.wgsl").into()),
        });
        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("mamba2-full-forward-int8"),
            bind_group_layouts: &[&forward_layout],
            push_constant_ranges: &[],
        });
        let forward_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("mamba2-full-forward-int8"),
            layout: Some(&pipeline_layout),
            module: &module,
            entry_point: Some("main"),
            compilation_options: Default::default(),
            cache: None,
        });
        let sub_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("sub-i32"),
            entries: &[
                storage_layout_entry(0, true),
                storage_layout_entry(1, true),
                storage_layout_entry(2, false),
                uniform_layout_entry(3),
            ],
        });
        let sub_module = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("sub-i32"),
            source: wgpu::ShaderSource::Wgsl(include_str!("sub_i32.wgsl").into()),
        });
        let sub_pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("sub-i32"),
            bind_group_layouts: &[&sub_layout],
            push_constant_ranges: &[],
        });
        let sub_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("sub-i32"),
            layout: Some(&sub_pipeline_layout),
            module: &sub_module,
            entry_point: Some("main"),
            compilation_options: Default::default(),
            cache: None,
        });
        let grad_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("outproj-grad-reduce-int8"),
            entries: &[
                storage_layout_entry(0, true),
                storage_layout_entry(1, true),
                storage_layout_entry(2, false),
                uniform_layout_entry(3),
            ],
        });
        let grad_module = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("outproj-grad-reduce-int8"),
            source: wgpu::ShaderSource::Wgsl(include_str!("outproj_grad_reduce_int8.wgsl").into()),
        });
        let grad_pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("outproj-grad-reduce-int8"),
            bind_group_layouts: &[&grad_layout],
            push_constant_ranges: &[],
        });
        let grad_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("outproj-grad-reduce-int8"),
            layout: Some(&grad_pipeline_layout),
            module: &grad_module,
            entry_point: Some("main"),
            compilation_options: Default::default(),
            cache: None,
        });
        let inproj_grad_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("inproj-grad-reduce-int8"),
            entries: &[
                storage_layout_entry(0, true),
                storage_layout_entry(1, true),
                storage_layout_entry(2, true),
                storage_layout_entry(3, false),
                uniform_layout_entry(4),
            ],
        });
        let inproj_grad_module = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("inproj-grad-reduce-int8"),
            source: wgpu::ShaderSource::Wgsl(include_str!("inproj_grad_reduce_int8.wgsl").into()),
        });
        let inproj_grad_pipeline_layout =
            device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
                label: Some("inproj-grad-reduce-int8"),
                bind_group_layouts: &[&inproj_grad_layout],
                push_constant_ranges: &[],
            });
        let inproj_grad_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("inproj-grad-reduce-int8"),
            layout: Some(&inproj_grad_pipeline_layout),
            module: &inproj_grad_module,
            entry_point: Some("main"),
            compilation_options: Default::default(),
            cache: None,
        });
        let update_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("signsgd-ef-update-int8"),
            entries: &[
                storage_layout_entry(0, false),
                storage_layout_entry(1, true),
                storage_layout_entry(2, false),
                uniform_layout_entry(3),
            ],
        });
        let update_module = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("signsgd-ef-update-int8"),
            source: wgpu::ShaderSource::Wgsl(include_str!("signsgd_ef_update_int8.wgsl").into()),
        });
        let update_pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("signsgd-ef-update-int8"),
            bind_group_layouts: &[&update_layout],
            push_constant_ranges: &[],
        });
        let update_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("signsgd-ef-update-int8"),
            layout: Some(&update_pipeline_layout),
            module: &update_module,
            entry_point: Some("main"),
            compilation_options: Default::default(),
            cache: None,
        });
        Ok(Self {
            device,
            queue,
            forward_pipeline,
            forward_layout,
            sub_pipeline,
            sub_layout,
            grad_pipeline,
            grad_layout,
            inproj_grad_pipeline,
            inproj_grad_layout,
            update_pipeline,
            update_layout,
        })
    }

    fn run(
        &self,
        dim: usize,
        state_dim: usize,
        expand: usize,
        seq_len: usize,
        batch_size: usize,
        block_size: usize,
    ) -> Result<i64> {
        let inner = dim * expand;
        anyhow::ensure!(inner <= 64, "wgpu int8 full forward currently requires inner <= 64");
        anyhow::ensure!(state_dim <= 16, "wgpu int8 full forward currently requires state_dim <= 16");

        let input_scale = IntScale::new(32, 8);
        let weight_scale = IntScale::new(24, 8);
        let sequence = make_mamba_lite_sequence(seq_len, batch_size, dim, 0, block_size, input_scale);
        let input_vals = flatten_sequence_i32(&sequence);
        let w_in_proj = flatten_i8_tensor_i32(&BlockwiseTensorI8::from_seeded(
            "mamba2.in_proj",
            inner * 2,
            dim,
            block_size,
            weight_scale,
            41,
        ));
        let w_dt = flatten_i8_tensor_i32(&BlockwiseTensorI8::from_seeded(
            "mamba2.dt",
            inner,
            inner,
            block_size,
            weight_scale,
            43,
        ));
        let w_b = flatten_i8_tensor_i32(&BlockwiseTensorI8::from_seeded(
            "mamba2.B",
            inner * state_dim,
            inner,
            block_size,
            weight_scale,
            47,
        ));
        let w_c = flatten_i8_tensor_i32(&BlockwiseTensorI8::from_seeded(
            "mamba2.C",
            inner * state_dim,
            inner,
            block_size,
            weight_scale,
            53,
        ));
        let w_out = flatten_i8_tensor_i32(&BlockwiseTensorI8::from_seeded(
            "mamba2.out",
            dim,
            inner,
            block_size,
            weight_scale,
            59,
        ));
        let total_tokens = sequence.len() * batch_size;
        let total = input_vals.len();
        let meta = Mamba2FullMeta {
            total_tokens: total_tokens as u32,
            batch_size: batch_size as u32,
            seq_len: seq_len as u32,
            dim: dim as u32,
            inner: inner as u32,
            state_dim: state_dim as u32,
            pad0: 0,
            pad1: 0,
        };
        let input_buf = storage_init_i32(&self.device, &input_vals);
        let w_in_proj_buf = storage_init_i32(&self.device, &w_in_proj);
        let w_dt_buf = storage_init_i32(&self.device, &w_dt);
        let w_b_buf = storage_init_i32(&self.device, &w_b);
        let w_c_buf = storage_init_i32(&self.device, &w_c);
        let w_out_buf = storage_init_i32(&self.device, &w_out);
        let meta_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("mamba2-full-meta"),
            contents: bytemuck::bytes_of(&meta),
            usage: wgpu::BufferUsages::UNIFORM,
        });
        let output_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("mamba2-full-output"),
            size: (total * std::mem::size_of::<i32>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let yz_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("mamba2-full-yz"),
            size: ((total_tokens * inner) * std::mem::size_of::<i32>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("mamba2-full-bind-group"),
            layout: &self.forward_layout,
            entries: &[
                storage_entry(0, &input_buf),
                storage_entry(1, &w_in_proj_buf),
                storage_entry(2, &w_dt_buf),
                storage_entry(3, &w_b_buf),
                storage_entry(4, &w_c_buf),
                storage_entry(5, &w_out_buf),
                wgpu::BindGroupEntry {
                    binding: 6,
                    resource: meta_buf.as_entire_binding(),
                },
                storage_entry(7, &output_buf),
                storage_entry(8, &yz_buf),
            ],
        });

        let mut encoder = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = encoder.begin_compute_pass(&Default::default());
            pass.set_pipeline(&self.forward_pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups((total_tokens as u32).div_ceil(64), 1, 1);
        }
        self.queue.submit(std::iter::once(encoder.finish()));
        let output = readback_i32(&self.device, &self.queue, &output_buf, total)?;
        Ok(output.iter().map(|v| *v as i64).sum())
    }

    #[allow(clippy::too_many_arguments)]
    fn run_with_tensors(
        &self,
        sequence: &[BlockwiseTensorI8],
        w_in_proj_t: &BlockwiseTensorI8,
        w_dt_t: &BlockwiseTensorI8,
        w_b_t: &BlockwiseTensorI8,
        w_c_t: &BlockwiseTensorI8,
        w_out_t: &BlockwiseTensorI8,
        dim: usize,
        state_dim: usize,
        expand: usize,
        batch_size: usize,
    ) -> Result<Vec<i32>> {
        let inner = dim * expand;
        anyhow::ensure!(inner <= 64, "wgpu int8 full forward currently requires inner <= 64");
        anyhow::ensure!(state_dim <= 16, "wgpu int8 full forward currently requires state_dim <= 16");
        let (output, _) = self.run_with_tensors_outputs(
            sequence,
            w_in_proj_t,
            w_dt_t,
            w_b_t,
            w_c_t,
            w_out_t,
            dim,
            state_dim,
            expand,
            batch_size,
        )?;
        Ok(output)
    }

    #[allow(clippy::too_many_arguments)]
    fn run_with_tensors_outputs(
        &self,
        sequence: &[BlockwiseTensorI8],
        w_in_proj_t: &BlockwiseTensorI8,
        w_dt_t: &BlockwiseTensorI8,
        w_b_t: &BlockwiseTensorI8,
        w_c_t: &BlockwiseTensorI8,
        w_out_t: &BlockwiseTensorI8,
        dim: usize,
        state_dim: usize,
        expand: usize,
        batch_size: usize,
    ) -> Result<(Vec<i32>, Vec<i32>)> {
        let inner = dim * expand;
        let input_vals = flatten_sequence_i32(sequence);
        let w_in_proj = flatten_i8_tensor_i32(w_in_proj_t);
        let w_dt = flatten_i8_tensor_i32(w_dt_t);
        let w_b = flatten_i8_tensor_i32(w_b_t);
        let w_c = flatten_i8_tensor_i32(w_c_t);
        let w_out = flatten_i8_tensor_i32(w_out_t);
        let total_tokens = sequence.len() * batch_size;
        let total = input_vals.len();
        let meta = Mamba2FullMeta {
            total_tokens: total_tokens as u32,
            batch_size: batch_size as u32,
            seq_len: sequence.len() as u32,
            dim: dim as u32,
            inner: inner as u32,
            state_dim: state_dim as u32,
            pad0: 0,
            pad1: 0,
        };
        let input_buf = storage_init_i32(&self.device, &input_vals);
        let w_in_proj_buf = storage_init_i32(&self.device, &w_in_proj);
        let w_dt_buf = storage_init_i32(&self.device, &w_dt);
        let w_b_buf = storage_init_i32(&self.device, &w_b);
        let w_c_buf = storage_init_i32(&self.device, &w_c);
        let w_out_buf = storage_init_i32(&self.device, &w_out);
        let meta_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("mamba2-full-meta"),
            contents: bytemuck::bytes_of(&meta),
            usage: wgpu::BufferUsages::UNIFORM,
        });
        let output_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("mamba2-full-output"),
            size: (total * std::mem::size_of::<i32>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let yz_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("mamba2-full-yz"),
            size: ((total_tokens * inner) * std::mem::size_of::<i32>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("mamba2-full-bind-group"),
            layout: &self.forward_layout,
            entries: &[
                storage_entry(0, &input_buf),
                storage_entry(1, &w_in_proj_buf),
                storage_entry(2, &w_dt_buf),
                storage_entry(3, &w_b_buf),
                storage_entry(4, &w_c_buf),
                storage_entry(5, &w_out_buf),
                wgpu::BindGroupEntry {
                    binding: 6,
                    resource: meta_buf.as_entire_binding(),
                },
                storage_entry(7, &output_buf),
                storage_entry(8, &yz_buf),
            ],
        });
        let mut encoder = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = encoder.begin_compute_pass(&Default::default());
            pass.set_pipeline(&self.forward_pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups((total_tokens as u32).div_ceil(64), 1, 1);
        }
        self.queue.submit(std::iter::once(encoder.finish()));
        let output = readback_i32(&self.device, &self.queue, &output_buf, total)?;
        let yz = readback_i32(&self.device, &self.queue, &yz_buf, total_tokens * inner)?;
        Ok((output, yz))
    }

    fn signsgd_ef_update_i8(
        &self,
        weights: &[i32],
        grads: &[i32],
        error: &[i32],
        lr_numerator: i32,
    ) -> Result<(Vec<i32>, Vec<i32>)> {
        anyhow::ensure!(weights.len() == grads.len(), "weights/grads size mismatch");
        anyhow::ensure!(weights.len() == error.len(), "weights/error size mismatch");
        let total = weights.len();
        let sign_step = lr_numerator.max(1) / 4 + 1;
        let weights_buf = storage_init_i32_rw(&self.device, weights);
        let grads_buf = storage_init_i32(&self.device, grads);
        let error_buf = storage_init_i32_rw(&self.device, error);
        let meta = UpdateMeta {
            total: total as u32,
            sign_step,
            pad0: 0,
            pad1: 0,
        };
        let meta_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("signsgd-ef-update-meta"),
            contents: bytemuck::bytes_of(&meta),
            usage: wgpu::BufferUsages::UNIFORM,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("signsgd-ef-update-bind-group"),
            layout: &self.update_layout,
            entries: &[
                storage_entry(0, &weights_buf),
                storage_entry(1, &grads_buf),
                storage_entry(2, &error_buf),
                wgpu::BindGroupEntry {
                    binding: 3,
                    resource: meta_buf.as_entire_binding(),
                },
            ],
        });
        let mut encoder = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = encoder.begin_compute_pass(&Default::default());
            pass.set_pipeline(&self.update_pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups((total as u32).div_ceil(64), 1, 1);
        }
        self.queue.submit(std::iter::once(encoder.finish()));
        let weights_out = readback_i32(&self.device, &self.queue, &weights_buf, total)?;
        let error_out = readback_i32(&self.device, &self.queue, &error_buf, total)?;
        Ok((weights_out, error_out))
    }

    fn sub_i32(&self, a: &[i32], b: &[i32]) -> Result<Vec<i32>> {
        anyhow::ensure!(a.len() == b.len(), "sub_i32 size mismatch");
        let total = a.len();
        let a_buf = storage_init_i32(&self.device, a);
        let b_buf = storage_init_i32(&self.device, b);
        let out_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("sub-i32-out"),
            size: (total * std::mem::size_of::<i32>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let meta = SubMeta {
            total: total as u32,
            pad0: 0,
            pad1: 0,
            pad2: 0,
        };
        let meta_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("sub-i32-meta"),
            contents: bytemuck::bytes_of(&meta),
            usage: wgpu::BufferUsages::UNIFORM,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("sub-i32-bind-group"),
            layout: &self.sub_layout,
            entries: &[
                storage_entry(0, &a_buf),
                storage_entry(1, &b_buf),
                storage_entry(2, &out_buf),
                wgpu::BindGroupEntry {
                    binding: 3,
                    resource: meta_buf.as_entire_binding(),
                },
            ],
        });
        let mut encoder = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = encoder.begin_compute_pass(&Default::default());
            pass.set_pipeline(&self.sub_pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups((total as u32).div_ceil(64), 1, 1);
        }
        self.queue.submit(std::iter::once(encoder.finish()));
        readback_i32(&self.device, &self.queue, &out_buf, total)
    }

    fn outproj_grad_reduce_i32(
        &self,
        yz: &[i32],
        residual: &[i32],
        tokens: usize,
        dim: usize,
        inner: usize,
    ) -> Result<Vec<i32>> {
        anyhow::ensure!(yz.len() == tokens * inner, "yz size mismatch");
        anyhow::ensure!(residual.len() == tokens * dim, "residual size mismatch");
        let total = dim * inner;
        let yz_buf = storage_init_i32(&self.device, yz);
        let residual_buf = storage_init_i32(&self.device, residual);
        let grad_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("outproj-grad-out"),
            size: (total * std::mem::size_of::<i32>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let meta = GradMeta {
            tokens: tokens as u32,
            dim: dim as u32,
            inner: inner as u32,
            pad0: 0,
        };
        let meta_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("outproj-grad-meta"),
            contents: bytemuck::bytes_of(&meta),
            usage: wgpu::BufferUsages::UNIFORM,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("outproj-grad-bind-group"),
            layout: &self.grad_layout,
            entries: &[
                storage_entry(0, &yz_buf),
                storage_entry(1, &residual_buf),
                storage_entry(2, &grad_buf),
                wgpu::BindGroupEntry {
                    binding: 3,
                    resource: meta_buf.as_entire_binding(),
                },
            ],
        });
        let mut encoder = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = encoder.begin_compute_pass(&Default::default());
            pass.set_pipeline(&self.grad_pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups((total as u32).div_ceil(64), 1, 1);
        }
        self.queue.submit(std::iter::once(encoder.finish()));
        readback_i32(&self.device, &self.queue, &grad_buf, total)
    }

    fn inproj_grad_reduce_i32(
        &self,
        input_vals: &[i32],
        residual: &[i32],
        w_out: &[i32],
        tokens: usize,
        dim: usize,
        inner: usize,
    ) -> Result<Vec<i32>> {
        anyhow::ensure!(input_vals.len() == tokens * dim, "input size mismatch");
        anyhow::ensure!(residual.len() == tokens * dim, "residual size mismatch");
        anyhow::ensure!(w_out.len() == dim * inner, "w_out size mismatch");
        let total = inner * 2 * dim;
        let input_buf = storage_init_i32(&self.device, input_vals);
        let residual_buf = storage_init_i32(&self.device, residual);
        let w_out_buf = storage_init_i32(&self.device, w_out);
        let grad_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("inproj-grad-out"),
            size: (total * std::mem::size_of::<i32>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let meta = InprojGradMeta {
            tokens: tokens as u32,
            dim: dim as u32,
            inner: inner as u32,
            pad0: 0,
        };
        let meta_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("inproj-grad-meta"),
            contents: bytemuck::bytes_of(&meta),
            usage: wgpu::BufferUsages::UNIFORM,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("inproj-grad-bind-group"),
            layout: &self.inproj_grad_layout,
            entries: &[
                storage_entry(0, &input_buf),
                storage_entry(1, &residual_buf),
                storage_entry(2, &w_out_buf),
                storage_entry(3, &grad_buf),
                wgpu::BindGroupEntry {
                    binding: 4,
                    resource: meta_buf.as_entire_binding(),
                },
            ],
        });
        let mut encoder = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = encoder.begin_compute_pass(&Default::default());
            pass.set_pipeline(&self.inproj_grad_pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups((total as u32).div_ceil(64), 1, 1);
        }
        self.queue.submit(std::iter::once(encoder.finish()));
        readback_i32(&self.device, &self.queue, &grad_buf, total)
    }
}

impl WgpuMamba2FullForwardFp16 {
    async fn new() -> Result<Self> {
        let instance = wgpu::Instance::default();
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                power_preference: wgpu::PowerPreference::HighPerformance,
                ..Default::default()
            })
            .await
            .context("no wgpu adapter available")?;
        let required_features = wgpu::Features::SHADER_F16;
        anyhow::ensure!(
            adapter.features().contains(required_features),
            "current wgpu adapter does not support SHADER_F16"
        );
        let (device, queue) = adapter
            .request_device(
                &wgpu::DeviceDescriptor {
                    required_features,
                    ..Default::default()
                },
                None,
            )
            .await
            .context("request wgpu device with SHADER_F16")?;

        let (forward_layout, forward_pipeline) =
            std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let forward_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
                label: Some("mamba2-full-forward-fp16"),
                entries: &[
                    storage_layout_entry(0, true),
                    storage_layout_entry(1, true),
                    storage_layout_entry(2, true),
                    storage_layout_entry(3, true),
                    storage_layout_entry(4, true),
                    storage_layout_entry(5, true),
                    uniform_layout_entry(6),
                    storage_layout_entry(7, false),
                ],
            });
            let module = device.create_shader_module(wgpu::ShaderModuleDescriptor {
                label: Some("mamba2-full-forward-fp16"),
                source: wgpu::ShaderSource::Wgsl(include_str!("mamba2_full_forward_fp16.wgsl").into()),
            });
            let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
                label: Some("mamba2-full-forward-fp16"),
                bind_group_layouts: &[&forward_layout],
                push_constant_ranges: &[],
            });
            let forward_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
                label: Some("mamba2-full-forward-fp16"),
                layout: Some(&pipeline_layout),
                module: &module,
                entry_point: Some("main"),
                compilation_options: Default::default(),
                cache: None,
            });
            (forward_layout, forward_pipeline)
        }))
        .map_err(|_| {
            anyhow::anyhow!(
                "wgpu fp16 WGSL pipeline creation failed; current wgpu/Naga stack does not support this shader path"
            )
        })?;
        Ok(Self {
            device,
            queue,
            forward_pipeline,
            forward_layout,
        })
    }

    fn run(
        &self,
        dim: usize,
        state_dim: usize,
        expand: usize,
        seq_len: usize,
        batch_size: usize,
        block_size: usize,
    ) -> Result<i64> {
        let inner = dim * expand;
        anyhow::ensure!(inner <= 64, "wgpu fp16 full forward currently requires inner <= 64");
        anyhow::ensure!(state_dim <= 16, "wgpu fp16 full forward currently requires state_dim <= 16");
        anyhow::ensure!(dim <= 64, "wgpu fp16 full forward currently requires dim <= 64");

        let input_scale = IntScale::new(32, 8);
        let weight_scale = IntScale::new(24, 8);
        let sequence = make_mamba_lite_sequence(seq_len, batch_size, dim, 0, block_size, input_scale);
        let input_vals = flatten_sequence_f16_bits(&sequence);
        let w_in_proj = flatten_i8_tensor_f16_bits(&BlockwiseTensorI8::from_seeded(
            "mamba2.in_proj",
            inner * 2,
            dim,
            block_size,
            weight_scale,
            41,
        ));
        let w_dt = flatten_i8_tensor_f16_bits(&BlockwiseTensorI8::from_seeded(
            "mamba2.dt",
            inner,
            inner,
            block_size,
            weight_scale,
            43,
        ));
        let w_b = flatten_i8_tensor_f16_bits(&BlockwiseTensorI8::from_seeded(
            "mamba2.B",
            inner * state_dim,
            inner,
            block_size,
            weight_scale,
            47,
        ));
        let w_c = flatten_i8_tensor_f16_bits(&BlockwiseTensorI8::from_seeded(
            "mamba2.C",
            inner * state_dim,
            inner,
            block_size,
            weight_scale,
            53,
        ));
        let w_out = flatten_i8_tensor_f16_bits(&BlockwiseTensorI8::from_seeded(
            "mamba2.out",
            dim,
            inner,
            block_size,
            weight_scale,
            59,
        ));

        let total_tokens = sequence.len() * batch_size;
        let total = input_vals.len();
        let meta = Mamba2FullMeta {
            total_tokens: total_tokens as u32,
            batch_size: batch_size as u32,
            seq_len: seq_len as u32,
            dim: dim as u32,
            inner: inner as u32,
            state_dim: state_dim as u32,
            pad0: 0,
            pad1: 0,
        };
        let input_buf = storage_init_u16(&self.device, &input_vals);
        let w_in_proj_buf = storage_init_u16(&self.device, &w_in_proj);
        let w_dt_buf = storage_init_u16(&self.device, &w_dt);
        let w_b_buf = storage_init_u16(&self.device, &w_b);
        let w_c_buf = storage_init_u16(&self.device, &w_c);
        let w_out_buf = storage_init_u16(&self.device, &w_out);
        let meta_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("mamba2-full-fp16-meta"),
            contents: bytemuck::bytes_of(&meta),
            usage: wgpu::BufferUsages::UNIFORM,
        });
        let output_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("mamba2-full-fp16-output"),
            size: (total * std::mem::size_of::<u16>()) as u64,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("mamba2-full-fp16-bind-group"),
            layout: &self.forward_layout,
            entries: &[
                storage_entry(0, &input_buf),
                storage_entry(1, &w_in_proj_buf),
                storage_entry(2, &w_dt_buf),
                storage_entry(3, &w_b_buf),
                storage_entry(4, &w_c_buf),
                storage_entry(5, &w_out_buf),
                wgpu::BindGroupEntry {
                    binding: 6,
                    resource: meta_buf.as_entire_binding(),
                },
                storage_entry(7, &output_buf),
            ],
        });

        let mut encoder = self.device.create_command_encoder(&Default::default());
        {
            let mut pass = encoder.begin_compute_pass(&Default::default());
            pass.set_pipeline(&self.forward_pipeline);
            pass.set_bind_group(0, &bind_group, &[]);
            pass.dispatch_workgroups((total_tokens as u32).div_ceil(64), 1, 1);
        }
        self.queue.submit(std::iter::once(encoder.finish()));
        let output = readback_u16(&self.device, &self.queue, &output_buf, total)?;
        Ok(output
            .iter()
            .map(|&bits| f16::from_bits(bits).to_f32() as i64)
            .sum())
    }
}

fn storage_layout_entry(binding: u32, read_only: bool) -> wgpu::BindGroupLayoutEntry {
    wgpu::BindGroupLayoutEntry {
        binding,
        visibility: wgpu::ShaderStages::COMPUTE,
        ty: wgpu::BindingType::Buffer {
            ty: wgpu::BufferBindingType::Storage { read_only },
            has_dynamic_offset: false,
            min_binding_size: None,
        },
        count: None,
    }
}

fn uniform_layout_entry(binding: u32) -> wgpu::BindGroupLayoutEntry {
    wgpu::BindGroupLayoutEntry {
        binding,
        visibility: wgpu::ShaderStages::COMPUTE,
        ty: wgpu::BindingType::Buffer {
            ty: wgpu::BufferBindingType::Uniform,
            has_dynamic_offset: false,
            min_binding_size: None,
        },
        count: None,
    }
}

fn storage_entry<'a>(binding: u32, buffer: &'a wgpu::Buffer) -> wgpu::BindGroupEntry<'a> {
    wgpu::BindGroupEntry {
        binding,
        resource: buffer.as_entire_binding(),
    }
}

fn storage_init_i32(device: &wgpu::Device, data: &[i32]) -> wgpu::Buffer {
    device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: None,
        contents: bytemuck::cast_slice(data),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
    })
}

fn storage_init_u16(device: &wgpu::Device, data: &[u16]) -> wgpu::Buffer {
    device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: None,
        contents: bytemuck::cast_slice(data),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
    })
}

fn storage_init_i32_rw(device: &wgpu::Device, data: &[i32]) -> wgpu::Buffer {
    device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: None,
        contents: bytemuck::cast_slice(data),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC | wgpu::BufferUsages::COPY_DST,
    })
}

fn readback_i32(
    device: &wgpu::Device,
    queue: &wgpu::Queue,
    buffer: &wgpu::Buffer,
    count: usize,
) -> Result<Vec<i32>> {
    let size = (count * std::mem::size_of::<i32>()) as u64;
    let staging = device.create_buffer(&wgpu::BufferDescriptor {
        label: None,
        size,
        usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });
    let mut encoder = device.create_command_encoder(&Default::default());
    encoder.copy_buffer_to_buffer(buffer, 0, &staging, 0, size);
    queue.submit(std::iter::once(encoder.finish()));
    let slice = staging.slice(..);
    let (tx, rx) = std::sync::mpsc::channel();
    slice.map_async(wgpu::MapMode::Read, move |result| {
        let _ = tx.send(result);
    });
    let _ = device.poll(wgpu::MaintainBase::Wait);
    rx.recv()
        .context("wgpu map recv")?
        .context("wgpu map_async failed")?;
    let data = slice.get_mapped_range();
    let result = bytemuck::cast_slice(&data).to_vec();
    drop(data);
    staging.unmap();
    Ok(result)
}

fn readback_u16(
    device: &wgpu::Device,
    queue: &wgpu::Queue,
    buffer: &wgpu::Buffer,
    count: usize,
) -> Result<Vec<u16>> {
    let size = (count * std::mem::size_of::<u16>()) as u64;
    let staging = device.create_buffer(&wgpu::BufferDescriptor {
        label: None,
        size,
        usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });
    let mut encoder = device.create_command_encoder(&Default::default());
    encoder.copy_buffer_to_buffer(buffer, 0, &staging, 0, size);
    queue.submit(std::iter::once(encoder.finish()));
    let slice = staging.slice(..);
    let (tx, rx) = std::sync::mpsc::channel();
    slice.map_async(wgpu::MapMode::Read, move |result| {
        let _ = tx.send(result);
    });
    let _ = device.poll(wgpu::MaintainBase::Wait);
    rx.recv()
        .context("wgpu map recv")?
        .context("wgpu map_async failed")?;
    let data = slice.get_mapped_range();
    let result = bytemuck::cast_slice(&data).to_vec();
    drop(data);
    staging.unmap();
    Ok(result)
}

fn flatten_sequence_i32(sequence: &[BlockwiseTensorI8]) -> Vec<i32> {
    let mut out = Vec::new();
    for token in sequence {
        out.extend(token.values.iter().map(|&v| v as i32));
    }
    out
}

fn flatten_i8_tensor_i32(tensor: &BlockwiseTensorI8) -> Vec<i32> {
    tensor.values.iter().map(|&v| v as i32).collect()
}

fn flatten_sequence_f16_bits(sequence: &[BlockwiseTensorI8]) -> Vec<u16> {
    let mut out = Vec::new();
    for token in sequence {
        out.extend(
            token.values
                .iter()
                .map(|&v| f16::from_f32(v as f32).to_bits()),
        );
    }
    out
}

fn flatten_i8_tensor_f16_bits(tensor: &BlockwiseTensorI8) -> Vec<u16> {
    tensor
        .values
        .iter()
        .map(|&v| f16::from_f32(v as f32).to_bits())
        .collect()
}

fn layer_norm_i8(input: &BlockwiseTensorI8) -> BlockwiseTensorI8 {
    let mut out = BlockwiseTensorI8::zeros(&input.name, input.rows, input.cols, input.block_size, IntScale::new(1, 0));
    for r in 0..input.rows {
        let mut mean = 0i32;
        for c in 0..input.cols {
            mean += input.get(r, c) as i32;
        }
        mean /= input.cols.max(1) as i32;
        let mut var = 0i32;
        for c in 0..input.cols {
            let d = input.get(r, c) as i32 - mean;
            var += d * d;
        }
        var /= input.cols.max(1) as i32;
        let denom = 1 + isqrt_i32(var);
        for c in 0..input.cols {
            let d = input.get(r, c) as i32 - mean;
            out.set(r, c, (d * 32 / denom).clamp(i8::MIN as i32, i8::MAX as i32) as i8);
        }
    }
    out
}

fn linear_vec_i8(input: &[i32], weight: &BlockwiseTensorI8, out_dim: usize, in_dim: usize) -> Vec<i32> {
    let mut out = vec![0i32; out_dim];
    for o in 0..out_dim {
        let mut acc = 0i32;
        for i in 0..in_dim {
            acc += input[i] * weight.get(o, i) as i32;
        }
        out[o] = acc >> 6;
    }
    out
}

fn linear_batch_f32(
    input: &BlockwiseTensorI8,
    weight: &[f32],
    out_dim: usize,
    in_dim: usize,
    precision: FloatPrecision,
) -> Vec<f32> {
    let mut out = vec![0.0; input.rows * out_dim];
    for r in 0..input.rows {
        for o in 0..out_dim {
            let mut acc = 0.0;
            for i in 0..in_dim {
                acc += input.get(r, i) as f32 * weight[o * in_dim + i];
            }
            out[r * out_dim + o] = quantize_float(acc / 64.0, precision);
        }
    }
    out
}

fn linear_vec_f32(input: &[f32], weight: &[f32], out_dim: usize, in_dim: usize, precision: FloatPrecision) -> Vec<f32> {
    let mut out = vec![0.0; out_dim];
    for o in 0..out_dim {
        let mut acc = 0.0;
        for i in 0..in_dim {
            acc += input[i] * weight[o * in_dim + i];
        }
        out[o] = quantize_float(acc / 64.0, precision);
    }
    out
}

fn silu_i32(x: i32) -> i32 {
    let gate = (x + 64).clamp(0, 128);
    (x * gate) >> 7
}

fn softplus_i32(x: i32) -> i32 {
    x.max(0) + 1
}

fn silu_f32(x: f32, precision: FloatPrecision) -> f32 {
    let sig = 1.0 / (1.0 + (-x / 16.0).exp());
    quantize_float(x * sig, precision)
}

fn softplus_f32(x: f32, precision: FloatPrecision) -> f32 {
    quantize_float((1.0 + (x / 16.0).exp()).ln() * 16.0, precision)
}

fn inspect_arrow(input: &PathBuf) -> Result<()> {
    let file = File::open(input).with_context(|| format!("open {}", input.display()))?;
    let reader = FileReader::try_new(file, None)?;
    for (batch_idx, batch) in reader.enumerate() {
        let batch = batch?;
        println!("batch[{batch_idx}] rows={}", batch.num_rows());
        for col in 0..batch.num_columns() {
            println!(
                "  {}: {:?}",
                batch.schema().field(col).name(),
                batch.column(col).data_type()
            );
        }
    }
    Ok(())
}

fn make_batch(
    batch_size: usize,
    input_dim: usize,
    step: i32,
    block_size: usize,
    scale: IntScale,
) -> BlockwiseTensorI8 {
    let mut batch = BlockwiseTensorI8::zeros("input", batch_size, input_dim, block_size, scale);
    for r in 0..batch_size {
        for c in 0..input_dim {
            let raw = ((((r * input_dim + c) as i32 + step * 5) * 11) % 41) - 20;
            batch.set(r, c, raw as i8);
        }
    }
    batch
}

fn matmul_i8(input: &BlockwiseTensorI8, weight: &BlockwiseTensorI8) -> Vec<i32> {
    let mut out = vec![0i32; input.rows * weight.rows];
    for r in 0..input.rows {
        for o in 0..weight.rows {
            let mut acc = 0i32;
            for c in 0..input.cols {
                acc += input.get(r, c) as i32 * weight.get(o, c) as i32;
            }
            out[r * weight.rows + o] = acc;
        }
    }
    out
}

fn diff_i32(a: &[i32], b: &[i32]) -> Vec<i32> {
    a.iter().zip(b.iter()).map(|(x, y)| x - y).collect()
}

fn outer_product_grad(
    input: &BlockwiseTensorI8,
    residual: &[i32],
    output_dim: usize,
    input_dim: usize,
    block_size: usize,
    fallback_scale: IntScale,
    scale_mode: ScaleMode,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) -> BlockwiseTensorI8 {
    let mut accum = vec![0i32; output_dim * input_dim];
    for o in 0..output_dim {
        for i in 0..input_dim {
            let mut acc = 0i32;
            for r in 0..input.rows {
                acc += residual[r * output_dim + o] * input.get(r, i) as i32;
            }
            accum[o * input_dim + i] = acc >> 12;
        }
    }
    quantize_blockwise(
        "linear.grad",
        output_dim,
        input_dim,
        block_size,
        &accum,
        fallback_scale,
        scale_mode,
        rng,
        stochastic_rounding,
    )
}

fn quantize_blockwise(
    name: &str,
    rows: usize,
    cols: usize,
    block_size: usize,
    source: &[i32],
    fallback_scale: IntScale,
    scale_mode: ScaleMode,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) -> BlockwiseTensorI8 {
    let mut tensor = BlockwiseTensorI8::zeros(name, rows, cols, block_size, fallback_scale);
    for block_idx in 0..tensor.scales.len() {
        let start = block_idx * block_size;
        let end = (start + block_size).min(source.len());
        let scale_value = match scale_mode {
            ScaleMode::Max => source[start..end].iter().map(|v| v.saturating_abs()).max().unwrap_or(0),
            ScaleMode::P75 => percentile_abs(&source[start..end], 75),
            ScaleMode::P90 => percentile_abs(&source[start..end], 90),
        };
        let scale = if scale_value == 0 {
            fallback_scale
        } else {
            IntScale::new((scale_value / 96).max(1), 0)
        };
        tensor.scales[block_idx] = scale;
        for (offset, value) in source[start..end].iter().enumerate() {
            tensor.values[start + offset] = scale.quantize_i32(*value, rng, stochastic_rounding);
        }
    }
    tensor
}

fn quantize_blockwise_pow2(
    name: &str,
    rows: usize,
    cols: usize,
    block_size: usize,
    source: &[i32],
    fallback_scale: IntScale,
    scale_mode: ScaleMode,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) -> BlockwiseTensorI8 {
    let mut tensor = BlockwiseTensorI8::zeros(name, rows, cols, block_size, fallback_scale);
    for block_idx in 0..tensor.scales.len() {
        let start = block_idx * block_size;
        let end = (start + block_size).min(source.len());
        let scale_value = match scale_mode {
            ScaleMode::Max => source[start..end].iter().map(|v| v.saturating_abs()).max().unwrap_or(0),
            ScaleMode::P75 => percentile_abs(&source[start..end], 75),
            ScaleMode::P90 => percentile_abs(&source[start..end], 90),
        };
        let scale = if scale_value == 0 {
            fallback_scale
        } else {
            let target = (scale_value / 96).max(1);
            IntScale::new((target as u32).next_power_of_two() as i32, 0)
        };
        tensor.scales[block_idx] = scale;
        for (offset, value) in source[start..end].iter().enumerate() {
            tensor.values[start + offset] = scale.quantize_i32(*value, rng, stochastic_rounding);
        }
    }
    tensor
}

fn quantize_blockwise_pow2_i16(
    name: &str,
    rows: usize,
    cols: usize,
    block_size: usize,
    source: &[i32],
    fallback_scale: IntScale,
    scale_mode: ScaleMode,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) -> BlockwiseTensorI16 {
    let mut tensor = BlockwiseTensorI16::zeros(name, rows, cols, block_size, fallback_scale);
    for block_idx in 0..tensor.scales.len() {
        let start = block_idx * block_size;
        let end = (start + block_size).min(source.len());
        let scale_value = match scale_mode {
            ScaleMode::Max => source[start..end].iter().map(|v| v.saturating_abs()).max().unwrap_or(0),
            ScaleMode::P75 => percentile_abs(&source[start..end], 75),
            ScaleMode::P90 => percentile_abs(&source[start..end], 90),
        };
        let scale = if scale_value == 0 {
            fallback_scale
        } else {
            let target = (scale_value / 24).max(1);
            IntScale::new((target as u32).next_power_of_two() as i32, 0)
        };
        tensor.scales[block_idx] = scale;
        for (offset, value) in source[start..end].iter().enumerate() {
            tensor.values[start + offset] = scale.quantize_i32_to_i16(*value, rng, stochastic_rounding);
        }
    }
    tensor
}

fn percentile_abs(values: &[i32], percentile: usize) -> i32 {
    if values.is_empty() {
        return 0;
    }
    let mut v: Vec<i32> = values.iter().map(|x| x.saturating_abs()).collect();
    v.sort_unstable();
    let idx = ((v.len() - 1) * percentile) / 100;
    v[idx]
}

fn isqrt_i32(value: i32) -> i32 {
    if value <= 0 {
        return 0;
    }
    let mut x = value as u32;
    let mut y = x.div_ceil(2);
    while y < x {
        x = y;
        y = (x + (value as u32 / x)) / 2;
    }
    x as i32
}

#[allow(clippy::too_many_arguments)]
fn update_adam_i8(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    momentum: &mut BlockwiseTensorI8,
    v: &mut BlockwiseTensorI8,
    beta_scale: IntScale,
    one_minus_beta_scale: IntScale,
    beta2_scale: IntScale,
    one_minus_beta2_scale: IntScale,
    v_scale_mode: ScaleMode,
    grad_sq_scale: IntScale,
    lr_scale: IntScale,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    let mut next_v_accum = vec![0i32; v.len()];

    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let mom_scale = momentum.scale_for(idx);
        let old_m = mom_scale.dequantize_i8(momentum.values[idx]);
        let mixed = beta_scale.apply_i32(old_m) + one_minus_beta_scale.apply_i32(grad_i32);
        let new_m = mom_scale.quantize_i32(mixed, rng, stochastic_rounding);
        momentum.values[idx] = new_m;

        if new_m == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }

        let old_v = v.scale_for(idx).dequantize_i8(v.values[idx]);
        let grad_sq = grad_sq_scale.apply_i32(grad_i32.saturating_mul(grad_i32)).max(0);
        let mixed_v = beta2_scale.apply_i32(old_v) + one_minus_beta2_scale.apply_i32(grad_sq);
        next_v_accum[idx] = mixed_v;
    }

    let requantized_v = quantize_blockwise_pow2(
        "linear.v",
        v.rows,
        v.cols,
        v.block_size,
        &next_v_accum,
        IntScale::new(1, 0),
        v_scale_mode,
        rng,
        stochastic_rounding,
    );
    v.scales.clone_from(&requantized_v.scales);
    v.values.clone_from(&requantized_v.values);

    for idx in 0..weights.len() {
        let new_v = v.values[idx];
        if new_v == 0 {
            stats.zeroed_v_updates += 1;
        } else {
            stats.nonzero_v_updates += 1;
        }

        let mom_scale = momentum.scale_for(idx);
        let new_m = momentum.values[idx];
        let v_scale = v.scale_for(idx);
        let denom = 1 + isqrt_i32(v_scale.dequantize_i8(new_v).saturating_abs());
        let delta = lr_scale.apply_i32(mom_scale.dequantize_i8(new_m)) / denom.max(1);
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }

        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

#[allow(clippy::too_many_arguments)]
fn update_adam_i8_ef(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    momentum: &mut BlockwiseTensorI8,
    v: &mut BlockwiseTensorI8,
    update_error: &mut BlockwiseTensorI8,
    beta_scale: IntScale,
    one_minus_beta_scale: IntScale,
    beta2_scale: IntScale,
    one_minus_beta2_scale: IntScale,
    v_scale_mode: ScaleMode,
    grad_sq_scale: IntScale,
    lr_scale: IntScale,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    let mut next_v_accum = vec![0i32; v.len()];

    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let mom_scale = momentum.scale_for(idx);
        let old_m = mom_scale.dequantize_i8(momentum.values[idx]);
        let mixed = beta_scale.apply_i32(old_m) + one_minus_beta_scale.apply_i32(grad_i32);
        let new_m = mom_scale.quantize_i32(mixed, rng, stochastic_rounding);
        momentum.values[idx] = new_m;

        if new_m == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }

        let old_v = v.scale_for(idx).dequantize_i8(v.values[idx]);
        let grad_sq = grad_sq_scale.apply_i32(grad_i32.saturating_mul(grad_i32)).max(0);
        let mixed_v = beta2_scale.apply_i32(old_v) + one_minus_beta2_scale.apply_i32(grad_sq);
        next_v_accum[idx] = mixed_v;
    }

    let requantized_v = quantize_blockwise_pow2(
        "linear.v",
        v.rows,
        v.cols,
        v.block_size,
        &next_v_accum,
        IntScale::new(1, 0),
        v_scale_mode,
        rng,
        stochastic_rounding,
    );
    v.scales.clone_from(&requantized_v.scales);
    v.values.clone_from(&requantized_v.values);

    for idx in 0..weights.len() {
        let new_v = v.values[idx];
        if new_v == 0 {
            stats.zeroed_v_updates += 1;
        } else {
            stats.nonzero_v_updates += 1;
        }

        let mom_scale = momentum.scale_for(idx);
        let new_m = momentum.values[idx];
        let v_scale = v.scale_for(idx);
        let denom = 1 + isqrt_i32(v_scale.dequantize_i8(new_v).saturating_abs());
        let err_scale = update_error.scale_for(idx);
        let carried = err_scale.dequantize_i8(update_error.values[idx]);
        let desired_delta = lr_scale.apply_i32(mom_scale.dequantize_i8(new_m)) / denom.max(1) + carried;
        let quantized_delta = desired_delta.clamp(i8::MIN as i32, i8::MAX as i32);
        let residual = desired_delta - quantized_delta;
        update_error.values[idx] = err_scale.quantize_i32(residual, rng, stochastic_rounding);

        if quantized_delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }

        let next = (weights.values[idx] as i32 - quantized_delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

#[allow(clippy::too_many_arguments)]
fn update_adam_i16v(
    weights: &mut BlockwiseTensorI8,
    grad: &BlockwiseTensorI8,
    momentum: &mut BlockwiseTensorI8,
    v: &mut BlockwiseTensorI16,
    beta_scale: IntScale,
    one_minus_beta_scale: IntScale,
    beta2_scale: IntScale,
    one_minus_beta2_scale: IntScale,
    v_scale_mode: ScaleMode,
    grad_sq_scale: IntScale,
    lr_scale: IntScale,
    denom_shift: u8,
    stats: &mut TrainStats,
    rng: &mut Lcg64,
    stochastic_rounding: bool,
) {
    let mut next_v_accum = vec![0i32; v.len()];

    for idx in 0..weights.len() {
        let grad_i32 = grad.scale_for(idx).dequantize_i8(grad.values[idx]);
        let mom_scale = momentum.scale_for(idx);
        let old_m = mom_scale.dequantize_i8(momentum.values[idx]);
        let mixed = beta_scale.apply_i32(old_m) + one_minus_beta_scale.apply_i32(grad_i32);
        let new_m = mom_scale.quantize_i32(mixed, rng, stochastic_rounding);
        momentum.values[idx] = new_m;
        if new_m == 0 {
            stats.zeroed_momentum_updates += 1;
        } else {
            stats.nonzero_momentum_updates += 1;
        }

        let old_v = v.scale_for(idx).dequantize_i16(v.values[idx]);
        let grad_sq = grad_sq_scale.apply_i32(grad_i32.saturating_mul(grad_i32)).max(0);
        let mixed_v = beta2_scale.apply_i32(old_v) + one_minus_beta2_scale.apply_i32(grad_sq);
        next_v_accum[idx] = mixed_v;
    }

    let requantized_v = quantize_blockwise_pow2_i16(
        &v.name,
        v.rows,
        v.cols,
        v.block_size,
        &next_v_accum,
        IntScale::new(1, 0),
        v_scale_mode,
        rng,
        stochastic_rounding,
    );
    v.scales.clone_from(&requantized_v.scales);
    v.values.clone_from(&requantized_v.values);

    for idx in 0..weights.len() {
        let new_v = v.values[idx];
        if new_v == 0 {
            stats.zeroed_v_updates += 1;
        } else {
            stats.nonzero_v_updates += 1;
        }

        let mom_scale = momentum.scale_for(idx);
        let new_m = momentum.values[idx];
        let v_scale = v.scale_for(idx);
        let denom = 1 + (isqrt_i32(v_scale.dequantize_i16(new_v).saturating_abs()) >> denom_shift);
        let delta = lr_scale.apply_i32(mom_scale.dequantize_i8(new_m)) / denom.max(1);
        if delta == 0 {
            stats.zeroed_weight_updates += 1;
        } else {
            stats.nonzero_weight_updates += 1;
        }
        let next = (weights.values[idx] as i32 - delta).clamp(i8::MIN as i32, i8::MAX as i32);
        weights.values[idx] = next as i8;
    }
}

fn write_checkpoint(path: &PathBuf, tensors: &[BlockwiseTensorI8], stats: &TrainStats) -> Result<()> {
    let tensor_schema = Arc::new(Schema::new(vec![
        Field::new("name", DataType::Utf8, false),
        Field::new("rows", DataType::UInt32, false),
        Field::new("cols", DataType::UInt32, false),
        Field::new("block_size", DataType::UInt32, false),
        Field::new("block_idx", DataType::UInt32, false),
        Field::new("scale_numerator", DataType::Int32, false),
        Field::new("scale_shift", DataType::UInt8, false),
        Field::new("stochastic_rounding", DataType::Boolean, false),
        Field::new("value", DataType::Int8, false),
    ]));

    let mut names = Vec::new();
    let mut rows = Vec::new();
    let mut cols = Vec::new();
    let mut block_sizes = Vec::new();
    let mut block_indices = Vec::new();
    let mut numerators = Vec::new();
    let mut shifts = Vec::new();
    let mut stochastic = Vec::new();
    let mut values = Vec::new();

    for tensor in tensors {
        for (flat_idx, value) in tensor.values.iter().enumerate() {
            let block_idx = tensor.block_idx(flat_idx);
            let scale = tensor.scales[block_idx];
            names.push(tensor.name.clone());
            rows.push(tensor.rows as u32);
            cols.push(tensor.cols as u32);
            block_sizes.push(tensor.block_size as u32);
            block_indices.push(block_idx as u32);
            numerators.push(scale.numerator);
            shifts.push(scale.shift);
            stochastic.push(stats.stochastic_rounding);
            values.push(*value);
        }
    }

    let batch = RecordBatch::try_new(
        tensor_schema.clone(),
        vec![
            Arc::new(StringArray::from(names)) as ArrayRef,
            Arc::new(UInt32Array::from(rows)),
            Arc::new(UInt32Array::from(cols)),
            Arc::new(UInt32Array::from(block_sizes)),
            Arc::new(UInt32Array::from(block_indices)),
            Arc::new(Int32Array::from(numerators)),
            Arc::new(UInt8Array::from(shifts)),
            Arc::new(BooleanArray::from(stochastic)),
            Arc::new(Int8Array::from(values)),
        ],
    )?;

    let mut writer = FileWriter::try_new(
        File::create(path).with_context(|| format!("create {}", path.display()))?,
        &tensor_schema,
    )?;
    writer.write(&batch)?;
    writer.finish()?;

    let stats_path = path.with_extension("json");
    std::fs::write(&stats_path, serde_json::to_vec_pretty(stats)?)?;
    Ok(())
}
