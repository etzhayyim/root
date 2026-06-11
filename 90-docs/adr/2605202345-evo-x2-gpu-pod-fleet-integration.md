---
id: adr-2605202345-evo-x2-gpu-pod-fleet-integration
title: "ADR-2605202345: EVO-X2 GMKtec を Murakumo fleet の外部 GPU 推論ポッドとして統合"
status: proposed
doc_type: adr
topic: evo-x2-gpu-pod-fleet-integration
authoritative: true
last_verified: 2026-05-20
priority: 6.0
axis: infrastructure
weight: 0.55
priority_note: "Religious-corp ethics fallback + image/video pipeline 提供"
authoritative_for:
  - "External non-macOS GPU compute pod integration into Murakumo fleet"
  - "EthicsContentClassifierCell LLM fallback ルーティング"
depends_on:
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605202100-etzhayyim-kotodama-cell-runner-launchd
related:
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - 2605182312-local-bring-up-murakumo-gemma4
  - adr-2605192400-etzhayyim-eros-gore-council-judging
supersedes: []
superseded_by: []
---

# ADR-2605202345: EVO-X2 GMKtec を Murakumo fleet の外部 GPU 推論ポッドとして統合

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

ADR-2605192415 で religious-corp daemon architecture (Murakumo fleet) を 10 ノードの Mac mini で構成した。各ノードは `kotodama-cell-runner` を launchd 経由で起動し (ADR-2605202100)、Pregel cell を実行する。LLM 推論が必要な cell (EthicsContentClassifierCell 等) は **各ノードローカル の Ollama gemma3:4b** をフォールバックとして使う構成。

2026-05-20 に新規ハードウェア **GMKtec EVO-X2** を導入。仕様:
- CPU: AMD Ryzen AI Max+ 395 (16C/32T, Zen 5)
- GPU: Radeon 8060S iGPU (RDNA 3.5, gfx1151)
- NPU: AMD XDNA (50 TOPS)
- メモリ: 128 GB LPDDR5X-8000 unified (BIOS UMA 32 GiB を iGPU VRAM に割当、96 GB が system RAM)
- OS: Windows 11 Pro 24H2
- LAN IP: `192.168.1.70` (etzhayyim.lan セグメント)

同日に subagent 検証で以下を確認:

| 検証項目 | 結果 |
|---|---|
| Ollama 0.24 + ROCm gfx1151 backend | ✅ 動作 (Windows ネイティブ、WSL2 不要) |
| llama3.2:3b Q4_K_M inference | 83 tok/s |
| llama3.3:70b Q4_K_M inference | 1.18 tok/s (57% iGPU offload、UMA bound) |
| ComfyUI 0.21.1 portable AMD + PyTorch 2.9.1+rocm7.2.1 | ✅ 動作 |
| Animagine XL 4.0 (SDXL 1024², 25 steps) | 21 s/img, 1.20 it/s |
| WAI-Illustrious SDXL v160 (1024², 30 steps) | 25 s/img, 1.21 it/s |
| Wan 2.2 TI2V-5B 動画生成 (1280×704, 41 frames) | 8.4 min |
| LiteLLM 1.85 OpenAI-compatible proxy | ✅ port 4000 公開 |
| Windows Scheduled Task 永続化 | ✅ S4U principal、reboot 耐性確認 |

これにより EVO-X2 は (a) 70B クラス LLM、(b) SDXL/Wan 2.2 画像・動画生成 を提供できる単独 GPU マシンとして確立。Mac mini fleet にどう位置付けるかが本 ADR の決定事項。

# Decision

EVO-X2 を Murakumo fleet の **外部 GPU 推論ポッド** として登録する。具体:

## D1. fleet.toml に `[[inference_backends]]` 配列を新設

`[[nodes]]` (cell 実行 Mac mini ノード) とは別カテゴリで、非 macOS / 非 cell-runner マシンを推論バックエンドとして列挙する top-level セクションを追加。

