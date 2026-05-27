#!/usr/bin/env python3
"""bench_trained_hellaswag.py — R1.5 ckpt HellaSwag Δ via HF transformers."""
import argparse, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import torch


def make_instruction(ctx, endings):
    options = "\n".join(f"{chr(65+i)}. {e}" for i, e in enumerate(endings))
    return (f"Complete the following scenario. Choose the most likely continuation.\n\n"
            f"Scenario: {ctx}\n\n"
            f"Options:\n{options}\n\n"
            f"Answer with just the letter A, B, C, or D.")


def extract_answer(gen_text):
    for pat in [r"\b([ABCD])\b", r"(?:answer\s*[:=]\s*|is\s+)([ABCD])", r"\(([ABCD])\)"]:
        m = re.search(pat, gen_text, re.IGNORECASE)
        if m:
            return ord(m.group(1).upper()) - ord("A")
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--n-experts", type=int, default=32)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=32)
    p.add_argument("--layers-fraction", type=float, default=0.10)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=200)
    p.add_argument("--max-new-tokens", type=int, default=64)
    p.add_argument("--output", default="/workspace/bench-hellaswag-trained-result.jsonl")
    p.add_argument("--baseline-accuracy", type=float, default=0.4450)
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
    ds = load_dataset("Rowan/hellaswag", split="validation")
    n_correct = 0
    results = []
    t_start = time.perf_counter()
    for idx in range(args.start, min(args.end, len(ds))):
        row = ds[idx]
        ctx = row.get("ctx", "")
        endings = row.get("endings", [])
        gold = int(row.get("label", -1))
        if len(endings) != 4 or gold not in (0, 1, 2, 3):
            continue
        instruction = make_instruction(ctx, endings)
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
            results.append({"idx": idx, "correct": False, "err": str(e)[:80]})
            continue
        pred = extract_answer(gen_text)
        correct = pred == gold
        if correct:
            n_correct += 1
        results.append({"idx": idx, "correct": correct, "pred": pred, "gold": gold})
        n_done = len(results)
        if n_done % 25 == 0 or n_done == 1:
            elapsed = time.perf_counter() - t_start
            print(f"  [{n_done:3d}/{args.end-args.start}] acc={n_correct/n_done:.3f} ({n_correct}/{n_done}) elapsed={elapsed:.0f}s")

    total_wall = time.perf_counter() - t_start
    n_done = len(results)
    acc = n_correct / n_done if n_done else 0
    delta_pp = (acc - args.baseline_accuracy) * 100
    print(f"\n[done] acc={n_correct}/{n_done}={acc:.4f}  Δ={delta_pp:+.2f}pp")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "model": f"{args.model} + moemoekyun MoE residual (ckpt {args.checkpoint})",
        "task": "hellaswag_chat_trained",
        "n_tasks_evaluated": n_done,
        "n_correct": n_correct,
        "accuracy": round(acc, 4),
        "baseline_accuracy": args.baseline_accuracy,
        "delta_pp": round(delta_pp, 2),
        "wall_sec": round(total_wall, 1),
        "checkpoint": args.checkpoint,
    }
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
