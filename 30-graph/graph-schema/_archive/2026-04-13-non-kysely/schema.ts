/**
 * Graph Schema Documentation
 *
 * The Etzhayyim graph database contains 188 tables:
 * - 130 vertex (entity) tables: vertex_actor, vertex_post, vertex_profile, etc.
 * - 57 edge (relationship) tables: edge_follows, edge_has_author, edge_contains, etc.
 *
 * Architecture
 * ============
 * - Database: RisingWave (PostgreSQL-compatible streaming SQL)
 * - ORM: Kysely (type-safe query builder)
 * - Connection: Hyperdrive (Cloudflare D1 Postgres wire proxy)
 *
 * Schema Sources
 * ==============
 * 1. Table definitions → migrations/0001_initial_schema.ts (CREATE TABLE statements)
 * 2. TypeScript types → src/database.ts (Kysely row interfaces)
 * 3. Table resolution → src/helpers.ts (label→table mapping functions)
 *
 * Creating Tables
 * ===============
 * Use the Kysely migration system:
 *   1. Create new migration file: migrations/000X_<name>.ts
 *   2. Implement up() function with sql`CREATE TABLE ...`
 *   3. Run: DATABASE_URL=... pnpm db:migrate
 *
 * Adding Columns to Existing Tables
 * ==================================
 * Use Kysely migrations with ALTER TABLE:
 *   await db.schema.alterTable('vertex_actor')
 *     .addColumn('new_column', 'varchar(255)')
 *     .execute();
 *
 * Querying Data
 * =============
 * import { createKyselyDb } from "@etzhayyim/magatama-host-sdk";
 * import type { Database } from "@etzhayyim/graph-schema";
 *
 * const db = createKyselyDb(sql, env.HYPERDRIVE);
 * const actors = await db.selectFrom('vertex_actor')
 *   .selectAll()
 *   .execute();
 *
 * Type-Safe Rows
 * ==============
 * import type { VertexActorRow, VertexPostRow } from "@etzhayyim/graph-schema";
 *
 * function processRow<T extends Record<string, any>>(row: T): void {
 *   // Full type safety on row properties
 * }
 *
 * Migration History
 * =================
 * - 2026-04-08: DuckDB → RisingWave migration (atomic SWAP TABLE, ~30ms)
 * - 2026-04-11: Python SQLAlchemy archived, Drizzle ORM introduced
 * - 2026-04-12: Drizzle → Kysely migration (188 tables, type-safe query builder)
 *
 * Previous Schema Sources (Archived)
 * ==================================
 * - Python SQLAlchemy models: _archive/30-graph/graph-schema-py-260412/models.py
 * - Alembic migrations: _archive/30-graph/graph-schema-py-260412/alembic/versions/
 */

export {};
