CREATE TABLE IF NOT EXISTS vertex_skill (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      source_homepage   VARCHAR,
      code              VARCHAR,
      esco_id           VARCHAR,
      skill_type        VARCHAR,
      reuse_level       VARCHAR,
      name              VARCHAR,
      description       VARCHAR,
      alt_labels        VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_occupation_skill (
      edge_id           VARCHAR PRIMARY KEY,
      occupation_id     VARCHAR,
      skill_id          VARCHAR,
      relation_type     VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      ingested_at       VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_skill_skill (
      edge_id           VARCHAR PRIMARY KEY,
      requiring_id      VARCHAR,
      required_id       VARCHAR,
      relation_type     VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      ingested_at       VARCHAR
    );
