#!/usr/bin/env python3
"""bench_humanevalplus.py — minimal HumanEval+ exec-graded eval for BitNet 2B baseline.

Per ADR-2605262100 Phase 3 + moemoekyun-bench-plan-260526.md.

Loads evalplus/humanevalplus from HF (already pinned W6, CID bafkrei...),
generates code per task via BitNet 2B greedy decoding, exec-runs against
HumanEval+ test cases in a sandboxed subprocess (timeout 10s/task), reports
pass@1.

Sandboxing: subprocess + signal.alarm timeout. NO docker (too heavy for smoke).
Trade-off: malicious generated code could escape. Acceptable for BitNet 2B
baseline (no adversarial inputs) but R2+ should use proper docker sandbox.

Output: 90-docs/baien/bench-snapshot-260526-bitnet2b-humanevalplus.jsonl

Run:
    HF_HOME=/Volumes/260317/models/huggingface KMP_DUPLICATE_LIB_OK=TRUE \
        python3 70-tools/baien-moemoekyun-train/scripts/bench_humanevalplus.py \
        --n-tasks 20
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HOME", "/Volumes/260317/models/huggingface")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import torch


def exec_task_in_subprocess(code: str, test_code: str, timeout_sec: int = 10) -> tuple[bool, str]:
    """Exec generated code + test in a subprocess (python -c) with timeout.

    Avoids multiprocessing pickling issues + provides proper isolation.
    NOT a docker sandbox — generated code runs as current user. For smoke only.
    """
    import subprocess, tempfile
    full = code + "\n\n" + test_code
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(full)
        path = f.name
    try:
        r = subprocess.run(
            ["python3", path],
            capture_output=True, text=True, timeout=timeout_sec,
        )
        if r.returncode == 0:
            return True, ""
        return False, (r.stderr or r.stdout)[:200]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:200]}"
    finally:
        os.unlink(path)


def extract_python_code(generated: str, signature: str) -> str:
    """Heuristic: keep the function body until next top-level def or end-of-text."""
    lines = generated.splitlines()
    out = [signature.rstrip() + "\n"]
    in_body = False
    for ln in lines:
        if not in_body:
            if ln.strip().startswith("def ") and "(" in ln:
                in_body = True
                continue
            if ln.startswith("    ") or ln.startswith("\t"):
                in_body = True
        if in_body:
            # Stop at next top-level def
            if ln and not ln.startswith((" ", "\t")) and ln.lstrip().startswith("def "):
                break
            out.append(ln + "\n")
    return "".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    parser.add_argument("--n-tasks", type=int, default=None, help="Subset (default: all 164)")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--timeout-sec", type=int, default=10)
    parser.add_argument("--output",
                        default=str(Path(__file__).parent.parent.parent.parent /
                                    "90-docs/baien/bench-snapshot-260526-bitnet2b-humanevalplus.jsonl"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"[env] torch={torch.__version__} mps={torch.backends.mps.is_available()}")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[env] device={device}")

    print(f"\n[load] {args.model}")
    t0 = time.perf_counter()
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16, trust_remote_code=False)
    model.to(device).eval()
    print(f"[load] {time.perf_counter() - t0:.1f}s")

    print(f"\n[data] loading evalplus/humanevalplus")
    from datasets import load_dataset
    ds = load_dataset("evalplus/humanevalplus", split="test")
    print(f"[data] total tasks: {len(ds)}")

    indices = list(range(len(ds)))
    if args.n_tasks:
        indices = indices[:args.n_tasks]

    n_pass = 0
    results = []
    t_start = time.perf_counter()
    for i, idx in enumerate(indices):
        row = ds[idx]
        prompt = row["prompt"]  # function signature + docstring
        test = row["test"]      # test code
        entry_point = row["entry_point"]

        # Generate completion
        ids = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(
                **ids,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id or 0,
            )
        gen = tokenizer.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
        # Strip markdown code fences if BitNet generated them (instruction-tuned style):
        #   "```python\n<code>\n```" → "<code>"
        #   trailing "```" anywhere → cut
        if "```" in gen:
            # Extract code between first ```python (or ```) and next ```
            import re
            m = re.search(r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)", gen, re.DOTALL)
            if m:
                gen = m.group(1)
            else:
                gen = gen.split("```")[0]
        # Cut at next top-level def/class (avoid spurious extra definitions)
        cut_lines = []
        for ln in gen.splitlines():
            if cut_lines and ln and not ln.startswith((" ", "\t", "#")) and (
                ln.lstrip().startswith("def ") or ln.lstrip().startswith("class ")
            ):
                break
            cut_lines.append(ln)
        gen = "\n".join(cut_lines)
        code = prompt + gen  # full executable

        # Exec test
        passed, err = exec_task_in_subprocess(code, test + f"\ncheck({entry_point})", args.timeout_sec)
        if passed:
            n_pass += 1

        elapsed = time.perf_counter() - t_start
        eta = elapsed / (i + 1) * (len(indices) - i - 1)
        if (i + 1) % 5 == 0 or i == 0:
            print(f"[{i+1:3d}/{len(indices)}] pass@1={n_pass/(i+1):.3f} ({n_pass}/{i+1}) elapsed={elapsed:.0f}s eta={eta:.0f}s")

        results.append({
            "task_id": row.get("task_id", f"HumanEval+/{idx}"),
            "passed": passed,
            "error": err[:200] if not passed else None,
        })

    total = time.perf_counter() - t_start
    accuracy = n_pass / len(indices)
    print(f"\n[done] pass@1 = {n_pass}/{len(indices)} = {accuracy:.4f}")
    print(f"[done] wall: {total:.0f}s = {total/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "mac-260317",
        "device": str(device),
        "torch_version": torch.__version__,
        "model": args.model,
        "task": "humanevalplus",
        "task_source": "evalplus/humanevalplus",
        "n_tasks": len(indices),
        "n_pass": n_pass,
        "pass1": round(accuracy, 4),
        "wall_sec": round(total, 1),
        "tasks_per_min": round(len(indices) / total * 60, 2),
        "scoring": "exec-graded subprocess (multiprocessing.Process timeout=10s, NO docker — smoke only)",
        "max_new_tokens": args.max_new_tokens,
        "seed": args.seed,
        "subset": args.n_tasks if args.n_tasks else "full",
        "per_task": results if args.n_tasks and args.n_tasks <= 30 else None,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
