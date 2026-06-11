"""R1.1 test: optimizer MUST have 3 param groups with router/experts/alpha LR per ADR-2605262100 §4."""

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
from baien_moemoekyun.trainer import build_optimizer, split_moe_param_groups


class FakeFFN(nn.Module):
    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.gate = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.up = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.down = nn.Linear(intermediate_size, hidden_size, bias=False)

    def forward(self, x):
        return self.down(torch.nn.functional.silu(self.gate(x)) * self.up(x))


class FakeLayer(nn.Module):
    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.attention = nn.Linear(hidden_size, hidden_size, bias=False)
        self.mlp = FakeFFN(hidden_size, intermediate_size)

    def forward(self, x):
        return x + self.mlp(x + self.attention(x))


class FakeBitNetLike(nn.Module):
    def __init__(self, hidden_size=128, intermediate_size=512, n_layers=4):
        super().__init__()
        self.layers = nn.ModuleList([FakeLayer(hidden_size, intermediate_size) for _ in range(n_layers)])

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x


@pytest.fixture
def attached_model():
    torch.manual_seed(0)
    hidden = 128
    inter = 512
    model = FakeBitNetLike(hidden, inter, n_layers=4)
    installed = attach_moe_to_model(
        model,
        moe_layer_indices=[2, 3],
        hidden_size=hidden,
        intermediate_size=inter,
        num_experts=8,
        top_k=2,
    )
    freeze_backbone_verify(model, installed)
    return model, installed


def test_split_param_groups_correct_counts(attached_model):
    model, installed = attached_model
    router_p, expert_p, alpha_p = split_moe_param_groups(installed)
    assert len(router_p) == 2  # 2 layers x 1 router each (weight only, no bias)
    # 2 layers × 8 experts × 2 linear layers (no bias) = 32 tensors
    assert len(expert_p) == 32
    assert len(alpha_p) == 2  # 2 layers × 1 alpha each


def test_build_optimizer_three_groups_with_correct_lr(attached_model):
    model, installed = attached_model
    opt = build_optimizer(
        installed,
        lr_router=1e-4,
        lr_experts=2e-4,
        lr_alpha=5e-5,
    )
    assert len(opt.param_groups) == 3
    groups_by_name = {g.get("name"): g for g in opt.param_groups}
    assert "router" in groups_by_name
    assert "experts" in groups_by_name
    assert "alpha" in groups_by_name
    assert groups_by_name["router"]["lr"] == 1e-4
    assert groups_by_name["experts"]["lr"] == 2e-4
    assert groups_by_name["alpha"]["lr"] == 5e-5
    assert groups_by_name["router"]["betas"] == (0.9, 0.95)
    assert groups_by_name["router"]["weight_decay"] == 0.1


def test_optimizer_groups_disjoint(attached_model):
    """No param should appear in more than one group."""
    model, installed = attached_model
    opt = build_optimizer(installed)
    all_param_ids = []
    for g in opt.param_groups:
        for p in g["params"]:
            all_param_ids.append(id(p))
    assert len(all_param_ids) == len(set(all_param_ids)), "param appears in multiple groups"


def test_optimizer_groups_cover_all_trainable(attached_model):
    """All trainable params (requires_grad=True) MUST be in some group."""
    model, installed = attached_model
    opt = build_optimizer(installed)
    in_opt_ids = set()
    for g in opt.param_groups:
        for p in g["params"]:
            in_opt_ids.add(id(p))
    trainable_ids = {id(p) for p in model.parameters() if p.requires_grad}
    missing = trainable_ids - in_opt_ids
    assert not missing, f"{len(missing)} trainable params NOT in optimizer groups"


def test_optimizer_excludes_frozen_backbone(attached_model):
    """Backbone params (requires_grad=False) MUST NOT be in any group."""
    model, installed = attached_model
    opt = build_optimizer(installed)
    in_opt_ids = set()
    for g in opt.param_groups:
        for p in g["params"]:
            in_opt_ids.add(id(p))
    frozen_ids = {id(p) for p in model.parameters() if not p.requires_grad}
    overlap = frozen_ids & in_opt_ids
    assert not overlap, f"{len(overlap)} frozen params accidentally in optimizer groups"
