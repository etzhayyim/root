#!/usr/bin/env python3
"""Best-of-N with LINT verifier (ruff) — stronger signal than syntax-only.

Score = -n_errors (more negative = worse); picks sample with fewest errors.
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
import torch


def extract_code(gen: str, prompt: str) -> str:
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", gen, re.DOTALL)
    if blocks:
        return max(blocks, key=len)
    return prompt + gen.split("```")[0]


def lint_score(code: str, timeout_sec: int = 3) -> float:
    """Higher = better. 1.0 = no errors, drops by 0.1 per error, min 0.
    Returns -inf if even compile fails (worse than syntax error).
    """
    try:
        compile(code, "<lint>", "exec")
    except (SyntaxError, ValueError):
        return -1.0  # worse than no-lint-info
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        r = subprocess.run(
            ["ruff", "check", "--output-format=concise", path],
            capture_output=True, text=True, timeout=timeout_sec,
        )
        # Errors are non-empty lines
        n_errors = len([ln for ln in r.stdout.splitlines() if ln.strip()])
        return max(0.0, 1.0 - 0.1 * n_errors)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1.0  # ruff missing — fall through to syntax-only OK
    finally:
        try:
            Path(path).unlink()
        except OSError:
            pass


def run_test(code: str, test: str, entry_point: str, timeout_sec: int = 10) -> bool:
    full = code + "\n\n" + test + f"\ncheck({entry_point})\n"
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(full); path = f.name
    try:
        r = subprocess.run(["python3", path], capture_output=True, text=True, timeout=timeout_sec)
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False
    finally:
        try: os.unlink(path)
        except OSError: pass


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
    p.add_argument("--n-samples", type=int, default=5)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=50)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.attach import attach_moe_to_model, freeze_backbone_verify
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = torch.device("cuda")
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to(device).eval()
    cfg = model.config
    n_moe = max(1, int(round(cfg.num_hidden_layers * args.layers_fraction)))
    moe_indices = list(range(cfg.num_hidden_layers - n_moe, cfg.num_hidden_layers))
    moe_wrappers = attach_moe_to_model(
        model, moe_layer_indices=moe_indices,
        hidden_size=cfg.hidden_size, intermediate_size=cfg.intermediate_size,
        num_experts=args.n_experts, top_k=args.top_k,
        expert_hidden_ratio=args.expert_hidden_ratio, ffn_attribute_name="mlp",
        routing_mode=args.routing_mode, expert_kind=args.expert_kind,
    )
    for w in moe_wrappers.values():
        w.to(device=device, dtype=torch.bfloat16)
    sd = torch.load(args.checkpoint, map_location=device)
    for fqn, w in moe_wrappers.items():
        if fqn in sd:
            w.load_state_dict(sd[fqn], strict=False)
    freeze_backbone_verify(model, moe_wrappers)
    model.eval()

    from datasets import load_dataset
    ds = load_dataset("evalplus/humanevalplus", split="test")
    print(f"[data] Best-of-{args.n_samples} with LINT verifier (ruff), T={args.temperature}")

    per_problem = []
    t_start = time.perf_counter()
    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        task_id, prompt_raw = row["task_id"], row["prompt"]
        test, entry_point = row["test"], row["entry_point"]
        instr = (f"Complete the following Python function. "
                 f"Return the full function body inside a ```python``` code block.\n\n"
                 f"```python\n{prompt_raw}```")
        msgs = [{"role": "user", "content": instr}]
        try:
            chat = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        except Exception:
            chat = f"### Instruction:\n{instr}\n\n### Response:\n"
        input_ids = tok(chat, return_tensors="pt", truncation=True, max_length=1024).input_ids.to(device)
        samples, scores = [], []
        for _ in range(args.n_samples):
            with torch.no_grad():
                out = model.generate(
                    input_ids, max_new_tokens=args.max_new_tokens,
                    do_sample=True, temperature=args.temperature, top_p=args.top_p,
                    pad_token_id=tok.eos_token_id or 0,
                )
            text = tok.decode(out[0][input_ids.shape[1]:], skip_special_tokens=True)
            code = extract_code(text, prompt_raw)
            samples.append(code)
            scores.append(lint_score(code))
        best_idx = max(range(args.n_samples), key=lambda i: scores[i])
        passed = run_test(samples[best_idx], test, entry_point)
        oracle_any = any(run_test(s, test, entry_point) for s in samples)
        per_problem.append({"task_id": task_id, "passed": passed,
                             "oracle_pass_any": oracle_any,
                             "best_lint_score": scores[best_idx]})
        n_done = len(per_problem)
        if n_done % 10 == 0 or n_done == 1:
            elapsed = time.perf_counter() - t_start
            ls = sum(1 for r in per_problem if r["passed"]) / n_done
            orc = sum(1 for r in per_problem if r["oracle_pass_any"]) / n_done
            print(f"  [{n_done:3d}/{args.end-args.start}] lint-Bon={ls:.3f}  oracle-any={orc:.3f}  elapsed={elapsed:.0f}s")

    wall = time.perf_counter() - t_start
    lint_pass = sum(1 for r in per_problem if r["passed"]) / len(per_problem)
    oracle_any = sum(1 for r in per_problem if r["oracle_pass_any"]) / len(per_problem)
    print(f"\n[done] lint-Best-of-{args.n_samples} pass = {lint_pass:.4f}")
    print(f"[done] oracle pass@{args.n_samples} = {oracle_any:.4f}")
    print(f"[done] wall {wall:.0f}s")

    env = {
        "schema": "etzhayyim.baien.bench.bestofn.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "model": args.model, "checkpoint": args.checkpoint,
        "n_samples": args.n_samples, "temperature": args.temperature, "top_p": args.top_p,
        "verifier": "ruff_lint",
        "n_tasks_evaluated": len(per_problem),
        "lint_bestofn_pass_rate": round(lint_pass, 4),
        "oracle_passatN_upper_bound": round(oracle_any, 4),
        "wall_sec": round(wall, 1),
        "per_problem": per_problem,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(env, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
