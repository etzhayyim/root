CREATE TABLE IF NOT EXISTS edge_business_person_relation (
      edge_id           VARCHAR PRIMARY KEY,
      src_person_id     VARCHAR,
      dst_person_id     VARCHAR,
      relation_type     VARCHAR,
      org_context       VARCHAR,
      direction         VARCHAR,
      strength          VARCHAR,
      since             VARCHAR,
      description       VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR
    );
