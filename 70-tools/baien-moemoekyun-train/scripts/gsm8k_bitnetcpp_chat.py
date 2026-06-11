#!/usr/bin/env python3
"""gsm8k_bitnetcpp_chat.py — GSM8K bench via bitnet.cpp + chat template.

Cycle 33+ — orthogonal bench (math vs HumanEval+ ceiling at 33.54%).
Validates cycle 28 finding that math_500 per-source loss dropped 1.42→0.87
during R1.4 mid-scale train.

GSM8K format:
  question: math word problem
  answer:   reasoning chain + "#### N" where N is the numeric answer

Score: extract last number from generated text; match to gold N exactly.

Run on RTX 5090 with bitnet.cpp packed kernel:
    python3 gsm8k_bitnetcpp_chat.py --start 0 --end 200 --output ...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("NO_CUDA_GRAPHS", "1")

import torch


def make_instruction(question: str) -> str:
    """Wrap GSM8K question in instruction-style for chat completion."""
    return (
        f"Solve this math problem step by step. "
        f"At the end, write the final numeric answer after '####'.\n\n"
        f"Problem: {question}"
    )


def extract_answer(gen_text: str) -> str | None:
    """Extract final numeric answer from generation."""
    # Prefer #### marker first (matches gold format)
    m = re.search(r"####\s*([\-\d\.,]+)", gen_text)
    if m:
        return m.group(1).replace(",", "").rstrip(".")
    # Fall back: last number in generation
    numbers = re.findall(r"-?\d+\.?\d*", gen_text)
    if numbers:
        return numbers[-1].replace(",", "").rstrip(".")
    return None


def extract_gold(answer: str) -> str:
    """Extract gold numeric answer from GSM8K answer field."""
    m = re.search(r"####\s*([\-\d\.,]+)", answer)
    if m:
        return m.group(1).replace(",", "").rstrip(".")
    return ""


def normalize_num(s: str) -> str:
    """Normalize numeric string for comparison (drop trailing zeros, etc)."""
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except (ValueError, TypeError):
        return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="/workspace/BitNet/gpu/checkpoints/")
    p.add_argument("--output", default="/workspace/gsm8k-bitnetcpp-chat-result.jsonl")
    p.add_argument("--max-prompt-len", type=int, default=512)
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=200)
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

    print(f"\n[data] loading openai/gsm8k")
    from datasets import load_dataset
    ds = load_dataset("openai/gsm8k", "main", split="test")
    print(f"[data] {len(ds)} test; range [{args.start}, {args.end})")

    EOS = g.tokenizer.eos_id
    EOT = g.tokenizer.special_tokens.get("<|eot_id|>", EOS)

    n_correct = 0
    results = []
    t_start = time.perf_counter()

    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        question = row["question"]
        gold_answer = row["answer"]
        gold_num = extract_gold(gold_answer)
        task_id = f"GSM8K/{idx}"

        instruction = make_instruction(question)
        ids = cf.encode_dialog_prompt(
            dialog=[{"role": "user", "content": instruction}],
            completion=True,
        )
        if len(ids) > args.max_prompt_len:
            tail = ids[-4:]
            ids = ids[: args.max_prompt_len - 4] + tail

        t_gen = time.perf_counter()
        try:
            stats, out_list = g.generate_all(
                [ids], use_cuda_graphs=False, use_sampling=False,
            )
            gen_ids = out_list[0]
            # Stop at EOT or EOS
            stop_idx = len(gen_ids)
            for stop in (EOT, EOS):
                if stop is not None and stop in gen_ids:
                    stop_idx = min(stop_idx, gen_ids.index(stop))
            gen_ids = gen_ids[:stop_idx]
            gen_text = g.tokenizer.decode(gen_ids)
        except Exception as e:
            results.append({"task_id": task_id, "correct": False, "error": f"gen_err: {type(e).__name__}: {str(e)[:120]}"})
            continue
        gen_wall = time.perf_counter() - t_gen

        pred = extract_answer(gen_text)
        correct = normalize_num(pred or "") == normalize_num(gold_num) and gold_num != ""

        if correct:
            n_correct += 1

        results.append({
            "task_id": task_id,
            "correct": correct,
            "pred": pred,
            "gold": gold_num,
            "gen_wall_sec": round(gen_wall, 2),
        })

        n_done = len(results)
        elapsed = time.perf_counter() - t_start
        eta = elapsed / n_done * (args.end - args.start - n_done) if n_done else 0
        if n_done % 10 == 0 or n_done == 1:
            print(f"  [{n_done:3d}/{args.end-args.start}] acc={n_correct/n_done:.3f} ({n_correct}/{n_done}) elapsed={elapsed:.0f}s eta={eta:.0f}s gen={gen_wall:.1f}s")

    total_wall = time.perf_counter() - t_start
    n_done = len(results)
    acc = n_correct / n_done if n_done else 0
    print(f"\n[done] acc = {n_correct}/{n_done} = {acc:.4f}")
    print(f"[done] wall {total_wall:.0f}s = {total_wall/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "device": "cuda",
        "model": "microsoft/bitnet-b1.58-2B-4T (ternary native W2A8)",
        "harness": "bitnet.cpp FastGen + ChatFormat + gsm8k extract_answer",
        "task": "gsm8k",
        "task_source": "openai/gsm8k main split=test",
        "n_tasks_evaluated": n_done,
        "start_idx": args.start,
        "end_idx": args.end,
        "n_correct": n_correct,
        "accuracy": round(acc, 4),
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_done / total_wall * 60, 2) if total_wall else 0,
        "scoring": "exact numeric match after extracting last number or #### marker",
        "max_prompt_len": args.max_prompt_len,
        "max_new_tokens": args.max_new_tokens,
        "context": "PRE-TRAIN canonical baseline; cycle 28 mid-scale ckpt will be benched against this",
        "results_sample": results[:3] + results[-3:] if len(results) > 6 else results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
