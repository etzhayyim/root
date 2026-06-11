#!/usr/bin/env python3
"""Reference inference for BitNet b1.58 2B 4T bf16 master via transformers
(ADR 2605092350). Used to compare against bitnet.cpp i2_s output.

CPU-only, fp32 (MPS does not support bf16). Disables torch.dynamo /
torch.compile because BitNet's quantized linears trip the inductor
compile path on Apple Silicon and hang at ~0% CPU."""

import json
import os
import sys
import time

import torch
torch._dynamo.config.disable = True
os.environ["TORCH_COMPILE_DISABLE"] = "1"

from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

MODEL_DIR = os.environ.get(
    "BAIEN_BF16_DIR", os.path.expanduser("~/.cache/baien/models/BitNet-b1.58-2B-4T-bf16")
)
PROMPT = sys.argv[1] if len(sys.argv) > 1 else "The capital of France is"
N_NEW = int(sys.argv[2]) if len(sys.argv) > 2 else 32

torch.manual_seed(20260510)
torch.set_num_threads(8)

print(f"[bf16-ref] loading {MODEL_DIR}", flush=True)
t0 = time.time()
tok = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=True)
mdl = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    dtype=torch.float32,
    device_map={"": "cpu"},
    trust_remote_code=False,
    low_cpu_mem_usage=True,
)
mdl.eval()
load_sec = time.time() - t0
print(f"[bf16-ref] load: {load_sec:.2f}s on cpu fp32", flush=True)

inputs = tok(PROMPT, return_tensors="pt").to("cpu")
print(f"[bf16-ref] generating up to {N_NEW} tokens (greedy)…", flush=True)

t1 = time.time()
with torch.no_grad():
    out = mdl.generate(
        **inputs,
        max_new_tokens=N_NEW,
        do_sample=False,
        temperature=None,
        top_p=None,
        use_cache=True,
    )
gen_sec = time.time() - t1
text = tok.decode(out[0], skip_special_tokens=True)
n_new_actual = out.shape[1] - inputs["input_ids"].shape[1]

result = {
    "prompt": PROMPT,
    "n_new": int(n_new_actual),
    "load_seconds": round(load_sec, 4),
    "generate_seconds": round(gen_sec, 4),
    "tok_per_sec": round(n_new_actual / gen_sec, 3) if gen_sec > 0 else None,
    "completion": text[len(PROMPT):],
    "full_text": text,
}
print(json.dumps(result, indent=2, ensure_ascii=False))
