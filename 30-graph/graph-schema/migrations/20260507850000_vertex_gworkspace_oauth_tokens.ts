import { type Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const svc of ["gdrive", "gcontacts", "gdocs", "gmeet", "gsheets", "gslides"] as const) {
    await sql`
      CREATE TABLE IF NOT EXISTS vertex_${sql.raw(svc)}_oauth_token (
        vertex_id                VARCHAR PRIMARY KEY,
        account_did              VARCHAR,
        email                    VARCHAR,
        encrypted_refresh_token  VARCHAR,
        wrapped_data_key         VARCHAR,
        iv                       VARCHAR,
        scope                    VARCHAR,
        access_token_cache       VARCHAR,
        access_expires_at        BIGINT,
        status                   VARCHAR,
        cursor                   VARCHAR,
        history_id               VARCHAR,
        last_sync_at             VARCHAR,
        created_at               VARCHAR,
        updated_at               VARCHAR,
        actor_did                VARCHAR,
        org_did                  VARCHAR,
        at_did                   VARCHAR
      )
    `.execute(db);

    await sql`
      CREATE INDEX IF NOT EXISTS idx_${sql.raw(svc)}_oauth_token_email
        ON vertex_${sql.raw(svc)}_oauth_token (email)
    `.execute(db);

    await sql`
      CREATE INDEX IF NOT EXISTS idx_${sql.raw(svc)}_oauth_token_status
        ON vertex_${sql.raw(svc)}_oauth_token (status)
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const svc of ["gdrive", "gcontacts", "gdocs", "gmeet", "gsheets", "gslides"] as const) {
    await sql`DROP TABLE IF EXISTS vertex_${sql.raw(svc)}_oauth_token`.execute(db);
  }
}
