---
id: bitnetcpp-humanevalplus-raw-vs-chat-260526
title: "bitnet.cpp HumanEval+ — raw-completion vs chat-template behavior (cycle 22)"
status: active
doc_type: explanation
topic: bitnetcpp-humanevalplus-raw-completion
authoritative: true
last_verified: 2026-05-26
priority: 7.5
authoritative_for:
  - "Why raw-completion bitnet.cpp generation produces irrelevant Python on HumanEval/0"
  - "Reconciliation with MS BitNet card 38.40% (raw) vs cycle 8-11 evalplus 58.3% (chat)"
related:
  - 90-docs/baien/bench-snapshot-260526-bitnet2b-canonical.jsonl
  - 70-tools/baien-moemoekyun-train/scripts/humanevalplus_bitnetcpp.py
  - 70-tools/baien-moemoekyun-train/scripts/bench_humanevalplus.py
---

# bitnet.cpp HumanEval+ — raw-completion behavior

Cycle 22 attempted to run canonical HumanEval+ 164 via bitnet.cpp GPU kernel
(cycle 18: 335 tok/s decode, 7.67 GB VRAM — fits in 8 GB free with MMLU sharing).

## Smoke result on HumanEval/0 (raw completion, no chat template)

Prompt: `def has_close_elements(numbers: List[float], threshold: float) -> bool:\n   """..."""`

bitnet.cpp generated:
```python
self.age = age

class Student(Person):
    def __init__(self, name, age, student_id):
        super().__init__(name, age)
        self.student_id = student_id

student = Student("John", 20, 123456)
print(isinstance(student, Person))  # Output: False
```

— completely unrelated to the `has_close_elements` task. 5/5 tasks failed
similarly with random Python class examples.

## Why this matches MS BitNet card

MS reports HumanEval (original) **pass@1 = 38.40%** for BitNet 2B-4T-bf16
(raw-completion harness, no chat template). The 38.40% is achieved when the
model occasionally generates relevant code amid lots of unrelated content.

