#!/usr/bin/env python3
"""bench_trained_mbppplus.py — moemoekyun ckpt MBPP+ bench via HF transformers."""
import argparse, json, os, re, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import torch


def make_instruction(description, test_list):
    first_test = test_list[0] if test_list else ""
    return (f"Write a Python function that satisfies the following description.\n\n"
            f"Description: {description}\n\n"
            f"Example test:\n{first_test}\n\n"
            f"Output only the Python function in a ```python code block, no explanations.")


def extract_code(gen_text):
    if "```" in gen_text:
        m = re.search(r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)", gen_text, re.DOTALL)
        if m:
            gen_text = m.group(1)
    lines = gen_text.splitlines()
    out_lines = []
    in_def = False
    for ln in lines:
        if not in_def:
            if ln.lstrip().startswith(("def ", "import ", "from ")):
                in_def = True
            out_lines.append(ln)
        else:
            if ln and not ln.startswith((" ", "\t", "#")) and not ln.lstrip().startswith(("def ", "import ", "from ", "@")):
                break
            out_lines.append(ln)
    return "\n".join(out_lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--n-experts", type=int, default=64)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=32)
    p.add_argument("--layers-fraction", type=float, default=0.18)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=200)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--output", default="/workspace/bench-mbppplus-trained-result.jsonl")
    p.add_argument("--baseline-pass1", type=float, default=0.3650)
    p.add_argument("--timeout-sec", type=int, default=10)
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.attach import attach_moe_to_model, freeze_backbone_verify

    device = torch.device("cuda")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"[load] {args.model}")
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16, trust_remote_code=False)
    model.to(device).eval()
    cfg = model.config
    n_layers = cfg.num_hidden_layers
    n_moe = max(1, int(round(n_layers * args.layers_fraction)))
    moe_layer_indices = list(range(n_layers - n_moe, n_layers))
    moe_wrappers = attach_moe_to_model(
        model, moe_layer_indices=moe_layer_indices,
        hidden_size=cfg.hidden_size, intermediate_size=cfg.intermediate_size,
        num_experts=args.n_experts, top_k=args.top_k,
        expert_hidden_ratio=args.expert_hidden_ratio, ffn_attribute_name="mlp",
    )
    for fqn, w in moe_wrappers.items():
        w.to(device=device, dtype=torch.bfloat16)
    print(f"[ckpt] loading {args.checkpoint}")
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    for fqn, state in ckpt.items():
        if fqn in moe_wrappers:
            moe_wrappers[fqn].load_state_dict(state)
    freeze_backbone_verify(model, moe_wrappers)
    model.eval()

    from datasets import load_dataset
    ds = load_dataset("evalplus/mbppplus", split="test")
    n_pass = 0
    results = []
    t_start = time.perf_counter()
    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        description = row.get("text") or row.get("prompt") or ""
        test_list = row.get("test_list") or row.get("test", "").split("\n")
        assertions = row.get("test") or "\n".join(test_list)
        task_id = f"MBPP+/{row.get('task_id', idx)}"

        instruction = make_instruction(description, test_list)
        msgs = [{"role": "user", "content": instruction}]
        chat = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        input_ids = tok(chat, return_tensors="pt", truncation=True, max_length=1024).input_ids.to(device)

        try:
            with torch.no_grad():
                out = model.generate(input_ids, max_new_tokens=args.max_new_tokens, do_sample=False,
                                     pad_token_id=tok.eos_token_id or 0)
            gen_ids = out[0][input_ids.shape[1]:]
            gen_text = tok.decode(gen_ids, skip_special_tokens=True)
        except Exception as e:
            results.append({"task_id": task_id, "passed": False, "err": str(e)[:80]})
            continue

        full_code = extract_code(gen_text)
        test_code = full_code + "\n\n" + assertions
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
            err = f"{type(e).__name__}: {str(e)[:80]}"
        results.append({"task_id": task_id, "passed": passed, "err": err[:150] if not passed else None})

        n_done = len(results)
        if n_done % 20 == 0 or n_done == 1:
            elapsed = time.perf_counter() - t_start
            print(f"  [{n_done:3d}/{args.end-args.start}] pass@1={n_pass/n_done:.3f} ({n_pass}/{n_done}) elapsed={elapsed:.0f}s")

    total_wall = time.perf_counter() - t_start
    n_done = len(results)
    pass1 = n_pass / n_done if n_done else 0
    delta_pp = (pass1 - args.baseline_pass1) * 100
    print(f"\n[done] pass@1={n_pass}/{n_done}={pass1:.4f}  Δ={delta_pp:+.2f}pp vs baseline {args.baseline_pass1:.4f}")
    print(f"[done] wall {total_wall:.0f}s = {total_wall/60:.1f}min")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "model": f"{args.model} + moemoekyun MoE residual (ckpt {args.checkpoint})",
        "harness": "HF transformers + chat template + mbppplus extract_code + exec subprocess",
        "task": "mbppplus_chat_trained",
        "n_tasks_evaluated": n_done,
        "n_pass": n_pass,
        "pass1": round(pass1, 4),
        "baseline_pass1": args.baseline_pass1,
        "delta_pp": round(delta_pp, 2),
        "wall_sec": round(total_wall, 1),
        "n_experts": args.n_experts, "n_moe_layers": n_moe,
        "checkpoint": args.checkpoint,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope) + "\n")
    print(f"[done] appended to {args.output}")

if __name__ == "__main__":
    main()
