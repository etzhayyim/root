import type { Kysely } from 'kysely';
import { sql } from 'kysely';

/**
 * Migration 20260430160000: game chart analysis schema.
 *
 * Adds weekly chart snapshot persistence + LLM analysis topology:
 *   vertex_game_chart_snapshot  — per-source weekly rank row (idempotent PK)
 *   vertex_game_chart_analysis  — LLM-generated insights per week × source
 *   edge_game_charted_at        — vertex_game_title → chart_snapshot
 *   mv_game_rank_trend          — rolling rank aggregate per title × source
 *   mv_game_genre_chart_dominance — genre-level chart dominance (cardinality ≤ 90)
 *
 * Sources: steamspy_top2w (free, no auth), rawg_top (API key optional),
 *   steam_jp_topsellers (Steam featured API).
 *
 * Design: ADR-0036 (Worker-direct Hyperdrive), ADR-0056 (BPMN-as-actor).
 * cardinality notes: snapshot ≤ 60 rows/week; rank_trend ≤ 200 unique pairs;
 *   genre_dominance ≤ 90 rows → all MVs safe for streaming.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const v = (name: string, extra: string[]) => sql`CREATE TABLE IF NOT EXISTS ${sql.raw(name)} (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    ${sql.raw(extra.join(',\n    '))}
  )`.execute(db);

  const e = (name: string, extra: string[]) => sql`CREATE TABLE IF NOT EXISTS ${sql.raw(name)} (
    edge_id         VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    ${sql.raw(extra.join(',\n    '))}
  )`.execute(db);

  await v('vertex_game_chart_snapshot', [
    'title_did        VARCHAR',       // FK to vertex_game_title (NULL if not matched)
    'source           VARCHAR',       // steamspy_top2w | rawg_top | steam_jp_topsellers
    'week_start       DATE',          // Monday of the chart week (ISO)
    'rank             INTEGER',       // 1-based rank in source chart
    'rank_prev        INTEGER',       // previous week rank (NULL = new entry)
    'rank_delta       INTEGER',       // rank_prev - rank; positive = rising
    'external_id      VARCHAR',       // source-specific ID (Steam appid or RAWG ID)
    'title_hint       VARCHAR',       // game title as returned by source
    'score_source     DOUBLE PRECISION', // RAWG rating (0-5) or positive_pct
    'players_2w       BIGINT',        // SteamSpy: unique players in last 2 weeks
    'price_usd        DOUBLE PRECISION',
    'metadata_json    VARCHAR',       // {tags:[], reviews_total:N, genres:[]}
    'fetched_at       VARCHAR',       // ISO timestamp
    'actor_did        VARCHAR',
    'org_did          VARCHAR',
    'created_at       VARCHAR',
  ]);

  await v('vertex_game_chart_analysis', [
    'week_start           DATE',
    'source               VARCHAR',
    'analysis_ja          VARCHAR',   // ≤500 chars Japanese insight (social post body)
    'analysis_en          VARCHAR',
    'top_genre            VARCHAR',   // most frequent genre in top 10
    'rising_titles_json   VARCHAR',   // [{title_did,rank_delta,title_hint,rank}]
    'falling_titles_json  VARCHAR',
    'new_entries_json     VARCHAR',   // [{title_did,rank,title_hint}] first-appearance
    'insight_tags_json    VARCHAR',   // ["indie-surge","sequel-effect","seasonal"]
    'social_post_rkey     VARCHAR',   // AT rkey of published post (NULL until posted)
    'model_id             VARCHAR',
    'actor_did            VARCHAR',
    'org_did              VARCHAR',
    'created_at           VARCHAR',
  ]);

  await e('edge_game_charted_at', [
    'rank        INTEGER',
    'source      VARCHAR',
    'week_start  DATE',
    'created_at  VARCHAR',
  ]);

  // ── Indexes ───────────────────────────────────────────────────────────────

  await sql`CREATE INDEX IF NOT EXISTS idx_game_chart_snapshot_source_week
    ON vertex_game_chart_snapshot (source, week_start)`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_game_chart_snapshot_title
    ON vertex_game_chart_snapshot (title_did)
    WHERE title_did IS NOT NULL`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_game_chart_analysis_week
    ON vertex_game_chart_analysis (week_start, source)`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_charted_at_src
    ON edge_game_charted_at (src_vid)`.execute(db);

  // ── Materialized Views ────────────────────────────────────────────────────

  // Rolling rank aggregate per title × source — cardinality bounded by unique
  // game-source pairs observed in charts (typically ≤ 200, grows slowly).
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_rank_trend AS
    SELECT
      title_did,
      source,
      COUNT(*)                  AS weeks_charted,
      CAST(AVG(rank) AS DOUBLE PRECISION) AS avg_rank,
      MIN(rank)                 AS peak_rank,
      MAX(rank_delta)           AS best_rise,
      MIN(rank_delta)           AS worst_fall,
      MAX(week_start)           AS last_charted_week
    FROM vertex_game_chart_snapshot
    WHERE title_did IS NOT NULL
    GROUP BY title_did, source`.execute(db);

  // Genre-level chart dominance — cardinality: genres(~30) × sources(3) ≤ 90.
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_genre_chart_dominance AS
    SELECT
      g.dst_vid                 AS genre_did,
      s.source,
      COUNT(DISTINCT s.title_did) AS titles_in_chart,
      CAST(AVG(s.rank) AS DOUBLE PRECISION) AS avg_rank,
      MIN(s.rank)               AS top_rank,
      MAX(s.week_start)         AS last_seen_week
    FROM vertex_game_chart_snapshot s
    JOIN edge_game_has_genre g ON g.src_vid = s.title_did
    WHERE s.title_did IS NOT NULL AND s.rank <= 20
    GROUP BY g.dst_vid, s.source`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_game_genre_chart_dominance`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_game_rank_trend`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_game_charted_at`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_game_chart_analysis`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_game_chart_snapshot`.execute(db);
}
