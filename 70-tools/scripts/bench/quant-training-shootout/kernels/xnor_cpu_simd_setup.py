"""Load xnor_cpu_simd.cpp via torch.utils.cpp_extension with arch-specific flags.

  - On x86_64: enables -mavx512f -mavx512vpopcntdq if compiler accepts them
  - On aarch64: NEON is default; enables -O3 -fopenmp
"""
from __future__ import annotations

import platform
import time
from pathlib import Path

import torch
from torch.utils.cpp_extension import load


HERE = Path(__file__).parent
SRC = HERE / "xnor_cpu_simd.cpp"


def build_cpu_extension(verbose: bool = False):
    extra_cflags = ["-O3", "-std=c++17"]
    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        extra_cflags += ["-mavx512f", "-mavx512vpopcntdq"]
    # On ARM Apple Silicon, NEON is always available; no extra flag needed.
    # OpenMP for the at::parallel_for backend.
    if platform.system() == "Darwin":
        # Use llvm-omp via brew if present, otherwise drop -fopenmp
        extra_cflags += ["-Xpreprocessor", "-fopenmp"]
    else:
        extra_cflags += ["-fopenmp"]
    extra_ldflags = []
    name = "xnor_cpu_simd"
    print(f"[build] {name}  arch={arch}  flags={extra_cflags}", flush=True)
    t0 = time.time()
    mod = load(
        name=name,
        sources=[str(SRC)],
        extra_cflags=extra_cflags,
        extra_ldflags=extra_ldflags,
        verbose=verbose,
        build_directory=str(HERE / "_build_cpu"),
    )
    print(f"[build] {name} done in {time.time()-t0:.1f}s; "
          f"backend={mod.xnor_cpu_backend()}", flush=True)
    return mod


def pack_bits_cpu(x: torch.Tensor) -> tuple[torch.Tensor, int]:
    """Pack ±-tensor [..., K] -> int32 [..., ceil(K/32)] on CPU."""
    K = x.size(-1)
    P = (K + 31) // 32
    K_padded = P * 32
    if K_padded > K:
        pad = torch.ones(*x.shape[:-1], K_padded - K, dtype=x.dtype, device=x.device)
        x = torch.cat([x, pad], dim=-1)
    bits = (x > 0).to(torch.int32)
    bits = bits.reshape(*x.shape[:-1], P, 32)
    powers = (1 << torch.arange(32, device=x.device, dtype=torch.int32))
    packed = (bits * powers).sum(dim=-1).to(torch.int32)
    return packed.contiguous(), K


if __name__ == "__main__":
    import sys, time, json
    print(f"python={sys.version.split()[0]}  torch={torch.__version__}  "
          f"platform={platform.machine()}")
    mod = build_cpu_extension(verbose=True)
    backend = mod.xnor_cpu_backend()

    # ----- correctness across sizes
    print("\n[correctness]")
    correctness = []
    for B, K, N in [(8, 64, 16), (16, 256, 128), (32, 1023, 256), (64, 4096, 512)]:
        rng = torch.Generator().manual_seed(0)
        x = torch.randn(B, K, generator=rng)
        w = torch.randn(N, K, generator=rng)
        xp, _ = pack_bits_cpu(torch.sign(x))
        wp, _ = pack_bits_cpu(torch.sign(w))
        y = mod.xnor_popcount_matmul_cpu(xp, wp, K, 0.5, 1.3)
        y_ref = 0.5 * 1.3 * (torch.sign(x) @ torch.sign(w).t())
        diff = (y - y_ref).abs().max().item()
        ok = diff < 1e-3
        correctness.append({"B": B, "K": K, "N": N, "max_diff": diff, "passed": ok})
        print(f"  {'PASS' if ok else 'FAIL'}  B={B:>3} K={K:>5} N={N:>4}  "
              f"max_abs_diff={diff:.3e}")

    # ----- microbench
    print("\n[microbench]")
    rows = []
    for B, K, N in [(16, 256, 128), (64, 1024, 512), (128, 2048, 2048),
                    (256, 4096, 4096)]:
        rng = torch.Generator().manual_seed(0)
        x = torch.randn(B, K, generator=rng)
        w = torch.randn(N, K, generator=rng)
        xp, _ = pack_bits_cpu(torch.sign(x))
        wp, _ = pack_bits_cpu(torch.sign(w))

        # warmup
        for _ in range(2):
            _ = mod.xnor_popcount_matmul_cpu(xp, wp, K, 0.5, 1.3)
        t0 = time.time()
        n_iter = 5
        for _ in range(n_iter):
            y = mod.xnor_popcount_matmul_cpu(xp, wp, K, 0.5, 1.3)
        t_xnor = (time.time() - t0) / n_iter

        # Dense bf16 CPU reference (sign(x) @ sign(w).T)
        xs = torch.sign(x).to(torch.bfloat16)
        ws = torch.sign(w).to(torch.bfloat16)
        for _ in range(2):
            _ = xs @ ws.t()
        t0 = time.time()
        for _ in range(n_iter):
            y_dense = (xs @ ws.t()) * (0.5 * 1.3)
        t_dense = (time.time() - t0) / n_iter

        ops = 2 * B * N * K
        rows.append({
            "B": B, "K": K, "N": N,
            "t_xnor_cpu_sec": round(t_xnor, 6),
            "t_dense_bf16_sec": round(t_dense, 6),
            "xnor_cpu_tops": round(ops / (t_xnor * 1e12), 3),
            "dense_bf16_tflops": round(ops / (t_dense * 1e12), 3),
            "speedup_xnor_vs_dense": round(t_dense / t_xnor, 3),
        })
        r = rows[-1]
        print(f"  B={B:>4} K={K:>5} N={N:>5}  "
              f"dense_bf16={r['dense_bf16_tflops']:>6.3f} TFLOPS  "
              f"xnor_cpu={r['xnor_cpu_tops']:>6.3f} TOPS  "
              f"speedup={r['speedup_xnor_vs_dense']:>5.2f}x")

    out = Path("/tmp/bp-xnor-cpu-simd")
    out.mkdir(parents=True, exist_ok=True)
    (out / "xnor_cpu_simd_results.json").write_text(json.dumps({
        "backend": backend,
        "platform": platform.machine(),
        "correctness": correctness,
        "microbench": rows,
    }, indent=2), encoding="utf-8")
    print(f"\n[done] backend={backend}  results -> {out}")
