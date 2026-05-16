import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Yabai attacker tracking — bait URLs + access logs + IP timeline.
 *
 * Use-case (2026-04-17): spam/BEC actor identified via yabai entity/evidence
 * (e.g. AlexaKing1726@outlook.com). Unique bait URL is embedded in a reply
 * or decoy page. When the attacker visits, yabai-tracker Worker records:
 *   - IP + GeoIP + ASN + proxy/datacenter/tor flags
 *   - UA + device fingerprint + TLS JA3
 *   - Session cookies, referrer, timestamps
 *
 * Continuous actor attribution: same device_fingerprint or canvas_hash
 * across multiple IPs → proxy rotation detected → cluster to single actor.
 *
 * Bait embedding channels:
 *   - reply email (tracking pixel 1x1 img)
 *   - decoy link in reply ("unsubscribe", "view invoice")
 *   - canary document (PDF/DOCX with remote image)
 *   - honeypot form (submit to tracking endpoint)
 *
 * Read path: `G("YabaiAttackerHit").Match(Eq{"bait_id": "bait-xxx"}).Query()`
 * Cross-link: `mv_attacker_ip_timeline` rolls up hits per entity.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Bait registry: one row per deployed tracking resource
  await sql`
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
    )
  `.execute(db);

  // Hit log: one row per request to a bait URL
  await sql`
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
    )
  `.execute(db);

  // Edge: bait → target yabai entity (attacker email/person/org)
  await sql`
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
    )
  `.execute(db);

  // Edge: hit → bait (which bait URL triggered the hit)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hit_triggered_bait (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      created_at      VARCHAR
    )
  `.execute(db);

  // Edge: hit → ipaddress vertex (link to vertex_ip_address / GeoipEnrichment)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hit_from_ip (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      created_at      VARCHAR
    )
  `.execute(db);

  // MV: per-entity IP timeline (aggregate all hits for one attacker)
  await sql`
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
    GROUP BY target_entity_id, accessor_ip
  `.execute(db);

  // MV: device-fingerprint timeline (detect proxy rotation — same device, multiple IPs)
  await sql`
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
    GROUP BY target_entity_id, device_fingerprint
  `.execute(db);

  // MV: proxy-rotation alert (same fingerprint, >=3 IPs in 1h window)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attacker_rotation_alert AS
    SELECT
      target_entity_id,
      device_fingerprint,
      distinct_ip_count,
      hit_count,
      first_seen,
      last_seen
    FROM mv_attacker_device_timeline
    WHERE distinct_ip_count >= 3
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_tracking_hit_bait ON vertex_yabai_tracking_hit (bait_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tracking_hit_entity ON vertex_yabai_tracking_hit (target_entity_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tracking_hit_ip ON vertex_yabai_tracking_hit (accessor_ip)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tracking_hit_device ON vertex_yabai_tracking_hit (device_fingerprint)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tracking_bait_target ON vertex_yabai_tracking_bait (target_entity_id)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_attacker_rotation_alert`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_attacker_device_timeline`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_attacker_ip_timeline`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_hit_from_ip`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_hit_triggered_bait`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_bait_targets_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_tracking_hit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_tracking_bait`.execute(db);
}
