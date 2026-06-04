import { Kysely, sql } from 'kysely';

/**
 * Migration 0053: `vertex_cohort_actor` — cohort lineage + signature storage
 * (ADR-0026 Iteration 5).
 *
 * Holds the 4 signature/fission columns that do NOT belong on per-evidence rows:
 *   segment_hash      — cohort demographic segment id (k-anonymity bucket)
 *   k_anonymity       — declared k at genesis (static; live k via mv_cohort_k_drift)
 *   fission_enabled   — Phase C gate
 *   derived_from      — parent cohort DID (NULL for kind='cohort')
 *
 * Plus lifecycle metadata:
 *   kind              — "cohort" | "fissioned"
 *   status            — "pending-plc-genesis" | "active" | "purged"
 *   genesis_at        — ISO-8601 timestamp
 *
 * PK = cohort_did (did:plc:* for active, did:plc:pending-* for staged).
 *
 * Populated by `etzhayyim cohort seed` CLI + `com.etzhayyim.cohort.seed` procedure.
 * Read by Path F scheduler `cohortKReevaluate` task for fission_enabled lookup.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_cohort_actor" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "cohort_did"      VARCHAR NOT NULL,
    "handle"          VARCHAR,
    "kind"            VARCHAR NOT NULL,
    "segment_hash"    VARCHAR NOT NULL,
    "k_anonymity"     BIGINT       NOT NULL,
    "fission_enabled" BOOLEAN      NOT NULL DEFAULT FALSE,
    "derived_from"    VARCHAR,
    "status"          VARCHAR NOT NULL,
    "signature_uri"   VARCHAR,
    "genesis_at"      VARCHAR NOT NULL,
    "owner_did"       VARCHAR,
    "_seq"            BIGINT,
    "created_date"    DATE
  )`.compile(db));

  await db.executeQuery(
    sql`CREATE INDEX IF NOT EXISTS "idx_vertex_cohort_actor_did" ON "vertex_cohort_actor"("cohort_did")`.compile(db),
  );
  await db.executeQuery(
    sql`CREATE INDEX IF NOT EXISTS "idx_vertex_cohort_actor_derived_from" ON "vertex_cohort_actor"("derived_from")`.compile(db),
  );
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_vertex_cohort_actor_derived_from"`.compile(db));
  await db.executeQuery(sql`DROP INDEX IF EXISTS "idx_vertex_cohort_actor_did"`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "vertex_cohort_actor"`.compile(db));
}
