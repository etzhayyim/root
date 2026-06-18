"""Real ProjectionAdapter (NumPy) — joint embedding (D) → DiT cross-attn context (L×C).

The ONLY trainable module of the graft (encoder frozen, DiT trained). A small MLP that
maps one D-dim joint embedding to L conditioning tokens of width C. Real matmul; seed-
initialised. (The torch trainable twin is in dit_torch.py.)
"""
from __future__ import annotations

import numpy as np


def _gelu(x):
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * x ** 3)))


class ProjectionNP:
    def __init__(self, in_dim: int, context_len: int = 4, context_dim: int = 64, seed: int = 11):
        self.in_dim, self.L, self.C = in_dim, context_len, context_dim
        rng = np.random.default_rng(seed)
        hidden = max(context_len * context_dim, in_dim)
        self.w1 = rng.standard_normal((in_dim, hidden)) * 0.02
        self.b1 = np.zeros(hidden)
        self.w2 = rng.standard_normal((hidden, context_len * context_dim)) * 0.02
        self.b2 = np.zeros(context_len * context_dim)

    def forward(self, z):
        """z [B, in_dim] -> context [B, L, C]."""
        if z.shape[-1] != self.in_dim:
            raise ValueError(f"projection expects dim {self.in_dim}, got {z.shape[-1]}")
        h = _gelu(z @ self.w1 + self.b1) @ self.w2 + self.b2
        return h.reshape(z.shape[0], self.L, self.C)
