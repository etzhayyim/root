#!/usr/bin/env python3
r"""train_cpt — CPT-LoRA 継続事前学習 (gfx1151 / ROCm)。

生テキスト jsonl ({"text": …}) で causal-LM の継続学習 LoRA を回す。SFT ではなく
CPT: モデルに Clojure / kotoba-Datomic イディオムの「言語分布」を焼き込む段。

EVO で動かす (ComfyUI venv, torch 2.5.1+rocm6.2):
  HSA_OVERRIDE_GFX_VERSION=11.0.0 ~/ComfyUI/venv/bin/python train_cpt.py \
      --model HuggingFaceTB/SmolLM2-135M \      # smoke 用 (疎通確認)
      --data cpt-gold.jsonl --out cpt-out --epochs 1 --smoke

本番ベースは fleet の gemma4:e4b-it-qat と同一重み:
  google/gemma-4-E4B-it-qat-q4_0-unquantized  (dequant QAT it = "4B_dequant_qat_it_hf"; gated なし)
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

    # Gemma4 は *ForConditionalGeneration (マルチモーダル)。テキスト CPT には
    # CausalLM として読むか、失敗時は text submodel を取り出す。
    try:
        model = AutoModelForCausalLM.from_pretrained(
            args.model, torch_dtype=torch.bfloat16).cuda()
    except (ValueError, KeyError, TypeError):
        from transformers import AutoModelForImageTextToText
        full = AutoModelForImageTextToText.from_pretrained(
            args.model, torch_dtype=torch.bfloat16).cuda()
        model = getattr(getattr(full, "model", full), "language_model", None) or full
        print(f"loaded text submodel: {type(model).__name__}")
    # use_reentrant=False が必須: reentrant checkpointing は後付け LoRA への勾配を遮断し
    # lora_B がゼロのまま (no-op) になる。enable_input_require_grads と併用する。
    model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()

    # CPT は decoder の全 linear に薄く LoRA を当てる。
    # CRITICAL (Gemma4): vision_tower の proj は Gemma4ClippableLinear、language_model の proj は
    # 素の nn.Linear。テキスト loss の勾配は language_model にしか流れないので、ターゲットは
    # language_model の decoder linear に **スコープ** する (regex)。vision tower を狙うと
    # lora_B がゼロのまま (no-op) になる — 実際に踏んだ罠。
    has_lm = any("language_model" in n for n, _ in model.named_modules())
    proj = "q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj"
    if has_lm:
        # PEFT の target_modules は str(=regex, fullmatch) か list[str]。re.Pattern を渡すと
        # `key in target_modules` で TypeError。regex は str で渡す。
        targets = rf".*language_model\.layers\.\d+\.(self_attn|mlp)\.({proj})"
    else:
        targets = proj.split("|")
    lora = LoraConfig(
        r=args.lora_r, lora_alpha=args.lora_r * 2, lora_dropout=0.05,
        target_modules=targets,
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

    # no-op ガード: lora_B が全てゼロなら勾配が流れていない (silent no-op を二度と通さない)
    nz_b = sum(float(p.detach().abs().sum()) for n, p in model.named_parameters()
               if "lora_B" in n)
    if nz_b == 0.0:
        raise RuntimeError("lora_B all-zero — gradients never reached the adapter "
                           "(no-op). Check gradient_checkpointing use_reentrant=False.")
    print(f"lora_B nonzero mass: {nz_b:.4f} — adapter learned")

    if not args.smoke:
        model.save_pretrained(args.out)
        tok.save_pretrained(args.out)
        print(f"CPT-LoRA saved → {args.out}")
    else:
        print("SMOKE OK — CPT pipeline e2e (tokenize → LoRA → train step → loss)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
