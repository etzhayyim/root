ALTER TABLE edge_constrained_by ADD COLUMN evidence_type VARCHAR;

ALTER TABLE edge_constrained_by ADD COLUMN rationale TEXT;

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_constrained_by_src ON edge_constrained_by(src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_constrained_by_dst ON edge_constrained_by(dst_vid);

CREATE INDEX IF NOT EXISTS idx_vertex_belief_system_tradition ON vertex_belief_system(tradition);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_belief_karma AS
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
    WHERE ec.dst_vid LIKE 'belief:%';

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_karma_aggregate AS
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
    GROUP BY actor_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_belief_actor_coverage AS
    SELECT
      belief_vertex_id,
      belief_name,
      tradition,
      COUNT(DISTINCT actor_vid)               AS actor_count,
      AVG(binding_strength)                   AS avg_binding_strength,
      COUNT(CASE WHEN binding_strength > 0.7 THEN 1 END) AS high_binding_actor_count
    FROM mv_actor_belief_karma
    GROUP BY belief_vertex_id, belief_name, tradition;

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
    'Etzhayyim is a technology platform built on Shannon information theory, AT Protocol, and empirical agent evaluation. Secular rationalist epistemology underlies design principles (η efficiency, formal verification, game-theoretic trust).'
  );

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

INSERT INTO edge_constrained_by (
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
  );

FLUSH;

INSERT INTO edge_constrained_by (
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
  );

INSERT INTO edge_constrained_by (
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
  );

FLUSH;
