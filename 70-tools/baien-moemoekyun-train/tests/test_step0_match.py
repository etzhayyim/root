"""G5 acceptance test (extended): at step-0, BitNetFFNWithMoE forward output MUST
match the original FFN output within ‖Δ‖_2 / ‖y_base‖_2 < 0.01 per ADR-2605262100 §7 R1.1.

This validates the constitutional invariant that α=0 init means the model behaves
identically to base BitNet at step-0 (loss curve match within 1% per ADR-2605261900 G5).
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn

from baien_moemoekyun import BaienMoEResidual, BitNetFFNWithMoE


class FakeFFN(nn.Module):
    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.gate = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.up = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.down = nn.Linear(intermediate_size, hidden_size, bias=False)

    def forward(self, x):
        return self.down(torch.nn.functional.silu(self.gate(x)) * self.up(x))


@pytest.mark.parametrize("seed", [42, 123, 2026])
def test_step0_forward_match_within_1pct(seed):
    """For random input, ‖wrapped_out - original_out‖_2 / ‖original_out‖_2 < 0.01."""
    torch.manual_seed(seed)
    hidden = 256
    inter = 1024
    batch = 2
    seq = 32

    ffn = FakeFFN(hidden, inter)
    moe = BaienMoEResidual(
        hidden_size=hidden,
        num_experts=32,
        intermediate_size=inter,
        top_k=2,
    )
    wrapper = BitNetFFNWithMoE(
        original_ffn=ffn,
        moe_branch=moe,
        alpha_init=0.0,
        alpha_init_jitter=1e-3,
    )

    x = torch.randn(batch, seq, hidden)
    with torch.no_grad():
        y_base = ffn(x)
        y_wrapped = wrapper(x)

    delta_norm = (y_wrapped - y_base).norm()
    base_norm = y_base.norm()
    rel_delta = (delta_norm / (base_norm + 1e-9)).item()

    assert rel_delta < 0.01, (
        f"seed={seed}: ‖Δ‖_2 / ‖y_base‖_2 = {rel_delta:.6f} >= 0.01 "
        "(G5 step-0 match violated; check α init or MoE branch output magnitude)"
    )


def test_alpha_zero_means_exact_match():
    """If we force α=0 exactly, output MUST equal base FFN exactly (fp32)."""
    torch.manual_seed(0)
    hidden = 128
    inter = 512
    ffn = FakeFFN(hidden, inter)
    moe = BaienMoEResidual(hidden, num_experts=8, intermediate_size=inter, top_k=2)
    wrapper = BitNetFFNWithMoE(original_ffn=ffn, moe_branch=moe, alpha_init=0.0, alpha_init_jitter=0.0)

    # Force alpha to exactly 0
    with torch.no_grad():
        wrapper.alpha.zero_()
    assert wrapper.alpha.item() == 0.0

    x = torch.randn(1, 8, hidden)
    with torch.no_grad():
        y_base = ffn(x)
        y_wrapped = wrapper(x)

    # bit-exact (no MoE contribution, just original_ffn)
    assert torch.allclose(y_base, y_wrapped, rtol=0, atol=0)
