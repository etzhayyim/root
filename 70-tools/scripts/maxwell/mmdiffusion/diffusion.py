"""Real DDPM diffusion process (NumPy) — forward noising + reverse sampling.

Standard DDPM (Ho et al. 2020): a cosine beta schedule, q_sample for the forward
noising used in training, and an ancestral p_sample loop that runs the DiT in reverse
to produce an image-shaped sample. Real math; runnable offline.
"""
from __future__ import annotations

import numpy as np


def cosine_betas(T, s=0.008):
    steps = np.arange(T + 1)
    f = np.cos(((steps / T) + s) / (1 + s) * np.pi / 2) ** 2
    abar = f / f[0]
    betas = 1 - (abar[1:] / abar[:-1])
    return np.clip(betas, 1e-4, 0.999)


class Diffusion:
    def __init__(self, timesteps=50):
        self.T = timesteps
        self.betas = cosine_betas(timesteps)
        self.alphas = 1.0 - self.betas
        self.abar = np.cumprod(self.alphas)
        self.abar_prev = np.concatenate([[1.0], self.abar[:-1]])

    def q_sample(self, x0, t, noise):
        """Forward: add noise to x0 at timestep t (per-sample t array)."""
        a = np.sqrt(self.abar[t])[:, None, None, None]
        am = np.sqrt(1.0 - self.abar[t])[:, None, None, None]
        return a * x0 + am * noise

    def p_sample_loop(self, model, shape, context, rng):
        """Reverse: start from noise, denoise T→0 with the DiT (eps-prediction)."""
        x = rng.standard_normal(shape)
        for i in reversed(range(self.T)):
            t = np.full(shape[0], i, dtype=np.int64)
            eps = model.forward(x, t, context)
            a, ab, abp, b = self.alphas[i], self.abar[i], self.abar_prev[i], self.betas[i]
            # posterior mean from predicted noise
            coef = b / np.sqrt(1.0 - ab)
            mean = (x - coef * eps) / np.sqrt(a)
            if i > 0:
                var = b * (1.0 - abp) / (1.0 - ab)
                x = mean + np.sqrt(var) * rng.standard_normal(shape)
            else:
                x = mean
        return x

    def training_loss(self, model, x0, context, rng):
        """Real DDPM loss: predict the noise added at a random t (MSE). Forward-only
        in NumPy (no autograd here — see dit_torch.py for the trainable path)."""
        B = x0.shape[0]
        t = rng.integers(0, self.T, size=B)
        noise = rng.standard_normal(x0.shape)
        xt = self.q_sample(x0, t, noise)
        pred = model.forward(xt, t, context)
        return float(np.mean((pred - noise) ** 2))
