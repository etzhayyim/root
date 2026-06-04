---
id: adr-2605250400-gemma-coder-distill-rocm
title: "ADR-2605250400: gemma-coder distill — gemma4:e4b の LangGraph コーディング適応 (EVO-X2 ROCm)"
status: accepted
doc_type: adr
topic: gemma-coder-distill
authoritative: true
last_verified: 2026-05-25
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Mac mini fleet で serve 中の gemma4:e4b のコーディング能力を上げるための初の non-baien distill 経路"
authoritative_for:
  - "gemma4:e4b への LoRA fine-tune 経路 (baien 範囲外)"
  - "EVO-X2 ROCm trainer 選択 (Unsloth → peft+trl fallback)"
  - "merged HF → GGUF → Ollama 配布 runbook"
  - "LangGraph coding bench を distill 改善信号として採用する宣言"
depends_on:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605202345-evo-x2-gpu-pod-fleet-integration
  - adr-2605231300-baien-distill-react-loop
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - "70-tools/baien-distill/"
  - "50-infra/murakumo/fleet.toml"
  - "50-infra/cluster/murakumo/litellm/config.yaml"
supersedes: []
superseded_by: []
---

# ADR-2605250400: gemma-coder distill — gemma4:e4b の LangGraph コーディング適応 (EVO-X2 ROCm)

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki

# Context

## 現状

Mac mini fleet (10 nodes, `naphtali..asher`) は各ノード loopback の `ollama gemma4:e4b` (8B-class, Gemma 4 Effective 4B) を Tier-1 LLM fallback として serve している (judah Ollama `192.168.1.17:11434` で 2026-05-25 実機確認: `gemma4:e4b 8.0B Q4_K_M`、 `qwen3.5:9b 9.7B Q4_K_M`、`gemma3:1b 999M Q4_K_M`)。

**注**: `fleet.toml` および各種 ADR は `gemma3:4b` 表記が残っているが (ADR-2605215000 §1.1 表 etc.)、実 serve は **`gemma4:e4b`**。本 ADR は実態に合わせ Gemma 4 を student として固定する。`fleet.toml` の表記揺れは別 ADR で sweep する。religious-corp daemon (Pregel cell) が LangGraph で実装され (`20-actors/magatama/cells/`、ADR-2605192415)、その中で gemma4:e4b は **LangGraph code 生成** に使われる候補 (kaizen observer の自動修正提案、cell の dry-run 補助、bench prompt 生成等)。しかし現行 gemma4:e4b base は LangGraph 固有の API surface (StateGraph / reducer / interrupt / Send / `Annotated[T, ...]` 等) に専門特化されておらず、prompt-only では出力品質が頭打ち。

## なぜ baien-distill を流用しないか

`70-tools/baien-distill/` は **BitNet b1.58 2B-4T 専用** (`src/baien_distill/nodes/train.py:38` `BASE_MODEL_ID = "microsoft/bitnet-b1.58-2B-4T-bf16"` がハードコード)。かつ ADR-2605241900 (baien edge-target invariant) が baien の trunk 上限 ≤12 B / packed ≤1.6 GB / RAM ≤2.5 GB を constitutional に固定しており、gemma4:e4b (bf16 ≈ 8 GB、Q4_K_M でも ~2.5 GB 超) は **baien 名で出せない**。よって別 model class として fork する必要がある。

## なぜ Unsloth + ROCm か

| 候補 | 評価 |
|---|---|
| Unsloth on EVO-X2 (Windows + ROCm 7.2.1 + gfx1151) | **第一候補** — 2× 速度、量子化 LoRA、gemma-3 arch サポートあり (要 version 確認)。ただし Windows ROCm は Unsloth 公式 matrix 未掲載、`triton` 周りが brittle |
| peft + trl 直 (現 `baien-distill` と同じスタック) | **fallback** — `baien-distill/scripts/probe_rocm.py` で動作確認済み (torch 2.9.1+rocm7.2.1)。速度は Unsloth より遅いが機能は同等 |
| MLX-LM on Mac mini fleet | 棄却 — fleet は inference 専用、train ワークロードを launchd cell と混在させない (ADR-2605202100 §3) |
| 商用 GPU rental (RunPod 等) | **constitutionally 禁止** — ADR-2605215000 §1.2 + CHARTER-RIDER.md §2(i) |

## なぜ Claude Opus 直叩きを使わないか

ADR-2605215000 §1.2 は religious-corp inference path から「Anthropic-direct from vendor key」を constitutionally 禁止。一方で **Claude via judah LiteLLM gateway** は許容 (`fleet.toml:295` の `EthicsContentClassifierCell` が `llm_primary = "claude-sonnet-4-6"` で稼働中)。

