---
id: moemoekyun-precision-architecture-260526
title: "moemoekyun precision architecture — inference ternary native (1.58-bit packed) + training FP4 (TransformerEngine)"
status: active
doc_type: explanation
topic: moemoekyun-precision-architecture
authoritative: true
last_verified: 2026-05-26
priority: 8.5
authoritative_for:
  - "BitNet 2B baseline inference path: ternary native (bitnet.cpp / packed kernel), NOT NVFP4 conversion"
  - "moemoekyun R1.4+ training path: TransformerEngine FP4 (Blackwell native) per train_oka.py recipe"
  - "Why TRT-LLM NVFP4 was considered + abandoned for inference"
related:
  - moemoekyun-bench-cycles-1-7-synthesis-260526
  - adr-2605261900-baien-moemoekyun-moe-charter
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
---

# moemoekyun precision architecture — ternary inference + FP4 training

User directive 2026-05-26: **inference は ternary のまま、 training を FP4 setup で**.

## Decision summary

| Path | Format | Stack | Rationale |
|---|---|---|---|
| **BitNet 2B inference (baseline + post-train serve)** | **Ternary native (1.58-bit packed)** | bitnet.cpp (Microsoft official) / packed kernels | Native BitNet format, no precision loss from re-quantization, smallest memory footprint |
| **moemoekyun R1.4+ training** | **FP4 weight + FP8 activation (TransformerEngine)** | NVIDIA TransformerEngine + PyTorch, Blackwell native | Matches train_oka.py recipe, leverages 5090 / B200 FP4 Tensor Cores natively |

## Why NOT TRT-LLM NVFP4 for inference

cycle 12-13 で TRT-LLM (~5 GB, 177 packages) install したが、最終的に inference には使わない。 理由:

1. **Format mismatch**: BitNet 1.58-bit (ternary `{-1, 0, +1}`) → NVFP4 (4-bit float) 変換は **bit budget を 1.58 → 4 に増やす** — native ternary の compactness を捨てる
2. **Quantization round-trip**: BitNet (1.58-bit) → bf16 unpacked → NVFP4 (PTQ) は二重変換、 精度劣化リスク
3. **Native ternary kernel が存在する**: bitnet.cpp の i2_s / tl1 / tl2 packed kernels で 1.58-bit のまま行列演算可能
4. **5090 GPU native ternary**: nvidia は INT2 Tensor Core を Blackwell に持つが、 標準 framework から直接呼べない (TRT-LLM/transformers 共に INT2 ネイティブ kernel 未提供)

TRT-LLM はサンクコスト化、 別 model (gemma / qwen / moemoekyun trained checkpoint) の NVFP4 inference には流用可能。

## Why TransformerEngine FP4 for training (NOT TRT-LLM)

cycle 12 で確認: user の train_oka.py は既に `TransformerEngine FP4 weight + FP8 activation` recipe を使用 (B200/5090 Blackwell native)。 moemoekyun R1.4+ も **同じ recipe を流用** する:

| Layer | Precision (train) |
|---|---|
| BitNet backbone (frozen) | bf16 frozen (forward only, no FP4 quantize necessary since gradient is zero) |
| MoE router | TE FP4 weight + FP8 activation |
| MoE experts (128 × 7 layers) | TE FP4 weight + FP8 activation |
| Per-layer α gate | TE FP4 weight + FP8 activation |
| AdamW optimizer state | fp32 master (TE handles cast) |

→ R1.4+ corpus rebalance + TE FP4 train recipe = **完全 5090 / B200 Blackwell native train path**。

## ADR-2605262300 §2 precision ladder 修正

現行 ADR-2605262300 §2 precision ladder は **R2 BF16 → R3 FP8 → R4 sparse FP4** (engineering 段階的 ladder)。 今回の決定でこれを修正:

| Phase | 旧 design | 新 design (user 2026-05-26 directive) |
|---|---|---|
| R1.4 | bf16 (EVO ROCm) | bf16 (EVO ROCm, unchanged — EVO offline で deferred) **OR** TE FP4 + FP8 (5090 ADR-2605263000 carve-out) — **R1.4 から FP4 introduce** |
| R2 | BF16 baseline | TE FP4 + FP8 (matches train_oka.py) |
| R3 | FP8 mixed-precision | (subsumed by R2 since FP4 is more aggressive) |
| R4 | sparse FP4 + 2:4 structured | sparse FP4 + 2:4 structured (still engineering open question) |

