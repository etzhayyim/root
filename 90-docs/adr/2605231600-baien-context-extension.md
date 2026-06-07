---
id: adr-2605231600-baien-context-extension
title: "Baien context window extension — 4k → 16k / 64k / 128k staged roadmap"
status: proposed
doc_type: adr
topic: baien-context-extension
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien (BitNet b1.58 2B-4T) context-window extension strategy
  - per-stage gate criteria + numerical budgets
  - BitNet-specific RoPE / KV-cache caveats
  - relation between context extension and baien-distill / baien-MX / baien-graft pipelines
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605231300-baien-distill-react-loop
  - adr-2605202345-evo-x2-gpu-pod-fleet-integration
related:
  - 70-tools/baien-distill/scripts/rope_extend_probe.py     (Stage 1 smoke)
  - 70-tools/scripts/bench/baien-microbench/microbench_long.py
  - 90-docs/baien/context-extend-snapshot-260523.md         (results, to be created)
supersedes: []
superseded_by: []
---

# Goal

Extend baien's effective context window from the official **4,096
tokens** (per Microsoft's `microsoft/bitnet-b1.58-2B-4T-bf16`
`config.json`) to a usable **16k baseline** (Stage 1, immediate) and
record a path to **64k / 128k** (Stages 2-3) without breaking baien's
edge / browser / CPU deployment promise.

This ADR is *not* about pretraining a longer-context BitNet from
scratch — that is Microsoft's domain. It is about **post-hoc context
extension** of the published 4k checkpoint on the etzhayyim fleet.

# Verified base model spec (from upstream `config.json`)

| Knob | Value |
|---|---|
| `max_position_embeddings` | **4,096** |
| `rope_theta` | 500,000.0 |
| `rope_scaling` | `null` (none configured upstream) |
| `num_attention_heads` | 20 (`head_dim = 128`) |
| `num_key_value_heads` | 5 (GQA 4:1 — KV cache = 1/4 of a dense-attn model of same width) |
| `num_hidden_layers` | 30 |
| `hidden_size` / `intermediate_size` | 2,560 / 6,912 |
| Activation / Norm | Squared-ReLU / SubLN |
| Tokenizer | LLaMA 3 (vocab 128,256) |
| License | MIT |

Microsoft's own card states: *"For optimal performance on tasks
requiring very long contexts (beyond the pre-training length or for
specialized long-reasoning tasks), we recommend performing
intermediate long-sequence adaptation/training before the final
fine-tuning stage."* This ADR operationalizes that recommendation.

# Decision

Phase the extension in **3 stages**, with explicit **gate criteria**
between stages so we never commit Stage N+1 compute before Stage N
proves quality + cost are acceptable.

```
Stage 1 ── rope_theta scaling  ──▶  4k →   16k    no training        ~30 min
   gate: ppl_4k inflation ≤ +5%, microbench pass-rate Δ ≤ -5pp
Stage 2 ── YaRN + LoRA fine-tune ──▶ 4k →  64k    ~500 step LoRA     4-8h ROCm
   gate: 16k retrieval recall ≥ 0.80, 64k recall ≥ 0.50
Stage 3 ── LongRoPE + continual  ──▶ 4k → 128k    ~1k step CT        24-48h ROCm
   gate: ADR amendment + cost approval
Stage 4 ── architecture surgery   (out of scope of this ADR)
```

Each stage produces:
- a verifiable score snapshot (microbench_long.py),
- a checkpoint variant (either config-only or LoRA adapter, registered
  via `commit_node` per ADR-2605231300),
- an explicit "promote / reject / hold" decision recorded in the
  snapshot doc.

# Numerical analysis

## KV cache cost (the bounded resource)

```
KV_bytes / token = 2 (K+V) × num_kv_heads × head_dim × num_layers × dtype_bytes
                 = 2          × 5             × 128       × 30          × 2 (bf16)
                 = 76,800     B  ≒  75 KB / token
```

| Target ctx | KV total | EVO-X2 96 GB RAM concurrent sessions | Browser/WebGPU budget |
|---|---|---|---|
| 4k (default) | 0.30 GB | 320 | OK |
| 8k | 0.60 GB | 160 | OK |
| **16k (Stage 1 target)** | **1.20 GB** | **80** | **borderline** |
| 32k | 2.40 GB | 40 | not viable |
| 64k (Stage 2 target) | 4.80 GB | 20 | server-only |
| 128k (Stage 3 target) | 9.60 GB | 10 | server-only |

