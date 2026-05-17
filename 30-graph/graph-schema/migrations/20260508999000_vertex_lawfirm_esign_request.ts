import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * lawfirm.etzhayyim.com e-sign request mirror.
 * Tracks DocuSign / AdobeSign / RazorpaySign envelopes per matter.
 *
 * Status lifecycle: draft → sent → delivered → completed | declined | expired.
 * Persisted by lawfirm.esign.request, updated by lawfirm.esign.webhook.
 *
 * ADR-0036 Hyperdrive direct.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_esign_request (
      vertex_id        varchar PRIMARY KEY,
      envelope_id      varchar NOT NULL,
      provider         varchar DEFAULT 'docusign',
      document_kind    varchar NOT NULL,
      matter_uri       varchar,
      recipients_json  varchar,
      status           varchar DEFAULT 'draft',
      expires_at       varchar,
      callback_url     varchar,
      completed_at     varchar,
      raw_status_json  varchar,
      updated_at       varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 200,
      owner_did        varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_esign_active AS
    SELECT envelope_id, provider, document_kind, matter_uri, status,
           expires_at, created_at, updated_at
    FROM vertex_lawfirm_esign_request
    WHERE status IN ('sent', 'delivered')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_esign_active`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_esign_request`.execute(db);
}
