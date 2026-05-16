CREATE TABLE IF NOT EXISTS vertex_business_person_career_event (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      org_name          VARCHAR,
      org_did           VARCHAR,
      title             VARCHAR,
      department        VARCHAR,
      employment_type   VARCHAR,
      since             VARCHAR,
      until             VARCHAR,
      country           VARCHAR,
      description       VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_business_person_skill (
      edge_id           VARCHAR PRIMARY KEY,
      person_vertex_id  VARCHAR,
      skill_id          VARCHAR,
      proficiency_level VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_business_person_cert (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      cert_name         VARCHAR,
      cert_code         VARCHAR,
      issuer            VARCHAR,
      issued_at         VARCHAR,
      expires_at        VARCHAR,
      credential_url    VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_business_person_edu (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      institution       VARCHAR,
      degree            VARCHAR,
      field_of_study    VARCHAR,
      start_year        VARCHAR,
      end_year          VARCHAR,
      country           VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    );