```toml
[[inference_backends]]
name = "evo-x2"
host_lan = "192.168.1.70"
role = "gpu-inference-pod"
adr = "2605202345"

[inference_backends.evo-x2.hardware]
chip = "AMD Ryzen AI Max+ 395"
igpu = "Radeon 8060S (gfx1151, RDNA 3.5)"
npu = "AMD XDNA"
vram_gib = 32
sys_ram_gb = 96

[inference_backends.evo-x2.endpoints.ollama]
url = "http://192.168.1.70:11434"
api = "openai-compatible"
auth = "lan-only"
models = ["llama3.2:3b", "llama3.3:70b"]
backend = "ROCm gfx1151"

[inference_backends.evo-x2.endpoints.litellm]
url = "http://192.168.1.70:4000"
api = "openai-compatible"
auth = "bearer master_key (rotate per security policy)"

[inference_backends.evo-x2.endpoints.comfyui]
url = "http://192.168.1.70:8188"
api = "comfyui-native"
auth = "lan-only"
models = ["animagine-xl-4.0", "waiIllustriousSDXL_v160", "wan2.2_ti2v_5B_fp16"]
```

完全な追加案は本 ADR 末尾の付録 A 参照。

## D2. EVO-X2 は cell を実行しない

理由:
- `kotodama-cell-runner` は macOS launchd 前提 (ADR-2605202100)
- Windows で同等を再実装すると保守二重化
- WSL2 入れて Linux 版 cell-runner 動かすと WSL2 を維持する必要 — 別途 ROCm の iGPU サポートが WSL2 で限定的のため AI ワークロードのメリット薄い (ADR-内検証済)
- EVO-X2 の付加価値は **推論性能** であり cell 実行ではない

## D3. EthicsContentClassifierCell の LLM ルーティング更新

現状:
```toml
[cells.EthicsContentClassifierCell]
llm_primary = "claude-sonnet-4-6"
llm_fallback_local = "gemma3:4b (Murakumo Ollama)"
```

新規:
```toml
[cells.EthicsContentClassifierCell]
llm_primary = "claude-sonnet-4-6"
llm_fallback_local = "llama3.2:3b @ evo-x2 (84 tok/s)"
llm_fallback_local_secondary = "gemma3:4b (own-node Ollama)"
llm_heavy_review = "llama3.3:70b @ evo-x2 (1.18 tok/s, batch-only)"
```

EVO-X2 が unreachable な時は各 cell ノードのローカル gemma3:4b にフォールバック (現行動作維持)。

## D4. 画像/動画生成は cell 群に組み込まない (現段階)

ComfyUI/Wan 2.2 は religious-corp ガバナンス cell 群の関心外。当面は **ad-hoc API endpoint** として公開し、将来 LandStewardshipMonitoringCell の現地写真要約や AuditWitnessCell の証拠映像処理など具体ユースケースが出てから新 cell として ADR 起こす。

## D5. ネットワーク公開範囲 LAN-only

- ファイアウォール TCP 11434 / 4000 / 8188 inbound allow (LAN 内のみ到達可)
- 外部公開は将来 Tailscale + Caddy TLS 経由 (別 ADR)
- master_key は placeholder 状態。デプロイ前に `openssl rand -hex 32` で rotation 必須

## D6. Charter Rider 準拠範囲

EVO-X2 上で動かす religious-corp サービス (LiteLLM proxy の religious-corp 用 endpoint 等) は Apache 2.0 + Charter Compliance Rider v2.0 (ADR-2605192200) 適用範囲。Ollama / ComfyUI 本体は third-party 配布物のため NOTICE 維持のみで Rider 不適用 (CLAUDE.md "Do not add Charter Rider to 3rd-party vendored code" 準拠)。

## D7. Health check

Murakumo fleet の prometheus exporter に EVO-X2 を含める。最小チェック:
- `GET http://192.168.1.70:11434/v1/models` → 200 期待
- `GET http://192.168.1.70:4000/v1/models -H "Authorization: Bearer $KEY"` → 200 期待
- `GET http://192.168.1.70:8188/system_stats` → 200 + `pytorch_version` に "rocm" 文字列

# Consequences

