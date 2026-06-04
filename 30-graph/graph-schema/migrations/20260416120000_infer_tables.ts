import { Kysely, sql } from 'kysely';

/**
 * Migration: infer tables for etzhayyim coverage infer.
 *
 * Tables:
 *   vertex_infer_input   — raw input feature vectors from statistical data
 *   vertex_infer_cluster — discovered latent clusters (GMM/LCA output)
 *   vertex_infer_match   — cluster ↔ cohort/entity match results
 *
 * MV:
 *   mv_infer_cluster_summary — per-cluster evidence count + avg posterior
 *
 * Pre-flight (graph-schema CLAUDE.md §MV Memory Safety Guardrails):
 *   - GROUP BY cluster_id cardinality: initial 0, scale ~1k → OK (< 500k)
 *   - Backfill: 0 rows (writes start after discover command)
 *   - No MAX(varchar) — narrow numeric aggregate only
 *
 * Design: 90-docs/260416-coverage-infer-statistical-entity-resolution.md
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Input feature vectors
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_infer_input" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "_seq"            BIGINT,
    "created_date"    DATE,
    "sensitivity_ord" BIGINT,
    "owner_did"       VARCHAR,
    "source_type"     VARCHAR NOT NULL,
    "source_file"     VARCHAR,
    "features"        VARCHAR NOT NULL,
    "feature_names"   VARCHAR,
    "label"           VARCHAR,
    "batch_id"        VARCHAR NOT NULL
  )`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_vertex_infer_input_batch"
    ON "vertex_infer_input"("batch_id")`.compile(db));

  // Discovered clusters
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_infer_cluster" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "_seq"            BIGINT,
    "created_date"    DATE,
    "sensitivity_ord" BIGINT,
    "owner_did"       VARCHAR,
    "cluster_id"      BIGINT NOT NULL,
    "batch_id"        VARCHAR NOT NULL,
    "method"          VARCHAR NOT NULL,
    "centroid"        VARCHAR,
    "k_anonymity"     BIGINT,
    "member_count"    BIGINT,
    "segment_hash"    VARCHAR,
    "features_avg"    VARCHAR,
    "status"          VARCHAR DEFAULT 'active'
  )`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_vertex_infer_cluster_batch"
    ON "vertex_infer_cluster"("batch_id")`.compile(db));

  // Match results
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_infer_match" (
    "vertex_id"        VARCHAR PRIMARY KEY,
    "_seq"             BIGINT,
    "created_date"     DATE,
    "sensitivity_ord"  BIGINT,
    "owner_did"        VARCHAR,
    "cluster_id"       VARCHAR NOT NULL,
    "cohort_did"       VARCHAR NOT NULL,
    "similarity"       DOUBLE PRECISION NOT NULL,
    "posterior"         DOUBLE PRECISION,
    "match_method"     VARCHAR NOT NULL,
    "batch_id"         VARCHAR NOT NULL,
    "status"           VARCHAR DEFAULT 'candidate'
  )`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_vertex_infer_match_cohort"
    ON "vertex_infer_match"("cohort_did")`.compile(db));

  // Cluster summary MV (label = cluster assignment from GMM)
  await db.executeQuery(sql`CREATE MATERIALIZED VIEW IF NOT EXISTS "mv_infer_cluster_summary" AS
    SELECT
      batch_id,
      label AS cluster_label,
      COUNT(*)::BIGINT AS input_count
    FROM "vertex_infer_input"
    WHERE batch_id IS NOT NULL AND label IS NOT NULL
    GROUP BY batch_id, label`.compile(db));
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`DROP MATERIALIZED VIEW IF EXISTS "mv_infer_cluster_summary"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_vertex_infer_match_cohort"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "vertex_infer_match"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_vertex_infer_cluster_batch"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "vertex_infer_cluster"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_vertex_infer_input_batch"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "vertex_infer_input"`.compile(db));
}
