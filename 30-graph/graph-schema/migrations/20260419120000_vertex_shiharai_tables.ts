import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_shiharai_* + edge_shiharai_* tables for etzhayyim-project-shiharai (sh1h4r41).
 *
 * P10v2 GraphAr-native: 1 AT record = 1 row, typed columns, no val_json.
 * RLS 3-col (org_id/user_id/actor_id) + created_at required on every table.
 *
 * Columns align with records emitted by
 *   60-apps/etzhayyim-project-shiharai/appview/etzhayyim-wasm-shiharai-sh1h4r41/src/app.ts
 * via collection NSIDs com.etzhayyim.apps.shiharai.{bill,payment,biller,recurring,
 * job,jobResult}.
 *
 * Credential material is NEVER stored server-side. vault.etzhayyim.com wraps
 * credentials with an ephemeral key (ADR-0029 injectWorkerSecret pattern)
 * and hands them to a local Playwright daemon; the Worker sees plaintext
 * creds only transiently in memory during a single job dispatch window
 * and never persists them to these tables or anywhere else.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shiharai_biller (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      biller_handle      VARCHAR,
      display_name       VARCHAR,
      country            VARCHAR,
      site_url           VARCHAR,
      pay_url            VARCHAR,
      recurring_url      VARCHAR,
      adapter            VARCHAR,
      auth_kind          VARCHAR,
      keychain_service   VARCHAR,
      capabilities       VARCHAR,
      notes              VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shiharai_bill (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      bill_id            VARCHAR,
      issuer             VARCHAR,
      biller_handle      VARCHAR,
      amount_jpy         BIGINT,
      currency           VARCHAR,
      due_date           VARCHAR,
      customer_number    VARCHAR,
      invoice_number     VARCHAR,
      pay_url            VARCHAR,
      method             VARCHAR,
      source_email_id    VARCHAR,
      state              VARCHAR,
      extracted_at       VARCHAR,
      paid_at            VARCHAR,
      cancelled_at       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shiharai_payment (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      payment_id         VARCHAR,
      bill_id            VARCHAR,
      biller_handle      VARCHAR,
      amount_jpy         BIGINT,
      method             VARCHAR,
      result_tx_id       VARCHAR,
      page_snapshot_cid  VARCHAR,
      approved_by_did    VARCHAR,
      approval_token_hash VARCHAR,
      committed_at       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shiharai_recurring (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      recurring_id       VARCHAR,
      biller_handle      VARCHAR,
      customer_number    VARCHAR,
      pay_method         VARCHAR,
      state              VARCHAR,
      registered_at      VARCHAR,
      cancelled_at       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shiharai_job (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      job_id             VARCHAR,
      bill_id            VARCHAR,
      biller_handle      VARCHAR,
      method             VARCHAR,
      pay_url            VARCHAR,
      state              VARCHAR,
      require_confirm    VARCHAR,
      daemon_id          VARCHAR,
      enqueued_at        VARCHAR,
      dispatched_at      VARCHAR,
      started_at         VARCHAR,
      finished_at        VARCHAR,
      expires_at         VARCHAR,
      last_error         VARCHAR,
      page_snapshot_cid  VARCHAR,
      result_tx_id       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shiharai_job_result (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      job_id             VARCHAR,
      outcome            VARCHAR,
      page_snapshot_cid  VARCHAR,
      result_tx_id       VARCHAR,
      error_message      VARCHAR,
      reported_at        VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  // ── Edges ──
  // bill → biller
  await sql`
    CREATE TABLE IF NOT EXISTS edge_shiharai_bill_for_biller (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      bill_id            VARCHAR,
      biller_handle      VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  // payment → bill (settles)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_shiharai_payment_settles_bill (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      payment_id         VARCHAR,
      bill_id            VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  // job → bill (processes)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_shiharai_job_processes_bill (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      job_id             VARCHAR,
      bill_id            VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  // job_result → job (reports)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_shiharai_result_reports_job (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      job_id             VARCHAR,
      outcome            VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  // recurring → biller (binds)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_shiharai_recurring_for_biller (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      recurring_id       VARCHAR,
      biller_handle      VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  // bill → source email (derived from)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_shiharai_bill_from_email (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      bill_id            VARCHAR,
      source_email_id    VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_shiharai_bill_from_email`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shiharai_recurring_for_biller`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shiharai_result_reports_job`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shiharai_job_processes_bill`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shiharai_payment_settles_bill`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shiharai_bill_for_biller`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shiharai_job_result`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shiharai_job`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shiharai_recurring`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shiharai_payment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shiharai_bill`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shiharai_biller`.execute(db);
}
