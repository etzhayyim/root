"""Bit-packed XNOR-popcount matmul via Triton — cross-platform JIT (CUDA + ROCm).

Triton (since 2.0) ships `tl.popcount` (also exposed as `tl.bit_count` in
some versions). The kernel here mirrors the CUDA/HIP reference: each
program (threadblock) computes a TILE_B × TILE_N output tile by reducing
the K-dim via popcount on packed uint32 chunks.

Requires:
  - triton >= 2.1 (CUDA backend) or triton >= 2.2 (ROCm backend)
  - CUDA or ROCm device
"""
from __future__ import annotations

import json
import platform
import time
from pathlib import Path
import sys

import torch

try:
    import triton
    import triton.language as tl
    HAVE_TRITON = True
except ImportError as e:
    HAVE_TRITON = False
    TRITON_IMPORT_ERR = str(e)


if HAVE_TRITON:
    # tl.popcount exists in newer triton; older versions name it differently.
    # We try a few aliases.
    _POPC = None
    for name in ("popcount", "bit_count", "popc"):
        if hasattr(tl, name):
            _POPC = getattr(tl, name)
            break

    @triton.jit
    def xnor_popcount_kernel(
        x_ptr, w_ptr, y_ptr,
        B, N, P, K_padded, pad, scale,
        stride_xb, stride_xp,
        stride_wn, stride_wp,
        stride_yb, stride_yn,
        BLOCK_B: tl.constexpr,
        BLOCK_N: tl.constexpr,
        BLOCK_P: tl.constexpr,
    ):
        pid_b = tl.program_id(0)
        pid_n = tl.program_id(1)
        offs_b = pid_b * BLOCK_B + tl.arange(0, BLOCK_B)
        offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
        offs_p = tl.arange(0, BLOCK_P)

        mask_b = offs_b < B
        mask_n = offs_n < N
        # Accumulate match counts in int32
        match = tl.zeros((BLOCK_B, BLOCK_N), dtype=tl.int32)
        for p0 in range(0, P, BLOCK_P):
            p_idx = p0 + offs_p
            mask_p = p_idx < P
            # Load x[B, P] block
            x_ptrs = (x_ptr + offs_b[:, None] * stride_xb
                      + p_idx[None, :] * stride_xp)
            w_ptrs = (w_ptr + offs_n[:, None] * stride_wn
                      + p_idx[None, :] * stride_wp)
            x_tile = tl.load(x_ptrs,
                             mask=(mask_b[:, None] & mask_p[None, :]),
                             other=0).to(tl.uint32)
            w_tile = tl.load(w_ptrs,
                             mask=(mask_n[:, None] & mask_p[None, :]),
                             other=0).to(tl.uint32)
            # Broadcast XOR over (B, N, BLOCK_P)
            xnor = ~(x_tile[:, None, :] ^ w_tile[None, :, :])
            # popcount via SWAR (portable across triton versions)
            v = xnor
            v = v - ((v >> 1) & 0x55555555)
            v = (v & 0x33333333) + ((v >> 2) & 0x33333333)
            v = (v + (v >> 4)) & 0x0F0F0F0F
            pc = ((v * 0x01010101) >> 24) & 0xFF
            match += tl.sum(pc.to(tl.int32), axis=2)

        dot = (2 * match - K_padded - pad).to(tl.float32)
        y_val = scale * dot
        y_ptrs = (y_ptr + offs_b[:, None] * stride_yb
                  + offs_n[None, :] * stride_yn)
        tl.store(y_ptrs, y_val, mask=(mask_b[:, None] & mask_n[None, :]))


