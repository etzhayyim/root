"""Real loss landscape of maxwell-1 (Gemma 4 E4B + M1-r2 LoRA adapter) — Li et al. 2018
filter-normalized 2-direction sweep over the ACTUAL trained weights, plus the real
gradient norm at θ*. Murakumo-only: runs on gad. Emits a JSON grid to render locally."""
import json, pathlib, sys, time
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "google/gemma-4-E4B-it"
ADAPTER = str(pathlib.Path.home() / "maxwell" / "out" / "m1-r1")
CORPUS = pathlib.Path.home() / "maxwell" / "corpus.jsonl"
G    = int(sys.argv[1]) if len(sys.argv) > 1 else 13     # grid GxG
SPAN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8  # alpha,beta in [-SPAN,SPAN]
NB   = int(sys.argv[3]) if len(sys.argv) > 3 else 6      # eval rows per grid point
torch.manual_seed(0)

print(f"loading {BASE} + adapter (E4B, bf16, GPU)...", flush=True)
tok = AutoTokenizer.from_pretrained(ADAPTER)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map={"": 0})
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()

# LoRA params = the trained subspace θ*
lora = {n: p for n, p in model.named_parameters() if "lora_" in n}
print(f"LoRA tensors: {len(lora)} | params: {sum(p.numel() for p in lora.values())/1e6:.2f}M", flush=True)
theta = {n: p.detach().clone() for n, p in lora.items()}

# two filter-normalized random directions (per-tensor norm matched to θ*)
def fnorm_dir():
    d = {}
    for n, p in theta.items():
        r = torch.randn_like(p)
        d[n] = r * (p.norm() / (r.norm() + 1e-12))
    return d
d1, d2 = fnorm_dir(), fnorm_dir()

# eval batch: first NB corpus rows → chat text → tokens (full-seq LM loss)
rows = [json.loads(l) for l in open(CORPUS) if l.strip()][:NB]
batches = []
for ex in rows:
    msgs = ex["messages"]
    text = tok.apply_chat_template(msgs, tokenize=False)
    enc = tok(text, return_tensors="pt", truncation=True, max_length=1024).to("cuda")
    batches.append(enc)

@torch.no_grad()
def mean_loss():
    tot = 0.0
    for enc in batches:
        ids = enc["input_ids"]
        out = model(input_ids=ids, attention_mask=enc["attention_mask"], labels=ids)
        tot += out.loss.item()
    return tot / len(batches)

def set_theta(a, b):
    with torch.no_grad():
        for n, p in lora.items():
            p.copy_(theta[n] + a * d1[n] + b * d2[n])

# real gradient norm at θ* (one batch, backward)
set_theta(0, 0)
for p in lora.values():
    p.requires_grad_(True)
model.zero_grad()
e0 = batches[0]
loss0 = model(input_ids=e0["input_ids"], attention_mask=e0["attention_mask"], labels=e0["input_ids"]).loss
loss0.backward()
gnorm = float(torch.sqrt(sum((p.grad.detach() ** 2).sum() for p in lora.values() if p.grad is not None)))
for p in lora.values():
    p.requires_grad_(False)
model.zero_grad()
print(f"‖∇L‖ at θ* = {gnorm:.4f} | L(θ*) = {loss0.item():.4f}", flush=True)

# sweep the grid
axis = np.linspace(-SPAN, SPAN, G)
Z = np.zeros((G, G))
t0 = time.time()
for i, a in enumerate(axis):
    for j, b in enumerate(axis):
        set_theta(a, b)
        Z[i, j] = mean_loss()
    print(f"row {i+1}/{G}  ({time.time()-t0:.0f}s)", flush=True)
set_theta(0, 0)  # restore θ*

out = pathlib.Path.home() / "maxwell" / "loss_landscape.json"
out.write_text(json.dumps({
    "model": "maxwell-1 (Gemma4 E4B + M1-r2 LoRA)", "G": G, "span": SPAN, "eval_rows": NB,
    "axis": axis.tolist(), "Z": Z.tolist(),
    "grad_norm": gnorm, "loss_center": float(loss0.item()),
    "method": "Li et al. 2018 filter-normalized 2-direction loss landscape",
}))
print("WROTE", out, "| Z range", float(Z.min()), float(Z.max()), flush=True)
print("LANDSCAPE_DONE", flush=True)
