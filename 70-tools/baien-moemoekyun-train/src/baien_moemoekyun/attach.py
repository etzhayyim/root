"""Module surgery: attach BaienMoEResidual to a BitNet (or BitNet-shaped) model.

Per ADR-2605262100 §Context: peft is LoRA-class adapter-shaped and unsuitable for
MoE residual (independent computation path). Use direct module replacement instead.

Pattern (from ADR-2605262100 §Context pseudocode):

    for layer_idx in moe_layers:
        layer = model.layers[layer_idx]
        layer.mlp = BitNetFFNWithMoE(
            original_ffn=layer.mlp,                # frozen, forwarded as-is
            moe_branch=BaienMoEResidual(...),
            alpha=nn.Parameter(torch.zeros(1)),    # init=0 (G5)
        )

Forward: y = original_ffn(x) + alpha * moe_branch(x)
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .moe import BaienMoEResidual


class BitNetFFNWithMoE(nn.Module):
    """Wrapper that adds MoE residual branch to an existing FFN module.

    Stores `last_aux_loss` after each forward so the trainer can collect it
    for the load-balancing loss (G6 MANDATORY).
    """

    def __init__(
        self,
        original_ffn: nn.Module,
        moe_branch: BaienMoEResidual,
        alpha_init: float = 0.0,
        alpha_init_jitter: float = 1e-3,
    ):
        super().__init__()
        self.original_ffn = original_ffn  # frozen by caller's requires_grad management
        self.moe_branch = moe_branch
        # G5 MANDATORY: α init = 0.0 ± 1e-3
        init_value = alpha_init + torch.empty(1).uniform_(-alpha_init_jitter, alpha_init_jitter).item()
        self.alpha = nn.Parameter(torch.tensor([init_value], dtype=torch.float32))
        self.last_aux_loss: torch.Tensor | None = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        original_out = self.original_ffn(x)
        moe_out, aux_loss = self.moe_branch(x)
        # Store aux_loss for trainer to collect (cleared each step)
        self.last_aux_loss = aux_loss
        return original_out + self.alpha * moe_out


def attach_moe_to_model(
    model: nn.Module,
    *,
    moe_layer_indices: list[int],
    hidden_size: int,
    intermediate_size: int,
    num_experts: int = 128,
    top_k: int = 2,
    expert_hidden_ratio: int = 32,
    ffn_attribute_name: str = "mlp",
    alpha_init: float = 0.0,
    alpha_init_jitter: float = 1e-3,
    routing_mode: str = "learned",  # "learned" | "distance" (MoCLE-style)
    expert_kind: str = "ffn",  # "ffn" | "memory" (UltraMem-style)
) -> dict[str, BitNetFFNWithMoE]:
    """Walk model.layers, replace `layer.<ffn_attribute_name>` with BitNetFFNWithMoE
    for each layer_idx in moe_layer_indices.

    Args:
        model: HF transformers model (must expose model.layers or model.model.layers)
        moe_layer_indices: 0-based layer indices to install MoE on (R0 default = last 25%)
        hidden_size: model.config.hidden_size
        intermediate_size: model.config.intermediate_size (used to size experts)
        ffn_attribute_name: name of the FFN attribute on each layer module ("mlp" for most HF models, "feed_forward" for some)

    Returns:
        dict mapping "layer.{idx}" -> the installed BitNetFFNWithMoE wrapper
        (useful for trainer to collect aux losses).
    """
    # Locate the layer list
    if hasattr(model, "layers"):
        layers = model.layers
    elif hasattr(model, "model") and hasattr(model.model, "layers"):
        layers = model.model.layers
    else:
        raise ValueError(
            "Could not find `layers` or `model.layers` attribute on model. "
            "For BitNet, model.model.layers is expected (LLaMA-style architecture)."
        )

    installed: dict[str, BitNetFFNWithMoE] = {}
    for idx in moe_layer_indices:
        if idx >= len(layers):
            raise IndexError(f"moe_layer_indices={idx} >= len(layers)={len(layers)}")
        layer = layers[idx]
        if not hasattr(layer, ffn_attribute_name):
            raise AttributeError(
                f"layer {idx} does not have attribute '{ffn_attribute_name}'. "
                f"Available: {[a for a in dir(layer) if not a.startswith('_')][:10]}"
            )
        original_ffn = getattr(layer, ffn_attribute_name)
        moe_branch = BaienMoEResidual(
            hidden_size=hidden_size,
            num_experts=num_experts,
            top_k=top_k,
            intermediate_size=intermediate_size,
            expert_hidden_ratio=expert_hidden_ratio,
            routing_mode=routing_mode,
            expert_kind=expert_kind,
        )
        wrapper = BitNetFFNWithMoE(
            original_ffn=original_ffn,
            moe_branch=moe_branch,
            alpha_init=alpha_init,
            alpha_init_jitter=alpha_init_jitter,
        )
        setattr(layer, ffn_attribute_name, wrapper)
        installed[f"layer.{idx}"] = wrapper

    return installed


def freeze_backbone_verify(
    model: nn.Module,
    installed_moe_wrappers: dict[str, BitNetFFNWithMoE],
) -> dict[str, int]:
    """Freeze all params except those inside the installed MoE wrappers (and per-wrapper alpha).

    Returns trainable/frozen param count summary for G8 acceptance.
    """
    # First freeze everything
    for p in model.parameters():
        p.requires_grad = False

    # Unfreeze MoE branch + alpha for each wrapper
    for name, wrapper in installed_moe_wrappers.items():
        for p in wrapper.moe_branch.parameters():
            p.requires_grad = True
        wrapper.alpha.requires_grad = True
        # Keep wrapper.original_ffn frozen (it inherits from `for p in model.parameters()` above)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen = sum(p.numel() for p in model.parameters() if not p.requires_grad)
    return {"trainable": trainable, "frozen": frozen, "moe_wrappers": len(installed_moe_wrappers)}


def collect_aux_losses(installed_moe_wrappers: dict[str, BitNetFFNWithMoE]) -> torch.Tensor:
    """Sum the per-wrapper last_aux_loss tensors. Caller weights by 0.01 (G6)."""
    losses = []
    for name, wrapper in installed_moe_wrappers.items():
        if wrapper.last_aux_loss is None:
            continue
        losses.append(wrapper.last_aux_loss)
    if not losses:
        return torch.tensor(0.0)
    return torch.stack(losses).sum()
