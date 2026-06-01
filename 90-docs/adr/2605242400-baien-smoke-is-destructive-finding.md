---
id: adr-2605242400-baien-smoke-is-destructive-finding
title: "Baien smoke runs are destructive, not informative — Move 1 Phase A + distill iter-00 honest signal"
status: accepted
doc_type: adr
topic: baien-training-floor
authoritative: true
last_verified: 2026-05-24
authoritative_for:
  - minimum-rolled training tier definition (when is a baien training run informative)
  - operator gates against publishing smoke-tier adapters to distilled-models.jsonl
depends_on:
  - adr-2605232500-baien-mx-move1-image-graft-self-training
  - adr-2605231300-baien-distill-react-loop
  - adr-2605241900-baien-edge-target-invariant
related:
  - doc-260524-move1-phaseA-snapshot
  - doc-260524-distill-iter00-snapshot
  - doc-260523-baien-context-extend-snapshot
supersedes: []
superseded_by: []
---

# Baien smoke runs are destructive, not informative — Move 1 Phase A + distill iter-00 honest signal

## Context

Two real-train runs landed on 2026-05-24 against the baien stack on EVO-X2:

1. **Move 1 Phase A** (image graft, ADR-2605232500): 10 samples, 3 SGD
   steps, projector head random-init → visual_microbench 0/4 = **0%** vs
   baseline 2/5 = 40% scorer-lenient. Outputs degraded to template loops
   ("1\n\n##: 1\n\nAnswer", 38-word "I am a human" repeats). See
   `90-docs/baien/move1-phaseA-260524.md`.

2. **Distill iter-00** (ReAct loop, ADR-2605231300): 12 validated examples,
   3 SGD steps, LoRA on q/k/v/o projections → microbench Δ = **−0.380**.
   Adapter discarded by `commit_node` abort gate.
   See `90-docs/baien/distill-iter00-260524.md`.

Both runs share the same shape:

- A trainable head (random-init projector / fresh LoRA adapter) is
  introduced into a frozen pretrained trunk
- 3 SGD steps are taken under Adam + bf16 defaults
- The resulting model is **strictly worse** than the frozen baseline

The pattern is mechanical: 3 SGD steps from random init under default
optimiser hyperparameters push the trainable head into a region of
embedding space that disrupts the trunk's pretrained behaviour. The trunk
then completes the disrupted prefix into degenerate templates or loops.

This is not a bug in the pipeline. Both pipelines work end-to-end
(data load → train loop → eval dispatch → gate decision). It is a
misclassification of what "smoke run" means.

A third run on the same day — `context-extend-snapshot-260523.md` Stage 1
RoPE scaling — surfaces a related-but-different lesson: smoke-sized eval
sets (5 prompts × 3 configs) cannot statistically distinguish "no change"
from "real failure mode", so eval-side smoke is also category-confused.

## Decision

1. **Formalise: "Phase A is pipeline validation, not learning."** Phase A
   runs (≤100 samples, ≤10 SGD steps) test that the training pipeline
   compiles end-to-end. They MUST NOT be used to compare model quality.

2. **Minimum-informative training tier (per pipeline):**

   | Pipeline | Minimum-informative tier | Approx. wall (EVO-X2 CPU bf16) |
   |---|---|---|
   | Move 1 image graft (ADR-2605232500) | Phase B: 1,000 samples → ~250 SGD steps | ~40 min |
   | Distill ReAct (ADR-2605231300) | `--n-per-category 200 --max-iter 2` (~50 kept × 2 iter) | ~30 min |
   | RoPE / context extend (ADR-2605231600) | n ≥ 20 prompts per config + 4k regression run | ~3 h per config |

   Below this tier, results carry no signal about model quality. Above
   this tier, the abort / promote gate output is trustworthy.

3. **Operator gate against publishing smoke-tier adapters.** A new entry
   in `90-docs/baien/distilled-models.jsonl` (the registry feeding
   `llm-model-registry-distilled.ts` codegen) MUST satisfy at least one of:

   - (a) trained for **≥250 SGD steps** (Phase B equivalent for image
     graft, Phase 2+ for distill); OR
   - (b) shows **≥+5 pp improvement** on `baien-microbench` over the
     frozen-trunk baseline of the same `parent_kind`

   Smoke runs that meet neither (a) nor (b) MUST NOT commit a row.
   `commit_node` in the distill ReAct loop already enforces (b) via the
   `decision = "abort"` path; the image-graft pipeline gets the
   equivalent gate in a follow-up PR.

## Consequences

- Smoke runs remain useful for **pipeline regression testing** (does the
  training loop compile? does the eval dispatcher fire? does the abort
  gate trigger correctly?) and SHOULD continue to run on every PR that
  touches `70-tools/baien-mx-train/` or `70-tools/baien-distill/`.
- Smoke results published in snapshots (e.g. `move1-phaseA-260524.md`,
  `distill-iter00-260524.md`) are **honest negative results** — they
  document that the pipeline runs and that the smoke tier is below the
  learning floor. They are NOT pipeline failures.
- ADR-2605232500's Phase table (A/B/C/D) is reaffirmed but reframed:
  Phase A is explicitly a pipeline-validation tier, not a learning tier;
  Phase B is the first tier whose outputs can be compared to baseline.
- The distill ReAct abort gate (Δ < 0 → discard) is reaffirmed as the
  correct default. Smoke runs that abort are the pipeline behaving
  correctly, not pipeline bugs.
- Wall-time budget for any "did baien actually learn anything" experiment
  rises from "~10 min smoke" to "~30 min minimum" — operators should plan
  EVO-X2 occupancy accordingly.

## Alternatives Considered

- **Lower the learning rate for smoke runs** so 3 SGD steps don't
  degrade the model. Rejected: this would mask the fact that smoke = no
  signal. The honest answer is that 3 SGD steps cannot teach, regardless
  of LR; lowering LR would just hide degradation behind "no measurable
  change", which is harder to reason about than "obvious abort".
- **Freeze the projector head for the first few warmup steps in Move 1
  Phase A** so the random-init head doesn't get pushed into a degenerate
  region. Viable Phase A enhancement; deferred to a future ADR because
  it's a Move-1-specific mitigation that doesn't generalise to the
  distill case (where the adapter is intentionally trainable from
  step 1). Tracking as Move 1 follow-up.
- **Skip Phase A entirely and jump to Phase B for any "real" Move 1
  run.** Adopted as the operator default: `e7m bench mx-train` runs Phase
  B by default unless `--phase A` is explicitly passed for
  pipeline-regression purposes.

## References

- ADR-2605232500 — Baien Move 1 image graft self-training (§Numerical
  analysis: Phase A/B/C/D table)
- ADR-2605231300 — Baien distill ReAct loop (§5 train spec; §commit_node
  abort gate)
- ADR-2605241900 — Baien edge-target invariant (encoder freeze rule;
  context for why projector + LoRA are the only learnable surfaces)
- `90-docs/baien/move1-phaseA-260524.md` — Phase A run snapshot
- `90-docs/baien/distill-iter00-260524.md` — distill iter-00 run snapshot
- `90-docs/baien/context-extend-snapshot-260523.md` — RoPE Stage 1
  snapshot (related lesson on eval-side smoke insufficiency)
- `70-tools/baien-distill/src/baien_distill/nodes/train.py` — trl 1.4.0
  fixes landed alongside this ADR
