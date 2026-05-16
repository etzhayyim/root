CREATE TABLE IF NOT EXISTS vertex_ads_campaign_cluster (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      campaign_key          VARCHAR,
      platform_scope        VARCHAR,
      advertiser_vertex_id  VARCHAR,
      advertiser_name       VARCHAR,
      landing_domain        VARCHAR,
      claim_token           VARCHAR,
      sample_headline       VARCHAR,
      sample_body_text      VARCHAR,
      creative_count        BIGINT,
      platform_count        BIGINT,
      first_seen_at         VARCHAR,
      last_seen_at          VARCHAR,
      risk_score_permille   BIGINT,
      summary               VARCHAR,
      org_id                VARCHAR,
      user_id               VARCHAR,
      actor_id              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_ads_campaign_cluster_key ON vertex_ads_campaign_cluster (campaign_key);

CREATE INDEX IF NOT EXISTS idx_vertex_ads_campaign_cluster_advertiser_domain ON vertex_ads_campaign_cluster (advertiser_vertex_id, landing_domain);

CREATE INDEX IF NOT EXISTS idx_vertex_ads_campaign_cluster_last_seen ON vertex_ads_campaign_cluster (last_seen_at);

CREATE TABLE IF NOT EXISTS edge_ads_creative_in_campaign (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      platform        VARCHAR,
      platform_ad_id  VARCHAR,
      match_basis     VARCHAR,
      created_at      VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_ads_creative_in_campaign_src ON edge_ads_creative_in_campaign (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_ads_creative_in_campaign_dst ON edge_ads_creative_in_campaign (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_ads_creative_in_campaign_platform ON edge_ads_creative_in_campaign (platform, platform_ad_id);
