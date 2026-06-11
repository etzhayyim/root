---
id: moemoekyun-bench-cycle3-260526
title: "moemoekyun bench cycle 3 (2026-05-26 15:10-15:40 JST) — MMLU-Pro 10-option + HumanEval+ smoke + W12 LiveCodeBench v6"
status: active
doc_type: reference
topic: moemoekyun-bench-cycle3
authoritative: true
last_verified: 2026-05-26
related:
  - moemoekyun-bench-cycle1-260526
  - moemoekyun-bench-cycle2-260526
  - 90-docs/baien/bench-snapshot-260526-bitnet2b-humanevalplus.jsonl
---

# moemoekyun bench cycle 3 — 2026-05-26 15:10-15:40 JST

**/loop fire 3** (cron `13,43 * * * *`, job `c8acb432`).

## Deliverables

### A. MMLU-Pro biology 50q (10-option MC) — STRONG baseline

| Bench | n_opt | Random | BitNet 2B | Δ vs random |
|---|---|---|---|---|
| MMLU-Pro biology (50q) | 10 | 10% | **52.0%** | **+42.0pp** |

vs MMLU-Redux biology (4-option): 54.0% → similar absolute accuracy, but
MMLU-Pro's 10-option format makes the +42pp delta much more dramatic.

Wall: 288s = 4.8 min (10.4 q/min on Mac MPS bf16 — slower than 4-option
because each question requires 10 forward passes for letter scoring).

**Reference comparison** (user's table): Qwen3.5-27B MMLU-Pro = 86.1% (overall).
BitNet 2B biology = 52% → ~34pp gap, but biology-specific gap may be smaller
(domain-rich knowledge).

### B. HumanEval+ 10 task exec-graded smoke — root-cause finding

| Bench | Tasks | BitNet 2B pass@1 | Wall |
|---|---|---|---|
| HumanEval+ 10 task (raw 0-shot, max=200 tokens) | 10 | **0/10 = 0.0%** | 393s |

**Root cause** (per_task JSONL inspection):
```
HumanEval/0: SyntaxError: invalid syntax at line 21 — "```"
HumanEval/1: SyntaxError: invalid syntax at line 27 — "```"
HumanEval/2: SyntaxError: invalid syntax at line 18 — "```"
...
```

All 10 failures = **Python SyntaxError on markdown code fence ` ``` `**.

BitNet 2B generates instruction-tuned style output (markdown-wrapped code
blocks), but my smoke evaluator passes raw `prompt + generation` to Python
exec. The trailing ` ``` ` markdown fence causes SyntaxError before any
test runs.

**Expected real pass@1 (after fence strip)**: BitNet 2B-4T model card reports
HumanEval ~37% (original, not +). HumanEval+ should be ~25-30% (harder tests).
So with proper markdown extraction, BitNet 2B baseline should be ~3/10 to 4/10
on this 10-task subset.

**Fix needed (cycle 4)**: implement `extract_python_code()` (helper already
defined in bench_humanevalplus.py but never called) to strip markdown fences
+ keep only function body. Then re-run.

### C. W12 LiveCodeBench v6 pinned (Phase 3 coding bench)

| Wave | Path | Size | License | Use |
|---|---|---|---|---|
| W12 | `livecodebench/code_generation_lite@main` `test6.jsonl` (filtered) | 134.3 MB | CC-BY-NC-4.0 | Phase 3 coding (LCB v6 release) |

Earlier `--include "*release_v6*"` matched 0 files; `--include "test6.jsonl"`
matched correctly (LCB stores releases as test{N}.jsonl, not release_v{N}).

Total Phase 1-3 bench corpus pinned: **44.7 MB + 134.3 MB = 179.0 MB** across
12 datasets (5 train + 7 bench).

### D. EVO-X2 status: still offline

Phase 1 lm-eval-harness 5-shot baseline blocked on EVO power-on.

## Cycle 3 score lift attribution

| Source | Lift |
|---|---|
| MMLU-Pro 10-option scoring | new datapoint (+42pp vs 10%-random, validates BitNet biology knowledge) |
| HumanEval+ smoke | 0% baseline (markdown fence bug, fixable) — informative null |
| Prompting/scoring tweaks (continued from cycle 2) | exhausted |

→ True score improvement still pending **training (R1.4)** + **markdown-strip fix** (next cycle).

## Cycle 4 plan (~15:43 JST fire)

1. **Fix bench_humanevalplus.py** with proper markdown extraction → re-run 10-task smoke
2. **EVO online check** + lm-eval-harness install if up
3. **Try MMLU-Pro mixed subjects** (e.g., `mmlu-pro:all` sample) — broader coverage
4. **Pin AIME26 actual dataset** (already pinned W10) → write AIME-style generator bench script
5. **Multi-cycle synthesis doc** consolidating cycles 1-3 findings into final
   "BitNet 2B baseline established" snapshot for ADR-2605262100 §5.4 commit_gate
   baseline reference
