"""Bit-packed XNOR-popcount matmul on Apple Silicon via MLX Metal kernel.

Uses `mlx.core.fast.metal_kernel` to register a custom MSL kernel. The
kernel computes:
    y[i, j] = alpha * beta * (2 * popcount( ~(x_bits[i] ^ w_bits[j]) ) - K)

Each thread computes one output (i, j) by XORing its row of x_bits with
its column of w_bits, popcount'ing each uint32 with the MSL builtin
`popcount(uint)`, summing, and applying the scale.

This is the kernel that actually unlocks the 1-bit speedup on Apple
silicon (M1/M2/M3/M4): popcount(uint) compiles to a single hardware
instruction on the Apple GPU (per Metal Feature Set tables / ISA docs).

Run:
  python xnor_metal_mlx.py                # correctness + microbench
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
# Note: do NOT import torch here — it conflicts with mlx OpenMP runtime on
# Apple Silicon (pthread_mutex_init failure). Use numpy for the reference.


_KERNEL_SRC = """
    // Inputs:
    //   x_bits: uint32 [B, P]
    //   w_bits: uint32 [N, P]
    //   K:      uint32 (real inner dim before padding)
    //   alpha:  float
    //   beta:   float
    // Output:
    //   y: float [B, N]
    //
    // Thread grid: (B, N, 1); each thread computes y[i, j].

    uint i = thread_position_in_grid.x;
    uint j = thread_position_in_grid.y;
    uint B = x_bits_shape[0];
    uint N = w_bits_shape[0];
    uint P = x_bits_shape[1];
    if (i >= B || j >= N) return;

    uint match = 0;
    for (uint p = 0; p < P; ++p) {
        uint xb = x_bits[i * P + p];
        uint wb = w_bits[j * P + p];
        // XNOR = ~(a ^ b); popcount counts matching bits.
        match += popcount(~(xb ^ wb));
    }
    uint K_padded = P * 32u;
    int pad = (int)K_padded - (int)K[0];
    // dot_padded = 2*match - K_padded ; dot_real = dot_padded - pad
    int dot = (int)(2u * match) - (int)K_padded - pad;
    y[i * N + j] = alpha[0] * beta[0] * (float)dot;
