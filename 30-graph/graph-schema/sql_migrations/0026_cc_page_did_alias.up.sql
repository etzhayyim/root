CREATE TABLE IF NOT EXISTS vertex_did_alias (
    vertex_id         VARCHAR NOT NULL PRIMARY KEY,  -- canonical_did
    canonical_did     VARCHAR NOT NULL,
    canonical_rkey    VARCHAR NOT NULL,
    canonical_collection VARCHAR,
    legacy_did        VARCHAR,
    legacy_rkey       VARCHAR,
    legacy_collection VARCHAR,
    alias_kind        VARCHAR NOT NULL,
    url               VARCHAR,
    domain            VARCHAR,
    first_seen_at     TIMESTAMP,
    _seq              BIGINT DEFAULT 0,
    sensitivity_ord   BIGINT DEFAULT 0,
    created_date      DATE,
    owner_did         VARCHAR
  );

CREATE VIEW view_cc_page_canonical AS
    SELECT
      url,
      MAX(domain) AS domain,
      MAX(CASE WHEN rkey LIKE '%:%' THEN rkey END) AS canonical_rkey,
      MAX(CASE WHEN rkey LIKE '%:%' THEN owner_did END) AS canonical_did,
      MAX(CASE WHEN rkey NOT LIKE '%:%' THEN rkey END) AS legacy_rkey,
      MAX(title) AS title,
      MAX(description) AS description,
      MAX(language) AS language,
      MAX(content_type) AS content_type,
      MAX(status_code) AS status_code,
      MAX(outlink_count) AS outlink_count,
      MAX(crawl) AS crawl,
      MAX(content_hash) AS content_hash,
      MAX(crawled_at) AS crawled_at,
      COUNT(*) AS row_count,
      BOOL_OR(rkey LIKE '%:%') AS has_canonical,
      BOOL_OR(rkey NOT LIKE '%:%' AND rkey ~ '^[a-f0-9]{16}$') AS has_legacy
    FROM vertex_page
    WHERE url IS NOT NULL AND url != ''
    GROUP BY url;

CREATE VIEW view_cc_edge_links_to_canonical AS
    SELECT
      COALESCE(a1.canonical_rkey, e.src_vid) AS src_vid,
      COALESCE(a2.canonical_rkey, e.dst_vid) AS dst_vid,
      e.src_vid AS original_src_vid,
      e.dst_vid AS original_dst_vid,
      e.label,
      e.anchor_text,
      e.edge_id,
      COALESCE(a1.canonical_did, e.owner_did) AS owner_did,
      e._seq,
      e.created_date,
      e.sensitivity_ord
    FROM edge_links_to e
    LEFT JOIN vertex_did_alias a1
      ON a1.legacy_rkey = e.src_vid AND a1.alias_kind = 'cc-sha-to-url-slug'
    LEFT JOIN vertex_did_alias a2
      ON a2.legacy_rkey = e.dst_vid AND a2.alias_kind = 'cc-sha-to-url-slug';

CREATE VIEW view_cc_domain_page_count_canonical AS
    SELECT
      domain,
      COUNT(*) AS page_count,
      SUM(CASE WHEN has_canonical THEN 1 ELSE 0 END) AS canonical_count,
      SUM(CASE WHEN has_legacy AND NOT has_canonical THEN 1 ELSE 0 END) AS legacy_only_count
    FROM view_cc_page_canonical
    WHERE domain IS NOT NULL
    GROUP BY domain;
