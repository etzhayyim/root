---
id: adr-2605302359-moe-expert-activation-profiling-and-agentic-qlora
title: "ADR-2605302359: MoE expert-activation profiling substrate (gemma-4-26B-A4B) + agentic-capability QLoRA enhancement plan — profiling informs the QLoRA target set (shared expert + attention + router); Unsloth is CUDA-gated, peft+trl on ROCm is the now-path"
status: proposed
doc_type: adr
topic: moe-expert-activation-and-agentic-qlora
authoritative: true
last_verified: 2026-05-30
priority: 6.5
axis: baien-ml
weight: 0.60
priority_note: "Two linked decisions from the 2026-05-30 session. (1) A per-model MoE expert-activation profiling substrate: tag each (layer, expert) of a llama.cpp MoE GGUF by query category via ffn_moe_topk capture, manage per-model as a DataLad subdataset (ADR-2605241500). Landed for gemma-4-26B-A4B (48-query probe, 3122/3840 experts classified, 81.3% coverage). (2) An agentic-capability QLoRA plan that USES the profiling: the always-active shared expert (dense FFN, 535M) + attention + router (ffn_gate_inp) are the efficient QLoRA targets, the 128 routed experts (22.8B) stay frozen in 4-bit. Honest hardware reality: Unsloth's CUDA-first dep tree does NOT install on the EVO-X2 (Windows + AMD ROCm 7.2 + Py3.12; probe 2026-05-25); the now-path is peft+trl QLoRA on ROCm (same stack as gemma-coder-distill); Unsloth becomes the path only once a CUDA GPU is provisioned under the §2(i)(2) train carve-out (ADR-2605262200, earliest effective ~2026-07-19). The 26B artifact is named baien-server-agentic-* (server carve-out; NOT the ≤12B edge baien per ADR-2605241900). Inference stays Murakumo-only (ADR-2605215000); training data is Charter §2(a)-(h) scanned; the agentic SFT corpus is the missing piece this ADR scopes."
authoritative_for:
  - MoE expert-activation profiling method (ffn_moe_topk capture via llama-eval-callback) + the `moe-expert-activation/<model>` DataLad subdataset layout
  - per-(layer,expert) classification schema (top_category / specialization / confidence / unseen-rare)
  - the MoE-aware QLoRA target policy (shared expert + attention + router trainable; routed experts frozen)
  - agentic-capability QLoRA plan for `baien-server-agentic-gemma4-26b-a4b-*`
  - Unsloth-vs-peft+trl decision under the ROCm/CUDA hardware reality
  - distributed-training path policy on the owned Murakumo Mac mini fleet (MLX data-parallel LoRA; pipeline-parallel for >1-mini models) — own hardware, no §2(i)(2) gate
depends_on:
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605253000-mac-mini-m4-16gb-gemma4-26b-moe-disk-inference
  - adr-2605250400-gemma-coder-distill-rocm
  - adr-2605231300-baien-distill-langgraph-coding
  - adr-2605262200-charter-rider-train-gpu-carveout
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605261900-baien-moemoekyun-moe-r0
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-30: after computing the shared-expert size of gemma-4-26B-A4B
  (535M; 30 layers x 3 x 2816 x 2112) the user asked to (a) tag which experts
  activate for which queries and manage per-model with DataLad — landed as the
  moe-expert-activation/gemma-4-26B-A4B subdataset — and then (b) "update toml,
  adr; how to strengthen agentic capability via Unsloth QLoRA". This ADR records
  both and ties them: the profiling tells you WHICH modules to put adapters on.
---

# Context

## Part A — MoE expert-activation profiling (landed)

`gemma-4-26B-A4B` (ADR-2605253000) is a 128-expert MoE: 8 routed + 1 shared
expert active per token, 25.2B total / ~4B active. The GGUF tensors give the
exact arch: 30 layers, hidden 2816, routed-expert FFN 704, **shared (dense)
FFN 2112** → shared expert ≈ **535M params** (always active); routed experts
≈ 22.84B (frozen knowledge mass).

To know *which experts do what*, this session built a profiling substrate:

- **Capture**: `llama-eval-callback` (llama.cpp b9290) exposes
  `ffn_moe_topk-{L}` (i32, `{8, n_tokens}`) — the top-8 selected experts per
  token per layer. A labeled query suite is run through the model; every
  captured expert selection while processing a category-`C` query increments
  `hist[layer][expert][C]`.
- **Tag**: per `(layer, expert)` the normalized category share → top category
  + specialization + salience (`spec × activations`) + confidence.
- **Classify ALL**: every one of the 30×128 = 3840 cells gets an entry;
  cells the probe never routed to are `unseen-rare` (not guessed).
