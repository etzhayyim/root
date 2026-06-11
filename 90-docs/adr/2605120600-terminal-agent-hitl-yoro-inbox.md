---
id: adr-2605120600-terminal-agent-hitl-yoro-inbox
title: "ADR-2605120600: Terminal Agent HITL — LangGraph inmem + Yoro Inbox"
status: active
doc_type: adr
topic: terminal-agent-hitl-yoro-inbox
authoritative: true
last_verified: 2026-05-12
priority: 6.0
axis: architecture
weight: 0.75
priority_note: "terminal-agent k8s deployment + HITL decision inbox wired into Yoro"
authoritative_for:
  - terminal-agent LangGraph Server runtime selection (langgraph-cli[inmem])
  - terminal-agent k8s deployment topology (Vultr VKE, terminal-agent namespace)
  - HITL proxy architecture (Yoro CF Worker → terminal-agent.etzhayyim.com)
  - Yoro HITL inbox UI (/tasks/inbox)
  - HITL authentication model (HITL_API_KEY bearer + LANGCHAIN_API_KEY x-api-key)
depends_on:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605082100-langgraph-checkpointer-storage
supersedes: []
superseded_by: []
amends: []
---

# ADR-2605120600: Terminal Agent HITL — LangGraph inmem + Yoro Inbox

**Status**: accepted
**Date**: 2026-05-12
**Deciders**: Jun Kawasaki

## Context

`60-apps/etzhayyim-terminal-agent` は Claude Code 相当の CLI エージェント。`request_human_decision`
ツールで業務クリティカルな判断を人間に委ねる HITL (Human-in-the-Loop) フローが必要だった。

問題点:
- CLI はインタラクティブ端末を必要とするが、非同期で別デバイス (スマートフォン) から判断したい
- LangGraph Platform (`langgraph-api` + Redis + Postgres) は k8s デプロイが重く、
  Redis/Postgres 接続 + `LANGGRAPH_RUNTIME_EDITION` 環境変数管理が複雑だった
- `langgraph-api < 0.5.35` は runtime edition 未サポートで ImportError が発生した
- Granian ASGI サーバー方式は `langgraph_api.server:app` のエントリポイント解決に失敗した

## Decision

### 1. LangGraph Server runtime: `langgraph-cli[inmem]`

`langgraph dev` (via `langgraph-cli[inmem]`) を採用。

```
旧: granian langgraph_api.server:app (+ Redis + Postgres + LANGGRAPH_RUNTIME_EDITION)
新: langgraph dev --host 0.0.0.0 --port 2024 --no-browser
```

- `langgraph-cli[inmem]` が `langgraph-api >= 0.5.35` + `langgraph-runtime-inmem >= 0.7` をバンドル
- Redis 不要 (inmem queue)、Postgres 接続は `LANGGRAPH_CHECKPOINT_URL` 経由でオプション
- `langgraph.json` が graph 定義の SSoT: `{"graphs": {"agent": "terminal_agent.graph:graph"}}`
- `CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser"]`

### 2. k8s デプロイ (Vultr VKE, terminal-agent namespace)

```yaml
image: ghcr.io/etzhayyim/terminal-agent-server:latest
namespace: terminal-agent
port: 2024
```

- Kaniko Job (init container: alpine/git clone → Kaniko executor → GHCR push) でイメージビルド
- CF Origin wildcard cert (`*.etzhayyim.com`) を `dispatcher-etzhayyim-ai-tls` から namespace にコピー
- nginx-ingress: `terminal-agent.etzhayyim.com` → ClusterIP :2024
  - `proxy-buffering: off` (SSE streaming)
  - `proxy-read-timeout: 600s` (long-running runs)
- `LANGCHAIN_API_KEY`: LangGraph Server の `x-api-key` 認証。公開 IP からの直接アクセスを防ぐ
  (CF DNS proxied=true で origin IP 非公開)

### 3. HITL プロキシアーキテクチャ

```
Browser
  → POST https://yoro.etzhayyim.com/api/hitl/* (Authorization: Bearer HITL_API_KEY)
    → Yoro CF Worker Hono proxy
      → https://terminal-agent.etzhayyim.com/* (x-api-key: LANGCHAIN_API_KEY)
        → nginx-ingress → ClusterIP :2024 → LangGraph Server
```

