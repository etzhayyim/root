# App Client Migration: Drizzle ORM + Kysely (2026-04-12)

> **Superseded in part 2026-04-17**: the "hand-managed `schema.ts`" claim no longer holds.
> Drizzle `schema.ts` was archived 2026-04-13 (`_archive/2026-04-13-non-kysely/`), and
> `@etzhayyim/graph-schema/src/database.ts` is now **generated** from live Kotoba/Datomic
> `information_schema` via `pnpm db:gen`, with `pnpm db:drift` as CI guard.
> See `30-graph/graph-schema/CLAUDE.md` for the current workflow.

## Executive Summary

**Cypher string literals (G() builder, cypherQueryAsync) → Drizzle/Kysely type-safe queries.**

- **Schema SSoT**: `@etzhayyim/graph-schema/schema.ts` (Drizzle ORM, hand-managed)
- **Query builder**: `createKyselyDb()` from `@etzhayyim/kotodama-host-sdk`
- **Type-safe row types**: exported from `@etzhayyim/graph-schema` (e.g., VertexActorRow, VertexOtherRow)
- **Scope**: 40+ wasm app clients (intel, ipaddress, natural-person, site, yorishiro, etc)
- **Migration**: Phase 1 (SDK + schema) complete 2026-04-11. Phase 2 (app clients) in-progress 2026-04-12.

## Architecture

### Before: Cypher String Literals

```typescript
// App code
import { G } from "@etzhayyim/kotodama-host-sdk";

async function getActors(did: string) {
  const cypher = `MATCH (a:Actor {did: $did}) RETURN a.vertex_id, a.name LIMIT 50`;
  const rows = await G(cypher).Query({ did });
  // rows: any[] — no type safety
  return rows.map(r => ({ id: r.vertex_id, name: r.name }));
}

// Flow:
// 1. App sends Cypher string to Graph Worker
// 2. graph-planner parses/plans/transpiles to SQL
// 3. SQL executed on Kotoba/Datomic
// 4. Results returned as JSON objects (untyped)
```

**Problems:**
- No type safety (rows: any)
- Runtime transpilation cost (graph-planner 1887 LOC)
- Cypher feature gaps (WITH clause unsupported)
- Cypher-specific gotchas (CONTAINS/STARTS WITH → OOM)

### After: Kysely Type-Safe Queries

```typescript
// App code
import { createKyselyDb } from "@etzhayyim/kotodama-host-sdk";
import type { Database, VertexActorRow } from "@etzhayyim/graph-schema";

async function getActors(sql: Sql, env: WorkerEnv, did: string) {
  const db = createKyselyDb(sql, env.HYPERDRIVE);
  const rows: VertexActorRow[] = await db
    .selectFrom('vertex_actor')
    .where('did', '=', did)
    .select(['vertex_id', 'name', 'display_name'])
    .limit(50)
    .execute();

  return rows.map(r => ({ id: r.vertex_id, name: r.name }));
}

// Flow:
// 1. App builds SQL via Kysely (type-safe at build-time)
// 2. Kysely.PostgresDialect generates SQL string
// 3. Hyperdrive RLS middleware + client.query(sql, params)
// 4. Kotoba/Datomic executes SQL
// 5. Results mapped to VertexActorRow type
```

**Benefits:**
- Full type safety (VertexActorRow | VertexOtherRow | etc)
- Zero-cost abstraction (Kysely compiles to SQL, no transpiler)
- SQL feature parity (Kotoba/Datomic PG dialect fully supported)
- IDE autocomplete (db.selectFrom('table') → available columns known)

## Implementation Details

### 1. Schema Definition (Drizzle ORM)

**File**: `30-graph/graph-schema/src/schema.ts`

```typescript
import { pgTable, varchar, bigint, text } from "drizzle-orm/pg-core";

export const vertexActor = pgTable("vertex_actor", {
  vertexId: varchar('vertex_id', { length: 512 }).primaryKey(),
  seq: bigint('_seq', { mode: 'number' }),
  did: varchar('did', { length: 512 }),
  displayName: varchar('display_name', { length: 1024 }),
  name: varchar('name', { length: 512 }),
  // ... 40+ actor-specific columns
});

export const vertexOther = pgTable("vertex_other", {
  vertexId: varchar('vertex_id', { length: 512 }).primaryKey(),
  label: varchar('label', { length: 256 }),
  did: varchar('did', { length: 512 }),
  props: text('props'), // JSON fallback for unmodeled properties
  // ... 6 promoted columns
});
```

