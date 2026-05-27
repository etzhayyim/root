---
id: 2605191113-ameno-active-inference-lexical-surprise
title: Ameno active inference loop — lexical surprise + predict-next node
status: proposed
doc_type: adr
topic: ameno-active-inference
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191000-ameno-browser-pregel-reflection
related:
V05190824-ameno-mediapipe-llm-browser-runtime
---

# ADR 2605191113: Ameno active inference loop — lexical surprise + predict-next node

## Context

ADR-2605191000 が "Stage 3 — active inference" を後段で扱うと約束した。約束の実体化が遅れると "reflection は付いたが agent loop は無いまま" の状態が固定化するため、最小実装を先に投入して構造を確定させる。

active inference の **理論を厳密に踏襲**するのは browser 単独では重い(prior / posterior 分布、free energy 最小化)。一方で **epistemic surrogate** — 「次ターンの user 発話を予測し、観測との差分を beliefs 更新の信号にする」 — は LLM + 簡易距離で近似可能で、ameno の chat フローに直接乗る。

## Decision

**Stage 3 を 3 階層で段階的に実装する。本 ADR は Tier A だけを確定する。**

| Tier | 採用 | LLM 増 | 追加依存 |
|---|---|---|---|
| **A. lexical surprise + predict-next** | **本 ADR で実装** | +1/turn (predict のみ) | なし |
| B. LLM-based surprise scoring | follow-up | +2/turn | なし |
| C. embedding-based surprise (sentence-transformer) | follow-up | +1/turn | `@huggingface/transformers` の embed pipeline (~25 MB) |

### Tier A データモデル

State annotation に 3 フィールドを追加:

```ts
prediction:     Annotation<string>     // 前ターン finalize 時に書かれた "次の user 発話" 予測
surprise:       Annotation<number|null> // 0-10、最新の予測 vs 観測の Jaccard 距離 ×10
activeInference: Annotation<boolean>   // UI トグルで切替
```

### Tier A graph 形状

```
START
 ├─ surprise_eval   ← state.prediction (前ターン) と最新 user message から Jaccard 距離計算
 ├─ generate        ← system prompt に surprise context を注入
 ├─ critic          ← (Reflection が ON のとき)
 ├─ revise (loop)   ← 同上
 ├─ finalize
 ├─ predict_next    ← LLM call: assistant が "次にユーザが言いそうな短文" を予測、state.prediction に書く
 └─ END
```

- `activeInference=false` なら **両 node を conditional edge で skip**(消費 LLM call 0)
- `surprise_eval` は **lexical** (Jaccard distance × 10)。LLM call ゼロ
- `predict_next` は LLM call 1 個。 prompt 圧縮で短く制限(`Predict the user's next short utterance in ≤20 tokens.`)
- generate は state.surprise が null でない時のみ "前回 X を予測したが Y が来た。surprise=N/10。" を system に注入

### Lexical surprise 関数

```ts
function lexicalSurprise(predicted: string, actual: string): number {
  if (!predicted || !actual) return 5;          // 予測なし = 中央値
  const tok = (s: string) => new Set(s.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? []);
  const a = tok(predicted);
  const b = tok(actual);
  if (a.size === 0 && b.size === 0) return 5;
  const inter = new Set([...a].filter(x => b.has(x)));
  const union = new Set([...a, ...b]);
  const jaccard = inter.size / union.size;       // 0 = 無関係, 1 = 同一
  return Math.round((1 - jaccard) * 10);         // 0 = 同一, 10 = 完全に外れた
}
```

Jaccard は語順を見ない・短文に弱い・言い換えに無力 — Tier A の限界として明示する。Tier C の embedding-cosine で本来欲しいが、まず構造を入れる。

### UI 表面

| element | 表示 |
|---|---|
| Reflection bar の右に **"Active Inference" toggle** | OFF / ON |
| 各 user message 右肩に **surprise badge** | `surprise N/10`、N≥7 で赤、3..6 で黄、0..2 で緑 |
| Input 上部 **predicted next chip** | "predicted: …" 短文。クリックで input にコピー |

### Surprise の system prompt 注入

```
Last turn you predicted the user would say: "{prediction}".
The user actually said: "{actual_last_user_msg}".
Surprise score: {surprise}/10 (lexical Jaccard).
{ if surprise >= 7: "Treat the user's intent as having shifted; ask a short clarifying question." }
{ if surprise <= 2: "Your model of the user is on track; proceed confidently." }
```

## Consequences

- ameno が **observation → surprise → belief update → action** の最小ループを持つ。"agent" を名乗る最低条件をクリア
- Tier A はゼロ追加依存。ADR-2605190824 の bundle size に変化なし(コードのみ +200 行)
- 1 ターンあたり LLM call は `(active off, reflection 0) = 1` → `(active on, reflection 0) = 2` → `(active on, reflection 1) = 4`。Gemma 4 E2B WebGPU で 10-15s/call × 4 = 40-60s/turn(明示する)
- Tier B/C ADR は本 ADR の `state.surprise` reducer をそのまま再利用、`surprise_eval` ノードの中身だけ差し替え

## Alternatives Considered

1. **embedding model を先に入れる(Tier C 先行)** — 25 MB 追加 + WebGPU pipeline 2 個並走で複雑度跳ね上がり。lexical でまず構造確定する方が後戻りリスク小
2. **predict_next を背景で非同期** — race を避けるため見送り。同期 graph 内で十分速い
3. **active inference を Pregel super-step ではなく Svelte $effect で実装** — graph 外で状態が二重化する。state はすべて Pregel side に保つ

## References

- ADR-2605191000 (browser Pregel + reflection)
- Friston, K. (2010) "The free-energy principle: a unified brain theory?" Nat Rev Neurosci
- (注: 厳密 FEP との対応は Tier C 以降で評価)
