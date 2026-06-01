---
id: 2605191120-ameno-embedding-surprise-tier-c
title: Ameno active inference — Tier C embedding-based surprise (MiniLM)
status: proposed
doc_type: adr
topic: ameno-active-inference
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191113-ameno-active-inference-lexical-surprise
related:
V05191000-ameno-browser-pregel-reflection
---

# ADR 2605191120: Ameno active inference — Tier C embedding-based surprise (MiniLM)

## Context

ADR-2605191113 で Tier A (lexical Jaccard surprise) を入れて active inference loop の骨格は確定した。lexical surprise の限界 — 「言い換え」「同義語」に無力、短文で語数が少ないと飽和 — を Tier A ADR 自身で明示済み。本 ADR でこれを **sentence embedding × cosine** に差し替える Tier C を実装する。

Tier B (LLM-based surprise scoring) は skip する: LLM call が +1/turn 増えるだけで Tier A 比の本質的改善が小さく、Tier C と二重実装する価値がない。

## Decision

**`Xenova/all-MiniLM-L6-v2` を transformers.js WASM で並走させ、prediction と actual user message の cosine 類似度から surprise を計算する。**

| 項目 | 値 |
|---|---|
| Model | `Xenova/all-MiniLM-L6-v2` (Apache 2.0, ungated, 22.7 MB ONNX fp32) |
| Runtime | `@huggingface/transformers` `pipeline("feature-extraction", ...)` |
| Device | `wasm`(MediaPipe LLM の WebGPU と GPU memory 競合させない) |
| Pooling | `mean` + `normalize: true`(L2 正規化済 vector で cosine が dot product と一致) |
| Surprise 式 | `surprise = round((1 - cosine) × 10)`、clamp [0, 10] |
| Lazy load | `surpriseMode === "embedding"` を最初に有効化した時のみ pipeline 初期化 |
| Fallback | pipeline 未 ready の間は lexical で代用、ready 後は embedding に自動切替 |

### State 拡張

```ts
// graph.ts StateAnnotation に追加
surpriseMode: Annotation<"lexical" | "embedding">({
  reducer: (_, b) => b,
  default: () => "lexical",
}),
```

### Surprise dispatch

```ts
async function evaluateSurprise(
  predicted: string,
  actual: string,
  mode: "lexical" | "embedding",
): Promise<{ score: number; mode: "lexical" | "embedding" }> {
  if (!predicted || !actual) return { score: 5, mode: "lexical" };
  if (mode === "embedding" && isEmbeddingReady()) {
    const [a, b] = await Promise.all([embed(predicted), embed(actual)]);
    const cos = cosine(a, b);
    return { score: clamp(Math.round((1 - cos) * 10), 0, 10), mode: "embedding" };
  }
  return { score: lexicalSurprise(predicted, actual), mode: "lexical" };
}
```

`surprise_eval` node が **lexical / embedding どちらで計算したか** を chunk として返し、UI に "lexical" / "embedding" ラベル付き badge を出す。

### UI 表面

| element | 動作 |
|---|---|
| Active inference 内 **"Embedding (MiniLM, ~23 MB)"** チェックボックス | ON で `surpriseMode = "embedding"` |
| ON した直後の lazy load 中 | "loading MiniLM…" pill 表示、surprise は lexical fallback |
| ready 後 | surprise badge に "via embedding" tooltip |

## Consequences

- ameno bundle に **lazy chunk +25 MB**(モデル + ONNX runtime 既ロード分は再利用)。初回 ON 時のみ DL、Cache API に乗る
- WebGPU は MediaPipe LLM が独占。embedding は WASM 1スレッド ~10ms/embedding なので 1 turn +20-30ms。MediaPipe decode の隣で誤差程度
- lexical → embedding 差替えは graph.ts 内に局所化、API 表面は同じ
- 後段で **RAG retrieval / 記憶検索** にも同じ embed pipeline が使い回せる(ADR-2605181100 encrypted records の semantic search 等)

## Alternatives Considered

1. **`Xenova/mxbai-embed-xsmall-v1`** — MiniLM より新しい・性能良好。ただし XSmall は HF Xenova mirror 未整備の time あり、stability 優先で MiniLM 採用
2. **WebGPU で embed pipeline 動かす** — MediaPipe との device 衝突は実害無いが、デバッグ複雑化。WASM 1 スレッドで十分速い
3. **Embedding を browser でなくサーバで** — ADR-2605172000 (RW-free / server-less) と相反。却下

## References

- ADR-2605191113 (Tier A lexical)
- ADR-2605191000 (browser Pregel + reflection)
- ADR-2605190824 (MediaPipe LLM browser runtime)
- Wang et al., MiniLM (2020)