ただし distill teacher としての Anthropic 利用は `baien-distill/src/baien_distill/nodes/select_teacher.py:7` §2 制約「OSS license; no commercial API」で除外されている。本 ADR では同制約を継承し、**Opus signal は HF-hosted Opus-distilled SFT corpus (Apache 2.0) からのみ取り込む** (例: `lordx64/reasoning-distill-opus-4-7-max-sft`、ADR-2605231300 §3a の祝福済みパターン)。

# Decision

## §1 スコープ

新規 tool `70-tools/gemma-coder-distill/` を作る。**`baien-distill` を fork せず、新規実装する** (理由: `BASE_MODEL_ID` ハードコード除去 + arch-agnostic 化は破壊的変更、baien 利用者を割らないため別 tool に分離)。共通化が必要な部分 (`adapters/hf_dataset.py` / Charter Rider scanner) は path import で再利用。

### §1.1 Student
- `google/gemma-4-e4b-it` (HF master, bf16)
- Ollama GGUF (`gemma4:e4b`) ではなく **HF model dir** を base に使う (LoRA 学習に必須)

### §1.2 Trainer (gate-1 probe 確定 — peft+trl)
- **採用**: peft + trl 直 (現 `baien-distill` と同じスタック)
- **Unsloth は不採用** — 2026-05-25 EVO-X2 probe で確定:
  - pip 依存解決が再帰深さ上限超過で破綻 (`90-docs/baien/probe_unsloth_rocm.json`)
  - 根因: Unsloth の依存ツリーが CUDA stack 前提 (`xformers` py39 wheel only / `triton-windows` CUDA-only / `torchao` + `cut_cross_entropy` CUDA 前提)
  - Windows + ROCm 7.2.1 + Python 3.12 環境ではインストール不能
- **再検討トリガ**: Unsloth が Windows ROCm wheel set を公式サポートした時点で再 probe (`70-tools/gemma-coder-distill/scripts/probe_unsloth_rocm.py` を再実行)
- 速度ペナルティ ~2× は許容 (gemma4:e4b LoRA は EVO-X2 1 iter ≤ 4 h 想定)

### §1.3 Teacher signal (3 種 mix)
1. **HF Opus-distilled SFT** (Apache 2.0 のみ)
   - `lordx64/reasoning-distill-opus-4-7-max-sft` (7823 rows) — general reasoning
   - コード特化 Apache/MIT corpus を 1-2 件追加 (per-iter で license review)
2. **LangGraph-API-specific synthetic SFT** — judah LiteLLM 経由で Claude に LangGraph code 生成 prompts を流して教師信号化。**ただし**:
   - LiteLLM master_key は Keychain 経由 (`50-infra/cluster/murakumo/litellm/install.sh`)
   - 生成 dataset は per-iter で Charter Rider §2 scanner 通す
   - 公開可否は ADR-2605231300 §"License and Charter Rider implications" のレビューゲート相当を本 tool にも適用
3. **既存 LangGraph 実装からの harvest** — `20-actors/magatama/cells/`、`70-tools/baien-distill/`、`50-infra/mst-projector/projection/` の自前コードから (prompt → 該当 cell code) ペアを抽出

### §1.4 LoRA configuration
ADR-2605231300 §5 表を継承:
- r=16, alpha=32, dropout=0.05
- target_modules = `["q_proj", "k_proj", "v_proj", "o_proj"]`
- learning_rate=2e-4, warmup=100, cosine scheduler
- batch_size=1, grad_accum=4, bf16

### §1.5 Bench gating
**新規 bench を本 ADR の前提として要求**: `70-tools/scripts/bench/langgraph-coding/`
- 50 prompts (StateGraph 設計 / node 関数 / reducer / interrupt 使用 / Send fan-out / Annotated reducer / checkpointer 統合 等)
- exec-graded: 生成コードを subprocess で実行し、固定 input に対する固定 output assertion で pass/fail
- lm-eval-harness 互換 JSON 出力 (`90-docs/baien/results-langgraph-*.jsonl`)
- distill loop の `evaluate.py` が iter 前後で delta を読み、改善がなければ `commit_node` を抑止

### §1.6 配布 (Mac mini fleet への push)
```
EVO-X2:  merged HF dir
         ↓ llama.cpp convert
         gemma3-coder-4b-Q4_K_M.gguf
         ↓ Ansible (60-apps/etzhayyim-project-murakumo/ansible/)
各 mini: ollama create gemma3-coder:4b -f Modelfile
         ↓
judah LiteLLM (192.168.1.17:4000): route `gemma3-coder:4b` 追加
```
- ADR-2605215000 §1.1 を不変に保つ (EVO-X2 + Mac mini Ollama + judah LiteLLM の三層構成)
- Mac mini 側に train 環境を入れない (§2.1 launchd-only 維持)

## §2 不変条件 (constitutional)

