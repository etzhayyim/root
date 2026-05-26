#!/usr/bin/env python3
"""probe_rocm_moe.py — R1.0 deliverable per ADR-2605262100 §7.

Verify EVO-X2 ROCm 7.2.1 + Python 3.12 + torch 2.9.1+rocm7.2.1 can:
  1. Load microsoft/bitnet-b1.58-2B-4T-bf16 (HF master)
  2. Apply BitNetFFNWithMoE surgery to 1 layer (last layer)
  3. Run 1 forward step on random input
  4. Report memory profile (RAM peak)

Acceptance (per ADR-2605262100 §7 R1.0 row):
  - forward output finite (no NaN/Inf)
  - no OOM
  - total RAM ≤ 30 GB

Plus extra: report measured single-matmul throughput on relevant shape
(B=8, K=hidden=2048, N=hidden=2048) to ground truth R1.4 wall estimation
(ADR-2605262100 §8 memory budget + prior-turn TFLOPS measurement).
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import torch

# Add src/ to path so baien_moemoekyun is importable when running from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from baien_moemoekyun import (  # noqa: E402
    BaienMoEResidual,
    BitNetFFNWithMoE,
    attach_moe_to_model,
    freeze_backbone_verify,
)


def get_memory_gb() -> dict[str, float]:
    """Cross-platform memory profiler (ROCm + CPU + system)."""
    out = {}
    if torch.cuda.is_available():  # HIP via cuda namespace on ROCm
        torch.cuda.synchronize()
        out["gpu_allocated_gb"] = torch.cuda.memory_allocated() / 1e9
        out["gpu_reserved_gb"] = torch.cuda.memory_reserved() / 1e9
        out["gpu_max_allocated_gb"] = torch.cuda.max_memory_allocated() / 1e9
    try:
        import psutil  # type: ignore
        p = psutil.Process()
        out["cpu_rss_gb"] = p.memory_info().rss / 1e9
    except ImportError:
        pass
    return out


def probe_matmul_throughput(
    device: torch.device,
    shapes: list[tuple[int, int, int]],
    n_warmup: int = 3,
    n_trial: int = 5,
) -> list[dict]:
    """Measure dense BF16 matmul throughput for grounding R1.4 wall estimate.

    Reference values from prior session (90-docs/baien/bit-packed-xnor-kernels-260524/):
      B=256, K=4096, N=4096 -> measured 9.54 TFLOPS BF16 on EVO-X2 Radeon 8060S.
    """
    results = []
    for B, K, N in shapes:
        a = torch.randn(B, K, dtype=torch.bfloat16, device=device)
        b = torch.randn(K, N, dtype=torch.bfloat16, device=device)
        # warmup
        for _ in range(n_warmup):
            c = a @ b
            if device.type == "cuda":
                torch.cuda.synchronize()
        # measure
        times = []
        for _ in range(n_trial):
            if device.type == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            c = a @ b
            if device.type == "cuda":
                torch.cuda.synchronize()
            times.append(time.perf_counter() - t0)
        t_median = sorted(times)[n_trial // 2]
        flops = 2 * B * K * N
        tflops = flops / t_median / 1e12
        results.append({
            "B": B, "K": K, "N": N,
            "median_sec": t_median,
            "tflops_bf16_measured": round(tflops, 3),
            "tflop_work": round(flops / 1e12, 4),
        })
        del a, b, c
        if device.type == "cuda":
            torch.cuda.empty_cache()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-model",
        default="microsoft/bitnet-b1.58-2B-4T-bf16",
        help="HF model id for backbone",
    )
    parser.add_argument("--num-experts", type=int, default=128)
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--moe-layers", type=int, nargs="+", default=None,
                        help="Layer indices (0-based) to install MoE on. Default: last layer only (R1.0 probe).")
    parser.add_argument("--output-json", default="probe_rocm_moe_result.json",
                        help="Output JSON path for R1.0 acceptance evidence")
    parser.add_argument("--skip-bitnet-load", action="store_true",
                        help="Skip BitNet checkpoint download (fast smoke without HF cache hit)")
    parser.add_argument("--seq-len", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()

    result = {
        "adr": "ADR-2605262100 R1.0",
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device_name": None,
        "args": vars(args),
        "stages": [],
        "acceptance": {"finite_output": None, "no_oom": True, "ram_under_30gb": None},
    }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.cuda.is_available():
        result["device_name"] = torch.cuda.get_device_name(0)
        result["hip_version"] = getattr(torch.version, "hip", None)
    print(f"[probe] device={device} name={result['device_name']}")

    # ─── Stage 1: matmul throughput grounding (no BitNet load yet) ──────
    print("[stage 1] matmul throughput grounding...")
    matmul_shapes = [
        (8, 2048, 2048),     # smallest realistic per-expert shape
        (256, 4096, 4096),   # matches prior 2026-05-24 measurement (~9.54 TFLOPS expected)
    ]
    matmul_results = probe_matmul_throughput(device, matmul_shapes)
    result["stages"].append({"name": "matmul_throughput", "results": matmul_results})
    for r in matmul_results:
        print(f"  B={r['B']:4d} K={r['K']:5d} N={r['N']:5d} -> {r['tflops_bf16_measured']} TFLOPS BF16")

    # ─── Stage 2: BitNet 2B load + MoE surgery + forward ────────────────
    if args.skip_bitnet_load:
        print("[stage 2] SKIPPED (--skip-bitnet-load)")
        result["stages"].append({"name": "bitnet_moe_forward", "skipped": True})
    else:
        print(f"[stage 2] loading {args.base_model}...")
        gc.collect()
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats()

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: F401
        except ImportError as e:
            print(f"  FAIL: transformers not importable: {e}")
            result["stages"].append({"name": "bitnet_moe_forward", "error": str(e)})
            result["acceptance"]["finite_output"] = False
            with open(args.output_json, "w") as f:
                json.dump(result, f, indent=2)
            sys.exit(1)

        load_start = time.perf_counter()
        try:
            model = AutoModelForCausalLM.from_pretrained(
                args.base_model,
                torch_dtype=torch.bfloat16,
                trust_remote_code=True,  # BitNet may use custom modeling
            )
        except Exception as e:
            print(f"  FAIL: model load: {e}")
            result["stages"].append({
                "name": "bitnet_moe_forward",
                "error": f"load: {e}",
                "load_time_sec": time.perf_counter() - load_start,
            })
            result["acceptance"]["finite_output"] = False
            with open(args.output_json, "w") as f:
                json.dump(result, f, indent=2)
            sys.exit(1)
        load_sec = time.perf_counter() - load_start
        print(f"  loaded in {load_sec:.1f}s")
        print(f"  config: hidden={model.config.hidden_size}, intermediate={model.config.intermediate_size}, n_layers={model.config.num_hidden_layers}")

        model.to(device)

        # Determine moe_layers (default = last layer for R1.0 probe)
        if args.moe_layers is None:
            moe_layers = [model.config.num_hidden_layers - 1]
        else:
            moe_layers = args.moe_layers
        print(f"  installing MoE on layers: {moe_layers}")

        installed = attach_moe_to_model(
            model.model if hasattr(model, "model") else model,
            moe_layer_indices=moe_layers,
            hidden_size=model.config.hidden_size,
            intermediate_size=model.config.intermediate_size,
            num_experts=args.num_experts,
            top_k=args.top_k,
        )
        # Move freshly-created MoE modules to the right device
        for wrapper in installed.values():
            wrapper.to(device)
            # Ensure MoE branch params match model dtype (bf16)
            wrapper.moe_branch.to(dtype=torch.bfloat16)
            # Keep alpha in fp32 for numerical stability of the gate

        param_summary = freeze_backbone_verify(
            model.model if hasattr(model, "model") else model,
            installed,
        )
        print(f"  param summary: {param_summary}")

        # Forward step on random input
        input_ids = torch.randint(0, model.config.vocab_size, (args.batch_size, args.seq_len), device=device)
        print(f"  forward pass on input shape={tuple(input_ids.shape)}...")
        fwd_start = time.perf_counter()
        try:
            with torch.no_grad():
                outputs = model(input_ids=input_ids)
            fwd_sec = time.perf_counter() - fwd_start
            logits = outputs.logits
            finite = torch.isfinite(logits).all().item()
            print(f"  forward {fwd_sec:.2f}s, logits shape={tuple(logits.shape)}, finite={finite}")
            result["acceptance"]["finite_output"] = bool(finite)
        except torch.cuda.OutOfMemoryError as e:
            print(f"  OOM during forward: {e}")
            result["acceptance"]["no_oom"] = False
            result["acceptance"]["finite_output"] = False
        except Exception as e:
            print(f"  FAIL forward: {e}")
            result["acceptance"]["finite_output"] = False

        mem = get_memory_gb()
        result["stages"].append({
            "name": "bitnet_moe_forward",
            "load_time_sec": round(load_sec, 2),
            "forward_time_sec": round(fwd_sec if 'fwd_sec' in locals() else 0, 3),
            "param_summary": param_summary,
            "moe_layers": moe_layers,
            "memory_gb": {k: round(v, 2) for k, v in mem.items()},
        })

        # G5 acceptance: alpha value check (should be ~0 ± 1e-3)
        alphas = [w.alpha.item() for w in installed.values()]
        result["acceptance"]["alpha_init_g5"] = {
            "alphas": alphas,
            "all_within_jitter": all(abs(a) <= 1.001e-3 for a in alphas),
        }
        print(f"  G5 alpha init check: {alphas} (all within ±1e-3: {result['acceptance']['alpha_init_g5']['all_within_jitter']})")

    # Memory check
    mem_final = get_memory_gb()
    total_gb = max(mem_final.get("gpu_max_allocated_gb", 0), mem_final.get("cpu_rss_gb", 0))
    result["acceptance"]["ram_under_30gb"] = total_gb <= 30.0
    result["peak_memory_gb"] = round(total_gb, 2)

    # Write JSON evidence
    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[probe] result written to {args.output_json}")

    # Print final acceptance summary
    acc = result["acceptance"]
    print(f"\n[acceptance R1.0]")
    print(f"  finite_output: {acc.get('finite_output')}")
    print(f"  no_oom:        {acc.get('no_oom')}")
    print(f"  ram_under_30gb: {acc.get('ram_under_30gb')} (peak {total_gb:.2f} GB)")
    print(f"  G5 alpha init: {acc.get('alpha_init_g5', {}).get('all_within_jitter')}")

    pass_count = sum(1 for v in [acc.get('finite_output'), acc.get('no_oom'), acc.get('ram_under_30gb'), acc.get('alpha_init_g5', {}).get('all_within_jitter')] if v)
    print(f"\n  {pass_count}/4 R1.0 acceptance criteria PASS")

    sys.exit(0 if pass_count == 4 else 1)


if __name__ == "__main__":
    main()
