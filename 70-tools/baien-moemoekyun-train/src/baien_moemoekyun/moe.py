"""BaienMoEResidual — MoE residual branch with top-k routing + load-balancing aux loss.

Per ADR-2605261900 §2 + ADR-2605262100 §2.2 R0 defaults:
  - num_experts = 128 (R1.4), sweep 64..256 in R2
  - top_k = 2
  - expert_hidden = config.intermediate_size // 32 (~172 dim for BitNet 2B)
  - router temperature = 1.0
  - aux loss = Switch-Transformer load-balance, weight = 0.01 (G6 MANDATORY)
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class BaienMoEResidual(nn.Module):
    """MoE residual branch: router + small-FFN experts.

    Forward returns (output, aux_loss). Caller MUST add aux_loss to main LM loss
    with weight w ∈ [0.001, 0.1] per G6.
    """

    def __init__(
        self,
        hidden_size: int,
        num_experts: int = 128,
        expert_hidden: int | None = None,
        top_k: int = 2,
        intermediate_size: int | None = None,
        expert_hidden_ratio: int = 32,  # dense_FFN / 32
        router_temperature: float = 1.0,
    ):
        super().__init__()
        if expert_hidden is None:
            if intermediate_size is None:
                raise ValueError("Provide either expert_hidden or intermediate_size")
            expert_hidden = max(intermediate_size // expert_hidden_ratio, 16)
        self.hidden_size = hidden_size
        self.num_experts = num_experts
        self.expert_hidden = expert_hidden
        self.top_k = top_k
        self.router_temperature = router_temperature

        # Router: linear projection from hidden -> E logits
        self.router = nn.Linear(hidden_size, num_experts, bias=False)

        # Experts: standard 2-layer FFN with SiLU activation (NOT BitLinear in R1 per ADR-2605261900 §3)
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, expert_hidden, bias=False),
                nn.SiLU(),
                nn.Linear(expert_hidden, hidden_size, bias=False),
            )
            for _ in range(num_experts)
        ])

        # Initialize router with small random for symmetry-breaking; not zero
        nn.init.normal_(self.router.weight, mean=0.0, std=0.02)

        # G7: experts MUST NOT be initialized from dense FFN copy (Drop-Upcycling partial-reinit OK; identical-expert collapse rejected).
        # Default torch init (Kaiming uniform for Linear) gives independent random init per expert. Verified by test_expert_init_independent.py.

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Args:
            x: (batch, seq, hidden_size)
        Returns:
            output: (batch, seq, hidden_size) — sum of top-k gated expert outputs
            aux_loss: scalar — Switch-Transformer load-balancing loss (caller weights by 0.01)
        """
        batch, seq, hidden = x.shape
        x_flat = x.reshape(-1, hidden)  # (batch*seq, hidden)
        num_tokens = x_flat.shape[0]

        # Router logits + softmax
        router_logits = self.router(x_flat) / self.router_temperature  # (num_tokens, E)
        router_probs = F.softmax(router_logits, dim=-1)  # (num_tokens, E)

        # top-k expert selection
        topk_probs, topk_indices = torch.topk(router_probs, self.top_k, dim=-1)  # (num_tokens, k)
        # Renormalize top-k probs (so they sum to 1 per token; gives gate weights)
        topk_probs = topk_probs / (topk_probs.sum(dim=-1, keepdim=True) + 1e-9)

        # Dispatch tokens to experts + gather outputs
        output = torch.zeros_like(x_flat)
        for k_pos in range(self.top_k):
            expert_idx_per_token = topk_indices[:, k_pos]  # (num_tokens,)
            gate_weight = topk_probs[:, k_pos].unsqueeze(-1)  # (num_tokens, 1)
            # For each expert, select tokens routed to it
            for e in range(self.num_experts):
                mask = expert_idx_per_token == e
                if not mask.any():
                    continue
                tokens_for_e = x_flat[mask]  # (n_e, hidden)
                expert_out = self.experts[e](tokens_for_e)  # (n_e, hidden)
                output[mask] += gate_weight[mask] * expert_out

        # Switch-Transformer load-balancing aux loss
        # = E * Σ_i (frac_tokens_i × frac_router_prob_i)
        # where frac_tokens_i = fraction of tokens routed to expert i
        #       frac_router_prob_i = mean router prob over all tokens for expert i
        # See Fedus et al. 2021 §4.1
        mask_per_expert = F.one_hot(topk_indices, num_classes=self.num_experts).float()  # (num_tokens, k, E)
        # fraction of tokens dispatched to each expert (across top-k positions)
        token_frac = mask_per_expert.sum(dim=(0, 1)) / (num_tokens * self.top_k)  # (E,)
        # mean router probability per expert (over all tokens)
        prob_frac = router_probs.mean(dim=0)  # (E,)
        aux_loss = self.num_experts * (token_frac * prob_frac).sum()

        return output.reshape(batch, seq, hidden), aux_loss

    def expert_utilization(self, x: torch.Tensor) -> torch.Tensor:
        """Diagnostic — returns fraction of tokens routed to each expert (no gradient).

        Useful for R1.3 acceptance: assert all experts > 1/E × 0.1.
        """
        with torch.no_grad():
            x_flat = x.reshape(-1, self.hidden_size)
            router_logits = self.router(x_flat) / self.router_temperature
            router_probs = F.softmax(router_logits, dim=-1)
            _, topk_indices = torch.topk(router_probs, self.top_k, dim=-1)
            mask = F.one_hot(topk_indices, num_classes=self.num_experts).float()
            return mask.sum(dim=(0, 1)) / (x_flat.shape[0] * self.top_k)