- **Manage per-model**: a DataLad subdataset per model under
  `90-docs/baien/datasets/moe-expert-activation/<model>/` (ADR-2605241500).

**Result (48-query probe, gemma-4-26B-A4B)**: 3122/3840 classified (81.3%),
718 unseen-rare. Coverage scales with query *count*, not tokens/query
(eval-callback prints only the prefill eval; generation adds no rows). Two
honest capture limits, documented in the dataset: eval-callback's preview
shows 6 of 8 experts/token (ranks 0-2 + 5-7; middle ranks 3-4 hidden) and 6
of n tokens — uniform across experts/categories, so relative tagging is
unbiased but it is a sample, not a census. `-c 128 -n 1` is OOM-safe on
Metal 16GB; larger ctx / generation OOMs (worked around with `-ngl 0` CPU).

## Part B — agentic-capability QLoRA (proposed)

The user wants to strengthen **agentic capability** (tool use, function
calling, multi-step ReAct planning, structured/JSON output, self-correction)
via **Unsloth QLoRA**. Three realities bound the answer:

1. **Unsloth is CUDA-first and does NOT install on the training node.** The
   EVO-X2 is Windows + AMD Radeon 8060S (ROCm 7.2) + Python 3.12. The
   2026-05-25 probe (`90-docs/baien/probe_unsloth_rocm.json`) failed: xformers
   wheel is py39-only, triton-windows is CUDA-only, torchao /
   cut_cross_entropy assume the CUDA stack → pip resolver recursion blew up.
   The working LoRA stack on this node is **peft + trl + bitsandbytes** (the
   gemma-coder-distill path, ADR-2605250400).
2. **Training on rented commercial GPU is currently prohibited.** Charter
   Rider §2(i) covers training + fine-tuning, not just inference. The
   train-only carve-out §2(i)(2) (ADR-2605262200) is *proposed*, earliest
   effective ~2026-07-19 (Council Lv6+ ≥4 + 30-day objection). Until then:
   EVO-X2-only.
3. **26B is not edge baien.** ADR-2605241900 caps `baien-*` edge artifacts at
   ≤12B trunk. A 26B agentic adapter artifact MUST be named
   `baien-server-agentic-*` (the server carve-out), out of the edge ceiling.

# Decision

## §1 — Profiling substrate (authoritative, landed)

The `moe-expert-activation/<model>` DataLad subdataset is the canonical home
for MoE expert tags. Per model: `model.json` (arch + GGUF sha256),
`query-suite.jsonl`, `expert-tags.json`, `expert-classification.json`/`.csv`
(all 3840 cells), `CLASSIFICATION.md`, `captures/` (raw `ffn_moe_topk` rows),
`harness/` (reproducible scripts). Expert ids are model-specific, so the
per-model subdataset is the correct versioning + IPFS-pin unit. Sibling models
(e.g. `qwen3.5-a3b`, `gemma-4-e4b`) are added with the same harness.

## §2 — MoE-aware QLoRA target policy (profiling-informed)

For QLoRA on a 128-expert MoE, the adapter target set is chosen from the
profiling, NOT blanket "all linear":

| Module group | Params | QLoRA? | Why |
|---|---|---|---|
| Attention `q/k/v/o_proj` (Gemma4 inner `.linear`) | small | **LoRA (trainable)** | shapes attention / planning; proven target (gemma-coder-distill) |
| **Shared/dense FFN** `ffn_{gate,up,down}` | **535M, always active** | **LoRA (trainable)** | every token passes it → highest-leverage behavior shaping per adapter param |
| Router `ffn_gate_inp` (2816×128/layer) | ~11M | **LoRA (optional, low-rank, low-LR)** | nudges routing toward agentic experts; risky → small r, frozen by default at R0 |
| 128 routed experts `ffn_{gate_up,down}_exps` | **22.84B, 4-bit** | **frozen** | broad knowledge mass; QLoRA shapes via attention + shared FFN instead |

The expert-classification (Part A) is the **instrument**: after a training
run, re-run the profiler and diff `expert-classification.json` to confirm
(a) code/reasoning/tool-adjacent experts gain salience, (b) routing entropy
stays healthy (no expert collapse), (c) no catastrophic category drift.

## §3 — Training stack: three paths (Mac-mini fleet / EVO-X2 / gated CUDA)

The constitutionally cleanest training substrate is the **owned Murakumo Mac
mini fleet** itself — own hardware, no commercial rental, so NO §2(i)(2)
carve-out gate applies.

