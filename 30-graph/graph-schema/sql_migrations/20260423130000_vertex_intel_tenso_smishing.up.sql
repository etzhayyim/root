CREATE TABLE IF NOT EXISTS vertex_intel_report (
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
      analysis_id VARCHAR,
      domain VARCHAR,
      node_label VARCHAR,
      source_app VARCHAR,
      source_collection VARCHAR,
      source_rkey VARCHAR,
      source_did VARCHAR,
      title VARCHAR,
      summary VARCHAR,
      classification VARCHAR,
      source_family VARCHAR,
      collection_method VARCHAR,
      analytic_lens VARCHAR,
      entities_json VARCHAR,
      facts_json VARCHAR,
      findings_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_intel_report_classification ON vertex_intel_report (classification);

CREATE INDEX IF NOT EXISTS idx_intel_report_status ON vertex_intel_report (status);

CREATE INDEX IF NOT EXISTS idx_intel_report_analysis_id ON vertex_intel_report (analysis_id);

CREATE INDEX IF NOT EXISTS idx_intel_report_domain ON vertex_intel_report (domain);

CREATE INDEX IF NOT EXISTS idx_intel_report_actor_created ON vertex_intel_report (actor_id, created_at);

CREATE TABLE IF NOT EXISTS vertex_intel_entity_did (
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
      entity_id VARCHAR,
      name VARCHAR,
      entity_type VARCHAR,
      domain VARCHAR,
      node_label VARCHAR,
      source_analysis VARCHAR,
      source_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_intel_entity_did_entity_id ON vertex_intel_entity_did (entity_id);

CREATE INDEX IF NOT EXISTS idx_intel_entity_did_name ON vertex_intel_entity_did (name);

CREATE INDEX IF NOT EXISTS idx_intel_entity_did_actor_created ON vertex_intel_entity_did (actor_id, created_at);

CREATE TABLE IF NOT EXISTS vertex_intel_inference_chain (
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
      chain_id VARCHAR,
      subject_name VARCHAR,
      subject_did VARCHAR,
      industry VARCHAR,
      source_text VARCHAR,
      source_url VARCHAR,
      steps_count BIGINT,
      cohorts_generated BIGINT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_intel_chain_id ON vertex_intel_inference_chain (chain_id);

CREATE INDEX IF NOT EXISTS idx_intel_chain_subject_did ON vertex_intel_inference_chain (subject_did);

CREATE INDEX IF NOT EXISTS idx_intel_chain_actor_created ON vertex_intel_inference_chain (actor_id, created_at);

CREATE TABLE IF NOT EXISTS vertex_intel_inferred_cohort (
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
      cohort_id VARCHAR,
      chain_id VARCHAR,
      target_domain VARCHAR,
      entity_type VARCHAR,
      layer BIGINT,
      estimated_count DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      methodology VARCHAR,
      inference_rule VARCHAR,
      input_fact VARCHAR,
      assumptions VARCHAR,
      cohort_hash VARCHAR,
      subject_did VARCHAR,
      subject_name VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_intel_cohort_id ON vertex_intel_inferred_cohort (cohort_id);

CREATE INDEX IF NOT EXISTS idx_intel_cohort_chain_id ON vertex_intel_inferred_cohort (chain_id);

CREATE INDEX IF NOT EXISTS idx_intel_cohort_target_domain ON vertex_intel_inferred_cohort (target_domain);

CREATE INDEX IF NOT EXISTS idx_intel_cohort_status ON vertex_intel_inferred_cohort (status);

CREATE TABLE IF NOT EXISTS vertex_tenso_transfer_request (
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
      transfer_id VARCHAR,
      sender_did VARCHAR,
      recipient_did VARCHAR,
      filename VARCHAR,
      mime_type VARCHAR,
      size_bytes BIGINT,
      chunk_count BIGINT,
      expire_at VARCHAR,
      max_downloads BIGINT,
      project_convo_id VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_tenso_transfer_request_transfer_id ON vertex_tenso_transfer_request (transfer_id);

CREATE INDEX IF NOT EXISTS idx_tenso_transfer_request_sender ON vertex_tenso_transfer_request (sender_did);

CREATE INDEX IF NOT EXISTS idx_tenso_transfer_request_recipient ON vertex_tenso_transfer_request (recipient_did);

CREATE INDEX IF NOT EXISTS idx_tenso_transfer_request_status ON vertex_tenso_transfer_request (status);

CREATE TABLE IF NOT EXISTS vertex_tenso_file_manifest (
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
      transfer_id VARCHAR,
      chunk_count BIGINT,
      chunk_size BIGINT,
      total_size BIGINT,
      encrypted_payload VARCHAR,
      payload VARCHAR,
      chunk_cids_json VARCHAR,
      blob_keys_json VARCHAR,
      manifest_hash VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_tenso_file_manifest_transfer_id ON vertex_tenso_file_manifest (transfer_id);

CREATE INDEX IF NOT EXISTS idx_tenso_file_manifest_created ON vertex_tenso_file_manifest (created_at);

CREATE TABLE IF NOT EXISTS vertex_tenso_transfer_log (
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
      transfer_id VARCHAR,
      event_type VARCHAR,
      actor_did VARCHAR,
      ip_hash VARCHAR,
      user_agent_hash VARCHAR,
      details_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_tenso_transfer_log_transfer_id ON vertex_tenso_transfer_log (transfer_id);

CREATE INDEX IF NOT EXISTS idx_tenso_transfer_log_event_type ON vertex_tenso_transfer_log (event_type);

CREATE INDEX IF NOT EXISTS idx_tenso_transfer_log_created ON vertex_tenso_transfer_log (created_at);

CREATE TABLE IF NOT EXISTS vertex_tenso_access_control (
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
      transfer_id VARCHAR,
      recipient_did VARCHAR,
      encrypted_payload VARCHAR,
      permissions_json VARCHAR,
      max_downloads BIGINT,
      downloads_used BIGINT,
      expire_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_tenso_access_control_transfer_id ON vertex_tenso_access_control (transfer_id);

CREATE INDEX IF NOT EXISTS idx_tenso_access_control_recipient ON vertex_tenso_access_control (recipient_did);

CREATE INDEX IF NOT EXISTS idx_tenso_access_control_status ON vertex_tenso_access_control (status);

CREATE TABLE IF NOT EXISTS vertex_smishing_sms_message (
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
      sms_id VARCHAR,
      sender_hash VARCHAR,
      sender_address VARCHAR,
      body VARCHAR,
      type VARCHAR,
      timestamp VARCHAR,
      has_urls BOOLEAN,
      url_count BIGINT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_smishing_sms_id ON vertex_smishing_sms_message (sms_id);

CREATE INDEX IF NOT EXISTS idx_smishing_sms_sender_hash ON vertex_smishing_sms_message (sender_hash);

CREATE INDEX IF NOT EXISTS idx_smishing_sms_timestamp ON vertex_smishing_sms_message (timestamp);

CREATE TABLE IF NOT EXISTS vertex_smishing_threat_detection (
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
      analysis_id VARCHAR,
      sms_id VARCHAR,
      classification VARCHAR,
      confidence VARCHAR,
      reason VARCHAR,
      score DOUBLE PRECISION,
      url_count BIGINT,
      urls_json VARCHAR,
      domains_json VARCHAR,
      sender_did VARCHAR,
      geo_intel VARCHAR,
      generated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_smishing_threat_analysis_id ON vertex_smishing_threat_detection (analysis_id);

CREATE INDEX IF NOT EXISTS idx_smishing_threat_sms_id ON vertex_smishing_threat_detection (sms_id);

CREATE INDEX IF NOT EXISTS idx_smishing_threat_classification ON vertex_smishing_threat_detection (classification);

CREATE INDEX IF NOT EXISTS idx_smishing_threat_score ON vertex_smishing_threat_detection (score);

CREATE TABLE IF NOT EXISTS vertex_smishing_url_intel (
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
      url_id VARCHAR,
      analysis_id VARCHAR,
      sms_id VARCHAR,
      url VARCHAR,
      domain VARCHAR,
      score DOUBLE PRECISION,
      classification VARCHAR,
      ip_address VARCHAR,
      asn VARCHAR,
      country VARCHAR,
      provider VARCHAR,
      ioc_confirmed BOOLEAN,
      ioc_confirmed_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_smishing_url_intel_url_id ON vertex_smishing_url_intel (url_id);

CREATE INDEX IF NOT EXISTS idx_smishing_url_intel_analysis_id ON vertex_smishing_url_intel (analysis_id);

CREATE INDEX IF NOT EXISTS idx_smishing_url_intel_domain ON vertex_smishing_url_intel (domain);

CREATE TABLE IF NOT EXISTS vertex_smishing_sender_blocklist (
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
      block_id VARCHAR,
      sender_hash VARCHAR,
      sender_address VARCHAR,
      sender_did VARCHAR,
      reason VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_smishing_blocklist_block_id ON vertex_smishing_sender_blocklist (block_id);

CREATE INDEX IF NOT EXISTS idx_smishing_blocklist_sender_hash ON vertex_smishing_sender_blocklist (sender_hash);

CREATE INDEX IF NOT EXISTS idx_smishing_blocklist_status ON vertex_smishing_sender_blocklist (status);

CREATE TABLE IF NOT EXISTS vertex_smishing_phishing_report (
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
      report_id VARCHAR,
      analysis_id VARCHAR,
      classification VARCHAR,
      score DOUBLE PRECISION,
      sender_did VARCHAR,
      urls_json VARCHAR,
      domains_json VARCHAR,
      geo_intel VARCHAR,
      generated_at VARCHAR,
      jpcert_url VARCHAR,
      ipa_url VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_smishing_report_report_id ON vertex_smishing_phishing_report (report_id);

CREATE INDEX IF NOT EXISTS idx_smishing_report_analysis_id ON vertex_smishing_phishing_report (analysis_id);

CREATE INDEX IF NOT EXISTS idx_smishing_report_score ON vertex_smishing_phishing_report (score);

CREATE TABLE IF NOT EXISTS vertex_smishing_takedown_request (
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
      takedown_id VARCHAR,
      url_id VARCHAR,
      analysis_id VARCHAR,
      domain VARCHAR,
      abuse_contact VARCHAR,
      abuse_ref VARCHAR,
      requested_at VARCHAR,
      resolved_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_smishing_takedown_id ON vertex_smishing_takedown_request (takedown_id);

CREATE INDEX IF NOT EXISTS idx_smishing_takedown_url_id ON vertex_smishing_takedown_request (url_id);

CREATE INDEX IF NOT EXISTS idx_smishing_takedown_status ON vertex_smishing_takedown_request (status);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_intel_report_count AS
    SELECT actor_id, count(*)::bigint AS cnt
    FROM vertex_intel_report
    GROUP BY actor_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_intel_entity_did_count AS
    SELECT actor_id, count(*)::bigint AS cnt
    FROM vertex_intel_entity_did
    GROUP BY actor_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_tenso_transfer_request_count AS
    SELECT actor_id, status, count(*)::bigint AS cnt
    FROM vertex_tenso_transfer_request
    GROUP BY actor_id, status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_smishing_threat_detection_count AS
    SELECT actor_id, classification, count(*)::bigint AS cnt
    FROM vertex_smishing_threat_detection
    GROUP BY actor_id, classification;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_smishing_sender_blocklist_count AS
    SELECT actor_id, count(*)::bigint AS cnt
    FROM vertex_smishing_sender_blocklist
    GROUP BY actor_id;
