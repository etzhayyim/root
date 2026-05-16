import { Kysely, sql } from 'kysely';

/**
 * Migration 0046: media_anime domain depth — 13 vertex + 11 edge + 5 MV (2026-04-14).
 *
 * Design: 90-docs/260414-domain-coverage-depth-design.md §B
 *
 * Expands 25K title count into studio / committee / character / staff / episode /
 * broadcaster / distribution / source / song / merchandise / franchise network.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Vertex tables (13) ─────────────────────────────────────────────────

  const v = (name: string, extra: string[]) => sql`CREATE TABLE IF NOT EXISTS ${sql.raw(name)} (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,
    ${sql.raw(extra.join(',\n    '))}
  )`.execute(db);

  // title already exists as vertex_repo_record collection; add a typed projection
  await v('vertex_anime_title', [
    'external_ids    VARCHAR',     // comma-separated mal:N,anilist:N,kitsu:N
    'title_en        VARCHAR',
    'title_ja        VARCHAR',
    'type            VARCHAR',     // TV, OVA, Movie, Special, Music
    'episodes        INT',
    'status          VARCHAR',     // FINISHED, ONGOING
    'season          VARCHAR',
    'year            INT',
    'studio_did      VARCHAR',     // primary studio
    'committee_did   VARCHAR',
    'franchise_did   VARCHAR',
    'source_did      VARCHAR',     // source adaptation
    'picture_url     VARCHAR',
  ]);
  await v('vertex_anime_franchise', ['name VARCHAR', 'wikidata_qid VARCHAR', 'first_year INT', 'last_year INT', 'work_count INT']);
  await v('vertex_anime_studio', ['name VARCHAR', 'country VARCHAR', 'wikidata_qid VARCHAR', 'legal_entity_did VARCHAR', 'founded_year INT']);
  await v('vertex_anime_committee', [
    'title_did       VARCHAR',
    'year            INT',
    'member_count    INT',
  ]);
  await v('vertex_anime_staff', [
    'name            VARCHAR',
    'name_ja         VARCHAR',
    'staff_role      VARCHAR',     // director, voice_actor, animator, composer
    'wikidata_qid    VARCHAR',
    'country         VARCHAR',
    'legal_entity_did VARCHAR',
  ]);
  await v('vertex_anime_character', [
    'title_did       VARCHAR',
    'name            VARCHAR',
    'name_ja         VARCHAR',
    'character_role  VARCHAR',     // protagonist, supporting, antagonist
    'gender          VARCHAR',
    'voice_actor_did VARCHAR',
  ]);
  await v('vertex_anime_episode', [
    'title_did       VARCHAR',
    'episode_number  INT',
    'title_en        VARCHAR',
    'title_ja        VARCHAR',
    'aired_date      DATE',
    'duration_sec    INT',
  ]);
  await v('vertex_anime_broadcaster', [
    'name            VARCHAR',
    'country         VARCHAR',
    'kind            VARCHAR',     // tv, streaming
    'wikidata_qid    VARCHAR',
    'legal_entity_did VARCHAR',
  ]);
  await v('vertex_anime_distribution', [
    'title_did       VARCHAR',
    'platform_did    VARCHAR',
    'country         VARCHAR',
    'license_start   DATE',
    'license_end     DATE',
    'sub_lang        VARCHAR',
    'dub_lang        VARCHAR',
  ]);
  await v('vertex_anime_source', [
    'title_did       VARCHAR',
    'kind            VARCHAR',     // manga, light_novel, game, original
    'source_title    VARCHAR',
    'author_did      VARCHAR',
    'publisher_did   VARCHAR',
    'first_year      INT',
  ]);
  await v('vertex_anime_song', [
    'title_did       VARCHAR',
    'kind            VARCHAR',     // op, ed, insert, bgm
    'seq             INT',
    'name            VARCHAR',
    'artist          VARCHAR',
    'composer_did    VARCHAR',
  ]);
  await v('vertex_anime_merchandise', [
    'title_did       VARCHAR',
    'sku             VARCHAR',
    'kind            VARCHAR',     // figure, acrylic, blu-ray, manga, goods
    'manufacturer_did VARCHAR',
    'msrp_jpy        BIGINT',
    'release_date    DATE',
  ]);
  await v('vertex_anime_ratings', [
    'title_did       VARCHAR',
    'source          VARCHAR',     // mal, anilist, anikore
    'rating_numeric  DOUBLE PRECISION',
    'rating_scale    VARCHAR',
    'votes_count     BIGINT',
    'snapshot_date   DATE',
  ]);

  // ── Edge tables (11) ───────────────────────────────────────────────────

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

  await e('edge_anime_produced_by', ['production_role VARCHAR']);            // title → studio
  await e('edge_anime_funded_by');                                 // title → committee
  await e('edge_anime_committee_member', ['investment_share DOUBLE PRECISION']); // committee → legal_entity
  await e('edge_anime_part_of_franchise');                         // title → franchise
  await e('edge_anime_stars_character');                           // title → character
  await e('edge_anime_voiced_by');                                 // character → staff
  await e('edge_anime_directed_by', ['credit_role VARCHAR']);            // title → staff (director/writer/...)
  await e('edge_anime_aired_on', ['start_date DATE', 'end_date DATE', 'slot VARCHAR']); // title → broadcaster
  await e('edge_anime_licensed_to');                               // title → distribution
  await e('edge_anime_adapted_from');                              // title → source
  await e('edge_anime_has_song');                                  // title → song

  // ── Streaming MVs (5) ──────────────────────────────────────────────────

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_studio_production_count AS
    SELECT s.vertex_id AS studio_did,
           s.name      AS studio_name,
           COUNT(DISTINCT t.vertex_id) AS title_count,
           MIN(t.year)                  AS first_year,
           MAX(t.year)                  AS last_year
    FROM vertex_anime_studio s
    LEFT JOIN edge_anime_produced_by p ON p.dst_vid = s.vertex_id
    LEFT JOIN vertex_anime_title   t ON t.vertex_id = p.src_vid
    GROUP BY s.vertex_id, s.name`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_distribution_by_country AS
    SELECT country,
           COUNT(DISTINCT title_did) AS title_count,
           COUNT(DISTINCT platform_did) AS platform_count
    FROM vertex_anime_distribution
    GROUP BY country`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_character_depth AS
    SELECT title_did, COUNT(*)::BIGINT AS character_count
    FROM vertex_anime_character
    GROUP BY title_did`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_committee_network AS
    SELECT cm.dst_vid AS legal_entity_did,
           COUNT(DISTINCT cm.src_vid) AS committee_count
    FROM edge_anime_committee_member cm
    GROUP BY cm.dst_vid`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anime_source_adaptation_ratio AS
    SELECT kind AS source_kind,
           COUNT(DISTINCT title_did) AS adapted_title_count
    FROM vertex_anime_source
    GROUP BY kind`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    'mv_anime_source_adaptation_ratio',
    'mv_anime_committee_network',
    'mv_anime_character_depth',
    'mv_anime_distribution_by_country',
    'mv_anime_studio_production_count',
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const t of [
    'edge_anime_has_song', 'edge_anime_adapted_from', 'edge_anime_licensed_to',
    'edge_anime_aired_on', 'edge_anime_directed_by', 'edge_anime_voiced_by',
    'edge_anime_stars_character', 'edge_anime_part_of_franchise',
    'edge_anime_committee_member', 'edge_anime_funded_by', 'edge_anime_produced_by',
    'vertex_anime_ratings', 'vertex_anime_merchandise', 'vertex_anime_song',
    'vertex_anime_source', 'vertex_anime_distribution', 'vertex_anime_broadcaster',
    'vertex_anime_episode', 'vertex_anime_character', 'vertex_anime_staff',
    'vertex_anime_committee', 'vertex_anime_studio', 'vertex_anime_franchise',
    'vertex_anime_title',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