- **NOW, CLEANEST (Murakumo Mac mini fleet via MLX `mlx.distributed`)** —
  Apple MLX supports multi-Mac distributed training (MPI or ring backend over
  LAN/Thunderbolt). The sweet spot is **data-parallel LoRA/QLoRA**: each mini
  holds the frozen 4-bit base + the small adapters and trains on a data shard;
  only the **LoRA gradients** (MBs, not the full model) are all-reduced, so the
  fleet's 1GbE/10GbE interconnect is not the bottleneck → near-linear scaling
  across the ~10 minis. **Constraint**: data-parallel requires the model to fit
  on ONE 16GB mini, so this path fits **≤~8-12B 4-bit** (gemma-4-e4b, a ≤4B
  baien) cleanly. A **26B** model does NOT fit one mini for training → needs
  pipeline/model-parallel (shard the 30 layers across ~3-4 minis via MLX
  distributed) which is feasible but slower and more complex, OR use EVO-X2.
  This is the preferred R0 path for `baien-*`/`baien-server-*` adapters that
  fit a mini. No Council gate.
- **NOW, BEST FOR 26B (EVO-X2 single node, 128 GB unified)** — the EVO-X2
  (AMD Ryzen AI Max+ 395, **128 GB unified**: 32 GB VRAM UMA carve-out +
  96 GB sys, BIOS-re-carvable up to ~96 GB to the iGPU) is the owned node
  that fits **gemma-4-26B-A4B QLoRA whole**: 4-bit base ≈14 GB + LoRA
  adapters + AdamW(adapter-only) + grad-checkpointed activations all sit in
  unified memory — no model sharding, no disk-paging, no Council gate.
  peft + trl QLoRA, for models too large to data-parallel on a single
  16 GB mini (the 26B is exactly this case):
  `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
  bnb_4bit_compute_dtype=bf16)` + `LoraConfig(r=16–32, alpha=32–64,
  target_modules=<§2 set>)` + `SFTTrainer`. Same stack as gemma-coder-distill,
  extended with the shared-FFN (+ optional router) targets. 26B 4-bit ≈ 14 GB
  weights + adapters + optimizer — fits the Strix Halo large unified memory,
  slow (~hours/epoch). This needs **no amendment** (own hardware, not rental).
- **WHEN a CUDA GPU is provisioned (gated on ADR-2605262200, ~2026-07-19)** —
  Unsloth: `FastModel.from_pretrained(load_in_4bit=True)` +
  `get_peft_model(r=…, target_modules=<§2 set>,
  use_gradient_checkpointing="unsloth")` + `SFTTrainer`. ~2× faster, lower
  memory, native 4-bit MoE. Gated by the carve-out's 7 conditions (per-rental
  kotoba-datomic attestation; >7 days → Council; data Charter-scanned; artifact
  named `baien-server-agentic-*`). Unsloth on the AMD node is re-probed via
  `70-tools/gemma-coder-distill/scripts/probe_unsloth_rocm.py` when upstream
  ships a Windows-ROCm dep tree.

**Verdict on "Unsloth で agentic を QLoRA で強化": yes, but Unsloth is the
CUDA/post-carve-out path (gated). Today, on owned hardware: data-parallel
LoRA across the Mac mini fleet via MLX for any model that fits a mini
(≤~8-12B 4-bit), or peft+trl QLoRA on EVO-X2 for the 26B. Same LoRA config
and same agentic data in every case; only the trainer/backend differs, so
the corpus (§4) and target set (§2) are written once and reused.**

### Distributed-train sizing on the Mac mini fleet (MLX)

| Model | Fits 1 mini (16GB) for LoRA-train? | Fleet path |
|---|---|---|
| ≤4B baien / gemma-4-e4b (~8B) 4-bit | yes (4-bit base ~2-4 GB + adapters + activations) | **data-parallel** across N minis; all-reduce LoRA grads only → near-linear |
| ~12B 4-bit | tight (≈7 GB base + train overhead) | data-parallel with small batch + grad-checkpointing |
| **26B-A4B** (4-bit ≈14 GB) | **no** (16 GB has no room for grads/optimizer/activations) | **train on EVO-X2** (128 GB unified — fits whole, the recommended 26B path); Mac mini fleet only via custom **pipeline-parallel** MLX trainer (~3-4 minis hold layer-shards) — buildable but a real project, not off-the-shelf MLX-LM |

Interconnect: gradient all-reduce of LoRA adapters is communication-light, so
1GbE suffices; Thunderbolt-bridge / 10GbE only matters for pipeline-parallel
activation passing or full-weight (non-LoRA) training.

## §4 — Agentic SFT corpus (the missing piece)

