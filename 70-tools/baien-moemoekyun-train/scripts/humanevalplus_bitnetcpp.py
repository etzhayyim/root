#!/usr/bin/env python3
"""humanevalplus_bitnetcpp.py — canonical HumanEval+ pass@1 via bitnet.cpp GPU kernel.

Runs all 164 HumanEval+ tasks on RTX 5090 using BitNet's native ternary
W2A8 GEMV kernel (cycle 16: 335 tok/s decode, 7.67 GB VRAM).

Fits in 8 GB free VRAM while MMLU PID 20745 holds 23.9 GB → unblocks
cycle 22 canonical bench production.

Usage:
    python3 /workspace/humanevalplus_bitnetcpp.py \
        --ckpt /workspace/BitNet/gpu/checkpoints/ \
        --output /workspace/humanevalplus-bitnetcpp-result.jsonl \
        --max-prompt-len 512 --max-new-tokens 512 \
        --start 0 --end 164
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# Add bitnet path
sys.path.insert(0, "/workspace/BitNet/gpu")

import torch


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="/workspace/BitNet/gpu/checkpoints/")
    p.add_argument("--output", default="/workspace/humanevalplus-bitnetcpp-result.jsonl")
    p.add_argument("--max-prompt-len", type=int, default=384)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=164)
    p.add_argument("--timeout-sec", type=int, default=10)
    p.add_argument("--use-cuda-graphs", action="store_true",
                   help="Use CUDA graphs (faster but ALL prompts must be same length after padding)")
    args = p.parse_args()

    if not args.use_cuda_graphs:
        os.environ["NO_CUDA_GRAPHS"] = "1"

    print(f"[env] cwd={Path.cwd()}")
    print(f"[env] cuda={torch.cuda.is_available()} device={torch.cuda.get_device_name(0)}")

    # Build bitnet generator
    print(f"\n[build] bitnet.cpp FastGen from {args.ckpt}")
    # FastGen expects to be run with cwd=/workspace/BitNet/gpu/ (relative tokenizer.model path)
    os.chdir("/workspace/BitNet/gpu")
    from generate import FastGen, GenArgs

    # gen_length needs to be the max we plan to generate
    gen_args = GenArgs(
        gen_length=args.max_new_tokens,
        gen_bsz=1,
        prompt_length=args.max_prompt_len,
        use_sampling=False,  # greedy
    )

    t0 = time.perf_counter()
    g = FastGen.build(args.ckpt, gen_args, device="cuda:0")
    print(f"[build] {time.perf_counter() - t0:.1f}s")

    # Load HumanEval+ dataset
    print(f"\n[data] loading evalplus/humanevalplus")
    from datasets import load_dataset
    ds = load_dataset("evalplus/humanevalplus", split="test")
    print(f"[data] {len(ds)} total tasks; bench range [{args.start}, {args.end})")

    # Tokenizer
    tok = g.tokenizer
    EOS = getattr(tok, "eos_id", None)
    if EOS is None:
        # Try common alternatives
        for attr in ("special_tokens", "eot_id"):
            v = getattr(tok, attr, None)
            if isinstance(v, dict):
                EOS = v.get("<|end_of_text|>") or v.get("<|eot_id|>")
                if EOS:
                    break
    print(f"[tok] EOS={EOS}")

    n_pass = 0
    n_fail = 0
    n_total = 0
    results = []
    t_start = time.perf_counter()

    for idx in range(args.start, args.end):
        row = ds[idx]
        prompt = row["prompt"]
        test = row["test"]
        entry_point = row["entry_point"]
        task_id = row.get("task_id", f"HumanEval+/{idx}")

        # Encode prompt
        ids = tok.encode(prompt, bos=True, eos=False)
        if len(ids) > args.max_prompt_len:
            ids = ids[-args.max_prompt_len:]
        # Pad to max_prompt_len
        n_real = len(ids)
        if n_real < args.max_prompt_len:
            pad_id = 0
            ids = ids + [pad_id] * (args.max_prompt_len - n_real)

        # Generate
        t_gen = time.perf_counter()
        try:
            stats, out_tokens_list = g.generate_all(
                [ids],
                use_cuda_graphs=args.use_cuda_graphs,
                use_sampling=False,
            )
            out = out_tokens_list[0]
            # Strip prompt portion (first max_prompt_len) — output starts after prompt
            gen_ids = out[args.max_prompt_len:]
            # Stop at EOS if present
            if EOS is not None and EOS in gen_ids:
                gen_ids = gen_ids[:gen_ids.index(EOS)]
            gen_text = tok.decode(gen_ids)
        except Exception as e:
            gen_text = ""
            err_gen = f"generation_error: {type(e).__name__}: {str(e)[:100]}"
            n_fail += 1
            results.append({"task_id": task_id, "passed": False, "error": err_gen})
            n_total += 1
            continue
        gen_wall = time.perf_counter() - t_gen

        # Strip markdown fences if present
        if "```" in gen_text:
            import re
            m = re.search(r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)", gen_text, re.DOTALL)
            if m:
                gen_text = m.group(1)

        # Cut at next top-level def/class (avoid spurious extra defs)
        cut_lines = []
        for ln in gen_text.splitlines():
            if cut_lines and ln and not ln.startswith((" ", "\t", "#")) and (
                ln.lstrip().startswith("def ") or ln.lstrip().startswith("class ") or ln.lstrip().startswith("if __name__")
            ):
                break
            cut_lines.append(ln)
        gen_text = "\n".join(cut_lines)

        full_code = prompt + gen_text
        test_code = full_code + "\n\n" + test + f"\ncheck({entry_point})\n"

        # Exec in subprocess (10s timeout)
        passed = False
        err = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
                f.write(test_code)
                tmp_path = f.name
            r = subprocess.run(["python3", tmp_path],
                               capture_output=True, text=True, timeout=args.timeout_sec)
            if r.returncode == 0:
                passed = True
                n_pass += 1
            else:
                n_fail += 1
                err = (r.stderr or r.stdout)[:200]
            os.unlink(tmp_path)
        except subprocess.TimeoutExpired:
            n_fail += 1
            err = "timeout"
        except Exception as e:
            n_fail += 1
            err = f"{type(e).__name__}: {str(e)[:100]}"

        n_total += 1
        results.append({
            "task_id": task_id,
            "passed": passed,
            "gen_wall_sec": round(gen_wall, 2),
            "error": err[:200] if not passed else None,
        })

        elapsed = time.perf_counter() - t_start
        eta = elapsed / n_total * (args.end - args.start - n_total)
        if n_total % 10 == 0 or n_total == 1:
            print(f"  [{n_total:3d}/{args.end-args.start}] pass@1={n_pass/n_total:.3f} ({n_pass}/{n_total})  elapsed={elapsed:.0f}s eta={eta:.0f}s  gen_wall={gen_wall:.1f}s")

    total_wall = time.perf_counter() - t_start
    pass1 = n_pass / n_total if n_total > 0 else 0
    print(f"\n[done] pass@1 = {n_pass}/{n_total} = {pass1:.4f}")
    print(f"[done] wall: {total_wall:.0f}s = {total_wall/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "device": "cuda",
        "model": "microsoft/bitnet-b1.58-2B-4T (ternary native W2A8 packed)",
        "harness": "bitnet.cpp GPU kernel via FastGen + evalplus dataset",
        "task": "humanevalplus",
        "task_source": "evalplus/humanevalplus",
        "n_tasks_total": 164,
        "n_tasks_evaluated": n_total,
        "start_idx": args.start,
        "end_idx": args.end,
        "n_pass": n_pass,
        "pass1": round(pass1, 4),
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_total / total_wall * 60, 2) if total_wall else 0,
        "scoring": "exec-graded subprocess (timeout 10s, NO docker)",
        "max_prompt_len": args.max_prompt_len,
        "max_new_tokens": args.max_new_tokens,
        "use_cuda_graphs": args.use_cuda_graphs,
        "results_summary": results[:5] + results[-5:] if len(results) > 10 else results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
