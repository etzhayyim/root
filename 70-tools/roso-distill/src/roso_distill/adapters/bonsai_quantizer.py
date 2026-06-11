"""Bonsai-style end-to-end 1-bit quantization.

Per ADR-2605242000 §Phase 1 step 2. The published Bonsai 8B 1-bit
(Prism ML 2026 March) uses per-layer optimization with inline
dequantize kernels in MLX (Apple Silicon). This module is a Python
port stub that:

  1. **Documents the algorithm interface** so it's clear what's wired
     vs what's pending implementation.
  2. **Provides a stub `quantize_module()`** that returns a structurally
     1-bit-shaped weight tensor (signed ternary cast of a clamped
     bf16 master) — enough to exercise the pipeline end-to-end.
  3. **Leaves the per-tensor optimization step as TODO** (real Bonsai
     uses calibration data + GPTQ-style block coordinate descent;
     ~500 LoC research port).

Reference impl to port from:
  https://github.com/PrismML-Eng/Bonsai-demo
  + the 1-bit-bonsai-8b-whitepaper.pdf
"""

from __future__ import annotations

from typing import Any


def quantize_module(module: Any, *, method: str = "bonsai-w1",
                    calibration_inputs=None, in_place: bool = True) -> dict:
    """Quantize a single nn.Module's linear weights to 1-bit packed.

    Returns a dict with `{packed_bytes, scale, original_dtype, num_params}`.

    Current implementation = sign-based ternarization with per-tensor scale:

        scale = mean(|W|)
        Wq = sign(W) * scale    where sign(0) = 0

    When `in_place=True` (default), mutates `child.weight.data` to the
    sign-quantized tensor so a subsequent `model.save_pretrained()` writes
    functionally-1-bit weights (stored as the parameter's dtype). Phase B
    recovery loads this checkpoint as the SFT student.

    This is the simplest 1.58-bit projection (matches BitNet b1.58
    semantics, NOT full Bonsai). Real Bonsai computes per-layer optimal
    1-bit using calibration_inputs (TODO).
    """
    import torch
    from torch import nn

    out: dict[str, Any] = {"layer_class": type(module).__name__,
                           "method": method, "weights": {}}
    total_params = 0
    total_packed_bytes = 0

    for name, child in module.named_modules():
        if not isinstance(child, nn.Linear):
            continue
        W = child.weight.detach()
        scale = W.abs().mean().item()
        Wq = torch.sign(W) * scale
        if in_place:
            child.weight.data.copy_(Wq.to(child.weight.dtype))
        # packed bytes: 1 trit per 1.58 bits → 5 trits / 8 bits = 5 trits / byte
        n = int(W.numel())
        packed_bytes = (n + 4) // 5     # 5 trits per byte (Microsoft i2_s style)
        out["weights"][name] = {
            "shape": list(W.shape),
            "scale": scale,
            "ternary_proxy_max_abs": float(Wq.abs().max()),
            "packed_bytes": packed_bytes,
        }
        total_params += n
        total_packed_bytes += packed_bytes

    out["total_params"] = total_params
    out["total_packed_bytes"] = total_packed_bytes
    out["packed_gb"] = total_packed_bytes / (1024 ** 3)
    out["TODO"] = (
        "real Bonsai 1-bit requires per-layer optimization with calibration "
        "inputs (PrismML whitepaper Algorithm 1). Current impl = naive sign "
        "projection; expect ~30% perplexity inflation vs published Bonsai. "
        "Port from https://github.com/PrismML-Eng/Bonsai-demo when wiring "
        "the real Phase 1 quantization."
    )
    return out
