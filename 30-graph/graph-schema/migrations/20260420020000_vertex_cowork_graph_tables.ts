import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_cowork_graph_* tables for etzhayyim-project-cowork-graph (c0w0rkg1).
 *
 * P10v2 GraphAr-native: 1 AT record = 1 row, typed columns, no val_json.
 * RLS 3-col (org_id/user_id/actor_id) + created_at required on every table.
 *
 * Columns align with records emitted by
 *   60-apps/etzhayyim-project-cowork/appview/etzhayyim-wasm-cowork-graph-c0w0rkg1/src/app.ts
 * via collection NSIDs com.etzhayyim.apps.coworkGraph.{syncJob, mailDraft, toolGrant}.
 *
 * Graph API token cache is stored in GRAPH_D1 (CF D1) per-worker — not here.
 * This migration covers only RisingWave (graph) projections of AT Repo records.
 *
 * PII: subject/body_preview は内部メタデータ (Signal field-encrypt 不要、
 * internal sensitivity_ord=2)。送信先 email は sensitivity_ord=3 で管理。
 */
export async function up(db: Kysely<any>): Promise<void> {
  // sync_job: Graph API token refresh + cron run 履歴
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cowork_graph_sync_job (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      job_type        VARCHAR,
      status          VARCHAR,
      actor_did       VARCHAR,
      error_message   VARCHAR,
      started_at      VARCHAR,
      done_at         VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR
    )
  `.execute(db);

  // mail_draft: Graph API 下書き記録 (draft_only ルール準拠)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cowork_graph_mail_draft (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      draft_id        VARCHAR,
      user_id         VARCHAR,
      subject         VARCHAR,
      to_addrs        VARCHAR,
      cc_addrs        VARCHAR,
      importance      VARCHAR,
      web_link        VARCHAR,
      approved_at     VARCHAR,
      sent_at         VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      actor_id        VARCHAR
    )
  `.execute(db);

  // tool_grant: MCP tool アクセス許可記録
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cowork_graph_tool_grant (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      caller_did      VARCHAR,
      tool_nsid       VARCHAR,
      effect          VARCHAR,
      granted_by      VARCHAR,
      expires_at      VARCHAR,
      revoked_at      VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR
    )
  `.execute(db);

  // mv_cowork_graph_draft_pending: 承認待ち下書き一覧
  // GROUP BY: draft_id は高々 1,000 件/day (低カーディナリティ) — MV 安全
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cowork_graph_draft_pending AS
    SELECT
      draft_id,
      user_id,
      subject,
      to_addrs,
      importance,
      web_link,
      created_at
    FROM vertex_cowork_graph_mail_draft
    WHERE approved_at IS NULL AND sent_at IS NULL
  `.execute(db);

  // インデックス
  await sql`
    CREATE INDEX IF NOT EXISTS idx_cowork_graph_sync_job_type
      ON vertex_cowork_graph_sync_job (job_type, created_date)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_cowork_graph_mail_draft_user
      ON vertex_cowork_graph_mail_draft (user_id, created_date)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_cowork_graph_tool_grant_caller
      ON vertex_cowork_graph_tool_grant (caller_did, tool_nsid)
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cowork_graph_draft_pending`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cowork_graph_tool_grant`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cowork_graph_mail_draft`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cowork_graph_sync_job`.execute(db);
}
