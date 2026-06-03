// ADR-0095 §D2 — Incremental actor_did / org_did backfill for Tier 1 app-writable tables.
//
// Scope: vertex_* tables that have legacy org_id / user_id / actor_id columns but lack
//   the canonical actor_did / org_did columns introduced by ADR-0095.
//
// Tier 1 = app-writable, per-tenant domain tables (451 tables).
// Tier 2 = excluded (public bulk ingest, shared reference data, no per-tenant isolation needed):
//   vertex_open_*  (~570 tables, public bulk data)
//   vertex_bio_*   (taxonomy)
//   vertex_phys_*  (physics reference data)
//   vertex_seibutsu_* (biological taxonomy)
//   vertex_itr*_return* (tax bulk)
//   vertex_gstr*   (GST bulk)
//   vertex_epfo_*  (EPFO bulk)
//   vertex_esic_*  (ESIC bulk)
//   vertex_ind_*   (India eFiling bulk)
//
// CREATE INDEX intentionally excluded from this migration.
// Reason: CREATE INDEX on large tables caused a cluster reset in a prior incident
// (2026-04-xx). Indexes will be added in a separate follow-up migration
// (20260428250000_actor_did_indexes.ts) after cluster stability is confirmed.
//
// Migration semantics:
//   - ADD COLUMN IF NOT EXISTS: idempotent, safe to re-run
//   - org_did DEFAULT 'anon': sentinel value until org resolution is implemented
//   - Old org_id / user_id / actor_id columns remain in place (grandfathered, ADR-0095 §D2)
//   - Backfill of existing rows tracked in deps.toml [[migrations]] identity-canonical-columns-backfill
//
// down() is a no-op: RisingWave does not support DROP COLUMN.

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_actor_capability ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_actor_capability ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_actor_embedding ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_actor_embedding ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_adr_arbitrator ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_adr_arbitrator ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_adr_case ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_adr_case ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_ads_advertiser ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_ads_advertiser ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_ads_creative ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_ads_creative ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_ads_scraper_run ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_ads_scraper_run ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_ads_snapshot ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_ads_snapshot ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_agent_publication ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_agent_publication ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_agent_runtime_artifact ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_agent_runtime_artifact ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_agent_runtime_checkpoint ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_agent_runtime_checkpoint ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_agent_runtime_receipt ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_agent_runtime_receipt ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_airline ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_airline ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_apqc_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apqc_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arb_proposal ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arb_proposal ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arb_publication ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arb_publication ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arb_quote ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arb_quote ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arb_score ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arb_score ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arms_auth_session ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arms_auth_session ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arms_custody_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arms_custody_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arms_firearm ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arms_firearm ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arms_firearm_pii ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arms_firearm_pii ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arms_permit ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arms_permit ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_arms_permit_pii ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_arms_permit_pii ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_auth_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_auth_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bluesky_follow ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bluesky_follow ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bluesky_opt_out ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bluesky_opt_out ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bluesky_post ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bluesky_post ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bluesky_profile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bluesky_profile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bluesky_tombstone ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bluesky_tombstone ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bpmn_activity_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_activity_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bpmn_lexicon_binding ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_lexicon_binding ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bpmn_process_def ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process_def ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_bpmn_signal_log ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_signal_log ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_calendar_invitation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_calendar_invitation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_calendar_reminder ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_calendar_reminder ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_calendar_rsvp ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_calendar_rsvp ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_claim_challenge ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_challenge ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_claim_resolution ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_resolution ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_claim_stake ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_claim_stake ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_cloudflare_browser_render_artifact ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cloudflare_browser_render_artifact ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_cloudflare_browser_render_session ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cloudflare_browser_render_session ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_archive_snapshot ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_archive_snapshot ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_blockchain_actor ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_blockchain_actor ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_dns_change ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_dns_change ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_dns_observation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_dns_observation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_dns_snapshot ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_dns_snapshot ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_organization ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_organization ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_risk_signal ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_risk_signal ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_collector_scan_result ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_collector_scan_result ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_contracts_organization ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contracts_organization ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_contracts_social_contract ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contracts_social_contract ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_cowork_graph_mail_draft ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cowork_graph_mail_draft ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_cowork_graph_tool_grant ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cowork_graph_tool_grant ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_crypto_asset_freeze_forensic_trace ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_crypto_asset_freeze_forensic_trace ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_crypto_asset_freeze_incident ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_crypto_asset_freeze_incident ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_crypto_asset_freeze_request ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_crypto_asset_freeze_request ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_datacenter_access_request ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_datacenter_access_request ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_datacenter_access_request_pii ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_datacenter_access_request_pii ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_datacenter_capacity_reservation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_datacenter_capacity_reservation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_datacenter_operation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_datacenter_operation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_docs_entity ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_docs_entity ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_docs_report ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_docs_report ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_drive_file ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_drive_file ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_drive_folder ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_drive_folder ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_drive_share ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_drive_share ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_editor_file ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_editor_file ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_editor_project ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_editor_project ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_erc725_root_identity ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_erc725_root_identity ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_esim_profile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_esim_profile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_esimprofile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_esimprofile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_flight_offer_alert ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_flight_offer_alert ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_flight_offer_source ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_flight_offer_source ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_flight_offer_source_run ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_flight_offer_source_run ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_flight_offer_watch ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_flight_offer_watch ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_fukkou_recipient_org ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_fukkou_recipient_org ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_fuyou_declaration ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_fuyou_declaration ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_fuyou_declaration_pii ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_fuyou_declaration_pii ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcal_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcal_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcal_attendee ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcal_attendee ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcal_calendar ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcal_calendar ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcal_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcal_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcal_watch_channel ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcal_watch_channel ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcontacts_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcontacts_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcontacts_contact ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcontacts_contact ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gcontacts_group ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gcontacts_group ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdocs_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdocs_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdocs_document ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdocs_document ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdocs_revision ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdocs_revision ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdrive_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdrive_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdrive_file ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdrive_file ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdrive_permission ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdrive_permission ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdrive_revision ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdrive_revision ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gdrive_watch_channel ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gdrive_watch_channel ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gitrepo ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gitrepo ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_account_binding ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_account_binding ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_contact ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_contact ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_email ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_outbound_email ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_outbound_email ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_sync_job ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_sync_job ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmail_thread ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_thread ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmeet_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmeet_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmeet_conference ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmeet_conference ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmeet_participant ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmeet_participant ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gmeet_recording ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmeet_recording ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gov_form_extraction_result ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gov_form_extraction_result ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gov_form_extraction_task ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gov_form_extraction_task ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gov_form_language_variant ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gov_form_language_variant ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gov_local_variation_gap ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gov_local_variation_gap ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gsheets_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gsheets_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gsheets_sheet ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gsheets_sheet ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gsheets_spreadsheet ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gsheets_spreadsheet ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gslides_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gslides_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gslides_presentation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gslides_presentation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gslides_slide ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gslides_slide ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gtasks_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gtasks_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gtasks_list ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gtasks_list ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_gtasks_task ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gtasks_task ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_contract_acceptance ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_contract_acceptance ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_email_outbox ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_email_outbox ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_game_capture_assignment ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_game_capture_assignment ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_game_capture_review ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_game_capture_review ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_game_capture_submission ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_game_capture_submission ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_game_capture_task ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_game_capture_task ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_kyc_review ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_kyc_review ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_kyc_submission ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_kyc_submission ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_minor_guardian_intake ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_minor_guardian_intake ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_record ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_record ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_sp_application ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_sp_application ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_sp_audit ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_sp_audit ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_sp_registration ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_sp_registration ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_sp_verification ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_sp_verification ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_task ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_task ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_hc_worker_intake ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hc_worker_intake ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_historical_conflict ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_historical_conflict ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_houbun_amendmentevent ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_houbun_amendmentevent ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_houbun_article ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_houbun_article ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_houbun_statute ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_houbun_statute ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_houbun_treaty ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_houbun_treaty ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_intel_entity_did ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_intel_entity_did ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_intel_evidence ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_intel_evidence ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_intel_inference_chain ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_intel_inference_chain ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_intel_inference_run ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_intel_inference_run ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_intel_inferred_cohort ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_intel_inferred_cohort ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_intel_report ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_intel_report ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_intel_subject ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_intel_subject ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_ipaddress_access_log ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_ipaddress_access_log ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_isekai_world_map ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_isekai_world_map ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_isekai_world_portal ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_isekai_world_portal ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_isekai_world_scene ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_isekai_world_scene ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_edinet_material_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_edinet_material_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_edinet_securities_filing ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_edinet_securities_filing ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_invoice_corporate_tax ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_invoice_corporate_tax ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_invoice_issuer ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_invoice_issuer ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_jma_earthquake ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_jma_earthquake ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_jma_weather_warning ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_jma_weather_warning ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_jpo_application ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_jpo_application ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_jpo_examination ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_jpo_examination ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_mlit_road_construction ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_mlit_road_construction ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_jpn_mlit_road_restriction ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jpn_mlit_road_restriction ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_kind_mcp_binding ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kind_mcp_binding ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_langgraph_checkpoint ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_langgraph_checkpoint ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_langgraph_state ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_langgraph_state ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_legal_aid_case ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_aid_case ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_legal_aid_office ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_aid_office ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_legal_corpus_document ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_corpus_document ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_legal_corpus_document_pii ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_corpus_document_pii ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_legal_corpus_source ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_corpus_source ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_livecam_anomaly ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_livecam_anomaly ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_livecam_camera ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_livecam_camera ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_livecam_detection_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_livecam_detection_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_livecam_person_cohort ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_livecam_person_cohort ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_livecam_summary ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_livecam_summary ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_livecam_vehicle_cohort ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_livecam_vehicle_cohort ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_livecam_zone ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_livecam_zone ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_m365_sync_state ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_m365_sync_state ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_m365_user ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_m365_user ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_mailer_inbound_email ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_mailer_inbound_email ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_maps_coverage_target ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_maps_coverage_target ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_maps3d_tile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_maps3d_tile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_natural_person_census_source ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_natural_person_census_source ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_natural_person_cohort_person ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_natural_person_cohort_person ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_natural_person_identified_person ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_natural_person_identified_person ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_natural_person_person_enrichment ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_natural_person_person_enrichment ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_advisory_note ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_advisory_note ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_crop_plan ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_crop_plan ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_direct_sales_item ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_direct_sales_item ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_farm ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_farm ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_kyosai_policy ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_kyosai_policy ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_loan_application ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_loan_application ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_member ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_member ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_purchase_order ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_purchase_order ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_nokyo_sale_lot ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_nokyo_sale_lot ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_creator ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_creator ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_entitlement ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_entitlement ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_payout_ledger ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_payout_ledger ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_post ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_post ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_report ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_report ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_subscription ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_subscription ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_tier ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_tier ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_oshinobi_tip ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_oshinobi_tip ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_association ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_association ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_chain ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_chain ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_distributor ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_distributor ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_maker ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_maker ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_prize ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_prize ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_regulator ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_regulator ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_supplier ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_supplier ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pachinko_vendor ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pachinko_vendor ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_playwright_action ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_playwright_action ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_playwright_artifact ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_playwright_artifact ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_playwright_session ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_playwright_session ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pptx_image ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pptx_image ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pptx_presentation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pptx_presentation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pptx_shape ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pptx_shape ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pptx_slide ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pptx_slide ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pptx_slide_template ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pptx_slide_template ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_pptx_text_run ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_pptx_text_run ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_projector_flow ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_projector_flow ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_projector_flow_node ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_projector_flow_node ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_projector_flow_run ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_projector_flow_run ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_projector_flow_step ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_projector_flow_step ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_projector_reflection ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_projector_reflection ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_projector_task ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_projector_task ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_real_estate_listing ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_real_estate_listing ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_real_estate_party ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_real_estate_party ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_real_estate_property ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_real_estate_property ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_real_estate_source ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_real_estate_source ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_real_estate_transaction ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_real_estate_transaction ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_repository_blob ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_repository_blob ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_repository_commit ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_repository_commit ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_repository_ref ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_repository_ref ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_repository_tree ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_repository_tree ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_resource_flow_anomaly ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_resource_flow_anomaly ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_resource_flow_anomaly_review ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_resource_flow_anomaly_review ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_resource_flow_currency ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_resource_flow_currency ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_resource_flow_personnel ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_resource_flow_personnel ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_resource_flow_service ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_resource_flow_service ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_sanctions_entry ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_sanctions_entry ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_sanctions_list_update ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_sanctions_list_update ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_sanctions_match ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_sanctions_match ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_satellite_analysis ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_satellite_analysis ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_satellite_scene ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_satellite_scene ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_scraper_dsl ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_scraper_dsl ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_scraper_run ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_scraper_run ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_scraper_source ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_scraper_source ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shigotoba_company_profile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shigotoba_company_profile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shigotoba_job_posting ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shigotoba_job_posting ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shiharai_bill ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shiharai_bill ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shiharai_biller ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shiharai_biller ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shiharai_job ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shiharai_job ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shiharai_job_result ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shiharai_job_result ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shiharai_payment ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shiharai_payment ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_shiharai_recurring ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_shiharai_recurring ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_smishing_phishing_report ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_smishing_phishing_report ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_smishing_sender_blocklist ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_smishing_sender_blocklist ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_smishing_sms_message ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_smishing_sms_message ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_smishing_takedown_request ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_smishing_takedown_request ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_smishing_threat_detection ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_smishing_threat_detection ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_smishing_url_intel ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_smishing_url_intel ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_stripe_authorization ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_stripe_authorization ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_stripe_card_credit_allocation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_stripe_card_credit_allocation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_stripe_card_credit_consumption ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_stripe_card_credit_consumption ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_stripe_cardholder ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_stripe_cardholder ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_stripe_issued_card ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_stripe_issued_card ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_stripe_spending_limit ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_stripe_spending_limit ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_alarm ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_alarm ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_alarm_correlation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_alarm_correlation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_amf_registration ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_amf_registration ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_auth_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_auth_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_capacity_forecast ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_capacity_forecast ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_cdr ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_cdr ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_cell_site ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_cell_site ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_change_approval ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_change_approval ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_change_request ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_change_request ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_charging_record ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_charging_record ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_config_snapshot ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_config_snapshot ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_emergency_call ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_emergency_call ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_esim_audit ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_esim_audit ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_esim_euicc ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_esim_euicc ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_esim_ownership_transfer ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_esim_ownership_transfer ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_esim_profile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_esim_profile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_esim_profile_op ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_esim_profile_op ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_esim_smds_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_esim_smds_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ims_billing_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ims_billing_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ims_subscription ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ims_subscription ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_interconnect_agreement ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_interconnect_agreement ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_interconnect_cdr ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_interconnect_cdr ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_invoice ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_invoice ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_kpi_sample ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_kpi_sample ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_li_access_audit ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_li_access_audit ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_li_cc_delivery ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_li_cc_delivery ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_li_delivery_ack ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_li_delivery_ack ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_li_iri_delivery ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_li_iri_delivery ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_li_target ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_li_target ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_li_warrant ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_li_warrant ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_maintenance_window ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_maintenance_window ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mec_app_package ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mec_app_package ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mec_eas ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mec_eas ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mec_eas_discovery ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mec_eas_discovery ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mec_eas_relocation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mec_eas_relocation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mec_federation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mec_federation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mec_host ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mec_host ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mec_service_call ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mec_service_call ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_mnp_request ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_mnp_request ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_network_asset ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_network_asset ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nf_instance ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nf_instance ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nfv_heal_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nfv_heal_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nfv_ns ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nfv_ns ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nfv_nsd ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nfv_nsd ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nfv_scale_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nfv_scale_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nfv_sdn_flow ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nfv_sdn_flow ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nfv_vnf ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nfv_vnf ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nfv_vnfd ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nfv_vnfd ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_cag ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_cag ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_id_mapping ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_id_mapping ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_nid_allocation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_nid_allocation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_nsacf_decision ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_nsacf_decision ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_pni_slice ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_pni_slice ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_prose_policy ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_prose_policy ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_snpn_deployment ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_snpn_deployment ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_npn_subscriber_enrollment ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_npn_subscriber_enrollment ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_cell ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_cell ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_contact ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_contact ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_earth_station ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_earth_station ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_ephemeris ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_ephemeris ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_handover ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_handover ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_isl ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_isl ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_partner ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_partner ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ntn_satellite ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ntn_satellite ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_number_range ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_number_range ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nwdaf_result ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nwdaf_result ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_nwdaf_subscription ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_nwdaf_subscription ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_alarm ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_alarm ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_domain ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_domain ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_dwdm_channel ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_dwdm_channel ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_fiber_span ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_fiber_span ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_ols ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_ols ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_otn_connection ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_otn_connection ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_pm_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_pm_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_optical_roadm ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_optical_roadm ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_a1_policy ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_a1_policy ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_e2_indication ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_e2_indication ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_e2_subscription ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_e2_subscription ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_o1_config ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_o1_config ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_o2_resource ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_o2_resource ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_rapp ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_rapp ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_smo ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_smo ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_oran_xapp ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_oran_xapp ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_pdu_session ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_pdu_session ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_policy_decision ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_policy_decision ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_ran_node ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_ran_node ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_rma_case ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_rma_case ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_roaming_invoice ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_roaming_invoice ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_roaming_partner ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_roaming_partner ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_scp_discovery ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_scp_discovery ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_scp_route ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_scp_route ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_sepp_context ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_sepp_context ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_sepp_key_rotation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_sepp_key_rotation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_sepp_message ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_sepp_message ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_sepp_trust_negotiation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_sepp_trust_negotiation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_service ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_service ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_sim ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_sim ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_sip_registration ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_sip_registration ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_site_incident ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_site_incident ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_sla_breach ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_sla_breach ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_slice_selection ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_slice_selection ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_spectrum_license ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_spectrum_license ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_subscriber ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_subscriber ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_subscriber_pii ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_subscriber_pii ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_subscriber_profile_5g ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_subscriber_profile_5g ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_supp_service_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_supp_service_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tap_file ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tap_file ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_customer_account ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_customer_account ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_customer_bill ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_customer_bill ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_product_inventory ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_product_inventory ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_product_offering ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_product_offering ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_product_order ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_product_order ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_service_activation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_service_activation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_service_inventory ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_service_inventory ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tmf_service_order ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tmf_service_order ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_bridge ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_bridge ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_domain ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_domain ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_frer_profile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_frer_profile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_shaper ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_shaper ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_sla_breach ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_sla_breach ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_stream ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_stream ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_sync_deviation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_sync_deviation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_tsn_sync_profile ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_tsn_sync_profile ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_voice_call ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_voice_call ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_voice_interconnect_bridge ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_voice_interconnect_bridge ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_andsp_bridge ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_andsp_bridge ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_anqp_query ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_anqp_query ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_pps_mo ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_pps_mo ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_rcoi ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_rcoi ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_roaming_exchange ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_roaming_exchange ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_roaming_invoice ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_roaming_invoice ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_session ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_session ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_telecom_wlan_venue ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_telecom_wlan_venue ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_tenso_access_control ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tenso_access_control ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_tenso_file_manifest ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tenso_file_manifest ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_tenso_transfer_request ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tenso_transfer_request ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_translation_link ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_translation_link ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vector_embedding_chunk ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vector_embedding_chunk ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vector_embedding_model ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vector_embedding_model ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vector_embedding_projection ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vector_embedding_projection ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vector_embedding_source ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vector_embedding_source ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vector_embedding_space ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vector_embedding_space ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vector_emotion_signal ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vector_emotion_signal ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_cohort_registration ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_cohort_registration ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_jurisdiction_registry ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_jurisdiction_registry ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_license_plate ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_license_plate ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_manufacturer ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_manufacturer ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_production_line ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_production_line ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_production_plant ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_production_plant ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_shipment_volume ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_shipment_volume ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_vehicle ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_vehicle ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_vehicle_type ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_vehicle_type ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_vin_wmi_code ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vin_wmi_code ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_cell ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_cell ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_chart ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_chart ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_defined_name ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_defined_name ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_pivot ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_pivot ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_sheet ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_sheet ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_style ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_style ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_table ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_table ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_workbook ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_workbook ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_xlsx_workbook_template ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_xlsx_workbook_template ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_alert ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_alert ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_enforcement ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_enforcement ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_entity ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_entity ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_evidence ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_evidence ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_flag ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_flag ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_infra_track ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_infra_track ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_intel_access_log ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_intel_access_log ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_registration_ban ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_registration_ban ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yabai_risk ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_risk ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yadoya_flow_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yadoya_flow_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yadoya_hotel ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yadoya_hotel ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yadoya_reservation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yadoya_reservation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yoro_monitor_attestation ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yoro_monitor_attestation ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yoro_monitor_vote ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yoro_monitor_vote ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yotei_availability ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yotei_availability ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yotei_booking ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yotei_booking ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yotei_calendar ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yotei_calendar ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);

  await sql`ALTER TABLE vertex_yotei_event ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yotei_event ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support DROP COLUMN — down() is intentionally a no-op.
  // To revert, drop and recreate the table (data-destructive; prefer forward migration).
}
