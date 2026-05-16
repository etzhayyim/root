import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (reaction = shosha's autonomous response to upstream actor
//          commits. Rationale text + confidence; no Tier-3 PII.)

/**
 * shosha.gftd.ai Phase 2a — cross-actor reactive layer.
 *
 * Lets shosha react to upstream actor commits (oil-trading, cargo, port,
 * etc.) via polling BPMN. Pull-based, AT-Protocol-friendly, no upstream
 * actor changes needed.
 *
 * Tables (2 vertex + 1 streaming MV):
 *   vertex_shosha_consumer_cursor   per (consumer_id) cursor over
 *                                    upstream `vertex_repo_record.seq`
 *                                    so resumed scans only see new rows
 *   vertex_shosha_reaction          one row per shosha-generated
 *                                    response (trade idea / hedge
 *                                    suggestion / risk alert / pass)
 *   mv_shosha_reaction_count_by_upstream
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_consumer_cursor (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      consumer_id varchar NOT NULL,
      upstream_did varchar NOT NULL,
      collection_prefix varchar,
      last_seq bigint NOT NULL,
      last_ts_ms bigint,
      last_seen_at varchar,
      records_seen bigint,
      reactions_emitted bigint,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_reaction (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      reaction_id varchar NOT NULL,
      upstream_did varchar NOT NULL,
      upstream_collection varchar,
      upstream_seq bigint,
      upstream_rkey varchar,
      upstream_record_vid varchar,
      reaction_type varchar NOT NULL,
      commodity varchar,
      direction varchar,
      target_action varchar,
      rationale varchar,
      confidence double precision,
      llm_model varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_reaction_count_by_upstream AS
      SELECT
        upstream_did,
        reaction_type,
        COUNT(*) AS reaction_count,
        AVG(COALESCE(confidence, 0)) AS avg_confidence
      FROM vertex_shosha_reaction
      WHERE status = 'active'
      GROUP BY upstream_did, reaction_type;
  `.execute(db);

  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_consumer_cursor TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_consumer_cursor TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_reaction        TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_reaction        TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON vertex_shosha_reaction        FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_shosha_reaction        FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_shosha_consumer_cursor FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_shosha_consumer_cursor FROM root`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_reaction_count_by_upstream`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_reaction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_consumer_cursor`.execute(db);
}
