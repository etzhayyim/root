---
id: adr-2605242110-baien-mx-move5-video-graft
title: "Baien Move 5 — video graft (VideoMAE-base + 1.58-bit projector + on-demand modality)"
status: accepted
doc_type: adr
topic: baien-multimodal
authoritative: true
last_verified: 2026-05-24
authoritative_for:
  - baien Move 5 video architecture
  - Move 5 modal configs (A edge default / B edge HD / C server / D XL)
  - on-demand modality loading rule (edge tier)
  - Move 5 fit within ADR-2605241900 edge ceiling via on-demand swap
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605231300-baien-distill-react-loop
  - adr-2605232500-baien-mx-move1-image-graft-self-training
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605241930-baien-mx-move4-audio-graft
  - adr-2605241940-baien-mx-move7-3d-graft
  - adr-2605242100-baien-server-xl-carve-out
related:
  - 70-tools/baien-mx-train/src/baien_mx_train/moves/video.py
supersedes: []
superseded_by: []
---

# Context

baien Moves 1 (image), 4 (audio), and 7 (3D) fit within the
ADR-2605241900 cumulative encoder budget when all simultaneously
loaded:

| Move | Encoder | Size |
|---|---|---|
| 1 image | SigLIP-base-patch16-224 (Apache-2.0, frozen) | 170 MB (380 MB cited in spec; both consistent with bf16 vs alternative packing) |
| 4 audio | Whisper-tiny (MIT, frozen) | 80 MB |
| 7 3D | Pixal3D SLAT — no extra runtime encoder | 0 MB |

Adding video pushes the cumulative encoder footprint over the
600 MB ceiling. This ADR makes the architectural choice to keep video
in scope **on the edge tier** via an on-demand load rule, with explicit
opt-in to the heavier server/XL configurations via the ADR-2605242100
carve-out.

# Decision

| Pin | Value |
|---|---|
| Video encoder | **`MCG-NJU/videomae-base`** (86 M params, MIT, ~340 MB bf16) |
| Frozen at | inference + projector training time |
| Projector | 1.58-bit BitLinear (same 2-layer pattern as Move 1) |
| Default token count (edge) | **16 video tokens** |
| Chat-template placeholder | `<video>` (single placeholder; token expansion via forward hook on `embed_tokens`, mirroring `<image>` / `<audio>`) |
| Loss mask | mask all `<video>` positions to -100 (loss on assistant turn only) |

## Modal configs

Four runtime-selectable configurations:

| Config | Frames | Spatial tokens/frame | Total video tokens | Input res | Target tier |
|---|---|---|---|---|---|
| **A (edge default)** | 8 | 2 | 16 | 224 × 224 | edge |
| **B (edge HD)** | 4 | 4 | 16 | 384 × 384 | edge |
| **C (server)** | 16 | 8 | 128 | 384 × 384 | server |
| **D (XL)** | 32 | 16 | 512 | 512 × 512 | XL |

Runtime picker:

```python
def permitted_video_modal_config(
    target_tier: Literal["edge", "server", "XL"],
    *, name: str | None = None,
) -> VideoModalConfig
```

Returns the `VideoModalConfig` (n_frames, tokens_per_frame, total
tokens, spatial res). Raises `ValueError` for unknown tiers. Edge
tier defaults to config A (smallest); explicit `name=` accepted on
server/XL. Edge tier cannot opt into C/D (would breach the ceiling).

## Edge fit math

VideoMAE 340 MB + 1.58-bit projector ≤ 8 MB = **≤ 348 MB**.

Cumulative across all 4 modalities after Move 5:

| Move | Encoder | bf16 size |
|---|---|---|
| 1 image | SigLIP-base | 380 MB |
| 4 audio | Whisper-tiny | 80 MB |
| 7 3D | Pixal3D SLAT (no runtime encoder) | 0 MB |
| 5 video | VideoMAE-base | 340 MB (incl. projector ≤ 348 MB) |
| **Cumulative** | | **808 MB** |

**808 MB exceeds the 600 MB cumulative-encoder ceiling per
ADR-2605241900 §Decision rule 7.**

**Resolution**: edge runtime loads modalities **on-demand** — only
one of {image, audio, video} is resident in RAM at a time. The 3D
path has no runtime encoder, so it stays free. Simultaneous
image + video forward is **server tier only** (see ADR-2605242100).

The on-demand rule lives in the runtime loader (not in the
projector / trainer), so training-time the budget can be inspected
modality by modality without runtime trickery.

## Training data

| Phase | Rows | Dataset | License gate |
|---|---|---|---|
| **A** | 100 | HMDB51 / UCF101-tiny subset | CC-BY-NC-SA — Charter Rider §2 review for NC clause; if NC blocks, fall back to public-domain Open Video Dataset |
| **B** | 1 000 | Kinetics-400 train split | per-clip YouTube license (non-redistributable; stream-only at training time) |
| **C** | 10 000 | WebVid-10M filtered through `etzhayyim_organism.sensors.charter_rider.scan()` | clean subset only |

