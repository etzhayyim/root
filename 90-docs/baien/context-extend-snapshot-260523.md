---
id: doc-260523-baien-context-extend-snapshot
title: "Baien context extension Stage 1 snapshot 2026-05-23"
status: active
doc_type: snapshot
topic: baien-context-extension
authoritative: false
last_verified: 2026-05-23
related:
  - adr-2605231600-baien-context-extension
  - 70-tools/baien-distill/scripts/rope_extend_probe.py
  - 70-tools/scripts/bench/baien-microbench/microbench_long.py
---

# Stage 1 — rope_theta scaling smoke

Per ADR-2605231600 §Stage 1. Three configurations probed against
baien (`microsoft/bitnet-b1.58-2B-4T-bf16`) on EVO-X2:

| Label | rope_theta | max_pos | rope_scaling | meaning |
|---|---|---|---|---|
| A_baseline | 500,000 (default) | 4,096 | none | upstream sanity baseline |
| B_linear_x4 | 2,000,000 | 16,384 | none | linear theta scaling, 4× ctx |
| C_ntk_x4 | 2,044,497 | 16,384 | none | NTK-aware (head_dim=128), 4× ctx |

## How to run

```bash
# from the etzhayyim repo root, on a host that can load baien
# (EVO-X2 ComfyUI python_embeded for ROCm; system Python 3.10 for CPU)
e7m bench rope-extend
# or only a subset:
e7m bench rope-extend --only B_linear_x4,C_ntk_x4
```

Each config writes to
`90-docs/baien/context-extend-260523/results_long_<label>.jsonl` plus
a side-by-side pass-rate matrix to stdout.

## Results

<!-- TO BE FILLED after first run -->

```
(awaiting first run — kick off via `e7m bench rope-extend`)
```

## Stage 1 gate (per ADR-2605231600)

Promote to Stage 2 (YaRN + LoRA) only if all three hold:

1. 4k microbench Δ ≤ -5 pp vs the existing baseline
   (frontier-bench-snapshot-260523.md §D, 8/15 strict / 73% lenient).
2. 16k needle prompts in B / C show recall ≥ 0.40
   (the two needle prompts in microbench_long.py at 6k + 12k).
3. ppl on a held-out 4k validation set inflation ≤ +5%
   (separate run — out of scope of this probe; planned as a follow-up).

If gate fails: stay at 4k, archive this snapshot, open a new ADR
amendment with the observed failure mode + a proposal for Stage 2-first
(skip rope_theta scaling, jump straight to YaRN + LoRA).

## Caveats

- Stage 1 is **inference-only**; quality at extended ctx depends
  entirely on baien's pretrained extrapolation behavior.
- BitNet's W1.58 quantization × extended RoPE has not been published
  in any peer-reviewed work as of 2026-05-23. The result of this probe
  is the first datapoint we have on that interaction.
- Token estimates in `microbench_long.py` are approximate (~4 chars
  per token for English filler). Actual input token counts are
  recorded per row.
- Runtimes other than HuggingFace transformers (bitnet.cpp, llama.cpp,
  WebGPU) may hard-code max_position_embeddings in their KV cache
  allocator — verify per runtime before relying on the extension at
  serving time.
