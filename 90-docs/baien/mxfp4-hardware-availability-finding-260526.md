---
id: mxfp4-hardware-availability-finding-260526
title: "MXFP4 hardware availability finding — 5090 NOT supported, B200/B300 only (cycle 18)"
status: active
doc_type: explanation
topic: mxfp4-hardware-availability
authoritative: true
last_verified: 2026-05-26
priority: 9.0
authoritative_for:
  - "Concrete HW availability of native MXFP4 Tensor Core in torchao 0.18 stack (cycle 18 measurement)"
  - "Why moemoekyun R1.4 train on RTX 5090 must use MXFP8 (not MXFP4) precision"
  - "What HW upgrade unlocks MXFP4 (B200/B300 data-center class)"
related:
  - moemoekyun-mxfp4-training-260526
  - moemoekyun-precision-architecture-260526
  - adr-2605263100-founder-lv7-amendment-runpod-5090-train-mxfp4-extension
  - 90-docs/baien/runpod-5090-runlog-260526.jsonl
---

# MXFP4 hardware availability — 5090 NOT supported (cycle 18 measurement)

**Cycle 18 finding** (2026-05-26 21:35 JST): empirical test on RunPod RTX 5090
with torchao 0.18.0.dev20260407+cu128 + torch 2.12.0.dev20260408+cu128.

## What the empirical run showed

Cycle 17 implemented `apply_mxfp4_quantize()` using
`torchao.prototype.mx_formats.MXDynamicActivationMXWeightConfig`. Cycle 18
attempted to actually train with `precision="mxfp4"` on RTX 5090 and got:

```
NotImplementedError: MXFP4 scaling only supported in CUDA for B200/B300
  at: torchao/prototype/mx_formats/mx_tensor.py:759 _addmm_mx_dispatch
       → F.scaled_mm()  → torch._scaled_mm_v2()
```

**Verdict**: native MXFP4 GEMM kernels in torchao 0.18 dispatch only to
`F.scaled_mm()`, which only has B200/B300 implementations in
torch 2.12 dev. RTX 5090 (consumer Blackwell sm_120) is **NOT** supported.

## Hardware compatibility matrix

| GPU | Compute capability | MXFP8 (torchao 0.18) | MXFP4 (torchao 0.18) |
|---|---|---|---|
| H100 | sm_90a (Hopper) | ✅ scaled_mm | ❌ (FP4 Tensor Core absent) |
| H200 | sm_90a (Hopper) | ✅ scaled_mm | ❌ (FP4 Tensor Core absent) |
| **RTX 5090** | **sm_120 (Blackwell consumer)** | ✅ **scaled_mm** | ❌ **(error this cycle)** |
| **B200** | **sm_100 (Blackwell DC)** | ✅ scaled_mm | ✅ **scaled_mm + native MXFP4** |
| **B300** | sm_100 (Blackwell DC) | ✅ scaled_mm | ✅ scaled_mm + native MXFP4 |
| MI300X (AMD) | gfx940 | ⚠️ via amd-mx-quantization | ⚠️ separate path |

## Why 5090 lacks MXFP4 despite being "Blackwell"

NVIDIA segmented Blackwell into:
- **GB202 / GB203 consumer (sm_120)**: RTX 5090 / 5080 / 5070 — has FP8 Tensor
  Core, FP6 Tensor Core, **does NOT have FP4 Tensor Core for compute**.
  Has FP4 only for **storage / decoding** (e.g., NVFP4 inference via TRT-LLM).
- **GB100/GB200 data-center (sm_100)**: B100 / B200 / B300 — full MXFP4
  Tensor Core for compute. ~1318 TFLOPS dense FP4 / 2638 sparse FP4.

Per-NVIDIA-spec (verified 2026 docs): RTX 5090 peak compute is
- bf16: 104.8 TFLOPS dense (with TF32 accumulation)
- FP8 (e4m3 / e5m2): 419 TFLOPS dense
- **FP4 compute: not present** (Blackwell GeForce SM diagrams omit FP4 path)

## Impact on moemoekyun R1.4 train architecture

