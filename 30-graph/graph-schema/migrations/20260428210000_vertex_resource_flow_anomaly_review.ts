import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 15 — anomaly review audit log (ADR-0028 + ADR-0046).
// tier: A (public aggregate; no PII)
//
// One row per review action (acknowledge / dismiss / escalate). Append-only
// — the latest action per anomaly_id wins via ORDER BY observed_at DESC.
// We keep a derived `mv_resource_flow_anomaly_review_latest` MV so the
// AppView can join the latest decision back onto the anomaly row in
// one read.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_resource_flow_anomaly_review (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      review_id          varchar NOT NULL,
      anomaly_id         varchar NOT NULL,
      action             varchar NOT NULL,
      reason             varchar,
      reviewer_did       varchar NOT NULL,
      reviewer_facade    varchar,
      thread_post_uri    varchar,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar,
      root_did           varchar,
      root_did_hash      varchar,
      root_identity_addr varchar,
      facade_did         varchar,
      facade_did_hash    varchar,
      identity_method    varchar,
      migration_status   varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_anomaly_review_anomaly  ON vertex_resource_flow_anomaly_review (anomaly_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anomaly_review_observed ON vertex_resource_flow_anomaly_review (observed_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anomaly_review_reviewer ON vertex_resource_flow_anomaly_review (reviewer_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  // Latest review action per anomaly. RisingWave streaming MV; bounded
  // by the cardinality of vertex_resource_flow_anomaly (a few thousand
  // at most for the foreseeable future), and the SELECT-MAX shape is
  // safe (varchar MAX over a single small partition).
  await sql`
    CREATE MATERIALIZED VIEW mv_resource_flow_anomaly_review_latest AS
      SELECT
        anomaly_id,
        MAX(observed_at) AS latest_observed_at,
        COUNT(*)         AS review_count
      FROM vertex_resource_flow_anomaly_review
      GROUP BY anomaly_id
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_anomaly_review_latest`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_anomaly_review_reviewer`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_anomaly_review_observed`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_anomaly_review_anomaly`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_resource_flow_anomaly_review`.execute(db);
  await sql`FLUSH`.execute(db);
}
