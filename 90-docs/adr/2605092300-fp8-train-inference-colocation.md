---
id: adr-2605092300-fp8-train-inference-colocation
title: "FP8 Train+Inference Colocation on Ada/Hopper — Single Pod Time-Share"
status: active
doc_type: adr
topic: fp8-train-inference-colocation
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - FP8 format conventions (E4M3 fwd / E5M2 bwd)
  - per-tensor scaling + master weight policy
  - KV cache FP8 + NCCL config
  - train/inference time-share scheduling on RunPod 6000 Ada
priority: 9.0
axis: hardware-runtime
weight: 0.9
priority_note: "Hardware-level invariant. Train + Inference share the same pod (盆栽は同じ場所で育つ)."
depends_on:
  - adr-2605010000
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605092200-continuous-metabolic-training
related:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605092100-lora-per-cell-moe-expert-cohort-fission
supersedes: []
superseded_by: []
---

# Context

ADR-2605010000 で RunPod 6000 Ada を LLM SSoT とした。FP8 native 演算
(1457 TFLOPS, Transformer Engine) を活用し、訓練と推論を **同一 pod 上で時分割** する。
これにより inference 中の activation を即座に SGD step に流す
"learn-while-think" が可能になる。

# Decision

## A. Format Conventions

| 用途 | dtype | 備考 |
|---|---|---|
| Forward activation / weight | E4M3 (1.5.2 bias=7) | 動的 range 狭, 精度高 |
| Backward gradient | E5M2 (1.5.2 bias=15) | 動的 range 広, 精度低 |
| Optimizer master weight | BF16 (cell adapter) / FP32 (trunk) | NV TE 標準 |
| Optimizer momentum/variance | FP32 (trunk) / BF16 (adapter) | |
| KV cache | E4M3 | per-channel scale |
| Embedding (vertex_organism_embedding) | E4M3 + per-row scale | 1 byte/dim |
| Inter-GPU all-reduce | NCCL FP8 (Hopper) / BF16 (Ada) | Ada は NCCL FP8 未成熟 |
| Loss scaling | per-tensor dynamic | TE auto-scale |

## B. Train/Inference Time-Share

- 単一 pod に **vLLM-FP8 (inference)** と **TE-FP8 trainer** を共駐
- scheduler:
  - inference is **default occupant** — latency SLA を保つ
  - SGD step は inference の queue が空いた micro-window (1ms+) で fire
  - LoRA adapter swap (HotSwap) は GPU memory 上で direct
- trunk_W はメモリ常駐 (read-only), Δ は active cell 分のみ swap-in
- batch size: inference は dynamic (1〜N), train は micro-batch (1〜32, gradient accumulation)

## C. KV Cache Policy

- FP8 E4M3 per-channel scale (Hopper FlashAttention-3 / Ada FlashAttention-2 + manual cast)
- cohort 内で **共有可能**: 同じ trunk_W + 似た context のとき複数 cell が KV を共用
- TTL = active reasoning thread 終了で flush (LangGraph thread end)

## D. NCCL / Comm

- Hopper (H100/H200): NCCL FP8 collective, GPU-to-GPU NVLink で OK
- Ada (RTX 6000 Ada): NCCL FP8 は flaky なので all-reduce は BF16 cast → FP8 store
- multi-pod: gradient compression (powerSGD or 1-bit) optional, default は無し

## E. Memory Budget (RTX 6000 Ada 48GB)

| 項目 | サイズ |
|---|---|
| trunk_W (7B FP8) | ~7 GB |
| KV cache (8K context, 32 concurrent) | ~12 GB |
| activations + workspace | ~10 GB |
| active LoRA adapters (× 1000 hot, ~10 MB each) | ~10 GB |
| optimizer states (active cells, BF16 master) | ~5 GB |
| margin | ~4 GB |

cold cell adapter は B2 / IPFS に offload, swap-in latency ~50ms。

## F. Inference Path

```
MCP request → granian L3 (ADR-2605080600)
  → dispatcher 解析 → cohort_did 決定
  → vLLM-FP8 invoke with trunk_W + active Δ
  → activation cache → 戻り値 + train signal hook
```

`learn-while-think`: 各 forward の output が `edge_gradient_flow` の dst として
即座に書込まれ、reward_sign が確定すれば同 pod の trainer が SGD 実行。

## G. Stability Guards

- NaN detection: per-tensor scale tracker が 4 step 連続 overflow なら BF16 fallback
- Drift gate: 1 hour 単位で adapter checkpoint diff の L2 norm を計測, 閾値超で hold
- Floor gate (ADR-2605081300): forward 結果が floor 違反予測ならば inference reject + train signal 抑制

# Consequences

## Positive
- inference + train ループが ms 単位で閉じる
- FP8 ネイティブで TFLOPS 2-3x (BF16 比), VRAM 半減
- learn-while-think が natural

## Negative
- FP8 stability tuning に学習曲線 (per-tensor scale 設計など)
- Ada の NCCL FP8 不成熟で BF16 cast オーバーヘッド
- inference latency と train fairness の co-tuning

## Reversibility
runtime 設定なので reversible。format 変更 (FP8 → BF16) は LoRA adapter 一時 dequant で対応可。

# Alternatives Considered

- **train pod を別建て**: rejected。signal latency が増え、learn-while-think 不可
- **BF16 統一**: rejected。FLOPS / VRAM コストで FP8 採用が必然
- **INT8 PTQ**: rejected。online learning と quant aware training の interleave が不安定

# References

- ADR-2605010000 RunPod 6000 Ada
- ADR-2605092000 vector substrate
- ADR-2605092200 continuous training
- NV TE FP8: arXiv:2209.05433
- vLLM FP8: vllm/quantization docs