The GQA 4:1 ratio (5 KV heads vs 20 attention heads) gives baien a
**4× memory headroom** vs a hypothetical dense-attention BitNet of
the same width — without GQA, 16k would already be at 4.8 GB.

## Attention compute scaling

Naive attention is O(n²) per layer. Relative to 4k:

| Target ctx | Attention FLOPs ratio | Per-token decode latency ratio (CPU bf16 estimate) |
|---|---|---|
| 4k | 1× | 1× |
| 16k | 16× | ~5-6× (only attention scales quadratically; ~70% of decode is MLP which is linear) |
| 32k | 64× | ~12× |
| 64k | 256× | ~40× |
| 128k | 1024× | ~120× |

Browser / mobile NPU deployment past **8k context** is not realistic
without sliding-window or sink-attention (Stage 4 territory). Server
side (EVO-X2 ROCm), Stages 2-3 are feasible.

# Stage 1 — rope_theta scaling (DEFAULT, smoke-first)

The cheapest possible extension: override `config.rope_theta` so the
positional frequencies are scaled down, letting attention extrapolate
beyond the trained 4k. Two flavors, both **inference-time only**:

| Flavor | Config change | Effective ctx |
|---|---|---|
| Linear theta scaling | `rope_theta = 500_000 × extend_factor` | factor× original = 4k × factor |
| NTK-aware | `rope_theta = 500_000 × extend_factor^(d/(d-2))` with `d=128` | slightly better quality at 4-8× |

For baien (`rope_theta = 500_000`, `head_dim = 128`):

| extend_factor | linear `rope_theta` | NTK-aware `rope_theta` (head_dim=128) | target ctx |
|---|---|---|---|
| 2 | 1,000,000 | 1,011,164 | 8k |
| 4 | 2,000,000 | **2,044,497** | 16k |
| 8 | 4,000,000 | 4,134,231 | 32k |
| 16 | 8,000,000 | 8,358,898 | 64k |

Formula: `theta' = 500_000 × extend_factor^(128 / (128-2))`. Verified in
`70-tools/baien-distill/scripts/rope_extend_probe.py:ntk_theta()`.

**Stage 1 smoke** runs both `linear×4` and `NTK×4` against:
1. The existing `microbench.py` 15-prompt suite at 4k (sanity — no regression)
2. A new `microbench_long.py` with 5 verifiable long-context prompts
   (needle-in-haystack @ 6k / 12k, long-doc 3-line summary, ordered-list
   recall, multi-passage compare).

**Stage 1 gate to promote to Stage 2**:
- 4k microbench pass-rate Δ ≤ -5 pp (≤ 0.05 absolute drop)
- 16k needle-in-haystack recall ≥ 0.40 (random ≈ 0.10, dense readable goal 0.80+)
- ppl on a held-out 4k validation set inflation ≤ +5%

Failure mode prediction: at 4× extension, BitNet's ternary weights
may quantize away the fine positional distinctions that RoPE relies
on. If Stage 1 gate fails, we skip to **YaRN with light LoRA** in
Stage 2 (training-aware path).

# Stage 2 — YaRN + LoRA fine-tune