**Key points:**
- Drizzle column names = database column names (snake_case)
- TS variable names = camelCase (normal TS convention)
- Hand-managed (NO auto-generation from introspection)
- drizzle-kit migrations: `pnpm db:generate` → `migrations/YYYY_*`

### 2. Database Client (Kysely)

**File**: `30-graph/graph-schema/src/database.ts`

```typescript
import { Kysely, PostgresDialect, type Database as KyselyDb } from 'kysely';
import type { Database } from './types.js'; // Kysely type definition

export function createKyselyDb(sql: Sql, hyperdrive: any): Kysely<Database> {
  return new Kysely<Database>({
    dialect: new PostgresDialect({
      pool: new HyperdrivePgPool(hyperdrive, sql),
    }),
  });
}
```

**Types exported**:
```typescript
// Row types (from schema.ts pgTable definitions)
export type VertexActorRow = InferSelectModel<typeof vertexActor>;
export type VertexOtherRow = InferSelectModel<typeof vertexOther>;
export type EdgeFollowsRow = InferSelectModel<typeof edgeFollows>;
// ... all 188 table row types
```

### 3. Table Resolution Helpers

**File**: `30-graph/graph-schema/src/helpers.ts`

```typescript
export function resolveVertexTable(label: string): keyof Database['Tables'] {
  // label='Actor' → 'vertex_actor'
  // label='Other' → 'vertex_other'
  // label='ThreatActor' → 'vertex_threat_actor'
  const snakeLabel = toSnakeCase(label);
  return `vertex_${snakeLabel}` as const;
}
```

Used for dynamic table selection when label is only known at runtime.

### 4. App Client Integration

**Pattern**:

```typescript
// src/app.ts
export default createWorkerExport((sdk) => {
  sdk.app.command('com.etzhayyim.apps.intel.search', searchIntel);
});

async function searchIntel(sdk: HostSDK, params: SearchParams) {
  const { did, query } = params;
  const db = createKyselyDb(sdk.sql, sdk.env.HYPERDRIVE);

  // Type-safe query
  const results = await db
    .selectFrom('vertex_intel_analysis')
    .where('owner_did', '=', did)
    .where('status', '=', 'published')
    .select(['vertex_id', 'title', 'content', 'created_at'])
    .limit(100)
    .execute();

  // Results: VertexIntelAnalysisRow[] (fully typed)
  return { results, count: results.length };
}
```

**Field reference rules**:
- DB columns: snake_case (`vertex_id`, `owner_did`, `created_at`)
- TS variables: camelCase (`vertexId`, `ownerDid`, `createdAt`)
- Row type properties: snake_case (match DB columns for JSON serialization)

## Migration Phases

### Phase 1: SDK + Schema (DONE 2026-04-11)

- [x] Drizzle schema.ts created (188 pgTable definitions)
- [x] drizzle-kit integration (pnpm db:generate)
- [x] Kysely database.ts + Database type
- [x] kotodama-host-sdk: createKyselyDb() export
- [x] Type exports: @etzhayyim/graph-schema (Database, VertexActorRow, etc)
- [x] Python schema archived (_archive/30-graph/graph-schema-py-260412)
- [x] Documentation: CLAUDE.md + design doc

### Phase 2: App Client Migration (IN PROGRESS 2026-04-12)

- [ ] intel: db.selectFrom() full migration
- [ ] ipaddress: db.selectFrom() full migration
- [ ] natural-person: db.selectFrom() full migration
- [ ] site (webpage): db.selectFrom() full migration
- [ ] yorishiro (all providers): db.selectFrom() full migration
- [ ] kotodama graph-builder.ts: Drizzle only (no Cypher fallback)
- [ ] Type safety: all row types imported + used

**Sub-tasks per app**:
1. Replace `G(cypher_string)` with `db.selectFrom(table)`
2. Update row type imports: `import type { VertexOtherRow } from "@etzhayyim/graph-schema"`
3. Fix field references: `row.vertexId` → `row.vertex_id`
4. Update helper functions: `parseVertexOther(row: any)` → `parseVertexOther(row: VertexOtherRow)`

### Phase 3: Graph Component Cleanup (PENDING 2026-04-13+)

- [ ] graph-planner/src/cypher → _archive/30-graph/graph-planner-cypher-260412
  - Cypher parser, planner, transpiler (1887 LOC)
  - No longer needed once all apps use Kysely
