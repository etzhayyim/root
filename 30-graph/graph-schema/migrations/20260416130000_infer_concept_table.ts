import { Kysely, sql } from 'kysely';

/**
 * Migration: vertex_infer_concept — ideology / philosophy / religion / political system concept nodes.
 *
 * Latent entity dependency graph: country/cluster actors follow/require concept nodes.
 * Used by: etzhayyim coverage infer deps --seed-concepts / --input deps.jsonl
 *
 * Design: 90-docs/260416-coverage-infer-statistical-entity-resolution.md
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_infer_concept" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "_seq"            BIGINT,
    "created_date"    DATE,
    "sensitivity_ord" BIGINT,
    "owner_did"       VARCHAR,
    "slug"            VARCHAR NOT NULL,
    "category"        VARCHAR NOT NULL,
    "display_name"    VARCHAR,
    "description"     VARCHAR,
    "era"             VARCHAR,
    "origin_country"  VARCHAR
  )`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_vertex_infer_concept_slug"
    ON "vertex_infer_concept"("slug")`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_vertex_infer_concept_category"
    ON "vertex_infer_concept"("category")`.compile(db));
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_vertex_infer_concept_category"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_vertex_infer_concept_slug"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "vertex_infer_concept"`.compile(db));
}
