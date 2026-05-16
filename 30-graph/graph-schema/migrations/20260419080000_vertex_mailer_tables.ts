import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_mailer_* tables for the mailer inbound relay and outbound Resend path.
 *
 * P10v2 GraphAr-native: 1 AT record = 1 row, typed columns, no val_json.
 * RLS 3-col (org_id/user_id/actor_id) + created_at required on every table.
 *
 * Records emitted by 50-infra/cloudflare/workers/email-relay/worker.ts via
 *   ai.gftd.apps.mailer.{inboundEmail,emailBinding,inboundEmailStatus,outboundEmail}.
 *
 * PII (from/to/subject/body/headers) is AES-256-GCM encrypted at write time
 * by email-relay when DATA_ENCRYPTION_KEY is configured. Plaintext columns
 * carry literal "[encrypted]" in that mode; *_enc columns carry ciphertext.
 * When the key is absent, *_enc columns are NULL and content_protection =
 * "redacted-no-key".
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_mailer_inbound_email (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      message_id           VARCHAR,
      from_address         VARCHAR,
      from_address_hash    VARCHAR,
      from_address_enc     VARCHAR,
      to_local             VARCHAR,
      to_local_hash        VARCHAR,
      to_local_enc         VARCHAR,
      subject              VARCHAR,
      subject_enc          VARCHAR,
      body_text            VARCHAR,
      body_text_enc        VARCHAR,
      body_html            VARCHAR,
      headers_json         VARCHAR,
      headers_json_enc     VARCHAR,
      content_protection   VARCHAR,
      received_at_ms       BIGINT,
      status               VARCHAR,
      created_at           VARCHAR,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_mailer_email_binding (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      email                VARCHAR,
      did                  VARCHAR,
      direction            VARCHAR,
      verified             BIGINT,
      created_at_ms        BIGINT,
      created_at           VARCHAR,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_mailer_inbound_email_status (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      message_id           VARCHAR,
      status               VARCHAR,
      sender_did           VARCHAR,
      recipient_did        VARCHAR,
      convo_id             VARCHAR,
      delivered_at_ms      BIGINT,
      created_at           VARCHAR,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_mailer_outbound_email (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      message_id           VARCHAR,
      from_address         VARCHAR,
      to_address           VARCHAR,
      subject              VARCHAR,
      body_text            VARCHAR,
      body_html            VARCHAR,
      provider             VARCHAR,
      provider_message_id  VARCHAR,
      status               VARCHAR,
      error                VARCHAR,
      sent_at_ms           BIGINT,
      created_at           VARCHAR,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_mailer_outbound_email`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mailer_inbound_email_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mailer_email_binding`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mailer_inbound_email`.execute(db);
}
