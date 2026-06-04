---
id: adr-2605082100-langgraph-checkpointer-mode
title: "ADR-2605082100: Per-assistant LangGraph checkpointer_mode"
status: active
doc_type: adr
topic: langgraph-checkpointer-mode
authoritative: true
last_verified: 2026-05-08
priority: 7.5
axis: architecture
weight: 0.80
priority_note: "Per-assistant checkpointer selection (none | rw_vertex | postgres) addressable by row, not by global env."
authoritative_for:
  - vertex_langgraph_assistant.checkpointer_mode column
  - checkpointer mode taxonomy: none | rw_vertex | postgres
  - Resolution rule (_resolve_checkpointer): import + init at compile-time, log+None on failure
  - Rollout: NULL → 'none' (fail-safe default) for all pre-migration rows
depends_on:
  - adr-2605082200-langgraph-single-task-and-row-driven-runtime
  - adr-2605080600-langgraph-server-granian-l3-runtime
related: []
supersedes: []
superseded_by: []
---

# ADR-2605082100: Per-assistant LangGraph checkpointer_mode

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki

## Context

ADR-2605080600 §"RisingWave custom storage 実装" defined two
custom checkpointers: `RisingWaveCheckpointSaver` (writes to
`vertex_langgraph_checkpoint`) and Postgres-backed
`langgraph.checkpoint.postgres.PostgresSaver` (used when an assistant has
short-lived HITL state and Hyperdrive is preferable).

The choice of checkpointer was a global env decision baked into the
loader: every assistant got the same `checkpointer_kwargs` regardless of
whether it actually needed durable state. Most do not — Cron-fired one-shot
actors (`shinka_cron_tick`, `wellbecoming_*`, `aria_*`) complete in seconds
and never resume. Forcing them through a checkpointer adds RW write
amplification (every node step = INSERT into `vertex_langgraph_checkpoint`)
for no operational benefit.

This ADR moves the decision into the row.

## Decision

### D1. Schema addition

```sql
ALTER TABLE vertex_langgraph_assistant
  ADD COLUMN IF NOT EXISTS checkpointer_mode varchar DEFAULT 'none';
```

Pre-existing rows have `NULL`; loader's
`COALESCE(a.checkpointer_mode, 'none')` treats NULL as `'none'` so the
migration is backwards-compatible without a UPDATE pass.

### D2. Mode taxonomy

| Mode | Behavior | Use |
|---|---|---|
| `none` (default) | `checkpointer=None`. No state persisted. | One-shot Cron actors, ingest pipelines, anything that completes in <1 minute and never resumes. Vast majority of the 64 builtins. |
| `rw_vertex` | `RisingWaveCheckpointSaver()`. Writes to `vertex_langgraph_checkpoint` / `_checkpoint_write` / `_checkpoint_blob`. | Long-running actors with multi-step state worth replaying after pod restart. Currently zero in production; reserved for `projector` / `shosha_agent_loop` pattern when HITL pause/resume lands. |
| `postgres` | `langgraph.checkpoint.postgres.PostgresSaver.from_conn_string($HYPERDRIVE_LANGGRAPH_URL or $DATABASE_URL)` + `.setup()`. | Direct Postgres-backed for graphs that need `langgraph` upstream's `interrupt()` HITL semantics, where RW's lack of LISTEN/NOTIFY makes `rw_vertex` awkward. |

### D3. Resolution rule

`langgraph_loader._resolve_checkpointer(mode: str | None) -> Any` — invoked
at assistant compile time, returns the checkpointer instance (or `None`).
Failures (missing module, missing DSN, RW table not yet migrated) log a
warning and return `None`. **No exceptions propagate to compile.** A
misconfigured row degrades to `checkpointer=None` rather than blocking the
loader.

```python
def _resolve_checkpointer(mode):
    if not mode or mode == "none":
        return None
    if mode == "rw_vertex":
        try: from pymagatama.langgraph_checkpoint_rw import RisingWaveCheckpointSaver
        except Exception as e: LOG.warning(...); return None
        return RisingWaveCheckpointSaver()
    if mode == "postgres":
        dsn = os.environ.get("HYPERDRIVE_LANGGRAPH_URL") or os.environ.get("DATABASE_URL")
        if not dsn: LOG.warning(...); return None
        try:
            saver = PostgresSaver.from_conn_string(dsn); saver.setup(); return saver
        except Exception as e: LOG.warning(...); return None
    LOG.warning("unknown checkpointer_mode %r — defaulting to None", mode); return None
```

### D4. Threaded into compile

`_compile_topology(...)` accepts a `checkpointer_mode` kwarg passed from
the loader’s row read; each compile path (py_factory / topology /
single_task) hands the resolved checkpointer to LangGraph’s `.compile(...)`
where applicable.

For `py_factory` rows, the mode is **advisory only** — the factory
function decides whether to honor it. (Some legacy factories hard-code
their own checkpointer; the loader does not override.)

### D5. Default / rollout

The migration sets `DEFAULT 'none'`. Existing 64 builtin rows had `NULL`
written by the seed; loader's COALESCE handles them as `'none'`. No data
backfill required.

When promoting an assistant to a non-`none` mode:

```sql
UPDATE vertex_langgraph_assistant
   SET checkpointer_mode = 'rw_vertex'
 WHERE assistant_id = '<aid>' AND version = <v>;

INSERT INTO vertex_langgraph_deployment (..., updated_at) VALUES (...);  -- bumps watcher diff key
```

Watcher detects the `updated_at` change, recompiles, swaps. In-flight
runs continue on the old graph (no checkpointer); next `/runs` POST gets
the checkpointer-enabled graph.

## Consequences

**Gained**:
- Per-actor checkpointer choice; no global setting required.
- Default `'none'` is fail-safe: no surprise RW writes from incidentally
  flipping a flag.
- Adding a new checkpointer (e.g. SQLite for local dev) = extending
  `_resolve_checkpointer` + adding a mode value; no schema change.

**Constraints**:
- Mode strings are not enforced by a CHECK constraint (RW limitation);
  unknown modes log warning + use `None`. `etzhayyim lint` could add a
  defensive check at row insert time (out of scope).
- Switching modes between versions is a true graph swap; in-flight runs
  cannot migrate state across modes (e.g. `none` → `rw_vertex`).
  Document this as a soft contract: pin a long-running actor’s
  checkpointer at v1 and don't change it within a major version.

## References

- ADR-2605080600: LangGraph Server + Granian L3 Runtime (parent)
- ADR-2605082200: Row-driven LangGraph runtime (sibling — assistant kind taxonomy)
- Migration `r_20260509130000_alter_langgraph_assistant_checkpointer_mode`
- Implementation: `pymagatama/langgraph_loader.py:_resolve_checkpointer`
