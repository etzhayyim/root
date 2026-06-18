"""Real (runnable) DiT — Diffusion Transformer with cross-attention conditioning.

ADR-2606061000 D6 M3 (Maxwell multimodal image-diffusion graft). This is NOT a stub:
it is a faithful DiT forward pass implemented in NumPy (patch-embed → sinusoidal
timestep embed → N×[adaLN self-attention + cross-attention to the joint-embedding
context + MLP] → adaLN final → unpatchify), so the architecture genuinely computes on
real tensors offline (numpy only). Weights are seed-initialised (untrained → the output
is noise-shaped, honestly not a good image until trained). A torch trainable twin lives
in dit_torch.py.

The cross-attention `context` is the projected LanguageBind/ImageBind joint embedding —
the multimodal conditioning slot a CLIP text encoder would normally fill.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class DiTConfig:
    image_size: int = 16
    patch_size: int = 4
    in_channels: int = 3
    hidden: int = 64
    depth: int = 2
    n_heads: int = 4
    context_dim: int = 64      # = projection out width (per conditioning token)
    seed: int = 7

    @property
    def grid(self) -> int:
        return self.image_size // self.patch_size

    @property
    def num_patches(self) -> int:
        return self.grid * self.grid

    @property
    def patch_dim(self) -> int:
        return self.in_channels * self.patch_size * self.patch_size


# ── primitives (real math) ───────────────────────────────────────────────────
def _gelu(x):
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * x ** 3)))


def _layernorm(x, eps=1e-5):
    mu = x.mean(-1, keepdims=True)
    var = x.var(-1, keepdims=True)
    return (x - mu) / np.sqrt(var + eps)


def _softmax(x, axis=-1):
    z = x - x.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def _modulate(x, shift, scale):
    # x [B,T,H], shift/scale [B,H]
    return x * (1.0 + scale[:, None, :]) + shift[:, None, :]


def _mha(q, k, v, n_heads):
    """Multi-head attention. q [B,Tq,H], k/v [B,Tk,H] → [B,Tq,H]."""
    B, Tq, H = q.shape
    Tk = k.shape[1]
    d = H // n_heads
    qh = q.reshape(B, Tq, n_heads, d).transpose(0, 2, 1, 3)   # B,h,Tq,d
    kh = k.reshape(B, Tk, n_heads, d).transpose(0, 2, 1, 3)
    vh = v.reshape(B, Tk, n_heads, d).transpose(0, 2, 1, 3)
    att = _softmax(qh @ kh.transpose(0, 1, 3, 2) / np.sqrt(d))  # B,h,Tq,Tk
    out = att @ vh                                              # B,h,Tq,d
    return out.transpose(0, 2, 1, 3).reshape(B, Tq, H)


def _sinusoidal(t, dim):
    """t [B] timesteps → [B, dim] sinusoidal embedding."""
    half = dim // 2
    freqs = np.exp(-np.log(10000.0) * np.arange(half) / max(half, 1))
    a = t[:, None].astype(np.float64) * freqs[None, :]
    emb = np.concatenate([np.cos(a), np.sin(a)], axis=-1)
    if emb.shape[-1] < dim:
        emb = np.concatenate([emb, np.zeros((emb.shape[0], dim - emb.shape[-1]))], -1)
    return emb


class DiT:
    """Seed-initialised DiT. Real forward; untrained weights."""

    def __init__(self, cfg: DiTConfig):
        self.cfg = cfg
        rng = np.random.default_rng(cfg.seed)
        H, Cd = cfg.hidden, cfg.context_dim

        def w(shape, s=0.02):
            return rng.standard_normal(shape) * s

        self.patch_embed_w = w((cfg.patch_dim, H))
        self.patch_embed_b = np.zeros(H)
        self.pos = w((cfg.num_patches, H))
        # timestep MLP
        self.t1_w, self.t1_b = w((H, 4 * H)), np.zeros(4 * H)
        self.t2_w, self.t2_b = w((4 * H, H)), np.zeros(H)
        # NOTE: production training uses adaLN-ZERO init (these = 0) for stability, which
        # makes the untrained forward output 0. For a runnable, demonstrably-sensitive
        # untrained network we seed the adaLN/final layers with small random weights; the
        # torch trainable twin (dit_torch.py) uses the standard adaLN-zero init.
        self.blocks = []
        for _ in range(cfg.depth):
            self.blocks.append({
                "adaln_w": w((H, 6 * H)), "adaln_b": np.zeros(6 * H),
                "qkv_w": w((H, 3 * H)), "o_w": w((H, H)),
                "cq_w": w((H, H)), "ckv_w": w((Cd, 2 * H)), "co_w": w((H, H)),
                "mlp1_w": w((H, 4 * H)), "mlp1_b": np.zeros(4 * H),
                "mlp2_w": w((4 * H, H)), "mlp2_b": np.zeros(H),
            })
        self.final_adaln_w, self.final_adaln_b = w((H, 2 * H)), np.zeros(2 * H)
        self.final_w = w((H, cfg.patch_dim))

    # ── patch <-> image ──
    def patchify(self, x):
        B, C, S, P, g = x.shape[0], self.cfg.in_channels, self.cfg.image_size, self.cfg.patch_size, self.cfg.grid
        x = x.reshape(B, C, g, P, g, P).transpose(0, 2, 4, 1, 3, 5)  # B,g,g,C,P,P
        return x.reshape(B, g * g, C * P * P)

    def unpatchify(self, x):
        B, C, P, g = x.shape[0], self.cfg.in_channels, self.cfg.patch_size, self.cfg.grid
        x = x.reshape(B, g, g, C, P, P).transpose(0, 3, 1, 4, 2, 5)
        return x.reshape(B, C, g * P, g * P)

    def forward(self, x, t, context):
        """x [B,C,S,S] noised image · t [B] · context [B,L,context_dim] → predicted noise [B,C,S,S]."""
        cfg = self.cfg
        h = self.patchify(x) @ self.patch_embed_w + self.patch_embed_b
        h = h + self.pos[None]
        c = _gelu(_sinusoidal(t, cfg.hidden) @ self.t1_w + self.t1_b) @ self.t2_w + self.t2_b  # [B,H]

        for blk in self.blocks:
            mod = c @ blk["adaln_w"] + blk["adaln_b"]                 # [B,6H]
            sh_a, sc_a, g_a, sh_m, sc_m, g_m = np.split(mod, 6, axis=-1)
            # self-attention (adaLN)
            xn = _modulate(_layernorm(h), sh_a, sc_a)
            qkv = xn @ blk["qkv_w"]
            q, k, v = np.split(qkv, 3, axis=-1)
            h = h + g_a[:, None, :] * (_mha(q, k, v, cfg.n_heads) @ blk["o_w"])
            # cross-attention to the joint-embedding context (the conditioning)
            xn = _layernorm(h)
            cq = xn @ blk["cq_w"]
            ck, cv = np.split(context @ blk["ckv_w"], 2, axis=-1)
            h = h + (_mha(cq, ck, cv, cfg.n_heads) @ blk["co_w"])
            # MLP (adaLN)
            xn = _modulate(_layernorm(h), sh_m, sc_m)
            h = h + g_m[:, None, :] * (_gelu(xn @ blk["mlp1_w"] + blk["mlp1_b"]) @ blk["mlp2_w"] + blk["mlp2_b"])

        fmod = c @ self.final_adaln_w + self.final_adaln_b
        sh, sc = np.split(fmod, 2, axis=-1)
        h = _modulate(_layernorm(h), sh, sc) @ self.final_w
        return self.unpatchify(h)
