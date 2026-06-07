---
id: 2605191407-ameno-browser-viewer-mode
title: Ameno browser viewer mode — svelte appview as thin client over daemon SSE
status: proposed
doc_type: adr
topic: ameno-viewer-mode
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191000-ameno-browser-pregel-reflection
  - 2605191229-ameno-daemon-path-a-bun-langgraph
  - 2605191257-ameno-daemon-path-b-kotodama-python
  - 2605191135-ameno-tier2-daemon-residency
related:
V05190824-ameno-mediapipe-llm-browser-runtime
V05191346-etzhayyim-vultr-free-murakumo-control-plane
---

# ADR 2605191407: Ameno browser viewer mode — svelte appview as thin client over daemon SSE

## Context

ameno は今 **3 つの実行モード**を持つ:

| モード | 場所 | LLM 経路 | state |
|---|---|---|---|
| **Tier 2 browser**(default) | user's browser tab | MediaPipe Gemma 4(WebGPU)| LocalCheckpointer(localStorage) |
| **Tier 2 host daemon, Path A** | user's box + launchd | Ollama localhost | FileCheckpointer(`~/.ameno/`) |
| **Tier 2 host daemon, Path B** | user's box + systemd | Ollama localhost | FileCheckpointer(`~/.ameno/`) |

3 つとも **同一の GraphChunk shape** を emit する設計を意図的に守ってきた(ADR-2605191000 → 2605191229 → 2605191257)。これにより svelte appview の chat UI 側はモード差を気にせず chunk を流すだけで描画できる構造になっている。

ただし現状の svelte appview は **常に local LangGraph を呼ぶ**:`invokeAmeno({ ... onChunk })` → ブラウザ内の StateGraph.stream(custom)。daemon を立ち上げても browser はそれを使えない。

本 ADR で **browser を daemon のビューア化** する。

## Decision

**`Compute mode` を svelte appview に導入**:

| value | 動作 | LLM 経路 |
|---|---|---|
| `local`(既存)| `invokeAmeno({ ... })` を browser 内で実行 | MediaPipe Gemma WebGPU |
| `daemon-a`(新規)| `invokeAmenoRemote("http://127.0.0.1:12480", { ... })` | daemon(Path A TS, Ollama) |
| `daemon-b`(新規)| `invokeAmenoRemote("http://127.0.0.1:12481", { ... })` | daemon(Path B Python, Ollama) |
| `custom`(新規)| 任意 URL(`https://ameno-daemon.etzhayyim.com` 等、 CF Tunnel 経由)| 同上 |

### Transport

daemon の `POST /threads/:tid/stream` は SSE で `data: <GraphChunk JSON>\n\n` を流す(`server.ts` / `server.py` 既存実装)。EventSource は POST 不可なので **`fetch` + `ReadableStream` の手書きパーサ** を browser-side に書く:

```ts
async function invokeAmenoRemote(baseUrl: string, opts: InvokeOpts): Promise<string> {
  const resp = await fetch(`${baseUrl}/threads/${tid}/stream`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ messages, maxIterations, activeInference, toolsEnabled }),
  });
  for await (const line of iterateSSE(resp.body!)) {
    const chunk = JSON.parse(line) as GraphChunk;
    opts.onChunk(chunk);
    if (chunk.type === "done") return chunk.draft;
  }
}
```

エラーは abort signal 受領 / network drop / HTTP non-2xx の 3 ケース対応。

### State 分離

| state | local mode | daemon-A/B mode |
|---|---|---|
| graph checkpoint(messages, prediction, tool_history) | LocalCheckpointer(localStorage) | daemon の FileCheckpointer(`~/.ameno/`) |
| Memory vault(remember/recall_long_term) | browser IndexedDB | (daemon は未対応、tool が error 返す) |
| Worker DID | `did:web:browser:<uuid>` | daemon の `did:web:host:<hostname>-<uuid>` |
| Surprise embedding(MiniLM)| browser WebGPU/WASM | (daemon は lexical のみ、`mode` フィールドで表示) |

つまり **viewer mode 時は user の "agent" としては daemon が主役**、 browser は表示器に過ぎない。state が daemon 側に集積する。

### UI 表面

Reflection bar に「**Compute**」セレクタ追加:

```
Compute: [ local | daemon @12480 (Path A) | daemon @12481 (Path B) | custom… ]
```

`daemon-a` / `daemon-b` 選択時:
1. background で `GET <url>/workerInfo` を 5s 間隔で poll、heartbeat chip に表示(`daemon ✓ gemma3:4b @ 127.0.0.1:12480 · uptime 12m`)
2. local の "Load Model" カードは「Daemon mode — no local model needed」プレースホルダに切替
3. メッセージ送信 → `invokeAmenoRemote(...)` → 同じ chunk handler → 同じ chat UI

`custom` 選択時:
- URL input 表示、フォーマット validate(http/https://*:port)
- 接続テストボタン(`/healthz` ping)
- 成功で daemon mode に切替

### 認証 / 公開エンドポイント

v0.1 は **localhost-only**(`127.0.0.1`)。`custom` 経由で `https://ameno-daemon.etzhayyim.com` を指す場合は **future ingress ADR**(CF Tunnel + auth)で扱う。daemon 側に auth middleware は今は無い(ADR-2605191229 §sec を参照、`AMENO_HOST=127.0.0.1` 推奨)。

### COOP/COEP との両立

`http://127.0.0.1:12480` への fetch は **cross-origin** 扱い(svelte dev は localhost:5173)。COEP `credentialless` で credentials なし fetch は許可される。CORS ヘッダは daemon 側で `Access-Control-Allow-Origin: *` を既に返す(Path A `cors({ origin: "*" })` / Path B `CORSMiddleware`)。

## Consequences

- **Tier 1+2 が初めて HTTP で繋がる**。svelte appview を起動したまま daemon に LLM 推論を委譲できる
- ameno 4 mode が `Compute` セレクタ 1 つで切替可能。同じチャット UI、同じ Reflection / Active inference / Tools の制御
- **state 集積点**が変わる:local mode は browser localStorage、daemon mode は `~/.ameno/`。同 user で両方使うと **会話履歴が分裂**(将来 MstCheckpointSaver で統合、ADR-2605171800)
- daemon mode 時は **MediaPipe model load 不要 → 初回起動が速い**(2 GB の `.task` DL なし)
- WebGPU 持たない端末(古い iPhone Safari など)でも viewer として完全使用可
- **remote daemon(custom URL)** 経路の auth が無いまま `*.etzhayyim.com` 公開すると不正利用される。next ADR(CF Tunnel + did:web 認証)で対応するまで localhost 限定の運用ルール

## Alternatives Considered

1. **EventSource 使用** — POST body 渡せない。GET-only。daemon API 設計を壊すため reject
2. **WebSocket protocol** — bi-directional 不要、SSE で十分。実装コスト・運用コストとも増える reject
3. **gRPC-Web** — token streaming も可能だが proto 定義 + tooling 追加。oversized reject
4. **local mode だけ残し、daemon は CLI / curl 専用** — ADR-2605191135 で daemon を Tier-2 worker と定義した意図(同じ UI で両方扱える)を捨てる reject
5. **iframe で daemon の独自 UI を埋め込む** — daemon は意図的に UI 持たない headless 設計 reject

## References

- ADR-2605191000(browser Pregel)
- ADR-2605191229(Path A daemon)
- ADR-2605191257(Path B daemon)
- ADR-2605191135(Tier-2 daemon residency)
- W3C Fetch Streams: <https://streams.spec.whatwg.org/>
- COEP credentialless: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Cross-Origin_Embedder_Policy>
