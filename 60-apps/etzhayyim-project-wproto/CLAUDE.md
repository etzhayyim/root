# ai-gftd-project-wproto — W Protocol Documentation Site (UI-Only)

## CRITICAL: UI-Only — Data Access via atproto.gftd.ai

→ `gftd dodaf tv1 query --id ai-gftd-project-wproto-ui-only-data-access-via-pds-gftd-ai` / MCP `gftd.dodaf.tv1.query`

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `wpr0t0c1` |
| **domain** | `wproto.gftd.ai` |
| **performer_id** | `wpr0t0c1` |
| **AT bot DID** | `did:web:wproto-wpr0t0c1.gftd.ai` |
| **Runtime** | Worker WASM (DEFAULT) |
| **UI mode** | iframe (SSR) |

## Purpose

W Protocol (`10-protocol/wproto`) の設計・仕様・アーキテクチャを公開するドキュメントサイト。**UI (SSR) のみ。** data endpoint なし。

- AT Protocol 100% coverage (35/35 XRPC)
- Signal Protocol 100% coverage (16/16 features)
- Matrix Protocol 90% parity (46/51 features)
- MDAG content-addressed sync
- WIT interface definitions
- Component Composition (cross-app WIT calls)

## Architecture

```
Request → CF Single Worker (src/app.ts)
  ├─ Static assets (has .)  → Workers Assets (svelte/build/)
  ├─ HTML pages (no .)      → Hono router (host-sdk, Svelte CSR)
  └─ /xrpc/*                → sdk.handleRequest()
```

## Data Model (SQL Graph)

### `WProtoDoc`

| Column | Type | Description |
|---|---|---|
| `doc_id` | string | Primary key (slug) |
| `section` | string | `overview` / `at-protocol` / `signal` / `matrix` / `mdag` / `wit` / `composition` / `architecture` |
| `title` | string | Section title |
| `content` | string | Markdown content |
| `order_idx` | int | Display order |
| `org_id` | string | RLS |
| `user_id` | string | RLS |
| `actor_id` | string | RLS |
