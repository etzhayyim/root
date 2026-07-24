---
id: tool-nvme-disk-inference
title: "nvme-disk-inference — Murakumo fleet disk-paged MoE inference substrate"
status: proposed
doc_type: reference
topic: murakumo-fleet-inference
authoritative: true
authoritative_for:
  - murakumo-disk-inference-bench-harness
  - disk-storage-tier-selection-for-moe-inference
last_verified: 2026-05-25
related:
  - adr-2605253015-nvme-disk-inference-substrate-project
  - adr-2605253000-mac-mini-m4-16gb-gemma4-26b-moe-disk-inference
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605241900-baien-edge-target-invariant
---

# nvme-disk-inference

Murakumo fleet で **RAM 越えサイズの MoE モデル** を NVMe/USB SSD disk paging で
serve するための substrate + bench harness。

## なぜこの project が存在するか

Mac mini M4 16GB が **25.2B param Gemma 4 26B-A4B MoE** を steady-state 7.7-8.4 tok/s で
動かせると判明 (ADR-2605253000)。さらに 2026-05-25 の A/B 検証で **USB 3.2 Gen 2
(836 MB/s) と内蔵 NVMe (2.3 GB/s) の差が generation tok/s でほぼゼロ** (+3%) と
empirical に確認。

これは MoE × mmap の経済性が disk bandwidth に依存しないことを意味し、religious-corp
fleet 内で **既存 fleet ハードのまま inference capability を拡張可能** な現実解になる。

本 project はその methodology を:

1. **再現可能 bench harness** として scaffold (本 dir)
2. **constitutional 適合** として固定 (ADR-2605215000 Murakumo-only / ADR-2605241900
   baien edge-target 不汚染)
3. **storage tier 選択 SoT** として deps.toml に登録

## Scope (R0)

- ✅ MoE モデルの disk inference (Gemma 4 26B-A4B が reference)
- ✅ Mac mini M4 fleet placement
- ✅ A/B bench harness (storage tier 比較)
- ✅ cold-cache flush ツール
- ❌ dense モデル (Llama 3.1 70B 等) — working set 大、disk paging 適さず R1+
- ❌ TB5/TB4 enclosure 実機検証 (hardware 購入後 R1)
- ❌ Murakumo fleet 自動配置 (cell-runner integration R2)
- ❌ Speculative decoding (draft=gemma3:4b / target=gemma-4-26B-A4B) R3

## Reference: 動作確認済構成

```
モデル:    gemma-4-26B-A4B-it-UD-Q3_K_M.gguf (12.73 GB, Unsloth Dynamic)
ホスト:    Mac mini M4 base (16GB unified memory, 10-GPU-core)
ランタイム: llama.cpp b9290 + ggml 0.12.0

llama-cli -m <model> \
  -ngl 0 -c 2048 -fa 1 -ctk q8_0 -ctv q8_0 -t 4 \
  -no-cnv -st --simple-io < /dev/null \
  -p "<prompt>"
```

### Empirical 計測 (2026-05-25)

| Storage tier | Raw read | Gen tok/s | Wall (200 tok) | Peak RSS |
|---|---|---|---|---|
| 内蔵 AP0256Z 256GB NVMe | 2.30 GB/s | 7.7 | 119 sec | 10.3 GB |
| SanDisk Extreme USB 3.2 Gen 2 (0x781:0x55BB) | 0.84 GB/s | 7.9 | 128 sec | 10.0 GB |

→ **steady-state generation は storage 独立**、cold-load (first token) のみ ~7% 差。

### なぜ storage 独立になるか — 5 層 root cause

予測モデル: `per-token = compute (9.5 ms) + disk (active 1.5 GB / bandwidth)` → 内蔵で 120 ms、TB5 で 64.5 ms。
実測: SanDisk 0.84 GB/s で 7.9 tok/s → **per-token disk read = 98 MB** (予測 1.5 GB の 1/15)。

| 層 | 機序 | per-token disk demand |
|---|---|---:|
| Naive (予測) | 全 active param read | 1.5 GB |
| L1: MoE sparsity (9/128 active) | × 0.07 | 105 MB |
| L2: Router routing stability (隣接 token 相関) | × 0.12 | 13 MB |
| L3: macOS page cache (~10 GB hot expert resident) | × 0.15 | **2 MB** |
| L4: Compute is actual bottleneck (50-75 ms ≠ 9.5 ms) | — | 律速側変わる |
| L5: Kernel readahead で disk-compute overlap | — | 実効 0-2 MB |

