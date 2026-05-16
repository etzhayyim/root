import { Kysely, sql } from 'kysely';

/**
 * Migration 0047: media_gamers domain depth — 14 vertex + 12 edge + 6 MV (2026-04-14).
 *
 * Design: 90-docs/260414-domain-coverage-depth-design.md §C
 *
 * Expands 900K title count into platform / engine / store / character / map /
 * item / quest / dlc / sales / esports / genre / mode. developer/publisher/store
 * participation is modeled as edges to vertex_legal_entity.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Vertex tables (14) ─────────────────────────────────────────────────

  const v = (name: string, extra: string[]) => sql`CREATE TABLE IF NOT EXISTS ${sql.raw(name)} (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    ${sql.raw(extra.join(',\n    '))}
  )`.execute(db);

  await v('vertex_game_title', [
    'external_ids   VARCHAR',     // igdb:N,steam:N,wikidata:QID
    'title_en       VARCHAR',
    'title_ja       VARCHAR',
    'release_year   INT',
    'first_release_date DATE',
    'franchise_did  VARCHAR',
    'engine_did     VARCHAR',
    'developer_did  VARCHAR',
    'publisher_did  VARCHAR',
    'genre_did      VARCHAR',
    'mode_did       VARCHAR',
    'rating_esrb    VARCHAR',
    'rating_cero    VARCHAR',
  ]);

  await v('vertex_game_franchise', ['name VARCHAR', 'wikidata_qid VARCHAR', 'first_year INT', 'title_count INT']);
  await v('vertex_game_platform', ['name VARCHAR', 'kind VARCHAR', 'maker_did VARCHAR', 'launch_year INT', 'wikidata_qid VARCHAR']);
  await v('vertex_game_engine', ['name VARCHAR', 'version VARCHAR', 'maker_did VARCHAR', 'license VARCHAR', 'wikidata_qid VARCHAR']);
  await v('vertex_game_store', ['name VARCHAR', 'operator_did VARCHAR', 'country_restrictions VARCHAR', 'wikidata_qid VARCHAR']);
  await v('vertex_game_character', [
    'title_did       VARCHAR',
    'name            VARCHAR',
    'name_ja         VARCHAR',
    'character_role  VARCHAR',     // protagonist, antagonist, companion, npc
    'class           VARCHAR',
    'first_appearance_title_did VARCHAR',
    'voice_actor_did VARCHAR',
  ]);
  await v('vertex_game_map', [
    'title_did       VARCHAR',
    'name            VARCHAR',
    'kind            VARCHAR',     // region, dungeon, city, arena
    'parent_map_did  VARCHAR',
    'coord_system    VARCHAR',
  ]);
  await v('vertex_game_item', [
    'title_did       VARCHAR',
    'name            VARCHAR',
    'kind            VARCHAR',     // weapon, armor, consumable, key, cosmetic
    'rarity          VARCHAR',
    'tradeable       BOOLEAN',
    'msrp_usd        DOUBLE PRECISION',
  ]);
  await v('vertex_game_quest', [
    'title_did       VARCHAR',
    'name            VARCHAR',
    'kind            VARCHAR',     // main, side, daily, event
    'act             VARCHAR',
    'prereq_quest_did VARCHAR',
  ]);
  await v('vertex_game_dlc', [
    'title_did       VARCHAR',
    'name            VARCHAR',
    'kind            VARCHAR',     // expansion, cosmetic, season_pass
    'release_date    DATE',
    'msrp_usd        DOUBLE PRECISION',
  ]);
  await v('vertex_game_sales_monthly', [
    'title_did       VARCHAR',
    'region          VARCHAR',     // NA, EU, JP, CN, ROW
    'year            INT',
    'month           INT',
    'units_sold      BIGINT',
    'revenue_usd     DOUBLE PRECISION',
    'source          VARCHAR',
  ]);
  await v('vertex_game_esports_event', [
    'name            VARCHAR',
    'title_did       VARCHAR',
    'year            INT',
    'country         VARCHAR',
    'prize_pool_usd  DOUBLE PRECISION',
    'organizer_did   VARCHAR',
  ]);
  await v('vertex_game_genre', ['name VARCHAR', 'parent_genre_did VARCHAR', 'iso_slot VARCHAR']);
  await v('vertex_game_mode', ['name VARCHAR', 'kind VARCHAR']); // single, coop, pvp, mmo

  // ── Edge tables (12) ───────────────────────────────────────────────────

  const e = (name: string, extra: string[] = []) => sql`CREATE TABLE IF NOT EXISTS ${sql.raw(name)} (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR${sql.raw(extra.length ? ',' : '')}
    ${sql.raw(extra.join(',\n    '))}
  )`.execute(db);

  await e('edge_game_developed_by', ['developer_role VARCHAR']);
  await e('edge_game_published_by', ['region VARCHAR']);
  await e('edge_game_runs_on', ['launch_year INT']);
  await e('edge_game_uses_engine', ['engine_version VARCHAR']);
  await e('edge_game_sold_on', ['price_usd DOUBLE PRECISION', 'available_from DATE', 'available_to DATE']);
  await e('edge_game_has_character');
  await e('edge_game_has_map');
  await e('edge_game_has_item');
  await e('edge_game_has_quest');
  await e('edge_game_part_of_franchise');
  await e('edge_game_has_genre', ['is_primary BOOLEAN']);
  await e('edge_game_esports_for');

  // ── Streaming MVs (6) ──────────────────────────────────────────────────

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_platform_share AS
    SELECT p.vertex_id AS platform_did,
           p.name       AS platform_name,
           COUNT(DISTINCT ro.src_vid) AS title_count
    FROM vertex_game_platform p
    LEFT JOIN edge_game_runs_on ro ON ro.dst_vid = p.vertex_id
    GROUP BY p.vertex_id, p.name`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_engine_usage AS
    SELECT e.vertex_id AS engine_did,
           e.name       AS engine_name,
           COUNT(DISTINCT ue.src_vid) AS title_count
    FROM vertex_game_engine e
    LEFT JOIN edge_game_uses_engine ue ON ue.dst_vid = e.vertex_id
    GROUP BY e.vertex_id, e.name`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_sales_by_region AS
    SELECT region, year,
           SUM(units_sold)::BIGINT AS units_year,
           SUM(revenue_usd)         AS revenue_year,
           COUNT(DISTINCT title_did) AS title_count
    FROM vertex_game_sales_monthly
    GROUP BY region, year`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_character_depth AS
    SELECT title_did, COUNT(*)::BIGINT AS character_count
    FROM vertex_game_character
    GROUP BY title_did`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_franchise_lifecycle AS
    SELECT f.vertex_id AS franchise_did,
           f.name       AS franchise_name,
           COUNT(DISTINCT t.vertex_id) AS title_count,
           MIN(t.release_year) AS first_year,
           MAX(t.release_year) AS last_year
    FROM vertex_game_franchise f
    LEFT JOIN vertex_game_title t ON t.franchise_did = f.vertex_id
    GROUP BY f.vertex_id, f.name`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_game_esports_per_genre AS
    SELECT g.vertex_id AS genre_did,
           g.name       AS genre_name,
           COUNT(DISTINCT ev.vertex_id) AS esports_event_count,
           SUM(ev.prize_pool_usd)        AS total_prize_pool_usd
    FROM vertex_game_genre g
    LEFT JOIN edge_game_has_genre hg ON hg.dst_vid = g.vertex_id
    LEFT JOIN vertex_game_esports_event ev ON ev.title_did = hg.src_vid
    GROUP BY g.vertex_id, g.name`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    'mv_game_esports_per_genre',
    'mv_game_franchise_lifecycle',
    'mv_game_character_depth',
    'mv_game_sales_by_region',
    'mv_game_engine_usage',
    'mv_game_platform_share',
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const t of [
    'edge_game_esports_for', 'edge_game_has_genre', 'edge_game_part_of_franchise',
    'edge_game_has_quest', 'edge_game_has_item', 'edge_game_has_map',
    'edge_game_has_character', 'edge_game_sold_on', 'edge_game_uses_engine',
    'edge_game_runs_on', 'edge_game_published_by', 'edge_game_developed_by',
    'vertex_game_mode', 'vertex_game_genre', 'vertex_game_esports_event',
    'vertex_game_sales_monthly', 'vertex_game_dlc', 'vertex_game_quest',
    'vertex_game_item', 'vertex_game_map', 'vertex_game_character',
    'vertex_game_store', 'vertex_game_engine', 'vertex_game_platform',
    'vertex_game_franchise', 'vertex_game_title',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
