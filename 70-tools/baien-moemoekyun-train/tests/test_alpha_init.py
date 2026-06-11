"""G5 acceptance test: BitNetFFNWithMoE alpha MUST init to 0.0 ± 1e-3 per ADR-2605262100 §7 R1.1.

Tests the per-layer alpha parameter without requiring BitNet model load
(uses a synthetic FFN substitute).
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn

from baien_moemoekyun import BaienMoEResidual, BitNetFFNWithMoE


class FakeFFN(nn.Module):
    """Synthetic stand-in for a real BitNet FFN (avoids HF download in unit test)."""

    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.gate = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.up = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.down = nn.Linear(intermediate_size, hidden_size, bias=False)

    def forward(self, x):
        return self.down(torch.nn.functional.silu(self.gate(x)) * self.up(x))


@pytest.fixture
def synthetic_wrapper():
    hidden = 256
    inter = 1024
    moe = BaienMoEResidual(
        hidden_size=hidden,
        num_experts=16,
        intermediate_size=inter,
        top_k=2,
    )
    wrapper = BitNetFFNWithMoE(
        original_ffn=FakeFFN(hidden, inter),
        moe_branch=moe,
        alpha_init=0.0,
        alpha_init_jitter=1e-3,
    )
    return wrapper


def test_alpha_init_within_jitter(synthetic_wrapper):
    """G5: alpha init ∈ [-1e-3, +1e-3]."""
    alpha = synthetic_wrapper.alpha.item()
    assert -1.001e-3 <= alpha <= 1.001e-3, f"alpha={alpha} outside ±1e-3 jitter"


def test_alpha_is_trainable(synthetic_wrapper):
    """alpha MUST be a trainable Parameter."""
    assert isinstance(synthetic_wrapper.alpha, nn.Parameter)
    assert synthetic_wrapper.alpha.requires_grad


def test_alpha_init_repeated_within_jitter():
    """Repeated init MUST all stay within ±1e-3."""
    hidden = 128
    inter = 512
    for _ in range(20):
        moe = BaienMoEResidual(hidden, num_experts=4, intermediate_size=inter, top_k=2)
        wrapper = BitNetFFNWithMoE(
            original_ffn=FakeFFN(hidden, inter),
            moe_branch=moe,
        )
        alpha = wrapper.alpha.item()
        assert -1.001e-3 <= alpha <= 1.001e-3, f"alpha={alpha} outside ±1e-3"


def test_alpha_dtype_fp32():
    """alpha kept in fp32 for numerical stability of the gate."""
    hidden = 128
    inter = 512
    moe = BaienMoEResidual(hidden, num_experts=4, intermediate_size=inter, top_k=2)
    wrapper = BitNetFFNWithMoE(
        original_ffn=FakeFFN(hidden, inter),
        moe_branch=moe,
    )
    assert wrapper.alpha.dtype == torch.float32
