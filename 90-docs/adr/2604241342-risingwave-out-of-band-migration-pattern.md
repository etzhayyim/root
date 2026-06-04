---
id: adr-2604241342-risingwave-out-of-band-migration-pattern
title: "RisingWave out-of-band migration pattern (apply-pending.sh as the happy path)"
status: active
doc_type: adr
topic: graph-schema-ops
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - standard migration workflow for @etzhayyim/graph-schema
  - known incompatibilities (ON CONFLICT, UNIQUE INDEX, test files in migrations/)
  - when pnpm db:migrate works vs. when to reach for apply-pending.sh
related:
  - adr-2604241038-yoro-pds-ideal-topology
---

# Context

`pnpm db:migrate latest` — the canonical kysely migration runner — does
not work reliably against RisingWave in this repo. `graph-schema/CLAUDE.md`
and multiple migration file comments note "applied out-of-band via psql"
as a recurring pattern; the 2026-04-24 session hit the same issues in
three distinct shapes, enough to codify as standard.

Observed failure modes, each recorded in
`scripts/run-one-migration.mjs` comments or `CLAUDE.md`:

## Failure A — kysely "corrupted migrations" guard

Live `kysely_migration` table carries rows for migrations whose `.ts`
files were later deleted (typical on a long-running branch where a
migration was rewritten + renamed). Kysely's
`ensureNoMissingMigrations()` refuses to run until every recorded row
has a matching file on disk, so a single stale row blocks the entire
sweep.

Observed row: `20260424030000_vertex_human_task_bpmn_columns` — applied
2026-04-24T03:04:13Z, file absent from the tree. No fix migration.

## Failure B — RisingWave sql_parser rejects `ON CONFLICT`

Migration SQL that uses PostgreSQL's `INSERT ... ON CONFLICT (...) DO
NOTHING` is a parse error in RisingWave — the clause is not implemented
at the parser level, not just the executor. The pattern is load-bearing
in idempotent-seed migrations (yabai / animeka / shinshi BPMN bindings)
so this failure surfaces on every re-run.

Fix pattern: SELECT-then-INSERT.

```ts
const existing = await sql<{ vertex_id: string }>`
  SELECT vertex_id FROM <table> WHERE vertex_id = ${seed.vertexId} LIMIT 1
`.execute(db);
if (existing.rows.length > 0) continue;
await sql`INSERT INTO <table> (...) VALUES (...)`.execute(db);
```

`scripts/run-one-migration.mjs:33-42` already uses this pattern for the
`kysely_migration` row it records at the end of each apply.

## Failure C — test files next to migrations import vitest

`FileMigrationProvider` reads every file in `migrations/` and imports
it as a migration module. Files named `*.test.ts` that export nothing
but `describe(...)` bodies still run their top-level imports —
`import { describe } from "vitest"` errors outside a vitest runtime
with `Cannot read properties of undefined (reading 'config')`.

Fix landed 2026-04-24 in `scripts/migrate.ts`: wrap `fs.readdir` to
filter out `*.test.ts` before the provider sees them (commit
`50469d6ca06`).

## Failure D — other unsupported DDL

Migrations occasionally use PG DDL that RisingWave hasn't implemented
yet:

- `CREATE UNIQUE INDEX` — not implemented (observed on
  `20260423194000_gyosei_source_graph`).
- `DROP MATERIALIZED VIEW ... CASCADE` — not implemented (observed on
  the dep-chain rebuild for `mv_actor_social_stats`).

Each needs a case-by-case rewrite: `CREATE UNIQUE INDEX` becomes
`CREATE INDEX` + app-level dedupe, `CASCADE` becomes explicit drops in
reverse dep order.

# Decision

**Default to `scripts/apply-pending.sh` for migrations on this repo.**
`pnpm db:migrate latest` stays available for the eventual clean path
but should not be the first tool reached for.

The helper encodes each failure mode's workaround:

- takes named migrations instead of sweeping everything, so a stray
  cross-scope migration can't break an otherwise-green batch;
- pre-flights each file for `ON CONFLICT` in executable SQL (stripping
  comments) so Failure B surfaces before the apply;
- delegates to `scripts/run-one-migration.mjs` which bypasses the
  kysely migrator's missing-history guard (Failure A);
- records the `kysely_migration` row itself when the runner errors
  partway through (common when Failure D hits a subsequent step);
- runs `pnpm db:drift` + `pnpm db:gen` once at the end so the
  `database.ts` diff is ready to commit.

Usage:

```bash
bash scripts/apply-pending.sh <migration-name> [<migration-name> ...]
DRY_RUN=1 bash scripts/apply-pending.sh <migration-name>
```

# Consequences

## Positive

- New migrations land with one reliable command instead of the
  "try `pnpm db:migrate`, watch it fail, grep for the workaround
  pattern in CLAUDE.md, paste into psql" dance that the 2026-04-24
  session documented having happen four times.
- Each failure mode has a named ADR section to link back to. Next
  session's "why did this fail?" is a ctrl-F away.
- Cross-scope migrations (datacenter, open_seiyaku, animeka, lawyer,
  gyosei) are applied individually, with opt-in, rather than being
  swept wholesale by whoever runs `db:migrate` next.

## Negative

- `apply-pending.sh` + `run-one-migration.mjs` each duplicate a
  small piece of the kysely migrator. If the kysely migrator is
  ever fixed upstream to support RisingWave cleanly, we'll need
  to revisit both.
- The helper reaches into macOS Keychain for `etzhayyim.rw / ROOT_URL`
  by default; a non-macOS contributor has to export `DATABASE_URL`
  manually. Acceptable — this repo's ops are Mac-only today.
- The pre-flight `ON CONFLICT` guard is an awk scan of comments and
  executable SQL. False negatives are possible on unusually-shaped
  template strings; we accept the risk because the runner itself
  will still catch the parse error.

# Exceptions

- **Clean new repo** — if `kysely_migration` has no stale rows and
  the batch uses no `ON CONFLICT` / `CREATE UNIQUE INDEX` /
  `CASCADE`, `pnpm db:migrate` is preferable. The helper is for
  repos that have accumulated drift.
- **Dry-run on CI** — `DRY_RUN=1 bash apply-pending.sh …` in CI is
  fine as a pre-commit guard; actual applies should still be local.

# References

- `30-graph/graph-schema/scripts/apply-pending.sh` — the helper.
- `30-graph/graph-schema/scripts/run-one-migration.mjs` — the
  per-migration runner it delegates to.
- `30-graph/graph-schema/scripts/migrate.ts:128-ish` — the `.test.ts`
  filter workaround for Failure C.
- `30-graph/graph-schema/migrations/20260424120000_seed_yabai_batch3_bpmn_actors.ts`
  — canonical SELECT-then-INSERT example (Failure B fix).
- `30-graph/graph-schema/migrations/20260424014529_mv_actor_social_stats_root_normalization.ts`
  — canonical explicit-drop-reverse-dep-order example (Failure D
  `CASCADE` fix).
- `graph-schema/CLAUDE.md` — pre-existing notes on out-of-band applies.
