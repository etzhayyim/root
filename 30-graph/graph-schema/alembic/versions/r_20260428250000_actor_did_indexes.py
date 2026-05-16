"""Captured from Kysely migration 20260428250000_actor_did_indexes."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428250000_actor_did_indexes"
down_revision = 'r_20260428240000_edge_business_person_relation'
branch_labels = None
depends_on = None

UP = [{'sql': 'SET BACKGROUND_DDL = true', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_agent_runtime_artifact_actor_did ON '
         '"vertex_agent_runtime_artifact" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_agent_runtime_checkpoint_actor_did ON '
         '"vertex_agent_runtime_checkpoint" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_agent_runtime_receipt_actor_did ON '
         '"vertex_agent_runtime_receipt" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bpmn_activity_event_actor_did ON '
         '"vertex_bpmn_activity_event" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bpmn_instance_actor_did ON "vertex_bpmn_instance" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bpmn_lexicon_binding_actor_did ON '
         '"vertex_bpmn_lexicon_binding" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bpmn_process_actor_did ON "vertex_bpmn_process" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bpmn_process_def_actor_did ON '
         '"vertex_bpmn_process_def" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bpmn_signal_log_actor_did ON '
         '"vertex_bpmn_signal_log" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_account_actor_did ON "vertex_gmail_account" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_contact_actor_did ON "vertex_gmail_contact" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_email_actor_did ON "vertex_gmail_email" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_outbound_email_actor_did ON '
         '"vertex_gmail_outbound_email" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_phishing_alert_actor_did ON '
         '"vertex_gmail_phishing_alert" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_sync_job_actor_did ON '
         '"vertex_gmail_sync_job" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_thread_actor_did ON "vertex_gmail_thread" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmeet_account_actor_did ON "vertex_gmeet_account" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmeet_conference_actor_did ON '
         '"vertex_gmeet_conference" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmeet_participant_actor_did ON '
         '"vertex_gmeet_participant" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmeet_recording_actor_did ON '
         '"vertex_gmeet_recording" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_satellite_analysis_actor_did ON '
         '"vertex_satellite_analysis" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_satellite_scene_actor_did ON '
         '"vertex_satellite_scene" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_maps_coverage_target_actor_did ON '
         '"vertex_maps_coverage_target" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_alert_actor_did ON "vertex_yabai_alert" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_enforcement_actor_did ON '
         '"vertex_yabai_enforcement" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_entity_actor_did ON "vertex_yabai_entity" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_evidence_actor_did ON '
         '"vertex_yabai_evidence" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_flag_actor_did ON "vertex_yabai_flag" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_infra_track_actor_did ON '
         '"vertex_yabai_infra_track" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_intel_access_log_actor_did ON '
         '"vertex_yabai_intel_access_log" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_registration_ban_actor_did ON '
         '"vertex_yabai_registration_ban" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_yabai_risk_actor_did ON "vertex_yabai_risk" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_legal_aid_case_actor_did ON '
         '"vertex_legal_aid_case" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_legal_aid_office_actor_did ON '
         '"vertex_legal_aid_office" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_legal_corpus_document_actor_did ON '
         '"vertex_legal_corpus_document" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_langgraph_checkpoint_actor_did ON '
         '"vertex_langgraph_checkpoint" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_langgraph_state_actor_did ON '
         '"vertex_langgraph_state" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_livecam_anomaly_actor_did ON '
         '"vertex_livecam_anomaly" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_livecam_detection_event_actor_did ON '
         '"vertex_livecam_detection_event" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_livecam_summary_actor_did ON '
         '"vertex_livecam_summary" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_nokyo_farm_actor_did ON "vertex_nokyo_farm" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_nokyo_member_actor_did ON "vertex_nokyo_member" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_nokyo_purchase_order_actor_did ON '
         '"vertex_nokyo_purchase_order" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_nokyo_sale_lot_actor_did ON '
         '"vertex_nokyo_sale_lot" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_oshinobi_creator_actor_did ON '
         '"vertex_oshinobi_creator" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_oshinobi_entitlement_actor_did ON '
         '"vertex_oshinobi_entitlement" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_oshinobi_payout_ledger_actor_did ON '
         '"vertex_oshinobi_payout_ledger" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_oshinobi_post_actor_did ON "vertex_oshinobi_post" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_oshinobi_subscription_actor_did ON '
         '"vertex_oshinobi_subscription" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_natural_person_cohort_person_actor_did ON '
         '"vertex_natural_person_cohort_person" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_natural_person_identified_person_actor_did ON '
         '"vertex_natural_person_identified_person" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_natural_person_person_enrichment_actor_did ON '
         '"vertex_natural_person_person_enrichment" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_arb_proposal_actor_did ON "vertex_arb_proposal" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_arb_publication_actor_did ON '
         '"vertex_arb_publication" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_arb_quote_actor_did ON "vertex_arb_quote" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_arb_score_actor_did ON "vertex_arb_score" '
         '(actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_m365_sync_state_actor_did ON '
         '"vertex_m365_sync_state" (actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_m365_user_actor_did ON "vertex_m365_user" '
         '(actor_did)',
  'parameters': []}]

DOWN = [{'sql': 'DROP INDEX IF EXISTS idx_vertex_m365_user_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_m365_sync_state_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_arb_score_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_arb_quote_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_arb_publication_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_arb_proposal_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_natural_person_person_enrichment_actor_did',
  'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_natural_person_identified_person_actor_did',
  'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_natural_person_cohort_person_actor_did',
  'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_oshinobi_subscription_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_oshinobi_post_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_oshinobi_payout_ledger_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_oshinobi_entitlement_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_oshinobi_creator_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_nokyo_sale_lot_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_nokyo_purchase_order_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_nokyo_member_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_nokyo_farm_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_livecam_summary_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_livecam_detection_event_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_livecam_anomaly_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_langgraph_state_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_langgraph_checkpoint_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_legal_corpus_document_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_legal_aid_office_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_legal_aid_case_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_risk_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_registration_ban_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_intel_access_log_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_infra_track_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_flag_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_evidence_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_entity_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_enforcement_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_yabai_alert_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_maps_coverage_target_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_satellite_scene_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_satellite_analysis_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmeet_recording_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmeet_participant_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmeet_conference_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmeet_account_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmail_thread_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmail_sync_job_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmail_phishing_alert_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmail_outbound_email_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmail_email_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmail_contact_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_gmail_account_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bpmn_signal_log_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bpmn_process_def_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bpmn_process_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bpmn_lexicon_binding_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bpmn_instance_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bpmn_activity_event_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_agent_runtime_receipt_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_agent_runtime_checkpoint_actor_did', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_agent_runtime_artifact_actor_did', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
