CREATE TABLE IF NOT EXISTS vertex_natural_person_demographic_stat (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      source_id VARCHAR,
      stat_type VARCHAR,
      country VARCHAR,
      region VARCHAR,
      age_min VARCHAR,
      age_max VARCHAR,
      gender VARCHAR,
      income_decile VARCHAR,
      education_isced VARCHAR,
      occupation_isco VARCHAR,
      employment_status VARCHAR,
      marital_status VARCHAR,
      household_size VARCHAR,
      housing_tenure VARCHAR,
      urban_rural VARCHAR,
      health_icd10 VARCHAR,
      disability_type VARCHAR,
      migration_status VARCHAR,
      vital_status VARCHAR,
      era VARCHAR,
      population_count BIGINT,
      population_share DOUBLE PRECISION,
      data_year BIGINT,
      data_currency VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_natural_person_birth_event (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      person_did VARCHAR,
      person_hash VARCHAR,
      birth_year VARCHAR,
      birth_country VARCHAR,
      birth_region VARCHAR,
      birth_municipality VARCHAR,
      parent_a_did VARCHAR,
      parent_b_did VARCHAR,
      parent_a_hash VARCHAR,
      parent_b_hash VARCHAR,
      registration_source VARCHAR,
      registration_id VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_family_relation (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation_type VARCHAR,
      confidence DOUBLE PRECISION,
      effective_from VARCHAR,
      effective_to VARCHAR,
      source_app VARCHAR,
      source_record_id VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_natural_person_person (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      person_hash VARCHAR,
      cohort_did VARCHAR,
      person_did VARCHAR,
      name VARCHAR,
      country VARCHAR,
      birth_year VARCHAR,
      gender VARCHAR,
      org_id_owner VARCHAR,
      registration_method VARCHAR,
      registered_by VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_natural_person_id_document (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      person_hash VARCHAR,
      doc_type VARCHAR,
      doc_number_hash VARCHAR,
      issue_country VARCHAR,
      issue_year VARCHAR,
      expiry_year VARCHAR,
      approval_count BIGINT,
      approval_class VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_natural_person_event_attendee (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      attendee_hash VARCHAR,
      person_did VARCHAR,
      name VARCHAR,
      title VARCHAR,
      company VARCHAR,
      country VARCHAR,
      biography VARCHAR,
      person_id VARCHAR,
      booth VARCHAR,
      event_name VARCHAR,
      event_year BIGINT,
      source_id VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_natural_person_vital_stats AS
    SELECT
      era,
      vital_status,
      COUNT(*) AS person_count
    FROM vertex_natural_person_cohort_person
    GROUP BY era, vital_status;

CREATE INDEX IF NOT EXISTS idx_np_demographic_stat_source ON vertex_natural_person_demographic_stat (source_id);

CREATE INDEX IF NOT EXISTS idx_np_demographic_stat_country ON vertex_natural_person_demographic_stat (country, vital_status);

CREATE INDEX IF NOT EXISTS idx_np_birth_event_person ON vertex_natural_person_birth_event (person_hash);

CREATE INDEX IF NOT EXISTS idx_np_birth_event_year ON vertex_natural_person_birth_event (birth_year, birth_country);

CREATE INDEX IF NOT EXISTS idx_edge_family_src ON edge_family_relation (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_family_dst ON edge_family_relation (dst_vid);

CREATE INDEX IF NOT EXISTS idx_np_person_hash ON vertex_natural_person_person (person_hash);

CREATE INDEX IF NOT EXISTS idx_np_id_doc_person ON vertex_natural_person_id_document (person_hash);

CREATE INDEX IF NOT EXISTS idx_np_attendee_hash ON vertex_natural_person_event_attendee (attendee_hash);

CREATE INDEX IF NOT EXISTS idx_np_attendee_event ON vertex_natural_person_event_attendee (event_name, event_year);
