"""Captured from Kysely migration 20260423100000_vertex_hc_platform."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260423100000_vertex_hc_platform"
down_revision = 'r_20260423055225_view_actor_universal'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_worker_intake (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      pii_key VARCHAR,\n'
         '      kyc_token_hash VARCHAR,\n'
         '      email_domain VARCHAR,\n'
         '      prefecture VARCHAR,\n'
         '      age_band VARCHAR,\n'
         '      referrer VARCHAR,\n'
         '      accepted_terms VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_worker_intake_id ON vertex_hc_worker_intake (id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_worker_intake_status ON vertex_hc_worker_intake '
         '(status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_worker_intake_referrer ON vertex_hc_worker_intake '
         '(referrer)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_minor_guardian_intake (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      pii_key VARCHAR,\n'
         '      guardian_email_domain VARCHAR,\n'
         '      child_age_band VARCHAR,\n'
         '      prefecture VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      referrer VARCHAR,\n'
         '      accepted_terms VARCHAR,\n'
         '      status VARCHAR,\n'
         '      daily_hour_limit BIGINT,\n'
         '      weekly_hour_limit BIGINT,\n'
         '      night_block_start_jst VARCHAR,\n'
         '      night_block_end_jst VARCHAR,\n'
         '      cero_allowed VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_minor_intake_id ON vertex_hc_minor_guardian_intake '
         '(id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_minor_intake_status ON vertex_hc_minor_guardian_intake '
         '(status)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_task (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      title VARCHAR,\n'
         '      platform VARCHAR,\n'
         '      genre VARCHAR,\n'
         '      game_name VARCHAR,\n'
         '      duration_minutes BIGINT,\n'
         '      audience VARCHAR,\n'
         '      cero_rating VARCHAR,\n'
         '      bonus_multiplier DOUBLE PRECISION,\n'
         '      payout_jpy BIGINT,\n'
         '      payout_currency VARCHAR,\n'
         '      payout_method VARCHAR,\n'
         '      requester_did VARCHAR,\n'
         '      referrer VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gct_id ON vertex_hc_game_capture_task (id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gct_status ON vertex_hc_game_capture_task (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gct_audience ON vertex_hc_game_capture_task (audience)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gct_referrer ON vertex_hc_game_capture_task (referrer)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_assignment (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      task_id VARCHAR,\n'
         '      worker_intake_id VARCHAR,\n'
         '      status VARCHAR,\n'
         '      accepted_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gca_id ON vertex_hc_game_capture_assignment (id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gca_task_id ON vertex_hc_game_capture_assignment '
         '(task_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gca_worker ON vertex_hc_game_capture_assignment '
         '(worker_intake_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_submission (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      assignment_id VARCHAR,\n'
         '      video_blob_key VARCHAR,\n'
         '      actual_minutes BIGINT,\n'
         '      pii_occluded_count BIGINT,\n'
         '      scene_tags VARCHAR,\n'
         '      status VARCHAR,\n'
         '      review_auto_approve_at VARCHAR,\n'
         '      submitted_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gcs_id ON vertex_hc_game_capture_submission (id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gcs_assignment ON vertex_hc_game_capture_submission '
         '(assignment_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gcs_status ON vertex_hc_game_capture_submission '
         '(status)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_game_capture_review (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      submission_id VARCHAR,\n'
         '      decision VARCHAR,\n'
         '      notes VARCHAR,\n'
         '      payout_jpy BIGINT,\n'
         '      payout_queued BOOLEAN,\n'
         '      gift_code_dispatched BOOLEAN,\n'
         '      reviewed_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gcr_id ON vertex_hc_game_capture_review (id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gcr_submission ON vertex_hc_game_capture_review '
         '(submission_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_gcr_decision ON vertex_hc_game_capture_review '
         '(decision)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_kyc_submission (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      intake_id VARCHAR,\n'
         '      doc_type VARCHAR,\n'
         '      blob_key VARCHAR,\n'
         '      mime_type VARCHAR,\n'
         '      byte_size BIGINT,\n'
         '      r2_uploaded BOOLEAN,\n'
         '      hash_sha256 VARCHAR,\n'
         '      status VARCHAR,\n'
         '      submitted_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_kyc_sub_id ON vertex_hc_kyc_submission (id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_kyc_sub_intake ON vertex_hc_kyc_submission (intake_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_kyc_sub_status ON vertex_hc_kyc_submission (status)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_kyc_review (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      submission_id VARCHAR,\n'
         '      decision VARCHAR,\n'
         '      notes VARCHAR,\n'
         '      reviewed_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_kyc_rev_submission ON vertex_hc_kyc_review '
         '(submission_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_contract_acceptance (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      contract_type VARCHAR,\n'
         '      contract_did VARCHAR,\n'
         '      acceptor_did VARCHAR,\n'
         '      acceptor_intake_id VARCHAR,\n'
         '      locale VARCHAR,\n'
         '      accepted_at VARCHAR,\n'
         '      ip_address VARCHAR,\n'
         '      user_agent VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_accept_intake ON vertex_hc_contract_acceptance '
         '(acceptor_intake_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_accept_type ON vertex_hc_contract_acceptance '
         '(contract_type)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_email_outbox (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      recipient VARCHAR,\n'
         '      subject VARCHAR,\n'
         '      html VARCHAR,\n'
         '      tag VARCHAR,\n'
         '      status VARCHAR,\n'
         '      provider VARCHAR,\n'
         '      provider_error VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_outbox_status ON vertex_hc_email_outbox (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_outbox_tag ON vertex_hc_email_outbox (tag)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_sp_application (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      legal_name VARCHAR,\n'
         '      trade_name VARCHAR,\n'
         '      country_iso3 VARCHAR,\n'
         '      category VARCHAR,\n'
         '      factory_type VARCHAR,\n'
         '      contact_email VARCHAR,\n'
         '      website VARCHAR,\n'
         '      lei VARCHAR,\n'
         '      isic_codes VARCHAR,\n'
         '      documents VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_sp_app_id ON vertex_hc_sp_application (id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_sp_app_status ON vertex_hc_sp_application (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_sp_app_country ON vertex_hc_sp_application '
         '(country_iso3)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_sp_app_category ON vertex_hc_sp_application (category)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_sp_verification (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      application_id VARCHAR,\n'
         '      result VARCHAR,\n'
         '      legal_entity_verified BOOLEAN,\n'
         '      sanctions_clear BOOLEAN,\n'
         '      notes VARCHAR,\n'
         '      reviewer_did VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_sp_verify_app ON vertex_hc_sp_verification '
         '(application_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_sp_audit (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      application_id VARCHAR,\n'
         '      audit_task_id VARCHAR,\n'
         '      result VARCHAR,\n'
         '      findings VARCHAR,\n'
         '      certifications_verified VARCHAR,\n'
         '      capacity_confirmed BIGINT,\n'
         '      employee_count_confirmed BIGINT,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_sp_audit_app ON vertex_hc_sp_audit (application_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_sp_registration (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      application_id VARCHAR,\n'
         '      tsukuru_result VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_sp_reg_app ON vertex_hc_sp_registration '
         '(application_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_task (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      title VARCHAR,\n'
         '      description VARCHAR,\n'
         '      category VARCHAR,\n'
         '      difficulty VARCHAR,\n'
         '      sp_application_id VARCHAR,\n'
         '      production_order_id VARCHAR,\n'
         '      factory_did VARCHAR,\n'
         '      inspection_type VARCHAR,\n'
         '      quantity BIGINT,\n'
         '      lot_number VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_task_id ON vertex_hc_task (id)', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_task_status ON vertex_hc_task (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_task_category ON vertex_hc_task (category)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_task_sp_app ON vertex_hc_task (sp_application_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hc_record (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      id VARCHAR,\n'
         '      type VARCHAR,\n'
         '      source VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_record_type ON vertex_hc_record (type)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hc_record_status ON vertex_hc_record (status)',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_hc_record', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_task', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_sp_registration', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_sp_audit', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_sp_verification', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_sp_application', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_email_outbox', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_contract_acceptance', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_kyc_review', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_kyc_submission', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_game_capture_review', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_game_capture_submission', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_game_capture_assignment', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_game_capture_task', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_minor_guardian_intake', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hc_worker_intake', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
