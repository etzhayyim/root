import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_yorishiroNuro_offer — cashback offer discovered on NURO MyPage
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroNuro_offer (
      vertex_id       VARCHAR PRIMARY KEY,
      campaign_code   VARCHAR NOT NULL,
      title           VARCHAR,
      amount_jpy      BIGINT,
      window_open     VARCHAR,
      window_close    VARCHAR,
      job_id          VARCHAR,
      discovered_at   VARCHAR,
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroNuro_offer_campaign_code
      ON vertex_yorishiroNuro_offer (campaign_code)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroNuro_offer_job_id
      ON vertex_yorishiroNuro_offer (job_id)
  `.execute(db);

  // vertex_yorishiroNuro_claimJob — cashback claim job (pending/done)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroNuro_claimJob (
      vertex_id         VARCHAR PRIMARY KEY,
      job_id            VARCHAR NOT NULL,
      campaign_code     VARCHAR NOT NULL,
      bank_vault_key    VARCHAR,
      idempotency_key   VARCHAR,
      provider          VARCHAR,
      entry_url         VARCHAR,
      status            VARCHAR NOT NULL DEFAULT 'pending',
      created_at        VARCHAR NOT NULL,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      sensitivity_ord   BIGINT NOT NULL DEFAULT 2,
      owner_did         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroNuro_claimJob_job_id
      ON vertex_yorishiroNuro_claimJob (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroNuro_claimJob_campaign_code
      ON vertex_yorishiroNuro_claimJob (campaign_code)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroNuro_claimJob_idempotency_key
      ON vertex_yorishiroNuro_claimJob (idempotency_key)
  `.execute(db);

  // vertex_yorishiroNuro_claimReceipt — completed cashback claim receipt
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroNuro_claimReceipt (
      vertex_id             VARCHAR PRIMARY KEY,
      receipt_id            VARCHAR NOT NULL,
      job_id                VARCHAR NOT NULL,
      campaign_code         VARCHAR NOT NULL,
      receipt_number        VARCHAR,
      screenshot_blob_key   VARCHAR,
      amount_jpy            BIGINT,
      submitted_at          VARCHAR,
      created_at            VARCHAR NOT NULL,
      org_id                VARCHAR,
      user_id               VARCHAR,
      actor_id              VARCHAR,
      sensitivity_ord       BIGINT NOT NULL DEFAULT 2,
      owner_did             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroNuro_claimReceipt_job_id
      ON vertex_yorishiroNuro_claimReceipt (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroNuro_claimReceipt_campaign_code
      ON vertex_yorishiroNuro_claimReceipt (campaign_code)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_yorishiroNuro_claimReceipt`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroNuro_claimJob`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroNuro_offer`.execute(db);
}
