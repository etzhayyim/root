#!/usr/bin/env python3
"""bench_trained_bbh.py — R1.5 ckpt BBH Δ via HF transformers."""
import argparse, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import torch

CONFIGS = [
    "boolean_expressions",
    "causal_judgement",
    "date_understanding",
    "logical_deduction_five_objects",
    "word_sorting",
]


def make_instruction(question):
    return (f"Solve this problem step by step. At the end, write your final answer as 'Answer: <X>' "
            f"where X is your answer.\n\n"
            f"Problem: {question}")


def normalize(s):
    return s.strip().lower().rstrip('.').strip()


def extract_answer(gen_text):
    m = re.search(r"answer\s*[:=]\s*(.+?)(?:\n|$)", gen_text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    lines = [ln.strip() for ln in gen_text.splitlines() if ln.strip()]
    if lines:
        return lines[-1]
    return None


def is_correct(pred, gold):
    if pred is None:
        return False
    pred_norm = normalize(pred)
    gold_norm = normalize(gold)
    if pred_norm == gold_norm:
        return True
    if re.fullmatch(r"\(?\s*" + re.escape(gold_norm) + r"\s*\)?", pred_norm):
        return True
    if re.fullmatch(r"\(?\s*" + re.escape(pred_norm) + r"\s*\)?", gold_norm):
        return True
    if re.search(r"\b" + re.escape(gold_norm) + r"\b", pred_norm):
        return True
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--n-experts", type=int, default=32)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=32)
    p.add_argument("--layers-fraction", type=float, default=0.10)
    p.add_argument("--per-config", type=int, default=40)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--output", default="/workspace/bench-bbh-trained-result.jsonl")
    p.add_argument("--baseline-accuracy", type=float, default=0.2550)
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
    delta_pp = (acc - args.baseline_accuracy) * 100
    print(f"\n[done] BBH agg = {n_correct_total}/{n_done} = {acc:.4f}  Δ={delta_pp:+.2f}pp")

    envelope = {
        "schema": "etzhayyim.baien.bench.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "host": "runpod-rtx5090",
        "model": f"{args.model} + moemoekyun MoE residual (ckpt {args.checkpoint})",
        "task": "bbh_chat_trained",
        "configs": CONFIGS,
        "n_tasks_evaluated": n_done,
        "n_correct": n_correct_total,
        "accuracy": round(acc, 4),
        "baseline_accuracy": args.baseline_accuracy,
        "delta_pp": round(delta_pp, 2),
        "per_config_acc": {k: round(v, 4) for k, v in per_config_acc.items()},
        "wall_sec": round(total_wall, 1),
        "checkpoint": args.checkpoint,
    }
    with open(args.output, "a") as f:
        f.write(json.dumps(envelope) + "\n")
    print(f"[done] appended to {args.output}")


if __name__ == "__main__":
    main()
