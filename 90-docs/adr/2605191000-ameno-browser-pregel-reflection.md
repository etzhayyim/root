---
id: 2605191000-ameno-browser-pregel-reflection
title: Ameno browser-side Pregel (LangGraph) with reflection loop
status: proposed
doc_type: adr
topic: ameno-browser-agent-loop
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605190824-ameno-mediapipe-llm-browser-runtime
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related:
  - adr-2605172000-etzhayyim-rw-free-substrate
---

# ADR 2605191000: Ameno browser-side Pregel (LangGraph) with reflection loop

## Context

`ameno.etzhayyim.com` の現状(2026-05-19 時点):

- ブラウザ側は素の chat UI。`handleSend` → `mediapipeGenerate` 1 回 → token stream → UI、で終わる単一 LLM call
- ADR-2605171800 が定める LangGraph Pregel パイプラインは **server-side LangServer (K8s pod `ameno-langserver`)** を対象に書かれており、browser 側には届いていない
- "active inference / reflection / agent loop" と言える構造は browser 側ゼロ

一方 ADR-2605182312 + 2605171300 が描く磐石化シナリオは、artificial-organism の active inference を **複数 tier に分散** する想定。Tier 2 (ameno browser) も「単発推論サーバ」ではなく **Pregel actor として super-step を回せる場所** であるべきで、それが「reflection を browser 内で完結させる」ための必須条件。

## Decision

**LangGraph TS (`@langchain/langgraph` v1.x) を browser ESM 経由で導入し、ameno svelte に StateGraph runtime を埋め込む。** server-side ADR-2605171800 の browser-side complement として扱う。

### Stage 1 — Pregel ランタイム化

| 追加 | 内容 |
|---|---|
| `@langchain/langgraph` ^1.3 (+ peer `@langchain/core` ^1.1) | StateGraph compile/invoke/streamEvents、Annotation API |
| `MemorySaver` checkpointer (browser in-memory) | thread_id 別の state 永続化。Stage 4 で `MstCheckpointSaver` (`@etzhayyim/sdk/checkpointer`) に差し替え |
| `60-apps/.../svelte/src/lib/graph.ts` | ameno 専用 StateGraph factory(後述) |

state schema:

```ts
const State = Annotation.Root({
  messages:        Annotation<ChatMessage[]>({ reducer: (a,b)=>a.concat(b), default: ()=>[] }),
  draft:           Annotation<string>({ reducer: (_,b)=>b, default: ()=>"" }),
  critique:        Annotation<{ score: number; feedback: string } | null>({
                     reducer: (_,b)=>b, default: ()=>null }),
  iteration:       Annotation<number>({ reducer: (_,b)=>b, default: ()=>0 }),
  maxIterations:   Annotation<number>({ reducer: (_,b)=>b, default: ()=>1 }),
});
```

### Stage 2 — Reflection loop

```
START
 └─ generate    ← mediapipeGenerate を呼んで draft 生成
        ↓
     critique   ← LLM が draft を 0-10 で採点 + 1 行改善コメント。
        ↓        Output: JSON {"score": N, "feedback": "..."}
   decide_continue (conditional edge)
   ├─ score ≥ 7 OR iteration ≥ maxIterations → finalize
   └─ else → revise
        ↓
       revise   ← critique を context に追加して再 generate
        └─ → critique (loop)
       finalize ← messages へ assistant turn 1 件 append
        ↓
       END
```

UI への露出:
- `maxIterations` を 0/1/2 のラジオ:
  - **0**: reflection 無効(従来挙動)
  - **1**: 1 ラウンド改善(default)
  - **2**: 2 ラウンドまで
- phase インジケータ: `thinking` / `critiquing` / `revising`
- 各 phase の tokens/sec を別計測

### Stream 統合

`mediapipeGenerate(messages, onToken)` を `generateNode` / `reviseNode` から呼ぶ。token は LangGraph の `dispatchCustomEvent("token", { token, phase })` で外に出して、`graph.streamEvents(input, { version: "v2" })` で App.svelte が拾う。Mediapipe の同期 callback と LangGraph の async event を橋渡しする adapter は graph.ts 内に閉じる。

### MediaPipe LlmInference 単一インスタンス制約

MediaPipe 0.10.x の `LlmInference` は **同時 generateResponse 不可**(2 つ目を呼ぶと throw)。reflection loop は逐次なので問題なし。ただし node 内から並列に呼ばないよう StateGraph は **直列辺のみ**に固定する。

## Consequences

- ameno が「Pregel actor」と名乗れる substrate になる。ADR-2605171800 で server-side LangServer 用に書かれた node 規約をそのまま browser 内に縮約再利用可能
- 1 ユーザターンの decode 回数は最大 1 + 2×maxIterations(generate + critique + revise loop)。Gemma 4 E2B WebGPU で 1 ターン 8-15 秒 × 最大 3-5 回 = 体感 30-75 秒。デフォルト maxIterations=1 でバランス
- ADR-2605181100 の encrypted records は graph state を直接持たない。graph state 自体は in-memory のみ、永続化が必要な時のみ messages slice を `encryptedWrite` で MST へ送る
- 後段 Stage 3 (active inference) は graph.ts に `predictionNode` / `surpriseNode` を足すだけで合流できる。state schema には今からそのスロットを置かない(YAGNI、Stage 2 完了後に再評価)

## Alternatives Considered

1. **LangChain Expression Language (LCEL) のみ** — Pregel 抽象が出ない。並列 / 循環 / checkpoint が辛い。reflection loop は state machine が要るので却下
2. **自前で StateMachine 書く** — できるが他 ADR との接続性ゼロ。LangGraph は既存 ADR の語彙そのものを使えるので採用
3. **server-side LangServer (Tier 1 K8s) に投げて browser は薄いクライアント** — Tier 2 browser が murakumo Tier 1 と独立して回ることが ameno の存在意義(ADR-2605182312)。server 依存にすると Tier 2 の意味を失う

## References

- ADR-2605190824 (Ameno MediaPipe LLM browser runtime)
- ADR-2605171800 (server-side LangGraph Pregel pipeline)
- ADR-2605182312 (Murakumo local bring-up; Tier 2 == ameno browser)
- Reflexion: Shinn et al. 2023 (self-critique → revise として模倣)
