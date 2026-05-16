import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * vertex_houbun_* — houbun.gftd.ai law corpus (ADR-0052).
 *
 * Four vertex tables + two edge tables:
 *   vertex_houbun_statute         — statute / regulation / treaty metadata
 *   vertex_houbun_article         — article body (quantum of citation)
 *   vertex_houbun_amendmentEvent  — amendment lineage
 *   vertex_houbun_treaty          — international treaty metadata
 *   edge_houbun_statute_article   — statute → article (ordered by article_no)
 *   edge_houbun_amends            — amendmentEvent → article (op in insert/modify/delete/repeal)
 *
 * Article DID is content-addressed via blake3_prefix12 so amendments
 * produce a new DID; lineage is preserved by edge_houbun_amends rather
 * than mutation on the original row.
 *
 * Write path: Hyperdrive direct (ADR-0036) from the pymagatama UDF pool
 * handler `20-actors/magatama/py/src/pymagatama/handlers/houbun.py`.
 *
 * Related:
 *   ADR-0052 houbun actor topology (this table set)
 *   ADR-0049 Python UDF shared pool runtime
 *   ADR-0036 Worker-direct Hyperdrive persistence
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_houbun_statute ────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_houbun_statute (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      jurisdiction VARCHAR,
      statute_id VARCHAR,
      title VARCHAR,
      title_native VARCHAR,
      statute_type VARCHAR,
      enacted_date VARCHAR,
      effective_date VARCHAR,
      repealed_date VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      license VARCHAR,
      language VARCHAR,
      article_count BIGINT,
      last_verified VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_statute_jurisdiction
      ON vertex_houbun_statute (jurisdiction)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_statute_statute_id
      ON vertex_houbun_statute (jurisdiction, statute_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_statute_source
      ON vertex_houbun_statute (source)
  `.execute(db);

  // ── vertex_houbun_article ────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_houbun_article (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      statute_ref VARCHAR,
      article_no VARCHAR,
      section VARCHAR,
      title VARCHAR,
      text VARCHAR,
      language VARCHAR,
      article_did VARCHAR,
      blake3_hash VARCHAR,
      amended_at VARCHAR,
      source_url VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Primary navigation: list articles of a statute ordered by article_no.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_article_statute_ref
      ON vertex_houbun_article (statute_ref)
  `.execute(db);

  // Content-addressed lookup by DID suffix for citation resolution.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_article_did
      ON vertex_houbun_article (article_did)
  `.execute(db);

  // ── vertex_houbun_amendmentEvent ─────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_houbun_amendmentEvent (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      statute_ref VARCHAR,
      article_ref VARCHAR,
      supersedes_article_did VARCHAR,
      op VARCHAR,
      amending_statute_ref VARCHAR,
      effective_date VARCHAR,
      diff_uri VARCHAR,
      note VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_amendment_statute_ref
      ON vertex_houbun_amendmentEvent (statute_ref)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_amendment_supersedes
      ON vertex_houbun_amendmentEvent (supersedes_article_did)
  `.execute(db);

  // ── vertex_houbun_treaty ─────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_houbun_treaty (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      title VARCHAR,
      title_native VARCHAR,
      parties_json VARCHAR,
      signed_date VARCHAR,
      entered_into_force_date VARCHAR,
      un_reg_no VARCHAR,
      depositary VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      source_url VARCHAR,
      language VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_houbun_treaty_source_record_id
      ON vertex_houbun_treaty (source, source_record_id)
  `.execute(db);

  // ── edge_houbun_statute_article ──────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_houbun_statute_article (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      article_no VARCHAR,
      order_key BIGINT,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_houbun_statute_article_src
      ON edge_houbun_statute_article (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_houbun_statute_article_dst
      ON edge_houbun_statute_article (dst_vid)
  `.execute(db);

  // ── edge_houbun_amends ───────────────────────────────────────────────
  // src_vid = amendmentEvent vertex, dst_vid = target article vertex.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_houbun_amends (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      op VARCHAR,
      effective_date VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_houbun_amends_src
      ON edge_houbun_amends (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_houbun_amends_dst
      ON edge_houbun_amends (dst_vid)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_houbun_amends_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_houbun_amends_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_houbun_amends`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_edge_houbun_statute_article_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_houbun_statute_article_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_houbun_statute_article`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_houbun_treaty_source_record_id`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_houbun_treaty`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_houbun_amendment_supersedes`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_houbun_amendment_statute_ref`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_houbun_amendmentEvent`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_houbun_article_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_houbun_article_statute_ref`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_houbun_article`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_houbun_statute_source`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_houbun_statute_statute_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_houbun_statute_jurisdiction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_houbun_statute`.execute(db);
}
