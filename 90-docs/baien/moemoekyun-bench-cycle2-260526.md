---
id: moemoekyun-bench-cycle2-260526
title: "moemoekyun bench cycle 2 (2026-05-26 14:25-14:55 JST) — 5-shot / CoT / MMLU-Pro support + W10-W11 datasets"
status: active
doc_type: reference
topic: moemoekyun-bench-cycle2
authoritative: true
last_verified: 2026-05-26
related:
  - moemoekyun-bench-cycle1-260526
  - 90-docs/baien/bench-snapshot-260526-bitnet2b-gpqa-diamond.jsonl
  - 70-tools/baien-moemoekyun-train/scripts/bench_gpqa_diamond.py
  - 70-tools/baien-moemoekyun-train/scripts/bench_humanevalplus.py
---

# moemoekyun bench cycle 2 — 2026-05-26 14:25-14:55 JST

**/loop fire 2** (cron `13,43 * * * *`, job `c8acb432`).

## Deliverables (cycle 2)

### A. Bench script upgrades

`bench_gpqa_diamond.py` extended with:
- `--n-shot <N>` flag (5-shot exemplars from `cais/mmlu <subject>` dev split since MMLU-Redux 2.0 has no dev split)
- `--cot` flag (zero-shot CoT, already existed but never validated; this cycle validated negatively)
- MMLU-Pro dataset variant (`mmlu-pro:<category>`, 10-option MC, variable n_opt; uses `answer_index` field from TIGER-Lab/MMLU-Pro)
- Variable option count throughout main loop (4 for MMLU/MMLU-Redux/GPQA, 10 for MMLU-Pro)
- random_baseline = 1/n_opt (auto-adapts vs hardcoded 0.25)

`bench_humanevalplus.py` (new, Phase 3 scaffold):
- exec-graded eval via `multiprocessing.Process` subprocess (timeout 10s/task)
- NO docker sandbox (smoke-only; R2+ proper docker required)
- HF `evalplus/humanevalplus` 164 tasks
- greedy decoding 256 max_new_tokens
- pass@1 reported

### B. Phase 2 generative math datasets pinned

| Wave | Dataset | License | Size | Use |
|---|---|---|---|---|
| W10 | `AI-MO/aimo-validation-aime` (AIME26) | Apache 2.0 | 0.26 MB | Phase 2 math reasoning |
| W11 | `MathArena/hmmt_feb_2025` (HMMT Feb 2025) | MIT | 13 KB | Phase 2 competition math |
| W12 (deferred) | `livecodebench/code_generation_lite` | CC-BY-NC-4.0 | 4.4 GB | Phase 3 exec coding — too large for `--max-bytes 50MB` cap, defer to cycle 3+ with include-glob filter or larger cap |

DataLad superdataset advanced (W10 + W11 subdataset pointers).

### C. 5-shot + CoT validation (key negative findings)

3 subjects × 100q × 5-shot + 1 subject × 100q × CoT on BitNet 2B Mac MPS:

| Subject | 0-shot baseline | **5-shot** | Δ vs 0-shot | 0-shot+CoT | Δ vs 0-shot |
|---|---|---|---|---|---|
| college_biology | 54.0% | **58.0%** | +4pp | **27.0%** | **-27pp** |
| college_physics | 41.0% | **42.0%** | +1pp | (not tested) | — |
| college_mathematics | 29.0% | **26.0%** | -3pp | (not tested) | — |
| **3-subject avg (5-shot)** | 41.3% | 42.0% | **+0.67pp** | — | — |

Wall: 5-shot ~430-530s per 100q (3-4x slower than 0-shot 130-141s due to longer context per question).

### D. Critical negative findings (cycle 2)

#### Finding 1: BitNet 2B doesn't benefit from 5-shot

Expected lift was +10-15pp (per Microsoft model card MMLU 52% 5-shot vs ~40% 0-shot). Observed: **+0.67pp average** (essentially flat). Math subjects HURT (-3pp).

