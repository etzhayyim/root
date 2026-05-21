# Top5 Export Validation

Generated: 2026-02-24

Scope: `quickwit / scheduler / sheets / collector / projection-operator`

## 1) ai-gftd-project-quickwit
- WIT export
  - `export search;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-quickwit/wasm/quickwit-provider-component/wit/world.wit:19)
- Code anchors
  - `search.Exports.UpsertIndex = upsertIndex`
  - `search.Exports.DeleteIndex = deleteIndex`
  - `search.Exports.IngestJSON = ingestJSON`
  - `search.Exports.SearchIndex = searchIndex`
  - `search.Exports.Health = health`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-quickwit/wasm/quickwit-provider-component/main.go:35)
- Verdict: `Implemented`

## 2) ai-gftd-project-scheduler
- WIT export
  - `export gftd:scheduler/scheduler@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-scheduler/wasm/scheduler-mcp-component/wit/world.wit:10)
- Code anchors
  - `schedulerExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> schedulerExportHandlers[name]`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-scheduler/wasm/scheduler-mcp-component/main.go:144)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## 3) ai-gftd-project-sheets
- WIT export
  - `export gftd:sheets/sheets@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-sheets/wasm/sheets-mcp-component/wit/world.wit:10)
- Code anchors
  - `sheetsExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> sheetsExportHandlers[toolName]`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-sheets/wasm/sheets-mcp-component/main.go:72)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## 4) ai-gftd-project-collector
- WIT export
  - `export gftd:intel-collector/collector@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-collector/wasm/resource-collector-component/wit/world.wit:10)
- Code anchors
  - `collectorExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> collectorExportHandlers[name]`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-collector/wasm/resource-collector-component/main.go:194)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## 5) ai-gftd-project-projection-operator
- WIT export
  - `export gftd:capabilities/capabilities@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-projection-operator/wasm/projection-manager-mcp-component/wit/world.wit:13)
- Code anchors
  - `capabilitiesExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> capabilitiesExportHandlers[name]`
  - `actorproxy.CallActorTool(...)` (runtime integration path)
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/ai-gftd-project-projection-operator/wasm/projection-manager-mcp-component/main.go:447)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## Notes
- `go test ./...` status:
  - scheduler: pass
  - sheets: setup fail (missing module `github.com/etzhayyim/kyber-erp/packages/wasm/gen/gftd/performer-registry`)
  - collector: setup fail (missing module `github.com/etzhayyim/kyber-erp/packages/wasm/gen/gftd/global-resources`)
  - projection-operator: setup fail (missing module `github.com/etzhayyim/kyber-erp/packages/wasm/gen/gftd/actor-proxy`)
