import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_hc_* — hc.etzhayyim.com Human Computing Platform typed tables
 *
 * Replaces `catch_all_vertex` + `props::jsonb` JSON-scan reads with typed projections.
 * Graph-worker convention fallback (`nsidToConventionTable` in
 * 50-infra/cloudflare/workers/graph/worker.ts L340) maps
 * `com.etzhayyim.apps.hc.<entity>` → `vertex_hc_<snake_case(entity)>`.
 * All existing hc writers (`sdk.pds.dispatch({ type: "com.atproto.repo.createRecord",
 * collection: "com.etzhayyim.apps.hc.<entity>" })`) now land in these typed tables
 * instead of being skipped with "convention table not found" warnings.
 *
 * Design (ADR-0036 worker-direct Hyperdrive, ADR-0051 game-play-uploader):
 *   - 1 AT record = 1 row (GraphAr-native, no JSON props column)
 *   - camelCase payload field → snake_case column (graph-worker buildConventionRow)
 *   - VARCHAR / BIGINT / DOUBLE PRECISION / BOOLEAN only (RW unsupported NUMERIC)
 *   - RLS 3 columns (org_id/user_id/actor_id) + created_at on every table
 *   - sensitivity_ord: 100 public (task/assignment/contract_acceptance),
 *                     200 internal (sp_*, worker_intake metadata, review),
 *                     300 PII Tier 3 (kyc_submission blob ref, email_outbox body,
 *                                     minor_guardian_intake)
 *   - PII itself NEVER lands here (writePrivate → Preferences); only
 *     pii_key references (e.g. "worker-intake:wi-...") + redacted fields
 *     (email_domain, age_band, kyc_token_hash)
 *
 * Related:
 *   ADR-0036 worker-direct Hyperdrive persistence
 *   ADR-0018 PII Tier 3 cohort-first pattern
 *   ADR-0051 game-play-uploader crowdsourced gameplay capture
 *   90-docs/260407-kagami-p10v2-graphar-native-design.md
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Core onboarding (adult + minor guardian) ──

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_worker_intake (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      pii_key VARCHAR,
      kyc_token_hash VARCHAR,
      email_domain VARCHAR,
      prefecture VARCHAR,
      age_band VARCHAR,
      referrer VARCHAR,
      accepted_terms VARCHAR,
      status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_worker_intake_id ON vertex_hc_worker_intake (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_worker_intake_status ON vertex_hc_worker_intake (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_worker_intake_referrer ON vertex_hc_worker_intake (referrer)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_minor_guardian_intake (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      pii_key VARCHAR,
      guardian_email_domain VARCHAR,
      child_age_band VARCHAR,
      prefecture VARCHAR,
      relation VARCHAR,
      referrer VARCHAR,
      accepted_terms VARCHAR,
      status VARCHAR,
      daily_hour_limit BIGINT,
      weekly_hour_limit BIGINT,
      night_block_start_jst VARCHAR,
      night_block_end_jst VARCHAR,
      cero_allowed VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_minor_intake_id ON vertex_hc_minor_guardian_intake (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_minor_intake_status ON vertex_hc_minor_guardian_intake (status)`.execute(db);

  // ── Game capture task lifecycle (ADR-0051) ──

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_task (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      title VARCHAR,
      platform VARCHAR,
      genre VARCHAR,
      game_name VARCHAR,
      duration_minutes BIGINT,
      audience VARCHAR,
      cero_rating VARCHAR,
      bonus_multiplier DOUBLE PRECISION,
      payout_jpy BIGINT,
      payout_currency VARCHAR,
      payout_method VARCHAR,
      requester_did VARCHAR,
      referrer VARCHAR,
      status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gct_id ON vertex_hc_game_capture_task (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gct_status ON vertex_hc_game_capture_task (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gct_audience ON vertex_hc_game_capture_task (audience)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gct_referrer ON vertex_hc_game_capture_task (referrer)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_assignment (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      task_id VARCHAR,
      worker_intake_id VARCHAR,
      status VARCHAR,
      accepted_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gca_id ON vertex_hc_game_capture_assignment (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gca_task_id ON vertex_hc_game_capture_assignment (task_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gca_worker ON vertex_hc_game_capture_assignment (worker_intake_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_submission (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      assignment_id VARCHAR,
      video_blob_key VARCHAR,
      actual_minutes BIGINT,
      pii_occluded_count BIGINT,
      scene_tags VARCHAR,
      status VARCHAR,
      review_auto_approve_at VARCHAR,
      submitted_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gcs_id ON vertex_hc_game_capture_submission (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gcs_assignment ON vertex_hc_game_capture_submission (assignment_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gcs_status ON vertex_hc_game_capture_submission (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_review (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      submission_id VARCHAR,
      decision VARCHAR,
      notes VARCHAR,
      payout_jpy BIGINT,
      payout_queued BOOLEAN,
      gift_code_dispatched BOOLEAN,
      reviewed_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gcr_id ON vertex_hc_game_capture_review (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gcr_submission ON vertex_hc_game_capture_review (submission_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_gcr_decision ON vertex_hc_game_capture_review (decision)`.execute(db);

  // ── KYC ──

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_kyc_submission (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      intake_id VARCHAR,
      doc_type VARCHAR,
      blob_key VARCHAR,
      mime_type VARCHAR,
      byte_size BIGINT,
      r2_uploaded BOOLEAN,
      hash_sha256 VARCHAR,
      status VARCHAR,
      submitted_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_kyc_sub_id ON vertex_hc_kyc_submission (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_kyc_sub_intake ON vertex_hc_kyc_submission (intake_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_kyc_sub_status ON vertex_hc_kyc_submission (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_kyc_review (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      submission_id VARCHAR,
      decision VARCHAR,
      notes VARCHAR,
      reviewed_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_kyc_rev_submission ON vertex_hc_kyc_review (submission_id)`.execute(db);

  // ── Contract acceptance (legally binding, immutable) ──

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_contract_acceptance (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      contract_type VARCHAR,
      contract_did VARCHAR,
      acceptor_did VARCHAR,
      acceptor_intake_id VARCHAR,
      locale VARCHAR,
      accepted_at VARCHAR,
      ip_address VARCHAR,
      user_agent VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_accept_intake ON vertex_hc_contract_acceptance (acceptor_intake_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_accept_type ON vertex_hc_contract_acceptance (contract_type)`.execute(db);

  // ── Email outbox (fallback queue when Resend API key missing) ──
  // NOTE: column `recipient`, not `to` — SQL reserved word.

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_email_outbox (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      recipient VARCHAR,
      subject VARCHAR,
      html VARCHAR,
      tag VARCHAR,
      status VARCHAR,
      provider VARCHAR,
      provider_error VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_outbox_status ON vertex_hc_email_outbox (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_outbox_tag ON vertex_hc_email_outbox (tag)`.execute(db);

  // ── Service Provider (OEM manufacturer) pipeline ──
  // Existing handlers in app.ts write these collections. Tables were missing
  // so graph-worker was skipping with "convention table not found" warnings.

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_sp_application (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      legal_name VARCHAR,
      trade_name VARCHAR,
      country_iso3 VARCHAR,
      category VARCHAR,
      factory_type VARCHAR,
      contact_email VARCHAR,
      website VARCHAR,
      lei VARCHAR,
      isic_codes VARCHAR,
      documents VARCHAR,
      status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_sp_app_id ON vertex_hc_sp_application (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_sp_app_status ON vertex_hc_sp_application (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_sp_app_country ON vertex_hc_sp_application (country_iso3)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_sp_app_category ON vertex_hc_sp_application (category)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_sp_verification (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      application_id VARCHAR,
      result VARCHAR,
      legal_entity_verified BOOLEAN,
      sanctions_clear BOOLEAN,
      notes VARCHAR,
      reviewer_did VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_sp_verify_app ON vertex_hc_sp_verification (application_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_sp_audit (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      application_id VARCHAR,
      audit_task_id VARCHAR,
      result VARCHAR,
      findings VARCHAR,
      certifications_verified VARCHAR,
      capacity_confirmed BIGINT,
      employee_count_confirmed BIGINT,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_sp_audit_app ON vertex_hc_sp_audit (application_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_sp_registration (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      application_id VARCHAR,
      tsukuru_result VARCHAR,
      status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_sp_reg_app ON vertex_hc_sp_registration (application_id)`.execute(db);

  // ── Generic hc task / record (used by SP KYC-task auto-generation,
  //    inspection tasks, and cmdCreateHc legacy handler) ──

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_task (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      title VARCHAR,
      description VARCHAR,
      category VARCHAR,
      difficulty VARCHAR,
      sp_application_id VARCHAR,
      production_order_id VARCHAR,
      factory_did VARCHAR,
      inspection_type VARCHAR,
      quantity BIGINT,
      lot_number VARCHAR,
      status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_task_id ON vertex_hc_task (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_task_status ON vertex_hc_task (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_task_category ON vertex_hc_task (category)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_task_sp_app ON vertex_hc_task (sp_application_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hc_record (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      id VARCHAR,
      type VARCHAR,
      source VARCHAR,
      status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_record_type ON vertex_hc_record (type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hc_record_status ON vertex_hc_record (status)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    "vertex_hc_record",
    "vertex_hc_task",
    "vertex_hc_sp_registration",
    "vertex_hc_sp_audit",
    "vertex_hc_sp_verification",
    "vertex_hc_sp_application",
    "vertex_hc_email_outbox",
    "vertex_hc_contract_acceptance",
    "vertex_hc_kyc_review",
    "vertex_hc_kyc_submission",
    "vertex_hc_game_capture_review",
    "vertex_hc_game_capture_submission",
    "vertex_hc_game_capture_assignment",
    "vertex_hc_game_capture_task",
    "vertex_hc_minor_guardian_intake",
    "vertex_hc_worker_intake",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
