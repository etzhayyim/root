"""Build + benchmark CUDA/HIP XNOR-popcount kernel.

Auto-detects NVIDIA vs ROCm. On ROCm (e.g. EVO gfx1151), PyTorch's
cpp_extension.load() runs hipify on the .cu source and compiles via hipcc.
"""
from __future__ import annotations

import json
import platform
import time
from pathlib import Path

import torch
from torch.utils.cpp_extension import load

HERE = Path(__file__).parent
SRC = HERE / "xnor_cuda_hip.cu"


def build_cuda_extension(verbose: bool = False):
    is_hip = getattr(torch.version, "hip", None) is not None
    extra_cuda_cflags = ["-O3"]
    if is_hip:
        extra_cuda_cflags += ["-std=c++17"]
    else:
        extra_cuda_cflags += ["-std=c++17", "-use_fast_math"]
    build_dir = HERE / ("_build_hip" if is_hip else "_build_cuda")
    build_dir.mkdir(parents=True, exist_ok=True)
    name = "xnor_cuda_hip"
    print(f"[build] {name}  is_hip={is_hip}  flags={extra_cuda_cflags}", flush=True)
    t0 = time.time()
    mod = load(
        name=name,
        sources=[str(SRC)],
        extra_cuda_cflags=extra_cuda_cflags,
        extra_cflags=["-O3", "-std=c++17"],
        verbose=verbose,
        build_directory=str(build_dir),
    )
    print(f"[build] done in {time.time()-t0:.1f}s; backend={mod.xnor_cuda_backend()}",
          flush=True)
    return mod


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
    packed = (bits * powers).sum(dim=-1).to(torch.int32)
    return packed.contiguous(), K


def main():
    import sys
    print(f"python={sys.version.split()[0]}  torch={torch.__version__}  "
          f"cuda_available={torch.cuda.is_available()}  "
          f"hip={getattr(torch.version, 'hip', None)}")
    if not torch.cuda.is_available():
        print("CUDA/ROCm device not available; aborting.")
        sys.exit(2)

    mod = build_cuda_extension(verbose=True)
    backend = mod.xnor_cuda_backend()
    device = torch.device("cuda")

    print("\n[correctness]")
    correctness = []
    for B, K, N in [(8, 64, 16), (16, 256, 128), (32, 1023, 256), (64, 4096, 512)]:
        g = torch.Generator(device=device).manual_seed(0)
        x = torch.randn(B, K, generator=g, device=device)
        w = torch.randn(N, K, generator=g, device=device)
        xp, _ = pack_bits_gpu(torch.sign(x))
        wp, _ = pack_bits_gpu(torch.sign(w))
        y = mod.xnor_popcount_matmul_cuda(xp, wp, K, 0.5, 1.3)
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
            _ = mod.xnor_popcount_matmul_cuda(xp, wp, K, 0.5, 1.3)
        torch.cuda.synchronize()
        n_iter = 10
        t0 = time.time()
        for _ in range(n_iter):
            y = mod.xnor_popcount_matmul_cuda(xp, wp, K, 0.5, 1.3)
        torch.cuda.synchronize()
        t_xnor = (time.time() - t0) / n_iter

        xs = torch.sign(x).to(torch.bfloat16)
        ws = torch.sign(w).to(torch.bfloat16)
        for _ in range(3):
            _ = xs @ ws.t()
        torch.cuda.synchronize()
        t0 = time.time()
        for _ in range(n_iter):
            y_d = (xs @ ws.t()) * (0.5 * 1.3)
        torch.cuda.synchronize()
        t_dense = (time.time() - t0) / n_iter

        ops = 2 * B * N * K
        rows.append({
            "B": B, "K": K, "N": N,
            "t_xnor_gpu_sec": round(t_xnor, 6),
            "t_dense_bf16_gpu_sec": round(t_dense, 6),
            "xnor_gpu_tops": round(ops / (t_xnor * 1e12), 3),
            "dense_bf16_gpu_tflops": round(ops / (t_dense * 1e12), 3),
            "speedup_xnor_vs_dense": round(t_dense / t_xnor, 3),
        })
        r = rows[-1]
        print(f"  B={B:>4} K={K:>5} N={N:>5}  "
              f"dense_bf16={r['dense_bf16_gpu_tflops']:>6.2f} TFLOPS  "
              f"xnor_gpu={r['xnor_gpu_tops']:>6.2f} TOPS  "
              f"speedup={r['speedup_xnor_vs_dense']:>5.2f}x")

    out = Path("/tmp/bp-xnor-cuda-hip")
    out.mkdir(parents=True, exist_ok=True)
    (out / "xnor_cuda_hip_results.json").write_text(json.dumps({
        "backend": backend,
        "platform": platform.machine(),
        "torch_version": torch.__version__,
        "hip": getattr(torch.version, "hip", None),
        "device": str(torch.cuda.get_device_name(0)),
        "correctness": correctness,
        "microbench": rows,
    }, indent=2), encoding="utf-8")
    print(f"\n[done] backend={backend}  results -> {out}")


if __name__ == "__main__":
    main()
