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
| **CPT held-out A/B 測定 (残課題 #2, 2026-06-12)** | **base 20.4% (11/54) vs CPT 18.5% (10/54) = −1.9pp (ノイズ域、net −1 unit)**。held-out = 訓練外54ユニット (rasen/mitooshi/watatsuna/kakaku、gold 30 とも cpt-full とも非重複)、gad peft 直接生成 (決定論 greedy)、bb-実ロードゲート両アーム同一適用。フリップ 5 gained / 6 lost は全て小 const/単純関数 (`_SQRT2`/`ALLOWED_USE`/`CLINSIG_WEIGHT` 等) でフォーマットノイズ級。**結論: gold-only 3-epoch CPT は held-out 汎化に効かない** (`lora_B≠0`=「学習成立」は held-out coverage 改善を含意しない)。アダプタは適用済み (出力は変化) だがコーパス過小 (30 doc/164 chunk) でスタイル獲得止まり |
| **SFT held-out A/B 測定 (残課題 #3, 2026-06-12)** | **base 20.4% vs SFT 18.5% (10/54) = −1.9pp (CPT と同一、ノイズ域)**。SFT-LoRA = `sft-clj-lora-v1` (139 検証済み Python→Clojure チャットペア = fleet-12b 増幅収穫、`lora_B≠0` 28505 / train_loss 0.7529、seq_len 1280 + `expandable_segments` で 32GB iGPU OOM 回避)、リーク0確認 (held-out 54 と exact (file,unit) overlap なし)、SFT アームのみ再生成 (base_out 再利用)。フリップ 2 gained / 3 lost。**統合結論: e4b スケール + 小コーパス (≤139例) では CPT も SFT も held-out ~20% 天井を上げられない**。両者ともアダプタ学習成立だが、失敗する 80% (FFI / 複雑 stdlib / 多関数依存) に capability を足せず、易しいユニットの入れ替え (ノイズ) のみ。レバーは**ファインチューン手法ではなく base スケール (→12b) とコーパス規模 (→1000s)** |
| **e4b vs 12b fleet A/B 測定 (base スケール lever 検証, 2026-06-12)** | **fleet Ollama 同一スタック (20-stream / 10ノード×2 / native `/api/chat` think:false): e4b-it-qat 16.7% (9/54) vs 12b-it-qat 24.1% (13/54) = +7.4pp (net +4, 5 gained / 1 lost)**。**base スケール (e4b→12b) は有意に効く** — fine-tune (CPT/SFT は ~0pp) が動かせなかった天井を base 規模が +7.4pp 押し上げる。これが「レバーは手法ではなく base 規模」の直接証拠。ただし **12b でも絶対 24%** (4ユニットに1つのみ実ポート、残り 3/4 は stub) — これがフリート単発コード生成の天井。(e4b の fleet 16.7% は gad/peft bf16-greedy の 20.4% よりやや低い = q4_0 量子化 + Ollama + temp 0.1 のスタック差; 12b>e4b 信号は同一スタック内で明瞭) |

成果物の質的転換: 「4% 完成」→「96% コンパイル可能スケルトン + 26% 関数実装 + 機械可読 TODO スタブ」。
CPT の効果は held-out で **ゼロ (ノイズ域)** — レバーは「アダプタが学習したか」ではなく「コーパスが汎化に足る規模/多様性か」。次の打ち手は残課題 #3 (SFT 蒸留 = 139 検証済み fleet 増幅ユニット) + CPT コーパス拡大であり、gold-style CPT 単独ではない。Charter 機微・正しさ要求の移植は引き続き Claude エージェント (本セッションで 19-module ibuki + 14-actor stub 置換を緑テスト付きで完遂、クロス言語 CID/出力パリティ多数) が担う — フリートはバルク下書き + SFT ペア収穫に役割限定。

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
2. ~~CPT 済アダプタを base に `unit_refactor` 再測定 → coverage 改善を計測。~~
   **DONE 2026-06-12 — 改善なし (実測表参照: base 20.4% vs CPT 18.5%, −1.9pp ノイズ域)。**
   gold-only 3-epoch CPT は held-out 汎化に効かず。eval harness =
   `70-tools/scripts/fleet-refactor/cpt/{eval_ab.py,score_ab.py}` +
   `heldout-units.jsonl` (再現可能)。→ 残課題 #3 (SFT 蒸留) + コーパス拡大に redirect。
3. ~~**A (SFT 蒸留)**~~ **DONE 2026-06-12 — 改善なし** (実測表: base 20.4% vs SFT 18.5%,
   CPT と同一のノイズ域)。139 検証済みペアの SFT も e4b の ~20% 天井を破れず。
   小コーパス LoRA (CPT/SFT) は打ち止め。残る lever は **base→12b** (pilot-results の
   `12b-qat-fixed.jsonl` 参照) + **コーパス 1000s 規模化** のみ。**stage 2 (file-type 別
   expert LoRA)** は同じ天井に当たる公算が高く、優先度低。
   → 実務上の確定方針: **正しさ要求の移植は Claude エージェント** (本セッション実証:
   ibuki 19-module + 14-actor stub 置換、緑テスト + クロス言語 CID/出力パリティ多数、
   PR #1706)、**フリートは 12b バルク下書き + SFT ペア収穫** に役割限定。
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
