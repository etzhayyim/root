"""Dense quantized matmul shootout on Mac M4 Metal — full picture for the
bit-packed XNOR-popcount kernels doc.

What runs natively on Apple M4 silicon:
  - fp32 dense matmul        (MLX, baseline)
  - bf16 dense matmul        (MLX)
  - fp16 dense matmul        (MLX)
  - int8 quantized matmul    (MLX mx.quantize + mx.quantized_matmul, group=64)
  - int4 quantized matmul    (MLX mx.quantized_matmul bits=4)
  - int2 quantized matmul    (MLX mx.quantized_matmul bits=2) — "1.58-bit proxy"

NOT runnable on M4 silicon:
  - fp8  — Apple GPU has no fp8 ALU (NV H100 / AMD MI300X only)
  - fp4  — same — only B200 / Blackwell-class hw

This bench reports throughput against the equivalent inner-dim
unsigned operation (B*N*K MACs ≈ 2*B*N*K FLOPs/OPs).

Companion to xnor_metal_mlx.py + xnor_cpu_simd_setup.py; all numbers
land in /tmp/bp-xnor-metal-quant-bench/.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import mlx.core as mx
import numpy as np


def _sync():
    # mlx is lazy; force evaluation completion
    mx.synchronize() if hasattr(mx, "synchronize") else None


def bench_dense(x: mx.array, w: mx.array, n_warmup=5, n_iter=20) -> float:
    """Time x @ w.T over n_iter. Returns seconds/iter."""
    for _ in range(n_warmup):
        y = x @ w.T
        mx.eval(y)
    _sync()
    t0 = time.time()
    for _ in range(n_iter):
        y = x @ w.T
        mx.eval(y)
    _sync()
    return (time.time() - t0) / n_iter


def bench_quantized(x: mx.array, q_w, scales, biases, group_size: int,
                    bits: int, n_warmup=5, n_iter=20) -> float:
    """Time mx.quantized_matmul(x, q_w, scales, biases, transpose=True, ...)."""
    for _ in range(n_warmup):
        y = mx.quantized_matmul(x, q_w, scales, biases,
                                transpose=True, group_size=group_size, bits=bits)
        mx.eval(y)
    _sync()
    t0 = time.time()
    for _ in range(n_iter):
        y = mx.quantized_matmul(x, q_w, scales, biases,
                                transpose=True, group_size=group_size, bits=bits)
        mx.eval(y)
    _sync()
    return (time.time() - t0) / n_iter


def run_shape(B: int, K: int, N: int, group_size: int = 64) -> dict:
    rng = np.random.default_rng(0)
    x_np = rng.standard_normal((B, K)).astype(np.float32)
    w_np = rng.standard_normal((N, K)).astype(np.float32)
    ops = 2 * B * N * K
    row = {"B": B, "K": K, "N": N, "ops": ops, "group_size": group_size}

    # ---- fp32 baseline
    x = mx.array(x_np, dtype=mx.float32)
    w = mx.array(w_np, dtype=mx.float32)
    mx.eval(x, w)
    t = bench_dense(x, w)
    row["fp32_dense_sec"] = round(t, 6)
    row["fp32_dense_tflops"] = round(ops / (t * 1e12), 3)

    # ---- bf16 dense
    x_bf = x.astype(mx.bfloat16); w_bf = w.astype(mx.bfloat16); mx.eval(x_bf, w_bf)
    t = bench_dense(x_bf, w_bf)
    row["bf16_dense_sec"] = round(t, 6)
    row["bf16_dense_tflops"] = round(ops / (t * 1e12), 3)

    # ---- fp16 dense
    x_h = x.astype(mx.float16); w_h = w.astype(mx.float16); mx.eval(x_h, w_h)
    t = bench_dense(x_h, w_h)
    row["fp16_dense_sec"] = round(t, 6)
    row["fp16_dense_tflops"] = round(ops / (t * 1e12), 3)

    # ---- int8 quantized (group_size=64, bits=8)
    try:
        q_w, scales, biases = mx.quantize(w, group_size=group_size, bits=8)
        mx.eval(q_w, scales, biases)
        t = bench_quantized(x_h, q_w, scales, biases, group_size, 8)
        row["int8_quant_sec"] = round(t, 6)
        row["int8_quant_tops"] = round(ops / (t * 1e12), 3)
    except Exception as e:
        row["int8_quant_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # ---- int4 quantized
    try:
        q_w, scales, biases = mx.quantize(w, group_size=group_size, bits=4)
        mx.eval(q_w, scales, biases)
        t = bench_quantized(x_h, q_w, scales, biases, group_size, 4)
        row["int4_quant_sec"] = round(t, 6)
        row["int4_quant_tops"] = round(ops / (t * 1e12), 3)
    except Exception as e:
        row["int4_quant_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # ---- int2 quantized (~1.58 bit proxy)
    try:
        q_w, scales, biases = mx.quantize(w, group_size=group_size, bits=2)
        mx.eval(q_w, scales, biases)
        t = bench_quantized(x_h, q_w, scales, biases, group_size, 2)
        row["int2_quant_sec"] = round(t, 6)
        row["int2_quant_tops"] = round(ops / (t * 1e12), 3)
    except Exception as e:
        row["int2_quant_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # ---- fp8 / fp4 — NOT supported on M4 silicon. Record explicitly.
    row["fp8_status"] = "unsupported on Apple M4 silicon (no fp8 ALU)"
    row["fp4_status"] = "unsupported on Apple M4 silicon (no fp4 ALU)"

    return row


def main():
    shapes = [(16, 256, 128), (64, 1024, 512),
              (128, 2048, 2048), (256, 4096, 4096)]
    print(f"[dense-quant-metal] mlx={mx.__version__}  device={mx.default_device()}")
    print(f"[dense-quant-metal] running {len(shapes)} shapes")

    rows = []
    for B, K, N in shapes:
        print(f"\n--- B={B} K={K} N={N} ---")
        r = run_shape(B, K, N)
        rows.append(r)
        print(f"  fp32  : {r['fp32_dense_tflops']:>6.2f} TFLOPS")
        print(f"  bf16  : {r['bf16_dense_tflops']:>6.2f} TFLOPS")
        print(f"  fp16  : {r['fp16_dense_tflops']:>6.2f} TFLOPS")
        if "int8_quant_tops" in r:
            print(f"  int8  : {r['int8_quant_tops']:>6.2f} TOPS")
        if "int4_quant_tops" in r:
            print(f"  int4  : {r['int4_quant_tops']:>6.2f} TOPS")
        if "int2_quant_tops" in r:
            print(f"  int2  : {r['int2_quant_tops']:>6.2f} TOPS  (≈1.58-bit)")

    out = Path("/tmp/bp-xnor-metal-quant-bench")
    out.mkdir(parents=True, exist_ok=True)
    (out / "dense_quant_metal_results.json").write_text(json.dumps({
        "mlx_version": mx.__version__,
        "device": str(mx.default_device()),
        "shapes": shapes,
        "results": rows,
        "fp8_status": "unsupported on Apple M4 silicon",
        "fp4_status": "unsupported on Apple M4 silicon",
    }, indent=2), encoding="utf-8")
    print(f"\n[done] wrote {out / 'dense_quant_metal_results.json'}")

    # Markdown summary
    print("\n## Dense quant matmul on Apple M4 (Metal via MLX)")
    print()
    cols = ["fp32_dense_tflops", "bf16_dense_tflops", "fp16_dense_tflops",
            "int8_quant_tops", "int4_quant_tops", "int2_quant_tops"]
    head = "| shape | " + " | ".join(c.replace("_", " ").replace("dense ", "").replace("quant ", "")
                                     for c in cols) + " |"
    sep = "|---|" + "---|" * len(cols)
    print(head); print(sep)
    for r in rows:
        cells = [f"{r['B']},{r['K']},{r['N']}"] + [
            f"{r.get(c, '—'):>6}" if c in r else "—" for c in cols
        ]
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
