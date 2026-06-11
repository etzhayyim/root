---
id: adr-2605241900-baien-edge-target-invariant
title: "Baien edge-target invariant — model size + context ceiling for universal edge deployment"
status: accepted
doc_type: adr
topic: baien-edge-invariant
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien model size + context window hard ceilings
  - permitted modality stack (frozen encoder + 1.58-bit projector) within ceiling
  - "edge / browser / cpu" useCases gate
  - server-side variant naming carve-out
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605231300-baien-distill-react-loop
  - adr-2605231600-baien-context-extension
  - adr-2605232500-baien-mx-move1-image-graft-self-training
related:
  - 40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts
  - 70-tools/baien-distill/
  - 70-tools/baien-mx-train/
supersedes: []
superseded_by: []
---

# Context

baien's value proposition (ADR-2605092350) is to be **the always-available
all-modalities zero-server tier** that runs on edge / browser / CPU.
Every Move ADR (1 image → ∞ future modalities) and extension ADR
(rope-extend, context-extend, etc.) has been written with this in
mind, but the constraint has never been **formally codified as a
hard ceiling that prevents accidental drift**.

Without a codified invariant:

- A future Move could add a per-modality trunk branch that grows the
  trunk past 2B (e.g., baien-MX Move 3 of ADR-2605101000 adds branches
  that, if cumulative, could push past edge limits).
- A future distill iteration could LoRA-merge a large adapter and
  silently bloat the deployment artifact.
- A future context-extension (ADR-2605231600 Stage 3 LongRoPE 128k)
  could land checkpoints that **no longer fit edge** but inherit the
  "baien" name + `useCases: ["edge", "browser", "cpu"]`.

This ADR fixes the invariant in the same constitutional layer as
Charter Rider §2: any baien artifact that exceeds the ceiling is
**out of bounds** and must be re-tagged as a separate non-edge
variant before publication.

# Decision

## Constitutional invariant (NOT amendable without same-level Council vote)

A model artifact may be tagged `baien` AND `useCases: ["edge", "browser", "cpu"]`
in the kotodama `MODEL_REGISTRY` (and shipped to first-party endpoints
that expect edge baien) **if and only if** it satisfies **all** of:

1. **Trunk params ≤ 12 B** (amended 2026-05-23 per ADR-2605242000 §Conflict —
   the original 4 B limit assumed BitNet 1.58 packing density; Bonsai-pattern
   1-bit can pack 8 B params in 1.15 GB per Prism ML 2026 reference,
   keeping criterion 2 binding. Hard wall stays at 12 B since beyond that
   the 1-bit packed size exceeds 1.6 GB regardless).
2. **Total weights packed ≤ 1.6 GB** (i2_s ternary or 1-bit Bonsai or equivalent — this is the binding criterion).
3. **Inference RAM peak at 4 k context ≤ 2.0 GB** (weights + KV cache + activations + runtime overhead).
4. **Inference RAM peak at 16 k context ≤ 2.5 GB** (Stage 1/2 rope-extend permitted).
5. **Context window ≤ 16 384 tokens** for the edge variant.
6. **All modality encoders frozen** at inference time (only 1.58-bit projector + trunk forward).
7. **Cumulative encoder footprint ≤ 600 MB** (frozen, summed across all attached modalities).
8. **First-token latency on iPhone 14 (A16, 6 GB) ≤ 3 s** for a 200-token prompt (measured via verified deployment artifact, not theoretical).

If any one of those eight fails, the artifact:

- **MUST NOT** be named with the `baien-` prefix in the registry.
- **MUST NOT** carry `useCases: ["edge", "browser", "cpu"]`.
- **MUST** be renamed to one of the carve-out classes below.

## Carve-out: server-side variants

A model larger than the edge ceiling that derives from baien
architecture (BitNet 1.58 trunk + modality grafts) **may** exist
under a different name + tag set:

| Class | Naming prefix | useCases | Trunk size cap |
|---|---|---|---|
| **baien** (this ADR) | `baien-*` | `["edge", "browser", "cpu", …]` | ≤ 4 B |
| baien-server (M-series Mac / desktop iGPU) | `baien-server-*` | `["server-cpu", "desktop-igpu"]` (NEW useCases) | ≤ 16 B |
| baien-XL (server GPU / data-center) | `baien-XL-*` | `["server-gpu", "datacenter"]` | unlimited |

