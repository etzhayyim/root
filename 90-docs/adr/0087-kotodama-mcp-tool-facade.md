---
id: adr-0087-kotodama-mcp-tool-facade
title: kotodama per-actor MCP tool facade (Hono Streamable HTTP)
status: proposed
doc_type: adr
topic: mcp-tool-facade
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - per-actor-mcp-endpoint
  - llm-agent-tool-discovery
  - asagenttool-external-exposure
related:
  - 90-docs/adr/0004-write-only-derived-architecture.md
  - 90-docs/adr/0005-shannon-redundancy-prohibition.md
  - 90-docs/adr/0022-auth-topology-consolidation.md
  - 90-docs/adr/0023-auth-shannon-optimal-4-layer.md
  - 90-docs/adr/0036-worker-direct-hyperdrive-persistence.md
  - 90-docs/260413-agent-loop-unification-path-analysis.md
  - adr-2604261000-mcp-registry-via-kysely-schema
supersedes: []
superseded_by: []
amended_by:
  - adr-2604261000-mcp-registry-via-kysely-schema  # §D3 codegen → Kysely registry
---

> **Amendment 2026-04-25 (ADR-2604261000)**: §D3 (`gen-tool-manifest.mjs`
> codegen) is replaced by a runtime Kysely registry (`vertex_mcp_tool_def` +
> `sync-mcp-registry.py`). §D1 per-actor `/mcp`, §D2 OpenAPI, §D4
> `mcpFacade` flag are unchanged in shape; `mcpFacade` gains a sibling
> `mcpRegistry` opt-in that wins when both are passed. New actors should
> default to `mcpRegistry`. See ADR-2604261000 for migration plan.

# Context

kotodama actor の CF Worker (T3 TS Native, F-Plan 2026-04-13) は command を `sdk.app.command(nsid, handler, asAgentTool("..."), ...)` で宣言し、`CommandEntry.agentToolDesc` → `buildActorCardFromCommands()` → `ActorCard.tools[]` 経由で **PDS governance manifest に登録、`mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` の単一 MCP endpoint で全 actor 分を合成公開** している。

これには 3 つの問題がある:

1. **scope が PDS 集約**: LangGraph / OpenAI Apps SDK / Claude Desktop 等の外部 LLM agent は actor 単位で tool scope を切りたい (例: lawfirm actor の tool だけを bind)。現状は全 actor tool を 1 endpoint で混ぜて公開しており、per-actor 切り出しは client 側 filter に頼る。
2. **discovery 規格の不在**: AtProto XRPC 仕様は service discovery を定義していない (*"there is not yet a consistent way to enumerate which endpoints do or do not"* — atproto.com/specs/xrpc)。AT-native client は lexicon JSON をビルド時取り込みで解決するが、LLM agent は runtime discovery を必要とする。
3. **2026 年事実上標準との乖離**: LLM agent tool exposure は **MCP (Model Context Protocol)** に収束した。Anthropic (origin) / OpenAI Apps SDK / LangGraph Server / Claude Code / Cursor が `/mcp` Streamable HTTP endpoint を採用。OpenAI Assistants API は 2026-08-26 終了、Responses API + MCP へ移行。repo も既に `com.etzhayyim.mcp.message` NSID と `mcp.etzhayyim.com/mcp` connector endpoint を持つが、per-actor Worker 側には MCP server 実体が無い。

5 プロトコル比較:

| プロトコル | path 規約 | discovery | 2026 採用 |
|---|---|---|---|
| MCP | `/mcp` (single endpoint, JSON-RPC over HTTP+SSE) | `tools/list` method | Anthropic, OpenAI Apps SDK, LangGraph, Claude Code, Cursor |
| OpenAI native function calling | 無し (tools inline in request body) | client-declared | — (server path 問題ではない) |
| Anthropic native tool use | 無し (tools inline, JSON Schema 2020-12 必須) | client-declared | — |
| GPT Actions / ChatGPT Plugins | `/.well-known/ai-plugin.json` + `/.well-known/openapi.yaml` | OpenAPI spec | Custom GPTs (Plugin は deprecated) |
| OpenAPI + LangChain OpenAPIToolkit | 任意 (`/openapi.json` 慣習) | OpenAPI spec | 汎用 fallback |

