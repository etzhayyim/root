CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_publisher (
      vertex_id          VARCHAR PRIMARY KEY,
      publisher_id       VARCHAR NOT NULL,
      domain             VARCHAR NOT NULL,
      owner_did          VARCHAR,
      revenue_share_pct  DOUBLE PRECISION NOT NULL DEFAULT 70.0,
      floor_cpm_usd      DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      content_category   VARCHAR,
      ad_policy          VARCHAR NOT NULL DEFAULT 'standard',
      status             VARCHAR NOT NULL DEFAULT 'active',
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 0,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_advertiser (
      vertex_id          VARCHAR PRIMARY KEY,
      advertiser_id      VARCHAR NOT NULL,
      brand_name         VARCHAR NOT NULL,
      domain             VARCHAR,
      industry_category  VARCHAR,
      monthly_budget_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      payment_method     VARCHAR,
      status             VARCHAR NOT NULL DEFAULT 'active',
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 0,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_campaign (
      vertex_id          VARCHAR PRIMARY KEY,
      campaign_id        VARCHAR NOT NULL,
      advertiser_did     VARCHAR NOT NULL,
      name               VARCHAR NOT NULL,
      objective          VARCHAR NOT NULL DEFAULT 'awareness',
      budget_daily_usd   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      bid_strategy       VARCHAR NOT NULL DEFAULT 'cpm',
      bid_floor_usd      DOUBLE PRECISION,
      targeting_json     VARCHAR,
      start_date         VARCHAR,
      end_date           VARCHAR,
      status             VARCHAR NOT NULL DEFAULT 'draft',
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 0,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_ad_unit (
      vertex_id              VARCHAR PRIMARY KEY,
      unit_id                VARCHAR NOT NULL,
      publisher_did          VARCHAR NOT NULL,
      unit_type              VARCHAR NOT NULL DEFAULT 'display',
      size                   VARCHAR,
      placement              VARCHAR,
      floor_cpm_usd          DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      active_campaign_count  INTEGER NOT NULL DEFAULT 0,
      status                 VARCHAR NOT NULL DEFAULT 'active',
      created_at             VARCHAR NOT NULL,
      sensitivity_ord        INTEGER NOT NULL DEFAULT 0,
      org_id                 VARCHAR,
      user_id                VARCHAR,
      actor_id               VARCHAR,
      actor_did              VARCHAR,
      org_did                VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_impression (
      vertex_id        VARCHAR PRIMARY KEY,
      imp_id           VARCHAR NOT NULL,
      unit_id          VARCHAR NOT NULL,
      campaign_id      VARCHAR NOT NULL,
      cpm_usd          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      viewable         BOOLEAN NOT NULL DEFAULT false,
      user_cohort      VARCHAR,
      country_iso2     VARCHAR,
      ts_ms            BIGINT NOT NULL,
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  INTEGER NOT NULL DEFAULT 0,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      actor_did        VARCHAR,
      org_did          VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_click (
      vertex_id        VARCHAR PRIMARY KEY,
      click_id         VARCHAR NOT NULL,
      imp_id           VARCHAR,
      unit_id          VARCHAR NOT NULL,
      campaign_id      VARCHAR NOT NULL,
      cpc_usd          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      country_iso2     VARCHAR,
      ts_ms            BIGINT NOT NULL,
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  INTEGER NOT NULL DEFAULT 0,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      actor_did        VARCHAR,
      org_did          VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_conversion (
      vertex_id        VARCHAR PRIMARY KEY,
      conv_id          VARCHAR NOT NULL,
      click_id         VARCHAR,
      campaign_id      VARCHAR NOT NULL,
      conv_type        VARCHAR NOT NULL DEFAULT 'lead',
      conv_value_usd   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      ts_ms            BIGINT NOT NULL,
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  INTEGER NOT NULL DEFAULT 0,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      actor_did        VARCHAR,
      org_did          VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_revenue_snapshot (
      vertex_id          VARCHAR PRIMARY KEY,
      snap_id            VARCHAR NOT NULL,
      publisher_did      VARCHAR NOT NULL,
      date               VARCHAR NOT NULL,
      impressions        BIGINT NOT NULL DEFAULT 0,
      clicks             BIGINT NOT NULL DEFAULT 0,
      conversions        BIGINT NOT NULL DEFAULT 0,
      total_revenue_usd  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      rpm_usd            DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      ctr_pct            DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      cvr_pct            DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      ai_insight         VARCHAR,
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 0,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    );

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_adnetwork_campaign_funnel AS
    SELECT
      i.campaign_id,
      count(DISTINCT i.imp_id) AS impressions,
      count(DISTINCT c.click_id) AS clicks,
      count(DISTINCT cv.conv_id) AS conversions,
      CASE WHEN count(DISTINCT i.imp_id) = 0 THEN 0.0
           ELSE count(DISTINCT c.click_id)::double precision / count(DISTINCT i.imp_id)::double precision * 100.0
      END AS ctr_pct,
      CASE WHEN count(DISTINCT c.click_id) = 0 THEN 0.0
           ELSE count(DISTINCT cv.conv_id)::double precision / count(DISTINCT c.click_id)::double precision * 100.0
      END AS cvr_pct,
      sum(i.cpm_usd) / 1000.0 AS total_spend_usd
    FROM vertex_open_adnetwork_impression i
    LEFT JOIN vertex_open_adnetwork_click c ON c.campaign_id = i.campaign_id
    LEFT JOIN vertex_open_adnetwork_conversion cv ON cv.campaign_id = i.campaign_id
    GROUP BY i.campaign_id;

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_adnetwork_publisher_daily_kpi AS
    SELECT
      r.publisher_did,
      r.date,
      r.impressions,
      r.clicks,
      r.conversions,
      r.total_revenue_usd,
      r.rpm_usd,
      r.ctr_pct,
      r.cvr_pct
    FROM vertex_open_adnetwork_revenue_snapshot r;

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_adnetwork_market_cpm_range AS
    SELECT
      unit_type,
      count(*) AS unit_count,
      min(floor_cpm_usd) AS min_floor_cpm,
      avg(floor_cpm_usd) AS avg_floor_cpm,
      max(floor_cpm_usd) AS max_floor_cpm
    FROM vertex_open_adnetwork_ad_unit
    WHERE status = 'active'
    GROUP BY unit_type;

FLUSH;
