---
id: adr-2605082200-langgraph-single-task-and-row-driven-runtime
title: "ADR-2605082200: LangGraph Row-Driven Runtime — single_task kind, hot-reload watcher, and /registry-source diagnostic"
status: active
doc_type: adr
topic: langgraph-row-driven-runtime
authoritative: true
last_verified: 2026-05-08
priority: 8.0
axis: architecture
weight: 0.85
priority_note: "Completes the migration from in-image LangGraph factories to vertex_langgraph_* row-driven assistant registry. 95% of registered actors (61/64) are pure data."
authoritative_for:
  - LangGraph assistant kind taxonomy: py_factory | topology | single_task
  - kind=single_task semantics (1-node SingleTaskState wrapper, factory_path = task ref)
  - Hot-reload watcher contract (poll vertex_langgraph_deployment.updated_at, lazy fetch, compile-then-swap)
  - /registry-source diagnostic schema (db_loaded / static_filled / watcher.* / errored_assistants[])
  - Two-phase rollout pattern: DB-first + static-fallback → static-disabled → static-removed
  - state_keys requirement on kind=topology rows (TypedDict per-key reducer; bare dict overwrites)
depends_on:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-0036-worker-direct-hyperdrive-persistence
amends:
  - adr-2605080600-langgraph-server-granian-l3-runtime  # introduces row-driven assistant registry as authoritative source
related:
  - adr-2605082000-mcp-tool-registry-resolution        # mcp://<nsid> in node_bindings
  - adr-2605082100-langgraph-checkpointer-mode         # checkpointer_mode column on assistant
supersedes: []
superseded_by: []
---

# ADR-2605082200: LangGraph Row-Driven Runtime

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki

## Context

ADR-2605080600 introduced LangGraph Server + Granian as the L3 virtual actor
runtime. It established `vertex_langgraph_checkpoint` / `_store` / `_run` as
state-only RW tables. Assistant *definitions* (compiled `StateGraph`s registered
under an `assistant_id`) still lived as Python factories in the
`kotodama-server` image: ~64 hand-written `_register_*` calls in
`langgraph_server_app.py:_register_builtin_graphs()`.

That left a structural mismatch with the platform’s "actor-as-data" rule
(ADR-0038): every change to an assistant definition required an image rebuild
+ rolling deploy, even when the change was purely structural (add a node,
swap a router, change an edge target).

This ADR codifies the migration to a row-driven assistant registry, the new
assistant kinds added to support it, and the operational contracts (watcher,
diagnostic) needed to run it safely on prod.

## Decision

### D1. Authoritative assistant registry = `vertex_langgraph_*` rows

`vertex_langgraph_deployment` is the SSoT for *which* assistants are active.
`vertex_langgraph_assistant` is the SSoT for *what* each assistant is.
`vertex_langgraph_assistant_node` is the SSoT for per-node bindings (used by
`kind=topology`).

Pod startup loads via `langgraph_loader.load_active_graphs(...)` which JOINs
deployment+assistant tables and registers each compiled graph into the
in-process `_GRAPH_REGISTRY`. The static `_register_builtin_graphs()` block
is preserved as a no-op fallback for emergency revert (set
`LANGGRAPH_RELOAD_INTERVAL_SEC=0` to disable hot-reload entirely).

### D2. Assistant kind taxonomy

| `kind` | Use | `factory_path` | `spec` | Bindings table |
|---|---|---|---|---|
| `py_factory` | Ad-hoc Runnables / non-`StateGraph` graphs / cross-package factories | dotted path to `build_graph()` (or `module:attr`) | NULL | none |
| `topology`   | Standard LangGraph graphs with declared state schema | NULL | JSON `{state_keys, entry, edges, conditional_edges}` | `vertex_langgraph_assistant_node` (one row per node) |
| `single_task` | One-shot pyzeebe-style task wrapping (kobo/kabi/kinoko/hakkou family) | dotted path to `task_*` coroutine | NULL | none (graph wrapper added internally) |

