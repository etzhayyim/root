"""maxwell-diffusion base 動作検証 — load google/diffusiongemma-26B-A4B-it on gad
(EVO-X2 gfx1151 ROCm, ~94GB unified mem via device_map="auto") and run real
block-diffusion generation. This proves the diffusion base RUNS on the fleet —
the prerequisite for maxwell-diffusion-1 (ADR-2606171100 D3). Murakumo-only:
runs on gad, no commercial GPU / no external inference API (ADR-2605215000).
"""
import time
import torch
from transformers import DiffusionGemmaForBlockDiffusion, AutoProcessor

MID = "google/diffusiongemma-26B-A4B-it"

print(f"torch {torch.__version__} | cuda?={torch.cuda.is_available()} "
      f"| {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}", flush=True)
print("loading processor...", flush=True)
proc = AutoProcessor.from_pretrained(MID)

print("loading model (DiffusionGemmaForBlockDiffusion, bf16, CPU)...", flush=True)
# 52GB bf16 > 34GB VRAM, and device_map="auto" leaves this model class on META
# tensors (accelerate dispatch no-ops here even with _no_split_modules set).
# 52GB fits in the ~58GB available CPU RAM, so load plain on CPU (non-meta path,
# no accelerate) and run block-diffusion on CPU. Slower, but it actually RUNS.
import os
os.environ.setdefault("OMP_NUM_THREADS", "16")
torch.set_num_threads(16)
t0 = time.time()
model = DiffusionGemmaForBlockDiffusion.from_pretrained(MID, dtype=torch.bfloat16)
model.eval()
print(f"model device: {next(model.parameters()).device} | is_meta: {next(model.parameters()).is_meta}", flush=True)
print(f"loaded in {time.time()-t0:.0f}s", flush=True)

PROMPTS = [
    "Why is the sky blue? Answer in one sentence.",
    "Convert this Python function to idiomatic Clojure:\n\ndef add(a, b):\n    return a + b",
]

for p in PROMPTS:
    msg = [{"role": "user", "content": p}]
    ii = proc.apply_chat_template(
        msg, tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt",
    ).to(model.device)
    in_len = ii["input_ids"].shape[-1]
    t = time.time()
    with torch.no_grad():
        out = model.generate(**ii, max_new_tokens=128)
    dt = time.time() - t
    seq = getattr(out, "sequences", out)          # DiffusionGemmaGenerationOutput -> .sequences
    if not hasattr(seq, "shape"):                  # fall back to first tensor-like attr
        seq = next(v for v in vars(out).values() if hasattr(v, "shape"))
    ntok = seq.shape[-1] - in_len
    txt = proc.decode(seq[0][in_len:], skip_special_tokens=True)
    print("=" * 64, flush=True)
    print("PROMPT :", p.replace("\n", " ⏎ "), flush=True)
    print("OUTPUT :", txt.strip()[:700], flush=True)
    print(f"[gen {ntok} tok in {dt:.1f}s = {ntok/max(dt,1e-9):.1f} tok/s]", flush=True)

print("SMOKE_DONE", flush=True)
