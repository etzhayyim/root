import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * 外部 SaaS サービスアカウント管理 + オフボーディングワークフロー schema
 *
 * critical rule: rw-only-for-operational-domain-data
 *   AT record は social publish 専用。service account 管理・解約タスク・
 *   認証試行ログ・アウトバウンドアクションはすべて RW のみ。
 *
 * テーブル構成:
 *   vertex_kaisya_service_account  — 外部 SaaS アカウント (SendGrid / Stripe / etc.)
 *   vertex_kaisya_offboarding_task — 解約/オフボーディングタスク
 *   vertex_kaisya_auth_attempt     — 認証試行ログ
 *   vertex_kaisya_outbound_action  — メール送信 / API コール / ブラウザ操作ログ
 *   edge_offboarding_targets_account  — task → service_account
 *   edge_task_attempted_auth          — task → auth_attempt
 *   edge_task_triggered_action        — task → outbound_action
 *   mv_offboarding_dashboard      — アクティブ解約タスク + SLA 残時間
 *   mv_auth_method_stats          — 認証メソッド別成功率 (provider × method)
 *
 * status enum (service_account):
 *   active | cancellation_pending | cancelled | suspended | failed
 *
 * task status enum:
 *   queued | in_progress | waiting_human | support_email_sent | completed | failed
 *
 * resolution enum:
 *   cancelled_via_ui | cancelled_via_api | cancelled_via_support_email | abandoned
 *
 * auth_attempt method enum:
 *   browser_form | api_basic_auth | password_reset_flow | ropg | playwright_headed
 *
 * auth_attempt status enum:
 *   success | failed_wrong_creds | failed_bot_detection |
 *   failed_grant_type | failed_extension_block | failed_timeout
 *
 * action_kind enum:
 *   send_email | api_call | password_reset_trigger | browser_form_submit
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_kaisya_service_account ─────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_service_account (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      rkey                VARCHAR,
      repo                VARCHAR,

      provider            VARCHAR NOT NULL,
      external_acct_id    VARCHAR,
      login_email         VARCHAR NOT NULL,
      status              VARCHAR NOT NULL DEFAULT 'active',
      plan_name           VARCHAR,
      overdue_amount_usd  INTEGER  NOT NULL DEFAULT 0,
      metadata_json       TEXT,

      actor_did           VARCHAR NOT NULL,
      org_did             VARCHAR NOT NULL,
      created_at          VARCHAR NOT NULL,
      updated_at          VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_service_account_provider_status
            ON vertex_kaisya_service_account (provider, status)`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_service_account_login_email
            ON vertex_kaisya_service_account (login_email)`.execute(db);

  // ── vertex_kaisya_offboarding_task ────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_offboarding_task (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,

      service_account_vid   VARCHAR NOT NULL,
      task_kind             VARCHAR NOT NULL DEFAULT 'cancel_account',
      status                VARCHAR NOT NULL DEFAULT 'queued',
      resolution            VARCHAR,
      spiff_instance_id     VARCHAR,
      deadline_at           VARCHAR,
      attempt_count         INTEGER  NOT NULL DEFAULT 0,
      last_error            TEXT,

      actor_did             VARCHAR NOT NULL,
      org_did               VARCHAR NOT NULL,
      created_at            VARCHAR NOT NULL,
      completed_at          VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_offboarding_task_status_created
            ON vertex_kaisya_offboarding_task (status, created_at)`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_offboarding_task_account
            ON vertex_kaisya_offboarding_task (service_account_vid, status)`.execute(db);

  // ── vertex_kaisya_auth_attempt ────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_auth_attempt (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,

      service_account_vid   VARCHAR NOT NULL,
      method                VARCHAR NOT NULL,
      status                VARCHAR NOT NULL,
      error_code            VARCHAR,
      error_detail          TEXT,
      bot_detection_kind    VARCHAR,

      actor_did             VARCHAR NOT NULL,
      org_did               VARCHAR NOT NULL,
      created_at            VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_auth_attempt_account_created
            ON vertex_kaisya_auth_attempt (service_account_vid, created_at)`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_auth_attempt_method_status
            ON vertex_kaisya_auth_attempt (method, status)`.execute(db);

  // ── vertex_kaisya_outbound_action ─────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_outbound_action (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,

      action_kind       VARCHAR NOT NULL,
      target_url        VARCHAR,
      to_address        VARCHAR,
      subject           VARCHAR,
      status            VARCHAR NOT NULL DEFAULT 'pending',
      external_id       VARCHAR,
      http_status       INTEGER,

      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL,
      created_at        VARCHAR NOT NULL,
      completed_at      VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_outbound_action_kind_status
            ON vertex_kaisya_outbound_action (action_kind, status, created_at)`.execute(db);

  // ── edges ─────────────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_offboarding_targets_account (
      edge_id     VARCHAR PRIMARY KEY,
      src_vid     VARCHAR NOT NULL,
      dst_vid     VARCHAR NOT NULL,
      _seq        BIGINT,
      created_at  VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`CREATE UNIQUE INDEX IF NOT EXISTS idx_edge_offboarding_targets_account_pair
            ON edge_offboarding_targets_account (src_vid, dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_task_attempted_auth (
      edge_id    VARCHAR PRIMARY KEY,
      src_vid    VARCHAR NOT NULL,
      dst_vid    VARCHAR NOT NULL,
      _seq       BIGINT,
      sequence   INTEGER NOT NULL DEFAULT 1,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`CREATE UNIQUE INDEX IF NOT EXISTS idx_edge_task_attempted_auth_pair
            ON edge_task_attempted_auth (src_vid, dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_task_triggered_action (
      edge_id    VARCHAR PRIMARY KEY,
      src_vid    VARCHAR NOT NULL,
      dst_vid    VARCHAR NOT NULL,
      _seq       BIGINT,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`CREATE UNIQUE INDEX IF NOT EXISTS idx_edge_task_triggered_action_pair
            ON edge_task_triggered_action (src_vid, dst_vid)`.execute(db);

  // ── mv_offboarding_dashboard ──────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_offboarding_dashboard AS
    SELECT
      t.vertex_id                                    AS task_vid,
      a.provider,
      a.external_acct_id,
      a.login_email,
      a.overdue_amount_usd,
      t.task_kind,
      t.status,
      t.resolution,
      t.deadline_at,
      t.attempt_count,
      t.spiff_instance_id,
      COUNT(DISTINCT auth.vertex_id)                 AS auth_attempt_count,
      MAX(auth.created_at)                           AS last_auth_at,
      COUNT(DISTINCT act.vertex_id)                  AS action_count,
      MAX(act.created_at)                            AS last_action_at
    FROM vertex_kaisya_offboarding_task t
    JOIN vertex_kaisya_service_account a
      ON a.vertex_id = t.service_account_vid
    LEFT JOIN edge_task_attempted_auth ea
      ON ea.src_vid = t.vertex_id
    LEFT JOIN vertex_kaisya_auth_attempt auth
      ON auth.vertex_id = ea.dst_vid
    LEFT JOIN edge_task_triggered_action eta
      ON eta.src_vid = t.vertex_id
    LEFT JOIN vertex_kaisya_outbound_action act
      ON act.vertex_id = eta.dst_vid
    WHERE t.status NOT IN ('completed', 'failed')
    GROUP BY
      t.vertex_id, a.provider, a.external_acct_id, a.login_email,
      a.overdue_amount_usd, t.task_kind, t.status, t.resolution,
      t.deadline_at, t.attempt_count, t.spiff_instance_id
  `.execute(db);

  // ── mv_auth_method_stats ──────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_auth_method_stats AS
    SELECT
      a.provider,
      auth.method,
      auth.bot_detection_kind,
      COUNT(*)                                                              AS total,
      COUNT(*) FILTER (WHERE auth.status = 'success')                      AS success_count,
      COUNT(*) FILTER (WHERE auth.status = 'failed_bot_detection')         AS bot_blocked_count,
      COUNT(*) FILTER (WHERE auth.status = 'failed_extension_block')       AS ext_blocked_count,
      COUNT(*) FILTER (WHERE auth.status = 'failed_wrong_creds')           AS wrong_creds_count,
      MAX(auth.created_at)                                                  AS last_attempt_at
    FROM vertex_kaisya_auth_attempt auth
    JOIN edge_task_attempted_auth ea     ON ea.dst_vid = auth.vertex_id
    JOIN vertex_kaisya_offboarding_task t ON t.vertex_id = ea.src_vid
    JOIN vertex_kaisya_service_account a  ON a.vertex_id = t.service_account_vid
    GROUP BY a.provider, auth.method, auth.bot_detection_kind
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_auth_method_stats`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_offboarding_dashboard`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_task_triggered_action_pair`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_task_triggered_action`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_task_attempted_auth_pair`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_task_attempted_auth`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_offboarding_targets_account_pair`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_offboarding_targets_account`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_outbound_action_kind_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kaisya_outbound_action`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_auth_attempt_method_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_auth_attempt_account_created`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kaisya_auth_attempt`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_offboarding_task_account`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_offboarding_task_status_created`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kaisya_offboarding_task`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_service_account_login_email`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_service_account_provider_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kaisya_service_account`.execute(db);
}
