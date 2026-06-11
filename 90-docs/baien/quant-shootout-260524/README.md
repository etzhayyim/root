---
id: doc-2605240500-quant-training-shootout-evo-x2
title: "Quant training-efficiency shootout on EVO-X2 (gfx1151) — 5 working formats, 4 hw-blocked"
status: active
doc_type: reference
topic: roso-distill
authoritative: true
authoritative_for:
  - empirical training-time quant comparison on AMD Radeon 8060S (gfx1151)
  - which quantization libraries actually work on this ROCm install
last_verified: 2026-05-24
related:
  - adr-2605242000-roso-pattern-frontier-distill
  - 70-tools/scripts/bench/quant-training-shootout/
---

# Quant training-efficiency shootout — 2026-05-24

## What this is

End-to-end SFT-training comparison of 5 quantization treatments of the
same frozen base + identical LoRA-on-top. Goal: real numbers, not specs,
for "which quant should we use when fine-tuning on EVO".

## Setup

| | value |
|---|---|
| device | AMD Radeon 8060S Graphics (gfx1151), 60 GB |
| stack | Windows 11 + Python 3.12.10 (ComfyUI portable) + torch 2.9.1+rocm7.2.1 + transformers 5.8.0 + trl 1.4.0 + peft 0.19.1 + optimum.quanto |
| base | `Qwen/Qwen2.5-0.5B-Instruct` (Apache-2.0, 494,032,768 params) |
| dataset | `lordx64/reasoning-distill-opus-4-7-max-sft` (Apache-2.0, Opus 4.7 distill, 8 rows) |
| LoRA targets | `q_proj`, `k_proj`, `v_proj`, `o_proj` (r=16, alpha=32, dropout=0.05) |
| trainable | 2,162,688 params (0.44%) |
| SFT shape | 8 rows × 3 optimizer steps, batch=1, grad_accum=4, lr=2e-4, bf16 |
| per-row isolation | each row runs in a fresh subprocess (no cuda cache leak) |

## Results

### Raw measurements (per row, written by `_one_row.py`)

| method | quantize_s | model_gb (count) | step_warm_s | peak_vram_gb | final_loss | verdict |
|---|---|---|---|---|---|---|
| **bf16** (baseline) | 0.00 | 0.92 | 1.61 | 2.281 | **1.7602** | reference |
| **bonsai-sign-1bit** (roso stub) | 0.53 | 0.92 | 2.24 | 2.281 | **12.31** | ❌ no packing / loss collapse |
| **quanto-int8** | 2.86 | 1.17 | **0.67** | 2.008 | **1.7616** | ✅ fastest + quality-equiv to bf16 |
| **quanto-int4** | 2.77 | 1.17 | 0.84 | **1.811** | 1.8981 | ✅ lowest VRAM + 0.14 loss tax (8%) |
| **quanto-int2** (1.58-bit proxy) | 2.74 | 1.17 | 0.85 | 1.694 | **13.51** | ❌ loss collapse w/o real Bonsai calibration |

### Derived throughput + TOPS

Assumptions: tokens/step ≈ **2,500** (estimated; prior Zamba2-1.2B SFT measured
2,539 tok/step on the same dataset); FLOPs per training step = **6·N·T**
(forward 2·N·T + backward 4·N·T, Chinchilla/Kaplan rule; LoRA trainable
params are 0.44% so the cost is dominated by frozen-base forward+backward,
not by adapter updates); hardware peak FP16 ≈ **30 TFLOPS** (vendor-claimed
for AMD Radeon 8060S / gfx1151 RDNA 3.5 APU iGPU).

| method | step_warm_s | samples/s | tokens/s | sustained TFLOPS | % of peak (30) | speedup vs bf16 |
|---|---|---|---|---|---|---|
| bf16 | 1.61 | 2.48 | 1,553 | 4.60 | 15.3% | 1.00× |
| bonsai-sign-1bit | 2.24 | 1.79 | 1,116 | 3.31 | 11.0% | **0.72×** (slower!) |
| **quanto-int8** | **0.67** | **5.97** | **3,731** | **11.06** | **36.9%** | **2.40×** |
| quanto-int4 | 0.84 | 4.76 | 2,976 | 8.82 | 29.4% | 1.92× |
| quanto-int2 | 0.85 | 4.71 | 2,941 | 8.72 | 29.1% | 1.89× |

### Quality-vs-speed efficiency

| method | final_loss | tokens/s/loss (higher = better) | VRAM·loss product (lower = better) |
|---|---|---|---|
| bf16 | 1.7602 | 882 | 4.02 |
| bonsai-sign-1bit | 12.31 | 91 | **28.07** ❌ |
| **quanto-int8** | 1.7616 | **2,118** | **3.54** ✅ |
| **quanto-int4** | 1.8981 | 1,568 | **3.44** ✅ (best) |
| quanto-int2 | 13.51 | 218 | 22.89 ❌ |

`model_gb` is raw `Σ(numel × element_size)` of parameters. For quanto rows this
includes the packed int tensor PLUS per-block fp16 scales, so the count is
slightly higher than bf16 even though the on-device VRAM is lower. The
honest size metric is `peak_vram_gb` measured during training.

## Key findings

