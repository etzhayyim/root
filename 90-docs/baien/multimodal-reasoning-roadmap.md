---
id: doc-baien-multimodal-reasoning-roadmap
title: "Baien — multimodal + reasoning growth roadmap"
status: active
doc_type: explanation
topic: edge-multimodal-model-1bit
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - Baien capability roadmap (multimodal + reasoning)
  - Decision on what NOT to chase at 2B / 1.58-bit scale
related:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605092345-runpod-l40s-fp8-multimodal-model-design
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
---

# Goal

Decide the next concrete moves to grow Baien from a text-only
1.58-bit edge model into a useful multimodal + reasoning sibling to
Oka, **without pretending 2B can carry frontier reasoning**.

# Reality check

Two non-negotiable constraints frame every decision below.

## 1. 2B is a hard ceiling on emergent reasoning

BitNet b1.58 2B 4T is a strong **base** model — 4 trillion training
tokens give it broad world knowledge — but it is not an
instruction-tuned, chain-of-thought-capable reasoner. The published
benchmarks (MMLU, ARC, etc.) are good for size, but multi-step
math/code/planning at 2B is structurally weak. RL-with-verifiable-
rewards (DeepSeek R1 / OpenAI o1 style) on a 1.58-bit trunk is a
research project, not an engineering task.

Implication: **do not try to make Baien a reasoner**. Make it a
great **router + summarizer + grounded responder + escalator** to
Oka or external teachers when reasoning is required. This is exactly
what the cell-membrane metaphor (ADR 2605091400) already says —
Baien is the membrane, Oka is the cytoplasm.

## 2. The arm64 / browser i2_s path is upstream-blocked

Until microsoft/BitNet fixes the arm64 i2_s decode bug or ships an
emscripten target with the fix, Baien on Apple Silicon and in the
browser produces fluent-but-incoherent output (ADR 2605092350
Status, 2026-05-10 bisect). Anything we ship for those targets is
deferred. Server-CPU pods (linux/amd64) work today.

# Roadmap (priority ordered)

The four moves below are ordered by **leverage / risk-adjusted value
per H100-hour spent**. The first three target multimodal capability;
the fourth and fifth target reasoning + grounding.

## Move 1 — Image graft on H100 (image → text, highest value)

The ADR already specifies the design: frozen SigLIP-So400m encoder +
1.58-bit projector + frozen BitNet trunk, trained as
`kind="baien-multimodal-graft"`. Make this real.

**Concrete steps**

1. Pick a paired image-text corpus visible through `v_training_text`
   or a sibling RW view. Reasonable starting set:
   - LAION-COCO subset (~1M caption pairs) — license OK, simple.
   - LLaVA-1.5 instruction data — gives instruction-following
     image-grounded answers, not just captions.
   Snapshot it under `vertex_training_dataset_snapshot` with
   `task: "image-grounded-text"`.
2. Implement `_train_baien_graft_image()` inside
   `pymagatama/primitives/training_run.py` (sibling to
   `_run_finetune`). Loop:
   - Load `microsoft/bitnet-b1.58-2B-4T-bf16` master, freeze.
   - Load `google/siglip-so400m-patch14-384`, freeze.
   - Build a 2-layer 1.58-bit projector (image_features → 64 latent
     tokens at trunk hidden dim).
   - Forward = `[image_tokens; text_tokens]` → trunk → next-token
     loss only on the text portion.
   - Train projector for ~10k–50k steps on H100; record
     `vertex_training_checkpoint` per save step.
3. Eval: pose 50 image-grounded questions (subset of MM-Vet or
   LLaVA-Bench) at the bf16 trunk + projector, then re-quantize the
   projector to 1.58-bit and re-eval. Acceptance gate: post-quant
   accuracy drops ≤ 5 pts vs bf16 master.
4. Publish artefacts: trunk unchanged, projector blob alongside the
   text-only i2_s GGUF in B2.

**Why this first**: lowest risk (mature LLaVA recipe), highest user
value (image questions are the most-asked multimodal feature),
already wired contractually (`runBaienMultimodalGraft` lexicon
exists, `task_train_baien_graft_run` Python wrapper exists, kind is
in the runpod_handler dispatch).

**H100 budget estimate**: ~6–10 hours single-GPU at projector-only
training (frozen trunk + frozen encoder makes this cheap).

## Move 2 — Audio-speech graft (Whisper-tiny → BitNet)

Same pattern as Move 1, encoder = `openai/whisper-tiny.en` (CTC
encoder output, not full Whisper decoder). Lets Baien answer
questions about short voice clips on-device after server-side ASR
encoding.

**Why this second**: voice input is the #2 multimodal modality on
edge, and Whisper-tiny is already small enough that the whole
audio→text pipeline can run server-side CPU before the BitNet trunk
runs on the user's device.

**H100 budget**: ~4–6 hours (audio corpora are smaller).

## Move 3 — Long-context RAG grounding (compensates for 2B's reasoning gap)

This is the highest-leverage **reasoning** move available at 2B
scale. Not because we make Baien smarter, but because we **outsource
recall to Kotoba/Datomic** and let the trunk focus on synthesis.

**Concrete steps**

1. Wire Baien serving (`bitnet.cpp` server or a tiny FastAPI wrapper)
   to query the existing RW vector substrate
   (`vertex_vector_embedding_768`, ADR-2604262359) with the user's
   prompt as the embedding key. Inject the top-k results as a
   pre-prompt context block.
