---
id: doc-260524-move1-phaseA-snapshot
title: "Baien Move 1 image graft — Phase A real-train snapshot 2026-05-24"
status: active
doc_type: snapshot
topic: baien-mx-move1
authoritative: false
last_verified: 2026-05-24
related:
  - adr-2605232500-baien-mx-move1-image-graft-self-training
  - 70-tools/baien-mx-train/
  - doc-260523-frontier-bench-snapshot
---

# Move 1 Phase A real-train snapshot — 2026-05-24

First end-to-end Phase A run of the `baien-mx-train` Move 1 pipeline on the
EVO-X2 reference host. Result: pipeline ✓ but visual gate FAIL — the smoke
tier is destructive to the projector head, not informative.

## Setup

- Host: EVO-X2 (Ryzen AI Max+ 395), Python 3.10, torch 2.12.0 CPU
- transformers 5.9.0, peft + trl 1.4.0
- Vision encoder: `google/siglip-base-patch16-224` (SiglipVisionModel, frozen)
- Trunk: `microsoft/bitnet-b1.58-2B-4T-bf16` (frozen)
- Projector: 8,524,800 trainable params (siglip hidden → bitnet embed)
- Dataset: `baien-graft-smoke` (10 PIL shapes; Phase A target=100 samples but
  only 10 actually collected — first hint that "Phase A" was warmup-only)
- Bootstrap: `pip install -e . sentencepiece protobuf`
- `PYTHONIOENCODING=utf-8` required (cp1252 fallback on Windows host crashed
  the `e7m bench mx-train` dispatch wrapper)

## Training

| Step | Loss |
|---|---|
| 1 | 3.77 |
| 2 | 10.71 (spike) |
| 3 | 1.87 |
| mean | 5.45 |

3 SGD steps over 10 samples, ~12 min wall.

## Eval

`visual_microbench` (4 prompts) post-train:

| Prompt | Result | Output |
|---|---|---|
| 1 | FAIL | "1\n\n##: 1\n\nAnswer" |
| 2 | FAIL | "1\nAnswer: 1\nAssistant" |
| 3 | FAIL | 38-word "I am a human" loop |
| 4 | FAIL | "1\n\n##: 1" |

Score: 0/4 = 0%. Baseline (frozen trunk, no projector training):
2/5 = 40% scorer-lenient on the same harness — i.e. 3 SGD steps from the
random-init projector head actively *degraded* outputs into degenerate
templates.

## Interpretation

The pipeline (data load → projector init → SFT loop → eval dispatch) runs
end-to-end on CPU bf16. But the run cannot be called "training" in any
meaningful sense:

1. 3 SGD steps × 10 samples is a forward-pass smoke, not a learning regime
2. The random-init projector head, under 3 grad steps with bf16 + Adam
   defaults, gets pushed into a degenerate region of embedding space
3. The trunk then completes the degenerate prefix into template/loop output

The honest read is "Phase A = pipeline validation, not learning". Trying to
read quality off Phase A results is a category error.

## Gate decision

FAIL on visual gate. Do not commit Phase A adapter. Proceed to Phase B
(1000 samples → ~250 SGD steps → ~40 min wall) as the actual
minimum-informative tier.

## Next runs

| Phase | Target samples | Actual SGD steps (batch=1, accum=4) | Wall (CPU bf16) |
|---|---|---|---|
| A (this run) | 100 → 10 | 3 | ~12 min |
| B | 1,000 | ~250 | ~40 min |
| C | 10,000 | ~2,500 | ~6.7 h |
| D | 50,000 | ~12,500 | ~33 h (overnight) |

## Follow-ups

- Run Phase B (1k samples) — this is the smallest tier where pre/post Δ on
  `visual_microbench` carries signal
- Verify the "text Δ subprocess" actually fires (current run dispatched but
  the parent process exited before subprocess result could be captured)
- Add `--with-eval` chain to `baien-mx-train/__main__.py` so the eval
  subprocess result lands inside the same run dir, not a sibling
- Address cp1252 in `e7m bench mx-train` dispatch (force utf-8 on the
  inner Python invocation, not just the outer shell)

## See also

- ADR-2605232500 — Move 1 image graft self-training spec (Phase A/B/C/D table)
- ADR-2605242400 — Smoke is destructive finding (formalises this snapshot's lesson)
- `90-docs/baien/distill-iter00-260524.md` — same-day distill smoke with same pattern
