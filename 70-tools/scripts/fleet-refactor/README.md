# fleet-refactor — Murakumo fleet 並列 source→Clojure 移植ハーネス

Python / TypeScript ソースを kotoba-Datomic-native Clojure へ移植する fan-out
ハーネス。Murakumo Mac mini fleet (10 ノード) の各 Ollama に tailscale 経由で
ラウンドロビン分配し、**clj-kondo 合格を強制**する (合格まで lint フィードバック
付きリトライ + EOF 閉じ括弧の決定的修復)。合格ペアは `fleet-refactor-sft.jsonl`
に SFT 蒸留データとして自動収穫される。

ADR-2605215000 (Murakumo-only inference) 準拠 — fleet Ollama 直叩きは認可経路。

## 使い方

```sh
# 単発
python3 fleet_refactor.py 20-actors/foo/methods/bar.py

# 一括 (stdin)
git ls-files '20-actors/**/*.py' | python3 fleet_refactor.py - --model gemma4:e4b-it-qat

# 12b は 1 リクエスト/ノード必須
python3 fleet_refactor.py --model gemma4:12b-it-qat --per-node 1 --timeout 600 FILE...
```

## パイロット結果 (2026-06-11, 同一 9 ファイル)

| 構成 | lint 合格 | 速度/ファイル | ログ |
|---|---|---|---|
| e4b Q4_K_M + 素朴プロンプト | 1/9 (11%) | 135–377s | `pilot-results/baseline-e4b-q4km.jsonl` |
| e4b Q4_K_M + プロンプト v2 | 2/9 (22%) | 60–173s | `pilot-results/v2-e4b-q4km.jsonl` |
| 12b-it-qat (ctx バグあり) | 1/9 | — | `pilot-results/12b-broken-ctx.jsonl` |
| **e4b-it-qat + 修正版** | **3/9 (33%)** | **21–110s** | `pilot-results/e4b-qat-fixed.jsonl` |
| **12b-it-qat + 修正版** | **4/9 (44%)** | 99–550s | `pilot-results/12b-qat-fixed.jsonl` |

e4b∪12b の合格は 5/9 (56%) — **カスケード (e4b 先行 → 失敗のみ 12b) が現状最良**。

## 学んだ罠

1. **OpenAI 互換エンドポイントは `options.num_ctx` を黙って無視する** — ctx が
   デフォルト 4096 のままになり、長い出力が切り詰められて「閉じ括弧不足」として
   現れる。ネイティブ `/api/chat` を使うこと。
2. **gemma4 QAT 系は reasoning モデル** — `think: false` を渡さないと思考トレース
   が ctx を食い潰す。
3. 12b はノードあたり 1 並列でないと M4 mini (16GB) では timeout する。
4. `brew services restart` は SSH セッションから launchctl gui domain に届かず
   exit 125。pkill → nohup `OLLAMA_HOST=0.0.0.0 ollama serve` が確実。
5. lint 合格 ≠ 意味的同値。lint は第1ゲートにすぎず、本採用には挙動検証
   (babashka 実行 + golden IO) が必要。
6. **原本の信頼を仮定しないこと** — 翻訳点検で fuchi/abaki の live_gate 空洞化
   (no-server-key 違反、一括 workspace commit 経由で混入) を発見。移植・SFT 収穫の
   前に原本の constitutional 整合を確認し、汚染ペアは `sft-quarantine.jsonl` へ。

## 次段 (fine-tune)

合格率の本命は LoRA 蒸留: teacher = 12b-it-qat + clj-kondo フィルタ
(rejection sampling)。`fleet-refactor-sft.jsonl` (chat-messages 形式) を
EVO-X2 の `e7m bench distill` (peft+trl, ADR-2605250400) に投入し
`gemma4:e4b` を本タスク特化で SFT する。教師データに Claude 出力は使わない
(Anthropic 規約)。Unsloth は ROCm gfx1151 対応が実験的なため、peft+trl で
動いてから乗り換えを検討。
