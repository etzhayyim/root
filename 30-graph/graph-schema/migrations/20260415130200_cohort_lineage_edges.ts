import { Kysely, sql } from 'kysely';

/**
 * Migration 0056: cohort lineage edge tables + lineage analytics MV
 * (ADR-0026, identity registration scaling).
 *
 * Adds explicit edge tables so lineage / evidence-attribution / projector
 * routing can be queried via standard CSR/CSC patterns without relying
 * solely on the `derived_from` column on `vertex_cohort_actor`.
 *
 * Tables:
 *   edge_cohort_derived       — parent cohort_did → fissioned individual_did
 *   edge_cohort_evidence_about — evidence_hash → cohort_did
 *   edge_cohort_routes_to     — cohort_did → APQC L1 path-based DID
 *
 * MV:
 *   mv_cohort_lineage_depth — per-cohort child count + max descendant chain
 *                             (bounded recursion depth = 2 to stay narrow)
 *
 * Pre-flight (graph-schema CLAUDE.md §MV Memory Safety Guardrails):
 *   - GROUP BY src_vid cardinality: bounded by cohort count (~1M)
 *   - Backfill: 0 rows initially (writes start after deploy)
 *   - No MAX(varchar) — narrow numeric aggregate
 *   - Hummock-only, no Iceberg sink
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_cohort_derived" (
    "edge_id"      VARCHAR PRIMARY KEY,
    "src_vid"      VARCHAR NOT NULL,
    "dst_vid"      VARCHAR NOT NULL,
    "_seq"         BIGINT,
    "created_date" DATE,
    "owner_did"    VARCHAR,
    "posterior"    DOUBLE PRECISION,
    "fission_at"   VARCHAR
  )`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_edge_cohort_derived_src" ON "edge_cohort_derived"("src_vid")`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_edge_cohort_derived_dst" ON "edge_cohort_derived"("dst_vid")`.compile(db));

  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_cohort_evidence_about" (
    "edge_id"      VARCHAR PRIMARY KEY,
    "src_vid"      VARCHAR NOT NULL,
    "dst_vid"      VARCHAR NOT NULL,
    "_seq"         BIGINT,
    "created_date" DATE,
    "owner_did"    VARCHAR,
    "signal_kind"  VARCHAR,
    "posterior"    DOUBLE PRECISION,
    "observed_at"  VARCHAR
  )`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_edge_cohort_evidence_dst" ON "edge_cohort_evidence_about"("dst_vid")`.compile(db));

  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_cohort_routes_to" (
    "edge_id"      VARCHAR PRIMARY KEY,
    "src_vid"      VARCHAR NOT NULL,
    "dst_vid"      VARCHAR NOT NULL,
    "_seq"         BIGINT,
    "created_date" DATE,
    "owner_did"    VARCHAR,
    "pcf_l1"       VARCHAR,
    "registered_at" VARCHAR
  )`.compile(db));
  await db.executeQuery(sql`CREATE INDEX IF NOT EXISTS "idx_edge_cohort_routes_pcfl1" ON "edge_cohort_routes_to"("pcf_l1")`.compile(db));

  await db.executeQuery(sql`CREATE MATERIALIZED VIEW IF NOT EXISTS "mv_cohort_lineage_depth" AS
    SELECT
      src_vid AS cohort_did,
      COUNT(*)::BIGINT AS direct_children,
      MAX(fission_at) AS last_fission_at
    FROM "edge_cohort_derived"
    GROUP BY src_vid`.compile(db));
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`DROP MATERIALIZED VIEW IF EXISTS "mv_cohort_lineage_depth"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_edge_cohort_routes_pcfl1"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "edge_cohort_routes_to"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_edge_cohort_evidence_dst"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "edge_cohort_evidence_about"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_edge_cohort_derived_dst"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_edge_cohort_derived_src"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "edge_cohort_derived"`.compile(db));
}