[YaRN (Peng et al. 2023)](https://arxiv.org/abs/2309.00071) extends
RoPE with non-uniform interpolation that preserves high-frequency
detail. transformers ≥4.55 supports it natively via:

```python
config.rope_scaling = {
    "type": "yarn",
    "factor": 4.0,
    "original_max_position_embeddings": 4096,
}
```

For baien we couple YaRN with a **light LoRA fine-tune** (r=8, ~500
step, target attention modules only) on a long-context calibration
mix (PG-19 long-passages + a multilingual subset of OpenAssistant).

Cost: ~4-8 h on EVO-X2 ROCm (ComfyUI python_embeded env, per
ADR-2605231300 §5).

Gate to Stage 3:
- 64k needle-in-haystack recall ≥ 0.50
- microbench pass-rate Δ ≤ -3 pp
- LoRA size ≤ 10 MB (so the adapter is shippable to browser/edge)

# Stage 3 — LongRoPE + continual pretraining

[LongRoPE (Microsoft, 2024)](https://arxiv.org/abs/2402.13753) uses
evolutionary search to find a non-uniform RoPE re-scaling that lets a
model extrapolate to **256× its trained length** with ~1k step
continual pretraining.

Direct alignment with baien (same lab; published as a generic
technique not BitNet-specific). Reference implementation:
https://github.com/microsoft/LongRoPE.

Cost: ~24-48 h continual pretraining on EVO-X2 ROCm, with a
long-context corpus subset (~10 GB, e.g. ProofPile-2 long, Together
RedPajama-Long-DC-1T-Sample, or a curated mix).

Gate to commit:
- 128k needle-in-haystack recall ≥ 0.60
- 4k microbench retention ≥ 95% of pre-extension
- Council Lv6+ approval for the cost (per ADR-2605192415 §6
  governance, since this consumes >24h of fleet GPU)

Stage 3 requires its own **amended ADR** (signed off as part of the
continual-pretrain plan) before kickoff.

# BitNet-specific caveats

1. **Ternary weight + extended RoPE interaction is unverified.** All
   published RoPE extension methods (linear, NTK, YaRN, LongRoPE) were
   evaluated against bf16/fp16 trunks. The W1.58 BitNet quantization
   may discard fine positional distinctions that RoPE scaling relies
   on. The Stage 1 smoke is precisely the experiment that answers
   this.
2. **bitnet.cpp / WebGPU runtime support.** Stage 1 is config-only and
   inherits whatever ctx limit the runtime kernel implements. Some
   runtimes hard-code `max_position_embeddings` in their KV cache
   allocator — verify per runtime before relying on the new ctx.
3. **Squared-ReLU + SubLN stability.** These choices are unusual; we
   should expect non-standard interactions at extended ctx. The Stage 2
   LoRA gives a path to repair these.
4. **Distill loop interaction.** baien-distill (ADR-2605231300) is
   currently configured for the 4k window. After Stage 2 lands, the
   distill loop should use the extended adapter for its SFT runs
   (longer reasoning traces from Opus distillation become usable).

# Pipeline interactions

| Component | Effect of context extension |
|---|---|
| `baien-microbench` (15 prompts ≤ 256 tok) | No change |
| `baien-distill` (ADR-2605231300, SFT max_seq=1024) | Stage 2 unlocks usable training on longer Opus-distill rows (the dataset has rows up to 32k tok — currently truncated) |
| `baien-graft-pipeline` (ADR-2605202115 — 3D multi-view caption) | Stage 1 unlocks 16k caption batches; Stage 2 unlocks full 3D-asset chains |
| `baien-MX` (ADR-2605101000 — modality grafts) | Stage 2+ required for multi-modality long sequences (4k splits modality budgets too thin) |
| `kotodama-host-sdk` `MODEL_REGISTRY` | `contextWindow` is updated per-stage when an extended variant is committed via `gen-distilled-entries.mjs` |

# Out of scope

- **Stage 4 architecture surgery** (sliding window / StreamingLLM /
  state-space hybrid). These are not RoPE extensions — they change the
  attention pattern. Deferred to a future ADR if Stages 1-3 plateau.
- **Multi-modal context extension.** baien-MX context is governed by
  ADR-2605101000; this ADR only treats text-modality positional
  encoding.
- **bitnet.cpp / WebGPU kernel patching** to admit longer KV caches.
  If runtime-side limits block adoption, address in a runtime-specific
  ADR — not here.

# Acceptance criteria (for `proposed → accepted`)

1. `70-tools/baien-distill/scripts/rope_extend_probe.py` exists and
   runs the Stage 1 smoke end-to-end against baien.
2. `70-tools/scripts/bench/baien-microbench/microbench_long.py` exists
   with at least 5 verifiable long-context prompts.
3. `90-docs/baien/context-extend-snapshot-260523.md` records the
   Stage 1 result (Δ vs 4k baseline) and a promote/reject/hold call.
4. If promoted, `MODEL_REGISTRY` gains an entry for the extended
   variant via the existing manifest → codegen pipeline
   (ADR-2605231300 §commit_node).

# References

- ADR-2605092350 baien design (1.58-bit BitNet + edge runtimes)
- ADR-2605231300 baien-distill ReAct loop (SFT pipeline that will
  benefit from the extension)
- ADR-2605202345 EVO-X2 ROCm pod (execution host)
- Microsoft `microsoft/bitnet-b1.58-2B-4T-bf16` model card and `config.json`
- LongRoPE: https://arxiv.org/abs/2402.13753 / https://github.com/microsoft/LongRoPE
- YaRN: https://arxiv.org/abs/2309.00071
- NTK-aware RoPE scaling: https://www.reddit.com/r/LocalLLaMA/comments/14lz7j5
- StreamingLLM (attention sinks): https://arxiv.org/abs/2309.17453