2. Train a small LoRA on the bf16 master (kind `baien-lora`) on a
   distilled corpus of `(question, retrieved-context, grounded-answer)`
   triples. Teacher = Oka 27B or an external API. The LoRA learns
   *to use* the retrieved context, not to memorize facts.
3. Re-quantize, deploy, measure grounded-QA accuracy vs
   no-RAG baseline.

**Why this**: at 2B, "knows the answer from weights" is unreliable;
"can summarize 4 retrieved snippets coherently" is reliable. The 4T
training corpus actually overshoots what 2B can densely memorize, so
the marginal value of more pretraining is low — the marginal value
of better recall is high.

**H100 budget**: ~8 hours for the LoRA, plus RW infra time.

## Move 4 — Bounded reasoning via teacher distillation (small step, honest framing)

We will not make Baien think harder. We will make Baien **imitate a
narrow band of CoT** that a teacher (Oka 27B or Opus / GPT-5.5)
solves correctly.

**Concrete steps**

1. Generate ~50k `(question, teacher_CoT, final_answer)` triples
   from the teacher on a curated corpus (math word problems, code
   reasoning, single-step planning). Snapshot as
   `kind="baien-cot-distill"` dataset.
2. Train a `baien-lora` on top of the bf16 master against the
   teacher CoT. Loss = next-token on the CoT + final answer.
3. Eval on a held-out set of the same teacher's
   solved-correctly-and-confidently subset. Acceptance gate:
   final-answer accuracy ≥ 60 % of teacher's, on this narrow band.

**Don't generalize the claim.** The output of this move is "Baien
imitates teacher CoT for question types it has seen", not "Baien
reasons". Outside the training distribution, fall back to delegating
to Oka via the magatama MCP facade.

**H100 budget**: ~6–10 hours, dataset generation cost depends on
which teacher.

## Move 5 — Plasmid / capability discovery as a reasoning surface

The cohort/cell ADRs (2605091300 cultivar, 2605091600 plasmid graft)
treat tools as horizontally-acquired capabilities. For a 2B trunk,
this is actually a **good reasoning shortcut**: if Baien can pick
the right tool for a query, the *tool* does the reasoning.

**Concrete steps**

1. Train a tool-router LoRA (kind `baien-lora`, with
   `task: "tool-routing"` in hyperparams). Inputs = user prompt +
   list of available capability descriptions; output = which
   capability to invoke. Teacher = Oka or rule-based ground truth.
2. Wire Baien serving's response into the magatama MCP facade so
   tool calls dispatch to either local edge tools or remote Oka.

**Why this**: combines with Moves 3+4. Baien acts as the routing
layer, escalates hard cases via MCP. The 2B / 1.58-bit constraints
become *features* (instant routing, low cost) rather than
limitations.

**H100 budget**: ~4 hours.

# What we explicitly do NOT do at this scale

- **Train Baien from scratch with multimodal pretraining.** That
  needs the full 4T-token budget × multiple modalities. Out of
  scope for our compute. We graft, we do not pretrain.
- **RL with verifiable rewards on the 1.58-bit trunk.** Theoretical
  win, no engineering ROI at 2B today. Revisit if microsoft / a
  community contributor publishes a working PEFT-with-RLHF recipe
  for BitNet.
- **Multi-image / video reasoning.** Single-image first; video is a
  separate capacity discussion (frame sampling + temporal
  aggregation) that we do not need to settle until image works.
- **A "Baien-XL" 7B or 14B trunk.** We have Oka for that. Adding a
  middle weight class is Shannon-redundant unless evidence shows
  Oka can't be the escalation target.

# Suggested first execution

**Move 1, image graft.** It is fully designed (lexicon + Python +
billing SKU + ADR all present), it is the highest-value single
addition for users, and its training cost is the lowest of the four
moves. Start by snapshotting the LAION-COCO subset into
`vertex_training_dataset_snapshot` and writing
`_train_baien_graft_image()` as a sibling to `_run_finetune`. A
working bf16-master + projector at LLaVA-Bench parity (within the
2B/projector class) is the milestone that proves the whole graft
architecture works; everything after that is repetition.

Concrete first sprint (one H100 session, ≤ 12 hours wall clock):

1. Dataset snapshot (60-min CPU-pod task — no GPU).
2. `_train_baien_graft_image()` implementation (2–3 hours human).
3. ~10k step projector training on H100 (≈ 2–3 hours wall clock).
4. Eval at bf16 master, eval after projector re-quant, write to
   ADR 2605092350 Status. Decide whether to invest in Moves 2–5.

# References

- ADR 2605092350 (Baien design + Status / bisect log)
- ADR 2605092345 (Oka — sibling FP8 trunk on H100)
- ADR 2605091300 (cultivar layer)
- ADR 2605091400 (cell-membrane / Lexicon demotion)
- ADR 2605091600 (plasmid / horizontal tool acquisition)
- ADR 2604262359 (Kotoba/Datomic vector substrate)
- `00-contracts/lexicons/com/etzhayyim/apps/training/runBaienMultimodalGraft.json`
- `20-actors/magatama/py/src/pymagatama/primitives/training_run.py:task_train_baien_graft_run`
