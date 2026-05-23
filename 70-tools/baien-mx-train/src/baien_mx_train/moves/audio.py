"""Move 4 audio loader — ADR-2605241930.

Skeleton: real Whisper-tiny encoder forward + projector wiring is gated
behind `cfg.dry_run` until baien-graft audio data lands. Phase A
(100 LibriSpeech clips) target runtime ~2 min on EVO-X2 CPU.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

# Schema for an audio training row (mirrors GraftRow's image fields,
# kept loose for skeleton). Real loader resolves librispeech / common voice
# manifest files in a follow-up.


def load_audio_input(audio_path: Path, *, device: str = "cpu",
                     dtype: str = "bfloat16"):
    """Stub: load Whisper-tiny mel input from waveform.

    Real impl: torchaudio.load(audio_path) → WhisperProcessor → mel
    spectrogram (1, 80, 3000) → WhisperModel.encoder forward → (1, 1500, 384).
    Stub returns a zero tensor of the right shape so dry-run paths walk.
    """
    import torch
    bf16 = getattr(torch, dtype)
    return torch.zeros((1, 1500, 384), dtype=bf16, device=device)


def whisper_load_real(device: str = "cuda"):
    """Real encoder load (called only when not dry_run).

    Returns (processor, encoder) where `encoder = whisper_model.encoder`
    — we discard the decoder branch since baien IS the decoder."""
    import torch
    from transformers import WhisperModel, WhisperProcessor

    proc = WhisperProcessor.from_pretrained("openai/whisper-tiny")
    full = WhisperModel.from_pretrained(
        "openai/whisper-tiny", dtype=torch.bfloat16,
    ).to(device)
    full.eval()
    return proc, full.encoder
