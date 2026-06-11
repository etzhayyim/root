---
id: moemoekyun-mxfp4-training-260526
title: "moemoekyun + BitNet trainable variant — MXFP4 (OCP MX) training setup"
status: active
doc_type: explanation
topic: moemoekyun-mxfp4-training
authoritative: true
last_verified: 2026-05-26
priority: 8.5
authoritative_for:
  - "MXFP4 (OCP MX open standard) as canonical training precision"
  - "Difference from NVIDIA NVFP4 + TransformerEngine FP4 path"
  - "Applicability: moemoekyun R1.4+ MoE residual + BitNet trainable variant"
related:
  - moemoekyun-precision-architecture-260526
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
  - adr-2605261900-baien-moemoekyun-moe-charter
---

# moemoekyun + BitNet trainable — MXFP4 (OCP MX) training

User directive 2026-05-26 refined: **training を MXFP4 (OCP MX) で**, vendor-neutral open standard。

## MXFP4 (OCP MX) とは

**Open Compute Project Microscaling Formats** (2023 spec, ratified by AMD, NVIDIA, Intel, Microsoft, Meta, ARM, etc.):

| Format | Element bits | Block size | Scale | Total bits/element (effective) |
|---|---|---|---|---|
| **MXFP4 (e2m1)** | 4 (e2m1) | **32** | shared 8-bit exponent per block | 4 + (8/32) = **4.25 bits** |
| MXFP6 (e3m2) | 6 | 32 | shared 8-bit exp | 6.25 bits |
| MXFP8 (e4m3 / e5m2) | 8 | 32 | shared 8-bit exp | 8.25 bits |
| MXINT8 | 8 (int8) | 32 | shared 8-bit exp | 8.25 bits |

**MXFP4 e2m1**:
- 1 sign + 2 exponent + 1 mantissa = 4 bits per element
- 32 elements share one 8-bit exponent (block-scale)
- Effective precision: ~4.25 bits per parameter
- Loss vs FP8: minor (paper shows <1pp on most LLM evals)

## Why MXFP4 over NVIDIA NVFP4?

| Axis | MXFP4 (OCP MX) | NVIDIA NVFP4 (proprietary) |
|---|---|---|
| Spec | Open, vendor-neutral | NVIDIA-proprietary |
| Block size | 32 | 16 (per NV docs) |
| Cross-vendor compat | ✅ AMD MI / Intel Gaudi / NVIDIA all support | ❌ NVIDIA only |
| Future-proof | Industry standard, broader adoption | NV lock-in |
| Religious-corp alignment | Charter Rider §2(e) vendor-neutrality preference | tighter lock-in |
| HW support | Hopper+ (FP8 microscaling kernel) + Blackwell (native MXFP4 Tensor Core) | Blackwell only (NV) |

→ **MXFP4 is the right religious-corp constitutional choice**: matches Charter Rider §2(e) anti-vendor-lock-in spirit + future-proof if religious-corp migrates to AMD MI / Intel Gaudi or own iwakura ASIC (ADR-2605242500).

## Applicability across moemoekyun architecture

### Inference path (unchanged from precision-architecture-260526)

- BitNet 2B baseline: **ternary native** (1.58-bit packed via bitnet.cpp GPU kernel)
- moemoekyun trained checkpoint inference: **ternary native or bf16 dequant** depending on R3+ packaging

### Training path (this doc)

| Layer | Train precision | Notes |
|---|---|---|
| BitNet backbone (frozen in R1.4) | bf16 frozen | no gradient → quantization 不要 |
| MoE router (Linear hidden→E) | **MXFP4 weight + MXFP8 activation** | TE 2.0+ recipe |
| MoE experts (128 × 7 layers, small FFN) | **MXFP4 weight + MXFP8 activation** | TE 2.0+ recipe |
| Per-layer α gate (scalar) | fp32 (single scalar, microscaling 不要) | numerical stability |
| AdamW optimizer state (m, v) | fp32 master | TE auto-cast |
| Embedding (when unfrozen R3+) | MXFP8 | typically embedding stays higher-precision |
| Logit head (when unfrozen R3+) | bf16 | output projection stability |

### BitNet trainable variant (continued pretrain / fine-tune)

User directive includes "BitNet の train model も MXFP4 training":

- Use case: continued pretrain of BitNet 2B with new corpus (e.g., religious-corp-specific data, agentic traces)
- Storage: weight in **MXFP4 trainable (Quantization-Aware Training)** — i.e., maintain bf16 master + MXFP4 cast in forward, full-precision backward
- TE recipe:
  ```python
  from transformer_engine.common.recipe import MXFP8BlockScaling, Format
  # MXFP4 recipe (preview API in TE 2.0+; may need TE source build)
  recipe = MXFP4Recipe(
      fp4_format=Format.E2M1,
      mantissa_bits=1,
      exponent_bits=2,
      block_size=32,
      scale_format=Format.E8M0,  # 8-bit shared exponent
  )
  with te.fp8.fp8_autocast(enabled=True, fp8_recipe=recipe):
      output = model(input_ids)
      loss.backward()
  ```