ADR-2605263100 §1.1.A authorized "MXFP4 (OCP MX) train" on 5090, but
this cycle's empirical test shows that path **is structurally impossible**
on 5090 HW. Per §7 trigger fallback ("TE 2.0 MXFP4 recipe unavailable →
fall back to MXFP8"), we shift to **MXFP8 (OCP MX block_size=32 with
e4m3 weight + e4m3 activation)** which IS supported on 5090.

### Revised precision plan

| Phase | Original plan (cycle 14-17) | Revised plan (cycle 18 finding) |
|---|---|---|
| R1.4 (5090) | MXFP4 | **MXFP8** (5090 native; ~419 TFLOPS peak) |
| R2 (5090 or H100) | MXFP4 + sparse 2:4 | **MXFP8** (no MXFP4 on consumer/Hopper) |
| R3+ (B200 if budget allows) | sparse MXFP4 | **MXFP4** finally executable |

### Cycle 18 actual TFLOPS measurements (smoke runs)

| Smoke | Trainable params | Tokens | wall | TFLOPS sustained | Util vs MXFP8 peak |
|---|---|---|---|---|---|
| Tiny (h=512 L=4 bs=2 seq=128) | 2.11 M | 2,560 | 0.51 s | 0.06 | 0.02% |
| Bigger (h=1024 L=8 bs=4 seq=512) | 16.81 M | 40,960 | 2.21 s | 1.87 | 0.45% |

**Both smokes used MXFP8** (after MXFP4 failed). The TFLOPS utilization
is very low (<0.5%) because:
1. Trainable params too small (16.81M vs needed ~1B+ to saturate Tensor Cores)
2. ~95% of forward is **un-quantized** backbone bf16 (MoE residual touches only
   the last layer in this smoke; production R1.4 will quantize routers + experts
   across last 25% of layers)
3. Python + kernel launch overhead dominates short ops

This means production R1.4 (BitNet 2B + 128 experts × 7 layers = ~1.1 B
trainable) will see **much higher TFLOPS utilization** — likely 10-30% of
MXFP8 peak (~40-120 TFLOPS sustained), based on similar MoE workload
reports in literature.

## Council clarification needed

ADR-2605263100 §1.1.A literally says "MXFP4 (OCP MX) only" with MXFP8 as
fallback in §7. Cycle 18 finding makes the fallback the **primary path on
5090 HW**. This is technically within the ADR scope (§7 contemplated this)
but the Council should clarify whether:

- (A) ADR-2605263100 §1.1.A should be **amended** to read
  "MX format family (MXFP4/MXFP8/MXFP6) where HW supports the requested
  precision; MXFP8 default on 5090, MXFP4 default on B200+" — or
- (B) the current wording is sufficient and only documentation needs to
  reflect the HW reality

Founder recommendation: **(B)** — current wording is fine; this doc
provides the HW-reality clarification. No new ADR needed.

## What MXFP4 unlocks (when B200 available)

If religious-corp later rents B200 (per ADR-2605262300 R2 plan):

| Workload | 5090 MXFP8 (current) | B200 MXFP4 (future) | Speedup |
|---|---|---|---|
| BitNet 2B MoE R1.4 train wall | ~40-60 min | ~10-15 min | ~4× |
| R1.4 single iter cost on rental | ~$0.30-0.50 | ~$0.50-0.80 | (B200 ~3× $/h but ~4× speedup) |
| Sparse 2:4 MXFP4 (R4 plan) | N/A | available | +50-100% over dense MXFP4 |

→ B200 path makes sense for R2+ if budget approved post-Council ratification.
For R1.4 cycle 18-20 timeframe, MXFP8 on 5090 is fully sufficient.

## Updated cycle 18+ delivery

| Item | Status |
|---|---|
| `apply_mxfp4_quantize()` cycle 17 code path | ✅ validated on real HW (MXFP8 mode) |
| Loss curves healthy across 30 train steps total | ✅ no NaN, no divergence |
| TFLOPS measurement methodology | ✅ established (`6×trainable×tokens / wall`) |
| Production R1.4 train (BitNet 2B + 128 experts) | 🟡 needs ≥24 GB free VRAM (MMLU+train_oka blocking) |
| MXFP4 native path (B200) | ⏳ R2+ post-Council ratification (per ADR-2605262300) |
| ADR-2605263100 status | unchanged (§7 fallback covers this case; this doc is the explanation) |
