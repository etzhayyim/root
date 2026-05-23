---
id: doc-260524-distill-iter00-snapshot
title: "Baien distill ReAct iter-00 snapshot 2026-05-24 (abort decision)"
status: active
doc_type: snapshot
topic: baien-distill
authoritative: false
last_verified: 2026-05-24
related:
  - adr-2605231300-baien-distill-react-loop
  - 70-tools/baien-distill/
  - 90-docs/baien/results-260523.jsonl
---

# Distill ReAct iter-00 snapshot — 2026-05-24 (abort decision)

First end-to-end execution of the `e7m bench distill` ReAct loop after the
trl 1.4.0 API-drift fixes landed. Result: pipeline ✓ end-to-end, abort gate
correctly fired on Δ = −0.380. Adapter discarded, score_history retained.

## Setup

- `e7m bench distill --quick --source hf --max-iter 1`
- Seed analysis: `90-docs/baien/results-260523.jsonl` (15-prompt microbench
  baseline: Multilingual 0%, Reasoning 0%, IFEval 60%, lenient pass 73%)
- trl 1.4.0 API drift fixes applied (see § below)

## ReAct trace

| Node | Outcome |
|---|---|
| `analyze` | Weak categories: Multilingual 0%, Reasoning 0%, IFEval 60% |
| `fetch_dataset` | OASST +50 + Opus distill +50 = 100 raw; IFEval gated skip |
| `validate` | 12/100 kept = 12% (oasst JSON parse failure ×44 dominant drop) |
| `train` | LoRA 7,987,200 params (0.33% of trunk); 12 samples × 1 epoch × grad_accum 4 = 3 SGD steps; 363s wall; train_loss 1.392; token_acc 67%; entropy 0.953 |
| `evaluate` | `e7m bench micro` on merged adapter — avg Δ = **−0.380** |
| `commit_node` | **abort** — adapter discarded, iter-00 dir removed, score_history committed |

## score_history (committed)

```json
{
  "iter": 0,
  "ts": "2026-05-24T03:14:00Z",
  "n_examples": 12,
  "sgd_steps": 3,
  "train_loss": 1.392,
  "token_acc": 0.67,
  "entropy": 0.953,
  "eval_delta": -0.380,
  "decision": "abort",
  "reason": "Δ below 0 — adapter degrades baseline microbench"
}
```

## Interpretation

Pipeline ✓. ReAct loop ✓. Charter Rider scanner ✓. Abort gate ✓.

But: 12 examples + 3 SGD steps cannot teach a 2.4B trunk anything. The
Δ = −0.38 = real degradation, not noise — the smoke tier pushes the LoRA
into a region that disrupts trunk output coherence (same pattern as
Move 1 Phase A on the projector head, see `move1-phaseA-260524.md`).

The honest signal is: **smoke runs are pipeline regressions, not training
runs**. Reading "did the model learn?" off `--quick` is a category error.
The gate correctly rejected this run.

## trl 1.4.0 fixes applied (this run)

The previous train.py was written against trl ≤1.2 and broke on the
1.4.0 wheel installed during the Phase A bootstrap. Three minimal edits:

1. Drop `max_seq_length=1024` from `SFTConfig` — removed from the 1.4.0
   `SFTConfig` API surface; `SFTConfig.__init__` raises `TypeError`
2. Add `use_cpu = not torch.cuda.is_available()` to `SFTConfig` — the bf16
   validator in `transformers` 5.9.0 raises `"Your setup doesn't support
   bf16/gpu. You need to assign use_cpu if you want to train the model on
   CPU."` without it
3. Migrate dataset schema from `{text}` to `{prompt, completion}` —
   `SFTTrainer._prepare_dataset` in 1.4.0 hard-codes the lookup for
   `example["prompt"]` + `example["completion"]`; passing
   `dataset_text_field="text"` no longer overrides this (also dropped
   from `SFTConfig`)

See `70-tools/baien-distill/src/baien_distill/nodes/train.py` for the
landed diff.

## Operator setup gaps (fresh Windows EVO-X2 bring-up)

These bit during this run; book them so the next operator does not repeat:

- `pip install sentencepiece protobuf` — required by SiglipTokenizer +
  BitNet tokenizer (neither is a hard dep of `transformers[torch]`)
- `python -X utf8 -m baien_distill ...` (or set `PYTHONIOENCODING=utf-8`)
  — Windows cp1252 fallback crashes on JSON containing non-ASCII
  (oasst entries are mostly multilingual)
- `scp microbench.py` to the path the wrapper expects — the bench harness
  hard-codes `70-tools/scripts/bench/baien-microbench/microbench.py`
  relative to repo root, and `e7m` discovers repo root via `git rev-parse`
- Seed the bench-dir with a prior `results-*.jsonl` for `analyze` to find
  weak categories; without it the node falls through to a stub that
  returns "no weak categories" and skips fetch

## Next runs

| Mode | n_per_category | max_iter | Expected wall | Expected Δ |
|---|---|---|---|---|
| iter-00 (this) | 100 raw → 12 kept | 1 | 363s | −0.380 (abort) |
| `--n-per-category 200 --max-iter 2` | 200/cat → ~50 kept × 2 iter | 2 | ~30 min | informative ± |
| full (default) | 500/cat → ~120 kept × 5 iter | 5 | ~3 h | promote-or-abort with real signal |

Minimum-informative tier formalised in ADR-2605242400.

## See also

- ADR-2605231300 — baien distill ReAct loop spec
- ADR-2605242400 — smoke is destructive finding (formalises this snapshot)
- `move1-phaseA-260524.md` — same-day Move 1 with same lesson
- `70-tools/baien-distill/src/baien_distill/nodes/train.py` — trl 1.4.0 fixes
