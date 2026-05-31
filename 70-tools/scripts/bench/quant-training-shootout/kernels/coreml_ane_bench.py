"""Core ML + Apple Neural Engine (ANE) dense fp16 matmul bench on Mac M4.

Builds a tiny Core ML model that does y = x @ W.T + b for a fixed W, then
times inference under 4 compute units:
  - CPU_ONLY
  - CPU_AND_GPU
  - CPU_AND_NE         (allow Neural Engine)
  - ALL                (compiler chooses best dispatch)

Important hw context:
  - Apple M4 ANE peak (vendor-claimed): ~38 TOPS at fp16
  - ANE is NOT user-programmable — no custom XNOR-popcount kernel possible
  - Arbitrary GEMM may be dispatched to GPU or CPU even with ANE allowed
    if the shape isn't a conv-shaped op the ANE prefers
  - Core ML always casts to fp16 internally for ANE-eligible ops

Run via the dedicated python3.12 venv (coremltools 9.0 needs Python 3.12).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

import coremltools as ct


class LinearOnly(nn.Module):
    def __init__(self, K: int, N: int):
        super().__init__()
        self.w = nn.Linear(K, N, bias=False)

    def forward(self, x):
        return self.w(x)


COMPUTE_UNITS = {
    "CPU_ONLY": ct.ComputeUnit.CPU_ONLY,
    "CPU_AND_GPU": ct.ComputeUnit.CPU_AND_GPU,
    "CPU_AND_NE": ct.ComputeUnit.CPU_AND_NE,
    "ALL": ct.ComputeUnit.ALL,
}


def build_model(B: int, K: int, N: int, compute_unit_name: str) -> ct.models.MLModel:
    torch.manual_seed(0)
    model = LinearOnly(K, N).eval()
    # Trace
    example_input = torch.randn(B, K, dtype=torch.float32)
    traced = torch.jit.trace(model, example_input)
    mlmodel = ct.convert(
        traced,
        inputs=[ct.TensorType(name="x", shape=example_input.shape,
                              dtype=np.float32)],
        outputs=[ct.TensorType(name="y", dtype=np.float32)],
        convert_to="mlprogram",
        compute_precision=ct.precision.FLOAT16,  # ANE-eligible
        compute_units=COMPUTE_UNITS[compute_unit_name],
        minimum_deployment_target=ct.target.macOS14,
    )
    return mlmodel


def time_inference(mlmodel: ct.models.MLModel, B: int, K: int,
                   n_warmup: int = 5, n_iter: int = 20) -> float:
    x_np = np.random.randn(B, K).astype(np.float32)
    inputs = {"x": x_np}
    for _ in range(n_warmup):
        _ = mlmodel.predict(inputs)
    t0 = time.time()
    for _ in range(n_iter):
        _ = mlmodel.predict(inputs)
    return (time.time() - t0) / n_iter


def run_shape(B: int, K: int, N: int) -> list[dict]:
    rows = []
    ops = 2 * B * N * K
    for cu_name in ["CPU_ONLY", "CPU_AND_GPU", "CPU_AND_NE", "ALL"]:
        print(f"  building {cu_name}...", flush=True)
        try:
            t_build_0 = time.time()
            m = build_model(B, K, N, cu_name)
            t_build = time.time() - t_build_0
            print(f"    built in {t_build:.1f}s; running...", flush=True)
            t = time_inference(m, B, K, n_warmup=3, n_iter=10)
            row = {
                "B": B, "K": K, "N": N, "compute_units": cu_name,
                "build_sec": round(t_build, 2),
                "inference_sec_per_iter": round(t, 6),
                "tflops": round(ops / (t * 1e12), 3),
            }
            print(f"    -> {row['tflops']:.3f} TFLOPS  ({t*1000:.2f} ms/iter)",
                  flush=True)
        except Exception as e:
            import traceback
            row = {"B": B, "K": K, "N": N, "compute_units": cu_name,
                   "error": f"{type(e).__name__}: {str(e)[:150]}",
                   "tb": traceback.format_exc()[-400:]}
            print(f"    ERROR: {row['error']}", flush=True)
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shapes", nargs="+",
                    default=["16,256,128", "64,1024,512",
                             "128,2048,2048", "256,4096,4096"])
    ap.add_argument("--out", type=Path, default=Path("/tmp/bp-xnor-coreml-ane"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    import platform
    print(f"[coreml-ane] coremltools={ct.__version__}  torch={torch.__version__}  "
          f"platform={platform.machine()}  py={platform.python_version()}")

    all_rows = []
    for s in args.shapes:
        B, K, N = (int(v) for v in s.split(","))
        print(f"\n=== B={B} K={K} N={N} ===")
        rows = run_shape(B, K, N)
        all_rows.extend(rows)

    out = args.out / "coreml_ane_results.json"
    out.write_text(json.dumps({
        "coremltools_version": ct.__version__,
        "torch_version": torch.__version__,
        "platform": platform.machine(),
        "python_version": platform.python_version(),
        "results": all_rows,
    }, indent=2), encoding="utf-8")
    print(f"\n[done] wrote {out}")

    # Markdown summary by shape
    print("\n## Core ML + ANE dense fp16 matmul (Mac M4)\n")
    print("| shape | CPU_ONLY | CPU_AND_GPU | CPU_AND_NE | ALL |")
    print("|---|---|---|---|---|")
    by_shape = {}
    for r in all_rows:
        key = (r["B"], r["K"], r["N"])
        by_shape.setdefault(key, {})[r["compute_units"]] = r
    for (B, K, N), d in by_shape.items():
        cells = [f"{B},{K},{N}"]
        for cu in ["CPU_ONLY", "CPU_AND_GPU", "CPU_AND_NE", "ALL"]:
            r = d.get(cu, {})
            if "tflops" in r:
                cells.append(f"{r['tflops']:.3f} TFLOPS")
            else:
                cells.append("err")
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