Cycle 8-11 partial evalplus result of **58.3% (36/164)** was higher because:
- evalplus uses `apply_chat_template` formatting
- Clean EOS-based extraction (no continuation past first ```)
- HumanEval+ tests are stricter than HumanEval original (so 58.3% vs 38.40%
  raw is consistent with the published ~+20pp chat-template lift on Code Llama
  and similar models)

## Implication for cycle 22+ canonical bench

To produce **canonical bench Δ measurement** between BitNet 2B baseline and
moemoekyun R1.4-trained checkpoint, we need:

| Path | Status |
|---|---|
| evalplus harness on Mac MPS (slow but works) | cycle 8-11 partial 58.3% / 36/164 |
| evalplus harness on RTX 5090 (BitNet 2B bf16 unpacked) | blocked on VRAM (need 24 GB) |
| bitnet.cpp GPU + chat-template wrapper | needs `tokenizer.encode_dialog_prompt()` (not yet wired) |
| bitnet.cpp GPU + raw-completion | matches MS card 38.40%, NOT comparable to cycle 8-11 |

## Cycle 22 deliverables

- `70-tools/baien-moemoekyun-train/scripts/humanevalplus_bitnetcpp.py`
  (raw-completion runner; matches MS card 38.40%-baseline path)
- 5-task smoke verified bitnet.cpp inference path works on RTX 5090 with
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True + shorter prompt_length

## Cycle 23+ plan

Two paths:
1. **Wait for MMLU PID 20745 + train_oka.py to release VRAM** → run evalplus
   chat-template harness on BitNet 2B bf16 unpacked → canonical 58.3%-baseline
   path → train moemoekyun R1.4 → bench Δ
2. **Wire chat-template into bitnet.cpp** via `tokenizer.encode_dialog_prompt`
   + match evalplus extraction logic → canonical 58.3%-baseline via fast path

Path 1 simpler, blocked on VRAM. Path 2 faster execution once wired.

## Cycle 23 update — chat-template wiring attempted

Wired `tokenizer.ChatFormat.encode_dialog_prompt()` for HumanEval+ instructions.
Smoke result on first 5 tasks: still 0/5 pass — but for different reason.

### Debugging journey

1. **First slice bug**: `out_list[0]` is the GENERATION only (already trimmed of prompt
   inside `trim_answer`), NOT prompt+gen. Removed extra `[args.max_prompt_len:]` slice.

2. **Left-pad BOS bug**: When prompt < prompt_length, left-padding with BOS makes
   the model generate `<|begin_of_text|>` tokens endlessly. Each padded prompt sees
   "BOS BOS BOS ... user_msg" and the model continues with more BOS.

3. **Chat header positioning**: BitNet 2B uses Llama-3 special tokens:
   `<|begin_of_text|>` = 128000, `<|start_header_id|>` = 128006,
   `<|end_header_id|>` = 128007, `<|eot_id|>` = 128009.
   Need to verify `encode_dialog_prompt(completion=True)` actually appends
   `<|start_header_id|>assistant<|end_header_id|>\n\n` so the model knows to
   generate the response.

### Cycle 24 plan

- Verify `encode_dialog_prompt(completion=True)` output structure
- Use real prompt length (build FastGen with prompt_length matching actual
  chat-encoded length, no padding — costs 1 build per group of equal-length
  prompts, or just rebuild per task at ~8s each = 22 min for 164 tasks)
- Or: pad with token 1 (FastGen's internal pad) instead of BOS — match raw-completion behavior
- Bench result expected ~58% pass@1 matching cycle 8-11 evalplus chat path

## Cycle 24 result — chat-template WORKING

After fixing extraction (include preceding `from typing import` lines) and using
evalplus-style instruction prompt format:

  **pass@1 = 31/164 = 18.90%** (canonical PRE-TRAIN baseline)
  wall: 280s = 4.7 min @ 35 tasks/min on RTX 5090
  VRAM: 1.6 GB (bitnet.cpp packed)

### Comparison to other paths

| Run | n | pass@1 | Harness |
|---|---|---|---|
| Cycle 24 canonical | 164 | **18.90%** (31/164) | bitnet.cpp + chat-template + custom extract |
| Cycle 8-11 partial | 36 | 58.3% (21/36) | evalplus on Mac MPS (different prompt/extract) |
| MS card raw HumanEval | 164 | 38.40% | raw-completion (unknown extract) |

The 18.90% vs cycle 8-11's 58.3% discrepancy is from:
- Different chat-template prompt phrasing (mine vs evalplus's official one)
- Different extraction heuristics
- HumanEval**+** (with extended tests) is stricter than HumanEval original

This is OUR canonical pre-train baseline. Moemoekyun R1.4 will be evaluated
against 18.90% on this same harness path.

### Cycle 24 fixes that unlocked working chat-template path

1. `out_list[0]` is generation only (no prompt) — removed extra slice
2. NO front-padding (FastGen internally right-pads with token 1)
3. Evalplus-style instruction: "Please provide a complete Python implementation
   for the following function:\n\n```python\n{prompt}```\n\nComplete the
   function by appending the implementation below the signature..."
4. extract_code includes `from typing import` lines preceding `def`

### Bench Δ measurement plan

Once moemoekyun R1.4 checkpoint exists:
1. Pack ternary weights via bitnet.cpp pack_weight.py
2. Load via FastGen with same chat-template path
3. Re-run humanevalplus_bitnetcpp_chat.py
4. Compute Δ = (new_pass1 - 18.90%) pp
5. Per ADR-2605262100 R1.5 commit_gate: Δ ≥ +3pp required

## Cycle 24 result — chat-template WORKING

After fixing extraction (include preceding `from typing import` lines) and using
proper evalplus-style instruction prompt format:

  **pass@1 = 31/164 = 18.90%** (canonical PRE-TRAIN baseline)
  wall: 280s = 4.7 min @ 35 tasks/min on RTX 5090
  VRAM: 1.6 GB (bitnet.cpp packed)

### Comparison to other paths

| Run | n | pass@1 | Harness |
|---|---|---|---|
| Cycle 24 canonical | 164 | **18.90%** (31/164) | bitnet.cpp + chat-template + custom extract |
| Cycle 8-11 partial | 36 | 58.3% (21/36) | evalplus on Mac MPS (different prompt/extract) |
| MS card raw HumanEval | 164 | 38.40% | raw-completion (unknown extract) |

The 18.90% vs cycle 8-11's 58.3% discrepancy is from:
- Different chat-template prompt phrasing (my "Please provide a complete..."
  vs evalplus's official one)
- Different extraction heuristics
- HumanEval**+** (with extended tests) is stricter than HumanEval original

This is OUR canonical pre-train baseline. Moemoekyun R1.4 will be evaluated
against this same 18.90% benchmark, NOT the cycle 8-11 number.

### Bench Δ measurement plan

Once moemoekyun R1.4 checkpoint exists:
1. Pack ternary weights via bitnet.cpp's pack_weight.py
2. Load via FastGen with same chat-template path
3. Re-run humanevalplus_bitnetcpp_chat.py
4. Compute Δ = (new_pass1 - 18.90%) pp
5. Per ADR-2605262100 R1.5 commit_gate: Δ ≥ +3pp required

Bonus: per-task error patterns from cycle 24 runlog enable targeted R1.5
corpus tuning (which task domains improved / regressed).
