---
id: 2605191129-ameno-browser-tool-use-react
title: Ameno browser-local tool use — ReAct over JSON-tagged calls
status: proposed
doc_type: adr
topic: ameno-tool-use
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191000-ameno-browser-pregel-reflection
  - 2605191113-ameno-active-inference-lexical-surprise
  - 2605191120-ameno-embedding-surprise-tier-c
related:
  - adr-2605172000-etzhayyim-kotoba-substrate
---

# ADR 2605191129: Ameno browser-local tool use — ReAct over JSON-tagged calls

## Context

ADR-2605191000 + 2605191113 + 2605191120 で reflection / active inference / embedding は導入済。残る "agent" の必須要素は **tool use** — model が言葉だけでなく行動を取れること。

Gemma 4 E2B は native function-calling format(Gemma 関数呼び出し JSON、OpenAI tools 形式 等)を学習していない。一方で **XML 風タグ + JSON 引数** の ReAct パターンは any LLM で機能する(Yao et al. 2022 ReAct, Shinn et al. 2023 Reflexion 派生)。

## Decision

**ReAct over JSON-tagged tool calls を採用。MediaPipe Gemma 4 が text-out 一発で `<tool>{...}</tool>` を emit、graph 側でパース → 実行 → 結果を context に積んで再 generate。** max 3 iteration / turn で発散を抑える。

### Wire format

model output に下記タグが出現した場合のみ tool call として扱う。複数並列可:

```
<tool>{"name":"<tool_name>","args":{...}}</tool>
```

正規表現: `/<tool>\s*(\{[\s\S]*?\})\s*<\/tool>/g`。JSON.parse が失敗したら無視。

### Built-in tools

| name | args | result | implementation |
|---|---|---|---|
| `now` | `{}` | ISO 8601 string | `new Date().toISOString()` |
| `recall` | `{ "query": string }` | top-3 prior messages by cosine | MiniLM (Tier C, ADR-2605191120)。embedding 未 ready なら error 文字列を返し model が反応できるように |
| `wikipedia` | `{ "title": string }` | first 500 chars of summary | `https://en.wikipedia.org/api/rest_v1/page/summary/{title}` (CORS `*`, ungated) |

Substrate boundary(ADR-2605172000)整合性: 外部 fetch は read-only / GET のみ・credentialless。書き込み tool は `e.write(...)` (= `@etzhayyim/sdk`) 経由でしか追加しない。

### Graph extension

state 追加:

```ts
toolIteration:     Annotation<number>     // 当ターン消費した tool loop 数
maxToolIterations: Annotation<number>     // default 3
toolHistory:       Annotation<Array<{call, result}>>  // reducer は concat(turn 内累積)
```

flow 変更(`generate` の後に conditional edge を増設):

```
generate → has_tool_call?
  ├ yes & toolIteration < max → execute_tool → generate (loop)
  └ no  → (critic if maxIterations > 0 else finalize)
```

`buildToolContext(state)` を generate の system 注入に追加。同一 turn 内で蓄積した `toolHistory` を:

```
Tool calls made so far this turn:
- now() → "2026-05-19T01:30:00Z"
- recall("active inference") → "[3 matches: ...]"
Either emit another <tool>{...}</tool> if you need more, or give the final answer.
```

の形で system message 1 件として前置。

### UI 表面

| element | 表示 |
|---|---|
| 各 tool call が起きた時点 | 黄系 chip `tool: now(...)` |
| 結果が返った時点 | 結果文字列(80 字 truncate + tooltip 全文)を chip に併記 |
| 失敗時 | 赤 chip + tooltip にエラー全文 |

assistant の最終応答からは `<tool>...</tool>` ブロックを strip して表示。

## Consequences

- ameno が **observation → reasoning → action** を回せる "tool-using agent" になる。reflection × active inference × tool use の 3 軸が browser 内で揃う
- 1 turn の最悪 LLM call 数: `(maxToolIterations) + 1(critic) + (maxReflections)(revise) + 1(predict_next)` = 3 + 1 + 2 + 1 = **7 call**(Gemma 4 E2B WebGPU で 70–105s/turn)。デフォルトは tool=3, reflect=1, predict=on で 5 call/40-60s
- tool ABI を JSON 1 行に固定したことで、`@etzhayyim/ameno/tools` から共通 registry を export して **他 actor app(kotodama / kami-engine 等)で再利用可能**
- 将来 Gemma が native tool-call トークンを学習したら、parser 側だけ拡張すれば共存(段階的差替え可能)

## Alternatives Considered

1. **OpenAI tools 形式 JSON schema fully-typed** — Gemma 4 は schema を確実に守らない(observed)。シンプル tag + free-form JSON の方が再現性高い
2. **Function call として直接 IndexedDB / fetch を model に与える** — code injection の脅威面が大きすぎる。tool は curated registry のみ
3. **Tool call を assistant message に role=tool として埋め込み(ChatML 風)** — Gemma chat template と衝突する。XML タグの方が安全

## References

- ADR-2605191000 / 191113 / 191120 (browser Pregel, reflection, active inference, embedding)
- Yao, S. et al. "ReAct: Synergizing Reasoning and Acting in Language Models" (2022)
- MediaWiki REST summary API: `https://en.wikipedia.org/api/rest_v1/`