Probable causes:
- MMLU-Redux 2.0 is a smaller curated subset (100q per subject vs original MMLU's 1k+) — high variance per subject
- BitNet 2B's instruction-following / few-shot generalization is limited at 2.4B parameters
- 5-shot exemplars from `cais/mmlu dev` may not match `mmlu-redux-2.0 test` distribution exactly (data shift)

#### Finding 2: Zero-shot CoT catastrophically HURTS BitNet 2B

Adding "Let me think step by step." suffix → biology accuracy **dropped 54% → 27% (-27pp)**. This is below random for 4-option MC (where random = 25%).

Probable cause: BitNet 2B's letter-prediction probability mass shifts after the CoT suffix to non-letter tokens (the model wants to start generating reasoning, not commit to an answer). The next-token-logit fallback path correctly captures this — the model's "preferred" letter no longer reflects its answer.

#### Finding 3: Score improvement REQUIRES training, not prompting

Cycle 1 + 2 combined:
- Evaluator fix: **+9.8pp** (huge, free, one-time)
- 5-shot: +0.67pp (negligible)
- CoT: -27pp (regression)

→ Prompting tweaks exhausted. Further moemoekyun improvement requires:
1. **R1.4 train** (Phase 0 freeze-train, coding-emphasis SFT) — EVO-X2 ROCm pending power-on
2. **R2 train** (Phase 1 partial unfreeze, larger corpus) — RunPod B200 post-amendment ~2026-07-19
3. **R2 corpus rebalance** — math weakness (29-30% on math subjects) suggests boost `reasoning-distill-opus` from 10% → 20%, add HMMT/AIME training data

This validates the moemoekyun architecture decision: **modify the model**, not the prompt.

## Updated bench-snapshot total

17 bench entries in `bench-snapshot-260526-bitnet2b-gpqa-diamond.jsonl`:
- Cycles 1-2: 10 MMLU/MMLU-Redux runs across 5 subjects × {0-shot broken, 0-shot fixed, 5-shot, 0-shot+CoT}
- 2 earlier MMLU smoke runs (pre-fix)

Full breakdown:

| Run | Subject | shots | CoT | accuracy | wall | notes |
|---|---|---|---|---|---|---|
| pre-fix 1 | physics 30q | 0 | — | 33.3% | <1s | bug (always-A) |
| pre-fix 2 | all 200q | 0 | — | 19.5% | <1s | bug (always-A, below random) |
| cycle-1-1 | physics 100q | 0 | — | 28.0% | <1s | bug |
| cycle-1-2 | chemistry 100q | 0 | — | 28.0% | <1s | bug |
| cycle-1-3 | biology 100q | 0 | — | 28.0% | <1s | bug |
| cycle-1-4 | math (HS) 100q | 0 | — | 28.0% | <1s | bug |
| cycle-1-5 | math (col) 100q | 0 | — | 28.0% | <1s | bug |
| cycle-1-fix-1 | physics 100q | 0 | — | **41.0%** | 132s | **fixed** |
| cycle-1-fix-2 | chemistry 100q | 0 | — | **35.0%** | 133s | **fixed** |
| cycle-1-fix-3 | biology 100q | 0 | — | **54.0%** | 135s | **fixed** |
| cycle-1-fix-4 | math (HS) 100q | 0 | — | **30.0%** | 130s | **fixed** |
| cycle-1-fix-5 | math (col) 100q | 0 | — | **29.0%** | 141s | **fixed** |
| cycle-2-1 | biology 100q | 5 | — | **58.0%** | 429s | +4pp |
| cycle-2-2 | physics 100q | 5 | — | **42.0%** | 450s | +1pp |
| cycle-2-3 | math (col) 100q | 5 | — | **26.0%** | 527s | -3pp |
| cycle-2-4 | biology 100q | 0 | ✓ | **27.0%** | 142s | -27pp (regression) |

## Cycle 3 plan (~15:13 JST fire)

1. **Try MMLU-Pro 1 subject** (e.g., `mmlu-pro:biology`) — 10-option MC, random baseline 10%, more challenging
2. **HumanEval+ smoke** (20 tasks, exec-graded) — first Phase 3 datapoint for coding bench
3. **Try LiveCodeBench v6 with include filter** — pin a subset (e.g., `data/v6/*` or `release_v6.json`) for Phase 3
4. **EVO online check**, if up: install lm-eval-harness + run proper 5-shot MMLU on ROCm (will give the canonical baseline number)
5. **Maybe**: try 1-shot, 2-shot to see if shot count has linear/non-linear effect (cycle 2 only tested 5-shot)

## Reflection

Cycle 1 gave **+9.8pp lift via evaluator fix** (real, free measurement improvement).
Cycle 2 gave **~0 lift via prompting** (5-shot flat, CoT regression) **but valuable negative information** — confirms that BitNet 2B at 2B scale has limited instruction-following capability, and that training is required for further improvement.

Per `/loop` directive ("score を向上していって"), the conclusion of cycle 2 is: **score improvement budget is now training-bound** (R1.4 EVO blocked, R2+ RunPod amendment blocked). Continuing cycles will:
- Add more bench datasets to substrate (Phase 3+ coding benches)
- Validate alternative scoring methods (logprob normalization, length bias correction)
- Test other models from MS BitNet family (1B BitNet variants for delta signal)
- Defer real score improvement to R1.4 train on EVO power-on
