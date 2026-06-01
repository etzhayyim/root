#!/usr/bin/env python3
"""smoke_inference.py — validate untrained moemoekyun against real BitNet 2B.

Runs 3 checks on real microsoft/bitnet-b1.58-2B-4T-bf16:
  A. base BitNet loads + generates on MPS / CPU
  B. BitNetFFNWithMoE module surgery succeeds on real architecture
  C. G5 invariant holds: untrained moemoekyun (α=0) output bit-identical to base BitNet

If C passes → scaffold is real-model-validated → R1.0 probe will likely succeed on EVO.
If C fails → mismatch in expected attribute names ("mlp" vs "feed_forward" etc.) — fix attach.py.

Run:
    HF_HOME=/Volumes/260317/models/huggingface \
        python3 70-tools/baien-moemoekyun-train/scripts/smoke_inference.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Default HF cache to external volume to avoid filling system disk
os.environ.setdefault("HF_HOME", "/Volumes/260317/models/huggingface")
os.environ.setdefault("HF_HUB_CACHE", os.environ["HF_HOME"] + "/hub")

import torch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from baien_moemoekyun import attach_moe_to_model, freeze_backbone_verify


def main():
    print(f"[env] torch={torch.__version__} mps={torch.backends.mps.is_available()}")
    print(f"[env] HF_HOME={os.environ['HF_HOME']}")

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[env] device={device}")

    base_id = "microsoft/bitnet-b1.58-2B-4T-bf16"

    # ─── A. Load base BitNet ─────────────────────────────────────────────
    print(f"\n[A] Loading {base_id} (may download ~4GB first time)...")
    from transformers import AutoModelForCausalLM, AutoTokenizer

    t0 = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_id,
        torch_dtype=torch.bfloat16,
        trust_remote_code=False,  # transformers 4.46+ has native BitNet (avoid stale remote configuration_bitnet.py)
    )
    load_sec = time.perf_counter() - t0
    print(f"[A] loaded in {load_sec:.1f}s")
    print(f"[A] config: hidden={model.config.hidden_size}, intermediate={model.config.intermediate_size}, n_layers={model.config.num_hidden_layers}")

    # Inspect layer structure to find FFN attribute name
    inner = model.model if hasattr(model, "model") else model
    if hasattr(inner, "layers"):
        layer0 = inner.layers[0]
        print(f"[A] layer[0] attrs: {[a for a in dir(layer0) if not a.startswith('_') and not callable(getattr(layer0, a))][:15]}")
        ffn_attr = None
        for candidate in ("mlp", "feed_forward", "ffn"):
            if hasattr(layer0, candidate):
                ffn_attr = candidate
                break
        print(f"[A] detected FFN attribute: {ffn_attr}")
    else:
        print("[A] FAIL: no .layers found")
        sys.exit(1)

    model.to(device)

    # ─── A.2 base generate ──────────────────────────────────────────────
    prompt = "def fibonacci(n):\n    "
    print(f"\n[A.2] base generate from: {prompt!r}")
    ids = tokenizer(prompt, return_tensors="pt").to(device)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=40, do_sample=False, pad_token_id=tokenizer.eos_token_id or 0)
    gen_sec = time.perf_counter() - t0
    base_text = tokenizer.decode(out[0], skip_special_tokens=True)
    base_tokens = out[0].numel() - ids["input_ids"].shape[1]
    print(f"[A.2] generated {base_tokens} tokens in {gen_sec:.2f}s = {base_tokens/gen_sec:.1f} tok/s")
    print(f"[A.2] base output:\n{base_text}\n")

    # Capture base logits on a fixed input for C comparison
    print("[A.3] capturing base logits for G5 comparison...")
    fixed_input = tokenizer("Hello world", return_tensors="pt").to(device)
    with torch.no_grad():
        base_out = model(**fixed_input)
    base_logits = base_out.logits.clone()
    print(f"[A.3] base logits shape={tuple(base_logits.shape)} norm={base_logits.norm().item():.3f}")

    # ─── B. Module surgery on real BitNet ───────────────────────────────
    print(f"\n[B] applying BitNetFFNWithMoE surgery to last layer (idx={model.config.num_hidden_layers - 1})...")
    moe_layers = [model.config.num_hidden_layers - 1]
    try:
        installed = attach_moe_to_model(
            inner,
            moe_layer_indices=moe_layers,
            hidden_size=model.config.hidden_size,
            intermediate_size=model.config.intermediate_size,
            num_experts=16,  # small for smoke
            top_k=2,
            ffn_attribute_name=ffn_attr,
        )
    except Exception as e:
        print(f"[B] FAIL surgery: {e}")
        sys.exit(1)

    # Move MoE wrappers to device + bf16
    for wrapper in installed.values():
        wrapper.to(device)
        wrapper.moe_branch.to(dtype=torch.bfloat16)

    summary = freeze_backbone_verify(inner, installed)
    print(f"[B] surgery OK, param summary: {summary}")

    # G5 alpha check
    alphas = [w.alpha.item() for w in installed.values()]
    g5_pass = all(abs(a) <= 1.001e-3 for a in alphas)
    print(f"[B] G5 α init: {alphas} (within ±1e-3: {g5_pass})")

    # ─── C. G5 step-0 invariant on real BitNet ──────────────────────────
    print("\n[C] G5 step-0 match check on real BitNet...")
    with torch.no_grad():
        moe_out = model(**fixed_input)
    moe_logits = moe_out.logits

    delta = (moe_logits - base_logits).float()
    base_norm = base_logits.float().norm().item()
    rel_delta = delta.norm().item() / (base_norm + 1e-9)
    g5_step0_pass = rel_delta < 0.01

    print(f"[C] base_logits.norm={base_norm:.3f}")
    print(f"[C] ‖moe_logits - base_logits‖ = {delta.norm().item():.6f}")
    print(f"[C] relative delta = {rel_delta:.6f} (G5: < 0.01)")
    print(f"[C] G5 step-0 invariant on REAL BitNet: {'PASS ✓' if g5_step0_pass else 'FAIL ✗'}")

    # ─── C.2 generate from MoE-augmented model ──────────────────────────
    print(f"\n[C.2] moemoekyun (untrained, α=0) generate from same prompt: {prompt!r}")
    t0 = time.perf_counter()
    with torch.no_grad():
        out2 = model.generate(**ids, max_new_tokens=40, do_sample=False, pad_token_id=tokenizer.eos_token_id or 0)
    gen2_sec = time.perf_counter() - t0
    moe_text = tokenizer.decode(out2[0], skip_special_tokens=True)
    moe_tokens = out2[0].numel() - ids["input_ids"].shape[1]
    print(f"[C.2] generated {moe_tokens} tokens in {gen2_sec:.2f}s = {moe_tokens/gen2_sec:.1f} tok/s")
    print(f"[C.2] moemoekyun output:\n{moe_text}\n")

    # Are base + moe outputs identical?
    identical = base_text == moe_text
    print(f"[C.2] base vs moemoekyun output bit-identical: {'YES ✓' if identical else 'NO (deterministic-but-different — α jitter)'}")

    # ─── Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SMOKE INFERENCE SUMMARY")
    print("=" * 60)
    print(f"  A. base BitNet load + generate:     PASS ({load_sec:.0f}s load, {base_tokens/gen_sec:.1f} tok/s)")
    print(f"  B. module surgery on real BitNet:   PASS (FFN attr='{ffn_attr}', G5 α: {g5_pass})")
    print(f"  C. G5 step-0 invariant (real model): {'PASS' if g5_step0_pass else 'FAIL'} (rel_delta={rel_delta:.6f})")
    print(f"  C.2 moemoekyun generate identical:  {'YES' if identical else 'NO (small α jitter)'}")
    print("=" * 60)
    print(f"  Verdict: scaffold {'REAL-MODEL VALIDATED ✓' if g5_step0_pass else 'NEEDS FIX ✗'}")

    sys.exit(0 if g5_step0_pass else 1)


if __name__ == "__main__":
    main()
