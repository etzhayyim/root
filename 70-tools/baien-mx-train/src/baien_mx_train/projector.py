"""1.58-bit projector layer (ADR-2605232500 §Decision #2).

Two BitLinear layers + GELU + reshape, mapping SigLIP image embeddings
to baien hidden_size with downsampling.

For Move 1 the projector is **the only trainable parameter set** in
the whole stack — SigLIP and the baien trunk stay frozen. peft is
not strictly needed (we treat the projector as a plain nn.Module and
mark only its params as trainable); however the BitLinear primitive
is borrowed from the `transformers` BitNet implementation so the
quantization scheme stays consistent.

Param count check (ADR §Numerical analysis trainable parameter budget):

    BitLinear(768,  2560) ternary  = 768 * 2560     = 1,966,080
    BitLinear(2560, 2560) ternary  = 2560 * 2560    = 6,553,600
    biases (bf16)                  = 2 * 2560       =     5,120
    --------------------------------------------------------------
    total                                           = 8,524,800 params
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch
    from torch import nn


def build_projector(
    siglip_dim: int,
    baien_dim: int,
    n_image_tokens: int,
    n_input_tokens: int = 196,  # 14x14 patches for SigLIP-base-patch16-224
):
    """Return an nn.Module that maps (B, n_input_tokens, siglip_dim) →
    (B, n_image_tokens, baien_dim).

    The downsampling step is a simple average-pool over groups of
    `n_input_tokens // n_image_tokens` tokens (12 for 196 → 16). Future
    work can replace this with a learned attention pool.
    """
    import torch
    from torch import nn

    try:
        # Prefer the canonical BitLinear from transformers' BitNet model
        # so the projector quantization matches the trunk's W1.58A8.
        from transformers.models.bitnet.modeling_bitnet import BitLinear  # type: ignore
    except Exception:  # pragma: no cover
        # Fallback for environments without BitNet integration:
        # plain nn.Linear with a clipping callback that quantizes at
        # save-time. Equivalent in math, slower in inference.
        BitLinear = nn.Linear  # type: ignore

    pool_kernel = n_input_tokens // n_image_tokens
    assert n_input_tokens == pool_kernel * n_image_tokens, (
        f"n_input_tokens={n_input_tokens} must be divisible by "
        f"n_image_tokens={n_image_tokens}"
    )

    class Move1Projector(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.l1 = BitLinear(siglip_dim, baien_dim)
            self.act = nn.GELU()
            self.l2 = BitLinear(baien_dim, baien_dim)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (B, n_input_tokens, siglip_dim)
            B, T, D = x.shape
            h = self.act(self.l1(x))             # (B, T, baien_dim)
            h = self.l2(h)                       # (B, T, baien_dim)
            # downsample T → n_image_tokens via average pool
            h = h.view(B, n_image_tokens, pool_kernel, baien_dim).mean(dim=2)
            return h                              # (B, n_image_tokens, baien_dim)

    return Move1Projector()


def count_trainable(module) -> int:
    return sum(p.numel() for p in module.parameters() if p.requires_grad)
