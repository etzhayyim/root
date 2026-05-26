#!/usr/bin/env python3
"""bench_gpqa_diamond.py — minimal GPQA-diamond evaluator without lm-eval-harness.

Standalone loglikelihood-style multiple-choice eval for BitNet 2B baseline.
Uses HF datasets directly (Idavidrein/gpqa, Diamond split, 198 questions).

Outputs: 90-docs/baien/bench-snapshot-260526-bitnet2b-gpqa-diamond.jsonl

Run:
    HF_HOME=/Volumes/260317/models/huggingface KMP_DUPLICATE_LIB_OK=TRUE \
        python3 70-tools/baien-moemoekyun-train/scripts/bench_gpqa_diamond.py
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HOME", "/Volumes/260317/models/huggingface")
os.environ.setdefault("HF_HUB_CACHE", os.environ["HF_HOME"] + "/hub")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import torch


def loglikelihood(model, tokenizer, context: str, continuation: str, device) -> float:
    """Compute log P(continuation | context) — sum log-probs of continuation tokens.

    Standard lm-eval-harness loglikelihood semantics (per-token log-prob sum).
    """
    full_ids = tokenizer(context + continuation, return_tensors="pt").input_ids.to(device)
    context_ids = tokenizer(context, return_tensors="pt").input_ids.to(device)
    cont_len = full_ids.shape[1] - context_ids.shape[1]
    if cont_len <= 0:
        return 0.0

    with torch.no_grad():
        logits = model(full_ids).logits  # (1, T, vocab)

    # Predict tokens at positions [context_len-1 : T-1] yield continuation tokens
    # (autoregressive: position i predicts token i+1)
    log_probs = torch.nn.functional.log_softmax(logits[0], dim=-1)
    cont_positions = range(context_ids.shape[1] - 1, full_ids.shape[1] - 1)
    target_ids = full_ids[0, context_ids.shape[1]:].tolist()
    total = 0.0
    for pos, tgt in zip(cont_positions, target_ids):
        total += log_probs[pos, tgt].item()
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    parser.add_argument("--gpqa-config", default="gpqa_diamond",
                        help="gpqa_diamond | gpqa_main | gpqa_extended | mmlu:<subject> (ungated stand-in)")
    parser.add_argument("--n-questions", type=int, default=None, help="Subset for smoke (default: all)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output",
                        default=str(Path(__file__).parent.parent.parent.parent /
                                    "90-docs/baien/bench-snapshot-260526-bitnet2b-gpqa-diamond.jsonl"))
    parser.add_argument("--cot", action="store_true",
                        help="Append 'Let me think step by step.' (zero-shot CoT)")
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    print(f"[env] torch={torch.__version__} mps={torch.backends.mps.is_available()}")
    print(f"[env] HF_HOME={os.environ['HF_HOME']}")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[env] device={device}")

    print(f"\n[load] {args.model}")
    t0 = time.perf_counter()
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16, trust_remote_code=False)
    model.to(device).eval()
    print(f"[load] model loaded in {time.perf_counter() - t0:.1f}s")

    from datasets import load_dataset
    if args.gpqa_config.startswith("mmlu-redux:"):
        # MMLU-Redux 2.0 (ungated, curated, matches user's bench table directly)
        subject = args.gpqa_config.split(":", 1)[1]
        print(f"\n[data] loading edinburgh-dawg/mmlu-redux-2.0 {subject}")
        ds = load_dataset("edinburgh-dawg/mmlu-redux-2.0", subject, split="test")
        normalized = []
        for r in ds:
            # MMLU-Redux 2.0 uses 'correct_answer' field (index) in addition to 'answer'
            ans_idx = r["answer"]
            normalized.append({
                "Question": r["question"],
                "Correct Answer": r["choices"][ans_idx],
                "Incorrect Answer 1": r["choices"][(ans_idx+1)%4],
                "Incorrect Answer 2": r["choices"][(ans_idx+2)%4],
                "Incorrect Answer 3": r["choices"][(ans_idx+3)%4],
            })
        ds = normalized
        print(f"[data] total questions: {len(ds)}")
    elif args.gpqa_config.startswith("mmlu:"):
        # Original MMLU (ungated) — broader coverage but noisier than MMLU-Redux
        subject = args.gpqa_config.split(":", 1)[1]
        print(f"\n[data] loading cais/mmlu {subject}")
        ds = load_dataset("cais/mmlu", subject, split="test")
        normalized = []
        for r in ds:
            normalized.append({
                "Question": r["question"],
                "Correct Answer": r["choices"][r["answer"]],
                "Incorrect Answer 1": r["choices"][(r["answer"]+1)%4],
                "Incorrect Answer 2": r["choices"][(r["answer"]+2)%4],
                "Incorrect Answer 3": r["choices"][(r["answer"]+3)%4],
            })
        ds = normalized
        print(f"[data] total questions: {len(ds)}")
    else:
        print(f"\n[data] loading Idavidrein/gpqa {args.gpqa_config}")
        ds = load_dataset("Idavidrein/gpqa", args.gpqa_config, split="train")
        print(f"[data] total questions: {len(ds)}")

    indices = list(range(len(ds)))
    if args.n_questions:
        random.shuffle(indices)
        indices = indices[:args.n_questions]
    print(f"[data] evaluating: {len(indices)} questions")

    correct = 0
    results = []
    t0 = time.perf_counter()

    for i, idx in enumerate(indices):
        row = ds[idx]
        q = row["Question"]
        choices = [
            row["Correct Answer"],
            row["Incorrect Answer 1"],
            row["Incorrect Answer 2"],
            row["Incorrect Answer 3"],
        ]
        # Shuffle to neutralize positional bias
        rng = random.Random(args.seed + idx)
        order = list(range(4))
        rng.shuffle(order)
        shuffled = [choices[o] for o in order]
        correct_pos = order.index(0)

        labels = ["A", "B", "C", "D"]
        cot_suffix = " Let me think step by step." if args.cot else ""
        prompt = (
            f"Question: {q}\n\n"
            + "\n".join(f"{labels[k]}. {shuffled[k]}" for k in range(4))
            + f"\n\nAnswer:{cot_suffix} "
        )

        # Loglikelihood scoring: P(letter | prompt) for each of A/B/C/D
        scores = []
        for k in range(4):
            ll = loglikelihood(model, tokenizer, prompt, labels[k], device)
            scores.append(ll)
        pred_pos = int(max(range(4), key=lambda k: scores[k]))
        is_correct = pred_pos == correct_pos
        if is_correct:
            correct += 1

        results.append({
            "idx": idx,
            "correct_pos": correct_pos,
            "pred_pos": pred_pos,
            "scores": [round(s, 4) for s in scores],
            "is_correct": is_correct,
        })

        elapsed = time.perf_counter() - t0
        eta = elapsed / (i + 1) * (len(indices) - i - 1)
        if (i + 1) % 10 == 0 or i == 0:
            acc_so_far = correct / (i + 1)
            print(f"[{i+1:3d}/{len(indices):3d}] acc={acc_so_far:.3f} ({correct}/{i+1}) "
                  f"elapsed={elapsed:.0f}s eta={eta:.0f}s")

    total_sec = time.perf_counter() - t0
    accuracy = correct / len(indices)
    random_baseline = 0.25

    print(f"\n[done] accuracy = {correct}/{len(indices)} = {accuracy:.4f}")
    print(f"[done] vs random 25% baseline: delta = {(accuracy - random_baseline) * 100:+.1f}pp")
    print(f"[done] total wall: {total_sec:.0f}s = {total_sec/60:.1f}min")
    print(f"[done] {len(indices)/total_sec*60:.1f} questions/min")

    # Emit result envelope
    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "mac-260317",
        "device": str(device),
        "torch_version": torch.__version__,
        "model": args.model,
        "task": f"gpqa_{args.gpqa_config.replace('gpqa_','')}",
        "task_source": "Idavidrein/gpqa",
        "n_questions": len(indices),
        "n_correct": correct,
        "accuracy": round(accuracy, 4),
        "random_baseline": random_baseline,
        "delta_vs_random_pp": round((accuracy - random_baseline) * 100, 2),
        "wall_sec": round(total_sec, 1),
        "questions_per_min": round(len(indices) / total_sec * 60, 2),
        "scoring": "loglikelihood (single-letter completion)",
        "cot": args.cot,
        "seed": args.seed,
        "subset": args.n_questions if args.n_questions else "full",
        "harness": "custom (bench_gpqa_diamond.py) — lm-eval-harness install blocked by system pydantic conflict",
        "per_question": results if args.n_questions and args.n_questions <= 50 else None,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