The `baien-server-*` and `baien-XL-*` classes are **NOT** subject to
this ADR's ceiling. They are out of scope of the edge promise and
do not block the constitutional invariant.

## Frontier-beating non-goal

This ADR makes explicit that **baien-edge is not designed to beat
frontier (Opus 4.7 / GPT-5 / Gemini 2.5 / Qwen3.7-Max) on any
benchmark**. The structural gap between 2 B BitNet edge and
200B-1T+ MoE frontier (per `90-docs/baien/frontier-bench-snapshot-260523.md`
§A) is **3 orders of magnitude in parameters + 2-3 orders in pretrain
compute**.

Realistic baien-edge target per benchmark is **"2 B SOTA"** (best 2 B
model, comparable to Qwen2-VL-2B / Phi-3.5-Mini / SmolVLM-2.2B), not
frontier parity.

`baien-server-*` / `baien-XL-*` may be benchmarked against frontier
in a separate ADR — but this is also explicitly outside scope here.

# Per-component budget table (baien-edge, fully loaded)

Reference deployment = baien 2B trunk + all 4 modalities + 16 k context:

| Component | Size (1.58-bit packed) | Source / status |
|---|---|---|
| baien BitNet 2B-4T trunk | **800 MB** | Microsoft, MIT, today's checkpoint |
| Image encoder — SigLIP-base-patch16-224 (frozen, bf16) | **170 MB** | Google, Apache-2.0, Move 1 today |
| Audio encoder — Whisper-tiny (frozen, bf16) | **80 MB** | OpenAI, MIT, Move 4 candidate |
| Video encoder — VideoMAE-base (frozen, bf16) | **170 MB** | MCG-NJU, CC-BY 4.0, Move 5 candidate |
| 3D encoder — PointTransformer-small (frozen, bf16) | **50 MB** | Various (per-paper license), Move 7 candidate |
| Per-modality 1.58-bit projectors (4 × ~9 M) | **8 MB** | trained by mx-train |
| Tokenizer + runtime overhead | **50 MB** | LLaMA 3 tokenizer + transformers / bitnet.cpp |
| **Weights subtotal** | **1.33 GB** | within 1.6 GB ceiling ✓ |
| KV cache @ 4k ctx (5 KV head × 128 × 30 × bf16 × 2 × 4096) | **300 MB** | |
| KV cache @ 16k ctx | **1.2 GB** | |
| Activations / scratch | **~200 MB** | |
| **Total inference RAM @ 4 k** | **~1.85 GB** | within 2.0 GB ✓ |
| **Total inference RAM @ 16 k** | **~2.75 GB** | **exceeds 2.5 GB by 250 MB** — must drop a modality or use Stage 2 LoRA projector merge |

The 16 k case is on the edge. Practical mitigations within the
ceiling:

- Drop video encoder at 16 k (image+audio+3D = 1.16 GB weights →
  2.66 GB total — still over; need bigger drop).
- Use Stage 2 YaRN with reduced KV head dim (would change config).
- Cap edge multimodal context at **8 k** when all 4 modalities are
  attached (8 k KV ≈ 600 MB → 2.13 GB total within 2.5 GB).

This is the kind of trade-off the invariant forces us to make
explicitly rather than discover at runtime.

# Implications per active ADR / Move

