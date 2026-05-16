import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A

/**
 * Common Crawl page DID alias layer (2026-04-14, v2 VIEW-only).
 *
 * Problem:
 *   cc-phase3 rkey format changed from SHA-16 hex to URL-path slug:
 *     legacy:   rkey = "a3b4c5d6e7f89012"           (SHA-8 hex × 2)
 *               owner_did = NULL
 *     new:      rkey = "example-com:foo:bar"        (domain-slug:path-segments)
 *               owner_did = "did:web:site.gftd.ai:example-com:foo:bar"
 *
 *   Both forms point to the same page (same URL). We preserve legacy rows
 *   untouched and alias them to the new canonical DID via a lightweight
 *   `vertex_did_alias` table + non-materialized VIEWs.
 *
 * DESIGN (revised 2026-04-14 after first-attempt OOM)
 * ---------------------------------------------------
 * The original v1 of this migration created MATERIALIZED VIEWs with
 * `GROUP BY url` + 14 × `MAX(varchar)` over 2.9M `vertex_page` rows.
 * During backfill the streaming operator held ~5 GiB of aggregation state
 * in memory and OOMKilled the 6.5 GiB compute pod. Root cause: high-
 * cardinality GROUP BY with wide VARCHAR aggregates is a known MV
 * anti-pattern on memory-constrained RisingWave clusters.
 *
 * v2 replaces the MVs with plain VIEWs (query-time computation, zero
 * memory footprint). Read latency is higher but the cluster is safe.
 * A narrow streaming MV can be added later only if a hot read path
 * demands it (e.g. filter by `WHERE rkey LIKE '%:%'` to restrict backfill
 * to the new-format rows, which starts at 0 and grows incrementally).
 *
 * See `90-docs/260414-risingwave-mv-memory-safety.md` for the MV design
 * guardrails derived from this incident.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_did_alias: generic DID alias mapping ────────────────────────
  //
  // Used for any DID rename / schema-migration scenario. CC page pairs are
  // the initial tenant. `alias_kind` distinguishes alias reasons:
  //   "cc-sha-to-url-slug"  — CC rkey format migration (this migration)
  //   "did-web-rename"      — future: did:web domain moved
  //   "did-plc-rotation"    — future: PLC key rotation alias
  await sql`CREATE TABLE IF NOT EXISTS vertex_did_alias (
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
  )`.execute(db);

  // ── view_cc_page_canonical: non-materialized per-URL dedup view ────────
  //
  // Groups vertex_page rows by URL at query time. Picks canonical_rkey /
  // canonical_did:
  //   - New-format rkey contains ':' (URL-slug). Legacy SHA-hex never does.
  //   - MAX(CASE WHEN rkey LIKE '%:%' ...) picks new-format if any.
  //   - MAX(CASE WHEN rkey NOT LIKE '%:%' ...) preserves legacy.
  //
  // VIEW not MV → zero memory / CPU footprint when idle. Query-time cost
  // is O(vertex_page scan) which Hyperdrive + RW executor handle fine
  // for bounded reads (domain-scoped, URL-scoped). DO NOT add
  // `SELECT * FROM view_cc_page_canonical` without a filter in hot paths.
  //
  // Read pattern (safe):
  //   SELECT canonical_did FROM view_cc_page_canonical
  //   WHERE url = 'https://example.com/foo/bar';
  //
  //   SELECT * FROM view_cc_page_canonical
  //   WHERE domain = 'example.com' LIMIT 100;
  await sql`CREATE VIEW view_cc_page_canonical AS
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
    GROUP BY url`.execute(db);

  // ── view_cc_edge_links_to_canonical: edge rewrite via alias ────────────
  //
  // Legacy edges reference SHA-rkey endpoints. After alias backfill, reads
  // see URL-slug endpoints transparently. LEFT JOIN vertex_did_alias
  // resolves SHA → slug; rows without an alias entry pass through
  // unchanged (legacy-only edges).
  //
  // Same VIEW-not-MV rationale as view_cc_page_canonical. Use with
  // filters (e.g. WHERE src_vid = '...') for bounded reads.
  await sql`CREATE VIEW view_cc_edge_links_to_canonical AS
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
      ON a2.legacy_rkey = e.dst_vid AND a2.alias_kind = 'cc-sha-to-url-slug'`.execute(db);

  // ── view_cc_domain_page_count_canonical: dedup page count per domain ───
  //
  // Counts URLs once regardless of legacy/new coexistence. Reads through
  // view_cc_page_canonical so the dedup logic is defined in exactly one
  // place.
  await sql`CREATE VIEW view_cc_domain_page_count_canonical AS
    SELECT
      domain,
      COUNT(*) AS page_count,
      SUM(CASE WHEN has_canonical THEN 1 ELSE 0 END) AS canonical_count,
      SUM(CASE WHEN has_legacy AND NOT has_canonical THEN 1 ELSE 0 END) AS legacy_only_count
    FROM view_cc_page_canonical
    WHERE domain IS NOT NULL
    GROUP BY domain`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_cc_domain_page_count_canonical`.execute(db);
  await sql`DROP VIEW IF EXISTS view_cc_edge_links_to_canonical`.execute(db);
  await sql`DROP VIEW IF EXISTS view_cc_page_canonical`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_did_alias`.execute(db);
}
