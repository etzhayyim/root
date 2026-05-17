import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B  (curated lifehack tips + product
// recommendations + post log; no Tier-3 PII).

/**
 * lifehack.etzhayyim.com Phase 1 — household life-hack actor (dust prevention,
 * humidity, cable management, storage, cleaning).
 *
 * Pattern: T2 BPMN-as-actor (ADR-0036 Worker-direct Hyperdrive +
 * ADR-0056 BPMN-as-actor + ADR-2604282300 pymagatama + Zeebe, no CF
 * Worker). Mirrors shosha (2026-05-06) bring-up.
 *
 * Boundary (2026-05-08):
 *   - lifehack holds tip text / effectiveness / recommendation +
 *     social posts.
 *   - Manufacturing / CAD / DIY assembly belong to tsukuru.etzhayyim.com +
 *     cad.etzhayyim.com.  vertex_lifehack_product reserves cross-reference
 *     fields (tsukuru_cad_model_did, tsukuru_factory_did,
 *     tsukuru_production_order_nsid) so a tip can later point at a
 *     buildable design without lifehack writing tsukuru tables.
 *
 * Tables (6 vertex + 3 edge):
 *   vertex_lifehack_topic               topic categories (e.g. "dust-on-desk")
 *   vertex_lifehack_tip                 individual countermeasure tip
 *   vertex_lifehack_product             recommended product (commercial or
 *                                        diy_tsukuru cross-ref)
 *   vertex_lifehack_environment_reading user-submitted humidity / temp /
 *                                        PM2.5 readings (static-electricity
 *                                        risk detection)
 *   vertex_lifehack_post_log            posted bsky URI per tip (dedup)
 *   vertex_lifehack_user_query          agentLoop query audit
 *   edge_lifehack_tip_solves_topic      tip → topic
 *   edge_lifehack_tip_recommends_product  tip → product
 *   edge_lifehack_topic_relates_to      topic ↔ topic
 *
 * Streaming MVs (4):
 *   mv_lifehack_top_tips_by_topic        per-topic effectiveness DESC
 *   mv_lifehack_recently_posted          last 30d posted tips (dedup gate)
 *   mv_lifehack_static_risk_now          humidity<40% reading aggregator
 *   mv_lifehack_trending_topic           query+post engagement weight
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lifehack_topic (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      topic_id varchar NOT NULL,
      category varchar NOT NULL,
      title_ja varchar,
      title_en varchar,
      summary_ja varchar,
      summary_en varchar,
      parent_topic_id varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lifehack_tip (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      tip_id varchar NOT NULL,
      topic_id varchar NOT NULL,
      body_ja varchar,
      body_en varchar,
      effectiveness_score double precision,
      cost_jpy_min double precision,
      cost_jpy_max double precision,
      difficulty varchar,
      source_url varchar,
      source_authority varchar,
      evidence_summary varchar,
      llm_model varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lifehack_product (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      product_id varchar NOT NULL,
      name varchar NOT NULL,
      brand varchar,
      category varchar NOT NULL,
      source_type varchar NOT NULL,
      price_jpy_min double precision,
      price_jpy_max double precision,
      amazon_search_keyword varchar,
      asin varchar,
      pse_certified boolean,
      tsukuru_cad_model_did varchar,
      tsukuru_factory_did varchar,
      tsukuru_production_order_nsid varchar,
      estimated_make_cost_jpy double precision,
      estimated_make_time_hours double precision,
      notes_ja varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lifehack_environment_reading (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      reading_id varchar NOT NULL,
      reporter_did varchar,
      location_h3 varchar,
      humidity_pct double precision,
      temp_c double precision,
      pm25_ugm3 double precision,
      ts_ms bigint NOT NULL,
      source varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lifehack_post_log (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      post_id varchar NOT NULL,
      tip_id varchar NOT NULL,
      topic_id varchar NOT NULL,
      bsky_uri varchar,
      bsky_cid varchar,
      posted_at_ms bigint NOT NULL,
      engagement_score double precision,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lifehack_user_query (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      query_id varchar NOT NULL,
      asker_did varchar,
      query_text varchar,
      answered_tip_ids varchar,
      llm_model varchar,
      latency_ms int,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_lifehack_tip_solves_topic (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_lifehack_tip_recommends_product (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_lifehack_topic_relates_to (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Streaming MVs ──────────────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_top_tips_by_topic AS
      SELECT
        t.topic_id,
        t.tip_id,
        t.body_ja,
        t.effectiveness_score,
        t.cost_jpy_min,
        t.difficulty,
        t.source_authority
      FROM vertex_lifehack_tip t
      WHERE t.status = 'active'
        AND t.effectiveness_score IS NOT NULL;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_recently_posted AS
      SELECT
        tip_id,
        topic_id,
        MAX(posted_at_ms) AS last_posted_at_ms,
        COUNT(*) AS post_count
      FROM vertex_lifehack_post_log
      WHERE status = 'active'
      GROUP BY tip_id, topic_id;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_static_risk_now AS
      SELECT
        location_h3,
        COUNT(*) AS reading_count,
        AVG(humidity_pct) AS avg_humidity_pct,
        MIN(humidity_pct) AS min_humidity_pct,
        MAX(ts_ms) AS last_ts_ms
      FROM vertex_lifehack_environment_reading
      WHERE status = 'active'
        AND humidity_pct IS NOT NULL
        AND humidity_pct < 40.0
      GROUP BY location_h3;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lifehack_trending_topic AS
      SELECT
        topic_id,
        COUNT(*) AS post_count,
        SUM(COALESCE(engagement_score, 0)) AS engagement_total,
        MAX(posted_at_ms) AS last_posted_at_ms
      FROM vertex_lifehack_post_log
      WHERE status = 'active'
      GROUP BY topic_id;
  `.execute(db);

  // ── Grants ─────────────────────────────────────────────────────────
  for (const tbl of [
    "vertex_lifehack_topic",
    "vertex_lifehack_tip",
    "vertex_lifehack_product",
    "vertex_lifehack_environment_reading",
    "vertex_lifehack_post_log",
    "vertex_lifehack_user_query",
    "edge_lifehack_tip_solves_topic",
    "edge_lifehack_tip_recommends_product",
    "edge_lifehack_topic_relates_to",
  ]) {
    await sql`GRANT SELECT, INSERT, UPDATE ON ${sql.raw(tbl)} TO root`.execute(db);
    await sql`GRANT SELECT, INSERT, UPDATE ON ${sql.raw(tbl)} TO kaisya_app`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_trending_topic`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_static_risk_now`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_recently_posted`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lifehack_top_tips_by_topic`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_lifehack_topic_relates_to`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_lifehack_tip_recommends_product`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_lifehack_tip_solves_topic`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lifehack_user_query`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lifehack_post_log`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lifehack_environment_reading`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lifehack_product`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lifehack_tip`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lifehack_topic`.execute(db);
}