| ADR / Move | Implication of edge invariant |
|---|---|
| ADR-2605092350 (baien design) | unchanged; this ADR codifies what was already implicit |
| ADR-2605101000 (baien-MX surgical Move 2/3) | Move 2 (cross-modal fusion block, +12 M) **OK** within budget; Move 3 (per-modality trunk branches, +30 M) **must verify** cumulative encoder budget after — borderline OK |
| ADR-2605202115 (baien-graft 3D dataset) | unchanged; data-gen pipeline doesn't affect runtime |
| ADR-2605231300 (baien-distill loop) | LoRA adapter merge produces edge-bound trunk; commit_node MUST verify post-merge total ≤ 1.6 GB before flipping `available: true` |
| ADR-2605231600 (rope-extend Stage 1-3) | Stage 1 (16k) **OK** within 2.5 GB; Stage 2 (64k) **drops edge** — becomes `baien-server` variant; Stage 3 (128k) **fully server-only** |
| ADR-2605232500 (Move 1 image graft) | unchanged; SigLIP + projector well within budget |
| (Future) Move 4 audio | Whisper-tiny + projector = **80 MB**, fits trivially |
| (Future) Move 5 video | VideoMAE-base + projector = **170 MB**, fits but pushes 16k headroom |
| (Future) Move 7 3D | PointTransformer-small + projector = **50 MB**, fits trivially |
| (Future) Move 6 robotics | actuation head adds ~5 M params, fits — but simulation / policy training is out of scope of this ADR |
| (Future) agent-coding > frontier | **REJECTED by §"Frontier-beating non-goal"** — pursue under `baien-server-*` if at all |

# Enforcement

## Phase 1 (this ADR, today)

- This ADR is the **single point of reference** when a Move ADR
  proposes a new component or capability.
- All future Move ADRs must include a row in §"Per-component budget"
  showing how the addition fits or what gets traded out.

## Phase 2 (next ADR session)

A lefthook hook + GitHub Action that:

1. Parses `MODEL_REGISTRY` and `MULTIMODAL_MODEL_REGISTRY` for any
   entry with `useCases` containing `"edge"`, `"browser"`, or `"cpu"`.
2. Cross-references to a manifest at `90-docs/baien/edge-fit-attestations.jsonl`
   that records (model_id, packed_weight_bytes, peak_ram_4k_bytes,
   peak_ram_16k_bytes, first_token_latency_iphone14_ms, attesting_council_seat_did).
3. Blocks the commit if any `edge`-tagged entry is missing a recent
   attestation OR an attestation reports values exceeding the §Decision
   ceiling.

Implementation deferred; this ADR is the source of truth that hook
will encode.

## Phase 3 (post-Council, post-Stage 19 of CLAUDE.md Status table)

This invariant moves into `etzhayyim-charters-compliance` on-chain
attestation registry, becoming a Council-attestable rule alongside
Charter Rider §2.

# Permitted deviations

| Deviation | Allowed? | Why |
|---|---|---|
| baien-server-* / baien-XL-* variants larger than 4 B | **Yes** | Out of edge scope; explicit naming + useCases keeps them distinct |
| Per-iter distill LoRA that temporarily exceeds 1.6 GB during training | **Yes** | Training-time only; the **deployed** merged artifact MUST fit ceiling |
| Research/dev branches that hold checkpoints exceeding ceiling | **Yes** | If not in `MODEL_REGISTRY` and not tagged `baien-edge` |
| Adding a modality encoder larger than 200 MB | **Possible** | Must trade out another modality or reduce trunk-context combination to stay under cumulative ceiling |
| Skipping a modality on devices below a memory threshold | **Yes** | Runtime feature flag is fine; what matters is that the **shipped baien-edge artifact** advertises a config that fits everywhere it claims |

# Acceptance criteria (this ADR `proposed → accepted` already met)

1. ✅ §Decision constitutional invariant table is published.
2. ✅ §Per-component budget shows current Move 1 stack fits.
3. ✅ §Implications table maps all active baien ADRs to this ceiling.
4. ⏳ Phase 2 enforcement hook (separate small ADR / runbook).

# References

- ADR-2605092350 baien design (1.58-bit multimodal edge / browser / CPU)
- ADR-2605101000 baien-MX surgical multimodal
- ADR-2605231300 baien-distill loop (commit_node gate target)
- ADR-2605231600 baien context extension (Stage 1/2 edge; Stage 3 non-edge)
- ADR-2605232500 baien Move 1 image graft (within ceiling)
- ADR-2605192100 etzhayyim mission charter (constitutional layer this ADR mirrors)
- Microsoft `bitnet-b1.58-2B-4T-bf16` model card (verified 800 MB packed ternary)
- WebAssembly memory64 status: https://webassembly.org/features/ (still experimental as of 2026-05)
- iOS jetsam behavior reference: Apple "Reducing Your App's Memory Use"
