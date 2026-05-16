# @gftd/graph-schema sqlc — multi-language type-safe queries

Generates typed query bindings from `.sql` files. Pairs with Alembic (base
tables) and SQLMesh (MVs) — sqlc owns the **query layer**, not schema.

ADR-2605110227 §3.9. Adopted to kill the "query and type re-declared in N
languages" paper-cut. Schema SSoT stays in live RisingWave per ADR-2605080700;
sqlc reads a mirrored DDL under `schema/` for codegen.

## Layout

```
sqlc/
├── sqlc.yaml          — config (postgres engine, ts plugin via WASM)
├── schema/            — DDL mirror of Alembic + SQLMesh shape (used at codegen)
├── query/             — typed queries with `-- name: <Name> :many|:one|:exec`
└── gen/               — generated client code (gitignored)
    └── ts/            — TypeScript bindings (postgres.js driver shape)
```

## Workflow

1. Add or edit `.sql` in `query/`. Use `sqlc.arg('name')::type` for required
   params, `sqlc.narg('name')::type` for nullable.
2. If schema changed in Alembic, refresh `schema/research.sql` to match.
3. `cd 30-graph/graph-schema/sqlc && sqlc generate`.
4. Import generated types in consumers (e.g. mcp-adapter.ts).

## Current consumers

| Caller | Imports | Bridging |
|---|---|---|
| `50-infra/cloudflare/workers/atproto/src/mcp-adapter.ts` (`handleResearchGpuPriceCompare`, `handleResearchListAdrs`) | `GpuPriceCompareListRow`, `AdrListFilteredRow` types | Generated runtime uses `postgres` (postgres.js); CF Worker uses Hyperdrive+Kysely. **Types only for now**; runtime call goes through Kysely. Full sqlc-runtime adoption gated on a postgres.js→Hyperdrive shim (ADR-2605110227 §3.9c). |

## Python

`sqlc-gen-python` plugin block is commented out in `sqlc.yaml`. Add when
the first Python consumer needs typed access (likely SQLMesh data quality
checks or research scripts). Sample plugin block:

```yaml
plugins:
  - name: py
    wasm:
      url: https://downloads.sqlc.dev/plugin/sqlc-gen-python_1.3.0.wasm
      sha256: <verify with `shasum -a 256`>

sql:
  - codegen:
      - plugin: py
        out: gen/python
        options:
          package: sqlc_research
          emit_async_querier: true
          emit_pydantic_models: true
```
