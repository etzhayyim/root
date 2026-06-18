#!/usr/bin/env python3
"""Real end-to-end smoke for MaxwellDiffusion (NumPy; no torch, no model download).

Unlike smoke.py (R0 wiring stub), this runs the ACTUAL computation: LanguageBind
fallback embedding → real ProjectionNP → real DiT forward (attention + adaLN) → real
DDPM sampling loop, and asserts shapes, finiteness, determinism, conditioning
sensitivity (output depends on context = the multimodal conditioning truly flows), and
Charter gates. Proves the architecture genuinely computes — not that it is trained.

Run:  python3 70-tools/scripts/maxwell/mmdiffusion/smoke_real.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                            # noqa: E402
from model import DiT, DiTConfig                              # noqa: E402
from pipeline import MaxwellDiffusion                         # noqa: E402
from conditioning import BiometricUseError                   # noqa: E402

PASS = FAIL = 0


def ok(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  ok   {name}")
    else:
        FAIL += 1; print(f"  FAIL {name}")


def main() -> int:
    print("MaxwellDiffusion — real end-to-end smoke (numpy)\n")
    cfg = DiTConfig(image_size=16, patch_size=4, in_channels=3, hidden=64,
                    depth=2, n_heads=4, context_dim=64)
    mx = MaxwellDiffusion(cfg=cfg, timesteps=8)

    print(f"  encoder backend: {mx.encoder.backend} (license {mx.encoder.source_license})\n")

    # 1. encoder — real [B,768], unit-normalised, deterministic
    z = mx.encoder.embed("text", ["a red cube", "ocean at dawn"])
    ok("encoder shape [B,768]", z.shape == (2, 768))
    ok("encoder unit-normalised", np.allclose(np.linalg.norm(z, axis=-1), 1.0, atol=1e-6))
    ok("encoder deterministic", np.allclose(z, mx.encoder.embed("text", ["a red cube", "ocean at dawn"])))

    # 2. projection — [B,L,C]
    ctx = mx.projection.forward(z)
    ok("projection shape [B,L,C]", ctx.shape == (2, 4, 64))
    ok("projection finite", np.all(np.isfinite(ctx)))

    # 3. DiT forward — real noise prediction, correct shape, finite
    x = np.random.default_rng(1).standard_normal((2, 3, 16, 16))
    t = np.array([3, 6])
    eps = mx.dit.forward(x, t, ctx)
    ok("DiT output shape == image", eps.shape == (2, 3, 16, 16))
    ok("DiT output finite", np.all(np.isfinite(eps)))

    # 4. conditioning truly flows — different context ⇒ different DiT output (not a stub)
    ctx2 = mx.projection.forward(mx.encoder.embed("text", ["totally different prompt", "x"]))
    eps2 = mx.dit.forward(x, t, ctx2)
    ok("output depends on conditioning context", not np.allclose(eps, eps2))
    # and depends on timestep
    eps_t = mx.dit.forward(x, np.array([0, 0]), ctx)
    ok("output depends on timestep", not np.allclose(eps, eps_t))

    # 5. patchify/unpatchify round-trips (architecture correctness)
    rt = mx.dit.unpatchify(mx.dit.patchify(x))
    ok("patchify∘unpatchify == identity", np.allclose(rt, x))

    # 6. full generate() — real reverse diffusion → image, finite, deterministic
    img, lic = mx.generate("text", ["a red cube", "ocean at dawn"], seed=0)
    ok("generate image shape", img.shape == (2, 3, 16, 16))
    ok("generate finite", np.all(np.isfinite(img)))
    img2, _ = mx.generate("text", ["a red cube", "ocean at dawn"], seed=0)
    ok("generate deterministic (same seed)", np.allclose(img, img2))
    ok("output license = ECL-on-Apache (commons path)", lic == "ECL-on-Apache")

    # 7. real training loss — finite, positive
    images = np.random.default_rng(2).standard_normal((2, 3, 16, 16))
    loss = mx.training_loss(images, "text", ["a", "b"])
    ok("training_loss finite & positive", np.isfinite(loss) and loss > 0)

    # 8. Charter gate G3 — no-biometric refusal
    try:
        mx.generate("image", [b"x", b"y"], intent="face-id")
        ok("G3 refuses biometric intent", False)
    except BiometricUseError:
        ok("G3 refuses biometric intent", True)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