- [ ] 30-graph/graph-schema/src/*.gen.ts → delete
  - p10.gen.ts, ddl.gen.ts, naming.gen.ts, etc
  - Currently frozen artifacts (only Cypher transpiler uses)
- [ ] 40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/cypher.ts → delete
  - G() builder, cypherQueryAsync
  - Replaced by createKyselyDb()
- [ ] Integration tests: replace Cypher test cases with Kysely

### Phase 4: Graph Worker Simplification (PENDING 2026-04-14+)

- [ ] Remove Cypher transpiler path from graph Worker
  - No more `/graph/cypher` endpoint
  - `createKyselyDb(env.HYPERDRIVE)` becomes sole path
- [ ] Graph path: remove rawCypher.exec() (deprecated path cleanup)
- [ ] Schema sync: remove yata ↔ Kotoba/Datomic sync (ddl.ts removed)

## Field Naming Conventions

**Database layer (columns)**: snake_case (storage format)
```sql
SELECT vertex_id, owner_did, created_at FROM vertex_actor
```

**TS type definitions**: snake_case (matches DB, for JSON serialization)
```typescript
type VertexActorRow = {
  vertex_id: string;
  owner_did: string;
  created_at: string;
};
```

**TS variables in code**: camelCase (idiomatic TS)
```typescript
const vertexId = row.vertex_id;
const ownerDid = row.owner_did;
```

**Future**: Planned migration to camelCase throughout (columns + types), pending full app client conversion.

## Blocked Work

**graph-planner Cypher transpiler still needed** (temporarily):
- App migration phase incomplete (Phase 2)
- graph-schema *.gen.ts consumed by graph SQL planner
- Will be archived once all apps use Kysely + graph switches to SQL dialect

**No active Cypher string literals** in new code:
- All new queries use Kysely
- Old cypherQueryAsync calls deprecated (will fail at lint time)
- Lint rule: `lint-dangerous-query` updated for Drizzle patterns

## Lint & Quality

### Lint Rules Updated

**`lint-dangerous-query.mjs`** (70-tools/scripts/lint/):
- ~~`G("...") with CONTAINS / STARTS WITH`~~ (Cypher only)
- `db.selectFrom().where('col', 'LIKE', '...')` with % wildcard (SQL text search)
- Recommends: exact match (=) or IVF vector search or post-filter

### Type Checking

**Strict mode**:
```typescript
// ❌ ERROR at build time: row is typed as VertexActorRow
const row: VertexOtherRow = rows[0]; // Type mismatch!

// ✅ Correct: use correct row type
const row: VertexActorRow = rows[0];
```

## RLS (Row-Level Security)

**Hyperdrive middleware enforces**:
- `WHERE owner_did = $userDid` automatically applied
- `WHERE org_id = $orgId` for multi-tenant queries
- Session JWT contains (did, org_id, etc)

App queries do NOT need to specify org_id:
```typescript
// ✅ Correct: RLS middleware adds org_id filter
const rows = await db.selectFrom('vertex_actor')
  .where('did', '=', userDid)
  .execute();

// ❌ Redundant (middleware does this):
const rows = await db.selectFrom('vertex_actor')
  .where('did', '=', userDid)
  .where('org_id', '=', orgId) // Unnecessary
  .execute();
```

## Related

- `@etzhayyim/graph-schema/CLAUDE.md` — schema management + migration procedure
- `@etzhayyim/graph-schema/drizzle.config.ts` — drizzle-kit configuration
- `40-engine/kotoba/crates/kotoba-kotodama/CLAUDE.md` — SDK architecture + createKyselyDb()
- `deps.toml [[migrations."drizzle-to-kysely"]]` — phase tracking
- `deps.toml [[conventions."App Data Access: Drizzle ORM + Kysely"]]` — standards

## Glossary

| Term | Definition |
|---|---|
| **Drizzle ORM** | TypeScript ORM for schema definitions (schema.ts). Not a query builder. |
| **Kysely** | Type-safe SQL query builder. Compiles to SQL strings (zero overhead). |
| **Database type** | TypeScript interface describing all tables/columns. Auto-generated from Drizzle schema. |
| **Row type** | TypeScript type for a single row (VertexActorRow, VertexOtherRow, etc). Inferred from pgTable. |
| **createKyselyDb** | SDK helper: instantiates Kysely client with Hyperdrive pool + RLS middleware. |
| **Hyperdrive** | Cloudflare D1 Postgres proxy. Handles RLS + connection pooling. |
| **Kotoba/Datomic** | Streaming SQL database (PG-compatible). Execution layer. |
| **Graph Worker** | Cloudflare Worker that exposes `/xrpc/*` and relays queries to Hyperdrive. |