**Rule**: prefer `topology` whenever a `StateGraph` can be expressed as a row
spec (61/64 builtins meet this). `py_factory` is reserved for genuine
exceptions: graphs that are not `StateGraph`, factories outside
`langgraph_graphs/`, or graphs whose conditional path keys cannot be string-
encoded (e.g. langgraph `END` sentinel as path key).

### D3. `kind=topology` requires `state_keys`

Empirically verified against langgraph 0.2: `StateGraph(dict)` uses an
overwriting reducer; node-return dicts replace the full state on each step.
`StateGraph(TypedDict)` uses a per-key merge reducer, which is what node
implementations expect. The loader synthesizes a dynamic
`TypedDict("_State_<aid>", {k: object for k in state_keys}, total=False)`
from the spec. A topology row with empty `state_keys` is rejected at compile
time (`ValueError: topology spec missing 'state_keys'`).

### D4. `kind=single_task` semantics

```sql
INSERT INTO vertex_langgraph_assistant (..., kind, factory_path) VALUES
  ('kobo.budAgent.v1', ..., 'single_task',
   'kotodama.kobo_worker_main:task_bud_agent');
```

Loader resolves `factory_path` to the task callable, wraps it with
`kotodama.langgraph_graphs._single_task_wrapper.build_single_task_graph`,
and registers the resulting 1-node graph. No `assistant_node` rows needed.
The internal SingleTaskState envelope (`{input, output, ok, error}`) is
preserved for compatibility with the prior `_register_organism_single_task_chains()`
path — clients calling `/runs assistant_id=kobo.budAgent.v1` see no behavior
change.

### D5. Hot-reload watcher contract

`langgraph_watcher.watch_forever(...)` runs as an asyncio background task
spawned in lifespan. Polling interval is `LANGGRAPH_RELOAD_INTERVAL_SEC`
(default 30s; set ≤0 to disable).

**Diff key** = `(version, status, updated_at)` per `assistant_id`. `_seq`
is unreliable in RW (does not auto-advance on PK upsert; values are whatever
the writer INSERTed). `updated_at` is the change signal — writers MUST bump
it on every meaningful row change.

**Behaviors**:

- **Lazy fetch**: poll touches only deployment table; full assistant +
  bindings fetched only for assistant_ids whose diff key changed.
- **Compile-then-swap**: a failed compile leaves the prior graph in place
  (`_GRAPH_REGISTRY[aid] = new_graph` only on successful build). In-flight
  `_execute_graph` runs hold their own local reference to the old graph;
  Python refcount keeps them alive past the swap.
- **Disable / delete**: `status='disabled'` or row removal pops the entry.
  New `/runs` 404; in-flight runs continue.
- **Error-trapped loop**: every poll iteration is wrapped in
  `try/except Exception` — a transient RW connection blip delays one tick.
- **`initial_seen` pass-through**: lifespan’s `load_active_graphs` returns
  the post-load `(aid, version, status, updated_at)` snapshot, which is
  passed as `initial_seen` to `watch_forever` so the first poll is a no-op
  for already-loaded actors. Without this, the first watcher pass
  re-compiles all 64 (wasteful + surfaces non-idempotent factory bugs).

### D6. `/registry-source` diagnostic

`GET /registry-source` returns:
```json
{
  "total": 64,
  "db_loaded": 64,
  "static_filled": 0,
  "watcher": {
    "running": true,
    "last_reload_at": <ms-epoch>,
    "reload_count": 0,
    "error_count": 0,
    "errored_assistants": [
      {"assistant_id": "<aid>", "error": "<exc-class>: <msg>"}
    ]
  }
}
```

This is the canonical signal for rollout phases:

- `static_filled > 0` → some assistants came from the static fallback (DB
  row missing or compile failed). Investigate before declaring DB SSoT.
- `errored_assistants` non-empty after watcher first pass settles →
  per-row compile failure (typo'd dotted path, missing module,
  non-idempotent factory). Each entry self-clears on next successful
  reload of the same `assistant_id`.

### D7. RW operational invariants

These are not new but were re-validated during the migration:

