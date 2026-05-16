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
    );

CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_domain ON vertex_yabai_infra_track (domain);

CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_entity ON vertex_yabai_infra_track (entity_id);

CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_asn ON vertex_yabai_infra_track (asn);

CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_hosting ON vertex_yabai_infra_track (hosting_provider);

CREATE INDEX IF NOT EXISTS idx_yabai_infra_track_registrar ON vertex_yabai_infra_track (registrar);

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
    ORDER BY domain, probed_at DESC;

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
    GROUP BY hosting_provider, asn, asn_country;