→ 7.9 tok/s × 13 MB worst-case = **103 MB/s** demand = USB 3.2 Gen 2 (836 MB/s) の 12% / 内蔵 NVMe (2300 MB/s) の 4% → どちらも余裕、bandwidth 律速ではない。
→ **真の律速 = compute 50-75 ms/token** (storage-tier 独立)。

### 適用範囲

| Workload | 本 finding | 理由 |
|---|---|---|
| MoE active ratio ≤10% (Gemma 4 / Qwen3.5-A3B / Mixtral / GPT-OSS) | ✅ 適用 | 本 mechanism |
| MoE active ratio 20-50% (DeepSeek-V2) | △ 半減 | sparsity 効果 |
| Dense モデル (Llama 3.1 70B etc.) | ❌ 非適用 | 全 param touched, cache 不可能 |
| Long-context (ctx ≥16K) | ❌ 非適用 | KV cache が page cache 侵食 |
| Multi-stream 並列 | ❌ 非適用 | cache 共有競合 |

## Bench Harness

`scripts/bench-storage-tier.sh`:

```bash
./scripts/bench-storage-tier.sh \
  --model gemma-4-26B-A4B-it-UD-Q3_K_M.gguf \
  --tier-a /Volumes/SanDisk/models \
  --tier-b /Users/$USER/Models \
  --prompt "Mac mini M4 16GB で 26B MoE モデルを動かす最大の制約を 3 行で。" \
  --output results/
```

3-stage protocol:
1. **Cache flush** — 14 GB junk file write+read to evict tier-A model from page cache
2. **Cold bench** — llama-cli with `time -l` (wall + RSS + page faults + swaps)
3. **Symmetric for tier-B** — same flush, same prompt

Outputs:
- `results/{tier}-{date}.txt` (full llama-cli + time output)
- `results/{tier}-{date}.json` (parsed perf summary; future: feed to e7m bench)

## Storage Tier Selection Guide

| Use case | Recommended tier | Reasoning |
|---|---|---|
| First-token-latency-critical (interactive chat) | TB5 NVMe (要 M4 Pro) or TB4 NVMe | cold-load 半減 |
| Throughput-only (batch generation) | 内蔵 NVMe OR USB 3.2 Gen 2 | 同等 (差 +3%) |
| 容量倉庫 (複数 GGUF) | SanDisk Extreme / 安価 USB SSD | コスト最重要 |
| Long-running 24/7 fleet member | 内蔵 NVMe + USB SSD swap 退避 | wear 保護 |

## Constitutional 適合

- ✅ **ADR-2605215000** Murakumo-only inference: Mac mini fleet ノード内完結、no
  commercial GPU rental (RunPod / Vertex AI / etc.)
- ✅ **ADR-2605241900** baien edge-target: 本 substrate は **fleet-side のみ**、
  iPhone/Android/WASM-32 トランクは依然 ≤4B BitNet 1.58 固定
- ✅ **ADR-2605172000** kotoba substrate boundary: 本 project は inference 経路の
  追加であり、storage / payment / identity boundary に変更なし

## Roadmap

- **R0 (current)**: scaffold + reference doc + bench harness
- **R1 (TB4 enclosure 入手後)**: TB4 NVMe single + ×2 並列 A/B 計測
- **R2 (TB5 enclosure 入手後 + M4 Pro)**: TB5 single + cross-tier 総合比較
- **R3 (speculative decoding)**: draft=`gemma3:4b`@EVO-X2 / target=`gemma-4-26B-A4B`@Mac
- **R4 (Murakumo cell-runner integration)**: fleet.toml に disk-inference node tag 追加

## Files

| Path | Purpose |
|---|---|
| `README.md` | this file |
| `scripts/bench-storage-tier.sh` | A/B bench protocol (cache flush + cold run × 2 tier) |
| `scripts/cache-flush.sh` | 14 GB junk file evict standalone |
| `bench/llama-cli-flags.txt` | reference invocation (`-no-cnv -st --simple-io <`) |
| `results/` | empirical bench output (gitignored except baseline) |
| `results/baseline-260525.md` | 初回 internal vs SanDisk 計測 markdown |
