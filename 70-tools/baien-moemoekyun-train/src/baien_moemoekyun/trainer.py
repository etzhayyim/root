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
        branch = wrapper.moe_branch
        # router = linear-router weights ("learned" mode) OR cluster centroids ("distance" mode);
        # both are R^{E×H} learnable params getting the same lr_router treatment.
        if branch.router is not None:
            router_params.append(branch.router.weight)
            if branch.router.bias is not None:
                router_params.append(branch.router.bias)
        elif branch.cluster_centroids is not None:
            router_params.append(branch.cluster_centroids)
        else:
            raise RuntimeError(
                f"moe_branch has neither router nor cluster_centroids (routing_mode={branch.routing_mode!r})"
            )

        # experts = all params in moe_branch.experts (FFN kind) OR moe_branch.memory_vectors (UltraMem kind)
        if branch.experts is not None:
            for p in branch.experts.parameters():
                expert_params.append(p)
        elif branch.memory_vectors is not None:
            expert_params.append(branch.memory_vectors)
        else:
            raise RuntimeError(
                f"moe_branch has neither experts nor memory_vectors (expert_kind={branch.expert_kind!r})"
            )

        # cycle 113 fix: out_norm + out_scale (LayerNorm + learnable scale on moe_branch output)
        # were not in any param group before — optimizer never updated them.
        # Group them with router (similar small param count, same lr policy).
        if hasattr(branch, "out_norm") and branch.out_norm is not None:
            for p in branch.out_norm.parameters():
                router_params.append(p)
        if hasattr(branch, "out_scale") and branch.out_scale is not None:
            router_params.append(branch.out_scale)

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


def apply_mxfp4_quantize(
    model: nn.Module,
    moe_wrappers: dict[str, BitNetFFNWithMoE],
    *,
    block_size: int = 32,
    weight_dtype: Any = None,
    activation_dtype: Any = None,
) -> dict[str, Any]:
    """Quantize MoE router + expert FFN nn.Linear modules to MXFP4 (OCP MX).

    Per ADR-2605263100 §1.1.A: trainable MoE params (router + experts) use
    MXFP4 weight + MXFP8 activation (OCP MX 32-element block scaling).
    NOT NVFP4 — vendor-neutral OCP standard per Charter Rider §2(e).

    Backbone (frozen bf16) and α gate (fp32 scalar) are NOT quantized.

    Returns dict {target_module_qualname: quantized_module} for audit.
    """
    import torch
    from torchao.prototype.mx_formats import MXDynamicActivationMXWeightConfig
    from torchao.quantization import quantize_

    if weight_dtype is None:
        weight_dtype = torch.float4_e2m1fn_x2  # MXFP4 (OCP MX e2m1)
    if activation_dtype is None:
        activation_dtype = torch.float8_e4m3fn  # MXFP8

    config = MXDynamicActivationMXWeightConfig(
        block_size=block_size,
        activation_dtype=activation_dtype,
        weight_dtype=weight_dtype,
    )

    quantized: dict[str, Any] = {}

    def _filter_router_and_experts(module: nn.Module, fqn: str) -> bool:
        if not isinstance(module, nn.Linear):
            return False
        for wrapper_fqn in moe_wrappers:
            if fqn.startswith(wrapper_fqn + ".moe_branch.router"):
                return True
            if fqn.startswith(wrapper_fqn + ".moe_branch.experts."):
                return True
        return False

    quantize_(model, config, filter_fn=_filter_router_and_experts)

    for fqn, mod in model.named_modules():
        if _filter_router_and_experts(mod, fqn):
            quantized[fqn] = mod

    logger.info(
        "MXFP4 quantized %d modules (block_size=%d, weight=%s, activation=%s)",
        len(quantized), block_size, weight_dtype, activation_dtype,
    )
    return quantized


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
    precision: str = "bf16",
):
    """Construct a BaienMoEMoekyunTrainer (SFTTrainer subclass) with per-group LR + aux_loss.

    `precision`:
      - "bf16": default; router + experts trained in bf16 (matches ADR-2605262100 §2 R1.4 EVO path)
      - "mxfp4": router + expert nn.Linear quantized to MXFP4 (OCP MX) weight + MXFP8 activation
        via torchao.prototype.mx_formats.MXDynamicActivationMXWeightConfig (block_size=32).
        Per ADR-2605263100 §1.1.A — Founder Lv7+ train carve-out on 5090.
        NOT NVFP4 — vendor-neutral OCP MX standard per Charter Rider §2(e).
      - "mxfp8": fallback if MXFP4 dtype unavailable on hardware; activation+weight both MXFP8.

    Returns the trainer instance. Caller invokes `.train()` and `.save_model()`.
    """
    # Validation gates BEFORE any heavyweight import (so config errors surface fast)
    if precision not in ("bf16", "mxfp4", "mxfp8"):
        raise ValueError(
            f"precision={precision!r} not in {{bf16, mxfp4, mxfp8}}. "
            "Per ADR-2605263100 §1.1.A: NVFP4 not permitted (vendor lock-in)."
        )
    # G6 MANDATORY: aux_loss_weight ∈ [0.001, 0.1]
    if not (0.001 <= aux_loss_weight <= 0.1):
        raise ValueError(
            f"aux_loss_weight={aux_loss_weight} outside [0.001, 0.1] range "
            "per ADR-2605261900 §5 G6 + ADR-2605262100 §4."
        )

    try:
        from trl import SFTTrainer
    except ImportError as e:
        raise ImportError(
            "trl>=0.11 required for training; install via `pip install trl>=0.11`. "
            f"Original error: {e}"
        )

    if precision == "mxfp4":
        import torch as _torch
        try:
            apply_mxfp4_quantize(
                model, moe_wrappers,
                block_size=32,
                weight_dtype=_torch.float4_e2m1fn_x2,
                activation_dtype=_torch.float8_e4m3fn,
            )
        except (ImportError, AttributeError) as e:
            raise RuntimeError(
                "MXFP4 quantize requires torchao>=0.7 with MX format support + "
                "torch>=2.5 with torch.float4_e2m1fn_x2 dtype. "
                "Fall back to precision='mxfp8' if HW lacks FP4 Tensor Core (pre-Blackwell). "
                f"Original error: {e}"
            )
    elif precision == "mxfp8":
        import torch as _torch
        apply_mxfp4_quantize(
            model, moe_wrappers,
            block_size=32,
            weight_dtype=_torch.float8_e4m3fn,
            activation_dtype=_torch.float8_e4m3fn,
        )
    # precision == "bf16": no-op, model already in bf16 per attach.py

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
