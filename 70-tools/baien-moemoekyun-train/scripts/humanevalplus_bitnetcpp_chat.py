#!/usr/bin/env python3
"""humanevalplus_bitnetcpp_chat.py — canonical HumanEval+ pass@1 via bitnet.cpp + chat template.

Per cycle 22 finding: raw-completion bitnet.cpp generates unrelated Python
(matches MS card 38.40%). Chat-template path matches cycle 8-11 evalplus
58.3% baseline.

Uses ChatFormat.encode_dialog_prompt() to apply Llama-3 chat template,
which BitNet 2B-4T was trained on.

Run on RTX 5090:
    python3 /workspace/humanevalplus_bitnetcpp_chat.py \\
        --start 0 --end 164 --max-prompt-len 384 --max-new-tokens 384
"""

from __future__ import annotations

import argparse
import io
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


def make_instruction(prompt: str) -> str:
    """Wrap HumanEval+ prompt in instruction-style for chat-template completion.

    Format matches evalplus convention: include the function signature + docstring
    as code in the user message, asking the model to provide the complete
    implementation.
    """
    return (
        f"Please provide a complete Python implementation for the following function:\n\n"
        f"```python\n{prompt}```\n\n"
        f"Complete the function by appending the implementation below the signature. "
        f"Output only the complete function code in a ```python code block, no explanations."
    )


def extract_code(gen_text: str, prompt: str) -> str:
    """Extract function body from chat-template generation.

    Strategy:
      1. Strip outermost ```python fences (take content of first complete block)
      2. If the function signature appears in gen, take the complete redefinition
         INCLUDING any imports/from statements that precede it
      3. Otherwise treat gen as raw function body and append to original prompt
      4. Always ensure the original prompt's imports stay accessible (prepend
         original prompt prefix if gen is missing them)
    """
    # Strip code fences — take content of first ```python ... ``` block
    if "```" in gen_text:
        m = re.search(r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)", gen_text, re.DOTALL)
        if m:
            gen_text = m.group(1)
    lines = gen_text.splitlines()
    func_name_m = re.search(r"def\s+(\w+)\s*\(", prompt)
    if func_name_m:
        func_name = func_name_m.group(1)
        # Find position of the function def
        def_idx = None
        for i, ln in enumerate(lines):
            if re.search(rf"def\s+{re.escape(func_name)}\s*\(", ln):
                def_idx = i
                break
        if def_idx is not None:
            # Cut where next top-level non-indented def/class appears AFTER our def
            end_idx = len(lines)
            for j in range(def_idx + 1, len(lines)):
                ln2 = lines[j]
                if ln2 and not ln2.startswith((" ", "\t", "#")) and (
                    ln2.lstrip().startswith("def ") or ln2.lstrip().startswith("class ")
                    or ln2.lstrip().startswith("if __name__")
                ):
                    end_idx = j
                    break
            # Take everything from start to end_idx — INCLUDES preceding imports
            extracted = "\n".join(lines[:end_idx])
            # Always prepend original prompt's imports too (in case gen missed them)
            return prompt.split("def ")[0] + extracted
    # No signature in response: append gen as body to prompt
    return prompt + gen_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="/workspace/BitNet/gpu/checkpoints/")
    p.add_argument("--output", default="/workspace/humanevalplus-bitnetcpp-chat-result.jsonl")
    p.add_argument("--max-prompt-len", type=int, default=384)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=164)
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

    print(f"\n[data] loading evalplus/humanevalplus")
    from datasets import load_dataset
    ds = load_dataset("evalplus/humanevalplus", split="test")
    print(f"[data] {len(ds)} total; range [{args.start}, {args.end})")

    EOS = g.tokenizer.eos_id
    # BitNet 2B uses Llama-3 special tokens; <|eot_id|> is the stop for chat
    EOT = g.tokenizer.special_tokens.get("<|eot_id|>", EOS)
    print(f"[tok] EOS={EOS}  EOT={EOT}")

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
        # Encode with chat template — BitNet uses simple "User: <msg> <|eot_id|> Assistant: "
        # format (NOT Llama-3 <|start_header_id|>...). completion=True appends "Assistant: ".
        ids = cf.encode_dialog_prompt(
            dialog=[{"role": "user", "content": instruction}],
            completion=True,
        )
        if len(ids) > args.max_prompt_len:
            # Truncate from start, preserve "<|eot_id|> Assistant: " tail (last 4 tokens)
            tail = ids[-4:]
            ids = ids[: args.max_prompt_len - 4] + tail
        # NO front-padding — FastGen internally right-pads with token 1 to prompt_length,
        # and trim_answer uses real prompt_len. The prompt_length on FastGen is the MAX
        # prompt length; padding shorter prompts is FastGen's job, not ours.
        n_real = len(ids)

        t_gen = time.perf_counter()
        try:
            stats, out_list = g.generate_all(
                [ids], use_cuda_graphs=False, use_sampling=False,
            )
            # FastGen.generate_all returns ONLY generated tokens (prompt already trimmed)
            gen_ids = out_list[0]
            # Stop at EOT or EOS
            stop_idx = len(gen_ids)
            for stop in (EOT, EOS):
                if stop is not None and stop in gen_ids:
                    stop_idx = min(stop_idx, gen_ids.index(stop))
            gen_ids = gen_ids[:stop_idx]
            gen_text = g.tokenizer.decode(gen_ids)
        except Exception as e:
            results.append({"task_id": task_id, "passed": False, "error": f"gen_err: {type(e).__name__}: {str(e)[:120]}"})
            continue
        gen_wall = time.perf_counter() - t_gen

        # Extract code
        full_code = extract_code(gen_text, prompt_raw)
        test_code = full_code + "\n\n" + test + f"\ncheck({entry_point})\n"

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
            "gen_text_first_100": gen_text[:100] if not passed else None,
        })

        n_done = len(results)
        elapsed = time.perf_counter() - t_start
        eta = elapsed / n_done * (args.end - args.start - n_done) if n_done else 0
        if n_done % 10 == 0 or n_done == 1:
            print(f"  [{n_done:3d}/{args.end-args.start}] pass@1={n_pass/n_done:.3f} ({n_pass}/{n_done})  elapsed={elapsed:.0f}s eta={eta:.0f}s gen={gen_wall:.1f}s")

    total_wall = time.perf_counter() - t_start
    n_done = len(results)
    pass1 = n_pass / n_done if n_done else 0
    print(f"\n[done] pass@1 = {n_pass}/{n_done} = {pass1:.4f}  wall={total_wall:.0f}s = {total_wall/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "device": "cuda",
        "model": "microsoft/bitnet-b1.58-2B-4T (ternary native W2A8) + chat template",
        "harness": "bitnet.cpp FastGen + ChatFormat.encode_dialog_prompt + evalplus dataset",
        "task": "humanevalplus_chat",
        "task_source": "evalplus/humanevalplus",
        "n_tasks_total": 164,
        "n_tasks_evaluated": n_done,
        "start_idx": args.start,
        "end_idx": args.end,
        "n_pass": n_pass,
        "pass1": round(pass1, 4),
        "wall_sec": round(total_wall, 1),
        "tasks_per_min": round(n_done / total_wall * 60, 2) if total_wall else 0,
        "scoring": "exec-graded subprocess (timeout 10s, NO docker) + chat template instruction wrap",
        "max_prompt_len": args.max_prompt_len,
        "max_new_tokens": args.max_new_tokens,
        "instruction_template": "Complete the following Python function. Write only the function body...",
        "results_sample": results[:3] + results[-3:] if len(results) > 6 else results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
