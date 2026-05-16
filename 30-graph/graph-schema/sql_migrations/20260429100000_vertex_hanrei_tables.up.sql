CREATE TABLE IF NOT EXISTS vertex_hanrei_court (
      vertex_id       VARCHAR PRIMARY KEY,
      court_id        VARCHAR NOT NULL,
      name            VARCHAR NOT NULL,
      court_did       VARCHAR,
      search_url      VARCHAR,
      actor_did       VARCHAR NOT NULL,
      org_did         VARCHAR NOT NULL,
      created_at      TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS vertex_hanrei_jurisdiction (
      vertex_id           VARCHAR PRIMARY KEY,
      iso3                VARCHAR NOT NULL,
      jurisdiction_did    VARCHAR,
      case_db_url         VARCHAR,
      legislation_url     VARCHAR,
      gazette_url         VARCHAR,
      actor_did           VARCHAR NOT NULL,
      org_did             VARCHAR NOT NULL,
      created_at          TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS vertex_hanrei_collection_job (
      vertex_id       VARCHAR PRIMARY KEY,
      job_id          VARCHAR NOT NULL,
      job_type        VARCHAR NOT NULL,
      court_id        VARCHAR,
      source_id       VARCHAR,
      iso3            VARCHAR,
      target_url      VARCHAR NOT NULL,
      page            INTEGER,
      status          VARCHAR NOT NULL DEFAULT 'queued',
      start_date      VARCHAR,
      end_date        VARCHAR,
      law_id          VARCHAR,
      category_id     INTEGER,
      category_name   VARCHAR,
      query_id        VARCHAR,
      sparql          VARCHAR,
      actor_did       VARCHAR NOT NULL,
      org_did         VARCHAR NOT NULL,
      created_at      TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_hanrei_collection_job_status
      ON vertex_hanrei_collection_job (status);

CREATE INDEX IF NOT EXISTS idx_hanrei_collection_job_type
      ON vertex_hanrei_collection_job (job_type);

CREATE TABLE IF NOT EXISTS vertex_hanrei_case_record (
      vertex_id       VARCHAR PRIMARY KEY,
      rkey            VARCHAR NOT NULL,
      title           VARCHAR,
      case_number     VARCHAR,
      court_id        VARCHAR,
      decision_date   VARCHAR,
      summary         VARCHAR,
      iso3            VARCHAR NOT NULL DEFAULT 'jpn',
      status          VARCHAR NOT NULL DEFAULT 'active',
      actor_did       VARCHAR NOT NULL,
      org_did         VARCHAR NOT NULL,
      created_at      TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_hanrei_case_record_court_id
      ON vertex_hanrei_case_record (court_id);

CREATE INDEX IF NOT EXISTS idx_hanrei_case_record_iso3
      ON vertex_hanrei_case_record (iso3);
