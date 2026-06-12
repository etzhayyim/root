#!/usr/bin/env python3
r"""train_cpt — CPT-LoRA 継続事前学習 (gfx1151 / ROCm)。

生テキスト jsonl ({"text": …}) で causal-LM の継続学習 LoRA を回す。SFT ではなく
CPT: モデルに Clojure / kotoba-Datomic イディオムの「言語分布」を焼き込む段。

EVO で動かす (ComfyUI venv, torch 2.5.1+rocm6.2):
  HSA_OVERRIDE_GFX_VERSION=11.0.0 ~/ComfyUI/venv/bin/python train_cpt.py \
      --model HuggingFaceTB/SmolLM2-135M \      # smoke 用 (疎通確認)
      --data cpt-gold.jsonl --out cpt-out --epochs 1 --smoke

本番は --model を gemma4 の HF id へ (google/gemma-3n-E4B-it 等; HF token + license 要)。
gfx1151 は HSA_OVERRIDE_GFX_VERSION=11.0.0 必須 (呼び出し側 env で設定)。
"""

from __future__ import annotations

import argparse


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--seq-len", type=int, default=1024)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--smoke", action="store_true",
                    help="2 step だけ回してパイプライン疎通を確認")
    args = ap.parse_args()

    import torch
    from datasets import load_dataset
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              DataCollatorForLanguageModeling, Trainer,
                              TrainingArguments)
    from peft import LoraConfig, get_peft_model

    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    ds = load_dataset("json", data_files=args.data, split="train")

    def tokenize(batch):
        out = tok(batch["text"], truncation=True, max_length=args.seq_len)
        return out

    ds = ds.map(tokenize, batched=True, remove_columns=ds.column_names)

    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16).cuda()
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    # CPT は全 linear に薄く LoRA を当てる (構文分布を広く動かす)
    lora = LoraConfig(
        r=args.lora_r, lora_alpha=args.lora_r * 2, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    targs = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        bf16=True,
        logging_steps=1,
        save_strategy="no" if args.smoke else "epoch",
        max_steps=2 if args.smoke else -1,
        report_to=[],
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
    )
    trainer = Trainer(
        model=model, args=targs, train_dataset=ds,
        data_collator=DataCollatorForLanguageModeling(tok, mlm=False))
    trainer.train()

    if not args.smoke:
        model.save_pretrained(args.out)
        tok.save_pretrained(args.out)
        print(f"CPT-LoRA saved → {args.out}")
    else:
        print("SMOKE OK — CPT pipeline e2e (tokenize → LoRA → train step → loss)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