# Decision

kotodama host-sdk に **2 つの加法的 Hono サブアプリ**を追加する。XRPC (`/xrpc/:nsid`) は完全に無変更で残す (AT-native client 向け、ADR-0022 Service Auth 経路のまま)。

## D1. Per-actor MCP server at `/mcp`

各 kotodama actor Worker に **MCP Streamable HTTP endpoint** を実装:

- `POST /mcp` — JSON-RPC 2.0 message (Accept: `application/json, text/event-stream`)
- `GET /mcp` — SSE stream open (server→client push。長期 stream 不要な call は 405 を返しても spec 準拠)
- JSON-RPC methods: `initialize`, `tools/list`, `tools/call`, `ping`
- `tools/list` は `CommandEntry[]` を列挙。`tools/call` は既存 `app.handleXRPC(nsid, args)` に delegate — **新規 dispatch 経路を作らない** (ADR-0005)

認証: `Authorization: Bearer <ES256 Service Auth JWT>`。既存 `10-protocol/xrpc/src/ServiceAuth` (ADR-0022 SSoT) を Hono middleware にラップして使う。`hono/jwt` は使わない (ES256 public-key サポートが公式 docs 上未文書化)。`lxm` claim は `tools/call` の tool name (NSID に逆変換) と一致検証。

Path F middleware (memory / consent / audit / scheduler, 260413) は `handleXRPC` 経由で自動適用。**MCP は agent loop の 6 番目の entry point** として Path F の外延となる。

## D2. OpenAPI 3.0 spec at `/.well-known/openapi.json`

GPT Actions / LangChain OpenAPIToolkit / 汎用 REST client 向け補助経路。`@hono/zod-openapi` を使って lexicon から生成。

- `GET /.well-known/openapi.json` — OpenAPI 3.0.0 JSON
- `GET /.well-known/openapi/docs` — Swagger UI (dev profile のみ)
- GPT Actions 経由で公開する actor は同時に `/.well-known/ai-plugin.json` も出す (optional)

OpenAPI 3.0 は Hono `@hono/zod-openapi` の現行 default。Lexicon は JSON Schema 2020-12 寄りなので 3.0-safe subset に projection する (`$defs` → `definitions`, `examples` → `example`)。Lexicon が SSoT、OpenAPI は派生 artifact。

## D3. Codegen pipeline

Lexicon → Zod + MCP tool manifest を単一 codegen で出す:

```
00-contracts/lexicons/com/etzhayyim/apps/**/*.json
  └─ (existing) gen-service-from-lexicon.mjs → service-generated.ts     (XRPC path)
  └─ (NEW)      gen-tool-manifest.mjs        → tool-manifest.ts
                                              ├─ Zod schemas per NSID
                                              ├─ OpenAPI route defs (@hono/zod-openapi createRoute)
                                              └─ MCP tool entries ({name, description, inputSchema})
```

**NSID ↔ MCP tool name 規約**: MCP tool name = NSID そのまま (`com.etzhayyim.apps.lawfirm.createCase`)。一部 client が `.` を受け付けない場合は `_` 置換を client 側責務とする (server 側は SSoT 維持)。

## D4. `kotodama.jsonld` flag

新規 field `mcpFacade: { enabled: boolean, scope?: "actor" | "project" }` を追加。default `enabled: true`。`enabled: false` の actor は従来通り PDS 集約 MCP のみ。

# Consequences

**Positive:**
- LangGraph / OpenAI Apps SDK / Claude Desktop が **per-actor で kotodama の tool を bind できる**。scope の最小化 = Shannon η 向上。
- MCP が 2026 年の de facto standard なので、外部 agent ecosystem 連携が **protocol 追加なしで完成**。
- 既存 `asAgentTool` / lexicon / XRPC dispatch は全て流用 (ADR-0005 遵守、新 SSoT ゼロ)。
- Path F middleware (consent/audit) が外部 LLM call にも自動適用される (governance の漏れが発生しない)。
- Service Auth JWT の `lxm` claim が tool name と強制一致 → tool ごとの最小 scope auth が spec 準拠で実現。

