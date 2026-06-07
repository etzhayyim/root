---
id: actor-cypher-mcp
title: Actor Cypher + MCP Capability Architecture
status: active
doc_type: adr
topic: actor-architecture
authoritative: true
last_verified: 2026-04-06
---

# Actor Cypher + MCP Capability Architecture

**Status**: [IMPLEMENTED] PDS deployed. 1626 Actor nodes live. Tool/ToolGrant seeding pending.

## Decision

Actor DID = Cypher graph node (PDS manages)。App Worker = MCP capability provider (stateless compute)。

```
Before:  1 App Worker = 1 Actor DID + business logic + MCP tools
After:   Actor DID = Cypher graph node (PDS manages)
         App Worker = MCP capability provider (stateless compute)
```

## Architecture

```
                    ┌─────────────────────────────────┐
                    │         Cypher Graph (kagami)    │
                    │                                  │
                    │  (:Actor {did, status})           │
                    │  (:Tool {name, capabilityWorker}) │
                    │  (:ToolGrant {actorDid, toolName})│
                    │                                  │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │         PDS (sole gateway)       │
                    │                                  │
                    │  XRPC: com.etzhayyim.actor.*           │
                    │  XRPC: com.etzhayyim.tool.*            │
                    │  MCP:  /mcp (JSON-RPC 2.0)       │
                    │                                  │
                    └──────────┬──────────────────────┘
                               │ (tool execution only)
                    ┌──────────▼──────────────────────┐
                    │  Capability Workers (MCP servers) │
                    │  Pure tool handlers, no DID mgmt  │
                    └─────────────────────────────────┘
```

## Graph Labels

### Actor

Promoted columns: `did`, `repo`, `status`, `collection`, `updatedAt`.
Non-promoted (in `val`): `nanoid`, `handle`, `projectId`, `displayName`, `description`, `hasWorker`, `createdAt`, `lastHeartbeat`.

```cypher
MERGE (a:Actor {did: "did:web:k3rn5la4.etzhayyim.com"})
SET a.nanoid = "k3rn5la4", a.handle = "k3rn5la4.etzhayyim.com",
    a.status = "active", a.hasWorker = "true", ...
```

### Tool

MCP tool definition. `capabilityWorker` = nanoid of the Worker that serves it.

```cypher
MERGE (t:Tool {name: "news.summarize"})
SET t.description = "Summarize article by URL",
    t.capabilityWorker = "n3ws0001",
    t.inputSchemaJson = '{"type":"object","properties":{"url":{"type":"string"}}}',
    t.status = "active"
```

### ToolGrant

Actor → Tool access (CAN_USE). Vertex with composite key `grantId = actorDid::toolName`.

```cypher
MERGE (g:ToolGrant {grantId: "did:web:k3rn5la4.etzhayyim.com::news.summarize"})
SET g.actorDid = "did:web:k3rn5la4.etzhayyim.com", g.toolName = "news.summarize",
    g.status = "active"
```

## XRPC Endpoints

### Actor (`pds-actor.ts`)

| NSID | Auth | Description |
|---|---|---|
| `com.etzhayyim.actor.create` | required | Create Actor node (Cypher MERGE) |
| `com.etzhayyim.actor.update` | required | Update Actor properties |
| `com.etzhayyim.actor.delete` | required | Archive Actor (status="archived") |
| `com.etzhayyim.actor.get` | public | Get Actor by DID |
| `com.etzhayyim.actor.list` | public | List Actors by status |
| `com.etzhayyim.actor.setStatus` | required | Change Actor status |
| `com.etzhayyim.actor.heartbeatBatch` | required | Batch heartbeat update |
| `com.etzhayyim.actor.grantTool` | required | Grant CAN_USE (ToolGrant) |
| `com.etzhayyim.actor.revokeTool` | required | Revoke ToolGrant |
| `com.etzhayyim.actor.listTools` | public | List granted tools for Actor |
| `com.etzhayyim.actor.migrateBatch` | required | Bulk migration (App → Actor + Tool + ToolGrant) |

### Tool (`pds-actor-tools.ts`)

| NSID | Auth | Description |
|---|---|---|
| `com.etzhayyim.tool.register` | required | Register MCP tool |
| `com.etzhayyim.tool.update` | required | Update tool properties |
| `com.etzhayyim.tool.delete` | required | Delete tool (status="deleted") |
| `com.etzhayyim.tool.get` | public | Get Tool by name |
| `com.etzhayyim.tool.list` | public | List Tools (filter by capabilityWorker/tag) |
| `com.etzhayyim.tool.registerBatch` | required | Batch register tools (capability worker startup) |

## MCP Gateway (`mcp-adapter.ts`)

| Method | Source | Flow |
|---|---|---|
| `tools/list` | Tool graph + ToolGrant | If caller DID: filter by ToolGrant. Else: all active Tools |
| `tools/call` | Tool → capabilityWorker → DISPATCHER | Tool graph lookup → resolve nanoid → proxy to Worker. ToolGrant auth enforced |
| `resources/list` | Actor graph | Active Actor nodes |
| `resources/read` | Actor graph | Single Actor by DID |

## Runtime (`@etzhayyim/kotodama-host-sdk`)

### createCapabilityWorker()

DID management なし。MCP tool handler only。Auto-registers tools via `com.etzhayyim.tool.registerBatch` on first request.

