---
id: adr-2605253000-mac-mini-m4-16gb-gemma4-26b-moe-disk-inference
title: "Mac mini M4 16GB で Gemma 4 26B-A4B MoE を NVMe disk inference で動作確認"
status: accepted
doc_type: adr
topic: murakumo-fleet-inference
authoritative: true
authoritative_for:
  - mac-mini-m4-fleet-gemma4-26b-moe-disk-inference
  - tb5-ssd-speedup-prediction-disk-bound-llm-inference
last_verified: 2026-05-25
related:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605231300-baien-distill-react-loop
  - adr-2605250400-gemma-coder-distill-rocm
depends_on:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
---

# ADR-2605253000: Mac mini M4 16GB で Gemma 4 26B-A4B MoE を NVMe disk inference で動作確認

# Context

baien edge-target (ADR-2605241900) は WASM-32 / iPhone 12+ / Android 4GB の trunk
≤4B BitNet 1.58 が constitutional invariant。一方で Murakumo fleet 内には EVO-X2
ROCm + Mac mini M4 16GB が含まれ、後者は 16GB という RAM 制約で 26B 級モデルを
"動かせない" と従来扱われていた。

2026-05-25 セッションで `gemma-4-26B-A4B-it` (Gemma 4 26B-A4B MoE: 25.2B total /
3.8B active / 128 experts / 8 active + 1 shared / 256K context / 30 layers) を
ターゲットに **NVMe disk inference** が実用域に到達するかの empirical 検証を実施。
背景仮説:

1. **MoE × mmap シナジー** — 1 token あたり 8/128 expert + shared のみが触れられ
   る → working set が dense モデル比 ~15% → mmap page cache hit rate が高い
2. **Apple NVMe sequential read 3.1 GB/s** + macOS unified memory mmap 実装 → モデル
   サイズ > RAM でも disk paging で実行可能 (Apple "LLM in a Flash" ICLR 2026
   論文の経験的裏付け)
3. **llama.cpp default mmap** + Q3_K_M 量子化 (12 GB on disk; Metal
   `recommendedMaxWorkingSetSize = 12.7 GB` ギリギリ)

# Decision

**accepted** — Mac mini M4 16GB で Gemma 4 26B-A4B MoE を NVMe disk inference で
8.4 tok/s 生成可能と確認。以下を fleet 運用上の reference として固定する:

## §1. 動作確認構成 (SSoT)

```
モデル:   gemma-4-26B-A4B-it-UD-Q3_K_M.gguf  (12 GB on disk, Unsloth Dynamic)
ホスト:   Mac mini M4 (base, 16GB unified memory, 10-GPU-core)
ランタイム: llama.cpp b9290 + ggml 0.12.0 (Homebrew)
ダウンロード元: huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF

起動オプション (動作確認済み non-interactive):
  llama-cli -m gemma-4-26B-A4B-it-UD-Q3_K_M.gguf \
    -ngl 0 -c 2048 -fa 1 -ctk q8_0 -ctv q8_0 -t 4 \
    -no-cnv -st --simple-io < /dev/null \
    -p "<prompt>"
```

## §2. 計測結果 (2026-05-25T20:00 JST 計測)

| 指標 | 値 | 備考 |
|---|---|---|
| Generation throughput | **8.4 tok/s** | MoE 8/128 active expert × mmap page hit |
| Prompt eval | 3.5 tok/s | 50 tok = 14 sec |
| First-token latency (cold) | ~80 sec | 初回 mmap 全 expert page-fault |
| Wall time (50 prompt + ~150 gen) | 113 sec | |
| Peak RSS | 8.5 GB | 12 GB モデルの ~70% resident |
| Peak memory footprint | 7.2 GB | |
| Page faults | 2.3M | mmap disk paging 想定どおり |
| Swaps | 0 | idle wait を起こさない場合 |

## §3. Constitutional 適合性

- ✅ ADR-2605215000 §1 (Murakumo-only inference): Mac mini M4 は Murakumo fleet
  ノード — `gemma3:4b` 既存 placement と同じ inference SSoT
