"""5 additional low-bit matmul techniques on Mac M4 Metal (via MLX):

  1. AND-popcount        — both operands in {0, 1}; y = α·popcount(W AND X)
  2. Bit-slice 2-bit W   — decompose W into 2 planes; y = Σ_b 2^b · (XNOR-popcount of x with W_b)
  3. Bit-slice 4-bit W   — same with 4 planes
  4. Bit-serial 2x2 GEMM — both W and X are 2-bit; 4 popcounts per inner product
  5. LUT matmul          — 8-bit × 8-bit precomputed 64 KB table, byte-tile lookup

All kernels share the same `(B, K, N)` input shape and produce a
[B, N] fp32 output. Compared head-to-head with the prior XNOR-popcount
Metal kernel + dense fp/int paths.

Companion to:
  - kernels/xnor_metal_mlx.py        (XNOR-popcount, ±1)
  - kernels/dense_quant_metal_bench.py  (fp32 / bf16 / fp16 / int8 / int4 / int2)
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import mlx.core as mx
import numpy as np


# =========================================================================
# Pack utilities (sign vs unsigned)
# =========================================================================

def _powers32():
    return mx.power(mx.array(2, dtype=mx.uint32),
                    mx.arange(32, dtype=mx.uint32))


def pack_sign_bits(x: mx.array) -> tuple[mx.array, int]:
    """±1 -> bit: positive=1, non-positive=0. Pad with +1."""
    K = x.shape[-1]
    P = (K + 31) // 32
    Kp = P * 32
    if Kp > K:
        x = mx.concatenate([x, mx.ones((*x.shape[:-1], Kp - K), dtype=x.dtype)], axis=-1)
    bits = (x > 0).astype(mx.uint32).reshape(*x.shape[:-1], P, 32)
    return (bits * _powers32()).sum(axis=-1).astype(mx.uint32), K


def pack_unsigned_bits(x: mx.array, K: int) -> mx.array:
    """{0, 1} -> bit-packed uint32 [..., ceil(K/32)]. Pad with 0."""
    P = (K + 31) // 32
    Kp = P * 32
    if Kp > K:
        x = mx.concatenate([x, mx.zeros((*x.shape[:-1], Kp - K), dtype=x.dtype)], axis=-1)
    bits = (x > 0).astype(mx.uint32).reshape(*x.shape[:-1], P, 32)
    return (bits * _powers32()).sum(axis=-1).astype(mx.uint32)


def quantize_to_bits(x: mx.array, n_bits: int) -> mx.array:
    """Map x ∈ ℝ to {0, ..., 2^n_bits - 1} via per-tensor min-max scaling.
    Returns uint32 with values in [0, 2^n_bits - 1]. Used for bit-slice."""
    lo, hi = x.min(), x.max()
    levels = (1 << n_bits) - 1
    norm = (x - lo) / (hi - lo + 1e-9)
    q = mx.round(norm * levels).astype(mx.uint32)
    return q


def split_bit_planes(q: mx.array, n_bits: int) -> list[mx.array]:
    """Decompose a multi-bit value [..., K] uint32 into n_bits planes
    each [..., K] uint32 ∈ {0, 1} (bit b of original)."""
    return [((q >> b) & 1).astype(mx.uint32) for b in range(n_bits)]


# =========================================================================
# Kernel 1: AND-popcount (both operands unsigned binary)
# =========================================================================

_AND_KERNEL_SRC = """
    uint i = thread_position_in_grid.x;
    uint j = thread_position_in_grid.y;
    uint B = x_bits_shape[0];
    uint N = w_bits_shape[0];
    uint P = x_bits_shape[1];
    if (i >= B || j >= N) return;

    uint cnt = 0;
    for (uint p = 0; p < P; ++p) {
        cnt += popcount(x_bits[i * P + p] & w_bits[j * P + p]);
    }
    y[i * N + j] = alpha[0] * (float)cnt;