def xnor_popcount_triton(x_bits: torch.Tensor, w_bits: torch.Tensor,
                         K: int, alpha: float, beta: float) -> torch.Tensor:
    assert HAVE_TRITON, f"triton not installed: {TRITON_IMPORT_ERR}"
    assert x_bits.is_cuda and w_bits.is_cuda
    assert x_bits.dtype == torch.int32 and w_bits.dtype == torch.int32

    B, P = x_bits.shape
    N, _ = w_bits.shape
    K_padded = P * 32
    pad = K_padded - K
    scale = float(alpha * beta)

    y = torch.empty((B, N), dtype=torch.float32, device=x_bits.device)
    BLOCK_B, BLOCK_N, BLOCK_P = 16, 16, 32
    grid = ((B + BLOCK_B - 1) // BLOCK_B,
            (N + BLOCK_N - 1) // BLOCK_N)
    xnor_popcount_kernel[grid](
        x_bits, w_bits, y,
        B, N, P, K_padded, pad, scale,
        x_bits.stride(0), x_bits.stride(1),
        w_bits.stride(0), w_bits.stride(1),
        y.stride(0), y.stride(1),
        BLOCK_B=BLOCK_B, BLOCK_N=BLOCK_N, BLOCK_P=BLOCK_P,
    )
    return y


def pack_bits_gpu(x: torch.Tensor) -> tuple[torch.Tensor, int]:
    K = x.size(-1)
    P = (K + 31) // 32
    K_padded = P * 32
    if K_padded > K:
        pad = torch.ones(*x.shape[:-1], K_padded - K, dtype=x.dtype, device=x.device)
        x = torch.cat([x, pad], dim=-1)
    bits = (x > 0).to(torch.int32)
    bits = bits.reshape(*x.shape[:-1], P, 32)
    powers = (1 << torch.arange(32, device=x.device, dtype=torch.int32))
    return (bits * powers).sum(dim=-1).to(torch.int32).contiguous(), K


def main():
    print(f"python={sys.version.split()[0]}  torch={torch.__version__}  "
          f"cuda_available={torch.cuda.is_available()}  "
          f"hip={getattr(torch.version, 'hip', None)}  "
          f"triton={getattr(triton, '__version__', 'unknown') if HAVE_TRITON else 'MISSING'}")
    if not HAVE_TRITON:
        print(f"triton not installed: {TRITON_IMPORT_ERR}")
        sys.exit(2)
    if not torch.cuda.is_available():
        print("CUDA/ROCm device not available")
        sys.exit(2)

    device = torch.device("cuda")
    print("\n[correctness]")
    correctness = []
    for B, K, N in [(8, 64, 16), (16, 256, 128), (32, 1023, 256), (64, 4096, 512)]:
        g = torch.Generator(device=device).manual_seed(0)
        x = torch.randn(B, K, generator=g, device=device)
        w = torch.randn(N, K, generator=g, device=device)
        xp, _ = pack_bits_gpu(torch.sign(x))
        wp, _ = pack_bits_gpu(torch.sign(w))
        y = xnor_popcount_triton(xp, wp, K, 0.5, 1.3)
        y_ref = 0.5 * 1.3 * (torch.sign(x) @ torch.sign(w).t())
        diff = (y - y_ref).abs().max().item()
        ok = diff < 1e-3
        correctness.append({"B": B, "K": K, "N": N, "max_diff": diff, "passed": ok})
        print(f"  {'PASS' if ok else 'FAIL'}  B={B:>3} K={K:>5} N={N:>4}  "
              f"max_abs_diff={diff:.3e}")

    print("\n[microbench]")
    rows = []
    for B, K, N in [(16, 256, 128), (64, 1024, 512), (128, 2048, 2048),
                    (256, 4096, 4096)]:
        g = torch.Generator(device=device).manual_seed(0)
        x = torch.randn(B, K, generator=g, device=device)
        w = torch.randn(N, K, generator=g, device=device)
        xp, _ = pack_bits_gpu(torch.sign(x))
        wp, _ = pack_bits_gpu(torch.sign(w))
        for _ in range(3):
            _ = xnor_popcount_triton(xp, wp, K, 0.5, 1.3)
        torch.cuda.synchronize()
        n_iter = 10
        t0 = time.time()
        for _ in range(n_iter):
            y = xnor_popcount_triton(xp, wp, K, 0.5, 1.3)
        torch.cuda.synchronize()
        t_xnor = (time.time() - t0) / n_iter

        xs = torch.sign(x).to(torch.bfloat16)
        ws = torch.sign(w).to(torch.bfloat16)
        for _ in range(3):
            _ = xs @ ws.t()
        torch.cuda.synchronize()
        t0 = time.time()
        for _ in range(n_iter):
            _ = (xs @ ws.t()) * (0.5 * 1.3)
        torch.cuda.synchronize()
        t_dense = (time.time() - t0) / n_iter

        ops = 2 * B * N * K
        rows.append({"B": B, "K": K, "N": N,
                     "t_xnor_sec": round(t_xnor, 6),
                     "t_dense_sec": round(t_dense, 6),
                     "xnor_tops": round(ops / (t_xnor * 1e12), 3),
                     "dense_tflops": round(ops / (t_dense * 1e12), 3),
                     "speedup": round(t_dense / t_xnor, 3)})
        r = rows[-1]
        print(f"  B={B:>4} K={K:>5} N={N:>5}  "
              f"dense={r['dense_tflops']:>6.2f} TFLOPS  "
              f"xnor_triton={r['xnor_tops']:>6.2f} TOPS  "
              f"speedup={r['speedup']:>5.2f}x")

    out = Path("/tmp/bp-xnor-triton")
    out.mkdir(parents=True, exist_ok=True)
    (out / "xnor_triton_results.json").write_text(json.dumps({
        "triton_version": getattr(triton, "__version__", "unknown"),
        "device": str(torch.cuda.get_device_name(0)),
        "hip": getattr(torch.version, "hip", None),
        "correctness": correctness,
        "microbench": rows,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
