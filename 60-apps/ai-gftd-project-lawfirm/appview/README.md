# ai-gftd-project-lawfirm wasm components

## 実装済み components

- `lawfirm-client-mcp-component`
  - `lawfirm.etzhayyim.com` / `lawyer.etzhayyim.com` の `/xrpc` を担当
  - `GET /...` で静的フロント (`svelte/build`) を配信
  - runtime: magatama runtime (performer.Adapter + ClickHouse)
  - XRPC: `gftd.lawfirm.v1.LawfirmService` (62 methods)
  - Go-defined Arrow/Nata schemas: 24 tables (cases, documents, persons, courts, judges, hearings, filings, tasks, etc.)
