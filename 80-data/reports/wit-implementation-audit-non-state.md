# WIT Implementation Audit (Non-state)

Generated: 2026-02-24 07:12:53Z

Excluded: isco, cpc, cofog, isic, states

## Priority
- high: etzhayyim-project-quickwit, etzhayyim-project-scheduler, etzhayyim-project-sheets, etzhayyim-project-collector, etzhayyim-project-projection-operator
- mid: etzhayyim-project-hrse, etzhayyim-project-performer-cloud, etzhayyim-project-wvme, etzhayyim-project-kami
- low: etzhayyim-project-apqc, etzhayyim-project-communities, etzhayyim-project-resources, etzhayyim-project-cards, etzhayyim-project-fleamarket, etzhayyim-project-news, etzhayyim-project-os, etzhayyim-project-web4

## Summary Table
| Project | world.wit(import/exportあり) | unique imports | unique exports | mapped imports | mapped exports | status |
|---|---:|---:|---:|---:|---:|---|
| etzhayyim-project-apqc | 294 | 34 | 25 | 8 | 25 | medium |
| etzhayyim-project-cards | 1 | 1 | 0 | 1 | 0 | high |
| etzhayyim-project-collector | 1 | 1 | 1 | 1 | 1 | high |
| etzhayyim-project-communities | 218 | 1 | 1 | 0 | 1 | medium |
| etzhayyim-project-fleamarket | 1 | 3 | 1 | 0 | 1 | medium |
| etzhayyim-project-hrse | 1 | 0 | 1 | 0 | 1 | high |
| etzhayyim-project-kami | 1 | 0 | 1 | 0 | 0 | low |
| etzhayyim-project-news | 9 | 13 | 1 | 2 | 1 | medium |
| etzhayyim-project-os | 1 | 3 | 0 | 3 | 0 | high |
| etzhayyim-project-performer-cloud | 1 | 0 | 1 | 0 | 1 | high |
| etzhayyim-project-projection-operator | 1 | 2 | 1 | 2 | 1 | high |
| etzhayyim-project-quickwit | 1 | 16 | 1 | 1 | 1 | medium |
| etzhayyim-project-resources | 90 | 1 | 5 | 0 | 5 | medium |
| etzhayyim-project-scheduler | 1 | 1 | 1 | 1 | 1 | high |
| etzhayyim-project-sheets | 1 | 1 | 1 | 1 | 1 | high |
| etzhayyim-project-web4 | 2 | 1 | 1 | 1 | 1 | high |
| etzhayyim-project-wvme | 1 | 0 | 1 | 0 | 1 | high |

## Key Findings
- quickwit is the clearest full implementation (explicit export bindings in code).
- scheduler/sheets/collector/projection-operator show partial import wiring; export side needs explicit binding validation.
- apqc/communities/resources have many WIT declarations but runtime mapping is sparse in sampled main.go paths.
- kami has world export only and no main.go in component directory.

## Execution Notes
- `scheduler-mcp-component` was updated to use explicit MCP JSON-RPC (`tools/call`) for thread sync when `mcp_url` is provided.
- This removes direct dependency on external generated import package paths and keeps the component buildable in this workspace.
- Local verification: `go test ./...` succeeds in `60-apps/etzhayyim-project-scheduler/wasm/scheduler-mcp-component`.
