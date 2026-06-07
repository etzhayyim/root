---
id: adr-2605210000-search-etzhayyim-ai-internal-only
title: "search.etzhayyim.com = internal-only; 外部 DNS ルート削除"
status: active
doc_type: adr
topic: search-worker-internal-only
authoritative: true
last_verified: 2026-05-21
phase_status: "Done 2026-05-21 — wrangler.toml workers_dev=false + routes 削除 + magatama.jsonld joinRule=invite"
priority: 6.0
axis: architecture
weight: 0.70
priority_note: "search.etzhayyim.com は CF Service Binding / MCP facade 経由の internal アクセスのみ許可。外部 HTTP 公開禁止。"
authoritative_for:
  - search-worker-public-access-prohibition
  - search-etzhayyim-ai-internal-only
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2604282300
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
supersedes: []
superseded_by: []
amends: []
amended_by: []
---

# Goal

`search.etzhayyim.com` CF Worker を **外部非公開 (internal-only)** にする。
公開 DNS ルートと `workers.dev` URL を削除し、同 Worker は CF Service Binding および
`mcp.etzhayyim.com/mcp` MCP facade 経由の内部呼び出しのみ受け付ける。

# Context

`magatama.jsonld` の `governance.classification` はすでに `"internal"` であったが、
`wrangler.toml` に `workers_dev = true` と `routes = [{ pattern = "search.etzhayyim.com/*" }]` が
存在し、実際には外部から HTTP で直接到達可能な状態だった。

2026-05-09 の `chat-search-kotoba-only` 変更で `tool_web_search` を Kotoba/Datomic 内部検索に
一本化したことで、`search.etzhayyim.com` への外部 HTTP アクセスを必要とするクライアントは存在しなくなった。
また MCP as Cell Membrane (ADR-2605091400) により、外部向け API は `mcp.etzhayyim.com/mcp` MCP facade に
集約する方針が確定している。

# Decision

1. **`workers_dev = false`** — `*.workers.dev` URL を無効化する。
2. **`routes` 削除** — `search.etzhayyim.com/*` の CF DNS ルートを削除する。Worker は CF ダッシュボード上に
   存在するが外部 HTTP エンドポイントを持たない。
3. **`space.joinRule = "invite"`** — Space への参加を招待制に変更し、公開ディスカバリーを遮断する。

# Access pattern after this ADR

| 呼び出し元 | 方法 | 許可 |
|---|---|---|
| 内部 CF Worker (PDS / dispatcher) | CF Service Binding | ✅ |
| K8s pod / LangServer | XRPC `com.etzhayyim.apps.search.*` via dispatcher | ✅ |
| 外部クライアント | `mcp.etzhayyim.com/mcp` MCP tool 経由 | ✅ (MCP facade が auth gate) |
| 外部クライアント | `search.etzhayyim.com` 直接 HTTP | ❌ 禁止 |
| `*.workers.dev` URL | — | ❌ 無効化 |

# Files Changed

```
60-apps/etzhayyim-project-search/appview/search-mcp-component/wrangler.toml
  workers_dev: true → false
  routes: [{ pattern = "search.etzhayyim.com/*", zone_name = "etzhayyim.com" }] → 削除

60-apps/etzhayyim-project-search/appview/search-mcp-component/magatama.jsonld
  space.joinRule: "public" → "invite"
```

# Consequences

- `etzhayyim deploy` 後に CF DNS の `search.etzhayyim.com` A/CNAME レコードは自動削除される。
- 既存の `atproto.etzhayyim.com` gateway に `WORKER_SEARCH` binding が未登録のため、
  `atproto` 経由での search XRPC ルートも存在せず、機能影響はない。
- search 機能は `chat-agent` pod の `tool_web_search` が Kotoba/Datomic 経由で提供しており、
  外部公開 Worker がなくても検索品質に影響しない。
- 将来 search を外部公開する場合は `mcp.etzhayyim.com/mcp` MCP tool として公開し、
  Worker への直接 HTTP ルートは設けない (ADR-2605091400)。
