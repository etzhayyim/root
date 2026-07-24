"""MaxwellDiffusion — the wired multimodal image-diffusion graft (real, runnable).

LanguageBind (frozen, MIT) → ProjectionNP (trainable) → DiT (cross-attn conditioned) →
DDPM sampling. Reuses the Charter gates from conditioning.py (G1 Murakumo-preferred /
G3 no-biometric / G4 license-firewall). LanguageBind is the commons path, so its outputs
carry ECL-on-Apache and G4 does not firewall it (unlike the CC-BY-NC ImageBind path).

Untrained (seed weights) → generate() returns a real, correctly-shaped image array that
is noise-like; train it (dit_torch.py) for content. The point of this module is that the
architecture genuinely computes end-to-end, offline, today.
"""
from __future__ import annotations

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from languagebind_encoder import LanguageBindEncoder        # noqa: E402
from projection_np import ProjectionNP                      # noqa: E402
from model import DiT, DiTConfig                             # noqa: E402
from diffusion import Diffusion                              # noqa: E402
from conditioning import (                                   # noqa: E402  (Charter gates)
    GenerationRequest, assert_no_biometric, MURAKUMO_ONLY,
)


class MaxwellDiffusion:
    def __init__(self, cfg: DiTConfig | None = None, timesteps: int = 25,
                 prefer_real_encoder: bool = True):
        self.cfg = cfg or DiTConfig()
        self.encoder = LanguageBindEncoder(prefer_real=prefer_real_encoder)
        self.projection = ProjectionNP(self.encoder.embed_dim,
                                       context_len=4, context_dim=self.cfg.context_dim)
        self.dit = DiT(self.cfg)
        self.diffusion = Diffusion(timesteps=timesteps)
        self.output_license = self.encoder.output_license

    # ── Charter gates (reuse conditioning.py) ──
    def _gate(self, req: GenerationRequest):
        if not MURAKUMO_ONLY:
            # G1: objective-function-assessed (ADR-2606172359); Murakumo preferred.
            pass
        assert_no_biometric(req.intent)                       # G3
        # G4: LanguageBind is redistributable (commons), so commercial context is allowed.
        if req.commercial_context and not self.encoder.redistributable:
            raise RuntimeError("G4: non-redistributable encoder cannot feed commercial context")

    def _context(self, modality, items):
        z = self.encoder.embed(modality, items)               # [B, D] frozen
        return self.projection.forward(z)                     # [B, L, C]

    def generate(self, modality: str, items, *, intent: str = "general",
                 commercial_context: bool = False, seed: int = 0):
        """any-modality → image. Returns (images [B,C,S,S], output_license)."""
        req = GenerationRequest(modality, items, intent=intent,
                                commercial_context=commercial_context)
        self._gate(req)
        context = self._context(modality, items)
        B, C, S = len(items), self.cfg.in_channels, self.cfg.image_size
        rng = np.random.default_rng(seed)
        imgs = self.diffusion.p_sample_loop(self.dit, (B, C, S, S), context, rng)
        return imgs, self.output_license

    def training_loss(self, images, modality: str, items, seed: int = 0):
        """Real DDPM eps-MSE loss on (images, conditioning). Forward-only in NumPy."""
        context = self._context(modality, items)
        rng = np.random.default_rng(seed)
        return self.diffusion.training_loss(self.dit, images, context, rng)
