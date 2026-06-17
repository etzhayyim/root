"""maxwell-diffusion D4 — block-diffusion SFT trainer (uniform-corruption objective).

The RSi train-leg for the diffusion variant (ADR-2606171100 D4). DiffusionGemma's
forward exposes `forward(input_ids=prompt, decoder_input_ids=canvas) -> logits` with
NO internal loss, and its sampler initialises the canvas with RANDOM tokens (uniform
discrete diffusion, not absorbing-mask). So the SFT objective is: corrupt a fraction
t of the target canvas with random-token replacements, run the forward, and take
cross-entropy at the corrupted positions against the clean target (denoising).

This is a UNIFORM-diffusion SFT objective — a legitimate discrete-diffusion loss, but
the exact corruption schedule / self-conditioning / loss-weighting Google trained with
is unpublished, so the schedule here is the standard one and is marked for recipe
validation. PEFT-LoRA on the decoder attention projections; corpus = the shared
maxwell-sft-corpus (same data as maxwell-1). Murakumo-only (ADR-2605215000): runs on
gad. 52GB bf16 > 34GB VRAM + no ROCm 4-bit ⇒ CPU; --steps small = a MECHANISM smoke
(proves loss+backward+LoRA-step+save), full SFT needs a 4-bit GPU fit.
"""
import argparse
import json
import os
import pathlib
import random
import time

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoProcessor, DiffusionGemmaForBlockDiffusion

MID = "google/diffusiongemma-26B-A4B-it"
CORPUS = pathlib.Path.home() / "maxwell" / "corpus.jsonl"
PROV = pathlib.Path.home() / "maxwell" / "maxwell-models.local.jsonl"


def build_example(ex, proc, tok, canvas_len, pad_id):
    msgs = ex["messages"]
    sysmsg = next((m["content"] for m in msgs if m["role"] == "system"), "")
    usr = next(m["content"] for m in msgs if m["role"] == "user")
    tgt = next(m["content"] for m in msgs if m["role"] == "model")
    prompt = (sysmsg + "\n\n" + usr).strip()
    pii = proc.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=True, add_generation_prompt=True,
        return_tensors="pt", return_dict=True,
    )
    tids = tok(tgt, return_tensors="pt")["input_ids"][0][:canvas_len]
    clean = torch.full((canvas_len,), pad_id, dtype=torch.long)
    clean[: len(tids)] = tids
    valid = torch.zeros(canvas_len, dtype=torch.bool)
    valid[: len(tids)] = True
    return pii, clean, valid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--canvas", type=int, default=48)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--out", default=str(pathlib.Path.home() / "maxwell" / "out" / "diffusion-m1-smoke"))
    args = ap.parse_args()

    torch.manual_seed(0)
    random.seed(0)
    torch.set_num_threads(16)

    print(f"torch {torch.__version__} | loading {MID} (bf16, CPU)...", flush=True)
    proc = AutoProcessor.from_pretrained(MID)
    tok = getattr(proc, "tokenizer", proc)
    model = DiffusionGemmaForBlockDiffusion.from_pretrained(MID, dtype=torch.bfloat16)
    model.train()
    model.config.use_cache = False

    # The projections are Gemma4ClippableLinear wrappers (not bare nn.Linear), so
    # name-targeting fails; "all-linear" makes peft discover the inner nn.Linear
    # modules (same fix as maxwell-1's causal-LM LoRA, ADR-2606130900).
    lcfg = LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.0,
        target_modules="all-linear",
        bias="none",
    )
    model = get_peft_model(model, lcfg)
    model.print_trainable_parameters()

    vocab = model.config.text_config.vocab_size
    pad_id = getattr(tok, "pad_token_id", 0) or 0

    rows = [json.loads(l) for l in open(CORPUS) if l.strip()][: args.steps]
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)

    losses = []
    t_start = time.time()
    for step, ex in enumerate(rows):
        pii, clean, valid = build_example(ex, proc, tok, args.canvas, pad_id)
        t = random.uniform(0.3, 0.9)                       # diffusion noise level
        mask = (torch.rand(args.canvas) < t) & valid       # positions to corrupt
        corrupt = clean.clone()
        n = int(mask.sum())
        if n:
            corrupt[mask] = torch.randint(0, vocab, (n,))
        ts = time.time()
        out = model(
            input_ids=pii["input_ids"],
            attention_mask=pii["attention_mask"],
            decoder_input_ids=corrupt.unsqueeze(0),
        )
        logits = out.logits[0].float()                     # (canvas, vocab)
        labels = clean.clone()
        labels[~mask] = -100                               # loss only on corrupted positions
        loss = torch.nn.functional.cross_entropy(logits, labels, ignore_index=-100)
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(loss.item())
        print(f"step {step} t={t:.2f} masked={n} loss={loss.item():.4f} ({time.time()-ts:.0f}s)", flush=True)

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out_dir))
    dt = round(time.time() - t_start)
    prov = {
        "ts": time.strftime("%Y-%m-%d"), "run": "diffusion-m1-smoke", "kind": "train-smoke",
        "base": MID, "objective": "uniform-diffusion canvas-corruption CE (recipe-unvalidated)",
        "steps": len(losses), "canvas": args.canvas, "losses": [round(x, 4) for x in losses],
        "lora": "r8 a16 q/k/v/o-proj", "hw": "gad gfx1151 CPU bf16 (no 4-bit ROCm)",
        "runtime_s": dt, "status": "mechanism-smoke",
        "note": "proves diffusion train leg executes (loss+backward+LoRA-step+save). Full SFT needs 4-bit GPU fit + recipe validation vs Google's schedule.",
    }
    PROV.write_text((PROV.read_text() if PROV.exists() else "") + json.dumps(prov, ensure_ascii=False) + "\n")
    print("SAVED", out_dir, flush=True)
    print("SMOKE_TRAIN_DONE", flush=True)


if __name__ == "__main__":
    main()