"""

_and_kernel = None
def _and_get():
    global _and_kernel
    if _and_kernel is None:
        _and_kernel = mx.fast.metal_kernel(
            name="and_popcount_matmul",
            input_names=["x_bits", "w_bits", "alpha"],
            output_names=["y"],
            source=_AND_KERNEL_SRC,
            ensure_row_contiguous=True,
        )
    return _and_kernel


def and_popcount_matmul(x_bits: mx.array, w_bits: mx.array, alpha: float) -> mx.array:
    B, N = x_bits.shape[0], w_bits.shape[0]
    out = _and_get()(
        inputs=[x_bits, w_bits, mx.array([alpha], dtype=mx.float32)],
        output_shapes=[(B, N)],
        output_dtypes=[mx.float32],
        grid=(B, N, 1),
        threadgroup=(min(B, 8), min(N, 8), 1),
    )[0]
    return out


# =========================================================================
# Kernel 2: Bit-slice (W is N_w-bit, X is 1-bit) — N_w XNOR-popcounts
# =========================================================================
# We reuse the original XNOR-popcount kernel per plane and sum with 2^b scales.

_XNOR_KERNEL_SRC = """
    uint i = thread_position_in_grid.x;
    uint j = thread_position_in_grid.y;
    uint B = x_bits_shape[0];
    uint N = w_bits_shape[0];
    uint P = x_bits_shape[1];
    if (i >= B || j >= N) return;

    uint match = 0;
    for (uint p = 0; p < P; ++p) {
        match += popcount(~(x_bits[i * P + p] ^ w_bits[j * P + p]));
    }
    uint K_padded = P * 32u;
    int dot = (int)(2u * match) - (int)K_padded;
    y[i * N + j] = alpha[0] * (float)dot;
"""

_xnor_kernel = None
def _xnor_get():
    global _xnor_kernel
    if _xnor_kernel is None:
        _xnor_kernel = mx.fast.metal_kernel(
            name="xnor_popcount_bitslice",
            input_names=["x_bits", "w_bits", "alpha"],
            output_names=["y"],
            source=_XNOR_KERNEL_SRC,
            ensure_row_contiguous=True,
        )
    return _xnor_kernel


def xnor_popcount_one(x_bits, w_bits, alpha=1.0):
    B, N = x_bits.shape[0], w_bits.shape[0]
    return _xnor_get()(
        inputs=[x_bits, w_bits, mx.array([alpha], dtype=mx.float32)],
        output_shapes=[(B, N)],
        output_dtypes=[mx.float32],
        grid=(B, N, 1),
        threadgroup=(min(B, 8), min(N, 8), 1),
    )[0]


def bit_slice_matmul_W(x_signs: mx.array, w_real: mx.array,
                       n_w_bits: int, alpha: float = 1.0) -> mx.array:
    """W decomposed into n_w_bits planes, X stays 1-bit.
    Result = alpha * Σ_b 2^b · (sign(X) · W_b_signed_plane)
    where W_b is the b-th bit of quantized W mapped to ±1 (1 stays +1,
    0 maps to -1) before bit-packing for the XNOR-popcount kernel.
    """
    K = w_real.shape[-1]
    # Quantize W to n_w_bits, split into planes
    w_q = quantize_to_bits(w_real, n_w_bits)
    w_planes = split_bit_planes(w_q, n_w_bits)
    # Pack X (already ±) as sign-bits
    x_bits, _ = pack_sign_bits(x_signs)
    accum = None
    for b in range(n_w_bits):
        # Map W_b ∈ {0,1} -> ±1: 1->+1, 0->-1, then pack as sign
        w_pm1 = (w_planes[b].astype(mx.float32) * 2.0 - 1.0)
        w_bits = pack_unsigned_bits(w_pm1 > 0, K)
        # XNOR-popcount this plane
        y_b = xnor_popcount_one(x_bits, w_bits, alpha=1.0)
        weight = float(1 << b)
        accum = y_b * weight if accum is None else accum + y_b * weight
    return accum * alpha


# =========================================================================
# Kernel 3: Bit-serial GEMM (W=N_w bits, X=N_x bits) — N_w·N_x popcounts
# =========================================================================

def bit_serial_gemm(x_real: mx.array, w_real: mx.array,
                    n_x_bits: int, n_w_bits: int,
                    alpha: float = 1.0) -> mx.array:
    """Both X and W decomposed into bit planes.
    Result = alpha * Σ_i Σ_j 2^(i+j) · popcount(X_i AND W_j)
    where each plane is bit-packed and the inner kernel is AND-popcount.
    """
    K = w_real.shape[-1]
    x_q = quantize_to_bits(x_real, n_x_bits)
    w_q = quantize_to_bits(w_real, n_w_bits)
    x_planes = split_bit_planes(x_q, n_x_bits)
    w_planes = split_bit_planes(w_q, n_w_bits)

    accum = None
    for i in range(n_x_bits):
        x_bits = pack_unsigned_bits(x_planes[i].astype(mx.float32), K)
        for j in range(n_w_bits):
            w_bits = pack_unsigned_bits(w_planes[j].astype(mx.float32), K)
            y_ij = and_popcount_matmul(x_bits, w_bits, alpha=1.0)
            weight = float(1 << (i + j))
            accum = y_ij * weight if accum is None else accum + y_ij * weight
    return accum * alpha


# =========================================================================
# Kernel 4: LUT matmul (8-bit × 8-bit precomputed)
# =========================================================================
# Idea: precompute a 256×256 byte table of all int8 × int8 products mod
# something useful (actually use int16 to hold full -127·127..127·127).
# For each output, sum K table lookups instead of K MACs.
# Storage: 256*256*2 = 128 KB (int16 table) — fits in M4 GPU L2 cache.

_LUT_KERNEL_SRC = """
    // x_q: uint8 [B, K] (values 0..255)
    // w_q: uint8 [N, K]
    // lut: int16 [256*256]
    // y:   float [B, N]

    uint i = thread_position_in_grid.x;
    uint j = thread_position_in_grid.y;
    uint B = x_q_shape[0];
    uint N = w_q_shape[0];
    uint K = x_q_shape[1];
    if (i >= B || j >= N) return;

    int acc = 0;
    for (uint k = 0; k < K; ++k) {
        uint8_t xv = x_q[i * K + k];
        uint8_t wv = w_q[j * K + k];
        acc += (int)lut[((uint)xv << 8) | (uint)wv];
    }
    y[i * N + j] = alpha[0] * (float)acc;
