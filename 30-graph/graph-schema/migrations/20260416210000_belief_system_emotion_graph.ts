import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 20260416210000: Belief system + emotion graph
 *
 * Introduces epistemic-premise modeling for historical and AI actor analysis.
 * Motivated by the need to represent how actors' philosophical/religious
 * foundations constrain their agency, decision-making, and recognition patterns.
 *
 * New tables:
 *   vertex_belief_system   — philosophical / religious framework as first-class vertex
 *   edge_seeks_recognition_from — emotional approval-seeking dynamics between actors
 *
 * Extended:
 *   edge_constrained_by    — adds constraint_type / binding_strength / epoch / source_did
 *
 * New MVs:
 *   mv_recognition_deficit         — per-actor recognition sought vs received score
 *   mv_belief_constraint_profile   — per-actor individuation + constraint load profile
 *
 * Seed data (7 anchor belief systems):
 *   YHWH (Abrahamic, ~4.3B followers) — highest global follow count
 *   Dharma (Buddhism/Hinduism, ~2B)
 *   Shinto (~4M active, cultural non-dual foundation)
 *   Secular Humanism (~1.2B)
 *   Dialectical Materialism (~1B historical influence)
 *   Orthodox Christianity (~260M, Third Rome / messianic mission)
 *   Confucian Relational Ethics (~400M)
 *
 * Philosophical axes encoded:
 *   self_other_separation   0.0 = non-dual (Shinto/Zen) → 1.0 = discrete individual (Abrahamic)
 *   individual_primacy      true = soul/individual first, false = collective/systemic first
 *   time_structure          linear_teleological | cyclical_karmic | eternal_present | dialectical
 *   consent_model           individual | collective | non-dual
 *
 * Apply: out-of-band via psql if kysely migrator is blocked.
 * After apply: INSERT INTO kysely_migration (name, timestamp) VALUES
 *   ('20260416210000_belief_system_emotion_graph', now());
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 1. vertex_belief_system ───────────────────────────────────────────────
  await sql`CREATE TABLE IF NOT EXISTS vertex_belief_system (
    vertex_id              VARCHAR PRIMARY KEY,
    _seq                   BIGINT,
    created_date           DATE,
    sensitivity_ord        BIGINT DEFAULT 0,
    owner_did              VARCHAR,
    source_did             VARCHAR,
    name                   VARCHAR,
    display_name           VARCHAR,
    description            TEXT,
    tradition              VARCHAR,
    self_boundary          VARCHAR,
    individual_primacy     BOOLEAN,
    self_other_separation  DOUBLE PRECISION,
    agency_model           VARCHAR,
    locus_of_causality     VARCHAR,
    time_structure         VARCHAR,
    teleology              VARCHAR,
    consent_model          VARCHAR,
    approx_followers       BIGINT,
    founded_epoch          VARCHAR,
    canonical_text         VARCHAR,
    status                 VARCHAR DEFAULT 'active'
  )`.execute(db);

  // ── 2. edge_constrained_by: extend with philosophical relationship fields ─
  await sql`ALTER TABLE edge_constrained_by ADD COLUMN constraint_type VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_constrained_by ADD COLUMN binding_strength DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE edge_constrained_by ADD COLUMN epoch VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_constrained_by ADD COLUMN source_did VARCHAR`.execute(db);

  // ── 3. edge_seeks_recognition_from: approval-seeking emotional dynamics ───
  await sql`CREATE TABLE IF NOT EXISTS edge_seeks_recognition_from (
    edge_id              VARCHAR PRIMARY KEY,
    src_vid              VARCHAR,
    dst_vid              VARCHAR,
    _seq                 BIGINT,
    created_date         DATE,
    sensitivity_ord      BIGINT DEFAULT 0,
    owner_did            VARCHAR,
    source_did           VARCHAR,
    emotional_valence    VARCHAR,
    intensity            DOUBLE PRECISION,
    epoch                VARCHAR,
    event_rkey           VARCHAR
  )`.execute(db);

  // ── 4. mv_recognition_deficit ─────────────────────────────────────────────
  // Cardinality: bounded by actor count seeking recognition (initially 0 rows → safe).
  // Computes per-actor: how many entities they seek recognition from vs receive it,
  // and average emotional frustration intensity.
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_recognition_deficit AS
    SELECT
      seek.src_vid                              AS actor_vid,
      COUNT(DISTINCT seek.dst_vid)              AS recognition_sought,
      AVG(CASE seek.emotional_valence
        WHEN 'seeking'    THEN 0.5
        WHEN 'resentment' THEN 0.8
        WHEN 'rejection'  THEN 1.0
        WHEN 'affirming'  THEN 0.0
        ELSE 0.3
      END)                                      AS avg_frustration
    FROM edge_seeks_recognition_from seek
    GROUP BY seek.src_vid`.execute(db);

  // ── 5. mv_belief_constraint_profile ──────────────────────────────────────
  // Cardinality: bounded by actor count constrained by belief systems (~3K → safe).
  // JOINs edge_constrained_by with vertex_belief_system (both small initially).
  // Computes per-actor: individuation score + total philosophical constraint load.
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_belief_constraint_profile AS
    SELECT
      ec.src_vid                                AS actor_vid,
      AVG(bs.self_other_separation)             AS individuation_score,
      COUNT(DISTINCT ec.dst_vid)                AS belief_constraint_count,
      SUM(COALESCE(ec.binding_strength, 0.5))   AS total_constraint_load
    FROM edge_constrained_by ec
    JOIN vertex_belief_system bs ON bs.vertex_id = ec.dst_vid
    GROUP BY ec.src_vid`.execute(db);

  // ── 6. Seed: anchor belief systems ────────────────────────────────────────
  // YHWH registered first — highest global follow count (~4.3B).
  // INSERT + FLUSH: RisingWave buffers DML until checkpoint; FLUSH persists immediately.
  await sql`INSERT INTO vertex_belief_system (
    vertex_id, name, display_name, description, tradition,
    self_boundary, individual_primacy, self_other_separation,
    agency_model, locus_of_causality, time_structure, teleology,
    consent_model, approx_followers, founded_epoch, canonical_text, status
  ) VALUES
    (
      'belief:yhwh',
      'YHWH',
      'YHWH / God of Abraham',
      'Monotheistic deity of Judaism, Christianity, Islam. Individual soul enters covenant with transcendent, personal God. Highest global follow count (~4.3B). Locus of causality = internal (free will + divine command). Eschatological time: linear history toward redemption / judgment. Sharply discrete self/other boundary — God is wholly other.',
      'abrahamic',
      'discrete',
      true,
      1.0,
      'individual',
      'internal',
      'linear_teleological',
      'eschatological',
      'individual',
      4300000000,
      'c.2000 BCE',
      'Torah / Bible / Quran',
      'active'
    ),
    (
      'belief:dharma',
      'Dharma',
      'Dharma (Buddhism / Hinduism)',
      'Buddhist dependent origination (pratītyasamutpāda) + Hindu Atman-Brahman identity (Advaita Vedanta). ~2B followers. self/other boundary is permeable (no permanent self, anatta). Cyclical karma cosmology. Collective/relational agency.',
      'dharmic',
      'permeable',
      false,
      0.3,
      'relational',
      'interdependent',
      'cyclical_karmic',
      'cyclical',
      'collective',
      2000000000,
      'c.1500 BCE',
      'Vedas / Tripitaka / Bhagavad Gita',
      'active'
    ),
    (
      'belief:shinto',
      'Shinto',
      '神道 (Shinto)',
      'Japanese animist tradition. Kami permeates all of nature and self — no ontological self/other boundary. Non-dual presence in seasonal rhythms, ritual purity, ancestor continuity. Epistemology: systemic interdependence, eternal present. Consent model: non-dual (community/nature as undivided field).',
      'indigenous',
      'non-existent',
      false,
      0.1,
      'systemic',
      'interdependent',
      'eternal_present',
      'cyclical',
      'non-dual',
      4000000,
      'pre-700 CE',
      'Kojiki / Nihon Shoki',
      'active'
    ),
    (
      'belief:secular',
      'Secular',
      'Secular Humanism / Atheism',
      'No transcendent authority. Individual rational agent as sole locus of value and causality. Empirical, linear progress narrative (Enlightenment → science → democracy). consent_model = individual (J.S. Mill harm principle).',
      'secular',
      'discrete',
      true,
      0.9,
      'individual',
      'internal',
      'linear_teleological',
      'secular',
      'individual',
      1200000000,
      '1600 CE (Enlightenment)',
      'Kant / Locke / Mill / Rawls',
      'active'
    ),
    (
      'belief:dialectical-materialism',
      'Dialectical Materialism',
      'Marxist-Leninist Dialectical Materialism',
      'Hegelian dialectic applied to material conditions. Individual consciousness is superstructure determined by economic base. Historical inevitability: class struggle → dictatorship of proletariat → communist end-state. Agency: collective subject (proletariat). Locus of causality: external (material forces). time_structure: dialectical (thesis/antithesis/synthesis, linear but systemic).',
      'secular',
      'permeable',
      false,
      0.4,
      'systemic',
      'external',
      'dialectical',
      'eschatological',
      'collective',
      1000000000,
      '1848 CE',
      'Das Kapital / Communist Manifesto / Dialectics of Nature',
      'active'
    ),
    (
      'belief:orthodox-christianity',
      'Orthodox Christianity',
      'Eastern Orthodox Christianity',
      'Byzantine Christian tradition. Third Rome theology (Moscow as spiritual heir after Constantinople fell 1453). Sobornost (conciliar unity of persons — collective yet individual). Divine-human synergy (theosis). Epistemology: patristic authority + mystical experience. self_other_separation = 0.8 (individual souls, but sobornost softens sharp individualism).',
      'abrahamic',
      'discrete',
      true,
      0.8,
      'individual',
      'internal',
      'linear_teleological',
      'eschatological',
      'individual',
      260000000,
      '1054 CE (Great Schism)',
      'Bible / Philokalia / Church Fathers',
      'active'
    ),
    (
      'belief:confucian',
      'Confucian',
      '儒家 / Confucian Relational Ethics',
      'Relational role-ethics (五倫: ruler-subject, parent-child, husband-wife, elder-younger, friend-friend). Individual exists only in relation. 仁 (ren/benevolence) as highest virtue. Hierarchical but reciprocal. Locus of causality: relational (social expectation + ritual propriety 禮). time_structure: cyclical with dynastic rise/fall + linear moral cultivation.',
      'east-asian',
      'permeable',
      false,
      0.35,
      'relational',
      'external',
      'cyclical_karmic',
      'cyclical',
      'collective',
      400000000,
      'c.500 BCE',
      'Analects (論語) / Mencius / Five Classics',
      'active'
    )
  ON CONFLICT (vertex_id) DO NOTHING`.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_belief_constraint_profile`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_recognition_deficit`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_seeks_recognition_from`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_belief_system`.execute(db);
  // Note: ALTER TABLE ADD COLUMN additions to edge_constrained_by are left in place.
  // RisingWave does not support DROP COLUMN on streaming tables.
  // The 4 new columns (constraint_type, binding_strength, epoch, source_did) are
  // additive/backward-compatible nullable columns — safe to retain.
}