The Charter Rider scanner is mandatory at the data-fetcher boundary
for video, where adversarial-content frequencies are higher than for
LibriSpeech-class audio.

## Self-training loop

Same ReAct pattern as ADR-2605231300 distill:

```
analyze → fetch_dataset (HF, with charter_rider.scan filter)
        → SFT (projector only, trunk + encoder frozen)
        → microbench eval
        → commit_node (append `90-docs/baien/multimodal-models.jsonl`)
```

Forward hook: `<video>` placeholder consumes N tokens (per active
config), forward hook on `embed_tokens` substitutes
`projector(video_encoder(frames))` at positions `[0:N]`. Mirrors
ADR-2605232500 §"Chat template extension" exactly for the image case.

## Eval (`video_microbench`)

5 verifiable video prompts (proposed; all rule-based):

| id | input | prompt | scorer |
|---|---|---|---|
| vmb_action | HMDB51 clip (e.g. wave) | "What action is performed? One word." | substring action label |
| vmb_object_count | object-count clip | "How many distinct objects appear? Single digit." | regex `[1-9]` matches GT |
| vmb_motion_dir | left-right vs right-left | "Which direction does the primary subject move? left, right, up, down." | exact GT |
| vmb_static_dynamic | static-shot vs dynamic | "Is the camera static or moving? Reply with one word." | substring `static` or `moving` |
| vmb_indoor_outdoor | indoor vs outdoor | "Is the scene indoor or outdoor? One word." | substring GT |

Move 5 gate (analogous to Move 1):
- `video_microbench` pass ≥ 60 % (3/5)
- text + image + audio microbench regression Δ ≥ -3 pp each

# Consequences

- **Edge ships with on-demand modality loader** — runtime contract: at
  most one of {image, audio, video} resident at any moment. Image
  encoder + audio encoder + video encoder all live on disk but only
  one is mmapped + decoded into RAM. 3D SLAT is always free.
- **Server/XL configs unblock dense video** — config C (server) and
  D (XL) live under `baien-server-*` / `baien-XL-*` per ADR-2605242100
  with no ceiling concerns.
- **Single `<video>` placeholder** keeps tokenizer growth minimal
  (one new special token per Move, not per config).
- **Move 5 → Move 6 (robotics) wiring** — Move 6's server tier
  multi-modal observation bundle can reuse Move 5's video encoder
  + Move 1's image encoder, but only at server tier (edge tier of
  Move 6 is image-only scene description, see ADR-2605242120).

# Alternatives Considered

1. **Drop video entirely from edge.** Rejected — video understanding
   is a primary user-visible capability for the assistant role; the
   on-demand rule is a clean compromise.
2. **Use a smaller video encoder (e.g. TimeSformer-mini).** Rejected
   — VideoMAE-base is the smallest self-supervised video transformer
   with credible benchmark numbers in the 2026-class literature, and
   its MIT license is clean. A future ADR can swap in a smaller
   encoder if one emerges.
3. **One placeholder token per frame.** Rejected — token expansion
   should happen at the forward hook (consistent with image / audio),
   not in the tokenizer; per-frame placeholders bloat input_ids and
   complicate the chat template.
4. **Allow simultaneous image + video at edge.** Rejected — would
   require shrinking either encoder past the point of meaningful
   accuracy.

# Non-goals

- **Text-to-video generation**, **video editing**, **video-as-output**
  — Move 5 is **video-IN** only. Move 5's text head produces text
  (e.g. action labels, captions, Q&A answers); generative video
  output is out of scope and would require a separate ADR.
- **Real-time video stream** at edge — Move 5 expects a clip-bounded
  input (8-32 frames depending on config). Stream-mode (rolling
  window) is a future runtime concern.
- **Frontier video VLM parity** — see ADR-2605241900 §"Frontier-beating
  non-goal" and ADR-2605242100 §"Non-goals". Move 5 targets "2 B SOTA"
  on video QA, not frontier parity.

# References

- ADR-2605241900 — baien edge-target invariant (the ceiling Move 5
  has to respect via on-demand loading)
- ADR-2605242100 — baien-server / baien-XL carve-out (where configs
  C/D live)
- ADR-2605232500 — Move 1 image graft (architectural pattern + chat
  template + forward hook reused here)
- ADR-2605241930 — Move 4 audio graft (sibling Move; same pattern)
- ADR-2605241940 — Move 7 3D graft (sibling Move; no runtime encoder)
- ADR-2605231300 — baien-distill ReAct loop (training loop reused)
- VideoMAE: https://huggingface.co/MCG-NJU/videomae-base
- HMDB51: https://serre-lab.clps.brown.edu/resource/hmdb-a-large-human-motion-database/
- Kinetics-400: https://deepmind.com/research/open-source/kinetics
- WebVid-10M: https://m-bain.github.io/webvid-dataset/
