"""One row of the quant-training shootout. Run as subprocess.

Stdin: JSON {quant, base, n_rows, n_steps, dataset_id, out_dir}
Stdout: progress logs
Exit:   writes out_dir/row-<quant>.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

import torch  # noqa: E402

try:
    import torch._dynamo as _dyn
    _dyn.config.suppress_errors = True
    _dyn.disable()
except Exception:
    pass


def _gb(n_bytes: int) -> float:
    return round(n_bytes / 1024 ** 3, 3)


def _load_examples(dataset_id: str, n_rows: int) -> list[dict[str, str]]:
    """Load N rows from a HF dataset. Uses the same parser as baien-distill
    for qwen-text format (lordx64/reasoning-distill-opus-4-7-max-sft)."""
    from baien_distill.adapters.hf_dataset import (
        DATASET_REGISTRY, load_examples,
    )
    flat = {}
    for cat, specs in DATASET_REGISTRY.items():
        for s in specs:
            flat.setdefault(s.id, (cat, s))
    hit = flat.get(dataset_id)
    if hit is None:
        raise RuntimeError(f"dataset {dataset_id} not in DATASET_REGISTRY")
    category, spec = hit
    examples = list(load_examples(spec, category, limit=n_rows))
    return [{"prompt": ex.prompt, "response": ex.response} for ex in examples]


def _apply_quant(model, quant: str) -> dict:
    """Mutate `model` in-place per `quant`. Return {quantize_sec, model_gb}."""
    t0 = time.time()
    n_params = sum(p.numel() for p in model.parameters())

    if quant == "bf16":
        # baseline; model already loaded in bf16
        pass

    elif quant == "bonsai-sign-1bit":
        # roso stub — in-place sign(W)*mean(|W|) on every nn.Linear
        from torch import nn
        with torch.no_grad():
            for _, child in model.named_modules():
                if isinstance(child, nn.Linear):
                    W = child.weight.data
                    scale = W.abs().mean()
                    child.weight.data.copy_(torch.sign(W) * scale)

    elif quant.startswith("quanto-"):
        from optimum.quanto import quantize as q_quantize, freeze, qint8, qint4, qint2
        dtype_map = {"quanto-int8": qint8, "quanto-int4": qint4, "quanto-int2": qint2}
        dt = dtype_map[quant]
        q_quantize(model, weights=dt)
        freeze(model)

    else:
        raise NotImplementedError(f"quant={quant} not supported in this script")

    quantize_sec = round(time.time() - t0, 2)

    # Measure model size on device
    model_bytes = 0
    for p in model.parameters():
        model_bytes += p.numel() * p.element_size()
    # quanto packs weights into special tensors; approximate with element_size
    model_gb = _gb(model_bytes)

    return {"quantize_sec": quantize_sec, "n_params": n_params, "model_gb": model_gb}


def run(quant: str, base: str, n_rows: int, n_steps: int,
        dataset_id: str, out_dir: Path) -> dict:
    print(f"[row {quant}] load base = {base}", flush=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[row {quant}] device = {device}", flush=True)

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(base)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16,
                                                 device_map=device)
    n_param_total = sum(p.numel() for p in model.parameters())
    print(f"[row {quant}] params = {n_param_total:,}", flush=True)

    qmeta = _apply_quant(model, quant)
    print(f"[row {quant}] quantize done in {qmeta['quantize_sec']}s "
          f"-> model_gb={qmeta['model_gb']}", flush=True)

    # LoRA on top
    from peft import LoraConfig, get_peft_model
    lora_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                          target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                          task_type="CAUSAL_LM", bias="none")
    model = get_peft_model(model, lora_cfg)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[row {quant}] trainable = {trainable:,}", flush=True)

    # Build dataset
    rows = _load_examples(dataset_id, n_rows)
    print(f"[row {quant}] loaded {len(rows)} examples", flush=True)

    from datasets import Dataset

    def _format(ex):
        if getattr(tok, "chat_template", None):
            p = tok.apply_chat_template(
                [{"role": "user", "content": ex["prompt"]}],
                tokenize=False, add_generation_prompt=True,
            )
        else:
            p = f"<|user|>\n{ex['prompt']}\n<|assistant|>\n"
        return {"prompt": p, "completion": ex["response"]}

    ds = Dataset.from_list(rows).map(_format)

    from trl import SFTConfig, SFTTrainer  # type: ignore
    sft = SFTConfig(
        output_dir=str(out_dir / f"sft-{quant}"),
        max_steps=n_steps,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_steps=0,
        lr_scheduler_type="constant",
        bf16=True,
        use_cpu=not torch.cuda.is_available(),
        logging_steps=1,
        save_strategy="no",
        report_to=[],
        packing=False,
    )
    trainer = SFTTrainer(
        model=model, args=sft, train_dataset=ds, processing_class=tok,
    )

    # Reset peak memory tracker
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    # Manual per-step timing via callback
    step_times: list[float] = []

    from transformers import TrainerCallback

    class StepTimer(TrainerCallback):
        def on_step_begin(self, args, state, control, **kw):
            self._t0 = time.time()

        def on_step_end(self, args, state, control, **kw):
            step_times.append(time.time() - self._t0)

    trainer.add_callback(StepTimer())

    print(f"[row {quant}] starting trainer.train (max_steps={n_steps})", flush=True)
    t0 = time.time()
    result = trainer.train()
    train_wall = round(time.time() - t0, 2)
    final_loss = float(getattr(result, "training_loss", float("nan")))

    peak_vram_gb = (_gb(torch.cuda.max_memory_allocated())
                    if torch.cuda.is_available() else None)

    # Warm avg = mean of steps[1:] (drop step 0 = cold)
    if len(step_times) >= 2:
        warm = sum(step_times[1:]) / max(1, len(step_times) - 1)
    elif step_times:
        warm = step_times[0]
    else:
        warm = None
    cold = step_times[0] if step_times else None

    row = {
        "quant": quant,
        "status": "ok",
        "device": device,
        "n_params": qmeta["n_params"],
        "trainable_params": trainable,
        "quantize_sec": qmeta["quantize_sec"],
        "model_gb": qmeta["model_gb"],
        "step_count": len(step_times),
        "step_cold_sec": round(cold, 2) if cold else None,
        "step_warm_sec": round(warm, 2) if warm else None,
        "train_wall_sec": train_wall,
        "peak_vram_gb": peak_vram_gb,
        "final_loss": round(final_loss, 4),
    }
    return row


def main():
    if len(sys.argv) < 2:
        print("usage: _one_row.py <json-payload>", file=sys.stderr)
        sys.exit(2)
    payload = json.loads(sys.argv[1])
    out_dir = Path(payload["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    quant = payload["quant"]
    try:
        row = run(quant=quant, base=payload["base"],
                  n_rows=payload["n_rows"], n_steps=payload["n_steps"],
                  dataset_id=payload["dataset_id"], out_dir=out_dir)
    except Exception as e:
        import traceback
        row = {"quant": quant, "status": "error",
               "error_type": type(e).__name__,
               "error_msg": str(e),
               "tb": traceback.format_exc()[-2000:]}
    (out_dir / f"row-{quant}.json").write_text(
        json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[row {quant}] DONE status={row.get('status')}", flush=True)


if __name__ == "__main__":
    main()
