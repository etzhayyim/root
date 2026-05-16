import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B  (curated audit log; no Tier-3 PII).

/**
 * karma.gftd.ai — rebirth severance log (Phase K3).
 *
 * Audit trail for the rebirth.severFollows step. Records every
 * follow-edge action taken during organism rebirth:
 *   - outgoing-deleted: org's own app.bsky.graph.follow records were
 *                         dispatched for deletion via PDS
 *   - incoming-frozen:  external followers retain stale follows;
 *                         we record the severance event but cannot
 *                         unilaterally update remote follow records
 *
 * Pure append-only ledger; one row per (rebirth_did, follow_uri).
 *
 * Tables (1 vertex + 1 streaming MV):
 *   vertex_karma_rebirth_severance_log
 *   mv_karma_rebirth_severance_summary  per-DID severance counts
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_karma_rebirth_severance_log (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      severance_id varchar NOT NULL,
      rebirth_did varchar NOT NULL,
      follow_uri varchar NOT NULL,
      author_did varchar NOT NULL,
      subject_did varchar NOT NULL,
      action varchar NOT NULL,
      dispatch_outcome varchar,
      dispatch_error varchar,
      ts_ms bigint NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_sev_rebirth_did ON vertex_karma_rebirth_severance_log (rebirth_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sev_action ON vertex_karma_rebirth_severance_log (action)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sev_ts ON vertex_karma_rebirth_severance_log (ts_ms)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_karma_rebirth_severance_summary AS
    SELECT
      rebirth_did,
      action,
      count(*) AS n
    FROM vertex_karma_rebirth_severance_log
    GROUP BY rebirth_did, action
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_karma_rebirth_severance_summary`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_karma_rebirth_severance_log`.execute(db);
}
