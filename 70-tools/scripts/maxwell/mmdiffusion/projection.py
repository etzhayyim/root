"""ProjectionAdapter — joint embedding (D) → diffusion cross-attention context (L×C).

This is the ONLY trainable module in the graft (the encoder is frozen, the diffusion
backbone is frozen at R0). It maps a single D-dim joint embedding to an L-token,
C-channel context tensor that the backbone cross-attends to (the slot a CLIP text
encoder would normally fill).

R0: shape logic only. The real forward (a small MLP + reshape, trained on the baien
Move pipeline) raises NotImplementedError until weights exist (smoke uses the
deterministic `fake_forward`).
"""
from __future__ import annotations

from dataclasses import dataclass

from joint_encoder import Embedding


@dataclass
class ProjectionAdapter:
    in_dim: int                 # encoder.embed_dim
    context_len: int = 4        # L — number of conditioning tokens
    context_dim: int = 8        # C — backbone cross-attn channel width

    @property
    def out_shape(self) -> tuple[int, int]:
        return (self.context_len, self.context_dim)

    def forward(self, z: Embedding) -> list[list[float]]:
        if z.dim != self.in_dim:
            raise ValueError(
                f"ProjectionAdapter expects dim {self.in_dim}, got {z.dim} "
                f"({z.modality} via {z.source_license})"
            )
        raise NotImplementedError(
            "Trained projection weights do not exist at R0 (smoke=destructive "
            "discipline, ADR-2605242400). Train on the baien Move pipeline, "
            "Murakumo-only. Use fake_forward for the wiring smoke."
        )

    def fake_forward(self, z: Embedding) -> list[list[float]]:
        """Deterministic shape-correct projection for the smoke — no learned params.

        Tiles/truncates the embedding into the (L, C) context grid so downstream
        shape asserts pass without any trained weights.
        """
        if z.dim != self.in_dim:
            raise ValueError(f"expects dim {self.in_dim}, got {z.dim}")
        flat = list(z.vector)
        need = self.context_len * self.context_dim
        # repeat to fill, then truncate — fully deterministic
        filled = (flat * ((need // len(flat)) + 1))[:need]
        return [filled[i * self.context_dim:(i + 1) * self.context_dim]
                for i in range(self.context_len)]
