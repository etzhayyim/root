CREATE TABLE IF NOT EXISTS vertex_press_signal (
      vertex_id         VARCHAR PRIMARY KEY,
      source            VARCHAR,
      source_url        VARCHAR,
      source_license    VARCHAR,
      company_name      VARCHAR,
      company_did       VARCHAR,
      headline          VARCHAR,
      body_snippet      VARCHAR,
      trigger_type      VARCHAR,
      trigger_score     DOUBLE PRECISION,
      isco_codes        VARCHAR,
      country           VARCHAR,
      published_at      VARCHAR,
      detected_at       VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_demand_forecast (
      vertex_id           VARCHAR PRIMARY KEY,
      isco_code           VARCHAR,
      country             VARCHAR,
      period              VARCHAR,
      demand_score        DOUBLE PRECISION,
      supply_size_k       DOUBLE PRECISION,
      typical_salary      DOUBLE PRECISION,
      salary_currency     VARCHAR,
      engagement_types    VARCHAR,
      top_skills          VARCHAR,
      press_signal_count  BIGINT,
      posting_count       BIGINT,
      computed_at         VARCHAR
    );