No tool-use / function-calling SFT dataset exists in-repo. Build one as a
`baien-moemoekyun-train` recipe (TOML, weighted mix, all Tier-A
Apache/MIT/CC-BY + Charter §2(a)-(h) scanned), combining:

1. **Open agentic corpora** (license + Charter scanned): function-calling /
   tool-use / ReAct SFT sets (e.g. Glaive-function-calling, xLAM/APIGen,
   ToolACE-class — admit only Charter-clean, openly-licensed shards).
2. **In-repo harvested traces**: instrument the kotodama LangGraph cells +
   `aria` + the kanae actor's `Invoke(did, method, params)` calls →
   `(state, tool_call, tool_result, next)` tuples → Gemma chat-template
   tool-call turns. This is the highest-value, on-distribution signal.
3. **Synthetic traces via Murakumo** (NOT Anthropic-direct): generate
   tool-use dialogues through the judah LiteLLM gateway (gemma teacher), per
   the baien-distill §3a indirect-teacher pattern (ADR-2605231300). Direct
   vendor-API distillation is prohibited (ADR-2605215000 §1.2).

Format: Gemma chat template with `system` (tools schema) / `user` /
`assistant` (tool_call JSON) / `tool` (result) / `assistant` (final). Gate
JSON validity + tool-arg schema-match at `validate`.

## §5 — Eval gate (mirror gemma-coder-distill)

`analyze → fetch → validate → train → evaluate → commit`. The `evaluate`
node runs an **agentic bench** (tool-call accuracy, multi-step task
completion, JSON/schema validity) AND re-runs the expert-profiler to confirm
routing health; `commit` appends the artifact manifest only on improvement.
Artifact name: `baien-server-agentic-gemma4-26b-a4b-r<NN>`. Inference of the
trained adapter remains Murakumo-only (ADR-2605215000).

# Consequences

**Positive.** Expert tags become a *training instrument*, not just an
analysis curio: they choose the adapter target set and verify routing health
post-train. The now-path (peft+trl on ROCm) needs no Council gate, so R0
agentic QLoRA can start on owned hardware immediately; Unsloth is a drop-in
speedup later.

**Costs / risks.** (a) Unsloth on AMD/ROCm remains blocked — the "Unsloth"
ask is satisfiable only on CUDA (gated). (b) Training the router risks expert
collapse — frozen by default at R0; the profiler is the guardrail. (c) The
agentic SFT corpus is net-new work (§4) and is the real critical path. (d)
26B QLoRA on EVO-X2 is slow; the carve-out + a CUDA rental is what makes it
practical at scale (gated ~2026-07-19).

**Neutral.** No model is trained by this ADR; it records the substrate (landed)
+ the plan (proposed). Inference invariant and edge ceiling are untouched.

# Alternatives Considered

1. **Force Unsloth onto EVO-X2 now.** Rejected: dep tree is CUDA-only; the
   2026-05-25 probe confirmed it is uninstallable on Windows+ROCm+Py3.12.
2. **QLoRA all-linear (including routed experts).** Rejected: 22.8B routed
   experts are the frozen knowledge mass; adapting them is expensive and
   destabilizing. Shared FFN + attention is the efficient, profiling-justified
   target.
3. **Rent a CUDA GPU now for Unsloth.** Rejected until ADR-2605262200
   ratifies (~2026-07-19); Charter Rider §2(i) currently forbids rental
   training.
4. **Name the 26B artifact `baien-*`.** Rejected: violates the ≤12B edge
   invariant (ADR-2605241900). Must be `baien-server-agentic-*`.

# References

- `/90-docs/baien/datasets/moe-expert-activation/gemma-4-26B-A4B/` — the landed profiling subdataset (tags + classification + harness)
- `/90-docs/adr/2605253000-mac-mini-m4-16gb-gemma4-26b-moe-disk-inference.md` — model arch + disk inference
- `/90-docs/adr/2605241500-etzhayyim-dataset-cid-substrate.md` — DataLad substrate
- `/90-docs/adr/2605250400-gemma-coder-distill-rocm.md` — peft+trl LoRA on ROCm (the now-path stack) + Unsloth ROCm probe
- `/90-docs/adr/2605262200-charter-rider-train-gpu-carveout.md` — §2(i)(2) train-only GPU carve-out (gated)
- `/90-docs/adr/2605241900-baien-edge-target-invariant.md` — ≤12B edge ceiling + baien-server-* carve-out
- `/90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — Murakumo-only inference
- `/CHARTER-RIDER.md` §2 — prohibited categories (training-data scan)
- `/70-tools/baien-moemoekyun-train/recipes/` — recipe TOML format for the agentic corpus
