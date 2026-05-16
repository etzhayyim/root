CREATE TABLE IF NOT EXISTS vertex_fund (
      vertex_id       VARCHAR PRIMARY KEY,
      fund_id         VARCHAR,
      name            VARCHAR,
      fund_kind       VARCHAR,
      jurisdiction    VARCHAR,
      aum_amount      DOUBLE PRECISION,
      source_url      VARCHAR,
      source_license  VARCHAR,
      created_date    VARCHAR,
      sensitivity_ord INT         DEFAULT 0,
      owner_did       VARCHAR,
      _seq            BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_rare_earth_coverage (
      vertex_id   VARCHAR PRIMARY KEY,
      mineral     VARCHAR,
      symbol      VARCHAR,
      source      VARCHAR,
      created_at  TIMESTAMPTZ,
      sensitivity_ord INT DEFAULT 0,
      owner_did   VARCHAR,
      _seq        BIGINT
    );

GRANT SELECT, INSERT ON vertex_fund TO root;

GRANT SELECT, INSERT ON vertex_fund TO kaisya_app;

GRANT SELECT, INSERT ON vertex_rare_earth_coverage TO root;

GRANT SELECT, INSERT ON vertex_rare_earth_coverage TO kaisya_app;
