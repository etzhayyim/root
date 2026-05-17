CREATE TABLE IF NOT EXISTS vertex_webya_client (
      vertex_id        VARCHAR PRIMARY KEY,
      client_id        VARCHAR NOT NULL,
      client_name      VARCHAR NOT NULL,
      profession_kind  VARCHAR NOT NULL,
      contact_email    VARCHAR,
      contact_phone    VARCHAR,
      org_did          VARCHAR,
      created_at       VARCHAR NOT NULL
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_webya_site (
      vertex_id              VARCHAR PRIMARY KEY,
      site_id                VARCHAR NOT NULL,
      client_id              VARCHAR NOT NULL,
      template_id            VARCHAR NOT NULL,
      site_name              VARCHAR NOT NULL,
      custom_domain          VARCHAR,
      subdomain              VARCHAR NOT NULL,
      cf_custom_hostname_id  VARCHAR,
      ssl_status             VARCHAR NOT NULL DEFAULT 'none',
      "status"               VARCHAR NOT NULL DEFAULT 'draft',
      published_at           VARCHAR,
      created_at             VARCHAR NOT NULL
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_webya_template (
      vertex_id        VARCHAR PRIMARY KEY,
      template_id      VARCHAR NOT NULL,
      profession_kind  VARCHAR NOT NULL,
      pages_json       VARCHAR NOT NULL,
      html_skeleton    VARCHAR NOT NULL,
      slot_schema_json VARCHAR NOT NULL,
      "version"        INT NOT NULL DEFAULT 1,
      active           BOOLEAN NOT NULL DEFAULT TRUE,
      created_at       VARCHAR NOT NULL
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_webya_page (
      vertex_id        VARCHAR PRIMARY KEY,
      page_id          VARCHAR NOT NULL,
      site_id          VARCHAR NOT NULL,
      slug             VARCHAR NOT NULL,
      title            VARCHAR NOT NULL,
      meta_description VARCHAR,
      slots_json       VARCHAR,
      html_content     VARCHAR,
      json_ld          VARCHAR,
      "status"         VARCHAR NOT NULL DEFAULT 'draft',
      updated_at       VARCHAR NOT NULL
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_webya_legal_disclosure (
      vertex_id         VARCHAR PRIMARY KEY,
      disclosure_id     VARCHAR NOT NULL,
      site_id           VARCHAR NOT NULL,
      profession_kind   VARCHAR NOT NULL,
      disclosure_type   VARCHAR NOT NULL,
      disclosure_value  VARCHAR NOT NULL,
      verified_at       VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_webya_domain (
      vertex_id              VARCHAR PRIMARY KEY,
      domain_id              VARCHAR NOT NULL,
      site_id                VARCHAR NOT NULL,
      domain                 VARCHAR NOT NULL,
      cf_hostname_id         VARCHAR,
      ssl_status             VARCHAR NOT NULL DEFAULT 'pending',
      ownership_verified     BOOLEAN NOT NULL DEFAULT FALSE,
      dns_cname_target       VARCHAR NOT NULL DEFAULT 'proxy.webya.etzhayyim.com',
      verification_txt_name  VARCHAR,
      verification_txt_value VARCHAR,
      provisioned_at         VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_webya_generation_job (
      vertex_id         VARCHAR PRIMARY KEY,
      job_id            VARCHAR NOT NULL,
      site_id           VARCHAR NOT NULL,
      langgraph_run_id  VARCHAR,
      "status"          VARCHAR NOT NULL DEFAULT 'pending',
      llm_calls_count   INT NOT NULL DEFAULT 0,
      revision_count    INT NOT NULL DEFAULT 0,
      started_at        VARCHAR NOT NULL,
      completed_at      VARCHAR,
      error_message     VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_webya_client_site (
      vertex_id  VARCHAR PRIMARY KEY,
      src        VARCHAR NOT NULL,
      dst        VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL
    );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_webya_site_page (
      vertex_id  VARCHAR PRIMARY KEY,
      src        VARCHAR NOT NULL,
      dst        VARCHAR NOT NULL,
      slug       VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL
    );

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_webya_sites_by_status AS
    SELECT
      status,
      COUNT(*) AS site_count
    FROM vertex_webya_site
    GROUP BY status;

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_webya_domain_ssl_pending AS
    SELECT
      d.vertex_id,
      d.site_id,
      d.domain,
      d.ssl_status,
      d.ownership_verified,
      d.dns_cname_target,
      d.verification_txt_name,
      d.verification_txt_value,
      d.provisioned_at
    FROM vertex_webya_domain d
    WHERE d.ssl_status <> 'active';

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_webya_generation_queue AS
    SELECT
      j.vertex_id,
      j.job_id,
      j.site_id,
      j.status,
      j.langgraph_run_id,
      j.llm_calls_count,
      j.started_at
    FROM vertex_webya_generation_job j
    WHERE j.status IN ('pending', 'running');

FLUSH;