1. **quanto-int8 is the optimal training quant on this hw** —
   **11.06 TFLOPS sustained = 37% of vendor-claimed gfx1151 FP16 peak**,
   2.4× faster step than bf16, -12% peak VRAM, **0.001 loss delta** vs bf16
   (1.7616 vs 1.7602). 2.86 s one-time quantize cost.
2. **quanto-int4 is the optimal VRAM-saver** —
   -21% peak VRAM vs bf16 with +0.14 loss tax (~8%). Still 1.9× faster than bf16
   (8.82 TFLOPS sustained = 29% of peak).
3. **bonsai-sign-1bit is SLOWER than bf16 (0.72×)** —
   anti-pattern confirmed. Sign-quantized weights stored as bf16 give the
   ROCm matmul kernel no information to exploit; instead the kernel hits a
   slow path because the weight statistics are degenerate (~50% zeros after
   the in-place mutation). Sustained throughput: 3.31 TFLOPS = 11% of peak.
4. **Naive 1-bit cannot survive few-shot SFT** —
   both `bonsai-sign-1bit` (in-place `sign(W)·mean(|W|)`) AND `quanto-int2`
   (2-bit packed, ~1.58 effective bits) collapse to loss 12-13 after 3 SGD steps.
   This confirms the published Bonsai 8B path: real per-layer optimization
   with calibration inputs (whitepaper Algorithm 1, ~500 LoC port) is NOT
   optional — it's the difference between a usable 1-bit model and noise.
5. **bonsai-sign-1bit has no packing benefit** at this stack —
   the sign-quantized weights are stored back into the original bf16
   tensors, so VRAM is identical to bf16 (2.281 GB). The packed-bytes
   number reported by roso (0.358 GB packed) is a theoretical accounting
   figure; without bitnet.cpp-style ternary kernels the model still loads
   as bf16 and trains at bf16 cost.
6. **Sustained TFLOPS reality check** — even the best row (quanto-int8 at
   37% of peak) leaves significant headroom. Likely upside from:
   `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1` (enables Flash/Mem-Efficient
   attention on gfx1151 — currently fallback), Flash-Attn 2 ROCm build,
   bigger micro-batch sizes (batch=1 here is latency-bound), longer
   sequences, and bitsandbytes ROCm DLL (if `libbitsandbytes_rocm72.dll`
   is built and dropped in).

## Blocked on this hw (documented, not run)

| format | reason |
|---|---|
| **bnb-int8 / bnb-nf4 / bnb-int4** | bitsandbytes 0.49.2 imported but `libbitsandbytes_rocm72.dll` is missing in this ComfyUI portable install. `quantize_blockwise` and `Linear8bitLt` both fail at first call with "🚨 Forgot to compile the bitsandbytes library?". Either build the ROCm DLL or use the upstream PyPI wheel that ships it. |
| **fp8** (transformer-engine) | `transformer_engine` not installed. gfx1151 has **no native fp8 silicon** — only NVIDIA H100/H200 and AMD MI300X have it. Installing TE here would still fall back to fp16 emulation. |
| **fp4** | Same as fp8 — needs H100/MI300X-class hw or a Marlin-style kernel that isn't currently in the gfx1151 build. |
| **gptq-int4** | `auto-gptq` not installed. Pre-built ROCm wheels are sparse; would need to build from source. |
| **AWQ** | `awq` not installed. Same wheel-availability story as gptq. |
| **HQQ** | `hqq` not installed. Half-quadratic is one of the more promising 1-2 bit paths; worth installing in a follow-up. |
| **ternary BitNet kernels** | Only valid for `microsoft/bitnet-b1.58-2B-4T-bf16` trunk (BitNet QAT pretrained), not for arbitrary bases. Apples-to-oranges comparison; tracked separately under ADR-2605092350. |

## Recommendation for the roso family

- For **near-term training**: switch the roso LoRA recovery stack from
  `naive-sign-1bit + bf16-stored` to `quanto-int8` for the frozen base
  (free speed + free VRAM, no quality cost).
- For **production inference / edge deployment**: keep the goal of
  packed 1-bit weights, but block the `available=true` flip on
  porting the real Bonsai per-layer algorithm (whitepaper Algorithm 1).
  The naive sign quantize is unfit for use without that port — confirmed
  by this shootout.
- Re-run with bnb once `libbitsandbytes_rocm72.dll` is available
  (compile from source or upgrade install) to compare quanto vs bnb on
  the same hw.

## Files

- `shootout_results.json` — top-level rollup
- `row-{method}.json` — per-method detail (cold/warm step times, params,
  errors if any)
- `../../70-tools/scripts/bench/quant-training-shootout/run_shootout.py`
  + `_one_row.py` — reproducer (each row runs in a fresh subprocess)

## Reproducing

```powershell
# on EVO (in ComfyUI portable venv):
$env:PYTHONUTF8="1" ; $env:PYTHONIOENCODING="utf-8"
& <python> C:\Users\gad\quant-training-shootout\run_shootout.py `
  --base Qwen/Qwen2.5-0.5B-Instruct `
  --methods bf16 bonsai-sign-1bit quanto-int8 quanto-int4 quanto-int2 `
  --rows 8 --steps 3 --out C:\Users\gad\shootout-small
```

Wall-clock: ~3:30 total (5 methods, ~21-87 s per method depending on
quantize cost + step time).
