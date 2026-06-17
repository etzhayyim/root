# bitsandbytes ROCm (HIP) build for gad / gfx1151

Reproducible recipe for the QLoRA 4-bit path on the EVO-X2 (gad). The PyPI
`bitsandbytes` wheel ships **no ROCm binary** — it detects `BNB_BACKEND=ROCm` then
looks for `libbitsandbytes_rocm83.so`, which isn't in the wheel — so it must be
compiled from source with the HIP backend. Murakumo-only (ADR-2605215000): built and
run on gad, no external/commercial GPU.

**Verified 2026-06-17**: the build compiles for `gfx1151` and a 4-bit GPU matmul
(`bitsandbytes.nn.Linear4bit` on `cuda`) produces finite output. The hard infra
blocker (no 4-bit on ROCm gfx1151) is cleared.

## Prereqs (already present on gad)
- ROCm 7.13 (`/opt/rocm`), `hipcc` (HIP 7.13), `cmake` 3.28, `git`
- the training venv `~/maxwell/venv-train` (torch 2.10+rocm7.13)
- GPU arch: `gfx1151` (Radeon 8060S, EVO-X2 APU)

## Build
```bash
cd ~/maxwell && rm -rf bnb-src
git clone --depth 1 --branch 0.49.2 https://github.com/bitsandbytes-foundation/bitsandbytes.git bnb-src
cd bnb-src
export ROCM_PATH=/opt/rocm PATH=/opt/rocm/bin:$PATH
cmake -DCOMPUTE_BACKEND=hip -DBNB_ROCM_ARCH="gfx1151" -S . -B .
make -j8                       # → bitsandbytes/libbitsandbytes_rocm713.so
~/maxwell/venv-train/bin/pip install .
```

## CRITICAL post-step — name fix
`pip install .` re-bundles the wheel's prebuilt `.so`s (cuda*, rocm62–72) and drops
the freshly-built one, while the runtime expects `libbitsandbytes_rocm83.so` (bnb's
version map yields `rocm83` for ROCm 7.13). Copy the built binary into place under
the expected name:
```bash
cp ~/maxwell/bnb-src/bitsandbytes/libbitsandbytes_rocm713.so \
   ~/maxwell/venv-train/lib/python3.12/site-packages/bitsandbytes/libbitsandbytes_rocm83.so
```
This must be redone if the venv reinstalls bitsandbytes.

## Verify
```bash
HSA_OVERRIDE_GFX_VERSION=11.5.1 ~/maxwell/venv-train/bin/python -c \
"import torch,bitsandbytes as bnb; from bitsandbytes.nn import Linear4bit; \
 l=Linear4bit(2048,2048,bias=False,compute_dtype=torch.float16).to('cuda'); \
 print('4bit OK', tuple(l(torch.randn(4,2048,device='cuda',dtype=torch.float16)).shape))"
# → 4bit OK (4, 2048)
```

## Known ceiling — loading the 25B DiffusionGemma 4-bit (ADR-2606171100)
The 4-bit *kernel* works, but loading `google/diffusiongemma-26B-A4B-it` (25.2B) 4-bit
on gad's **32 GB usable VRAM** currently fails two ways:
- `device_map={"":0}` (all-GPU): **OOM at the load-materialization peak** — the final
  4-bit resident size (~30 GB) would fit, but transformers materializes each fp16 shard
  on-device before quantizing, peaking ~1 GB over the limit (`expandable_segments:True`
  did not save enough).
- `device_map="auto"` / CPU-offload (`llm_int8_enable_fp32_cpu_offload=True`): hits the
  **`diffusion_gemma` accelerate meta-tensor bug** (empty `hf_device_map`, generate
  fails: "Tensor on device cuda:0 is not on the expected device meta!").

### Unlocks (operator / one-time)
1. **VRAM headroom (the clean fix)** — the EVO-X2 has ~94 GB unified; raise the UMA
   framebuffer (BIOS) or GTT (`amdgpu.gttsize` / `ttm.pages_limit` kernel params) so
   >32 GB is GPU-usable → the all-GPU 4-bit load then fits with margin (and so does
   QLoRA training + the >1100 tok/s thesis).
2. **Pre-quantized checkpoint** — quantize once on CPU (proven to load there) and
   `save_pretrained` a 4-bit checkpoint, then load *that* (shards already 4-bit, ~1–2 GB
   each → no fp16 materialization peak). Avoids the OOM without a VRAM bump.
3. **Upstream**: fix the `diffusion_gemma` accelerate dispatch so `device_map` offload
   materializes (would enable the CPU-tail path).

Until one of these lands, maxwell-diffusion inference/SFT runs **CPU bf16** on gad
(verified: base bench 12/15=80%, train smoke loss 1.07→0.04); `available:false` stands.