- At end of train: quantize bf16 master → ternary (1.58-bit packed) for **inference deployment**
  - This is the **lossy step**, but well-studied (BitNet pretrain uses straight-through estimator with similar dequant→ternary path)

## TransformerEngine + PyTorch MXFP4 status (2026-Q2)

| Stack | MXFP4 support | Notes |
|---|---|---|
| TransformerEngine 1.x (current train_oka.py likely uses) | FP8 + experimental MXFP8 + MXFP6 | MXFP4 in preview/2.0 |
| TransformerEngine 2.0 (target) | Full MX format support incl. MXFP4 | Needed for this path; install via pip or source build |
| PyTorch 2.5+ | `torch.float4_e2m1` experimental | requires nightly + Blackwell HW |
| amd-mx-quantization | AMD's MX path for MI300X | parallel path |

## Action plan

### Step 1: TE 2.0 + MXFP4 recipe verify on 5090

```sh
# Pod side
pip install --upgrade "transformer-engine[pytorch]>=2.0"
python3 -c "
import transformer_engine.pytorch as te
from transformer_engine.common.recipe import Format, MXFP8BlockScaling
print('TE version:', te.__version__)
# Check if MXFP4 recipe exists
try:
    from transformer_engine.common.recipe import MXFP4Recipe
    print('MXFP4 recipe AVAILABLE')
except ImportError:
    print('MXFP4 NOT in pip release; need source build OR TE preview')
"
```

### Step 2: BaienMoEMoekyunTrainer extension to TE MXFP4

Modify `70-tools/baien-moemoekyun-train/src/baien_moemoekyun/trainer.py` (currently bf16 + per-group LR) to add `--precision mxfp4` mode:

```python
class _BaienTrainer(SFTTrainer):
    def __init__(self, ..., precision="bf16"):
        super().__init__(*args, **kwargs)
        self._precision = precision

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        if self._precision == "mxfp4":
            import transformer_engine.pytorch as te
            from transformer_engine.common.recipe import MXFP4Recipe
            with te.fp8.fp8_autocast(enabled=True, fp8_recipe=MXFP4Recipe(...)):
                outputs = model(**inputs)
        else:
            outputs = model(**inputs)
        ...
```

Plus: replace `nn.Linear` in `BaienMoEResidual` with `te.Linear` for FP4-aware forward/backward.

### Step 3: BitNet continued-pretrain variant

Separate ADR-2605263100 (new) for "BitNet trainable variant via MXFP4 continued pretrain on religious-corp corpus":

- Use case: domain adaptation of BitNet 2B-4T to religious-corp tokens (Charter / Mission Charter / kotoba-datomic / etc.)
- Training format: MXFP4 weight + MXFP8 activation
- Output: post-train BitNet 2B that is re-quantized to ternary for inference
- Distinguishes from moemoekyun (which is BitNet + MoE residual graft)

### Step 4: ADR amendments

| ADR | Amendment |
|---|---|
| ADR-2605262300 §2 precision ladder | R2/R3/R4 step ladder revised: R2 bf16 → R3 **MXFP8 mixed** → R4 **MXFP4** (open standard, NOT NV NVFP4) |
| ADR-2605263000 §1.1 Permitted | Add R1.4+ train on 5090 with MXFP4 to scope (was bench-eval only) |
| NEW ADR-2605263100 | BitNet trainable continued-pretrain variant via MXFP4 |

## Constitutional alignment

Charter Rider §2(e) "specialist gatekeeping" / vendor-lock-in spirit favors **vendor-neutral open standards**:

- MXFP4 ✓ (OCP MX, multi-vendor)
- NVFP4 ✗ (NVIDIA proprietary)

→ MXFP4 is the constitutionally-aligned training precision for moemoekyun + BitNet trainable variant.

## Cycle 14+ implementation order

1. **Verify TE 2.0 MXFP4 recipe availability** on pod (Step 1)
2. **Add precision flag** to BaienMoEMoekyunTrainer (Step 2)
3. **Smoke test**: 100-sample MXFP4 train run, verify G5/G6/G8 invariants still hold
4. **Profile**: throughput vs bf16 baseline on 5090 (expect 1.5-3× speedup for compute-bound R2+ runs)
5. **ADR amendments** (cycle 15+)
6. **BitNet trainable variant ADR** (parallel work)
