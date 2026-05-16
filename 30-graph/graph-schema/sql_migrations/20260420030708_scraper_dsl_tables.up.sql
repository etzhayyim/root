CREATE TABLE IF NOT EXISTS vertex_scraper_source (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      source_url       VARCHAR,
      ministry_did     VARCHAR,
      fetch_method     VARCHAR,
      content_type     VARCHAR,
      ua               VARCHAR,
      rate_ms          BIGINT,
      robots_allow     VARCHAR,
      status           VARCHAR,
      last_fetched_at  VARCHAR,
      last_status      VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      created_at       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vss_ministry ON vertex_scraper_source (ministry_did);

CREATE INDEX IF NOT EXISTS idx_vss_status   ON vertex_scraper_source (status);

CREATE TABLE IF NOT EXISTS vertex_scraper_dsl (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      source_vid         VARCHAR,
      dsl_kind           VARCHAR,
      target_table       VARCHAR,
      target_columns     VARCHAR,
      extract_hints      VARCHAR,
      edge_emit          VARCHAR,
      llm_model          VARCHAR,
      max_rows_per_run   BIGINT,
      prompt_override    VARCHAR,
      bpmn_process_id    VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      created_at         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vsd_source   ON vertex_scraper_dsl (source_vid);

CREATE INDEX IF NOT EXISTS idx_vsd_target   ON vertex_scraper_dsl (target_table);

CREATE TABLE IF NOT EXISTS vertex_scraper_run (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      dsl_vid          VARCHAR,
      started_at       VARCHAR,
      finished_at      VARCHAR,
      status           VARCHAR,
      fetched_bytes    BIGINT,
      extracted_rows   BIGINT,
      emitted_records  BIGINT,
      emitted_edges    BIGINT,
      llm_tokens_in    BIGINT,
      llm_tokens_out   BIGINT,
      error_summary    VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      created_at       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vsr_dsl    ON vertex_scraper_run (dsl_vid, started_at);

CREATE INDEX IF NOT EXISTS idx_vsr_status ON vertex_scraper_run (status);

CREATE TABLE IF NOT EXISTS edge_scraper_emits (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      emitted_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      created_at       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_ese_src ON edge_scraper_emits (src_vid);

CREATE INDEX IF NOT EXISTS idx_ese_dst ON edge_scraper_emits (dst_vid);
