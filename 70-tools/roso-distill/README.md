# roso-distill

Bonsai-pattern post-train 1-bit quantization + distill recovery for
baien siblings. Per **ADR-2605242000**.

Sibling to `70-tools/baien-distill/` (LangGraph SFT loop on bf16 master)
and `70-tools/baien-mx-train/` (Move 1 multimodal projector train).
This module handles the **trunk-level** transformation from a strong
bf16 base (Zamba2-7B / Qwen3-8B / DeepSeek-R1-Distill-Qwen-7B / …)
into a 1-bit, edge-fit baien sibling.

## Pipeline

```
pull_base       → snapshot_download HF id, verify license is permissive
   ↓
quantize        → Bonsai-style W1 per-layer ternary projection
   ↓                (current impl = naive sign projection, TODO: port whitepaper algorithm)
recovery (B)    → distill SFT on Opus / DeepSeek-R1 / Phi-4 corpora via baien-distill
   ↓                (Phase A skips this step)
attestation     → calculated edge invariant check (ADR-2605241900 ceilings)
   ↓
commit          → append entry to 90-docs/baien/roso-models.jsonl
                  + codegen → llm-model-registry-roso.ts
                  + reviewer flips `available: true`
```

## Quickstart

```bash
cd 70-tools/roso-distill
uv venv --python 3.10 .venv
. .venv/bin/activate
pip install -e .[dev]

# dry-run the full pipeline against Zamba2-1.2B (no weights downloaded)
python -m roso_distill \
    --base-model Zyphra/Zamba2-1.2B \
    --phase A --dry-run

# Phase A real quantization (~10-30 min, needs base weights + torch)
python -m roso_distill \
    --base-model Zyphra/Zamba2-1.2B \
    --phase A

# Phase B = Phase A + distill recovery (~1-3 days on EVO-X2 ROCm)
python -m roso_distill \
    --base-model Zyphra/Zamba2-7B \
    --phase B \
    --recovery-datasets \
        lordx64/reasoning-distill-opus-4-7-max-sft \
        lordx64/Opus-4.7-Thinking-Max-Distill-25k \
    --recovery-n-per-dataset 10000

# via the etzhayyim CLI
e7m bench bonsai --base Zyphra/Zamba2-1.2B --phase A --dry-run
e7m bench bonsai --base Zyphra/Zamba2-7B --phase B
```

## Candidate base models (edge-invariant verified per row in ADR-2605242000)

| HF id | License | FP16 | 1-bit | edge fit @4k | edge fit @16k | role |
|---|---|---|---|---|---|---|
| `Zyphra/Zamba2-1.2B` | Apache-2.0 | 2.4 GB | 170 MB | ✓ | ✓ at 128k | mass-deploy |
| `Zyphra/Zamba2-2.7B` | Apache-2.0 | 5.4 GB | 380 MB | ✓ | ✓ at 128k | long-context |
| `Zyphra/Zamba2-7B` | Apache-2.0 | 14 GB | 1.0 GB | ✓ | ✓ at 128k | **quality + long-context ★** |
| `Qwen/Qwen3-8B` | Apache-2.0 | 16 GB | 1.15 GB | ✓ | ✗ | quality @4k ★ |
| `Qwen/Qwen2.5-Coder-7B` | Apache-2.0 | 14 GB | 1.0 GB | ✓ | ✗ | code specialist |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | MIT | 14 GB | 1.0 GB | ✓ | ✗ | reasoning specialist |
| `mistralai/Mistral-7B-v0.3` | Apache-2.0 | 14 GB | 1.0 GB | ✓ | ✗ | general baseline |

Non-permissive bases (Llama-3.x Community License) NOT auto-permitted —
require explicit reviewer override at `commit` (ADR-2605242000 §License
chain).

## Frontier MoE as *teachers*, never as *base*

DeepSeek-V3 / -Pro-V4, MiniMax-M2, Moonshot Kimi K2, Qwen3-Max — all
exceed the 1.6 GB packed-weights ceiling (ADR-2605241900) at any
quantization level. Use them only as **distillation teachers** via
their published Apache-2.0 / MIT distill datasets:

- `lordx64/reasoning-distill-opus-4-7-max-sft` (Opus 4.7 traces, Apache-2.0)
- `lordx64/Opus-4.7-Thinking-Max-Distill-25k` (Opus thinking, 25k, Apache-2.0)
- `open-r1/OpenR1-Math-220k` (R1 math, Apache-2.0)
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` (already-distilled model — usable as base too)
- `nvidia/HelpSteer3` (mixed teacher, CC-BY-4.0 — review per Charter Rider §2 at commit)

## Status (Phase 1, this PR)

- ✅ skeleton (state / pull / quantize / recovery / attestation / commit / `__main__`)
- ✅ end-to-end **dry-run** path (no weights, no GPU, walks all stages)
- ⏳ real quantize: current impl = naive sign projection — replace
  with whitepaper Algorithm 1 (per-layer optimization with calibration
  inputs) before publishing a `roso-*` sibling.
- ⏳ recovery (Phase B): blocked on a small patch to `baien-distill`
  to allow `BASE_MODEL_ID` override pointing at quantized weights.
- ⏳ `gen-roso-entries.mjs` codegen (mirror of `gen-distilled-entries.mjs`).
- ⏳ `e7m bench bonsai` wiring in `70-tools/etzhayyim-cli/bench.go`.

## License

Apache 2.0 + etzhayyim Charter Compliance Rider v2.0.

Output sibling weights inherit:
- base model license (must be permissive — see §Candidate base models)
- distillation dataset licenses (see ADR-2605242000 §License inheritance chain)

The codegen + reviewer-gate process (`commit.py` → `gen-roso-entries.mjs`
→ human flip of `available: true`) protects against accidental
publication of non-Apache-clean derivatives.
