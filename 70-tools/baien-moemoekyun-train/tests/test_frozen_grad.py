"""G8 acceptance test: frozen backbone gradients MUST be zero after 1 backward step per ADR-2605262100 §7 R1.2.

Validates the freeze_backbone_verify pattern keeps backbone params frozen while
MoE branch + alpha collect gradients normally.
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn

from baien_moemoekyun import (
    BaienMoEResidual,
    BitNetFFNWithMoE,
    attach_moe_to_model,
    freeze_backbone_verify,
)


class FakeFFN(nn.Module):
    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.gate = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.up = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.down = nn.Linear(intermediate_size, hidden_size, bias=False)

    def forward(self, x):
        return self.down(torch.nn.functional.silu(self.gate(x)) * self.up(x))


class FakeLayer(nn.Module):
    """Mimics a HF transformer layer with .mlp attribute."""

    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.attention = nn.Linear(hidden_size, hidden_size, bias=False)  # placeholder
        self.mlp = FakeFFN(hidden_size, intermediate_size)
        self.norm = nn.LayerNorm(hidden_size)

    def forward(self, x):
        x = x + self.attention(x)
        x = x + self.mlp(x)
        return self.norm(x)


class FakeBitNetLike(nn.Module):
    """Mimics model.model.layers structure of HF LLaMA-class architecture."""

    def __init__(self, hidden_size=128, intermediate_size=512, n_layers=4):
        super().__init__()
        self.layers = nn.ModuleList([FakeLayer(hidden_size, intermediate_size) for _ in range(n_layers)])

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x


def test_freeze_backbone_grad_norm_zero():
    """After 1 backward, backbone params (attention, original_ffn, norm) MUST have zero grad.
    MoE branch + alpha MUST have non-zero grad.
    """
    torch.manual_seed(0)
    hidden = 128
    inter = 512
    model = FakeBitNetLike(hidden, inter, n_layers=4)

    installed = attach_moe_to_model(
        model,
        moe_layer_indices=[2, 3],  # last 2 layers
        hidden_size=hidden,
        intermediate_size=inter,
        num_experts=8,
        top_k=2,
    )
    summary = freeze_backbone_verify(model, installed)
    assert summary["moe_wrappers"] == 2

    # Forward + backward
    x = torch.randn(2, 16, hidden)
    target = torch.randn(2, 16, hidden)
    y = model(x)
    loss = ((y - target) ** 2).mean()
    loss.backward()

    # Backbone (attention + original_ffn inside wrapped layers + norm + non-MoE layers) MUST have grad == 0 or None
    backbone_grad_max = 0.0
    moe_grad_max = 0.0
    alpha_grad_max = 0.0
    for name, p in model.named_parameters():
        if p.grad is None:
            assert not p.requires_grad, f"{name} requires_grad but grad is None"
            continue
        grad_norm = p.grad.abs().max().item()
        if "moe_branch" in name:
            moe_grad_max = max(moe_grad_max, grad_norm)
        elif name.endswith(".alpha"):
            alpha_grad_max = max(alpha_grad_max, grad_norm)
        else:
            backbone_grad_max = max(backbone_grad_max, grad_norm)

    assert backbone_grad_max == 0.0, (
        f"backbone grad max = {backbone_grad_max} (expected 0). "
        "freeze_backbone_verify did NOT correctly freeze backbone params."
    )
    assert moe_grad_max > 0, "MoE branch grad max = 0 (expected non-zero, gradient should flow)"
    assert alpha_grad_max > 0, "alpha grad max = 0 (expected non-zero, gradient should flow)"


def test_param_count_summary_consistent():
    """trainable + frozen MUST equal total."""
    hidden = 128
    inter = 512
    model = FakeBitNetLike(hidden, inter, n_layers=4)
    installed = attach_moe_to_model(
        model, moe_layer_indices=[3], hidden_size=hidden, intermediate_size=inter,
        num_experts=4, top_k=2,
    )
    summary = freeze_backbone_verify(model, installed)
    total = sum(p.numel() for p in model.parameters())
    assert summary["trainable"] + summary["frozen"] == total
    assert summary["trainable"] > 0
    assert summary["frozen"] > 0
