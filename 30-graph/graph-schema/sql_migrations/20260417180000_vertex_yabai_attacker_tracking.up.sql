CREATE TABLE IF NOT EXISTS vertex_yabai_tracking_bait (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      bait_id           VARCHAR,
      target_entity_id  VARCHAR,
      bait_type         VARCHAR,
      bait_url          VARCHAR,
      embedded_in       VARCHAR,
      campaign_id       VARCHAR,
      status            VARCHAR,
      deployed_at       VARCHAR,
      expires_at        VARCHAR,
      hit_count         BIGINT,
      unique_ip_count   BIGINT,
      first_hit_at      VARCHAR,
      last_hit_at       VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_yabai_tracking_hit (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      hit_id             VARCHAR,
      bait_id            VARCHAR,
      target_entity_id   VARCHAR,
      accessor_ip        VARCHAR,
      geoip_country      VARCHAR,
      geoip_city         VARCHAR,
      geoip_asn          BIGINT,
      geoip_isp          VARCHAR,
      is_proxy           BOOLEAN,
      is_datacenter      BOOLEAN,
      is_tor             BOOLEAN,
      is_vpn             BOOLEAN,
      user_agent         VARCHAR,
      ua_browser         VARCHAR,
      ua_os              VARCHAR,
      ua_device_type     VARCHAR,
      device_fingerprint VARCHAR,
      canvas_hash        VARCHAR,
      webgl_renderer     VARCHAR,
      screen_resolution  VARCHAR,
      timezone           VARCHAR,
      accept_language    VARCHAR,
      tls_ja3            VARCHAR,
      tls_ja3s           VARCHAR,
      referrer           VARCHAR,
      http_method        VARCHAR,
      http_path          VARCHAR,
      http_headers_json  VARCHAR,
      session_id         VARCHAR,
      accessed_at        VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_bait_targets_entity (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      campaign_id     VARCHAR,
      created_at      VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_hit_triggered_bait (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      created_at      VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_hit_from_ip (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      created_at      VARCHAR
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attacker_ip_timeline AS
    SELECT
      target_entity_id,
      accessor_ip,
      MIN(accessed_at) AS first_seen,
      MAX(accessed_at) AS last_seen,
      COUNT(*) AS hit_count,
      MAX(geoip_country) AS geoip_country,
      MAX(geoip_asn) AS geoip_asn,
      MAX(geoip_isp) AS geoip_isp,
      BOOL_OR(is_proxy) AS ever_proxy,
      BOOL_OR(is_datacenter) AS ever_datacenter,
      BOOL_OR(is_tor) AS ever_tor
    FROM vertex_yabai_tracking_hit
    WHERE target_entity_id IS NOT NULL AND accessor_ip IS NOT NULL
    GROUP BY target_entity_id, accessor_ip;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attacker_device_timeline AS
    SELECT
      target_entity_id,
      device_fingerprint,
      COUNT(DISTINCT accessor_ip) AS distinct_ip_count,
      COUNT(*) AS hit_count,
      MIN(accessed_at) AS first_seen,
      MAX(accessed_at) AS last_seen,
      MAX(ua_browser) AS ua_browser,
      MAX(ua_os) AS ua_os,
      MAX(canvas_hash) AS canvas_hash,
      MAX(webgl_renderer) AS webgl_renderer
    FROM vertex_yabai_tracking_hit
    WHERE target_entity_id IS NOT NULL AND device_fingerprint IS NOT NULL
    GROUP BY target_entity_id, device_fingerprint;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attacker_rotation_alert AS
    SELECT
      target_entity_id,
      device_fingerprint,
      distinct_ip_count,
      hit_count,
      first_seen,
      last_seen
    FROM mv_attacker_device_timeline
    WHERE distinct_ip_count >= 3;

CREATE INDEX IF NOT EXISTS idx_tracking_hit_bait ON vertex_yabai_tracking_hit (bait_id);

CREATE INDEX IF NOT EXISTS idx_tracking_hit_entity ON vertex_yabai_tracking_hit (target_entity_id);

CREATE INDEX IF NOT EXISTS idx_tracking_hit_ip ON vertex_yabai_tracking_hit (accessor_ip);

CREATE INDEX IF NOT EXISTS idx_tracking_hit_device ON vertex_yabai_tracking_hit (device_fingerprint);

CREATE INDEX IF NOT EXISTS idx_tracking_bait_target ON vertex_yabai_tracking_bait (target_entity_id);
