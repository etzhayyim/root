#!/usr/bin/env python3
"""xlam_irrelevance_bitnetcpp.py — xLAM irrelevance bench via bitnet.cpp + chat template.

BFCL-style sub-test: model receives query + tool definitions, must output
"no tool call" when no tool applies. Scored pass = no tool-call emission;
fail = any function-call attempt despite irrelevance.

Per cycle 54 Phase 3 design.
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


def make_instruction(query: str, tools: str) -> str:
    """Wrap xLAM query + tools in chat instruction."""
    return (
        f"You have access to the following tools:\n{tools}\n\n"
        f"User query: {query}\n\n"
        f"If any tool can answer the query, output the tool call as JSON. "
        f"If no tool applies, respond with 'NO_TOOL_CALL'."
    )


def contains_tool_call(gen_text: str) -> bool:
    """Detect whether generation attempts a tool call.

    Heuristics:
      - JSON object pattern { "name": ..., ... }
      - "function_call" / "tool_call" / "call_function" patterns
      - JSON with parameters object
    """
    # Explicit no-call markers (passes irrelevance)
    no_call_markers = [
        "NO_TOOL_CALL", "no_tool_call", "no tool",
        "no applicable tool", "cannot answer", "no relevant tool",
        "none of the tools", "no tool can", "I don't have",
    ]
    lower = gen_text.lower()
    for marker in no_call_markers:
        if marker.lower() in lower:
            return False  # explicitly said no call
    # Detect JSON tool-call structure
    if re.search(r'\{\s*"name"\s*:\s*"[^"]+"', gen_text):
        return True
    if re.search(r'\{\s*"function"\s*:\s*"[^"]+"', gen_text):
        return True
    if re.search(r'\bfunction_call\s*[=:]', gen_text):
        return True
    if re.search(r'\btool_call\s*[=:]', gen_text):
        return True
    # JSON array of tool calls
    if re.search(r'\[\s*\{\s*"name"', gen_text):
        return True
    # If no clear marker either way, treat as no-call (lenient on small models)
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="/workspace/BitNet/gpu/checkpoints/")
    p.add_argument("--output", default="/workspace/xlam-irrelevance-bitnetcpp-result.jsonl")
    p.add_argument("--max-prompt-len", type=int, default=768)
    p.add_argument("--max-new-tokens", type=int, default=256)
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

    print("\n[data] loading MadeAgents/xlam-irrelevance-7.5k")
    from datasets import load_dataset
    ds = load_dataset("MadeAgents/xlam-irrelevance-7.5k", split="train")
    print(f"[data] {len(ds)} total; range [{args.start}, {min(args.end, len(ds))})")

    EOS = g.tokenizer.eos_id
    EOT = g.tokenizer.special_tokens.get("<|eot_id|>", EOS)

    n_pass = 0
    results = []
    t_start = time.perf_counter()

    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        query = row.get("query", "")
        tools_raw = row.get("tools", "")
        answers = row.get("answers", [])
        task_id = f"xlam-irrelevance/{idx}"

        # answers=[] means irrelevant — that's what we test (gold answer is no-call)
        # In this xlam-irrelevance-7.5k dataset ALL rows have answers=[]
        instruction = make_instruction(query, tools_raw if isinstance(tools_raw, str) else json.dumps(tools_raw))
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

        # For xlam-irrelevance: gold is "no tool call", so pass iff no tool call
        emitted_call = contains_tool_call(gen_text)
        passed = not emitted_call

        if passed:
            n_pass += 1

        results.append({
            "task_id": task_id,
            "passed": passed,
            "emitted_call": emitted_call,
            "gen_wall_sec": round(gen_wall, 2),
            "gen_first_100": gen_text[:100],
        })

        n_done = len(results)
        elapsed = time.perf_counter() - t_start
        eta = elapsed / n_done * (args.end - args.start - n_done) if n_done else 0
        if n_done % 20 == 0 or n_done == 1:
            print(f"  [{n_done:3d}/{args.end-args.start}] acc={n_pass/n_done:.3f} ({n_pass}/{n_done}) elapsed={elapsed:.0f}s eta={eta:.0f}s gen={gen_wall:.1f}s")

    total_wall = time.perf_counter() - t_start
    n_done = len(results)
    acc = n_pass / n_done if n_done else 0
    print(f"\n[done] irrelevance_acc = {n_pass}/{n_done} = {acc:.4f}")
    print(f"[done] wall {total_wall:.0f}s = {total_wall/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "device": "cuda",
        "model": "microsoft/bitnet-b1.58-2B-4T (ternary native W2A8)",
        "harness": "bitnet.cpp FastGen + ChatFormat + xlam-irrelevance contains_tool_call check",
        "task": "xlam_irrelevance_chat",
        "task_source": "MadeAgents/xlam-irrelevance-7.5k",
        "n_tasks_evaluated": n_done,
        "start_idx": args.start,
        "end_idx": args.end,
        "n_pass": n_pass,
        "accuracy": round(acc, 4),
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_done / total_wall * 60, 2) if total_wall else 0,
        "scoring": "irrelevance detection: pass = no tool-call emitted (gold=[]); fail = JSON tool-call attempt",
        "results_sample": results[:3] + results[-3:] if len(results) > 6 else results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
