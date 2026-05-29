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
        routing_mode: str = "learned",  # "learned" (default) | "distance" (MoCLE-style)
        expert_kind: str = "ffn",  # "ffn" (default 2-layer SiLU) | "memory" (UltraMem-style single learnable vector)
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
        self.routing_mode = routing_mode
        self.expert_kind = expert_kind

        if routing_mode == "learned":
            # Standard MoE: linear projection hidden -> E logits
            self.router = nn.Linear(hidden_size, num_experts, bias=False)
            self.cluster_centroids = None
        elif routing_mode == "distance":
            # MoCLE-style: learnable cluster centroids; routing = softmax(-dist/temp)
            # forces expert specialization via proximity-based assignment
            # breaks router-collapse problem in frozen-backbone regime (cycle 17-101 8-plateau)
            self.router = None
            self.cluster_centroids = nn.Parameter(torch.randn(num_experts, hidden_size) * 0.02)
        else:
            raise ValueError(f"routing_mode={routing_mode!r} not in {{'learned', 'distance'}}")

        # Expert kind:
        # - "ffn"    : standard 2-layer SiLU FFN (default, ADR-2605261900 §3)
        # - "memory" : UltraMem-style — each expert collapses to a single
        #              learnable vector ∈ R^H. Forward = top-k weighted sum
        #              of selected memory vectors (independent of x). Massive
        #              capacity drop per expert (≈100× fewer params) trades
        #              against ability to scale E to 10^4–10^6 cheaply.
        if expert_kind == "ffn":
            self.experts = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(hidden_size, expert_hidden, bias=False),
                    nn.SiLU(),
                    nn.Linear(expert_hidden, hidden_size, bias=False),
                )
                for _ in range(num_experts)
            ])
            self.memory_vectors = None
        elif expert_kind == "memory":
            # E × H learnable memory bank; one row per expert
            self.experts = None
            self.memory_vectors = nn.Parameter(torch.randn(num_experts, hidden_size) * 0.02)
        else:
            raise ValueError(f"expert_kind={expert_kind!r} not in {{'ffn', 'memory'}}")

        # Initialize router with small random for symmetry-breaking; not zero
        if self.router is not None:
            nn.init.normal_(self.router.weight, mean=0.0, std=0.02)

        # CRITICAL FIX (cycle 112c): output LayerNorm.
        # Without normalization, the raw expert output magnitude (FFN ~5, memory_vectors ~0.02)
        # is 100× to 30,000× smaller than the backbone FFN output magnitude (~641 on BitNet 2B).
        # The α gate then makes contribution α × 1e-3 vs backbone ~641 ≈ ratio 1e-9, below
        # bf16 precision. Result: wrapper output = backbone alone, MoE branch inert.
        # Fix: pass moe_out through LayerNorm to normalize magnitude to ~1.0,
        # then α × moe_out has predictable scale relative to backbone output.
        # The learnable out_scale allows the model to learn the right magnitude relative to FFN.
        self.out_norm = nn.LayerNorm(hidden_size)
        self.out_scale = nn.Parameter(torch.ones(1))

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

        # Router logits + softmax — fp32 routing math prevents bf16 overflow on aux_loss
        # (cycle 26 found bf16 routing → 36% NaN steps; fp32 cast then back stabilizes
        # without inflating memory since router is small Linear hidden→E).
        if self.routing_mode == "learned":
            router_logits = self.router(x_flat) / self.router_temperature  # (num_tokens, E)
        else:  # "distance" — MoCLE-style
            # Squared L2 distance from each token to each centroid (fp32 for stability)
            # x_flat: (num_tokens, hidden), centroids: (E, hidden)
            # dist[i, j] = ||x_flat[i] - centroids[j]||^2
            x_f32 = x_flat.float()
            c_f32 = self.cluster_centroids.float()
            # Efficient computation: ||x||^2 + ||c||^2 - 2*x@c.T
            dist_sq = (x_f32.pow(2).sum(dim=-1, keepdim=True)
                       + c_f32.pow(2).sum(dim=-1).unsqueeze(0)
                       - 2 * x_f32 @ c_f32.t())  # (num_tokens, E)
            router_logits = (-dist_sq / self.router_temperature).to(x_flat.dtype)
        router_probs = F.softmax(router_logits.float(), dim=-1).to(router_logits.dtype)

        # top-k expert selection
        topk_probs, topk_indices = torch.topk(router_probs, self.top_k, dim=-1)  # (num_tokens, k)
        # Renormalize top-k probs (so they sum to 1 per token; gives gate weights)
        topk_probs = topk_probs / (topk_probs.sum(dim=-1, keepdim=True) + 1e-9)

        # Dispatch tokens to experts + gather outputs
        if self.expert_kind == "memory":
            # UltraMem-style: each "expert" is one memory vector ∈ R^H.
            # Output = Σ_k topk_probs[:,k] * memory_vectors[topk_indices[:,k]]
            # Vectorized — no per-expert loop needed.
            # topk_indices: (num_tokens, k); memory_vectors: (E, H)
            selected = self.memory_vectors[topk_indices]  # (num_tokens, k, H)
            output = (topk_probs.unsqueeze(-1) * selected).sum(dim=1)  # (num_tokens, H)
        else:
            # FFN-expert path: per-expert scatter-gather
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
        token_frac = mask_per_expert.sum(dim=(0, 1)) / (num_tokens * self.top_k)  # (E,) fp32
        # mean router probability per expert (over all tokens) — fp32 to avoid bf16 overflow
        prob_frac = router_probs.float().mean(dim=0)  # (E,) fp32
        aux_loss = self.num_experts * (token_frac * prob_frac).sum()

        # CRITICAL FIX (cycle 112c): normalize output to ~1.0 magnitude and apply learnable scale.
        # Prevents the "MoE branch output 5×10⁻⁸ of backbone FFN" bug where the residual
        # contribution was below bf16 precision and the wrapper degenerated to backbone-only.
        output_norm = self.out_norm(output) * self.out_scale  # (num_tokens, hidden)

        return output_norm.reshape(batch, seq, hidden), aux_loss

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