- `HITL_API_KEY`: オペレーター用 Bearer token。Yoro Worker が検証
- `TERMINAL_AGENT_URL`: Worker secret (`wrangler secret put`)。`etzhayyim deploy` がwrangler.jsonc を
  再生成するため vars には書かない
- `TERMINAL_AGENT_API_KEY`: LangGraph Server の `x-api-key`。同じく Worker secret

Yoro Worker (`src/app.ts`) の `/api/hitl/*` Hono routes:
```typescript
app.all('/api/hitl/*', async (c) => {
  // 1. HITL_API_KEY bearer validation
  // 2. forward to TERMINAL_AGENT_URL with x-api-key header
  // 3. stream response body
});
```

### 4. Yoro HITL inbox UI (`/tasks/inbox`)

- `$lib/hitl-store.svelte.ts`: バックグラウンドポーラー (10s)
  - `/api/hitl/threads/search` (status=interrupted) を定期呼び出し
  - `pending` count を AppDrawer のバッジに反映
  - `HITL_TOKEN_KEY` (`etzhayyim:hitl-api-key`) を localStorage に保持
- `routes/tasks/inbox/+page.svelte`: 意思決定インボックス
  - API キーをキーアイコン UI から localStorage にセット
  - 中断スレッドを一覧表示: question / context / options
  - 選択肢タップ or 自由記述 → `POST /api/hitl/threads/{id}/runs/stream` (resume)
  - SSE ストリームで agent の続きの回答をリアルタイム表示
- AppDrawer: 「意思決定」nav item (紫バッジで pending 数表示)
- `+layout.svelte`: `hitl.start()` / `hitl.stop()` でポーラーのライフサイクル管理

### 5. resume プロトコル

```json
POST /api/hitl/threads/{thread_id}/runs/stream
{
  "assistant_id": "agent",
  "command": { "resume": "<human_answer_string>" },
  "stream_mode": ["messages", "updates"]
}
```

`assistant_id` は必須 (LangGraph Server `RunCreateStateful` スキーマ要件)。

## Consequences

### Positive
- Redis/Postgres 不要 → k8s デプロイ単純化
- スマートフォン (Yoro) から非同期で HITL 判断が可能
- LangGraph Server の全 REST API (`/threads`, `/runs/stream`, `/threads/search`) が
  Yoro proxy 経由で利用可能

### Negative / Constraints
- `langgraph dev` は development サーバー。Production 用 `langgraph-api` に移行する場合は
  Redis + Postgres + `LANGGRAPH_RUNTIME_EDITION=community` が再度必要
- inmem チェックポインタ: Pod 再起動でスレッド状態が消える。重要な HITL は
  `LANGGRAPH_CHECKPOINT_URL` (Postgres) を使う場合は `langgraph-checkpoint-postgres` を設定済み

## Key secrets (keychain)

| secret name | keychain service | 用途 |
|---|---|---|
| `HITL_API_KEY` | `etzhayyim.hitl_api_key` | Yoro → Worker bearer token |
| `LANGCHAIN_API_KEY` | k8s secret `terminal-agent-secrets/langchain-api-key` | LangGraph Server x-api-key |
| `TERMINAL_AGENT_URL` | Worker secret | Yoro Worker → terminal-agent upstream |

## Files

```
60-apps/etzhayyim-terminal-agent/
  Dockerfile                    # langgraph dev CMD
  pyproject.toml                # langgraph-cli[inmem]>=0.1.71
  langgraph.json                # {"graphs": {"agent": "terminal_agent.graph:graph"}}
  k8s/
    deployment.yaml             # terminal-agent-server Deployment + Service
    ingress.yaml                # terminal-agent.etzhayyim.com nginx-ingress

60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/
  src/app.ts                    # /api/hitl/* Hono proxy
  svelte/src/
    lib/hitl-store.svelte.ts    # background poller + hitlHeaders()
    routes/tasks/inbox/
      +page.svelte              # HITL decision inbox UI
    lib/components/AppDrawer.svelte  # 意思決定 nav item
    routes/+layout.svelte       # hitl.start()/stop()
```