- **No prepared statements**: RW rejects `PREPARE`. `psycopg.conn.execute(sql,
  params, prepare=False)` is required everywhere (loader, watcher, resolvers).
- **No dollar-quoted strings (`$$`)**: not implemented in RW SQL parser. Use
  single-quoted literals with `''` escaping for SQL spec JSON.
- **Visibility lag**: `INSERT 0 1` returns before the row is visible to
  fresh `SELECT`s; explicit `FLUSH;` is the deterministic barrier.
- **GRANT to pod RW user is mandatory**: new `vertex_langgraph_*` tables
  must `GRANT SELECT,INSERT,UPDATE,DELETE TO <pod_user>` (currently `root`)
  before pod restart, otherwise loader logs "Permission denied".

### D8. Two-phase rollout for static-block removal

When eliminating the static `_register_builtin_graphs()` body:

1. **Phase A — DB-first / static-fallback**: invert lifespan order so DB
   loads first; static fills gaps with a `_SKIP_IF_EXISTS` flag. Verify on
   prod that ≥1 Cron firing succeeds against the row-driven path while the
   fallback is in place.
2. **Phase B — static disabled**: the static function body becomes
   `return # disabled`. The function is preserved for revert (per-actor
   helpers retained for tests).

Skipping phase A is forbidden — without it, a single bad row would 404
silently with no rollback path other than redeploying the prior image.

## Consequences

**Gained**:

- 95% of registered actors (61/64) are pure data; structural changes ship
  via SQL `INSERT` instead of image rebuild + rolling deploy.
- Actor topology (nodes/edges/conditionals/state_keys) is queryable via
  RW SQL, which makes it observable by the same tools as the rest of the
  graph (`etzhayyim dodaf tv1 query`, ad-hoc joins with `vertex_langgraph_run`).
- New actors require: 1 `vertex_langgraph_assistant` INSERT + N
  `vertex_langgraph_assistant_node` INSERTs + 1 `vertex_langgraph_deployment`
  INSERT. No code change.
- Per-row deploy + per-row rollback. RW PK upsert means re-INSERTing the
  prior row body reverts atomically.

**Constraints / new responsibilities**:

- Writers MUST bump `updated_at` on row changes; otherwise watcher won’t
  re-compile.
- Function bodies (node implementations, gate functions, factory bodies)
  remain in-image — moving the actor *code* to data is a separate concern
  (would require sandboxed exec / WASM, not on roadmap).
- `kind=topology` rows whose conditional router returns the langgraph `END`
  sentinel cannot be auto-extracted; either use a string key or stay
  `py_factory`.
- The watcher’s 30s poll interval is the floor latency for new-row
  visibility. If sub-30s deploy latency is needed, lower
  `LANGGRAPH_RELOAD_INTERVAL_SEC` (with caution: per-row JOIN cost
  multiplies on heavy reload bursts) or implement RW change-stream
  watcher (out of scope here).

## References

- ADR-2605080000: Distributed Cognitive Actor System — 6-Layer Architecture
- ADR-2605080600: LangGraph Server + Granian as L3 Virtual Actor Runtime (amended)
- ADR-2605082000: MCP tool registry resolution (companion — `mcp://<nsid>` in node bindings)
- ADR-2605082100: LangGraph assistant checkpointer_mode (companion — per-assistant checkpointer)
- Migrations: `r_20260509100000_vertex_langgraph_assistant_registry`,
  `r_20260509120000_seed_langgraph_builtin_63`,
  `r_20260509130000_alter_langgraph_assistant_checkpointer_mode`,
  `r_20260509140000_topology_saikin_cycle`,
  `r_20260509150000_topology_bulk_51`,
  `r_20260509160000_topology_single_task_8`
- Verification trail: 7 image deploys (v1→v7) on prod RW (45.32.79.245:4566).
  64 actors registered. End-to-end `/runs` validated on `ki_cycle_rw`
  (PoC), `saikin.cycle.v1` (bulk topology), `wellbecoming_minimax_sweep`
  (bulk topology), `kobo.budAgent.v1` (single_task).
