---
id: adr-2605241930-baien-mx-move4-audio-graft
title: "Baien Move 4 — audio graft (Whisper-tiny + 1.58-bit projector + frozen baien trunk)"
status: proposed
doc_type: adr
topic: baien-multimodal
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien Move 4 audio architecture
  - Move 4 data sources + license chain
  - Move 4 fit within ADR-2605241900 edge ceiling
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605231300-baien-distill-react-loop
  - adr-2605232500-baien-mx-move1-image-graft-self-training
  - adr-2605241900-baien-edge-target-invariant
related:
  - 70-tools/baien-mx-train/                (extends Move 1 stack to modality=audio)
supersedes: []
superseded_by: []
---

# Goal

Add **audio understanding** to baien (text → text + audio → text + image)
via the same LLaVA-style pattern as Move 1: frozen audio encoder +
trainable 1.58-bit projector + frozen baien trunk.

Move 4 is the cheapest non-image modality to add: Whisper-tiny (39 M
params, 80 MB bf16) is the smallest competent speech encoder, and its
output naturally aligns with the projector pattern.

# Edge fit (per ADR-2605241900)

| Component | Size |
|---|---|
| Whisper-tiny encoder (frozen, bf16) | **80 MB** |
| 1.58-bit projector (audio 384 → baien 2560, ~10 M trainable) | **2 MB** |
| Δ to current Move-1 stack (baien 800 MB + SigLIP 170 MB + image projector 2 MB = 972 MB) | **+82 MB** |
| New cumulative encoder footprint (SigLIP + Whisper-tiny) | **250 MB** (within 600 MB cap ✓) |
| New cumulative inference @ 4 k ctx | **~1.94 GB** (within 2.0 GB ceiling ✓) |
| New cumulative inference @ 16 k ctx | **~2.84 GB** (exceeds 2.5 GB ⚠️ — must cap to 8 k OR drop image at 16 k) |

# Decision