"""

_lut_kernel = None
def _lut_get():
    global _lut_kernel
    if _lut_kernel is None:
        _lut_kernel = mx.fast.metal_kernel(
            name="lut_matmul",
            input_names=["x_q", "w_q", "lut", "alpha"],
            output_names=["y"],
            source=_LUT_KERNEL_SRC,
            ensure_row_contiguous=True,
        )
    return _lut_kernel


def lut_matmul(x_real: mx.array, w_real: mx.array, alpha: float = 1.0) -> mx.array:
    """Quantize x, w to int8 (signed, -127..127), precompute the 256*256
    product table, then do byte-lookup matmul.

    Notation: store x in uint8 by mapping signed int8 (-128..127) -> 0..255.
    Table indexed by (xv << 8 | wv) of uint8 input maps to the original
    signed product.
    """
    K = w_real.shape[-1]
    # Per-tensor scale to int8 range
    sx = 127.0 / float(mx.abs(x_real).max())
    sw = 127.0 / float(mx.abs(w_real).max())
    # Signed int8 quant
    x_i8 = mx.clip(mx.round(x_real * sx), -127, 127).astype(mx.int8)
    w_i8 = mx.clip(mx.round(w_real * sw), -127, 127).astype(mx.int8)
    # Re-interpret as uint8 (two's-complement view) for table indexing
    x_u8 = x_i8.view(mx.uint8)
    w_u8 = w_i8.view(mx.uint8)

    # Build 256x256 int16 table: int(x_i8) * int(w_i8) for all x, w pairs
    vals = mx.arange(256, dtype=mx.int32)
    # Convert uint8 (0..255) -> signed int8 view (-128..127)
    signed = mx.where(vals < 128, vals, vals - 256)
    lut2d = signed[:, None] * signed[None, :]   # [256, 256] int32
    lut = lut2d.reshape(-1).astype(mx.int16)

    B, N = x_u8.shape[0], w_u8.shape[0]
    out = _lut_get()(
        inputs=[x_u8, w_u8, lut, mx.array([alpha / (sx * sw)], dtype=mx.float32)],
        output_shapes=[(B, N)],
        output_dtypes=[mx.float32],
        grid=(B, N, 1),
        threadgroup=(min(B, 8), min(N, 8), 1),
    )[0]
    return out


# =========================================================================
# Reference: dense fp32 sign·sign for correctness oracle
# =========================================================================

def dense_ref_signed(x_np: np.ndarray, w_np: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    xs = np.sign(x_np).astype(np.float32)
    ws = np.sign(w_np).astype(np.float32)
    return alpha * (xs @ ws.T)


def dense_ref_unsigned(x_np: np.ndarray, w_np: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    """For AND-popcount: both in {0,1}."""
    xb = (x_np > 0).astype(np.float32)
    wb = (w_np > 0).astype(np.float32)
    return alpha * (xb @ wb.T)


def dense_ref_real(x_np: np.ndarray, w_np: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    return alpha * (x_np.astype(np.float32) @ w_np.astype(np.float32).T)


# =========================================================================
# Microbench
# =========================================================================

def _sync():
    if hasattr(mx, "synchronize"):
        mx.synchronize()


def time_fn(fn, n_warmup=3, n_iter=10):
    for _ in range(n_warmup):
        y = fn()
        mx.eval(y)
    _sync()
    t0 = time.time()
    for _ in range(n_iter):
        y = fn()
        mx.eval(y)
    _sync()
    return (time.time() - t0) / n_iter, y


def run_shape(B: int, K: int, N: int) -> dict:
    rng = np.random.default_rng(0)
    x_np = rng.standard_normal((B, K)).astype(np.float32)
    w_np = rng.standard_normal((N, K)).astype(np.float32)
    x = mx.array(x_np); w = mx.array(w_np); mx.eval(x, w)
    ops = 2 * B * N * K
    row = {"B": B, "K": K, "N": N}

    # ----- 1) AND-popcount (unsigned {0,1})
    x_signs = mx.sign(x); w_signs = mx.sign(w)
    x_bits01 = pack_unsigned_bits((x_signs > 0).astype(mx.float32), K)
    w_bits01 = pack_unsigned_bits((w_signs > 0).astype(mx.float32), K)
    mx.eval(x_bits01, w_bits01)
    t, y = time_fn(lambda: and_popcount_matmul(x_bits01, w_bits01, 1.0))
    ref = dense_ref_unsigned(x_np, w_np)
    diff = float(np.abs(np.array(y) - ref).max())
    row["and_popcount_sec"] = round(t, 6)
    row["and_popcount_tops"] = round(ops / (t * 1e12), 3)
    row["and_popcount_max_diff"] = diff
    row["and_popcount_passed"] = diff < 1e-3

    # ----- 2) Bit-slice W=2bit, X=1bit
    try:
        t, _ = time_fn(lambda: bit_slice_matmul_W(x_signs, w, 2, 1.0))
        row["bitslice_W2_X1_sec"] = round(t, 6)
        row["bitslice_W2_X1_tops"] = round(ops / (t * 1e12), 3)
    except Exception as e:
        row["bitslice_W2_X1_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # ----- 3) Bit-slice W=4bit, X=1bit
    try:
        t, _ = time_fn(lambda: bit_slice_matmul_W(x_signs, w, 4, 1.0))
        row["bitslice_W4_X1_sec"] = round(t, 6)
        row["bitslice_W4_X1_tops"] = round(ops / (t * 1e12), 3)
    except Exception as e:
        row["bitslice_W4_X1_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # ----- 4) Bit-serial 2x2 GEMM
    try:
        t, _ = time_fn(lambda: bit_serial_gemm(x, w, 2, 2, 1.0))
        row["bitserial_2x2_sec"] = round(t, 6)
        row["bitserial_2x2_tops"] = round(ops / (t * 1e12), 3)
    except Exception as e:
        row["bitserial_2x2_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    # ----- 5) LUT matmul (8x8)
    try:
        t, _ = time_fn(lambda: lut_matmul(x, w, 1.0))
        row["lut_8x8_sec"] = round(t, 6)
        row["lut_8x8_tops"] = round(ops / (t * 1e12), 3)
    except Exception as e:
        row["lut_8x8_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    return row


def main():
    shapes = [(16, 256, 128), (64, 1024, 512),
              (128, 2048, 2048), (256, 4096, 4096)]
    print(f"[xnor-techniques] mlx={mx.__version__} device={mx.default_device()}")
    rows = []
    for B, K, N in shapes:
        print(f"\n--- B={B} K={K} N={N} ---")
        r = run_shape(B, K, N)
        rows.append(r)
        for label, key in [
            ("AND-popcount", "and_popcount_tops"),
            ("bit-slice W2x1", "bitslice_W2_X1_tops"),
            ("bit-slice W4x1", "bitslice_W4_X1_tops"),
            ("bit-serial 2x2", "bitserial_2x2_tops"),
            ("LUT 8x8",        "lut_8x8_tops"),
        ]:
            if key in r:
                print(f"  {label:18}: {r[key]:>6.3f} TOPS")
            else:
                err_key = key.replace("_tops", "_error")
                print(f"  {label:18}: ERROR {r.get(err_key, '?')[:90]}")

    out = Path("/tmp/bp-xnor-techniques-metal")
    out.mkdir(parents=True, exist_ok=True)
    (out / "xnor_techniques_results.json").write_text(json.dumps({
        "mlx_version": mx.__version__,
        "device": str(mx.default_device()),
        "shapes": shapes,
        "results": rows,
    }, indent=2), encoding="utf-8")
    print(f"\n[done] wrote {out / 'xnor_techniques_results.json'}")


if __name__ == "__main__":
    main()