"""

_xnor_kernel = None


def _get_kernel():
    global _xnor_kernel
    if _xnor_kernel is None:
        _xnor_kernel = mx.fast.metal_kernel(
            name="xnor_popcount_matmul",
            input_names=["x_bits", "w_bits", "K", "alpha", "beta"],
            output_names=["y"],
            source=_KERNEL_SRC,
            ensure_row_contiguous=True,
        )
    return _xnor_kernel


def pack_bits_mlx(x: mx.array) -> tuple[mx.array, int]:
    """Pack a sign tensor [..., K] into uint32 [..., ceil(K/32)]."""
    K = x.shape[-1]
    P = (K + 31) // 32
    K_padded = P * 32
    if K_padded > K:
        pad = mx.ones((*x.shape[:-1], K_padded - K), dtype=x.dtype)
        x = mx.concatenate([x, pad], axis=-1)
    bits = (x > 0).astype(mx.uint32)
    bits = bits.reshape(*x.shape[:-1], P, 32)
    # mlx doesn't support `int << array`; build powers via mx.power
    powers = mx.power(mx.array(2, dtype=mx.uint32),
                      mx.arange(32, dtype=mx.uint32))
    packed = (bits * powers).sum(axis=-1).astype(mx.uint32)
    return packed, K


def xnor_popcount_matmul_mlx(x_bits: mx.array, w_bits: mx.array,
                              K: int, alpha: float, beta: float) -> mx.array:
    B = x_bits.shape[0]
    N = w_bits.shape[0]
    kernel = _get_kernel()
    out = kernel(
        inputs=[x_bits, w_bits,
                mx.array([K], dtype=mx.uint32),
                mx.array([alpha], dtype=mx.float32),
                mx.array([beta], dtype=mx.float32)],
        output_shapes=[(B, N)],
        output_dtypes=[mx.float32],
        grid=(B, N, 1),
        threadgroup=(min(B, 8), min(N, 8), 1),
    )[0]
    return out


# ----- reference via PyTorch for verify ----------------------------------

def dense_ref_numpy(x_np: np.ndarray, w_np: np.ndarray,
                    alpha: float, beta: float) -> np.ndarray:
    xs = np.sign(x_np).astype(np.float32)
    ws = np.sign(w_np).astype(np.float32)
    dot = xs @ ws.T
    return (alpha * beta * dot).astype(np.float32)


def verify(B: int, K: int, N: int, alpha: float = 0.5, beta: float = 1.3) -> dict:
    rng = np.random.default_rng(0)
    x_np = rng.standard_normal((B, K)).astype(np.float32)
    w_np = rng.standard_normal((N, K)).astype(np.float32)

    y_ref = dense_ref_numpy(x_np, w_np, alpha, beta)

    x_mx = mx.array(np.sign(x_np))
    w_mx = mx.array(np.sign(w_np))
    x_bits, K_x = pack_bits_mlx(x_mx)
    w_bits, K_w = pack_bits_mlx(w_mx)
    assert K_x == K and K_w == K

    y_mlx = xnor_popcount_matmul_mlx(x_bits, w_bits, K, alpha, beta)
    mx.eval(y_mlx)
    y_np = np.array(y_mlx)
    diff = float(np.abs(y_ref - y_np).max())
    return {"B": B, "K": K, "N": N, "max_abs_diff": diff,
            "passed": diff < 1e-3}


def microbench(B: int, K: int, N: int, alpha: float = 0.5, beta: float = 1.3,
               n_warmup: int = 5, n_iter: int = 20) -> dict:
    rng = np.random.default_rng(0)
    x_np = rng.standard_normal((B, K)).astype(np.float32)
    w_np = rng.standard_normal((N, K)).astype(np.float32)

    x_mx = mx.array(np.sign(x_np))
    w_mx = mx.array(np.sign(w_np))
    x_bits, _ = pack_bits_mlx(x_mx)
    w_bits, _ = pack_bits_mlx(w_mx)
    mx.eval(x_bits, w_bits)   # force materialize

    for _ in range(n_warmup):
        y = xnor_popcount_matmul_mlx(x_bits, w_bits, K, alpha, beta)
        mx.eval(y)

    t0 = time.time()
    for _ in range(n_iter):
        y = xnor_popcount_matmul_mlx(x_bits, w_bits, K, alpha, beta)
        mx.eval(y)
    t_xnor = (time.time() - t0) / n_iter

    # MLX bf16 dense matmul for comparison
    xs_mx = mx.array(np.sign(x_np)).astype(mx.bfloat16)
    ws_mx = mx.array(np.sign(w_np)).astype(mx.bfloat16)
    mx.eval(xs_mx, ws_mx)
    for _ in range(n_warmup):
        y = (xs_mx @ ws_mx.T) * (alpha * beta)
        mx.eval(y)
    t0 = time.time()
    for _ in range(n_iter):
        y = (xs_mx @ ws_mx.T) * (alpha * beta)
        mx.eval(y)
    t_dense = (time.time() - t0) / n_iter

    ops = 2 * B * N * K
    return {
        "B": B, "K": K, "N": N,
        "t_dense_bf16_sec": round(t_dense, 6),
        "t_xnor_metal_sec": round(t_xnor, 6),
        "speedup_xnor_vs_dense": round(t_dense / t_xnor, 3),
        "dense_bf16_tflops": round(ops / (t_dense * 1e12), 3),
        "xnor_metal_tops": round(ops / (t_xnor * 1e12), 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shapes", nargs="+",
                    default=["16,256,128", "64,1024,512",
                             "128,2048,2048", "256,4096,4096"])
    ap.add_argument("--out", type=Path,
                    default=Path("/tmp/bp-xnor-mlx-metal"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"[xnor-metal-mlx] mlx={mx.__version__} device={mx.default_device()}")

    print("\n[xnor-metal-mlx] correctness:")
    correctness = []
    for B, K, N in [(8, 64, 16), (16, 256, 128), (32, 1023, 256), (64, 4096, 512)]:
        r = verify(B, K, N)
        correctness.append(r)
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  {mark}  B={B:>3} K={K:>5} N={N:>4}  "
              f"max_abs_diff={r['max_abs_diff']:.3e}")

    print("\n[xnor-metal-mlx] microbench:")
    rows = []
    for s in args.shapes:
        B, K, N = (int(v) for v in s.split(","))
        r = microbench(B, K, N)
        rows.append(r)
        print(f"  B={B:>4} K={K:>5} N={N:>5}  "
              f"dense={r['dense_bf16_tflops']:>6.2f} TFLOPS  "
              f"XNOR_metal={r['xnor_metal_tops']:>6.2f} TOPS  "
              f"speedup={r['speedup_xnor_vs_dense']:>5.2f}x")

    out_path = args.out / "xnor_metal_mlx_results.json"
    out_path.write_text(json.dumps({
        "mlx_version": str(mx.__version__),
        "device": str(mx.default_device()),
        "correctness": correctness,
        "microbench": rows,
    }, indent=2), encoding="utf-8")
    print(f"\n[xnor-metal-mlx] wrote {out_path}")


if __name__ == "__main__":
    main()
