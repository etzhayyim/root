import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * Typed vertex tables for crypto-asset-freeze, sanctions, and seibutsu apps.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // --- cryptoAssetFreeze ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_crypto_asset_freeze_incident (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      incident_id VARCHAR,
      source_case_id VARCHAR,
      source_app VARCHAR,
      wallet_addresses VARCHAR,
      priority VARCHAR,
      case_id VARCHAR,
      chain VARCHAR,
      asset_symbol VARCHAR,
      amount DOUBLE PRECISION,
      wallet_address VARCHAR,
      tx_hash VARCHAR,
      authority VARCHAR,
      jurisdiction VARCHAR,
      reason VARCHAR,
      severity VARCHAR,
      freeze_status VARCHAR,
      reported_at VARCHAR,
      frozen_at VARCHAR,
      released_at VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      source_record_id VARCHAR,
      notes VARCHAR,
      evidence_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_incident_incident_id ON vertex_crypto_asset_freeze_incident (incident_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_incident_case_id ON vertex_crypto_asset_freeze_incident (case_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_incident_chain ON vertex_crypto_asset_freeze_incident (chain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_incident_wallet_address ON vertex_crypto_asset_freeze_incident (wallet_address)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_incident_status ON vertex_crypto_asset_freeze_incident (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_crypto_asset_freeze_request (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      request_id VARCHAR,
      incident_id VARCHAR,
      wallet_address VARCHAR,
      exchange VARCHAR,
      chain VARCHAR,
      target_address VARCHAR,
      target_entity VARCHAR,
      exchange_name VARCHAR,
      authority VARCHAR,
      requested_by_did VARCHAR,
      legal_basis VARCHAR,
      request_type VARCHAR,
      requested_at VARCHAR,
      due_at VARCHAR,
      resolved_at VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      notes VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_request_request_id ON vertex_crypto_asset_freeze_request (request_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_request_incident_id ON vertex_crypto_asset_freeze_request (incident_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_request_target_address ON vertex_crypto_asset_freeze_request (target_address)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_request_status ON vertex_crypto_asset_freeze_request (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_crypto_asset_freeze_forensic_trace (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      trace_id VARCHAR,
      incident_id VARCHAR,
      chain VARCHAR,
      tx_hash VARCHAR,
      from_address VARCHAR,
      to_address VARCHAR,
      asset_symbol VARCHAR,
      amount DOUBLE PRECISION,
      hop_index BIGINT,
      risk_score DOUBLE PRECISION,
      attribution_did VARCHAR,
      observed_at VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      notes VARCHAR,
      metadata_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_trace_trace_id ON vertex_crypto_asset_freeze_forensic_trace (trace_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_trace_incident_id ON vertex_crypto_asset_freeze_forensic_trace (incident_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_trace_tx_hash ON vertex_crypto_asset_freeze_forensic_trace (tx_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_trace_from_address ON vertex_crypto_asset_freeze_forensic_trace (from_address)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_crypto_trace_to_address ON vertex_crypto_asset_freeze_forensic_trace (to_address)`.execute(db);

  // --- sanctions ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_sanctions_entry (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      entry_id VARCHAR,
      list_source VARCHAR,
      entity_name VARCHAR,
      entity_type VARCHAR,
      aliases_json VARCHAR,
      identifiers_json VARCHAR,
      updated_at VARCHAR,
      list_name VARCHAR,
      list_version VARCHAR,
      authority VARCHAR,
      program VARCHAR,
      subject_name VARCHAR,
      subject_type VARCHAR,
      target_did VARCHAR,
      target_address VARCHAR,
      country VARCHAR,
      risk_level VARCHAR,
      effective_at VARCHAR,
      expires_at VARCHAR,
      source_url VARCHAR,
      source_record_id VARCHAR,
      metadata_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_entry_entry_id ON vertex_sanctions_entry (entry_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_entry_list_name ON vertex_sanctions_entry (list_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_entry_subject_name ON vertex_sanctions_entry (subject_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_entry_target_did ON vertex_sanctions_entry (target_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_entry_target_address ON vertex_sanctions_entry (target_address)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_sanctions_match (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      match_id VARCHAR,
      query_entity VARCHAR,
      matched_entry_id VARCHAR,
      list_source VARCHAR,
      screened_at VARCHAR,
      entry_id VARCHAR,
      subject_did VARCHAR,
      subject_name VARCHAR,
      matched_name VARCHAR,
      match_type VARCHAR,
      score DOUBLE PRECISION,
      decision VARCHAR,
      reviewer_did VARCHAR,
      reason VARCHAR,
      matched_at VARCHAR,
      reviewed_at VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_match_match_id ON vertex_sanctions_match (match_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_match_entry_id ON vertex_sanctions_match (entry_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_match_subject_did ON vertex_sanctions_match (subject_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_match_decision ON vertex_sanctions_match (decision)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_match_score ON vertex_sanctions_match (score)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_sanctions_list_update (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      update_id VARCHAR,
      list_source VARCHAR,
      version VARCHAR,
      entry_count BIGINT,
      downloaded_at VARCHAR,
      list_name VARCHAR,
      list_version VARCHAR,
      checksum VARCHAR,
      source_url VARCHAR,
      source_record_id VARCHAR,
      fetched_at VARCHAR,
      effective_at VARCHAR,
      change_count BIGINT,
      added_count BIGINT,
      removed_count BIGINT,
      notes VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_update_update_id ON vertex_sanctions_list_update (update_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_update_list_name ON vertex_sanctions_list_update (list_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_update_list_version ON vertex_sanctions_list_update (list_version)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sanctions_update_effective_at ON vertex_sanctions_list_update (effective_at)`.execute(db);

  // --- seibutsu ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_seibutsu_taxon (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      taxon_id VARCHAR,
      taxon_did VARCHAR,
      scientific_name VARCHAR,
      canonical_name VARCHAR,
      common_name VARCHAR,
      rank VARCHAR,
      parent_taxon_id VARCHAR,
      parent_did VARCHAR,
      authority VARCHAR,
      gbif_id VARCHAR,
      ncbi_taxon_id VARCHAR,
      wikidata_qid VARCHAR,
      kingdom VARCHAR,
      phylum VARCHAR,
      class_name VARCHAR,
      order_name VARCHAR,
      family VARCHAR,
      genus VARCHAR,
      species VARCHAR,
      common_names_json VARCHAR,
      source VARCHAR,
      source_id VARCHAR,
      source_url VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_taxon_taxon_id ON vertex_seibutsu_taxon (taxon_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_taxon_taxon_did ON vertex_seibutsu_taxon (taxon_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_taxon_scientific_name ON vertex_seibutsu_taxon (scientific_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_taxon_rank ON vertex_seibutsu_taxon (rank)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_taxon_parent_taxon_id ON vertex_seibutsu_taxon (parent_taxon_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_seibutsu_traits (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      trait_id VARCHAR,
      taxon_id VARCHAR,
      taxon_did VARCHAR,
      trait_name VARCHAR,
      trait_value VARCHAR,
      division VARCHAR,
      habit VARCHAR,
      arrangement VARCHAR,
      leaf_shape VARCHAR,
      canopy VARCHAR,
      height_range VARCHAR,
      stem_radius_base DOUBLE PRECISION,
      stem_radius_top DOUBLE PRECISION,
      leaf_count BIGINT,
      leaf_size DOUBLE PRECISION,
      color_base VARCHAR,
      color_tip VARCHAR,
      unit VARCHAR,
      method VARCHAR,
      confidence DOUBLE PRECISION,
      observed_at VARCHAR,
      source VARCHAR,
      source_id VARCHAR,
      metadata_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_traits_trait_id ON vertex_seibutsu_traits (trait_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_traits_taxon_id ON vertex_seibutsu_traits (taxon_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_traits_taxon_did ON vertex_seibutsu_traits (taxon_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_traits_trait_name ON vertex_seibutsu_traits (trait_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_traits_confidence ON vertex_seibutsu_traits (confidence)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_seibutsu_observation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      observation_id VARCHAR,
      taxon_id VARCHAR,
      observer_did VARCHAR,
      location_name VARCHAR,
      lat DOUBLE PRECISION,
      lng DOUBLE PRECISION,
      observed_at VARCHAR,
      observation_count BIGINT,
      source VARCHAR,
      source_record_id VARCHAR,
      media_url VARCHAR,
      notes VARCHAR,
      metadata_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_observation_observation_id ON vertex_seibutsu_observation (observation_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_observation_taxon_id ON vertex_seibutsu_observation (taxon_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_observation_observer_did ON vertex_seibutsu_observation (observer_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_seibutsu_observation_observed_at ON vertex_seibutsu_observation (observed_at)`.execute(db);

  // --- Count MVs ---
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_crypto_asset_freeze_incident_count AS
    SELECT actor_id, freeze_status, count(*)::bigint AS cnt
    FROM vertex_crypto_asset_freeze_incident
    GROUP BY actor_id, freeze_status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_sanctions_entry_count AS
    SELECT actor_id, list_name, count(*)::bigint AS cnt
    FROM vertex_sanctions_entry
    GROUP BY actor_id, list_name
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_seibutsu_observation_count AS
    SELECT actor_id, taxon_id, count(*)::bigint AS cnt
    FROM vertex_seibutsu_observation
    GROUP BY actor_id, taxon_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_seibutsu_observation_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_sanctions_entry_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_crypto_asset_freeze_incident_count`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_seibutsu_observation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_seibutsu_traits`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_seibutsu_taxon`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_sanctions_list_update`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sanctions_match`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sanctions_entry`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_crypto_asset_freeze_forensic_trace`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_crypto_asset_freeze_request`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_crypto_asset_freeze_incident`.execute(db);
}
