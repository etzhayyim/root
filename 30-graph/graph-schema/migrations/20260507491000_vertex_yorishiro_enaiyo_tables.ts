import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_yorishiroEnaiyo_draftNaiyo — e-naiyo draft record
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroEnaiyo_draftNaiyo (
      vertex_id       VARCHAR PRIMARY KEY,
      draft_id        VARCHAR NOT NULL,
      template_type   VARCHAR,
      payment_method  VARCHAR,
      vault_ref       VARCHAR,
      docx_blob_key   VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'draft',
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_draftNaiyo_draft_id
      ON vertex_yorishiroEnaiyo_draftNaiyo (draft_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_draftNaiyo_status
      ON vertex_yorishiroEnaiyo_draftNaiyo (status)
  `.execute(db);

  // vertex_yorishiroEnaiyo_docxBlob — docx render job
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroEnaiyo_docxBlob (
      vertex_id       VARCHAR PRIMARY KEY,
      job_id          VARCHAR NOT NULL,
      draft_id        VARCHAR NOT NULL,
      blob_key        VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_docxBlob_job_id
      ON vertex_yorishiroEnaiyo_docxBlob (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_docxBlob_draft_id
      ON vertex_yorishiroEnaiyo_docxBlob (draft_id)
  `.execute(db);

  // vertex_yorishiroEnaiyo_batchJob — batch submission job (差込差出し)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroEnaiyo_batchJob (
      vertex_id           VARCHAR PRIMARY KEY,
      batch_id            VARCHAR NOT NULL,
      draft_ids           TEXT,
      csv_blob_key        VARCHAR,
      template_blob_key   VARCHAR,
      mode                VARCHAR,
      provider            VARCHAR,
      entry_url           VARCHAR,
      format              VARCHAR,
      status              VARCHAR NOT NULL DEFAULT 'pending',
      count               BIGINT,
      created_at          VARCHAR NOT NULL,
      org_id              VARCHAR,
      user_id             VARCHAR,
      actor_id            VARCHAR,
      sensitivity_ord     BIGINT NOT NULL DEFAULT 2,
      owner_did           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_batchJob_batch_id
      ON vertex_yorishiroEnaiyo_batchJob (batch_id)
  `.execute(db);

  // vertex_yorishiroEnaiyo_submitJob — single submission job
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroEnaiyo_submitJob (
      vertex_id       VARCHAR PRIMARY KEY,
      job_id          VARCHAR NOT NULL,
      draft_id        VARCHAR NOT NULL,
      mode            VARCHAR,
      provider        VARCHAR,
      entry_url       VARCHAR,
      format          VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_submitJob_job_id
      ON vertex_yorishiroEnaiyo_submitJob (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_submitJob_draft_id
      ON vertex_yorishiroEnaiyo_submitJob (draft_id)
  `.execute(db);

  // vertex_yorishiroEnaiyo_receipt — submission receipt
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroEnaiyo_receipt (
      vertex_id               VARCHAR PRIMARY KEY,
      receipt_id              VARCHAR NOT NULL,
      job_id                  VARCHAR NOT NULL,
      draft_id                VARCHAR NOT NULL,
      receipt_number          VARCHAR,
      receipt_pdf_blob_key    VARCHAR,
      submitted_at            VARCHAR,
      created_at              VARCHAR NOT NULL,
      org_id                  VARCHAR,
      user_id                 VARCHAR,
      actor_id                VARCHAR,
      sensitivity_ord         BIGINT NOT NULL DEFAULT 2,
      owner_did               VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_receipt_job_id
      ON vertex_yorishiroEnaiyo_receipt (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroEnaiyo_receipt_draft_id
      ON vertex_yorishiroEnaiyo_receipt (draft_id)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_yorishiroEnaiyo_receipt`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroEnaiyo_submitJob`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroEnaiyo_batchJob`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroEnaiyo_docxBlob`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroEnaiyo_draftNaiyo`.execute(db);
}
