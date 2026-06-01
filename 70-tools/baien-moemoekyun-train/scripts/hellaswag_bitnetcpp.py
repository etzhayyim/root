#!/usr/bin/env python3
"""hellaswag_bitnetcpp.py — HellaSwag commonsense bench via bitnet.cpp + chat template.

Tests world-model / commonsense completion via 4-way MCQ.

Score: parse first A/B/C/D from model output; match to gold label.
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


def make_instruction(ctx: str, endings: list[str]) -> str:
    options = "\n".join(f"{chr(65+i)}. {e}" for i, e in enumerate(endings))
    return (
        f"Complete the following scenario. Choose the most likely continuation.\n\n"
        f"Scenario: {ctx}\n\n"
        f"Options:\n{options}\n\n"
        f"Answer with just the letter A, B, C, or D."
    )


def extract_answer(gen_text: str) -> int | None:
    """Find first A/B/C/D letter answer. Returns 0-indexed or None."""
    # Look for standalone letter answer
    for pat in [
        r"\b([ABCD])\b",
        r"(?:answer\s*[:=]\s*|is\s+)([ABCD])",
        r"\(([ABCD])\)",
    ]:
        m = re.search(pat, gen_text, re.IGNORECASE)
        if m:
            return ord(m.group(1).upper()) - ord("A")
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="/workspace/BitNet/gpu/checkpoints/")
    p.add_argument("--output", default="/workspace/hellaswag-bitnetcpp-result.jsonl")
    p.add_argument("--max-prompt-len", type=int, default=512)
    p.add_argument("--max-new-tokens", type=int, default=64)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=200)
    args = p.parse_args()

    print(f"[env] device={torch.cuda.get_device_name(0)}")
    os.chdir("/workspace/BitNet/gpu")
    sys.path.insert(0, "/workspace/BitNet/gpu")
    from generate import FastGen, GenArgs
    from tokenizer import ChatFormat

    gen_args = GenArgs(
        gen_length=args.max_new_tokens, gen_bsz=1,
        prompt_length=args.max_prompt_len, use_sampling=False,
    )
    t0 = time.perf_counter()
    g = FastGen.build(args.ckpt, gen_args, device="cuda:0")
    cf = ChatFormat(g.tokenizer)
    print(f"[build] {time.perf_counter() - t0:.1f}s")

    from datasets import load_dataset
    ds = load_dataset("Rowan/hellaswag", split="validation")
    print(f"[data] {len(ds)} total; range [{args.start}, {min(args.end, len(ds))})")

    EOS = g.tokenizer.eos_id
    EOT = g.tokenizer.special_tokens.get("<|eot_id|>", EOS)

    n_correct = 0
    results = []
    t_start = time.perf_counter()

    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        ctx = row.get("ctx", "")
        endings = row.get("endings", [])
        gold = int(row.get("label", -1))
        task_id = f"hellaswag/{idx}"

        if len(endings) != 4 or gold not in (0, 1, 2, 3):
            continue

        instruction = make_instruction(ctx, endings)
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
            results.append({"task_id": task_id, "correct": False, "err": str(e)[:80]})
            continue
        gen_wall = time.perf_counter() - t_gen

        pred = extract_answer(gen_text)
        correct = pred == gold
        if correct:
            n_correct += 1

        results.append({
            "task_id": task_id,
            "correct": correct,
            "pred": pred,
            "gold": gold,
            "gen_wall_sec": round(gen_wall, 2),
        })

        n_done = len(results)
        elapsed = time.perf_counter() - t_start
        eta = elapsed / n_done * (args.end - args.start - n_done) if n_done else 0
        if n_done % 20 == 0 or n_done == 1:
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
        "model": "microsoft/bitnet-b1.58-2B-4T (ternary native W2A8)",
        "harness": "bitnet.cpp FastGen + ChatFormat + HellaSwag 4-way MCQ extract_answer",
        "task": "hellaswag_chat",
        "task_source": "Rowan/hellaswag validation",
        "n_tasks_evaluated": n_done,
        "n_correct": n_correct,
        "accuracy": round(acc, 4),
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_done / total_wall * 60, 2) if total_wall else 0,
        "context": "cycle 62 HellaSwag commonsense PRE-TRAIN baseline. 6th canonical bench joining HE+/MBPP+/GSM8K/xLAM-irrelevance/MMLU-STEM.",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
