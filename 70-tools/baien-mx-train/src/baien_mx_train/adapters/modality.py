"""Modality registry per ADR-2605241930 (Move 4 audio) + ADR-2605241940 (Move 7 3D)
+ ADR-2605242110 (Move 5 video) + ADR-2605242120 (Move 6 robotics scene).

Each modality plugs into baien via the same LLaVA-style pattern:

    frozen encoder → 1.58-bit projector (n_input_tokens → n_target_tokens × baien_dim)
                  → forward-hook substitution at <placeholder> positions in input_ids
                  → frozen baien trunk → text response

Adding a new modality = appending a `ModalitySpec` row here + 1 file
under `moves/<modality>.py` that defines the per-modality data loader.

All edge-eligible encoders MUST satisfy ADR-2605241900 ceilings. Video is
edge-on-demand: counted against the cumulative encoder budget only when
loaded (mutually exclusive with image / audio at edge tier — see
ADR-2605242110 §"Edge fit math"). Robotics scene reuses Move 1's image
encoder; no new runtime encoder weights.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModalitySpec:
    name: str                            # "image" / "audio" / "video" / "three_d"
    encoder_id: str                      # HF id; "" if input is already a latent (e.g. Pixal3D SLAT)
    encoder_class: str                   # transformers class name
    processor_class: str                 # transformers class name; "" if no processor needed
    encoder_size_bytes: int              # frozen footprint in bf16 — counts against ADR-2605241900 600 MB cap
    output_dim: int                      # encoder hidden dim
    n_input_tokens: int                  # encoder output token count
    n_target_tokens: int                 # projector downsamples to this
    placeholder_token: str               # special token added to baien tokenizer
    license: str                         # SPDX-ish
    license_compat_note: str             # short note re: Charter Rider §2 compatibility


MODALITY_REGISTRY: dict[str, ModalitySpec] = {
    "image": ModalitySpec(
        name="image",
        encoder_id="google/siglip-base-patch16-224",
        encoder_class="SiglipVisionModel",
        processor_class="AutoProcessor",
        encoder_size_bytes=170 * 1024 * 1024,
        output_dim=768,
        n_input_tokens=196,               # 14×14 patches @ 224×224
        n_target_tokens=14,               # 196 / 14
        placeholder_token="<image>",
        license="apache-2.0",
        license_compat_note="Clean Apache-2.0; no Charter Rider §2 review needed for derivative weights.",
    ),
    "audio": ModalitySpec(
        name="audio",
        encoder_id="openai/whisper-tiny",
        encoder_class="WhisperModel",     # use .encoder branch only at inference
        processor_class="WhisperProcessor",
        encoder_size_bytes=80 * 1024 * 1024,
        output_dim=384,
        n_input_tokens=1500,              # 30s × 50 frames/s (mel)
        n_target_tokens=16,
        placeholder_token="<audio>",
        license="mit",
        license_compat_note="MIT (OpenAI Whisper); fully compatible with Apache-2.0 + Rider.",
    ),
    "three_d": ModalitySpec(
        name="three_d",
        encoder_id="",                    # Pixal3D SLAT is already a latent (no extra encoder at inference)
        encoder_class="",
        processor_class="",
        encoder_size_bytes=0,
        output_dim=128,                   # Pixal3D-T SLAT feat dim — TBD verify
        n_input_tokens=128,               # SLAT latent length — TBD verify
        n_target_tokens=14,
        placeholder_token="<three_d>",
        license="see-TencentARC-Pixal3D-T-card",
        license_compat_note=(
            "Pixal3D-T license review per ADR-2605202115 amendment 2026-05-23. "
            "OK for internal experimentation; verify before any first-party redistribution."
        ),
    ),
    "video": ModalitySpec(
        name="video",
        encoder_id="MCG-NJU/videomae-base",
        encoder_class="VideoMAEModel",
        processor_class="VideoMAEImageProcessor",
        # Counted only when loaded (edge tier = on-demand; mutually exclusive
        # with image / audio per ADR-2605242110 §"Edge fit math"). The 340 MB
        # exceeds the 600 MB ceiling when summed with all other modalities;
        # runtime loader enforces on-demand swap.
        encoder_size_bytes=340 * 1024 * 1024,
        output_dim=768,
        n_input_tokens=1568,              # 8 frames × 196 patches @ 224 (config A default)
        n_target_tokens=16,               # config A default — server/XL configs override at runtime
        placeholder_token="<video>",
        license="mit",
        license_compat_note=(
            "MIT (MCG-NJU VideoMAE); fully compatible with Apache-2.0 + Rider. "
            "Per-config token counts: A=16/B=16/C=128/D=512 — see "
            "moves/video.permitted_video_modal_config()."
        ),
    ),
    "robotics_scene": ModalitySpec(
        name="robotics_scene",
        # Edge tier reuses Move 1's image encoder; no new runtime weights.
        # (See ADR-2605242120 §"Modality registry entries".)
        encoder_id="google/siglip-base-patch16-224",
        encoder_class="SiglipVisionModel",
        processor_class="AutoProcessor",
        encoder_size_bytes=0,             # reuses image encoder budget; not double-counted
        output_dim=768,
        n_input_tokens=196,
        n_target_tokens=14,
        placeholder_token="<image>",      # reuses <image> placeholder; no new special token
        license="apache-2.0",
        license_compat_note=(
            "Edge tier reuses Move 1 SigLIP (Apache-2.0). Server-tier action "
            "head (`robotics_action`) is gated post-Council per ADR-2605242120 "
            "§Safety rationale and is NOT registered here."
        ),
    ),
}


def total_edge_encoder_bytes() -> int:
    """Sum of encoder weights for all modalities in the registry.

    Compared against ADR-2605241900 §Decision rule 7 (≤ 600 MB cumulative
    encoder footprint)."""
    return sum(spec.encoder_size_bytes for spec in MODALITY_REGISTRY.values())
