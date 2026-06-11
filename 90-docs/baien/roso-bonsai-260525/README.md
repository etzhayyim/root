# roso-bonsai 1-bit quantization session evidence — 2026-05-25

Raw `minibench.jsonl` artifacts from the 5-wall empirical loop (see
`90-docs/adr/2605242000-roso-pattern-frontier-distill.md`).

15 verifiable prompts × 5 categories (IFEval / MMLU / Reasoning /
Multilingual / General). One row per prompt with `id`, `ok`, `reason`,
`response`, `elapsed_sec`.

| file | base | method | exact_match |
|---|---|---|---|
| `35b_bonsai_c_minibench.jsonl` | Qwen/Qwen3.6-35B-A3B | Phase C OS only | 0/15 |
| `35b_bonsai_d_minibench.jsonl` | Qwen/Qwen3.6-35B-A3B | Phase C + D (GPTQ-CD) | 0/15 |
| `1.7b_bonsai_d_minibench.jsonl` | Qwen/Qwen3-1.7B-Base | Phase C + D (GPTQ-CD) | 0/15 |
| `1.7b_kd200_minibench.jsonl` | Qwen/Qwen3-1.7B-Base | + KD 200 steps (lr 1e-4) | 0/15 |
| `1.7b_kd1200_minibench.jsonl` | Qwen/Qwen3-1.7B-Base | + KD 1200 steps (lr 5e-4) | 0/15 |
| `1.7b_fp16_baseline.jsonl` | Qwen/Qwen3-1.7B-Base | fp16 (un-quantized ceiling) | **4/15** |

The fp16 baseline (4/15 = 26.7%) is the ceiling against which 1-bit
recovery is measured. None of the 5 walls escape exact_match=0 within
session-budget compute. Per the ADR, Bonsai-paper-equivalent recovery
requires 40-160× the per-step compute we could deliver on EVO 1 node.