## Positive
- **EthicsCell の信頼性向上**: ローカル gemma3:4b より高速で大規模な llama3.2:3b にアクセス可能、Claude Sonnet 4.6 が unreachable な場合の品質低下を緩和
- **画像/動画生成 capability の獲得**: Mac mini fleet に GPU 追加せず religious-corp 向け視覚処理が可能 (kuni-umi SiteSurvey/AuditWitness の将来拡張に有用)
- **70B クラス LLM**: 1.18 tok/s だが overnight batch / 重要レビュー用途では実用可能
- **ROCm Windows ネイティブ実証**: 本 ADR が ROCm 7.2 + gfx1151 Windows 動作の最初の公式記録 (HIP SDK 経由ではなく PyTorch + ComfyUI portable 経由で動作確認)

## Negative
- **単一障害点**: EVO-X2 down → llm_fallback_local の二次経路 (gemma3:4b ローカル) は機能維持するが、画像/動画は不可。冗長化には M3/M4 Ultra Mac mini など同等機 1 台追加が望ましい
- **Windows 運用負荷**: fleet は macOS で統一していたが Windows 機 1 台で混在。OS パッチ管理 / Windows Update 制御 / Scheduled Task メンテナンスの分岐が発生
- **70B 用途限定**: 1.18 tok/s は対話用途では実用不可。Q3 量子化変種 (~30 GB) or BIOS UMA 増設 (48-64 GiB) で改善余地あり、要追検証
- **master_key 平文管理**: placeholder 値 (`sk-evo-pod-master-key-CHANGE-ME`) が config に残る。デプロイ前 rotation + DPAPI 等で保護必須

## Open questions (本 ADR スコープ外、フォローアップ)
- **NPU (XDNA) を活用した推論パス → 未検証**。Subagent A は Ryzen AI SDK インストーラが GUI 必須なため SSH 単独で完遂不可と判定し停滞 (Python 3.10 のみ install して停止)。後続作業として:
  - cu_mac.py (Anthropic API + `computer_20250124` tool) で GUI installer 自動化
  - Ryzen AI SDK 1.5+ + VitisAIExecutionProvider + ResNet50 サンプル 推論成立確認
  - 結果は本 ADR の amendment または新 ADR (2605xxxxxx-evo-x2-npu-inference-routing) として追記
  - production-grade と判定されれば EthicsCell / 将来の force / phenotype 系で NPU offload ルート追加
- WSL2 + vLLM 構成の必要性 → 現状 Ollama で OpenAI 互換性十分。要求が出たら別 ADR
- Tailscale 経由 off-LAN 公開時の TLS 構成 → 別 ADR

# Alternatives Considered

## A1. EVO-X2 を `[[nodes]]` として fleet 統合 (12 tribes 命名拡張)

- 案: 11 番目の支族名 (gad / manasseh など) 付与し、WSL2 で kotodama-cell-runner 動かす
- 却下: WSL2 維持コスト + Linux 側 ROCm が iGPU 非対応で AI ワークロードの優位性消失。OS 統一性も崩れる

## A2. fleet 外部の独立リソース

- 案: EVO-X2 は fleet.toml に登録せず、別 ファイル (`50-infra/evo-x2/standalone.toml` 等) で管理
- 却下: cell からの discovery 機構が分散、monitoring も別実装になる。Murakumo prometheus に統合できない

## A3. 推論専用 mac mini (M4 Pro/Max) に置き換え

- 案: EVO-X2 売却 + Mac mini M4 Max 追加で OS 統一
- 却下: コスト 2-3 倍 / 90W TDP + 128 GB unified memory の cost-perf は EVO-X2 が優位 / ROCm gfx1151 動作確認済なら活用すべき

# References

- ADR-2605192415: Religious-Corp Daemon Architecture (Murakumo fleet 起源)
- ADR-2605202100: kotodama-cell-runner launchd 配備
- ADR-2605191346: No commercial K8s policy (本 ADR でも独自 control plane 維持)
- ADR-2605182312: 12-tribes 命名規約 (本 ADR は cell ノードではないので命名対象外)
- ADR-2605192400: Eros/Gore content classification policy (EthicsContentClassifierCell の理論的基盤)
- ADR-2605172300: Phenotype Agent (将来 SBT-bound LLM 推論に EVO-X2 利用可能性)
- ADR-2605192200: Charter Compliance Rider v2.0 (本マシン上 religious-corp service の license)
- ADR-2605192315: Transparent Religious Force (force-related cell が将来 70B 重量推論 を活用しうる)
- Subagent reports (2026-05-20 同日検証):
  - B: Ollama + ROCm benchmark
  - C: ComfyUI + Animagine XL 4.0 / WAI Illustrious v160 / Wan 2.2 TI2V-5B benchmark
  - D: LiteLLM gateway + Scheduled Task 永続化
  - A: Ryzen AI SDK + NPU 検証 (進行中、結果反映で本 ADR 改訂予定)

