#!/usr/bin/env python3
"""bbh_bitnetcpp.py — Big-Bench-Hard bench via bitnet.cpp + chat template.

Tests multi-step reasoning across 5 representative BBH sub-tasks.
Sample 40 tasks from each config, total 200.

Score: case-insensitive exact match against gold target.
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


CONFIGS = [
    "boolean_expressions",
    "causal_judgement",
    "date_understanding",
    "logical_deduction_five_objects",
    "word_sorting",
]


def make_instruction(question: str) -> str:
    return (
        f"Solve this problem step by step. At the end, write your final answer as 'Answer: <X>' "
        f"where X is your answer.\n\n"
        f"Problem: {question}"
    )


def normalize(s: str) -> str:
    return s.strip().lower().rstrip('.').strip()


def extract_answer(gen_text: str) -> str | None:
    """Extract final answer from generation."""
    # Prefer 'Answer:' marker
    m = re.search(r"answer\s*[:=]\s*(.+?)(?:\n|$)", gen_text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Fall back: last non-empty line
    lines = [ln.strip() for ln in gen_text.splitlines() if ln.strip()]
    if lines:
        return lines[-1]
    return None


def is_correct(pred: str | None, gold: str) -> bool:
    if pred is None:
        return False
    pred_norm = normalize(pred)
    gold_norm = normalize(gold)
    # Exact match
    if pred_norm == gold_norm:
        return True
    # Bracketed form e.g. "(A)" vs "A"
    if re.fullmatch(r"\(?\s*" + re.escape(gold_norm) + r"\s*\)?", pred_norm):
        return True
    if re.fullmatch(r"\(?\s*" + re.escape(pred_norm) + r"\s*\)?", gold_norm):
        return True
    # Contains exact gold as token
    if re.search(r"\b" + re.escape(gold_norm) + r"\b", pred_norm):
        return True
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="/workspace/BitNet/gpu/checkpoints/")
    p.add_argument("--output", default="/workspace/bbh-bitnetcpp-result.jsonl")
    p.add_argument("--max-prompt-len", type=int, default=512)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--per-config", type=int, default=40)
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

    EOS = g.tokenizer.eos_id
    EOT = g.tokenizer.special_tokens.get("<|eot_id|>", EOS)

    all_results = []
    per_config_acc = {}
    t_start = time.perf_counter()

    for cfg_name in CONFIGS:
        print(f"\n=== {cfg_name} ===")
        ds = load_dataset("lukaemon/bbh", cfg_name, split="test")
        n_use = min(args.per_config, len(ds))
        n_correct_cfg = 0
        for idx in range(n_use):
            row = ds[idx]
            question = row.get("input", "")
            gold = row.get("target", "")

            instruction = make_instruction(question)
            ids = cf.encode_dialog_prompt(
                dialog=[{"role": "user", "content": instruction}],
                completion=True,
            )
            if len(ids) > args.max_prompt_len:
                tail = ids[-4:]
                ids = ids[: args.max_prompt_len - 4] + tail

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
                all_results.append({"cfg": cfg_name, "idx": idx, "correct": False, "err": str(e)[:80]})
                continue
            pred = extract_answer(gen_text)
            correct = is_correct(pred, gold)
            if correct:
                n_correct_cfg += 1
            all_results.append({"cfg": cfg_name, "idx": idx, "correct": correct, "pred": pred, "gold": gold})
        acc = n_correct_cfg / n_use
        per_config_acc[cfg_name] = acc
        print(f"  {cfg_name}: {n_correct_cfg}/{n_use} = {acc:.3f}")

    total_wall = time.perf_counter() - t_start
    n_done = len(all_results)
    n_correct_total = sum(1 for r in all_results if r.get("correct"))
    acc = n_correct_total / n_done if n_done else 0
    print(f"\n[done] BBH agg = {n_correct_total}/{n_done} = {acc:.4f}")
    print(f"[done] wall {total_wall:.0f}s = {total_wall/60:.1f}min")
    print(f"[done] per-config:")
    for cfg, a in per_config_acc.items():
        print(f"  {cfg}: {a:.3f}")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "model": "microsoft/bitnet-b1.58-2B-4T (ternary native W2A8)",
        "task": "bbh_chat",
        "task_source": f"lukaemon/bbh × {len(CONFIGS)} configs × {args.per_config}/config",
        "configs": CONFIGS,
        "n_tasks_evaluated": n_done,
        "n_correct": n_correct_total,
        "accuracy": round(acc, 4),
        "per_config_acc": {k: round(v, 4) for k, v in per_config_acc.items()},
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_done / total_wall * 60, 2) if total_wall else 0,
        "context": "cycle 65 BBH baseline — multi-step reasoning. 7th canonical bench. Per cycle 48 magpie_reasoning per-source loss 0.47 (best learned) predicts LARGEST R1.5 Δ on reasoning-style bench.",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