- ✅ ADR-2605241900 (baien edge-target): 本 ADR は **baien carve-out 外** = Mac mini
  fleet 内専用の inference 経路追加であり、iPhone/Android/WASM-32 edge target を
  汚染しない (baien トランクは依然 ≤4B BitNet 1.58 固定)
- ✅ ADR-2605215000 §2 (no commercial GPU rental): NVMe + 内蔵 mmap のみで完結

## §4. 失敗経路 (再現性のため記録)

1. **Metal full offload `-ngl 99`** → `failed to decode prompt batch, res = -3`
   (12.7 GB Metal working set 超過; 12 GB モデル + KV cache + compute scratch)
2. **Metal partial `-ngl 4..16`** → 同じく `res = -3` (gemma4 MoE expert tensor
   は Metal/CPU split が効かない; weight router が GPU-side で完結する設計)
3. **`--no-conversation` 単独** → gemma4 chat template が conversation mode を
   自動発動し対話プロンプト `>` 待ちで 57 分 idle。CPU 92.8% (warmup) → idle。
   - 修正: `-no-cnv -st --simple-io < /dev/null` 3 点セットが必須

## §5. 外付け Thunderbolt 5 SSD への速度予測

### §5.1 律速分析

現状 8.4 tok/s = 119 ms/token の内訳推定:

- **Compute (M4 4 P-core × ~200 GFLOPS FP16 ≈ 800 GFLOPS)**
  - 1 token あたり 3.8B active × 2 FMA = 7.6 GFLOPs
  - = 9.5 ms / token (compute alone, 圧縮解凍コスト除く)
  - = 理論上限 **~105 tok/s**
- **Disk read (内蔵 NVMe ~3.1 GB/s sequential, ~1.5 GB/s for base 256GB 版)**
  - 残り 110 ms / token = 全体の **92% が disk-bound**
  - ↑ mmap page fault による random/4K read が主体 (sequential ではない)

→ **本構成は明確に disk-bound**。Compute は余裕。

### §5.2 TB5 SSD upgrade 予測

| 項目 | 内蔵 NVMe | TB5 SSD (理論) | TB5 SSD (現実) |
|---|---|---|---|
| プロトコル帯域 | PCIe 4.0 x4 (8 GB/s) | TB5 80 Gbps (10 GB/s) | TB5 80 Gbps |
| Sequential read | 3.1 GB/s (512GB+) | 10 GB/s | **6.0-6.4 GB/s** (OWC Envoy Ultra / Acasis TBU401E 等) |
| 4K random read IOPS | ~700k | — | ~600-900k |
| Disk time / tok | ~110 ms | ~55 ms | ~55-70 ms |
| Total time / tok | 119 ms | 64.5 ms | 64.5-79.5 ms |
| **予測 tok/s** | **8.4** | **~15.5** | **12.5-15.5** |

→ **予想 1.5-1.85× 高速化** = **12.5-15.5 tok/s 生成**

### §5.3 注意事項

- **First-token latency も短縮** (~80 sec → ~40-50 sec); 初回 cold-load は
  ほぼ sequential read 律速
- **Random 4K IOPS は内蔵 Apple SSD と TB5 SSD で大差ない** → 帯域より IOPS
  律速の場合は速度向上が小さい (1.3-1.5× 程度に留まる可能性)
- **熱問題**: 113 sec で全 expert を mmap 経由で fault-in する間、外付け SSD
  の thermal throttling が起きると性能劣化 → ヒートシンク付き enclosure 推奨
- **電源**: TB5 enclosure は Mac mini M4 から bus-power 取得; 同時に CPU 全力
  使用 → 5 W 程度の追加電力 (M4 全体 ~30 W 上限の問題なし)

## §6. 推奨運用

- ✅ **対話用途 (READ-mostly chat)**: 内蔵で十分。8.4 tok/s は人間の読み速度
  (5-7 tok/s) より速い
- ✅ **長文生成 (200-2000 tok)**: TB5 SSD で 12.5-15.5 tok/s なら実用域上昇
- ⚠️ **コード生成 / Agent ループ**: EVO-X2 fleet `gemma3:4b` (より高速) と
  speculative decoding 等で組合せたほうがよい — `gemma-4-26B-A4B` を draft 用に
  使うのは無意味 (重すぎ); 逆方向 (draft = `gemma3:4b`, target = `gemma-4-26B-A4B`
  on Mac mini) は将来の検討課題
