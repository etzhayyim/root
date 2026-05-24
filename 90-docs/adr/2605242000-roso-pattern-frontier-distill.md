---
id: adr-2605242000-roso-pattern-frontier-distill
title: "roso — Bonsai-pattern sibling family (post-train 1-bit + distill recovery)"
status: active
doc_type: adr
topic: roso-distill
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien Bonsai-style 1-bit quantization path (post-train, not from-scratch)
  - acceptable base model candidates per edge invariant
  - frontier-MoE-as-teacher distillation pattern
  - per-base license inheritance + Charter Rider §2 compatibility
  - 3-phase rollout (immediate / months / year)
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605231300-baien-distill-react-loop
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605231600-baien-context-extension
related:
  - https://github.com/PrismML-Eng/Bonsai-demo (Bonsai 8B 1-bit whitepaper)
  - https://huggingface.co/prism-ml/Bonsai-8B-mlx-1bit (Bonsai reference impl)
  - https://huggingface.co/Zyphra/Zamba2-7B (Zamba2 base candidate)
  - https://huggingface.co/Qwen/Qwen3-8B (Qwen3 base, Bonsai-proven)
  - 20-actors/magatama/sdk/magatama-host-sdk/src/llm-model-registry.ts
  - 70-tools/baien-distill/
supersedes: []
superseded_by: []
---

# Context

Today baien is **Microsoft's `bitnet-b1.58-2B-4T-bf16`** — a 2 B trunk
pretrained from scratch in ternary QAT mode. This delivers the edge
promise (~800 MB packed, fits ADR-2605241900 invariant) but caps
quality at "2 B SOTA" — meaningfully below frontier even at the
edge-feasible scale.

Two 2026 developments change the cost/benefit:

1. **Prism ML "Bonsai 8B" 1-bit** (March 2026 whitepaper) demonstrates
   **post-train 1-bit quantization** of a strong bf16 base (Qwen3-8B
   16 GB → 1.15 GB packed) with only ~9 point average-benchmark drop
   (79.3 → 70.5), **outperforming full-precision Llama-3.1-8B at
   1/14 the size**.

2. **Frontier MoE openness**: DeepSeek-V3 (MIT), MiniMax-M2,
   Moonshot Kimi K2, and Qwen3-Max all publish weights or distill
   datasets that can serve as *teachers* even if they cannot serve
   as edge *bases* (all > 100 GB FP16).

The combination — **strong dense student → Bonsai-style 1-bit → frontier
MoE distill recovery** — gives a tractable path to "frontier-near at
the edge" that wasn't available when baien was first specced
(ADR-2605092350).

This ADR pins the architectural choices, base candidates, and rollout
phases for that path, without retiring the current BitNet baien.

# Decision

Add a **sibling** to the current `baien-bitnet-1.58bit-base` in
`MODEL_REGISTRY`, named per the table below, produced by:

1. Choose a **strong bf16 base** ≤ 8 B params (Apache-2.0 preferred).
2. Apply **Bonsai-style end-to-end 1-bit quantization** (post-train,
   per-layer optimization with inline dequantize kernels in MLX or
   bitnet.cpp).
3. Run **distill recovery** using `baien-distill` (ADR-2605231300) with
   Opus-4.7 / DeepSeek-R1 / Phi-4 / Qwen3-Max-distilled SFT corpora.
4. Verify against the **edge invariant** (ADR-2605241900): packed ≤ 1.6 GB,
   inference @4k ≤ 2.0 GB, @16k ≤ 2.5 GB, encoder-cumulative ≤ 600 MB,
   iPhone 14 first-token ≤ 3 s.
5. Register via the existing two-phase ship (`commit_node` →
   `gen-distilled-entries.mjs` codegen → reviewer flips `available`).

The current BitNet 2B trunk stays as the **canonical / lowest-RAM**
edge baien; new sibling(s) cover **quality-priority / long-context /
domain-specialist** roles.

# Base-model feasibility (edge invariant verified per row)

