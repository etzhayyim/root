# Global Project MCP Tools

Endpoint: `POST /api/mcp` (JSON-RPC 2.0)

Supported methods:
- `tools/list` (alias: `list_tools`)
- `tools/call` (alias: `call_tool`)

## Envelope

Request:
```json
{
  "jsonrpc": "2.0",
  "id": "any",
  "method": "tools/call",
  "params": {
    "name": "global.list_resources",
    "arguments": {}
  }
}
```

Response (success):
```json
{
  "jsonrpc": "2.0",
  "id": "any",
  "result": {}
}
```

Response (tool error):
```json
{
  "jsonrpc": "2.0",
  "id": "any",
  "error": {
    "code": -32000,
    "message": "..."
  }
}
```

## Tools

### `global.list_resources`
List known global resources.

Arguments: none

Result: `Resource[]`
- `id` string
- `name` string
- `type` string
- `unit` string
- `description` string

Example:
```bash
curl -sS -X POST http://localhost:8080/api/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"global.list_resources","arguments":{}}}' | jq
```

### `global.list_flows`
List resource flows. Filter by `resource_id` and/or `year` when provided.

Arguments:
- `resource_id` string (optional)
- `year` integer (optional)

Result: `ResourceFlow[]`
- `id` string
- `resourceId` string
- `sourceRegion` string
- `targetRegion` string
- `year` number
- `volume` number
- `value` number

### `global.get_resource_stats`
Get region stats for a resource.

Arguments:
- `resource_id` string (required)

Result: `RegionStats[]`
- `regionId` string
- `regionName` string
- `year` number
- `production` number
- `consumption` number
- `export` number
- `import` number
- `reserve` number
- `lat` number
- `lng` number

### `global.get_graph`
Graph data for 3D graph view for a resource and year.

Arguments:
- `resource_id` string (optional; defaults to `crude-oil`)
- `year` integer (optional; defaults to `2023`)

Result: `GraphData`
- `nodes` GraphNode[]
- `edges` GraphEdge[]

### `global.get_timeline`
Year-indexed timeline for a resource.

Arguments:
- `resource_id` string (optional; defaults to `crude-oil`)

Result: `TimelineEntry[]`
- `year` number
- `data` RegionStats[]

### `global.list_cofog_actors`
List COFOG actor endpoints integrated into this global MCP component.

Arguments: none

Result: `CofogActor[]`
- `id` string
- `code` string
- `name` string
- `description` string
- `mcpUrl` string

### `global.get_cofog_status`
Get COFOG workflow status from a selected actor.

Arguments:
- `actor_id` string (required unless querying all actors is explicitly requested)
- `execution_id` string (optional, exact workflow execution lookup)

Result:
- single actor: `CofogStatusSummary`
- all actors: `CofogStatusSummary[]`

### `global.get_cofog_overview`
Get COFOG status summary across all actors for dashboard-level visualization.

Arguments: none

Result: `CofogOverview`
- `actors` `CofogStatusSummary[]`
- `totals` `Record<string, number>` (aggregated status counts)
- `count` number
- `updatedAt` string (RFC3339)

### `global.list_systems`
List available system models (index).

Arguments: none

Result: `{id: string, name: string}[]`

### `global.get_system`
Fetch a full systems-thinking model.

Arguments:
- `system_id` string (required)

Result: `SystemModel`
- `id` string
- `name` string
- `nodes` SystemNode[]
- `edges` SystemEdge[]

## Implementation References

- Backend MCP handler: `60-apps/etzhayyim-project-global/wasm/global-ui-w5n8p3q6/global-mcp-routes.go`
- Frontend MCP client: `60-apps/etzhayyim-project-global/wasm/global-ui-w5n8p3q6/svelte/src/lib/api/mcp.ts`

## Local Dev

Start the backend with an in-memory App state store:
```bash
60-apps/etzhayyim-project-global/legacy-runtime/run_local_global_app.sh
```

Smoke test:
```bash
60-apps/etzhayyim-project-global/legacy-runtime/smoke_mcp.sh | jq
```

For the UI, set `VITE_API_BASE` to point at the backend (example: `http://localhost:18080`).
Default local backend port is `18080` (override with `PORT=...`).
