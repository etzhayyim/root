# WIT Implementation Audit (Non-state)

Generated: 2026-02-24 07:12:53Z

Excluded: isco, cpc, cofog, isic, states

## Priority
- high: ai-gftd-project-quickwit, ai-gftd-project-scheduler, ai-gftd-project-sheets, ai-gftd-project-collector, ai-gftd-project-projection-operator
- mid: ai-gftd-project-hrse, ai-gftd-project-performer-cloud, ai-gftd-project-wvme, ai-gftd-project-kami
- low: ai-gftd-project-apqc, ai-gftd-project-communities, ai-gftd-project-resources, ai-gftd-project-cards, ai-gftd-project-fleamarket, ai-gftd-project-news, ai-gftd-project-os, ai-gftd-project-web4

## Summary Table
| Project | world.wit(import/exportあり) | unique imports | unique exports | mapped imports | mapped exports | status |
|---|---:|---:|---:|---:|---:|---|
| ai-gftd-project-apqc | 294 | 34 | 25 | 8 | 25 | medium |
| ai-gftd-project-cards | 1 | 1 | 0 | 1 | 0 | high |
| ai-gftd-project-collector | 1 | 1 | 1 | 1 | 1 | high |
| ai-gftd-project-communities | 218 | 1 | 1 | 0 | 1 | medium |
| ai-gftd-project-fleamarket | 1 | 3 | 1 | 0 | 1 | medium |
| ai-gftd-project-hrse | 1 | 0 | 1 | 0 | 1 | high |
| ai-gftd-project-kami | 1 | 0 | 1 | 0 | 0 | low |
| ai-gftd-project-news | 9 | 13 | 1 | 2 | 1 | medium |
| ai-gftd-project-os | 1 | 3 | 0 | 3 | 0 | high |
| ai-gftd-project-performer-cloud | 1 | 0 | 1 | 0 | 1 | high |
| ai-gftd-project-projection-operator | 1 | 2 | 1 | 2 | 1 | high |
| ai-gftd-project-quickwit | 1 | 16 | 1 | 1 | 1 | medium |
| ai-gftd-project-resources | 90 | 1 | 5 | 0 | 5 | medium |
| ai-gftd-project-scheduler | 1 | 1 | 1 | 1 | 1 | high |
| ai-gftd-project-sheets | 1 | 1 | 1 | 1 | 1 | high |
| ai-gftd-project-web4 | 2 | 1 | 1 | 1 | 1 | high |
| ai-gftd-project-wvme | 1 | 0 | 1 | 0 | 1 | high |

## Key Findings
- quickwit is the clearest full implementation (explicit export bindings in code).
- scheduler/sheets/collector/projection-operator show partial import wiring; export side needs explicit binding validation.
- apqc/communities/resources have many WIT declarations but runtime mapping is sparse in sampled main.go paths.
- kami has world export only and no main.go in component directory.

## Execution Notes
- `scheduler-mcp-component` was updated to use explicit MCP JSON-RPC (`tools/call`) for thread sync when `mcp_url` is provided.
- This removes direct dependency on external generated import package paths and keeps the component buildable in this workspace.
- Local verification: `go test ./...` succeeds in `60-apps/ai-gftd-project-scheduler/wasm/scheduler-mcp-component`.
