# Top5 Export Validation

Generated: 2026-02-24

Scope: `quickwit / scheduler / sheets / collector / projection-operator`

## 1) etzhayyim-project-quickwit
- WIT export
  - `export search;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-quickwit/wasm/quickwit-provider-component/wit/world.wit:19)
- Code anchors
  - `search.Exports.UpsertIndex = upsertIndex`
  - `search.Exports.DeleteIndex = deleteIndex`
  - `search.Exports.IngestJSON = ingestJSON`
  - `search.Exports.SearchIndex = searchIndex`
  - `search.Exports.Health = health`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-quickwit/wasm/quickwit-provider-component/main.go:35)
- Verdict: `Implemented`

## 2) etzhayyim-project-scheduler
- WIT export
  - `export etzhayyim:scheduler/scheduler@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-scheduler/wasm/scheduler-mcp-component/wit/world.wit:10)
- Code anchors
  - `schedulerExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> schedulerExportHandlers[name]`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-scheduler/wasm/scheduler-mcp-component/main.go:144)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## 3) etzhayyim-project-sheets
- WIT export
  - `export etzhayyim:sheets/sheets@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-sheets/wasm/sheets-mcp-component/wit/world.wit:10)
- Code anchors
  - `sheetsExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> sheetsExportHandlers[toolName]`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-sheets/wasm/sheets-mcp-component/main.go:72)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## 4) etzhayyim-project-collector
- WIT export
  - `export etzhayyim:intel-collector/collector@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-collector/wasm/resource-collector-component/wit/world.wit:10)
- Code anchors
  - `collectorExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> collectorExportHandlers[name]`
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-collector/wasm/resource-collector-component/main.go:194)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## 5) etzhayyim-project-projection-operator
- WIT export
  - `export etzhayyim:capabilities/capabilities@0.1.0;`
  - [world.wit](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-projection-operator/wasm/projection-manager-mcp-component/wit/world.wit:13)
- Code anchors
  - `capabilitiesExportHandlers` (export interface equivalent binding map)
  - `callTool(...) -> capabilitiesExportHandlers[name]`
  - `actorproxy.CallActorTool(...)` (runtime integration path)
  - [main.go](/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-projection-operator/wasm/projection-manager-mcp-component/main.go:447)
- Verdict: `Implemented (explicit export-equivalent binding path)`

## Notes
- `go test ./...` status:
  - scheduler: pass
  - sheets: setup fail (missing module `github.com/etzhayyim/kyber-erp/packages/wasm/gen/etzhayyim/performer-registry`)
  - collector: setup fail (missing module `github.com/etzhayyim/kyber-erp/packages/wasm/gen/etzhayyim/global-resources`)
  - projection-operator: setup fail (missing module `github.com/etzhayyim/kyber-erp/packages/wasm/gen/etzhayyim/actor-proxy`)
