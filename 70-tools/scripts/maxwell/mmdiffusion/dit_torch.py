"""Trainable DiT twin (PyTorch) — the real training artifact.

Mirrors model.py (numpy) as an actual nn.Module with standard adaLN-ZERO init and a real
training step (eps-prediction MSE + AdamW). Runs when torch is installed; trained on the
baien Move pipeline, Murakumo-preferred (ADR-2606172359). Imported lazily so the numpy
pipeline + smoke stay torch-free.

Charter: weights/outputs carry ECL-on-Apache when the encoder is LanguageBind (MIT).
"""
from __future__ import annotations

import math


def _require_torch():
    try:
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def build(cfg):  # cfg: model.DiTConfig
    import torch
    import torch.nn as nn

    def modulate(x, shift, scale):
        return x * (1 + scale.unsqueeze(1)) + shift.unsqueeze(1)

    class TimestepEmb(nn.Module):
        def __init__(self, h):
            super().__init__()
            self.mlp = nn.Sequential(nn.Linear(h, 4 * h), nn.GELU(), nn.Linear(4 * h, h))
            self.h = h

        def forward(self, t):
            half = self.h // 2
            freqs = torch.exp(-math.log(10000) * torch.arange(half, device=t.device) / half)
            a = t[:, None].float() * freqs[None]
            emb = torch.cat([a.cos(), a.sin()], -1)
            if emb.shape[-1] < self.h:
                emb = torch.cat([emb, torch.zeros(emb.shape[0], self.h - emb.shape[-1], device=t.device)], -1)
            return self.mlp(emb)

    class Block(nn.Module):
        def __init__(self, h, heads, cdim):
            super().__init__()
            self.n1, self.n2, self.n3 = (nn.LayerNorm(h, elementwise_affine=False) for _ in range(3))
            self.attn = nn.MultiheadAttention(h, heads, batch_first=True)
            self.cross = nn.MultiheadAttention(h, heads, batch_first=True, kdim=cdim, vdim=cdim)
            self.mlp = nn.Sequential(nn.Linear(h, 4 * h), nn.GELU(), nn.Linear(4 * h, h))
            self.adaln = nn.Sequential(nn.SiLU(), nn.Linear(h, 6 * h))
            nn.init.zeros_(self.adaln[-1].weight); nn.init.zeros_(self.adaln[-1].bias)  # adaLN-zero

        def forward(self, x, c, ctx):
            sa, sb, ga, sc, sd, gm = self.adaln(c).chunk(6, -1)
            h = modulate(self.n1(x), sa, sb)
            x = x + ga.unsqueeze(1) * self.attn(h, h, h, need_weights=False)[0]
            x = x + self.cross(self.n2(x), ctx, ctx, need_weights=False)[0]
            x = x + gm.unsqueeze(1) * self.mlp(modulate(self.n3(x), sc, sd))
            return x

    class DiTorch(nn.Module):
        def __init__(self):
            super().__init__()
            self.cfg = cfg
            self.patch = nn.Linear(cfg.patch_dim, cfg.hidden)
            self.pos = nn.Parameter(torch.zeros(1, cfg.num_patches, cfg.hidden))
            self.temb = TimestepEmb(cfg.hidden)
            self.blocks = nn.ModuleList([Block(cfg.hidden, cfg.n_heads, cfg.context_dim)
                                         for _ in range(cfg.depth)])
            self.fn = nn.LayerNorm(cfg.hidden, elementwise_affine=False)
            self.fadaln = nn.Sequential(nn.SiLU(), nn.Linear(cfg.hidden, 2 * cfg.hidden))
            self.head = nn.Linear(cfg.hidden, cfg.patch_dim)
            nn.init.zeros_(self.fadaln[-1].weight); nn.init.zeros_(self.head.weight)  # adaLN-zero

        def _patchify(self, x):
            B, C, P, g = x.shape[0], cfg.in_channels, cfg.patch_size, cfg.grid
            x = x.reshape(B, C, g, P, g, P).permute(0, 2, 4, 1, 3, 5)
            return x.reshape(B, g * g, C * P * P)

        def _unpatchify(self, x):
            import torch
            B, C, P, g = x.shape[0], cfg.in_channels, cfg.patch_size, cfg.grid
            x = x.reshape(B, g, g, C, P, P).permute(0, 3, 1, 4, 2, 5)
            return x.reshape(B, C, g * P, g * P)

        def forward(self, x, t, ctx):
            h = self.patch(self._patchify(x)) + self.pos
            c = self.temb(t)
            for blk in self.blocks:
                h = blk(h, c, ctx)
            s, sc = self.fadaln(c).chunk(2, -1)
            h = modulate(self.fn(h), s, sc)
            return self._unpatchify(self.head(h))

    return DiTorch()


def train_step(model, diffusion_betas, x0, ctx, opt):
    """One real DDPM training step (eps-MSE + backward). diffusion_betas: 1-D tensor."""
    import torch
    abar = torch.cumprod(1 - diffusion_betas, 0)
    B = x0.shape[0]
    t = torch.randint(0, len(diffusion_betas), (B,), device=x0.device)
    noise = torch.randn_like(x0)
    a, am = abar[t].sqrt()[:, None, None, None], (1 - abar[t]).sqrt()[:, None, None, None]
    xt = a * x0 + am * noise
    pred = model(xt, t, ctx)
    loss = torch.nn.functional.mse_loss(pred, noise)
    opt.zero_grad(); loss.backward(); opt.step()
    return float(loss.item())


if __name__ == "__main__":
    print("torch available:", _require_torch(),
          "— this is the trainable twin; numpy path runs via pipeline.py/smoke_real.py")
