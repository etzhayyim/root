---
id: 2605191257-ameno-daemon-path-b-kotodama-python
title: Ameno headless daemon (Path B) — kotodama Python port
status: proposed
doc_type: adr
topic: ameno-headless-daemon
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191229-ameno-daemon-path-a-bun-langgraph
  - 2605182312-local-bring-up-murakumo-gemma4
  - 2605191135-ameno-tier2-daemon-residency
related:
V05191000-ameno-browser-pregel-reflection
V05191113-ameno-active-inference-lexical-surprise
V05191129-ameno-browser-tool-use-react
  - adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
---

# ADR 2605191257: Ameno headless daemon (Path B) — kotodama Python port

## Context

ADR-2605191229 で Path A(Bun/Node + Hono + LangGraph TS)を投入した。これは速い ROI のための **dev / single-machine** 用途には十分だが、Tier 1 = Murakumo Mac mini fleet が稼働する `kotodama` Python LangGraph stack(ADR-2605182312, ADR-2605180900)とはコード資産が分かれている。

artificial-organism ecosystem 全体の **正本(Source of Truth)** は Python `kotodama` 側にある:

- `kotodama.local_llm` — Ollama / MLX 統合済の Async HTTP client
- `kotodama.projects.uhl_right_neural` — 既存 LangGraph Pregel project の良いテンプレート
- `kotodama.langserver_compat` + `langgraph_server_app` — FastAPI / Granian server runtime
- `kotodama.checkpointer` — checkpoint 抽象、MstCheckpointSaver sidecar (ADR-2605171800) と連動
- `kotodama.ameno_handlers` — 既存の PDS XRPC saveResult/listHistory 永続化(server-side persistence layer)
- K8s pod template(`50-infra/k8s/lg-uhl-right-neural`)で **同 shape の pod として deploy 可能**

Path B はこれら Python 資産の上に **ameno project を新設** し、Tier 1 Murakumo fleet 上で同じ active-inference + reflection + tool-use ループを走らせる。

## Decision

**`kotodama.projects.ameno` を新設し、既存 Python LangGraph 資産で Path A と同じ agent loop を再実装する。**

### Module 構成

```
40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/projects/ameno/
├── __init__.py
├── __main__.py              # python -m kotodama.projects.ameno
├── pregel.py                # StateGraph (TypedDict + langgraph)
├── ollama_stream.py         # async streaming Ollama /api/chat
├── tools.py                 # ToolDef registry: now / wikipedia / recall
├── file_checkpointer.py     # MemorySaver subclass, JSON 永続化
├── server.py                # FastAPI + SSE endpoints (Hono と同形)
├── README.md
└── ameno-daemon.service     # systemd unit template (Linux)
```

### Path A との対応

| TS daemon (Path A) | Python (Path B) |
|---|---|
| `graph.ts` StateAnnotation | `pregel.py` TypedDict `AmenoState` |
| `ollama-runtime.ts` `runtimeGenerate(messages, onToken)` | `ollama_stream.py` `async runtime_generate(messages, on_token)` |
| `file-checkpointer.ts` | `file_checkpointer.py` |
| `tools.ts` `parseToolCalls / executeToolCall` | `tools.py` `parse_tool_calls / execute_tool_call` |
| `server.ts` Hono + `@hono/node-server` | `server.py` FastAPI + Granian |
| launchd plist (macOS) | systemd unit (Linux) + launchd plist (macOS optional) |

ABI(HTTP endpoints)は **完全同一**:`/healthz` / `/workerInfo` / `/threads/:tid/{invoke,stream,state}`。これにより browser viewer mode が Path A / B 区別なく接続可能。

### Tier 1 統合

K8s pod target(将来 PR):

```
50-infra/k8s/lg-ameno/
├── kustomization.yaml
└── lg-ameno.yaml            # 2-container topology (kotodama + checkpointer sidecar)
                              # ADR-2605171800 と同 shape
```

`kotodama.ameno_handlers`(既存 XRPC saveResult ハンドラ)と **同 pod 同居** が可能 — `ameno_handlers` は PDS write-side(従来の svelte → CF Worker → langserver の bare metal 受け口)、 新規 `projects.ameno` は agent loop。互いに独立、同 K8s namespace で並走。

### Worker identity

`did:web:host:<hostname>-<uuid>` を `~/.ameno/worker-did` に永続化。Path A と同じ scheme(同じ host で TS daemon と Python daemon が両方動いてる場合は **異なる UUID** で別 instance として登録)。

### 非スコープ(v0.1 で除外)

| 項目 | 理由 |
|---|---|
| MstCheckpointSaver (`@etzhayyim/sdk/checkpointer` sidecar 統合) | 既存 `lg-uhl-right-neural` パターンに乗る follow-up |
| Encrypted memory vault (remember/recall_long_term) | ADR-2605191206 と同様、substrate 統合と同時 |
| Embedding-based surprise | local sentence-transformers は heavy。Path A と同じく lexical のみ |
| Streaming via Granian high-throughput tuning | v0.1 は default SSE で十分 |

## Consequences

- ameno が **Tier 1 (Python kotodama) の正本** を持つ。Murakumo fleet の lg-* pod 群と同 shape で deploy 可能 → K8s で水平スケール
- Path A (TS) と Path B (Python) は **両方残す**:
  - Path A: dev 環境、軽量、launchd で macOS 単機
  - Path B: production / fleet、既存 langserver stack に統合、`agent_daemon_main` イベントループに繋ぎ込み可能
- 同じ HTTP API なので browser viewer mode は **どちらにも接続できる**
- 重複コードのコスト(~1.2k 行を 2 言語で保持)は、Tier 1/2 の役割分離と移植性の保険として許容
- `ameno_handlers` (既存 XRPC) と `projects.ameno` (新規 agent loop) の境界が明確化:前者は **受動 substrate**、後者は **能動 organism worker**

## Alternatives Considered

1. **Path A だけで止める** — Tier 1 統合性を捨てる。Tauri 拒否したのと同じ理由で reject:Murakumo backbone と分離すると organism ecosystem の一体性が損なわれる
2. **TS daemon (Path A) を CLI として kotodama から呼ぶ** — multi-language IPC のオーバーヘッド + 2 つの runtime を pod に置く重さ。reject
3. **ameno_handlers に agent loop を埋め込む** — XRPC handler は receive-only の薄い層、agent loop の責務を混入させると単一責任原則違反

## References

- ADR-2605191229 (Path A TS daemon)
- ADR-2605182312 (Murakumo Tier 1 bring-up)
- ADR-2605180900 (unispsc/isic langserver pattern)
- ADR-2605181000 (uhl_right_neural project template)
- `kotodama.local_llm`, `kotodama.ameno_handlers`(既存資産)
