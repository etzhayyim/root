#!/usr/bin/env python3
"""Agentic QLoRA trainer for gemma-4-26B-A4B on EVO-X2 (ADR-2605302359 §3).

Owned-hardware now-path: EVO-X2 (AMD Ryzen AI Max+ 395, 128 GB unified —
32 GB VRAM UMA carve-out + 96 GB sys, BIOS-re-carvable). 4-bit base ≈14 GB +
LoRA(shared FFN + attention) + AdamW(adapter-only) + grad-checkpointed
activations fit in unified memory — no sharding, no Council gate.

Stack: transformers + peft + trl + bitsandbytes (ROCm). Same family as
gemma-coder-distill (ADR-2605250400); extended with the MoE-aware target set
(moe_targets.resolve_targets) so the 22.84 B routed experts stay frozen.

Inference of the resulting adapter remains Murakumo-only (ADR-2605215000).
Artifact name: baien-server-agentic-gemma4-26b-a4b-r<NN> (server carve-out;
NOT the ≤12 B edge baien, ADR-2605241900).

Run on EVO-X2:
  python train_evox2.py \
    --model-id <hf-repo-with-safetensors-for-gemma-4-26B-A4B> \
    --data seed/agentic-tooluse-r0-seed.jsonl \
    --out /Volumes/.../baien-server-agentic-gemma4-26b-a4b-r0 \
    --r 16 --epochs 2

NOTE: training needs HF *safetensors* weights (the .gguf is llama.cpp-only).
Point --model-id at the safetensors repo for gemma-4-26B-A4B; confirm it exists
before running (Unsloth ships GGUF; the bf16/safetensors source is required).
"""
from __future__ import annotations
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moe_targets import resolve_targets, summarize


def load_messages_dataset(path: str):
    from datasets import Dataset
    rows = [json.loads(l) for l in open(path) if l.strip()]
    # each row: {"messages": [...], optionally "tools": [...]}
    return Dataset.from_list(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", required=True,
                    help="HF repo with safetensors for gemma-4-26B-A4B")
    ap.add_argument("--data", default="seed/agentic-tooluse-r0-seed.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--max-seq", type=int, default=4096)
    ap.add_argument("--train-router", action="store_true",
                    help="ALSO adapt the router (risky; off by default, ADR §2)")
    ap.add_argument("--dry-run", action="store_true",
                    help="resolve targets + param accounting, do not train")
    args = ap.parse_args()

    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    # 4-bit QLoRA base (nf4 + double-quant, bf16 compute)
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tok = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, quantization_config=bnb, device_map="auto",
        torch_dtype=torch.bfloat16, trust_remote_code=True,
    )

    targets = resolve_targets(model, args.train_router)
    acct = summarize(model, args.train_router)
    print(f"[targets] {len(targets)} modules | "
          f"trainable base {acct['target_base_params']/1e6:.0f}M | "
          f"frozen experts {acct['frozen_routed_expert_params']/1e9:.2f}B", flush=True)
    if args.dry_run:
        print(json.dumps({"targets_sample": targets[:8], "accounting": acct}, indent=2))
        return

    model = prepare_model_for_kbit_training(
        model, use_gradient_checkpointing=True)
    lora = LoraConfig(
        r=args.r, lora_alpha=args.alpha, lora_dropout=args.dropout,
        target_modules=targets,          # FULL paths → experts excluded
        task_type="CAUSAL_LM", bias="none",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    ds = load_messages_dataset(args.data)

    def fmt(row):
        # apply the model's chat template (handles tool/function-call turns)
        return tok.apply_chat_template(
            row["messages"], tools=row.get("tools"),
            tokenize=False, add_generation_prompt=False)

    from trl import SFTTrainer, SFTConfig
    sft = SFTConfig(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        warmup_steps=50,
        lr_scheduler_type="cosine",
        bf16=True,
        gradient_checkpointing=True,
        max_seq_length=args.max_seq,
        logging_steps=5,
        save_strategy="epoch",
        packing=False,
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model, args=sft, train_dataset=ds,
        formatting_func=fmt, processing_class=tok,
    )
    trainer.train()
    trainer.save_model(args.out)
    tok.save_pretrained(args.out)
    print(f"[done] adapter saved → {args.out}", flush=True)
    print("[next] verify routing health: python verify_routing.py "
          f"--before <pre-tags> --after <re-profiled-tags>", flush=True)


if __name__ == "__main__":
    main()
