import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * vertex_gmail_* + edge_gmail_* tables for etzhayyim-project-gmail (gm4il0x1).
 *
 * P10v2 GraphAr-native: 1 AT record = 1 row, typed columns, no val_json.
 * RLS 3-col (org_id/user_id/actor_id) + created_at required on every table.
 *
 * Columns align with records emitted by
 *   60-apps/etzhayyim-project-gmail/appview/etzhayyim-wasm-gmail-gm4il0x1/src/app.ts
 * via collection NSIDs com.etzhayyim.apps.gmail.{account,thread,email,contact,syncJob,
 * outboundEmail,accountBinding,phishingAlert,labelAction,triageResult}.
 *
 * Private text fields (subject, snippet, body_preview, to/cc/bcc) are
 * Signal-encrypted (`signal:v1:{ciphertext}`) at write time by the PDS
 * pipeline (W Protocol). Columns themselves store varchar, ciphertext
 * indistinguishable from plaintext varchar at schema level.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gmail_account (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      account_did       VARCHAR,
      email             VARCHAR,
      display_name      VARCHAR,
      status            VARCHAR,
      scope             VARCHAR,
      history_id        VARCHAR,
      last_sync_at      VARCHAR,
      connected_at      VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gmail_thread (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      thread_id         VARCHAR,
      account_did       VARCHAR,
      email             VARCHAR,
      subject           VARCHAR,
      snippet           VARCHAR,
      message_count     BIGINT,
      history_id        VARCHAR,
      labels            VARCHAR,
      participants      VARCHAR,
      last_message_at   VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gmail_email (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      email_id          VARCHAR,
      thread_id         VARCHAR,
      message_id        VARCHAR,
      account_did       VARCHAR,
      account_email     VARCHAR,
      from_addr         VARCHAR,
      from_name         VARCHAR,
      to_addrs          VARCHAR,
      cc_addrs          VARCHAR,
      bcc_addrs         VARCHAR,
      reply_to          VARCHAR,
      return_path       VARCHAR,
      subject           VARCHAR,
      snippet           VARCHAR,
      body_preview      VARCHAR,
      body_urls_json    VARCHAR,
      labels            VARCHAR,
      direction         VARCHAR,
      spf_result        VARCHAR,
      dkim_result       VARCHAR,
      dmarc_result      VARCHAR,
      history_id        VARCHAR,
      size_estimate     BIGINT,
      internal_date     VARCHAR,
      sent_at           VARCHAR,
      received_at       VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gmail_contact (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      contact_did       VARCHAR,
      email             VARCHAR,
      display_name      VARCHAR,
      first_seen_at     VARCHAR,
      last_seen_at      VARCHAR,
      message_count     BIGINT,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gmail_sync_job (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      job_id            VARCHAR,
      account_did       VARCHAR,
      email             VARCHAR,
      kind              VARCHAR,
      status            VARCHAR,
      max_results       BIGINT,
      start_history_id  VARCHAR,
      end_history_id    VARCHAR,
      messages_synced   BIGINT,
      error             VARCHAR,
      started_at        VARCHAR,
      completed_at      VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gmail_outbound_email (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      outbound_id       VARCHAR,
      account_did       VARCHAR,
      account_email     VARCHAR,
      to_addrs          VARCHAR,
      cc_addrs          VARCHAR,
      bcc_addrs         VARCHAR,
      subject           VARCHAR,
      body_preview      VARCHAR,
      thread_id         VARCHAR,
      in_reply_to       VARCHAR,
      gmail_message_id  VARCHAR,
      status            VARCHAR,
      error             VARCHAR,
      sent_at           VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gmail_phishing_alert (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      alert_id          VARCHAR,
      email_id          VARCHAR,
      from_addr         VARCHAR,
      subject           VARCHAR,
      spf_result        VARCHAR,
      dkim_result       VARCHAR,
      dmarc_result      VARCHAR,
      body_urls         VARCHAR,
      phishing_score    BIGINT,
      reasons           VARCHAR,
      detected_at       VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  // ── Edges ──
  // email ∈ thread
  await sql`
    CREATE TABLE IF NOT EXISTS edge_gmail_email_in_thread (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      email_id          VARCHAR,
      thread_id         VARCHAR,
      position          BIGINT,
      created_at        VARCHAR
    )
  `.execute(db);

  // email sent from contact
  await sql`
    CREATE TABLE IF NOT EXISTS edge_gmail_email_from_contact (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      email_id          VARCHAR,
      contact_did       VARCHAR,
      created_at        VARCHAR
    )
  `.execute(db);

  // email addressed to contact (to/cc/bcc unified by field)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_gmail_email_to_contact (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      email_id          VARCHAR,
      contact_did       VARCHAR,
      field             VARCHAR,
      created_at        VARCHAR
    )
  `.execute(db);

  // account owns thread
  await sql`
    CREATE TABLE IF NOT EXISTS edge_gmail_account_owns_thread (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      account_did       VARCHAR,
      thread_id         VARCHAR,
      created_at        VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_gmail_account_owns_thread`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gmail_email_to_contact`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gmail_email_from_contact`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gmail_email_in_thread`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gmail_phishing_alert`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gmail_outbound_email`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gmail_sync_job`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gmail_contact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gmail_email`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gmail_thread`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gmail_account`.execute(db);
}
