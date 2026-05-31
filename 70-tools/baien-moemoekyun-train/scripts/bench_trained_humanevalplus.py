#!/usr/bin/env python3
"""bench_trained_humanevalplus.py — bench moemoekyun-trained checkpoint vs 18.90% baseline.

Loads BitNet 2B + MoE residual + checkpoint, runs HumanEval+ via HF transformers
generate (not bitnet.cpp; packed kernel doesn't yet integrate MoE).

Δ = (this pass@1 - 18.90% baseline) pp
Per ADR-2605262100 R1.5 commit_gate: Δ ≥ +3pp required for commit_to_registry.
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


def make_instruction(prompt: str) -> str:
    return (
        f"Please provide a complete Python implementation for the following function:\n\n"
        f"```python\n{prompt}```\n\n"
        f"Complete the function by appending the implementation below the signature. "
        f"Output only the complete function code in a ```python code block, no explanations."
    )


def extract_code(gen_text: str, prompt: str) -> str:
    if "```" in gen_text:
        m = re.search(r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)", gen_text, re.DOTALL)
        if m:
            gen_text = m.group(1)
    lines = gen_text.splitlines()
    func_name_m = re.search(r"def\s+(\w+)\s*\(", prompt)
    if func_name_m:
        func_name = func_name_m.group(1)
        def_idx = None
        for i, ln in enumerate(lines):
            if re.search(rf"def\s+{re.escape(func_name)}\s*\(", ln):
                def_idx = i
                break
        if def_idx is not None:
            end_idx = len(lines)
            for j in range(def_idx + 1, len(lines)):
                ln2 = lines[j]
                if ln2 and not ln2.startswith((" ", "\t", "#")) and (
                    ln2.lstrip().startswith("def ") or ln2.lstrip().startswith("class ")
                    or ln2.lstrip().startswith("if __name__")
                ):
                    end_idx = j
                    break
            return prompt.split("def ")[0] + "\n".join(lines[:end_idx])
    return prompt + gen_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--checkpoint", default="/workspace/moe-ckpt-c26.pt",
                   help="MoE state_dict from cycle 26 production train")
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--n-experts", type=int, default=16)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=32)
    p.add_argument("--layers-fraction", type=float, default=0.10)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=164)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--timeout-sec", type=int, default=10)
    p.add_argument("--output", default="/workspace/bench-trained-c26-result.jsonl")
    p.add_argument("--expert-kind", default="ffn", choices=["ffn","memory"])
    p.add_argument("--routing-mode", default="learned", choices=["learned","distance"], help="MoCLE-style cluster routing if distance")
    p.add_argument("--baseline-pass1", type=float, default=0.1890,
                   help="Pre-train baseline for Δ computation (cycle 24 = 18.90%)")
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.attach import (
        attach_moe_to_model, freeze_backbone_verify
    )

    device = torch.device("cuda")
    print(f"[env] {torch.cuda.get_device_name(0)}")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"\n[load] {args.model}")
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16, trust_remote_code=False)
    model.to(device).eval()
    print(f"[load] {time.perf_counter() - t0:.1f}s  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    cfg = model.config
    hidden = cfg.hidden_size
    intermediate = cfg.intermediate_size
    n_layers = cfg.num_hidden_layers
    n_moe = max(1, int(round(n_layers * args.layers_fraction)))
    moe_layer_indices = list(range(n_layers - n_moe, n_layers))
    print(f"[moe] re-attaching to layers {moe_layer_indices[0]}..{moe_layer_indices[-1]}")

    moe_wrappers = attach_moe_to_model(
        model,
        moe_layer_indices=moe_layer_indices,
        hidden_size=hidden,
        intermediate_size=intermediate,
        num_experts=args.n_experts,
        top_k=args.top_k,
        expert_hidden_ratio=args.expert_hidden_ratio,
        ffn_attribute_name="mlp",
        routing_mode=args.routing_mode,
        expert_kind=args.expert_kind,
    )
    for fqn, w in moe_wrappers.items():
        w.to(device=device, dtype=torch.bfloat16)
    print(f"[moe] attached {len(moe_wrappers)} wrappers")

    # Load checkpoint
    print(f"\n[ckpt] loading {args.checkpoint}")
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    n_loaded = 0
    for fqn, state in ckpt.items():
        if fqn in moe_wrappers:
            moe_wrappers[fqn].load_state_dict(state)
            n_loaded += 1
    print(f"[ckpt] loaded state for {n_loaded}/{len(moe_wrappers)} wrappers")

    freeze_backbone_verify(model, moe_wrappers)
    model.eval()
    print(f"[ckpt] vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    # HumanEval+ via HF transformers generate
    from datasets import load_dataset
    print(f"\n[data] loading evalplus/humanevalplus")
    ds = load_dataset("evalplus/humanevalplus", split="test")
    print(f"[data] {len(ds)} total; range [{args.start}, {args.end})")

    n_pass = 0
    results = []
    t_start = time.perf_counter()

    for idx in range(args.start, args.end):
        row = ds[idx]
        prompt_raw = row["prompt"]
        test = row["test"]
        entry_point = row["entry_point"]
        task_id = row.get("task_id", f"HumanEval+/{idx}")

        instruction = make_instruction(prompt_raw)
        msgs = [{"role": "user", "content": instruction}]
        try:
            chat_prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        except Exception:
            chat_prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"

        input_ids = tok(chat_prompt, return_tensors="pt", truncation=True, max_length=1024).input_ids.to(device)

        t_gen = time.perf_counter()
        try:
            with torch.no_grad():
                out = model.generate(
                    input_ids,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    pad_token_id=tok.eos_token_id or 0,
                )
            gen_ids = out[0][input_ids.shape[1]:]
            gen_text = tok.decode(gen_ids, skip_special_tokens=True)
        except Exception as e:
            results.append({"task_id": task_id, "passed": False, "error": f"gen_err: {type(e).__name__}: {str(e)[:120]}"})
            continue
        gen_wall = time.perf_counter() - t_gen

        full_code = extract_code(gen_text, prompt_raw)
        test_code = full_code + "\n\n" + test + f"\ncheck({entry_point})\n"

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
            "error": err[:200] if not passed else None,
        })

        n_done = len(results)
        elapsed = time.perf_counter() - t_start
        eta = elapsed / n_done * (args.end - args.start - n_done) if n_done else 0
        if n_done % 5 == 0 or n_done == 1:
            print(f"  [{n_done:3d}/{args.end-args.start}] pass@1={n_pass/n_done:.3f} ({n_pass}/{n_done})  elapsed={elapsed:.0f}s eta={eta:.0f}s gen={gen_wall:.1f}s")

    total_wall = time.perf_counter() - t_start
    n_done = len(results)
    pass1 = n_pass / n_done if n_done else 0
    delta_pp = (pass1 - args.baseline_pass1) * 100
    print(f"\n[done] pass@1 = {n_pass}/{n_done} = {pass1:.4f}")
    print(f"[done] vs baseline {args.baseline_pass1:.4f}: Δ = {delta_pp:+.2f} pp")
    print(f"[done] wall {total_wall:.0f}s = {total_wall/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "device": "cuda",
        "model": f"{args.model} + moemoekyun MoE residual ({n_moe} layers, ckpt {args.checkpoint})",
        "harness": "HF transformers generate + chat template + evalplus dataset",
        "task": "humanevalplus_chat_trained",
        "n_tasks_evaluated": n_done,
        "start_idx": args.start,
        "end_idx": args.end,
        "n_pass": n_pass,
        "pass1": round(pass1, 4),
        "baseline_pass1": args.baseline_pass1,
        "delta_pp": round(delta_pp, 2),
        "r15_commit_gate_threshold_pp": 3.0,
        "r15_commit_gate_passed": delta_pp >= 3.0,
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_done / total_wall * 60, 2) if total_wall else 0,
        "n_experts": args.n_experts,
        "top_k": args.top_k,
        "n_moe_layers": n_moe,
        "checkpoint": args.checkpoint,
        "scoring_note": "Δ vs cycle 24 canonical baseline 18.90%. Trained on 100 SFT steps of R1.4 corpus (NOT full 5000-step R1.4 — small sample for pipeline validation).",
        "results_sample": results[:3] + results[-3:] if len(results) > 6 else results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"\n[done] appended to {args.output}")


if __name__ == "__main__":
    main()
