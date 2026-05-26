"""BaienMoEMoekyunTrainer — trl SFTTrainer subclass with:
  - per-group LR (router 1e-4 / experts 2e-4 / alpha 5e-5)  per ADR-2605262100 §4
  - aux_loss collection from BitNetFFNWithMoE wrappers      per G6 MANDATORY (w ∈ [0.001, 0.1])

R1.1 fully realized deliverable.
"""

from __future__ import annotations

import logging
from typing import Any

import torch
import torch.nn as nn
from torch.optim import AdamW

from .attach import BitNetFFNWithMoE, collect_aux_losses

logger = logging.getLogger("baien-moemoekyun.trainer")


def split_moe_param_groups(
    moe_wrappers: dict[str, BitNetFFNWithMoE],
) -> tuple[list[nn.Parameter], list[nn.Parameter], list[nn.Parameter]]:
    """Split trainable MoE params into (router, experts, alpha) for per-group LR.

    Returns three lists of nn.Parameter ready to feed AdamW param groups.

    Per ADR-2605261900 §4 Phase 0:
      - router: 1e-4
      - experts: 2e-4
      - alpha: 5e-5
    """
    router_params: list[nn.Parameter] = []
    expert_params: list[nn.Parameter] = []
    alpha_params: list[nn.Parameter] = []

    for wrapper in moe_wrappers.values():
        # router = the linear projection inside moe_branch
        router_params.append(wrapper.moe_branch.router.weight)
        if wrapper.moe_branch.router.bias is not None:
            router_params.append(wrapper.moe_branch.router.bias)

        # experts = all params in moe_branch.experts (the ModuleList of small FFNs)
        for p in wrapper.moe_branch.experts.parameters():
            expert_params.append(p)

        # alpha = per-wrapper scalar Parameter
        alpha_params.append(wrapper.alpha)

    return router_params, expert_params, alpha_params


def build_optimizer(
    moe_wrappers: dict[str, BitNetFFNWithMoE],
    *,
    lr_router: float = 1.0e-4,
    lr_experts: float = 2.0e-4,
    lr_alpha: float = 5.0e-5,
    betas: tuple[float, float] = (0.9, 0.95),
    weight_decay: float = 0.1,
) -> AdamW:
    """Per ADR-2605262100 §4 Phase 0 hyperparameters."""
    router_p, expert_p, alpha_p = split_moe_param_groups(moe_wrappers)
    logger.info(
        "Optimizer param groups: router=%d experts=%d alpha=%d",
        sum(p.numel() for p in router_p),
        sum(p.numel() for p in expert_p),
        sum(p.numel() for p in alpha_p),
    )
    return AdamW(
        [
            {"params": router_p, "lr": lr_router, "name": "router"},
            {"params": expert_p, "lr": lr_experts, "name": "experts"},
            {"params": alpha_p, "lr": lr_alpha, "name": "alpha"},
        ],
        betas=betas,
        weight_decay=weight_decay,
    )


class BaienMoEMoekyunTrainer:
    """trl SFTTrainer subclass — instantiated only when trl is available.

    Use the factory `make_trainer()` below to construct (handles trl import +
    SFTTrainer subclassing in one place).
    """


def make_trainer(
    model: nn.Module,
    tokenizer: Any,
    train_dataset: Any,
    sft_config: Any,
    *,
    moe_wrappers: dict[str, BitNetFFNWithMoE],
    lr_router: float = 1.0e-4,
    lr_experts: float = 2.0e-4,
    lr_alpha: float = 5.0e-5,
    aux_loss_weight: float = 0.01,
    optimizer_betas: tuple[float, float] = (0.9, 0.95),
    optimizer_weight_decay: float = 0.1,
):
    """Construct a BaienMoEMoekyunTrainer (SFTTrainer subclass) with per-group LR + aux_loss.

    Returns the trainer instance. Caller invokes `.train()` and `.save_model()`.
    """
    try:
        from trl import SFTTrainer
    except ImportError as e:
        raise ImportError(
            "trl>=0.11 required for training; install via `pip install trl>=0.11`. "
            f"Original error: {e}"
        )

    # G6 MANDATORY: aux_loss_weight ∈ [0.001, 0.1]
    if not (0.001 <= aux_loss_weight <= 0.1):
        raise ValueError(
            f"aux_loss_weight={aux_loss_weight} outside [0.001, 0.1] range "
            "per ADR-2605261900 §5 G6 + ADR-2605262100 §4."
        )

    class _BaienTrainer(SFTTrainer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Stash for compute_loss + create_optimizer
            self._moe_wrappers = moe_wrappers
            self._aux_loss_weight = aux_loss_weight
            self._lr_router = lr_router
            self._lr_experts = lr_experts
            self._lr_alpha = lr_alpha
            self._optimizer_betas = optimizer_betas
            self._optimizer_weight_decay = optimizer_weight_decay
            # Bookkeeping for logging
            self._last_lm_loss: float = 0.0
            self._last_aux_loss: float = 0.0

        def create_optimizer(self):
            """Override to use per-group LR (router / experts / alpha)."""
            if self.optimizer is not None:
                return self.optimizer
            self.optimizer = build_optimizer(
                self._moe_wrappers,
                lr_router=self._lr_router,
                lr_experts=self._lr_experts,
                lr_alpha=self._lr_alpha,
                betas=self._optimizer_betas,
                weight_decay=self._optimizer_weight_decay,
            )
            return self.optimizer

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            """Override to add aux_loss * w to LM loss (G6 MANDATORY)."""
            outputs = model(**inputs)
            lm_loss = outputs.loss if hasattr(outputs, "loss") else outputs[0]

            # Collect aux losses from all MoE wrappers (G6)
            aux_loss = collect_aux_losses(self._moe_wrappers)
            # Ensure aux_loss on same device as lm_loss
            if aux_loss.device != lm_loss.device:
                aux_loss = aux_loss.to(lm_loss.device)

            total_loss = lm_loss + self._aux_loss_weight * aux_loss

            # Bookkeeping
            self._last_lm_loss = float(lm_loss.detach())
            self._last_aux_loss = float(aux_loss.detach())

            if return_outputs:
                return total_loss, outputs
            return total_loss

        def log(self, logs, *args, **kwargs):
            """Override to surface lm_loss + aux_loss separately in training logs."""
            logs["lm_loss"] = self._last_lm_loss
            logs["aux_loss"] = self._last_aux_loss
            logs["aux_loss_weighted"] = self._aux_loss_weight * self._last_aux_loss
            return super().log(logs, *args, **kwargs)

    return _BaienTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        args=sft_config,
    )
