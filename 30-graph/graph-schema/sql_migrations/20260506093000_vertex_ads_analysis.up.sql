CREATE TABLE IF NOT EXISTS vertex_ads_analysis (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      creative_vertex_id    VARCHAR,
      platform              VARCHAR,
      platform_ad_id        VARCHAR,
      analysis_kind         VARCHAR,
      model_id              VARCHAR,
      status                VARCHAR,
      summary               VARCHAR,
      risk_score_permille   BIGINT,
      claim_json            VARCHAR,
      targeting_json        VARCHAR,
      signals_json          VARCHAR,
      source_snapshot_id    VARCHAR,
      analyzed_at           VARCHAR,
      org_id                VARCHAR,
      user_id               VARCHAR,
      actor_id              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_ads_analysis_creative ON vertex_ads_analysis (creative_vertex_id);

CREATE INDEX IF NOT EXISTS idx_vertex_ads_analysis_platform_kind ON vertex_ads_analysis (platform, analysis_kind, analyzed_at);

CREATE INDEX IF NOT EXISTS idx_vertex_ads_analysis_risk ON vertex_ads_analysis (risk_score_permille);
