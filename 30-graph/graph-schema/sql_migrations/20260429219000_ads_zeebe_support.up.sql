CREATE TABLE IF NOT EXISTS vertex_ads_campaign (
      vertex_id VARCHAR PRIMARY KEY,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      collection VARCHAR,
      campaign_id VARCHAR,
      did VARCHAR,
      name VARCHAR,
      description VARCHAR,
      advertiser VARCHAR,
      budget_jpy BIGINT,
      active BOOLEAN,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_ads_sponsored_post (
      vertex_id VARCHAR PRIMARY KEY,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      collection VARCHAR,
      campaign_id VARCHAR,
      post_uri VARCHAR,
      cid VARCHAR,
      text VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_ads_campaign_created ON vertex_ads_campaign (created_at);

CREATE INDEX IF NOT EXISTS idx_ads_campaign_id ON vertex_ads_campaign (campaign_id);

CREATE INDEX IF NOT EXISTS idx_ads_sponsored_campaign ON vertex_ads_sponsored_post (campaign_id, created_at);
