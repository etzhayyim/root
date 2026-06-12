---
id: adr-2606120500-fleet-clojure-refactor-and-gemma4-cpt
title: "ADR-2606120500: Murakumo-fleet 並列 Clojure 移行ハーネス + gemma4 CPT 特化パイプライン"
status: proposed
doc_type: adr
topic: fleet-clojure-refactor-and-gemma4-cpt
authoritative: true
last_verified: 2026-06-12
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 70-tools/scripts/fleet-refactor
  - 70-tools/clj/murakumo-langchain
depends_on:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605250400-gemma-coder-distill-rocm
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605231525
  - adr-2606052300
supersedes: []
superseded_by: []
---

# ADR-2606120500: Murakumo-fleet 並列 Clojure 移行ハーネス + gemma4 CPT 特化パイプライン

**Status**: proposed
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

monorepo の Python/TS ソース (~8,371 files) を kotoba-Datomic-native Clojure へ移行する目的で、
Murakumo Mac mini fleet (10 ノード, gemma4) + EVO-X2 (gfx1151 学習ボックス) を使った並列・
特化パイプラインを構築した。本 ADR はその設計・実測・既知の罠・残課題を正本化する。
ADR-2605215000 (Murakumo-only inference) に適合 — fleet Ollama 直叩きは認可経路。

# Decision

## 1. 推論クライアント層 (`70-tools/clj/murakumo-langchain/`)