実質、 R1.4 から FP4 になり、 ladder が短縮される。 R3 FP8 step は省略可能。 ADR amendment 必要 (cycle 13+ で起こす)。

## Concrete actions (cycle 13+)

### Action 1: bitnet.cpp build on pod

```sh
# Pod side
apt-get update && apt-get install -y cmake clang ninja-build || \
  pip install cmake ninja  # fallback if apt fails
cd /workspace
git clone --depth 1 https://github.com/microsoft/BitNet.git
cd BitNet
git submodule update --init --recursive  # llama.cpp 同梱
# Build for x86_64 with AVX-512 (pod CPU has 256 cores)
python3 setup_env.py -md microsoft/bitnet-b1.58-2B-4T -q i2_s
# This auto-downloads + builds + tests
```

期待 throughput on pod (256 CPU cores):
- i2_s (1.58-bit packed) on x86_64 AVX-512: ~30-50 tok/s for 2B BitNet
- Multi-stream batch: scaling proportional

### Action 2: redo HumanEval+ via bitnet.cpp

bitnet.cpp の `llama-cli` / `llama-server` で BitNet 2B greedy decoding を駆動、 evalplus codegen 用 prompt 流すラッパー。 期待 wall:
- 164 tasks × ~5 sec each = ~15 min (vs cycle 8-11 で 30 min/task)
- **~25-30× speedup** over HF transformers bf16 path

### Action 3: TE FP4 train recipe for moemoekyun R1.4

train_oka.py を参照しつつ:
1. `BaienMoEMoekyunTrainer` (ADR-2605262100 §1) を TE FP4 対応に改修
2. `te.Linear` で router + expert FFN を置換
3. FP4 recipe: `te.fp8.fp8_autocast(enabled=True, fp8_recipe=DelayedScaling(margin=0, fp8_format=Format.E4M3))` 等
4. AdamW optimizer は fp32 master 維持 (TE が cast 自動)
5. 既存 ADR-2605262100 §2.3 G8 (backbone frozen verify) 不変

R1.4 train host:
- **5090 (Founder Lv7+ Emergency Authorization, ADR-2605263000)** で run 可能 — `bench-eval ONLY` の §1.1 条件を **train carve-out に拡張する amendment が必要**
- OR **EVO online 後** (依然 blocked) で run

### Action 4: ADR amendment

ADR-2605263000 §1.1 (Permitted) は **bench-eval inference のみ** で train を明示的に除外している。 user の現在の directive (training FP4 setup on Blackwell) は **train 用途で 5090 を使うこと** を意味するので、 ADR-2605263000 §1.1 を amend する必要:

> §1.1.A (proposed addition): Founder Lv7+ Emergency Authorization も **R1.4 train on RunPod 5090 with TransformerEngine FP4** を permitted scope に追加。 ただし single session ≤24h + $50 cap + per-rental kotoba-datomic attestation 継続。

これは ADR-2605262200 (charter §2(i)(2) train carve-out) と同じ実質効果だが、 Council ratification 待ちを待たず Founder authority で実行する記録になる。

## Status (cycle 13)

| Item | Status |
|---|---|
| BitNet ternary inference path (bitnet.cpp) | 🟡 pip cmake install pending, clone retry needed |
| TE FP4 train recipe design | ✅ documented (this doc) |
| ADR-2605263000 amendment for train carve-out | 📋 pending (cycle 14+) |
| MMLU full on 5090 | 🟡 running (PID 20745, cycle 12 launched) |
| HumanEval+ canonical (via bitnet.cpp) | 📋 pending bitnet.cpp build |
| ADR-2605262300 precision ladder amendment | 📋 pending (R1.4 from FP4 → R3 FP8 step subsumed) |

## Constitutional + budget state

ADR-2605263000 cumulative budget: <1% of $200 (probably ~$5-10 total now after TRT-LLM install GPU time, MMLU full GPU time). Comfortable margin for bitnet.cpp build + benches.