```typescript
export default createCapabilityWorker({
  tools: {
    "summarize": {
      description: "Summarize article by URL",
      inputSchema: { type: "object", properties: { url: { type: "string" } } },
      handler: async (params, ctx) => {
        const rows = await ctx.query("MATCH (a:Article {url: $url}) RETURN a", { url: params.url });
        return { summary: rows[0]?.text ?? "not found" };
      }
    }
  }
});
```

CapabilityContext: `ctx.query()` (Cypher read), `ctx.write()` (record write), `ctx.llm()` (LLM inference), `ctx.env` (raw bindings).

## Heartbeat

PDS cron (`*/5 * * * *`):
1. Worker-backed apps: DISPATCHER POST `/_heartbeat` (sync-registry apps)
2. All Actors: `MATCH (a:Actor {status: "active"}) SET a.lastHeartbeat = now` (Cypher batch)
3. Auto-migrate: App → Actor (batch 0, cron cycle)

## Migration (`pds-migrate-logical.ts`)

`com.etzhayyim.actor.migrateBatch` endpoint. 3 phases:

| Phase | Input → Output | Method |
|---|---|---|
| `actors` | App → Actor | Cypher MERGE via kagami.cypher() |
| `tools` | ActorCapability → Tool | Cypher MERGE via kagami.cypher() |
| `grants` | Actor × Tool → ToolGrant | Cypher MERGE via kagami.cypher() |

```bash
# Run all phases
curl -X POST atproto.etzhayyim.com/xrpc/com.etzhayyim.actor.migrateBatch \
  -H 'X-Kotodama-Verified: true' \
  -d '{"phase":"all","batchLimit":500}'
```

### kagami Query Constraint

kagami transpiles Cypher → B2 SQL. Only promoted columns (`did`, `repo`, `status`, `collection`, `updatedAt`, `val`) are SQL columns. Non-promoted fields (nanoid, handle, etc.) are in `val` — extracted in JS after query.

Actor writes use `kagami.cypher()` (Workers RPC → in-memory CSR) for immediate read-after-write. `ctx.aietzhayyimKagamiCypher()` falls back to B2 SQL which may not have the data yet.

## P9v20 Stability Update (2026-04-06)

PDS hot paths were patched to stop circuit-breaker cascades caused by non-P9v20 query shapes.

### Fixed

- Legacy/non-promoted references removed from hot handlers:
  - `updated_at` / `_updated_at` / `display_name` -> `updatedAt` / `displayName`
  - `projectBound` DB filter removed from Profile list/suggestions (value is in `val`, not promoted)
  - `App.name` lookup replaced by `displayName`/`val` parsing
- `aietzhayyimKagamiCypherCached` parameter handling fixed:
  - when `params` is present, execution now uses diagnose/non-cache path (no param-dropping cache key path)
- Incorrect Cypher aliases fixed in project/convo queries (`RETURN r.rkey` -> correct alias such as `t.rkey`, `m.rkey`)

### Resilience changes

- Fail-fast timeouts introduced on kagami reads to avoid 12-20s endpoint stalls.
- `getAuthorFeed` now avoids slow fallback chaining and uses bounded vanity-DID resolution.
- `getProfile` aggregate subqueries are soft-timeboxed so profile core fields still return quickly.

### Measured behavior after deploy (2026-04-06)

- `app.bsky.actor.getProfile?actor=did:web:shinka.etzhayyim.com`
  - stable `HTTP 200`, ~`1.27s`-`1.32s` over repeated runs
- `app.bsky.feed.getAuthorFeed?actor=did:web:shinka.etzhayyim.com&limit=10`
  - stable `HTTP 200`, typically ~`2.24s`-`2.31s` after warmup
  - no 12-20s timeout behavior observed in the final verification batch

## CLI: `etzhayyim actors shinka`

Local LLM (Ollama gemma3:4b) で Actor の domain knowledge を agentic に生成。詳細: `70-tools/etzhayyim/CLAUDE.md` §etzhayyim actors shinka

```bash
etzhayyim actors shinka --limit 50 --concurrency 4    # 実行
etzhayyim actors shinka --dry-run --limit 3 --json     # dry-run
etzhayyim actors shinka --filter handotai --limit 1    # 特定 actor
```

## Current State (2026-04-05)

| Item | Count | Status |
|---|---|---|
| Actor nodes | 3468+ | 1626 migrated + sub-DIDs from shinka |
| Tool nodes | 1626 | migrated via migrateBatch |
| ToolGrant nodes | 1626 | migrated via migrateBatch |
| account-level Workers | 26 | active |
| sync-registry | 26 | cleaned (from 567) |
| shinka (running) | 1626 target | ~8 sub-DIDs + ~16 knowledge edges / actor |
| PDS deploy | live | admin repo skip enabled |

## Files

| File | Role |
|---|---|
| `infra/.../pds-actor.ts` | Actor CRUD (10 XRPC + migrateBatch) |
| `infra/.../pds-actor-tools.ts` | Tool registry (6 XRPC) |
| `infra/.../mcp-adapter.ts` | MCP gateway (Tool graph + ToolGrant auth) |
| `infra/.../pds-migrate-logical.ts` | Bulk migration (3 phases) |
| `infra/.../pds-app.ts` | Heartbeat cron (Actor label batch + autoMigrate) |
| `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/index.ts` | `createCapabilityWorker()` |
| `70-tools/etzhayyim/actors_shinka.go` | `etzhayyim actors shinka` — Ollama agentic domain knowledge |

## Deleted

| File | Reason |
|---|---|
| `pds-logical-actor.ts` | Replaced by `pds-actor.ts` (Actor label) |