| 項目 | ルール |
|---|---|
| GPU backend | **EVO-X2 のみ** (LAN 192.168.1.70)。商用 GPU rental 禁止 (ADR-2605215000) |
| Train host | EVO-X2 only。Mac mini fleet で train しない (ADR-2605202100) |
| Teacher signal | HF Apache 2.0 SFT 優先。Claude は judah LiteLLM 経由のみ、Anthropic 直叩き禁止 (ADR-2605215000 §1.2) |
| Dataset license | per-iter で license review、Apache/MIT/CC-BY のみ commit、それ以外は train のみ可で artifact 非公開 |
| Charter Rider | 生成 dataset 全件で §2(a)-(h) scanner (`etzhayyim_organism.sensors.charter_rider.scan`) を通す。違反は drop |
| 命名 | `gemma3-coder:<tag>`。**`baien-` prefix 禁止** (ADR-2605241900 への侵食を防ぐ) |
| Substrate state | 学習ログ・dataset hash・adapter は `baien-distill-out/` 相当の local + IPFS pin。RW / Postgres 禁止 (ADR-2605172000) |

## §3 実行順序

| Step | 内容 | Gate |
|---|---|---|
| 1 | Unsloth ROCm probe を EVO-X2 で実行、`probe_unsloth_rocm.json` を `90-docs/baien/` に commit | trainer 確定 |
| 2 | `70-tools/scripts/bench/langgraph-coding/` を立てる (50 prompt, exec-graded) | 改善信号確保 |
| 3 | `70-tools/gemma-coder-distill/` scaffold (pyproject.toml + langgraph node 群、`baien-distill` adapters を path import) | tool 整備 |
| 4 | iter-00 quick run (1 epoch, n≤500) で E2E smoke、bench delta ≥ 0 を確認 | pipeline 検証 |
| 5 | iter-01 full (2 epoch, n=フル) で実改善を狙う、delta ≥ +3 pp 出れば commit | 価値検証 |
| 6 | GGUF convert + Ollama push runbook を `60-apps/etzhayyim-project-murakumo/ansible/` に追加 | 配布 |
| 7 | judah LiteLLM `config.yaml` に `gemma3-coder:4b` route 追加 | 公開 |

# Consequences

## Positive
- religious-corp の LangGraph 生成タスク (kaizen-observer 修正提案、cell scaffold、bench prompt 生成) が gemma4:e4b で改善され、Claude API 呼び出し回数が削減される (cost + sovereignty)
- baien (BitNet edge) と分離した gemma (Mac fleet serve) の二系列 distill 経路を establish、将来 llama / qwen など追加可能
- 既存憲法層 (ADR-2605215000 / 2605241900 / Charter Rider) を一切変更せずに済む

## Negative / Risk
- Unsloth Windows ROCm 未動作なら fallback で速度 2× 損 (許容)
- Teacher signal の品質が HF SFT に依存。LangGraph specific は §1.3.2 synthetic に依存し、これは Claude via judah を要求 — judah の master_key 運用と per-iter Charter Rider scan の信頼性が単一障害点
- bench 設計が貧弱だと commit gate が false-positive → 退行 model を公開してしまうリスク。bench design レビューを Council Lv4+ で要求

## Open
- gemma-3 license terms (`gemma-terms-of-use`) は Apache 2.0 ではない。**配布**するなら gemma TOS を継承する必要あり。fleet 内 inference のみなら問題なし。
- Unsloth が Windows ROCm 対応していない場合、Linux dual-boot or WSL2 への移行検討は scope 外 (ADR を別途切る)

# Alternatives Considered

| 案 | 却下理由 |
|---|---|
| baien-distill を一般化 (`--student` flag) | 破壊的変更、baien 利用者と道連れ。tool 分離が衛生的 |
| Mac mini fleet で MLX-LM 学習 | fleet を train ワークロードで汚染、launchd-only ルール (ADR-2605202100) と齟齬 |
| Claude を直 distill teacher として使う | ADR-2605215000 §1.2 違反 (Anthropic-direct from vendor key) |
| 配布せず EVO-X2 で gemma3-coder を serve | 単一障害点、Mac fleet の availability メリットを捨てる |
| GGUF ではなく vLLM で serve | Mac fleet は Ollama 統一、vLLM 導入は別 ADR |

# References

- ADR-2605215000 (etzhayyim inference Murakumo-fleet-only)
- ADR-2605202345 (EVO-X2 GPU pod integration)
- ADR-2605231300 (baien-distill ReAct loop)
- ADR-2605241900 (baien edge-target invariant)
- ADR-2605192200 (Charter Rider v2.0)
- ADR-2605172000 (RW-free substrate)
- `70-tools/baien-distill/src/baien_distill/` (reference implementation)
- `50-infra/murakumo/fleet.toml` (cell placement)
- `50-infra/cluster/murakumo/litellm/config.yaml` (gateway)
