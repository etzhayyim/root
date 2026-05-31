#!/usr/bin/env python3
"""mbppplus_bitnetcpp_chat.py — MBPP+ bench via bitnet.cpp + chat template.

Cycle 40+ — orthogonal CODE bench (different problem distribution than HumanEval+).
Tests whether cycle 32's HumanEval+ ceiling at 33.54% generalizes to other
code benches or was bench-specific.

MBPP+ format: text (description) + test_list (assertion tests)
Score: code passes ALL assertions in test_list = correct
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("NO_CUDA_GRAPHS", "1")

import torch


def make_instruction(description: str, test_list: list) -> str:
    """Wrap MBPP+ description + first test in instruction format."""
    first_test = test_list[0] if test_list else ""
    return (
        f"Write a Python function that satisfies the following description.\n\n"
        f"Description: {description}\n\n"
        f"Example test:\n{first_test}\n\n"
        f"Output only the Python function in a ```python code block, no explanations."
    )


def extract_code(gen_text: str) -> str:
    """Extract function definition from chat-template generation."""
    if "```" in gen_text:
        m = re.search(r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)", gen_text, re.DOTALL)
        if m:
            gen_text = m.group(1)
    # Find first def...end (until next top-level non-indented line)
    lines = gen_text.splitlines()
    out_lines = []
    in_def = False
    for ln in lines:
        if not in_def:
            if ln.lstrip().startswith(("def ", "import ", "from ")):
                in_def = True
            out_lines.append(ln)
        else:
            if ln and not ln.startswith((" ", "\t", "#")) and not ln.lstrip().startswith(("def ", "import ", "from ", "@")):
                break
            out_lines.append(ln)
    return "\n".join(out_lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="/workspace/BitNet/gpu/checkpoints/")
    p.add_argument("--output", default="/workspace/mbppplus-bitnetcpp-chat-result.jsonl")
    p.add_argument("--max-prompt-len", type=int, default=384)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=200)
    p.add_argument("--timeout-sec", type=int, default=10)
    args = p.parse_args()

    print(f"[env] cuda={torch.cuda.is_available()} device={torch.cuda.get_device_name(0)}")
    os.chdir("/workspace/BitNet/gpu")
    sys.path.insert(0, "/workspace/BitNet/gpu")
    from generate import FastGen, GenArgs
    from tokenizer import ChatFormat

    gen_args = GenArgs(
        gen_length=args.max_new_tokens,
        gen_bsz=1,
        prompt_length=args.max_prompt_len,
        use_sampling=False,
    )
    t0 = time.perf_counter()
    g = FastGen.build(args.ckpt, gen_args, device="cuda:0")
    cf = ChatFormat(g.tokenizer)
    print(f"[build] {time.perf_counter() - t0:.1f}s")

    from datasets import load_dataset
    ds = load_dataset("evalplus/mbppplus", split="test")
    print(f"[data] {len(ds)} test; range [{args.start}, {min(args.end, len(ds))})")
    print(f"[data] schema: {list(ds[0].keys())}")

    EOS = g.tokenizer.eos_id
    EOT = g.tokenizer.special_tokens.get("<|eot_id|>", EOS)

    n_pass = 0
    results = []
    t_start = time.perf_counter()

    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        description = row.get("text") or row.get("prompt") or ""
        test_list = row.get("test_list") or row.get("test", "").split("\n")
        assertions = row.get("test") or "\n".join(test_list)
        task_id = f"MBPP+/{row.get('task_id', idx)}"

        instruction = make_instruction(description, test_list)
        ids = cf.encode_dialog_prompt(
            dialog=[{"role": "user", "content": instruction}],
            completion=True,
        )
        if len(ids) > args.max_prompt_len:
            tail = ids[-4:]
            ids = ids[: args.max_prompt_len - 4] + tail

        t_gen = time.perf_counter()
        try:
            stats, out_list = g.generate_all([ids], use_cuda_graphs=False, use_sampling=False)
            gen_ids = out_list[0]
            stop_idx = len(gen_ids)
            for stop in (EOT, EOS):
                if stop is not None and stop in gen_ids:
                    stop_idx = min(stop_idx, gen_ids.index(stop))
            gen_ids = gen_ids[:stop_idx]
            gen_text = g.tokenizer.decode(gen_ids)
        except Exception as e:
            results.append({"task_id": task_id, "passed": False, "error": f"gen_err: {str(e)[:120]}"})
            continue
        gen_wall = time.perf_counter() - t_gen

        full_code = extract_code(gen_text)
        test_code = full_code + "\n\n" + assertions

        passed = False
        err = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
                f.write(test_code)
                tmp_path = f.name
            r = subprocess.run(["python3", tmp_path], capture_output=True, text=True, timeout=args.timeout_sec)
            if r.returncode == 0:
                passed = True
                n_pass += 1
            else:
                err = (r.stderr or r.stdout)[:200]
            os.unlink(tmp_path)
        except subprocess.TimeoutExpired:
            err = "timeout"
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:120]}"

        results.append({
            "task_id": task_id,
            "passed": passed,
            "gen_wall_sec": round(gen_wall, 2),
            "error": err[:150] if not passed else None,
        })

        n_done = len(results)
        elapsed = time.perf_counter() - t_start
        eta = elapsed / n_done * (args.end - args.start - n_done) if n_done else 0
        if n_done % 20 == 0 or n_done == 1:
            print(f"  [{n_done:3d}/{args.end-args.start}] pass@1={n_pass/n_done:.3f} ({n_pass}/{n_done})  elapsed={elapsed:.0f}s eta={eta:.0f}s gen={gen_wall:.1f}s")

    total_wall = time.perf_counter() - t_start
    n_done = len(results)
    pass1 = n_pass / n_done if n_done else 0
    print(f"\n[done] pass@1 = {n_pass}/{n_done} = {pass1:.4f}  wall {total_wall:.0f}s = {total_wall/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "device": "cuda",
        "model": "microsoft/bitnet-b1.58-2B-4T (ternary native W2A8)",
        "harness": "bitnet.cpp FastGen + ChatFormat + evalplus/mbppplus + exec-graded subprocess",
        "task": "mbppplus_chat",
        "task_source": "evalplus/mbppplus",
        "n_tasks_evaluated": n_done,
        "start_idx": args.start,
        "end_idx": args.end,
        "n_pass": n_pass,
        "pass1": round(pass1, 4),
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_done / total_wall * 60, 2) if total_wall else 0,
        "context": "cycle 40 MBPP+ PRE-TRAIN canonical baseline — orthogonal code bench vs HumanEval+ 18.90%",
        "results_sample": results[:3] + results[-3:] if len(results) > 6 else results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