[langchain-clj](https://github.com/com-junkawasaki/langchain-clj) /
[langgraph-clj](https://github.com/com-junkawasaki/langgraph-clj) (zero-dep / 全 .cljc /
I/O 注入の WASM premise) に **Ollama ネイティブ ChatModel アダプタ** + 10 ノード round-robin
fleet モデル + babashka host capability を実装。`(host/gemma)` で fleet 全体が 1 ChatModel に
なる。LCEL chain / StateGraph+checkpointer / ReAct (gemma4 native tool-calling) を live 検証。
移植先イディオムが langgraph-clj に 1:1 で落ちることを確認。

## 2. 移行ハーネス (`70-tools/scripts/fleet-refactor/`)

- `fleet_refactor.py` — whole-file 変換 (tailscale round-robin + clj-kondo ゲート + リトライ)。
- `cascade.py` — e4b 一次 → 失敗のみ 12b エスカレーション。
- `unit_refactor.py` — **stage 0**: Python ast で top-level 単位に分割 → fleet で個別変換 →
  `(ns…)+(declare…)+連結` を決定的組立 → clj-kondo + **bb (require ns) 実ロード**ゲート →
  失敗/幻覚単位は throw スタブへ降格 (demote-and-reassemble、収束保証)。
- `discover.py` / `evossh.sh` — 能力ベース動的ノード同定 (DHCP 腐敗の再発防止)。
- `sft_to_distill.py` — 収穫ペア → gemma-coder-distill (ADR-2605250400) TrainExample 変換。

## 3. CPT 特化パイプライン (`70-tools/scripts/fleet-refactor/cpt/`, EVO gfx1151)

founder 指示 (b): **Fable gold 30本で疎通 → fleet 増幅 → 本番 CPT**。

- ベース = `google/gemma-4-E4B-it-qat-q4_0-unquantized` (= fleet `gemma4:e4b-it-qat` の
  dequant QAT 同一重み; gated なし)。
- `gold-corpus/` = Fable 手実装 30 本 (1,622 行)、27 アーキタイプ被覆、全本 clj-kondo + bb 検証済、
  cid/GTIN/crane 物理は Python と出力一致。教師に Claude 出力は使わない (Anthropic 規約)。
- `cpt/cpt-full.jsonl` = gold 30 全文 + fleet 増幅の検証済み 134 unit = 164 docs。
- `train_cpt.py` — CPT-LoRA (causal-LM 継続学習)。

# Consequences

## 実測 (同一条件比較)

| 構成 | 結果 |
|---|---|
| whole-file ゼロショット (e4b→12b cascade) | 4/100 — 実分布では不成立 |
| stage 0 関数単位分解 (bb 実ロードゲート) | **47/49 ファイル compile-load / live unit 26%** |
| CPT パイプライン疎通 (SmolLM + 本番 gemma4) | e2e OK (loss 下降) |
| fleet 増幅 (140 files) | 139/140 bb 通過 / 139 検証済み unit |
| **本番 CPT-LoRA 再実行 (修正版, 2026-06-12)** | **lora_B nonzero mass 23693.68 — adapter learned**; grad_norm 2.298 / train_loss 2.097 (最終 step 1.489) vs 旧走行 grad_norm 0 / loss 7.086 横ばい; 3 epoch / 1,417 s; 保存 `gad:~/cpt-clj/cpt-clj-lora-v2` (残課題 #1 完了) |

成果物の質的転換: 「4% 完成」→「96% コンパイル可能スケルトン + 26% 関数実装 + 機械可読 TODO スタブ」。

## 確定した知見 / 罠

1. **Ollama OpenAI 互換 ep は `options/num_ctx` を黙って無視** → ctx 4096 で出力切断 → 「閉じ括弧不足」に見える。ネイティブ `/api/chat` を使う。
2. **gemma4 QAT 系は reasoning モデル** → `think:false` 必須。
3. **lint 合格 ≠ 意味的同値**: e4b 産には幻覚 API が混入。bb 実ロードゲート + SFT 教師は 12b 産限定。
4. **gemma4 マルチモーダル LoRA の no-op 罠 (CRITICAL)**: vision_tower の proj は `Gemma4ClippableLinear` /
   language_model の proj は素の `nn.Linear`。clippable 検出で `.linear` ターゲットに切替えると
   LoRA が **vision tower にだけ**注入され、テキスト loss の勾配経路外で `lora_B` 全ゼロのまま 3-epoch 走る
   (silent no-op)。修正: LoRA を `language_model.layers.N.(self_attn|mlp).(q|k|v|o|gate|up|down)_proj` へ
   regex スコープ + `use_reentrant=False` + post-train `lora_B==0` アサート。
5. **静的 IP は腐る**: EVO の記録 IP (.70→.22) は別マシン (Mac) を指していた。能力 (GPU 種別/OS/Ollama) で
   動的同定する (`discover.py`)。
6. **原本の信頼を仮定しない**: 移植点検中に fuchi/abaki の `live_gate.py` 空洞化 (no-server-key 違反、
   bulk workspace commit 経由で main 混入) を発見 → 別 blocker として founder 判断待ち。

## 環境 (EVO-X2 = gad)

- 192.168.1.16 (DHCP 変動; `discover.py --evo` で再確認) / Ubuntu 24.04.2 / AMD Ryzen AI MAX+ 395 /
  Radeon 8060S (gfx1151, RDNA3.5) / ROCm 7.13。
- 学習環境 = ComfyUI venv: torch 2.5.1+rocm6.2 + **`HSA_OVERRIDE_GFX_VERSION=11.0.0`** (gfx1100 偽装) で
  gfx1151 が動作 (rocm6.4 nightly / 素の gfx1151 カーネルは `hipErrorInvalidDeviceFunction`)。
  transformers 5.9 / peft 0.19 / trl 1.6。
- 鍵認証確立 (pw は Apple Keychain RDP 項目)、孤児鍵 2 つ除去。運用手順 = `ACCESS.md`。

## 残課題 (次セッション)

1. ~~**本番 CPT-LoRA 再実行** (修正版 train_cpt.py、3 epoch) → `lora_B` 非ゼロ確認。~~
   **DONE 2026-06-12** — 実測表参照 (lora_B nonzero 23693.68 / loss 7.086→2.097)。
   旧 gad 上スクリプトは no-op 版だったため repo 正本を再配置して実行。
2. CPT 済アダプタを base に `unit_refactor` 再測定 → coverage 改善を計測。
3. **stage 2 (file-type 別 expert LoRA)** / **A (SFT 蒸留)**。
4. founder 判断: fuchi/abaki `live_gate` 空洞化の処置 (revert / 正規 ADR で R2 化 / abaki 素性調査)。
5. Unsloth は EVO ROCm で probe FAIL 済 (ADR-2605250400 §1.2) — peft+trl direct を継続。

# Alternatives Considered

- **whole-file ゼロショット**: 実分布 4% で却下 (stage 0 の関数単位分解が桁違いに有効)。
- **教師に Claude 出力を使う**: Anthropic 規約のため不採用。教師は fleet 12b + 検証ゲート産に限定。
- **Unsloth**: gfx1151 ROCm で CUDA-only 依存により FAIL (ADR-2605250400)。peft+trl direct。
- **gemma-3n / gemma-3-4b をベースに**: fleet が走らせる重みと不一致のため却下。
  E4B-it-qat-unquantized が唯一の「fleet と同一重み」ベース。

# References

- `70-tools/scripts/fleet-refactor/plan.edn` — 計測・知見・改善ラダーの EDN 正本
- `70-tools/scripts/fleet-refactor/README.md` / `ACCESS.md`
- `70-tools/clj/murakumo-langchain/README.md`
- ADR-2605215000 (Murakumo-only inference) / ADR-2605250400 (gemma-coder-distill peft+trl)
- ADR-2605262130 (kotoba storage substrate) / ADR-2605231525 (no-server-key)
