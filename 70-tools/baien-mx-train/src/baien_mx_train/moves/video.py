"""Move 5 — video graft (ADR-2605242110).

Edge-on-demand modality: only one of {image, audio, video} active per forward
pass to stay within the ADR-2605241900 cumulative encoder budget (600 MB).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import torch
from torch import nn

VideoTier = Literal["edge", "server", "XL"]


@dataclass(frozen=True)
class VideoModalConfig:
    name: str  # "A" | "B" | "C" | "D"
    n_frames: int
    tokens_per_frame: int
    total_tokens: int
    spatial_res: int  # square HxW
    target_tier: VideoTier


# ADR-2605242110 §Modal configs
_CONFIGS: dict[str, VideoModalConfig] = {
    "A": VideoModalConfig("A", 8, 2, 16, 224, "edge"),
    "B": VideoModalConfig("B", 4, 4, 16, 384, "edge"),
    "C": VideoModalConfig("C", 16, 8, 128, 384, "server"),
    "D": VideoModalConfig("D", 32, 16, 512, 512, "XL"),
}


def permitted_video_modal_config(target_tier: VideoTier, *, name: str | None = None) -> VideoModalConfig:
    """Pick a video modal config compatible with the target tier.

    Edge tier defaults to A (smallest). Server/XL accept explicit `name=`."""
    if target_tier not in ("edge", "server", "XL"):
        raise ValueError(f"unknown tier: {target_tier!r}")
    if name is None:
        name = {"edge": "A", "server": "C", "XL": "D"}[target_tier]
    cfg = _CONFIGS.get(name)
    if cfg is None:
        raise ValueError(f"unknown config: {name!r}")
    # Edge cannot opt into server/XL configs.
    if target_tier == "edge" and cfg.target_tier != "edge":
        raise ValueError(
            f"config {name} (tier={cfg.target_tier}) exceeds edge ceiling; "
            f"see ADR-2605241900 + ADR-2605242100"
        )
    return cfg


def load_videomae_encoder(*, device: str = "cpu", dtype: torch.dtype = torch.bfloat16) -> nn.Module:
    """Load frozen VideoMAE-base encoder. ~340 MB bf16, MIT licensed."""
    from transformers import VideoMAEModel  # imported lazily — heavy

    model = VideoMAEModel.from_pretrained("MCG-NJU/videomae-base", torch_dtype=dtype)
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    return model.to(device)


def sample_frames_uniform(video_tensor: torch.Tensor, n_frames: int) -> torch.Tensor:
    """Uniform-sample `n_frames` from `video_tensor` (T, C, H, W). Returns (n_frames, C, H, W)."""
    t = video_tensor.shape[0]
    if t < n_frames:
        # pad by repeating last frame
        pad = video_tensor[-1:].expand(n_frames - t, *video_tensor.shape[1:])
        return torch.cat([video_tensor, pad], dim=0)
    idx = torch.linspace(0, t - 1, n_frames).long()
    return video_tensor[idx]


def pool_to_tokens(encoded: torch.Tensor, total_tokens: int) -> torch.Tensor:
    """Average-pool encoder output (B, N, D) → (B, total_tokens, D)."""
    b, n, d = encoded.shape
    if n == total_tokens:
        return encoded
    if n % total_tokens != 0:
        # fall back to adaptive avg pool over the sequence axis
        encoded_t = encoded.transpose(1, 2)  # (B, D, N)
        pooled = nn.functional.adaptive_avg_pool1d(encoded_t, total_tokens)
        return pooled.transpose(1, 2)
    stride = n // total_tokens
    return encoded.view(b, total_tokens, stride, d).mean(dim=2)
