import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * M365 tenant user cache + per-user sync watermark.
 *
 * Consumers: m365-ingest T1 actor pipelines. Replaces ad-hoc
 * ~/.etzhayyim/sync_state.json JSON file with graph-native state.
 *
 * vertex_m365_user  — tenant user enumeration cache (refreshed by enumerateUsers
 *                     step). Uses upn as natural key.
 * vertex_m365_sync_state — per-upn sync watermark per data-kind
 *                          (email/files/calendar). Idempotent upsert.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_m365_user (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      upn               VARCHAR,
      user_id           VARCHAR,
      display_name      VARCHAR,
      mail              VARCHAR,
      account_enabled   BOOLEAN,
      upn_domain        VARCHAR,
      first_seen_at     VARCHAR,
      last_seen_at      VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_m365_sync_state (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      upn                VARCHAR,
      data_kind          VARCHAR,
      last_sync_at       VARCHAR,
      last_received_at   VARCHAR,
      record_count       BIGINT,
      error_count        BIGINT,
      last_error         VARCHAR,
      last_error_at      VARCHAR,
      throttle_until     VARCHAR,
      status             VARCHAR,
      run_id             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      org_id             VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_m365_user_upn ON vertex_m365_user (upn)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_m365_user_domain ON vertex_m365_user (upn_domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_m365_sync_upn_kind ON vertex_m365_sync_state (upn, data_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_m365_sync_status ON vertex_m365_sync_state (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_m365_sync_state`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_m365_user`.execute(db);
}