| Pin | Value |
|---|---|
| Audio encoder | **`openai/whisper-tiny`** (39 M params, MIT, output `(1, 1500, 384)`) |
| Frozen at | inference + projector training time |
| Projector input dim | 384 |
| Projector output dim | 2560 (baien hidden) |
| Projector layers | 2 × BitLinear + GELU (mirrors Move 1) |
| Downsample target | **16 audio tokens** (1500 / 16 = 93 per token, average-pool) |
| Chat-template insertion | `<audio>` placeholder token (new special, vocab+1, same forward-hook substitution as Move 1's `<image>`) |
| Loss mask | mask all `<audio>` token positions to -100 |
| First training data | LibriSpeech-clean dev (CC-BY 4.0, ~9 hr) + Common Voice ja sample (CC0, JP carve-out) |

# Numerical analysis

## Trainable parameters

```
BitLinear(384,  2560)  ternary  = 384 * 2560     =   983,040
BitLinear(2560, 2560)  ternary  = 2560 * 2560    = 6,553,600
biases (bf16)                   = 2 * 2560       =     5,120
───────────────────────────────────────────────────────────
total trainable                 = 7,541,760 params (~0.4% trunk)
```

≈ 1.4 MB on-disk packed — shippable to edge with same i2_s scheme.

## Training-time budget on EVO-X2

Audio rows are ~30 s each in LibriSpeech, mel features compute ~50 ms,
Whisper encoder ~150 ms, projector + baien forward ~600 ms (similar to
Move 1). Per-row ~1 s. Per-step (grad_accum 4) ~4 s.

| Phase | rows | epochs | steps | wall (CPU) | wall (ROCm 2.3×) |
|---|---|---|---|---|---|
| A smoke | 100 | 1 | 25 | ~2 min | ~1 min |
| B bootstrap | 1 000 | 3 | 750 | ~50 min | ~22 min |
| C scale | 10 000 | 3 | 7 500 | ~8 h | ~3.5 h |

## Eval (`audio_microbench`)

5 verifiable audio prompts (proposed, all rule-based scorers):

| id | input | prompt | scorer |
|---|---|---|---|
| amb_transcribe | LibriSpeech-test clip | "Transcribe this audio. One line." | edit-distance against ground truth ≤ 20% |
| amb_lang_id | mixed en/ja clip | "What language is spoken? One word." | exact `english` or `japanese` |
| amb_speaker_count | 1-2 speaker clip | "How many speakers? Single digit." | regex `[12]` matches ground truth |
| amb_noise | noisy clip | "Is there background noise? yes/no." | yes/no regex matches GT |
| amb_yesno_simple | "is the sky blue?" speech | "Answer the question in the audio. yes/no only." | yes/no |

Move 4 gate (analogous to Move 1):
- audio_microbench ≥ 60% (3/5)
- text + image microbench regression Δ ≥ -3 pp each (no cross-modal hurt)

# Data source

Per ADR-2605231300 §3a / ADR-2605202115 (data-source decision pattern):

| Dataset | License | Use |
|---|---|---|
| **LibriSpeech-clean dev/test** | **CC-BY 4.0** | EN transcription + lang-id positive samples |
| **Mozilla Common Voice 17 (`ja` subset)** | **CC0-1.0** | JA transcription + lang-id negative samples |
| **AudioSet eval (small subset)** | YouTube-derived, **non-redistributable** — only use if streaming at eval time, never bundle | bg noise + speaker count |

LibriSpeech + Common Voice covers all 5 audio_microbench prompts
cleanly with Charter-Rider-compatible licenses.

# Skeleton (extends `70-tools/baien-mx-train/`)

Directory plan (additive, no rewrite of Move 1):

```
70-tools/baien-mx-train/src/baien_mx_train/
├── moves/                               (NEW)
│   ├── __init__.py
│   ├── image.py                         (Move 1 — refactor target, optional)
│   ├── audio.py                         (NEW — this ADR)
│   └── three_d.py                       (NEW — ADR-2605241940)
├── adapters/modality.py                 (NEW — registry of (encoder, processor, dim))
```

`adapters/modality.py`:

```python
MODALITY_REGISTRY = {
    "image": ModalitySpec(
        encoder_id="google/siglip-base-patch16-224",
        encoder_class="SiglipVisionModel",
        processor_class="AutoProcessor",
        output_dim=768, n_input_tokens=196,
        placeholder_token="<image>",
        n_target_tokens=14,  # 196/14
    ),
    "audio": ModalitySpec(
        encoder_id="openai/whisper-tiny",
        encoder_class="WhisperModel",          # use .encoder only at inference
        processor_class="WhisperProcessor",
        output_dim=384, n_input_tokens=1500,
        placeholder_token="<audio>",
        n_target_tokens=16,                    # 1500/16 ≈ 93 per token
    ),
    "three_d": ModalitySpec(...),              # ADR-2605241940
}
```

Trainer dispatch: `train(state, modality="audio")` selects from
registry. The Move 1 train.py is unchanged in behavior (defaults to
`modality="image"`); Move 4 just invokes the registry with `"audio"`.

# Implications

- Move 4 ships within the edge invariant (verified above).
- Move 4 introduces a new chat-template special token (`<audio>`).
  Special-token planning table in ADR-2605232500 §"Open issues" applies.
- `baien_prompt --audio path/to.wav` (mirror of `--image`) becomes the
  ad-hoc inference path post-training.

# Acceptance criteria

1. `70-tools/baien-mx-train/src/baien_mx_train/moves/audio.py` exists with
   the data loader + projector wiring (skeleton).
2. `adapters/modality.py` MODALITY_REGISTRY includes "audio".
3. `e7m bench mx-train --modality audio --phase A --dry-run` walks the
   trainer setup without loading Whisper / baien.
4. ADR-2605241900 §"Per-component budget" includes the audio row
   (already does).

# References

- Whisper-tiny: https://huggingface.co/openai/whisper-tiny (MIT, 39M, vision/audio-tower-only via WhisperModel.encoder)
- LibriSpeech: https://www.openslr.org/12/ (CC-BY 4.0)
- Common Voice 17: https://commonvoice.mozilla.org/ja/datasets (CC0)
- ADR-2605241900 baien edge-target invariant
- ADR-2605232500 Move 1 image graft (same pattern, swap encoder)