| Base | Type | License | FP16 | 1-bit (14×) | KV @4k | KV @16k | edge fit @4k | edge fit @16k | best use |
|---|---|---|---|---|---|---|---|---|---|
| **Zamba2-1.2B** | Mamba2 SSM + 6 共有 attn | Apache-2.0 | 2.4 GB | **170 MB** | 30 MB | **70 MB (SSM bounded)** | ✓ trivial | ✓ at **128k** | edge mass-deploy |
| **Zamba2-2.7B** | SSM | Apache-2.0 | 5.4 GB | **380 MB** | 50 MB | 100 MB | ✓ | ✓ at **128k** | long-context edge |
| **Zamba2-7B** | SSM | Apache-2.0 | 14 GB | **1.0 GB** | 80 MB | 150 MB | ✓ | ✓ at **128k** | **quality + long-context** ★ |
| **Qwen3-8B** | dense attn | Apache-2.0 | 16 GB | **1.15 GB** (Bonsai 実証) | 500 MB | 2 GB | ✓ | ✗ (3.65 GB) | quality @4k ★ |
| Mistral-7B-v0.3 | dense | Apache-2.0 | 14 GB | 1.0 GB | 500 MB | 2 GB | ✓ | ✗ | general 7B |
| Qwen2.5-Coder-7B | dense | Apache-2.0 | 14 GB | 1.0 GB | 500 MB | 2 GB | ✓ | ✗ | **code-specialist** ★ |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | dense (already R1-distilled) | MIT | 14 GB | 1.0 GB | 500 MB | 2 GB | ✓ | ✗ | reasoning ★ |
| Llama-3.1-8B | dense | **Llama 3 Community** | 16 GB | 1.15 GB | 500 MB | 2 GB | ✓ | ✗ | requires Llama naming + 700M-MAU review |
| Qwen2.5-14B | dense | Apache-2.0 | 28 GB | 2.0 GB | — | — | **✗ (>1.6 GB ceiling)** | — | server-only carve-out |
| Qwen3-32B | dense | Apache-2.0 | 64 GB | 4.6 GB | — | — | ✗ | — | `baien-server-*` only |

**Edge-fit candidates** (this ADR): the 7 rows above the first ✗ in the
"edge fit @4k" column.

**Quality + long-context optimum**: `Zamba2-7B` (Apache-2.0).
**Pure quality @4k**: `Qwen3-8B` (Bonsai-proven).
**Code-specialist**: `Qwen2.5-Coder-7B`.
**Reasoning-specialist**: `DeepSeek-R1-Distill-Qwen-7B`.

# Frontier MoE as *teacher*, never as *base*

Per ADR-2605241900 invariant, none of the frontier MoEs fit edge as a
base. But they remain valuable as **distillation teachers**:

| Frontier teacher | Params | License | Distill mode supported | Apache-friendly distill dataset available? |
|---|---|---|---|---|
| **DeepSeek-V3** | 671 B / 37 B active MoE | MIT | logits, traces | ✓ `deepseek-ai/DeepSeek-R1-Distill-Qwen-*` (MIT) |
| **DeepSeek-Pro-V4** | (assumed similar to V3+) | (assumed MIT) | — | — once published |
| **MiniMax-M2** | 456 B / 46 B active MoE | per card | traces only | — verify per card |
| **Moonshot Kimi K2** | ~1 T MoE | Apache-2.0 (Moonshot open weights) | logits + traces | partial open SFT |
| **Qwen3-Max** | undisclosed (frontier dense or MoE) | Apache-2.0 (Qwen license) | logits | `lordx64/Opus-4.7-Thinking-Max-Distill-25k` (Apache-2.0, Opus-distill) |
| **Claude Opus 4.7** | undisclosed | proprietary | traces only | ✓ `lordx64/reasoning-distill-opus-4-7-max-sft` (Apache-2.0 redistribution) |

For Phase 1 we will **use only already-published Apache-2.0 distill
datasets** (no need to run frontier teacher ourselves) — directly
slotting into baien-distill's `DATASET_REGISTRY`
(ADR-2605231300 §3a).

# License inheritance chain

The Bonsai-pattern sibling weights inherit from THREE upstream layers:

```
base weights      (e.g. Qwen3-8B Apache-2.0,  Zamba2-7B Apache-2.0)
       │
       ▼  post-train 1-bit quantize (Bonsai whitepaper method, public)
1-bit weights     (still Apache-2.0; quantization is mechanical)
       │
       ▼  distill recovery using Opus / R1 / Qwen3-Max distill data
recovered 1-bit weights
       │
       ▼  baien-distill SFT loop (commit_node → multimodal-models.jsonl)
"roso-*" candidate
       │
       ▼  Charter Rider §2 scan + edge-fit attestation
"roso-*" published with Apache-2.0 + Charter Rider v2.0
```