- ❌ **バッチ並列**: Mac mini M4 16GB では同時 2 streams で swap 発火必至

## §7. 派生課題 (separate ADR で扱う)

1. **TB5 SSD 実機検証** — 推奨候補: OWC Envoy Ultra (TB5, 6 GB/s claim) or
   Acasis TBU401E + WD SN850X 2TB
2. **Speculative decoding** — draft = `gemma3:4b` (EVO-X2 LAN serve) / target =
   `gemma-4-26B-A4B` (Mac mini M4 local) の Murakumo 2-node 構成
3. **Mac mini M4 fleet placement** — Murakumo fleet.toml に `gemma-4-26B-A4B-it`
   を追加 (現状は EVO-X2 judah 1 ノードのみ; Mac mini M4 でも serve 可能と判明)
4. **Context extension** — `-c 4096` で動作するが peak RSS 11.7 GB に到達; ctx
   8K 以上は QAT 量子化された KV cache か再 mmap 戦略が要検討

# Consequences

## Positive

- Mac mini M4 16GB が **26B 級 MoE モデルの実用 inference node** として
  認定 — Murakumo fleet 内推論キャパが事実上拡張
- `gemma3:4b` (4B) → `gemma-4-26B-A4B` (3.8B active / 25.2B total) 移行で **品質
  ジャンプ確保** without 新規ハード投資 (内蔵 NVMe で動く範囲)
- baien constitutional invariant 完全保持 (本 ADR は fleet-side 経路のみ)
- TB5 SSD 投資の ROI 数値根拠が確立 — 1.5-1.85× 高速化 = ~5-10万円投資で
  対話用途の応答性大幅改善

## Negative / Risks

- Cold-start 80 sec — chat UI ではプリウォーム必須
- ctx >2048 で peak RSS が 16GB に接近 → swap thrashing risk (idle wait や
  並列 query で発火)
- Apple NVMe write endurance — disk inference 自体は **read only** で wear 無し
  だが、swap が起きると別問題 (前回 57 分 idle で 942k swapouts 観測)
- ADR-2605215000 §4 で fleet.toml が SSoT — 本 ADR で Mac mini M4 への
  `gemma-4-26B-A4B` 配置を確定するなら fleet.toml 更新が follow-up で必要

## Out of Scope

- 内蔵 vs TB5 SSD の実機 A/B 計測 (TB5 SSD は手元になし; §7.1 で別 ADR)
- Mac mini M4 fleet 全台でのモデル serve (現状は 1 台での feasibility 確認のみ)
- 他モデル (Qwen3.5-35B-A3B / Llama 4 100B-MoE 等) への一般化

# Alternatives Considered

- **Metal full offload** — 失敗 (§4.1)
- **Metal partial offload** — 失敗 (§4.2)
- **Q4_K_M 量子化** (16.9 GB) — 12.7 GB Metal cap 超過 + 内蔵 mmap 範囲超過
  リスク (前回セッションで承認した Q3_K_M に固定)
- **IQ2_XXS 9.92 GB** — 量子化劣化が大きく品質試験なしで採用不可
- **MLX バックエンド** — ml-explore/mlx Issue #3393 (gemma4 MoE bug on base M4
  10-core GPU) のため対象外
- **disable mmap (`--no-mmap`)** — 12 GB を anonymous RAM に丸ごとロード →
  16GB Mac mini で OOM 確実

# References

- ADR-2605215000 (Murakumo-only inference, no commercial GPU rental)
- ADR-2605241900 (baien edge-target invariant — 本 ADR とは別経路)
- ADR-2605231300 (e7m bench distill — LangGraph ReAct distillation)
- ADR-2605250400 (gemma-coder-distill — EVO-X2 ROCm peft+trl)
- Apple "LLM in a Flash: Efficient Large Language Model Inference with Limited
  Memory" (ICLR 2026) — flash-paged inference theory
- ml-explore/mlx Issue #3393 (gemma4 MoE bug on base M4 10-core GPU)
- 50-infra/murakumo/fleet.toml (placement SSoT)
- 90-docs/baien/distilled-models.jsonl (Mac mini fleet model registry)
