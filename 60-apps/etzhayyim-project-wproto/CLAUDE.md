# etzhayyim-project-wproto — W Protocol Documentation Site (UI-Only)

## CRITICAL: UI-Only — Data Access via atproto.etzhayyim.com

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-wproto-ui-only-data-access-via-pds-etzhayyim-ai` / MCP `etzhayyim.dodaf.tv1.query`

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `wpr0t0c1` |
| **domain** | `wproto.etzhayyim.com` |
| **performer_id** | `wpr0t0c1` |
| **AT bot DID** | `did:web:wproto-wpr0t0c1.etzhayyim.com` |
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
