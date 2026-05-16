import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * vertex_api_key — sk_live_* / sk_test_* API key store.
 *
 * Referenced by:
 *   - 50-infra/cloudflare/workers/atproto/src/handlers/register.ts (createApiKey)
 *   - 50-infra/cloudflare/workers/atproto/src/auth/verify.ts (verifyApiKey)
 *
 * Schema source of truth — was previously expected to exist but never
 * created. PDS authenticate() rejected all sk_live_* tokens with 401
 * because the table didn't exist (silent error swallow in catch block).
 *
 * Columns mirror the verify.ts and listApiKeys SELECT shape.
 */

export async function up(db: Kysely<any>): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS vertex_api_key (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    key_hash        VARCHAR,
    key_prefix      VARCHAR,
    name            VARCHAR,
    scopes          VARCHAR,
    status          VARCHAR,
    last_used_at    VARCHAR,
    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_api_key_hash
    ON vertex_api_key(key_hash)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_api_key_owner
    ON vertex_api_key(owner_did)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_api_key_owner`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_api_key_hash`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_api_key`.execute(db);
  await sql`FLUSH`.execute(db);
}
