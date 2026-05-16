import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/** Migration 0050: outbox, governance, and page-domain support tables. */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS vertex_write_outbox (
    vertex_id     VARCHAR PRIMARY KEY,
    write_id      VARCHAR NOT NULL,
    write_type    VARCHAR NOT NULL,
    payload_json  VARCHAR NOT NULL,
    app_nanoid    VARCHAR,
    failed_at     VARCHAR,
    error_message VARCHAR,
    retry_count   BIGINT DEFAULT 0,
    created_date  VARCHAR,
    owner_did     VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_governance_policy (
    vertex_id   VARCHAR PRIMARY KEY,
    name        VARCHAR NOT NULL,
    kind        VARCHAR,
    standard    VARCHAR,
    repo        VARCHAR,
    collection  VARCHAR,
    status      VARCHAR,
    value_json  VARCHAR,
    created_at  VARCHAR,
    owner_did   VARCHAR
  )`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_page_domain ON vertex_page(domain)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_page_domain`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_governance_policy`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_write_outbox`.execute(db);
}
