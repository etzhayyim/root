ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS source_type VARCHAR NOT NULL DEFAULT 'rss';

ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS crawl_interval_min INTEGER NOT NULL DEFAULT 15;

ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS writer_did VARCHAR;

ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS subcategory VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS title_original VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS title_ja VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS title_en VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS summary_original VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS summary_ja VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS summary_en VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS entities_json TEXT;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS tags_json TEXT;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS sentiment VARCHAR;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS importance INTEGER NOT NULL DEFAULT 0;

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS visibility VARCHAR NOT NULL DEFAULT 'free';

ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS writer_did VARCHAR;

ALTER TABLE vertex_handotai_digest ADD COLUMN IF NOT EXISTS summary_ja TEXT;

ALTER TABLE vertex_handotai_digest ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP;

CREATE TABLE IF NOT EXISTS vertex_handotai_collection_job (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT '',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      job_id VARCHAR NOT NULL,
      requested_at TIMESTAMP,
      started_at TIMESTAMP,
      finished_at TIMESTAMP,
      sources_count INTEGER NOT NULL DEFAULT 0,
      articles_count INTEGER NOT NULL DEFAULT 0
    );

CREATE TABLE IF NOT EXISTS vertex_handotai_report (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT '',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      report_id VARCHAR NOT NULL,
      report_type VARCHAR NOT NULL DEFAULT 'weekly',
      entity_key VARCHAR,
      period VARCHAR,
      total_articles INTEGER NOT NULL DEFAULT 0,
      report_ja TEXT,
      generated_at TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS vertex_handotai_alert (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT '',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      alert_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      filter_categories_json TEXT,
      filter_entities_json TEXT,
      filter_keywords_json TEXT,
      filter_importance_min INTEGER NOT NULL DEFAULT 0,
      notify_channel VARCHAR,
      notify_email VARCHAR,
      tier VARCHAR NOT NULL DEFAULT 'free',
      enabled BOOLEAN NOT NULL DEFAULT true
    );

CREATE TABLE IF NOT EXISTS vertex_handotai_subscription (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      sub_id VARCHAR NOT NULL,
      tier VARCHAR NOT NULL DEFAULT 'free',
      company_name VARCHAR,
      tracked_entities_json TEXT,
      started_at TIMESTAMP,
      expires_at TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS vertex_handotai_semi_entity (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      entity_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      entity_type VARCHAR NOT NULL DEFAULT 'company',
      country VARCHAR,
      segment VARCHAR,
      did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_handotai_chip (
      vertex_id VARCHAR PRIMARY KEY,
      chip_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      manufacturer VARCHAR,
      product_family VARCHAR,
      source_url VARCHAR,
      source_title VARCHAR,
      source_domain VARCHAR,
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 300
    );

CREATE TABLE IF NOT EXISTS edge_handotai_source_article (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      article_id VARCHAR NOT NULL,
      relation VARCHAR NOT NULL DEFAULT 'published',
      created_at TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS edge_handotai_article_entity (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      article_id VARCHAR NOT NULL,
      entity_key VARCHAR NOT NULL,
      relation VARCHAR NOT NULL DEFAULT 'mentions',
      created_at TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS edge_handotai_subscription_entity (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      sub_id VARCHAR NOT NULL,
      entity_key VARCHAR NOT NULL,
      relation VARCHAR NOT NULL DEFAULT 'tracks',
      created_at TIMESTAMP
    );

CREATE TABLE IF NOT EXISTS edge_handotai_chip_source_page (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      chip_id VARCHAR NOT NULL,
      source_url VARCHAR,
      relation VARCHAR NOT NULL DEFAULT 'extracted_from',
      created_at TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_handotai_source_category_enabled ON vertex_handotai_source (category, enabled);

CREATE INDEX IF NOT EXISTS idx_handotai_source_writer_did ON vertex_handotai_source (writer_did);

CREATE INDEX IF NOT EXISTS idx_handotai_article_category ON vertex_handotai_article (category);

CREATE INDEX IF NOT EXISTS idx_handotai_article_source_name ON vertex_handotai_article (source_name);

CREATE INDEX IF NOT EXISTS idx_handotai_article_writer_did ON vertex_handotai_article (writer_did);

CREATE INDEX IF NOT EXISTS idx_handotai_alert_enabled_tier ON vertex_handotai_alert (enabled, tier);

CREATE INDEX IF NOT EXISTS idx_handotai_subscription_status_tier ON vertex_handotai_subscription (status, tier);

CREATE INDEX IF NOT EXISTS idx_handotai_semi_entity_type_country_segment ON vertex_handotai_semi_entity (entity_type, country, segment);

CREATE INDEX IF NOT EXISTS idx_handotai_chip_name ON vertex_handotai_chip (name);

CREATE INDEX IF NOT EXISTS idx_handotai_chip_manufacturer ON vertex_handotai_chip (manufacturer);

CREATE INDEX IF NOT EXISTS idx_handotai_edge_source_article_source ON edge_handotai_source_article (source_id);

CREATE INDEX IF NOT EXISTS idx_handotai_edge_article_entity_key ON edge_handotai_article_entity (entity_key);

CREATE INDEX IF NOT EXISTS idx_handotai_edge_subscription_entity_key ON edge_handotai_subscription_entity (entity_key);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_handotai_article_category_counts AS
    SELECT category, COUNT(*) AS article_count, MAX(published_at) AS latest_published_at
    FROM vertex_handotai_article
    GROUP BY category;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_handotai_alert_status_counts AS
    SELECT enabled, tier, COUNT(*) AS alert_count
    FROM vertex_handotai_alert
    GROUP BY enabled, tier;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_handotai_subscription_tier_counts AS
    SELECT status, tier, COUNT(*) AS subscription_count
    FROM vertex_handotai_subscription
    GROUP BY status, tier;