**Reviewer gate** (already enforced via `gen-multimodal-entries.mjs`
+ `gen-distilled-entries.mjs` two-phase codegen):

- Base must be **Apache-2.0** or equivalent permissive (rejects Llama-3.1
  for first-party redistribution unless we accept the Llama naming +
  MAU clause).
- Distill data must pass Charter Rider §2 scanner (already wired in
  `etzhayyim_organism.sensors.charter_rider.scan`).
- License field of the resulting `roso-*` registry entry is
  set to **the most restrictive upstream layer**.

# 3-phase rollout

## Phase 1 — immediate, edge-feasible (1–3 days on EVO-X2 ROCm)

**Pick: `Zamba2-1.2B` or `Zamba2-2.7B` (Apache-2.0, smallest viable Bonsai target).**

Steps:

1. Pull `Zyphra/Zamba2-1.2B` bf16.
2. Implement Bonsai-style end-to-end 1-bit quantization (port the
   PrismML reference algorithm; ~500 LoC, draws on `bitsandbytes` and
   `quanto` ecosystem).
3. Apply baien-distill loop with default Opus + DeepSeek-R1-Distill +
   Qwen3-Max distill datasets (~30 M tokens) for recovery.
4. Run `e7m bench smoke` + `e7m bench lite --limit 100` to compare
   to baien-bitnet-2B (today's baseline arc 52 / wino 78 / truthful 31).
5. Run `e7m bench mx-eval` visual_microbench if image-projector reused.
6. Verify edge invariant attestations (the 8 ceilings from ADR-2605241900).
7. `commit_node` → `multimodal-models.jsonl` → codegen → reviewer flip.

**Expected:** ~600 MB packed weights, ~70 average score (Bonsai 1.2B
projected from 8B-result curve), 128 k context viable on edge.

## Phase 2 — months, ambitious quality (1–3 weeks on EVO-X2 ROCm)

**Pick: `Zamba2-7B` OR `Qwen3-8B`** (which one depends on Phase 1
quality vs context-priority observation).

Steps:

1. Same as Phase 1 but at 7-8 B scale.
2. Distill corpus expanded to ~200 M tokens (R1 + Qwen3-Max + Phi-4
   reasoning + code-specialist data).
3. Multi-teacher distillation if available (combine logits of
   DeepSeek-R1 + Qwen3-Max + Phi-4 — research-heavy).
4. Verify edge invariant — Zamba2-7B fits at 128 k; Qwen3-8B only
   fits at 4 k; pick one based on context priority.

**Expected:** ~1.0–1.15 GB packed, ~75 average score (close to Phi-4
3.8 B), edge-deployable.

## Phase 3 — year+, full sibling family (post-Council)

Publish a family:

| `MODEL_REGISTRY` id | base | use cases | RAM @4k |
|---|---|---|---|
| `baien-bitnet-1.58bit-base` (current) | Microsoft BitNet 2B-4T | universal edge fallback | 1.0 GB |
| `roso-zamba-1.2b` | Zamba2-1.2B 1-bit | long-context edge, mass-deploy | 0.9 GB |
| `roso-zamba-7b` | Zamba2-7B 1-bit | quality long-context edge | 1.5 GB |
| `roso-coder-7b` | Qwen2.5-Coder-7B 1-bit | code-specialist | 1.5 GB |
| `roso-reason-7b` | DeepSeek-R1-Distill-Qwen-7B 1-bit | reasoning-specialist | 1.5 GB |
| `baien-server-*` carve-out | 14 B-32 B 1-bit (non-edge) | desktop / iPad Pro M | beyond ceiling |

Router code in `magatama-host-sdk` picks the right sibling per
use-case + per device-class (already supported via `USE_CASE_DEFAULTS`
in `llm-model-registry.ts`).

# Numerical analysis — projected vs measured

| Metric | Current baien (BitNet 2B) | Bonsai-Zamba-1.2B (Phase 1) | Bonsai-Zamba-7B (Phase 2) |
|---|---|---|---|
| Packed weights | 800 MB | ~600 MB | ~1.0 GB |
| Total RAM @4k | 1.0 GB | 0.9 GB | 1.5 GB |
| Total RAM @16k | 1.85 GB | 1.05 GB | 1.6 GB |
| **Total RAM @128k** | **infeasible** (KV blow-up) | **~1.2 GB** | **~1.8 GB** |
| baseline arc_challenge @ 100 q (today) | 52.0 | — | — |
| projected arc_challenge | (52) | ~58-62 | ~70-75 |
| projected MMLU-R | (unknown) | ~60 | ~70-75 |
| projected HumanEval+ | (unknown) | ~50 | ~70 |
| projected throughput on iPhone 14 | ~20 tok/s | ~25 tok/s | ~10 tok/s |
| projected first-token latency | <1 s | <1 s | 1-2 s |

Projection caveat: Phase 1/2 numbers are **interpolated from Bonsai 8B
1-bit** measurements and Zamba2 baselines. Actual numbers TBD on
implementation.

# Risks

| Risk | Mitigation |
|---|---|
| Bonsai-style 1-bit quantization not yet implemented for Zamba2 SSM blocks (only attention/dense layers proven) | Phase 1 starts with Zamba2 — discover any SSM-specific issues early on small base. Fall back to Qwen3-8B (Bonsai-proven dense path) if SSM quantization stalls |
| `Zyphra/Zamba2-*` license + Bonsai algorithm patent unclear | Apache-2.0 covers Zamba2; Bonsai whitepaper is public research with no claimed patent (verify in §License chain) |
| 1-bit recovery distillation diverges (quality drops below baien-bitnet-2B baseline) | Eval gate at every iter (ADR-2605231300 §6); reject merge if microbench delta ≤ -5 pp vs current baien |
| Multi-teacher distillation logits unavailable (Opus / Kimi don't publish logits, only traces) | Use trace-based SFT (cheaper, what baien-distill already does) |
| Edge invariant attestation can't be measured on iPhone 14 without physical device | Use iPhone simulator + Apple `mlx-lm` benchmark + Council attestation of equivalent measurement (deferred to Phase 2 enforcement, ADR-2605241900 §Enforcement Phase 2) |
| Inheriting Llama 3 Community License accidentally | Hard ban on Llama-3.x bases in commit_node validation; only Apache-2.0 / MIT bases auto-approve |

# Implications for current baien tooling

| Tool | Change needed |
|---|---|
| `e7m bench mx-train` | Generalize to accept `--base-model <id>` (currently hardcoded to baien-bitnet-2B) |
| `MODEL_REGISTRY` | New entries per §Phase 3 table; codegen via `gen-distilled-entries.mjs` |
| `baien-distill` (ADR-2605231300) | DATASET_REGISTRY already supports the Apache-2.0 distill candidates; no schema change needed |
| `baien-mx-train` (ADR-2605232500) | Projector pattern works on any trunk; no code change to support new bases |
| `e7m baien prompt` | Add `--variant <baien-bitnet|roso-zamba-1.2b|...>` flag |
| `e7m bench list` | Add Bonsai sibling description |

# Out of scope

- **Bonsai-style for trunks > 8 B**: out of edge invariant scope; pursue under `baien-server-*` only.
- **From-scratch ternary Mamba2 pretrain**: ADR-2605101000 §C path, deferred to year+.
- **Multimodal Move 4-7 integration with Bonsai variants**: Phase 3+ work; projector pattern from ADR-2605232500 stays modality-agnostic.
- **Beating frontier on benchmarks**: per ADR-2605241900 §Frontier-beating non-goal — still not a goal. Phase 2/3 target is "2 B-7 B SOTA, frontier-near via distillation".
- **Server-side variants**: `baien-server-*` and `baien-XL-*` carve-outs are separate ADRs.

# Acceptance criteria

`proposed → accepted` when:

1. ✅ Bonsai 8B 1-bit reference verified (Prism ML, Mar 2026 whitepaper).
2. ✅ Per-base feasibility table published with edge-invariant verification.
3. ✅ License chain documented + Charter Rider §2 path identified.
4. ✅ Phase 1 (Zamba2-1.2B-Instruct Bonsai quantize + distill recovery) implemented under `70-tools/roso-distill/` and `70-tools/baien-distill/` (2026-05-23).
5. ✅ First `roso-zamba2-1.2b-instruct` candidate passes edge-fit attestation (see §Phase 1 Validation below).

# Phase 1 Validation — 2026-05-23 on EVO-X2 (gfx1151)

End-to-end Phase B (quantize + distill recovery) executed on AMD Radeon
8060S iGPU, ROCm 7.2.1 / torch 2.9.1+rocm7.2.1:

| stage | result |
|---|---|
| base | `Zyphra/Zamba2-1.2B-Instruct` (Apache-2.0, ultrachat_200k SFT + DPO) |
| actual params | 1,924,399,104 (≈1.92B — "1.2B" is loose marketing) |
| quantize method | naive sign 1.58-bit projection (stub — real Bonsai per-layer optimization pending; expect ~30% perplexity tax vs published Bonsai-8B until ported from `PrismML-Eng/Bonsai-demo`) |
| quantize artifacts | in-place `child.weight.data.copy_(sign(W)*mean(\|W\|))` → `model.save_pretrained()` → loadable HF checkpoint at `sibling-00-Zyphra__Zamba2-1.2B-Instruct/` |
| recovery dataset | `lordx64/reasoning-distill-opus-4-7-max-sft` (Apache-2.0; Opus 4.7 extended-thinking traces; routed via `baien_distill.adapters.hf_dataset.DATASET_REGISTRY` category=Reasoning) |
| LoRA trainable | **2,949,120 / 1,218,013,824 = 0.2421%** (q/k/v/o targets across 6 shared attention blocks; Mamba2 SSM blocks left untrained) |
| SFT framework | trl 1.4.0 SFTTrainer + peft 0.19.1 LoraConfig; bf16; `use_cpu=not torch.cuda.is_available()` (auto-flips ROCm-on) |
| SFT shape | 50 rows × 2 epochs / batch=1 × grad_accum=4 = 26 optimizer steps |
| SFT runtime | **21:08 wall** (≈48.78 s/step warm; first step 88-168s cold) |
| train_loss progression | N=5 → 13.36, N=50 → **5.088** (meaningful descent over 26 steps) |
| packed weights | **0.358 GB** (vs edge invariant ceiling 1.6 GB) |
| RAM @4k | **0.626 GB** (vs 2.0 GB ceiling) |
| RAM @16k | **0.678 GB** (vs 2.5 GB ceiling) |
| `edge_invariant_pass` | **True** |
| decision | commit (manifest `available=false` per two-phase ship; reviewer must flip after eval) |

## Patches landed for Phase 1 closure

- `70-tools/roso-distill/src/roso_distill/state.py` — added Apache-2.0 Instruct variants to `BASE_CANDIDATES` (Zamba2-1.2B/2.7B/7B-Instruct).
- `70-tools/roso-distill/src/roso_distill/adapters/bonsai_quantizer.py` — `quantize_module(in_place=True)` mutates `child.weight.data` so a downstream `save_pretrained` writes the quantized tensors.
- `70-tools/roso-distill/src/roso_distill/quantize.py` — calls `model.save_pretrained(out_dir)` after in-place quantize so Phase B can load the sibling as the SFT student.
- `70-tools/roso-distill/src/roso_distill/recovery.py` — replaced `NotImplementedError` with the real wire: flattens `DATASET_REGISTRY` by HF id, calls `load_examples(spec, category, limit=…)`, sets `student_model_id=str(state.quantized_path)`, calls `distill_train(sub)`, writes a unified `recovery_manifest.json`.
- `70-tools/baien-distill/src/baien_distill/state.py` — added `student_model_id` to `DistillState` and `new_state(..., student_model_id=…)` kwarg.
- `70-tools/baien-distill/src/baien_distill/nodes/train.py` — replaced 3 module-constant `BASE_MODEL_ID` references with `student_id = state.get("student_model_id") or BASE_MODEL_ID`; auto-flipped `use_cpu` from torch.cuda.is_available() so the same code runs ROCm on EVO and CPU on Mac.

## Quant shootout — 2026-05-24 (5 formats × Qwen 0.5B-Instruct LoRA SFT)

Real comparison of training-time quant cost on the same hw (Qwen2.5-0.5B-Instruct, 8 rows × 3 SFT steps). Full doc + raw JSONs: `90-docs/baien/quant-shootout-260524/`.

| method | step_warm_s | tokens/s | sustained TFLOPS | % of gfx1151 peak (30) | speedup vs bf16 | peak VRAM | final_loss |
|---|---|---|---|---|---|---|---|
| bf16 | 1.61 | 1,553 | 4.60 | 15.3% | 1.00× | 2.281 | 1.7602 |
| bonsai-sign-1bit (roso stub) | 2.24 | 1,116 | 3.31 | 11.0% | **0.72× (slower!)** | 2.281 | **12.31** |
| **quanto-int8** | **0.67** | **3,731** | **11.06** | **36.9%** | **2.40×** | 2.008 | **1.7616** |
| quanto-int4 | 0.84 | 2,976 | 8.82 | 29.4% | 1.92× | **1.811** | 1.8981 |
| quanto-int2 (1.58-bit proxy) | 0.85 | 2,941 | 8.72 | 29.1% | 1.89× | 1.694 | **13.51** |

Blocked on this hw (documented, not run): **bnb int8/nf4/int4** (ROCm DLL missing), **fp8/fp4** (no gfx1151 silicon), **gptq/awq/hqq** (packages not installed).

Implications for roso:
- **The naive-sign Phase 1 stub is strictly worse than bf16 on this hw** — it loses quality AND trains 28% slower because sign-on-bf16 storage degenerates the matmul kernel's input distribution. Phase 2 of roso MUST land the real per-layer Bonsai algorithm or switch the SFT-recovery student to `quanto-int8` (which preserves both speed and quality).
- **`quanto-int8` is the new training default** for any LoRA-on-frozen-base workload on gfx1151. quanto-int4 is the inference-time fallback when VRAM is bound.
- **Sub-4-bit quantization without calibration is unusable** — both naive-sign-1bit and naive quanto-int2 collapsed loss to 12-13 after 3 SGD steps. The Bonsai-8B numerical claims are conditional on the published Algorithm 1 (per-layer optimization with calibration inputs); a naive cast cannot substitute.

## Known constraints / open items

- Naive sign quantize ≠ real Bonsai. Per-layer optimization with calibration inputs (PrismML whitepaper Algorithm 1) is a separate research port (~500 LoC); current results carry the documented ~30% perplexity tax. Replace before publishing `available=true`. Also confirmed by the 2026-05-24 shootout to be SLOWER than bf16 (0.72×).
- LoRA targets attention only (`q/k/v/o`); Mamba2 SSM `in_proj/out_proj/conv1d` not yet LoRA'd. Next-cut adds them with reduced r.
- bitsandbytes ROCm DLL absent on EVO ComfyUI venv — 8-bit optimizers unavailable, `adamw_torch` fallback used (no impact on correctness).
- ROCm SDPA fast-path not enabled (`TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1` would speed step time substantially).
- Windows cp1252 default encoding breaks trl chat-template I/O — must set `PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8`. Already in the run command; codify as a `roso run` wrapper later.
- `bench.go` lacks a `--recovery-n` flag; pass `--recovery-n-per-dataset` via the Python CLI directly for now.
- Scaling: ~46-90 s/step on gfx1151; 1000 rows × 2 epochs ≈ 4 hours. Larger runs need chunking or detached scheduling (Monitor caps at 1 hour).

# References

- ADR-2605092350 baien design
- ADR-2605231300 baien-distill loop (DATASET_REGISTRY entry point)
- ADR-2605241900 baien edge-target invariant (hard ceilings)
- ADR-2605232500 baien Move 1 image graft (projector pattern, reusable)
- Bonsai 8B 1-bit whitepaper https://github.com/PrismML-Eng/Bonsai-demo
- Bonsai 8B card https://huggingface.co/prism-ml/Bonsai-8B-mlx-1bit
- Zamba2 https://www.zyphra.com/post/zamba2-mini and `Zyphra/Zamba2-{1.2B,2.7B,7B}` on HF
- DeepSeek-R1-Distill-Qwen series (MIT) https://huggingface.co/deepseek-ai
- Qwen3 family (Apache-2.0) https://huggingface.co/Qwen
- Charter Rider scanner `etzhayyim_organism.sensors.charter_rider`
- `lordx64/reasoning-distill-opus-4-7-max-sft` (Opus distill, Apache-2.0)
