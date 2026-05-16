import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * vertex_ipaddress_access_log — PII Tier 3 visitor access log.
 *
 * Design decision: ADR-0018 Tier 3 — NOT written via AT Repo createRecord
 * (those are public + federable). Instead, PDS OCEL middleware inserts
 * directly via Hyperdrive on every XRPC call. ipaddress.gftd.ai actor owns
 * the rows logically but they never become AT Records.
 *
 * Written by: 50-infra/cloudflare/workers/atproto/src/middleware/index.ts
 *   `ocelLogging` middleware fire-and-forget after response.
 *
 * Ingest scope: every XRPC request (except getOcel / emitOcel).
 * Bots and crawlers are included — UA is kept as-is for analysis.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ipaddress_access_log (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      ip                VARCHAR,
      ip_did            VARCHAR,
      ip_version        BIGINT,
      user_agent        VARCHAR,
      nsid              VARCHAR,
      http_method       VARCHAR,
      path              VARCHAR,
      status            BIGINT,
      latency_ms        BIGINT,
      colo              VARCHAR,
      country           VARCHAR,
      referer           VARCHAR,
      auth_level        VARCHAR,
      caller_did        VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_ipaddress_access_log`.execute(db);
}
