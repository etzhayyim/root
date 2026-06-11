---
id: runbook-bitnet-cpp-evo-x2-build
title: "Build Microsoft bitnet.cpp on EVO-X2 (Ubuntu, AMD Radeon 8060S gfx1151, ROCm 6.2)"
status: active
doc_type: how-to
topic: bitnet-cpp-build
authoritative: true
last_verified: 2026-05-24
related:
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605242100-baien-server-xl-carve-out
  - 70-tools/etzhayyim-cli/bench.go
---

# Build Microsoft bitnet.cpp on EVO-X2

**Audience**: etzhayyim operator with SSH access to EVO-X2
(`gad@192.168.1.22` per current Murakumo LAN).

**Estimated time**: ~40 minutes total
(clone 5 min + deps 10 min + build 15 min + quantize 5 min + smoke 5 min).

**Operator attendance**: required. The build is **operator-attended**
— VS Build Tools / cmake interactive prompts may appear; sudo prompts
will fire during apt installs.

# Prerequisites

- SSH to EVO-X2 confirmed:
  ```bash
  ssh gad@192.168.1.22 uname -a
  ```
  Expect: `Linux ... x86_64 GNU/Linux`.
- ROCm 6.2 installed and verified:
  ```bash
  rocminfo | grep -i gfx1151        # expect 1 match
  rocm-smi                          # expect AMD Radeon Graphics in list
  ```
- Disk free: **≥ 10 GB on `/`** (model + build artifacts).
- Time budget: **~40 min uninterrupted**. Operator must approve sudo
  and any interactive prompts.

# Step 1 — System dependencies

```bash
sudo apt update
sudo apt install -y build-essential cmake ninja-build python3-pip \
                    python3-venv git libnuma-dev
```

# Step 2 — ROCm verification

```bash
rocminfo | grep gfx1151
rocm-smi
```

If `rocminfo` returns no match for `gfx1151` or `rocm-smi` does not
list the Radeon 8060S, **STOP** and re-install ROCm per AMD docs
before proceeding. The bitnet.cpp build will technically succeed on
CPU-only, but the operator's expected speedup numbers below assume
the ROCm path is available for the experimental `-DGGML_HIPBLAS=ON`
variant.

# Step 3 — Clone bitnet.cpp

```bash
cd ~
git clone https://github.com/microsoft/BitNet.git bitnet
cd bitnet
```

# Step 4 — Python venv + transformers pin

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pip install transformers==4.49.0
```

The transformers pin to `4.49.0` is required per upstream BitNet README
to avoid breaking changes in later transformers releases (the BitNet
model loader is sensitive to the model_type registration API).

# Step 5 — Build bitnet.cpp

Standard CPU build:

```bash
cmake -S . -B build -GNinja -DCMAKE_BUILD_TYPE=Release \
      -DBITNET_X86_TL2=ON
cmake --build build -j$(nproc)
```

Expected output: `build/bin/llama-cli` binary.

If experimental ROCm dispatch is desired:

```bash
cmake -S . -B build -GNinja -DCMAKE_BUILD_TYPE=Release \
      -DBITNET_X86_TL2=ON \
      -DGGML_HIPBLAS=ON -DAMDGPU_TARGETS=gfx1151
cmake --build build -j$(nproc)
```

Note: BitLinear CPU-side ops may dominate even with ROCm dispatch
enabled. Benchmark both paths (Step 7) and choose per workload.

# Step 6 — Quantize 2B-4T weights

Download the upstream Microsoft checkpoint (MIT licensed):

```bash
huggingface-cli download microsoft/BitNet-b1.58-2B-4T
```

Convert to bitnet.cpp's TL2 (table lookup, 2-bit packed) format:

```bash
python convert.py \
    --model-path ~/.cache/huggingface/hub/models--microsoft--BitNet-b1.58-2B-4T \
    --outfile ~/baien-bitnet-cpp-2b.gguf \
    --outtype tl2
```

Expected output: `~/baien-bitnet-cpp-2b.gguf` (~800 MB).

# Step 7 — Smoke test

```bash
./build/bin/llama-cli -m ~/baien-bitnet-cpp-2b.gguf -p "Hello, world." -n 32 -t 8
```

Expect coherent completion in < 5 sec.

Run the 15-prompt microbench:

```bash
bash 70-tools/scripts/bench/baien-microbench/run-bitnet-cpp.sh \
    ~/baien-bitnet-cpp-2b.gguf
```

(The `run-bitnet-cpp.sh` script ships in a follow-up PR alongside this
runbook; until then run microbench manually by feeding the 15 prompts
to `llama-cli`.)

# Step 8 — Wire into `e7m bench`

Add a `bitnet-cpp` backend choice in `70-tools/etzhayyim-cli/bench.go`
alongside the existing `transformers-gpu` / `transformers-cpu` cases.

Environment:

```bash
export BAIEN_BITNET_CPP_BIN=~/bitnet/build/bin/llama-cli
export BAIEN_BITNET_CPP_MODEL=~/baien-bitnet-cpp-2b.gguf
```

The backend dispatch is a parallel switch arm — same prompt
formatting, same scoring path, just a different binary invocation.

# Expected speedup

The bitnet.cpp packed TL2 kernel is roughly **2-4× faster** than
`transformers` bf16 on the same EVO-X2 CPU path for short
generations. GPU dispatch on `gfx1151` is experimental: official
upstream BitNet ROCm support targets MI-class accelerators, not
RDNA3/RDNA3.5 consumer iGPUs as of 2026-05.

**The stable target is CPU TL2.** GPU dispatch is for experimentation
only; results may regress on batched workloads.

# Rollback

```bash
rm -rf ~/bitnet ~/baien-bitnet-cpp-2b.gguf
unset BAIEN_BITNET_CPP_BIN BAIEN_BITNET_CPP_MODEL
```

# Known caveats

- **BitLinear CPU dispatch**: probe showed ~7× speedup on isolated
  generate calls but only ~1.2× on batched bench. Workload-dependent;
  CPU-side ops dominate for batched paths.
- **gfx1151 ROCm support**: experimental. May require
  `export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1` to satisfy
  AOTriton's gating. Capture full kernel logs on first run.
- **Charter Rider compliance**: bitnet.cpp source is MIT (compatible
  with Apache-2.0 + Charter Rider, since the Rider applies to first-party
  output not third-party source). The Microsoft `BitNet-b1.58-2B-4T`
  weights are MIT-licensed. Neither falls under any Charter Rider §2
  prohibited category.

# References

- ADR-2605241900 — baien edge-target invariant (bitnet.cpp serves edge
  benchmarking by establishing a reproducible 2 B reference latency)
- ADR-2605215000 — etzhayyim inference Murakumo-only (EVO-X2 is a
  Murakumo fleet member; running bitnet.cpp on EVO-X2 is compliant)
- ADR-2605242100 — baien-server / baien-XL carve-out (bitnet.cpp can
  also bench server-tier variants when wired through this runbook)
- Microsoft BitNet: https://github.com/microsoft/BitNet
- BitNet-b1.58-2B-4T model card: https://huggingface.co/microsoft/BitNet-b1.58-2B-4T
- ROCm 6.2 docs: https://rocm.docs.amd.com/en/docs-6.2.0/
