import { Kysely, sql } from 'kysely';

/**
 * Migration 20260416230000: Per-actor belief karma system
 *
 * Purpose: enable actor-specific belief system visualization on profile karma tab.
 * Actors are seeded with edge_constrained_by edges pointing to vertex_belief_system
 * vertices, expressing how their philosophical/institutional premises constrain
 * their agency.
 *
 * Builds on: 20260416210000_belief_system_emotion_graph (vertex_belief_system + edge_constrained_by)
 *
 * Changes:
 *   ALTER edge_constrained_by: ADD evidence_type, rationale
 *
 * New indexes:
 *   idx_edge_constrained_by_src   — fast CSR lookup per actor
 *   idx_edge_constrained_by_dst   — fast CSC lookup per belief
 *   idx_vertex_belief_system_trad — tradition facet filter
 *
 * New MVs (all low-cardinality, safe for streaming):
 *   mv_actor_belief_karma        — per-(actor, belief) detail row; ~95 actors × 7 beliefs = ≤665 rows
 *   mv_actor_karma_aggregate     — per-actor summary; ≤95 rows
 *   mv_belief_actor_coverage     — per-belief actor counts; exactly 7 rows
 *
 * Seed data:
 *   edge_constrained_by entries for ~10 key actors:
 *     pmc-ncbi-nlm-nih-gov.etzhayyim.com → secular (0.90), dharma (0.25)
 *     yhwh.etzhayyim.com                 → yhwh (1.00)
 *     etzhayyim.com                      → secular (0.65), shinto (0.35)
 *     news.etzhayyim.com                 → secular (0.70)
 *     handotai.etzhayyim.com             → secular (0.75)
 *     society6.etzhayyim.com             → secular (0.55), confucian (0.45)
 *     iryo.etzhayyim.com                 → secular (0.80), dharma (0.30)
 *     dojo.etzhayyim.com                 → dharma (0.65), confucian (0.40)
 *     shizen.etzhayyim.com               → shinto (0.80), dharma (0.45)
 *     murakumo.etzhayyim.com             → secular (0.60), shinto (0.40)
 *
 * Apply (if kysely migrator blocked):
 *   psql "${ROOT_URL}" -f <(npx ts-node --esm scripts/migrate.ts list)
 * Or directly:
 *   psql "${ROOT_URL}" -c "INSERT INTO kysely_migration ..."
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 1. Extend edge_constrained_by with evidence metadata ─────────────────
  await sql`ALTER TABLE edge_constrained_by ADD COLUMN evidence_type VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_constrained_by ADD COLUMN rationale TEXT`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── 2. Indexes ────────────────────────────────────────────────────────────
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_constrained_by_src ON edge_constrained_by(src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_constrained_by_dst ON edge_constrained_by(dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_belief_system_tradition ON vertex_belief_system(tradition)`.execute(db);

  // ── 3. mv_actor_belief_karma ──────────────────────────────────────────────
  // Cardinality: bounded by (actor × belief) edge count. Initially ≤70 rows.
  // Safe: no high-cardinality GROUP BY, no wide MAX VARCHAR, backfill trivial.
  // Only includes edges whose dst_vid is a belief system vertex (prefix 'belief:').
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_belief_karma AS
    SELECT
      ec.src_vid                              AS actor_vid,
      bs.vertex_id                            AS belief_vertex_id,
      bs.name                                 AS belief_name,
      bs.display_name                         AS belief_display_name,
      bs.tradition                            AS tradition,
      bs.self_other_separation                AS self_other_separation,
      bs.individual_primacy                   AS individual_primacy,
      bs.time_structure                       AS time_structure,
      bs.consent_model                        AS consent_model,
      bs.approx_followers                     AS approx_followers,
      bs.description                          AS belief_description,
      COALESCE(ec.binding_strength, 0.5)      AS binding_strength,
      ec.constraint_type                      AS constraint_type,
      ec.evidence_type                        AS evidence_type,
      ec.epoch                                AS epoch,
      ec.created_date                         AS edge_created_date
    FROM edge_constrained_by ec
    JOIN vertex_belief_system bs ON bs.vertex_id = ec.dst_vid
    WHERE ec.dst_vid LIKE 'belief:%'`.execute(db);

  // ── 4. mv_actor_karma_aggregate ──────────────────────────────────────────
  // Cardinality: exactly one row per actor with any belief edges. ≤95 rows.
  // weighted_individuation = SUM(self_other_separation × binding_strength) / SUM(binding_strength)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_karma_aggregate AS
    SELECT
      actor_vid,
      COUNT(*)                                              AS belief_count,
      AVG(self_other_separation)                            AS avg_individuation,
      SUM(binding_strength)                                 AS total_binding,
      CASE WHEN SUM(binding_strength) > 0
        THEN SUM(self_other_separation * binding_strength) / SUM(binding_strength)
        ELSE AVG(self_other_separation)
      END                                                   AS weighted_individuation
    FROM mv_actor_belief_karma
    GROUP BY actor_vid`.execute(db);

  // ── 5. mv_belief_actor_coverage ──────────────────────────────────────────
  // Cardinality: exactly 7 rows (one per belief system vertex).
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_belief_actor_coverage AS
    SELECT
      belief_vertex_id,
      belief_name,
      tradition,
      COUNT(DISTINCT actor_vid)               AS actor_count,
      AVG(binding_strength)                   AS avg_binding_strength,
      COUNT(CASE WHEN binding_strength > 0.7 THEN 1 END) AS high_binding_actor_count
    FROM mv_actor_belief_karma
    GROUP BY belief_vertex_id, belief_name, tradition`.execute(db);

  await sql`FLUSH`.execute(db);

  // ── 6. Seed: actor → belief system edges ─────────────────────────────────
  // Uses constraint_type='epistemological' (belief system shapes how actor
  // constructs knowledge and evaluates evidence).
  // evidence_type: 'institutional'=official mandate, 'cultural'=cultural heritage,
  //               'inferential'=inferred from domain/behavior, 'historical'=historical record.

  // NIH PubMed Central — secular empirical science institution
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:pmc:secular',
    'did:web:pmc-ncbi-nlm-nih-gov.etzhayyim.com',
    'belief:secular',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.90,
    '1879-present',
    'institutional',
    'NIH/NLM mandate: empirical evidence-based medicine, peer review, RCT standards. CONSORT/PRISMA methodological frameworks encode secular-rationalist epistemology at institutional level.'
  )`.execute(db);

  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:pmc:dharma',
    'did:web:pmc-ncbi-nlm-nih-gov.etzhayyim.com',
    'belief:dharma',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.25,
    '1990-present',
    'inferential',
    'Integrative medicine, mindfulness-based interventions (MBSR/MBCT) increasingly indexed in PubMed. Systems biology framing resonates with interdependent causality. Weak binding — institutional core remains secular.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // YHWH actor — Abrahamic belief anchor (binding = maximal, it IS the belief system)
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:yhwh:yhwh',
    'did:web:yhwh.etzhayyim.com',
    'belief:yhwh',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'soteriological', 1.0,
    'c.2000 BCE-present',
    'historical',
    'YHWH is the personification of the Abrahamic belief system. Binding strength = 1.0 (identity, not merely constraint). Orthodox divine command theory: God''s nature defines the possibility space of all agency.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // etzhayyim platform — secular with Shinto aesthetic influence (Japanese origin, non-dual design)
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:etzhayyim:secular',
    'did:web:etzhayyim.com',
    'belief:secular',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.65,
    '2023-present',
    'institutional',
    'etzhayyim is a technology platform built on Shannon information theory, AT Protocol, and empirical agent evaluation. Secular rationalist epistemology underlies design principles (η efficiency, formal verification, game-theoretic trust).'
  )`.execute(db);

  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:etzhayyim:shinto',
    'did:web:etzhayyim.com',
    'belief:shinto',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.35,
    '2023-present',
    'cultural',
    'Japanese origin. Platform aesthetic draws on ma (間, negative space), mono no aware (transience), and kami-in-systems thinking. Non-dual agent design: actor ↔ environment boundary is permeable by design.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // News actor — secular journalism epistemology
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:news:secular',
    'did:web:news.etzhayyim.com',
    'belief:secular',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.70,
    '2023-present',
    'institutional',
    'Journalism operates on Enlightenment epistemic norms: verification, sourcing, falsifiability, public accountability. Secular Fourth Estate theory underlies editorial independence.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // Handotai (semiconductor) — secular science + engineering
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:handotai:secular',
    'did:web:handotai.etzhayyim.com',
    'belief:secular',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.75,
    '1947-present',
    'institutional',
    'Semiconductor industry epistemology: physical chemistry, solid-state physics, Moore''s Law empirical extrapolation, TSMC process geometry. Strict secular-rationalist standards for device characterization.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // Society6 — Japanese society (secular modernity + Confucian relational ethics)
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:society6:secular',
    'did:web:society6.etzhayyim.com',
    'belief:secular',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.55,
    '1868-present',
    'cultural',
    'Post-Meiji modernization: imported Western secular institutional frameworks (law, science, democracy). Surface secular but beneath persists relational/hierarchical value system.'
  )`.execute(db);

  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:society6:confucian',
    'did:web:society6.etzhayyim.com',
    'belief:confucian',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.45,
    '600 CE-present',
    'cultural',
    'Japanese society retains strong Confucian relational structure: 上下関係 (hierarchical relations), 義理 (giri/duty), 恥 (haji/shame). 五倫 maps directly to Japanese institutional/family/workplace norms.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // Iryo (medical/healthcare) — secular biomedicine + dharmic palliative care
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:iryo:secular',
    'did:web:iryo.etzhayyim.com',
    'belief:secular',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.80,
    '1850-present',
    'institutional',
    'Evidence-based medicine (EBM) hierarchy of evidence, RCT gold standard, biostatistics, clinical guidelines (JCS/JMA). Japanese MHLW regulatory framework encodes secular-empirical epistemology.'
  )`.execute(db);

  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:iryo:dharma',
    'did:web:iryo.etzhayyim.com',
    'belief:dharma',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.30,
    '700 CE-present',
    'cultural',
    'Buddhist hospital tradition (悲田院 c.593 CE, Prince Shotoku). Palliative care philosophy: compassionate accompaniment to death, impermanence acceptance. Buddhist monks historically provided end-of-life care in Japan.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // Dojo — martial arts discipline (dharmic + Confucian)
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:dojo:dharma',
    'did:web:dojo.etzhayyim.com',
    'belief:dharma',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'soteriological', 0.65,
    '600 CE-present',
    'cultural',
    'Japanese martial arts (Budo) lineage traces through Buddhist temples (Shaolin → Zen Buddhism via Bodhidharma). Mushin (無心, no-mind), Zanshin (残心, remaining awareness) — dharmic non-self in combat flow. 武道 as spiritual path.'
  )`.execute(db);

  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:dojo:confucian',
    'did:web:dojo.etzhayyim.com',
    'belief:confucian',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.40,
    '1600-present',
    'cultural',
    'Edo period Bushido codification: loyalty (忠), honor (名誉), duty (義理) — Confucian relational ethics applied to warrior class. Sensei-deshi (師弟) relationship mirrors 五倫 (teacher-student). Kata as embodied social ritual.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // Shizen (nature) — Shinto animism + dharmic interdependence
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:shizen:shinto',
    'did:web:shizen.etzhayyim.com',
    'belief:shinto',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.80,
    'pre-700 CE-present',
    'cultural',
    'Nature (自然, shizen) is itself the foundational category of Shinto epistemology. Kami (神) are immanent in mountains, rivers, forests. Satoyama (里山) landscape ethics: humans are participants in, not masters of, natural systems.'
  )`.execute(db);

  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:shizen:dharma',
    'did:web:shizen.etzhayyim.com',
    'belief:dharma',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.45,
    '700 CE-present',
    'cultural',
    'Buddhist concept of dependent origination (縁起, engi) resonates with ecological systems thinking: no entity exists independently. 「木を見て森を見ず」inverted — forest first. Sato-umi (里海) coastal commons management.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);

  // Murakumo (cloud inference) — secular AI science + Shinto naming
  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:murakumo:secular',
    'did:web:murakumo.etzhayyim.com',
    'belief:secular',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.60,
    '2023-present',
    'institutional',
    'LLM inference infrastructure grounded in secular-empirical ML: loss minimization, benchmark evaluation, scaling laws, peer-reviewed architecture. Cloudflare Workers runtime is agnostic substrate.'
  )`.execute(db);

  await sql`INSERT INTO edge_constrained_by (
    edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did,
    constraint_type, binding_strength, epoch, evidence_type, rationale
  ) VALUES (
    'edge:belief:murakumo:shinto',
    'did:web:murakumo.etzhayyim.com',
    'belief:shinto',
    CURRENT_DATE, 0, 'did:web:etzhayyim.com',
    'epistemological', 0.40,
    '2023-present',
    'cultural',
    '叢雲 (Murakumo) = "gathering clouds" in Japanese mythology. Ame no Murakumo no Tsurugi (天叢雲剣) — the legendary sword of Susanoo. Naming intentionally invokes Shinto cosmological imagery: intelligence as emergent weather pattern, not designed artifact.'
  )`.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_belief_actor_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_karma_aggregate`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_belief_karma`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_belief_system_tradition`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_constrained_by_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_constrained_by_src`.execute(db);
  // Note: ALTER TABLE ADD COLUMN evidence_type / rationale left in place.
  // RisingWave does not support DROP COLUMN on streaming tables.
  // Seed edge rows are left in place (safe — will be overwritten by future migrations).
}