**Neutral:**
- bundle size +~40KB (MCP JSON-RPC layer + `@hono/zod-openapi` + generated schemas)。10MB 制限に対して誤差。
- OpenAPI 3.0 出力は Lexicon JSON Schema 2020-12 の lossy projection。Lexicon が SSoT なので実害なし、client が 2020-12 構造 (nested `$defs` 等) を要求する場合のみ限界。

**Risks / migration notes:**
- MCP SSE stream を長期保持する client は CF Worker 実行時間制約 (30s default, 15min paid) の影響を受ける。tool call は単発 request/response なので影響小。subscribe 系の将来機能は DO に逃がす。
- `mcp.etzhayyim.com/mcp` 集約 endpoint と per-actor `/mcp` が並存。両者は同じ tool 集合の 2 scope (all-actor vs per-actor) を出す。consumer 側で**どちらを指すかを明示**させる (例: Claude connector は集約、LangGraph は per-actor)。
- codegen 追加は CI で `gen-tool-manifest.mjs` 実行を `gen-service-from-lexicon.mjs` と同 step にまとめる。build 時間 +~2s/actor。

# Alternatives Considered

| Option | Why not |
|---|---|
| **独自 `/tools` REST path** | どの標準にも含まれない独自命名。LLM agent ecosystem の既存 client 対応がゼロ。ADR-0005 の SSoT 増加に当たる |
| **XRPC のみ (MCP facade 作らず)** | AtProto XRPC spec に service discovery が無い。LLM agent は runtime で tool 列挙できず、実質使えない |
| **PDS 集約 `com.etzhayyim.mcp.message` を per-actor scope 拡張** | scope param で filter する設計は可能だが、(a) endpoint が actor 位置と乖離、(b) governance manifest が単一 PDS worker に集中する SPoF、(c) ADR-0036 の worker-direct 方針と逆行 |
| **GPT Actions の `/.well-known/ai-plugin.json` のみ** | OpenAI custom GPTs 専用。Claude / LangGraph / Cursor は読めない |
| **WIT + wasmtime (T3 Container) 経由** | T3 TS Native (DEFAULT) では WIT は design-time contract 扱いで runtime 未使用 (F-Plan 2026-04-13)。Container 化は 128MB 超過 actor 限定で、一般 actor に強制する妥当性なし |
| **`hono/jwt` で ES256 bearer を検証** | 公式 docs が `secret: string` 例のみ。ES256 asymmetric の公開鍵 (JWK/PEM) 渡しが未文書化。既存 `ServiceAuth` (ADR-0022 SSoT) を流用した方が安全かつ重複ゼロ |
| **OpenAPI 3.1 で出す** | `@hono/zod-openapi` 現行 default は 3.0.0。3.1 対応を先行するコストに対し、LangChain OpenAPIToolkit / GPT Actions consumer は 3.0 で十分 |

# References

- atproto XRPC spec — https://atproto.com/specs/xrpc (service discovery 不在の根拠)
- MCP Streamable HTTP transport spec — https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- LangGraph Server MCP endpoint — https://docs.langchain.com/langgraph-platform/server-mcp
- OpenAI Apps SDK MCP server — https://developers.openai.com/apps-sdk/concepts/mcp-server
- Anthropic tool use (JSON Schema 2020-12 要件) — https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use
- Hono `@hono/zod-openapi` — https://hono.dev/examples/zod-openapi
- GPT Actions — https://platform.openai.com/docs/actions/introduction
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/app-metadata.ts` — `buildActorCardFromCommands()` (tool export SSoT)
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/host-web-router.ts` — Hono router 現行 12 ルート
- `10-protocol/xrpc/src/ServiceAuth` — ES256 検証 SSoT (ADR-0022)
- `70-tools/scripts/contract/gen-service-from-lexicon.mjs` — 既存 codegen の姉妹 pipeline
- 260413 Path F 分析 — agent loop 5 entry point 統合 (MCP は 6 番目 entry として外延)
