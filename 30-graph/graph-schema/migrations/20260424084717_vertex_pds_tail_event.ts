// tier: C   // ADR-0040: no DID (observational log; owner_did=atproto.etzhayyim.com PDS Worker).
//             Added to `30-graph/deps.toml [vertex_tier.tier_c.tables]`.
import { Kysely, sql } from 'kysely';

/**
 * PDS tail-event archive — multi-day capture of Worker tail events for NSID
 * traffic audit (complements the 3/60-min wrangler tail samples in
 * `90-docs/260424-nsid-traffic-audit.md`).
 *
 * Write path: `pds-tail-archiver` Worker consumes tail events from
 * `etzhayyim-pds-2603241700` via `tail_consumers` binding; each event → 1 row
 * via Kysely + Hyperdrive.
 *
 * Volume envelope (2026-04-24 60-min sample): ~20 events/min = 0.34/s,
 * ~30k/day. No concurrency concern on Hyperdrive / RW write quota.
 *
 * Guardrails:
 *   - PK = event_id (content hash / TID) — no duplicates, no high-cardinality
 *     GROUP BY on PK.
 *   - MV grouped by (nsid, outcome, hour): cardinality ~500 × 5 × 168 < 500k,
 *     well under the 30-graph MV memory guardrail (no MAX(varchar) over big
 *     group keys).
 *   - TIMESTAMPTZ for event_ts to enable date_trunc('hour', ...) in the MV.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // RisingWave rejects `VARCHAR(n)` size prefixes at CREATE TABLE — use bare
  // `varchar` (matches existing GraphAr convention, see recent migrations).
  await sql`
    CREATE TABLE vertex_pds_tail_event (
      event_id          varchar PRIMARY KEY,
      event_ts          timestamptz NOT NULL,
      script_name       varchar NOT NULL,
      script_version_id varchar,
      outcome           varchar NOT NULL,
      nsid              varchar,
      rpc_method        varchar,
      request_url       varchar,
      request_method    varchar,
      cf_ray            varchar,
      cf_country        varchar,
      cf_colo           varchar,
      client_ip         varchar,
      user_agent        varchar,
      wall_time_ms      int,
      cpu_time_ms       int,
      truncated         boolean,
      logs_text         text,
      exceptions_text   text,
      created_date      date NOT NULL,
      sensitivity_ord   int,
      owner_did         varchar,
      _seq              bigint
    );
  `.execute(db);
  await sql`CREATE INDEX idx_pds_tail_event_nsid_ts ON vertex_pds_tail_event (nsid, event_ts DESC);`.execute(db);
  await sql`CREATE INDEX idx_pds_tail_event_outcome_ts ON vertex_pds_tail_event (outcome, event_ts DESC);`.execute(db);
  await sql`CREATE INDEX idx_pds_tail_event_created_date ON vertex_pds_tail_event (created_date);`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_pds_tail_by_nsid_outcome_hour AS
    SELECT
      nsid,
      outcome,
      date_trunc('hour', event_ts) AS event_hour,
      COUNT(*) AS cnt
    FROM vertex_pds_tail_event
    WHERE nsid IS NOT NULL
    GROUP BY nsid, outcome, date_trunc('hour', event_ts);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_pds_tail_by_nsid_outcome_hour;`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pds_tail_event;`.execute(db);
}