# 付録 A: fleet.toml 完全追加案

下記を `50-infra/murakumo/fleet.toml` の `[bootstrap]` セクションの直前 (line 303 付近) に挿入:

```toml
# ─── External inference backends (non-cell, GPU pods) ───────────────
# Per ADR-2605202345. Windows / non-launchd machines that provide LLM
# and image/video inference for cells. Do NOT run kotodama cells here.

[[inference_backends]]
name = "evo-x2"
host_lan = "192.168.1.70"
role = "gpu-inference-pod"
adr = "2605202345"

[inference_backends.evo-x2.hardware]
chip = "AMD Ryzen AI Max+ 395"
igpu = "Radeon 8060S (gfx1151, RDNA 3.5)"
npu = "AMD XDNA"  # 50 TOPS, status pending Subagent A
vram_gib = 32  # BIOS UMA carve-out from 128 GB unified memory
sys_ram_gb = 96
os = "Windows 11 Pro 24H2"

[inference_backends.evo-x2.endpoints.ollama]
url = "http://192.168.1.70:11434"
api = "openai-compatible"
auth = "lan-only"
models = ["llama3.2:3b", "llama3.3:70b"]
backend = "ROCm gfx1151"
verified_perf = { "llama3.2:3b" = "83 tok/s", "llama3.3:70b" = "1.18 tok/s" }

[inference_backends.evo-x2.endpoints.litellm]
url = "http://192.168.1.70:4000"
api = "openai-compatible"
auth = "bearer master_key"
master_key_env = "EVO_X2_LITELLM_KEY"  # rotate per security policy

[inference_backends.evo-x2.endpoints.comfyui]
url = "http://192.168.1.70:8188"
api = "comfyui-native"
auth = "lan-only"
models = ["animagine-xl-4.0", "waiIllustriousSDXL_v160", "wan2.2_ti2v_5B_fp16"]
verified_perf = {
  "animagine_xl4_1024x1024_25steps" = "21 s",
  "wai_v160_1024x1024_30steps" = "25 s",
  "wan22_5B_1280x704_41frames" = "502 s",
}

[inference_backends.evo-x2.persistence]
ollama_task = "OllamaServer (Scheduled Task, AtStartup, gad/S4U, Highest)"
litellm_task = "LiteLLMProxy (Scheduled Task, AtStartup, gad/S4U, Highest)"
comfyui_task = "ComfyUI (Scheduled Task, AtLogOn, gad, Highest)"

[inference_backends.evo-x2.healthcheck]
endpoints = [
  "GET http://192.168.1.70:11434/v1/models",
  "GET http://192.168.1.70:4000/v1/models (with bearer)",
  "GET http://192.168.1.70:8188/system_stats",
]
prometheus_scrape = true  # add to murakumo prometheus config (separate change)

[inference_backends.evo-x2.failover]
on_unreachable = "cells fall back to own-node local Ollama gemma3:4b"
replica_recommended = "future M3/M4 Ultra Mac mini with 128 GB unified, or 2nd EVO-X2 class"
```

更新する既存セクション (line 231-237 付近):

```diff
 [cells.EthicsContentClassifierCell]
 healthz_port = 13014
 trigger = "synchronous API"
 api_port = 13114
 adr = ["2605192400"]
 llm_primary = "claude-sonnet-4-6"
-llm_fallback_local = "gemma3:4b (Murakumo Ollama)"
+llm_fallback_local = "llama3.2:3b @ evo-x2 (per ADR-2605202345)"
+llm_fallback_local_secondary = "gemma3:4b (own-node Ollama, on evo-x2 unreachable)"
+llm_heavy_review = "llama3.3:70b @ evo-x2 (batch-only, 1.18 tok/s)"
```
