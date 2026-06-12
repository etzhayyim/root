---
id: adr-2605082002-mcp-tool-registry-resolution
renumbered_from: "2605082000"
title: "ADR-2605082002: MCP Tool Registry Resolution — mcp://<nsid> in LangGraph node bindings"
status: active
doc_type: adr
topic: mcp-tool-registry-resolution
authoritative: true
last_verified: 2026-05-08
priority: 7.5
axis: architecture
weight: 0.80
priority_note: "How LangGraph row-driven nodes address MCP tools by NSID, resolving the actor_host endpoint at runtime via vertex_mcp_tool_def."
authoritative_for:
  - mcp:// URI scheme in vertex_langgraph_assistant_node.ref
  - vertex_mcp_tool_def runtime lookup contract (SELECT actor_host WHERE nsid AND enabled)
  - MCP envelope endpoint construction (https://{actor_host}/xrpc/com.etzhayyim.mcp.message)
  - tools/call default name = nsid
  - In-process TTL cache (60s) for registry hits
depends_on:
  - adr-2605082200-langgraph-single-task-and-row-driven-runtime
  - adr-2604261000-mcp-registry-via-kysely-schema
related:
  - adr-0087-kotodama-mcp-tool-facade
supersedes: []
superseded_by: []
---

# ADR-2605082002: MCP Tool Registry Resolution

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki

## Context

ADR-2604261000 made `vertex_mcp_tool_def` the SSoT for the MCP tool registry
(NSID → actor_host + lexicon I/O schemas, populated by `sync-mcp-registry.py`
from `00-contracts/lexicons/com/etzhayyim/apps/**/*.json`).

ADR-2605082200 introduced row-driven LangGraph assistants where each node's
`ref` column is a string. The resolver dispatch in
`langgraph_node_resolvers.py` already supported `mcp_tool` nodes whose `ref`
was a literal HTTP URL, but that violated the platform’s NSID-first identity
rule — every node binding hard-coded a hostname, defeating the actor-host
indirection that `vertex_mcp_tool_def` exists to provide.

This ADR fixes that: a node binding can declare `kind=mcp_tool` with
`ref="mcp://com.etzhayyim.tools.web.research"` and the loader resolves the
endpoint at runtime via `vertex_mcp_tool_def`.

## Decision

### D1. `mcp://<nsid>` URI scheme on node `ref`

When `vertex_langgraph_assistant_node.ref` starts with `mcp://`, the
remainder is parsed as a fully-qualified MCP tool NSID. Resolution rules:

```
ref = "mcp://com.etzhayyim.tools.web.research"
  └─ nsid = "com.etzhayyim.tools.web.research"

SELECT actor_host FROM vertex_mcp_tool_def
WHERE nsid = $1 AND enabled = true
LIMIT 1

endpoint = "https://{actor_host}/xrpc/com.etzhayyim.mcp.message"
tools/call body.name = nsid
```

Empty NSID (`mcp://`) raises `ValueError: nsid is empty`. Unknown or
`enabled=false` rows raise `ValueError: mcp_tool: unknown or disabled nsid`.

### D2. Pool factory dependency

Resolution requires the same `pool_factory` already threaded through
`_compile_topology` for `kind=sql_udf` / `py_ext_udf`. A `mcp_tool` node
created without `pool_factory` raises `ValueError: pool_factory required`
at compile time, not runtime — fail-fast on row author error.

Literal HTTP URLs (`https://...`) continue to work without `pool_factory`
for backwards compatibility, but new bindings MUST use `mcp://<nsid>`.

### D3. In-process TTL cache (60s)

```python
_MCP_REGISTRY_CACHE: dict[str, tuple[str, float]] = {}  # nsid → (actor_host, expires_at)
_MCP_REGISTRY_TTL_S = 60.0
```

Cache hit skips the SELECT entirely. Cache is invalidated by:

- TTL expiry (60s passive)
- Pod restart (in-memory dict)
- `vertex_mcp_tool_def.actor_host` change is **not** auto-detected — the
  next `mcp_tool` node invocation after TTL expiry picks up the new value.

A bypass for sub-60s rotation is not provided; if the actor_host of an MCP
tool changes, accept up to 60s of stale dispatch (each call is independent;
no in-flight state to migrate).

### D4. Default tools/call envelope

```json
{
  "method": "tools/call",
  "params": {
    "name": "<nsid>",                             // default — overridable via config.args.name
    "arguments": { "<input_keys[i]>": <state[k]> }
  }
}
```

Using the NSID itself as `tools/call.name` is the canonical convention —
matches what `host-sdk` MCP adapter dispatches when an app declares
`asAgentTool` (per ADR-0087). Authors who need to call a different tool on
the same MCP server may override via `config.args.name`.

### D5. Header injection

`config.args.headers` merges into the POST headers. `content-type:
application/json` is set by default. No automatic auth header injection —
the row author is responsible for the trust boundary (typically
`x-internal-trust: <secret>` on K8s-internal traffic, or proper OAuth on
public endpoints).

## Test coverage

Hermetic tests in `tests/test_langgraph_node_resolvers_pure.py`:

- `test_mcp_tool_registry_ref_requires_pool_factory` — compile fails when
  `mcp://` ref has no pool_factory.
- `test_mcp_tool_registry_ref_empty_nsid_rejected` — `mcp://` with no nsid.
- `test_mcp_tool_registry_ref_resolves_via_vertex_mcp_tool_def` — happy
  path: SELECT returns actor_host, endpoint built correctly, second
  invocation hits TTL cache (asserts `execute.await_count == 1`).

## Consequences

**Gained**:
- Row authors reference MCP tools by NSID, not hostname. Moving an MCP
  service to a new actor_host = `UPDATE vertex_mcp_tool_def`, no row
  rewrite.
- Disable a tool platform-wide via `vertex_mcp_tool_def.enabled = false`;
  all bindings that resolve it raise at next invocation.
- Per-actor binding tables stay clean: `ref` is a stable identifier, not a
  URL that rots.

**Constraints**:
- Up to 60s lag on registry changes (TTL).
- `vertex_mcp_tool_def` row deletion mid-graph-run produces clean
  `ValueError` from the resolver, surfaced to the LangGraph node — the
  graph’s error handling decides what to do (retry, fallback, fail).
- Resolution is per-call, not per-graph-compile; this means `_compile_topology`
  doesn’t need to reach the network or DB for `mcp_tool` nodes (it just
  builds the closure). Compile remains cheap.

## References

- ADR-2605082200: Row-driven LangGraph runtime (parent)
- ADR-2604261000: MCP tool registry as Kysely schema (`vertex_mcp_tool_def`)
- ADR-0087: kotodama MCP tool facade
- Implementation: `kotodama/langgraph_node_resolvers.py:make_mcp_tool_node`
- Migration `r_20260509170000_topology_saikin_cycle_v2_mcp` exercises the
  full path (saikin's MCP tool calls resolve via this scheme).
