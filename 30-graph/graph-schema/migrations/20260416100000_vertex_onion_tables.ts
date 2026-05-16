import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * 2026-04-16
 * onion.gftd.ai (0n10n001) — Dark Web Page Intelligence Platform
 * Three tables: vertex_onion_site, vertex_onion_page, vertex_onion_crawl
 * + edge_onion_hosted_on (page → site)
 * + edge_onion_links_to  (page → page, intra-site links)
 */
export async function up(db: Kysely<unknown>): Promise<void> {

  // -- vertex_onion_site -------------------------------------------------------
  // One row per .onion hidden service host.
  // site_did = did:web:onion.gftd.ai:{slug}
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_onion_site (
      vertex_id     VARCHAR PRIMARY KEY,
      onion_host    VARCHAR NOT NULL,
      node_id       VARCHAR,
      title         VARCHAR,
      category      VARCHAR,
      risk_score    INTEGER,
      reachable     BOOLEAN,
      page_count    INTEGER,
      first_seen    VARCHAR,
      last_seen     VARCHAR,
      site_did      VARCHAR,
      mirror_clearnet VARCHAR,
      threat_actor_ref VARCHAR,
      owner_did     VARCHAR,
      created_date  VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  // -- vertex_onion_page -------------------------------------------------------
  // One row per crawled .onion URL.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_onion_page (
      vertex_id         VARCHAR PRIMARY KEY,
      onion_url         VARCHAR NOT NULL,
      onion_host        VARCHAR NOT NULL,
      title             VARCHAR,
      content_hash      VARCHAR,
      content_blob_cid  VARCHAR,
      screenshot_blob_cid VARCHAR,
      status_code       INTEGER,
      language          VARCHAR,
      text_snippet      VARCHAR,
      outbound_links    VARCHAR,
      threat_indicators VARCHAR,
      risk_score        INTEGER,
      category          VARCHAR,
      crawled_at        VARCHAR,
      site_node_id      VARCHAR,
      owner_did         VARCHAR,
      created_date      VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  // -- vertex_onion_crawl ------------------------------------------------------
  // One row per crawl session (per host, per run).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_onion_crawl (
      vertex_id    VARCHAR PRIMARY KEY,
      onion_host   VARCHAR NOT NULL,
      session_id   VARCHAR,
      started_at   VARCHAR,
      finished_at  VARCHAR,
      page_count   INTEGER,
      error_count  INTEGER,
      reachable    BOOLEAN,
      error_msg    VARCHAR,
      owner_did    VARCHAR,
      created_date VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  // -- edge_onion_hosted_on ----------------------------------------------------
  // vertex_onion_page → vertex_onion_site
  await sql`
    CREATE TABLE IF NOT EXISTS edge_onion_hosted_on (
      edge_id      VARCHAR PRIMARY KEY,
      src_vid      VARCHAR NOT NULL,
      dst_vid      VARCHAR NOT NULL,
      owner_did    VARCHAR,
      created_date VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  // -- edge_onion_links_to -----------------------------------------------------
  // vertex_onion_page → vertex_onion_page (intra-site discovered links)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_onion_links_to (
      edge_id      VARCHAR PRIMARY KEY,
      src_vid      VARCHAR NOT NULL,
      dst_vid      VARCHAR NOT NULL,
      owner_did    VARCHAR,
      created_date VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    'edge_onion_links_to',
    'edge_onion_hosted_on',
    'vertex_onion_crawl',
    'vertex_onion_page',
    'vertex_onion_site',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
    await sql`FLUSH`.execute(db);
  }
}
