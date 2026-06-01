#!/usr/bin/env python3
"""bench_passk_humanevalplus.py — pass@k on HumanEval+ with sampling.

For each of 164 problems, generate N candidates at temp=T, verify each via
subprocess execution. Report pass@1 (just first), pass@k = 1 - C(n-c,k)/C(n,k)
(Chen et al 2021 unbiased estimator). Tests whether the backbone's true
capability is wider than greedy decode reveals.

If pass@10 >> pass@1, then RLVR has theoretical headroom — model CAN
solve more problems with the right token sequence, just needs to be
taught to consistently pick it.
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
from math import comb
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch


def extract_code(gen: str, prompt: str) -> str:
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", gen, re.DOTALL)
    if blocks:
        return max(blocks, key=len)
    return prompt + gen.split("```")[0]


def pass_at_k(n: int, c: int, k: int) -> float:
    """Chen et al 2021 unbiased pass@k estimator."""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--n-experts", type=int, default=2048)
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--expert-hidden-ratio", type=int, default=32)
    p.add_argument("--layers-fraction", type=float, default=0.10)
    p.add_argument("--routing-mode", default="learned", choices=["learned","distance"])
    p.add_argument("--expert-kind", default="memory", choices=["ffn","memory"])
    p.add_argument("--n-samples", type=int, default=10)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=164)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--timeout-sec", type=int, default=10)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.attach import attach_moe_to_model, freeze_backbone_verify

    device = torch.device("cuda")
    print(f"[env] {torch.cuda.get_device_name(0)}")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"[load] {args.model}")
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
                                                 trust_remote_code=False)
    model.to(device).eval()
    print(f"[load] {time.perf_counter()-t0:.1f}s  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    cfg = model.config
    n_layers = cfg.num_hidden_layers
    n_moe = max(1, int(round(n_layers * args.layers_fraction)))
    moe_layer_indices = list(range(n_layers - n_moe, n_layers))
    moe_wrappers = attach_moe_to_model(
        model, moe_layer_indices=moe_layer_indices,
        hidden_size=cfg.hidden_size, intermediate_size=cfg.intermediate_size,
        num_experts=args.n_experts, top_k=args.top_k,
        expert_hidden_ratio=args.expert_hidden_ratio, ffn_attribute_name="mlp",
        routing_mode=args.routing_mode, expert_kind=args.expert_kind,
    )
    for w in moe_wrappers.values():
        w.to(device=device, dtype=torch.bfloat16)

    print(f"[ckpt] loading {args.checkpoint}")
    sd = torch.load(args.checkpoint, map_location=device)
    for fqn, wrapper in moe_wrappers.items():
        if fqn in sd:
            wrapper.load_state_dict(sd[fqn])

    freeze_backbone_verify(model, moe_wrappers)
    model.eval()

    from datasets import load_dataset
    ds = load_dataset("evalplus/humanevalplus", split="test")
    print(f"[data] {len(ds)} HumanEval+ problems; sampling {args.n_samples} per problem at T={args.temperature}")

    eos_id = tok.eos_token_id

    per_problem = []  # list of (task_id, n, c) for unbiased pass@k
    t_start = time.perf_counter()

    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        task_id = row["task_id"]
        prompt_raw = row["prompt"]
        test = row["test"]
        entry_point = row["entry_point"]
        instruction = f"Complete the following Python function. Return the full function body inside a ```python``` code block.\n\n```python\n{prompt_raw}```"
        msgs = [{"role": "user", "content": instruction}]
        try:
            chat_prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        except Exception:
            chat_prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        input_ids = tok(chat_prompt, return_tensors="pt", truncation=True, max_length=1024).input_ids.to(device)

        n_correct_this = 0
        for sample_i in range(args.n_samples):
            try:
                with torch.no_grad():
                    out = model.generate(
                        input_ids,
                        max_new_tokens=args.max_new_tokens,
                        do_sample=True, temperature=args.temperature, top_p=args.top_p,
                        pad_token_id=eos_id or 0,
                    )
                gen_ids = out[0][input_ids.shape[1]:]
                gen_text = tok.decode(gen_ids, skip_special_tokens=True)
            except Exception:
                continue
            full_code = extract_code(gen_text, prompt_raw)
            test_code = full_code + "\n\n" + test + f"\ncheck({entry_point})\n"
            try:
                with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
                    f.write(test_code); tp = f.name
                r = subprocess.run(["python3", tp], capture_output=True, text=True, timeout=args.timeout_sec)
                if r.returncode == 0:
                    n_correct_this += 1
                os.unlink(tp)
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

        per_problem.append({"task_id": task_id, "n": args.n_samples, "c": n_correct_this})
        n_done = len(per_problem)
        if n_done % 5 == 0 or n_done == 1:
            elapsed = time.perf_counter() - t_start
            partial_p1 = sum(1 for r in per_problem if r["c"] > 0) / n_done  # any-pass = pass@n
            print(f"  [{n_done:3d}/{args.end-args.start}] any-pass={partial_p1:.3f}  elapsed={elapsed:.0f}s")

    total_wall = time.perf_counter() - t_start
    p1 = sum(pass_at_k(r["n"], r["c"], 1) for r in per_problem) / len(per_problem)
    p5 = sum(pass_at_k(r["n"], r["c"], 5) for r in per_problem) / len(per_problem) if args.n_samples >= 5 else None
    p10 = sum(pass_at_k(r["n"], r["c"], 10) for r in per_problem) / len(per_problem) if args.n_samples >= 10 else None
    any_pass = sum(1 for r in per_problem if r["c"] > 0) / len(per_problem)

    print(f"\n[done] pass@1 = {p1:.4f}")
    if p5 is not None: print(f"[done] pass@5 = {p5:.4f}")
    if p10 is not None: print(f"[done] pass@10 = {p10:.4f}")
    print(f"[done] any-pass (≥1 of {args.n_samples}) = {any_pass:.4f}")
    print(f"[done] wall {total_wall:.0f}s")

    envelope = {
        "schema": "etzhayyim.baien.bench.passk.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "model": args.model,
        "checkpoint": args.checkpoint,
        "n_samples": args.n_samples,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "n_tasks_evaluated": len(per_problem),
        "pass1": round(p1, 4),
        "pass5": round(p5, 4) if p5 is not None else None,
        "pass10": round(p10, 4) if p10 is not None else None,
        "any_pass_at_n": round(any_pass, 4),
        "wall_sec": round(total_wall, 1),
        "per_problem": per_problem,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
