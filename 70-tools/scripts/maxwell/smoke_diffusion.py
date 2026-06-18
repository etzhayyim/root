"""maxwell-diffusion base 動作検証 — load google/diffusiongemma-26B-A4B-it on gad
(EVO-X2 gfx1151 ROCm) and run real block-diffusion generation. Proves the diffusion
base RUNS on the fleet (ADR-2606171100 D3). Murakumo-only: gad, no commercial GPU /
no external inference API (ADR-2605215000).

Modes:
  (default)  CPU bf16 — verified working (52GB in ~58GB RAM); slow (2-10 tok/s).
  --4bit     GPU NF4 via bitsandbytes (built for gfx1151, BNB-ROCM-BUILD.md). The
             4-bit MATMUL is verified; the full 25.2B model load needs >32GB usable
             VRAM (raise the EVO-X2 UMA framebuffer — see BNB-ROCM-BUILD.md). Run:
               PYTORCH_HIP_ALLOC_CONF=expandable_segments:True \
               HSA_OVERRIDE_GFX_VERSION=11.5.1 HF_HUB_OFFLINE=1 \
               venv-train/bin/python smoke_diffusion.py --4bit
"""
import argparse
import os
import time

import torch
from transformers import AutoProcessor, DiffusionGemmaForBlockDiffusion

MID = "google/diffusiongemma-26B-A4B-it"

ap = argparse.ArgumentParser()
ap.add_argument("--4bit", dest="fourbit", action="store_true",
                help="GPU NF4 via bitsandbytes (needs >32GB usable VRAM; else CPU bf16)")
ap.add_argument("--max-new-tokens", type=int, default=128)
args = ap.parse_args()

print(f"torch {torch.__version__} | cuda?={torch.cuda.is_available()} "
      f"| {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'} "
      f"| mode={'4bit-GPU' if args.fourbit else 'bf16-CPU'}", flush=True)
proc = AutoProcessor.from_pretrained(MID)

t0 = time.time()
if args.fourbit:
    # GPU NF4. bitsandbytes built for ROCm/HIP gfx1151 (BNB-ROCM-BUILD.md); 4-bit
    # matmul verified. device_map={"":0} keeps the whole model on GPU (no accelerate
    # auto-infer → avoids the diffusion_gemma meta-tensor bug). Needs the 4-bit
    # resident (~30GB) + load peak to fit usable VRAM → raise the UMA framebuffer.
    from transformers import BitsAndBytesConfig
    qc = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model = DiffusionGemmaForBlockDiffusion.from_pretrained(MID, quantization_config=qc, device_map={"": 0})
    print(f"4-bit GPU load {time.time()-t0:.0f}s | VRAM {torch.cuda.memory_allocated()/1e9:.1f}GB", flush=True)
else:
    os.environ.setdefault("OMP_NUM_THREADS", "16")
    torch.set_num_threads(16)
    model = DiffusionGemmaForBlockDiffusion.from_pretrained(MID, dtype=torch.bfloat16)
    print(f"CPU bf16 load {time.time()-t0:.0f}s | meta:{next(model.parameters()).is_meta}", flush=True)
model.eval()

PROMPTS = [
    "Why is the sky blue? Answer in one sentence.",
    "Convert this Python function to idiomatic Clojure:\n\ndef add(a, b):\n    return a + b",
]

for p in PROMPTS:
    ii = proc.apply_chat_template(
        [{"role": "user", "content": p}], tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt",
    ).to(model.device)
    in_len = ii["input_ids"].shape[-1]
    t = time.time()
    with torch.no_grad():
        out = model.generate(**ii, max_new_tokens=args.max_new_tokens)
    dt = time.time() - t
    seq = getattr(out, "sequences", out)
    if not hasattr(seq, "shape"):
        seq = next(v for v in vars(out).values() if hasattr(v, "shape"))
    ntok = seq.shape[-1] - in_len
    txt = proc.decode(seq[0][in_len:], skip_special_tokens=True)
    print("=" * 64, flush=True)
    print("PROMPT :", p.replace("\n", " ⏎ "), flush=True)
    print("OUTPUT :", txt.strip()[:700], flush=True)
    print(f"[gen {ntok} tok in {dt:.1f}s = {ntok/max(dt,1e-9):.1f} tok/s]", flush=True)

print("SMOKE_DONE", flush=True)
