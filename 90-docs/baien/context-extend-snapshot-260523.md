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

## Results (2026-05-24, EVO-X2 CPU bf16)

Run executed 2026-05-23T11:20 → 12:18 UTC on EVO-X2 (Ryzen AI Max+ 395, CPU
bf16, transformers 5.9.0). Raw rows mirrored to
`90-docs/baien/context-extend-260524/results_long_{A_baseline,B_linear_x4,C_ntk_x4}.jsonl`
+ `rope_summary.json`.

### Pass matrix (5 prompts × 3 configs)

| Prompt | Input tok | A_baseline | B_linear×4 | C_ntk×4 | Failure mode (when FAIL) |
|---|---|---|---|---|---|
| `ctx_6k_needle` | 4,354 | PASS | PASS | PASS | — |
| `ctx_8k_summary` | 5,837 | FAIL | FAIL | FAIL | want 3 lines got 1 |
| `ctx_10k_roster` | 7,503 | FAIL | FAIL | FAIL | missing 'gad' got 'Kuiper' |
| `ctx_12k_needle` | 8,965 | FAIL | FAIL | FAIL | missing date got '1789' |
| `ctx_14k_compare` | 10,113 | PASS | PASS | PASS | — |
| **total** | | **2/5 = 40%** | **2/5 = 40%** | **2/5 = 40%** | identical across configs |

Per-category (identical A = B = C):

| Category | Pass rate |
|---|---|
| compare | 1/1 = 100% |
| needle | 1/2 = 50% |
| recall | 0/1 = 0% |
| summary | 0/1 = 0% |

### Configs (from `rope_summary.json`)

| Label | rope_theta | max_pos |
|---|---|---|
| A_baseline | (default 500,000) | (default 4,096) |
| B_linear×4 | 2,000,000 | 16,384 |
| C_ntk×4 | 2,044,497.12 (= 500,000 × 4^(128/126)) | 16,384 |

### Wall times (EVO-X2 CPU bf16)

| Config | Wall |
|---|---|
| A_baseline | ~25 min |
| B_linear×4 | ~30 min |
| C_ntk×4 | ~35 min |
| total | ~90 min |

### Verdict

Training-free RoPE scaling shows **zero measurable improvement** at 4×
extension. Linear and NTK both produce the bit-identical 2/5 = 40% pass
rate as baseline. The three failures are not range failures:

- `ctx_10k_roster` returns "Kuiper" instead of "gad" — wrong **content
  selection** out of the context window, not a context-truncation symptom
- `ctx_8k_summary` returns 1 line of paragraph-stitching when 3 distinct
  bullets were requested — **instruction-following at length**, not range
- `ctx_12k_needle` returns the embedded year "1789" instead of the target
  date — **attention quality on long context**, not range

These read as long-context **attention quality** problems, not long-context
**range** problems. Extending RoPE without retraining cannot fix any of them
— the trunk's internal pretrained behaviour at >4k is unchanged.

**Recommendation:** do NOT promote to Stage 2 YaRN + LoRA on this evidence
alone. Instead:

1. Expand prompt set 5 → 20+ to get a real statistical comparison (current
   `n=5` cannot distinguish identical pass rates from noise)
2. Add a 4k re-run with B / C configurations as a short-context regression
   check — the missing gate criterion per ADR-2605231600 §gate point 3
3. Investigate `<image>` / `<audio>` / `<video>` placeholder token
   interaction with long-context attention (multi-modal grafts may
   compound the failure mode)
4. Then decide between (a) Stage 2 YaRN + LoRA, (b) accept ~6k effective
   ctx as the baien edge ceiling and pin the invariant, or (c) defer the
   whole question until bitnet.cpp lands and re-measure on the deployed
   runtime (KV cache allocator may dominate)

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
