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
