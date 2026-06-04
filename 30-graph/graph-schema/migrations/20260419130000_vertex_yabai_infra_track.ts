import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Yabai phishing-infrastructure tracking table.
 *
 * One row per (domain, probed_at) snapshot. Re-probes append new rows
 * so we keep a temporal record of hosting/asn flips and TLS rotation.
 *
 * Source domains come from `vertex_yabai_entity WHERE entity_type='phishing_url'`
 * (entity_id like `url-*`). Local enrichment script
 * `60-apps/etzhayyim-project-yabai/tools/track-phishing-infra.mjs` populates it.
 *
 * Probe layers:
 *   passive — DNS (A/AAAA/NS/MX/CNAME), WHOIS (registrar/created), Team Cymru
 *             ASN/hosting, crt.sh CT log issuer/SAN
 *   active  — HTTP HEAD (Server / status / final URL), TLS s_client (CN/issuer/
 *             SAN/notAfter/version)
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_infra_track (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      entity_id          VARCHAR,
      domain             VARCHAR,
      probe_id           VARCHAR,
      probed_at          VARCHAR,
      probe_status       VARCHAR,
      dns_a              VARCHAR,
      dns_aaaa           VARCHAR,
      dns_cname          VARCHAR,
      dns_ns             VARCHAR,
      dns_mx             VARCHAR,
      resolved_ip        VARCHAR,
      asn                BIGINT,
      asn_org            VARCHAR,
      asn_country        VARCHAR,
      bgp_prefix         VARCHAR,
      hosting_provider   VARCHAR,
      registrar          VARCHAR,
      whois_created      VARCHAR,
      whois_updated      VARCHAR,
      whois_expires      VARCHAR,
      whois_raw_excerpt  VARCHAR,
      ct_issuer          VARCHAR,
      ct_san_count       BIGINT,
      ct_first_seen      VARCHAR,
      ct_last_seen       VARCHAR,
      tls_subject        VARCHAR,
      tls_issuer         VARCHAR,
      tls_san            VARCHAR,
      tls_not_before     VARCHAR,
      tls_not_after      VARCHAR,
      tls_version        VARCHAR,
      tls_cipher         VARCHAR,
      http_status        BIGINT,
      http_server        VARCHAR,
      http_final_url     VARCHAR,
      http_title         VARCHAR,
      http_powered_by    VARCHAR,
      probe_errors       VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_domain ON vertex_yabai_infra_track (domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_entity ON vertex_yabai_infra_track (entity_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_asn ON vertex_yabai_infra_track (asn)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_hosting ON vertex_yabai_infra_track (hosting_provider)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_registrar ON vertex_yabai_infra_track (registrar)`.execute(db);

  // Latest snapshot per domain — feeds dashboards / alerts
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yabai_infra_latest AS
    SELECT DISTINCT ON (domain)
      domain,
      entity_id,
      probed_at,
      resolved_ip,
      asn,
      asn_org,
      hosting_provider,
      registrar,
      whois_created,
      tls_issuer,
      tls_not_after,
      http_status,
      http_server,
      probe_status
    FROM vertex_yabai_infra_track
    WHERE domain IS NOT NULL
    ORDER BY domain, probed_at DESC
  `.execute(db);

  // Hosting provider concentration — which ASNs/registrars host the most phishing
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yabai_infra_hosting_rollup AS
    SELECT
      hosting_provider,
      asn,
      asn_country,
      COUNT(DISTINCT domain) AS domain_count,
      MIN(probed_at) AS first_seen,
      MAX(probed_at) AS last_seen
    FROM vertex_yabai_infra_track
    WHERE hosting_provider IS NOT NULL
    GROUP BY hosting_provider, asn, asn_country
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yabai_infra_hosting_rollup`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yabai_infra_latest`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_infra_track`.execute(db);
}
