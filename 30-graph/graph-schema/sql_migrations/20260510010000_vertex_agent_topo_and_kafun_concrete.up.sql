-- ADR-2605080600 amendment — generic agent goal-DAG schema + kafun concrete layer.
--
-- Captures "what an autonomous agent must reason about to reach its goal":
--   * vertex_agent_topo_node       — abstract dependency-DAG node (per app_did)
--   * edge_agent_topo_depends      — X requires Y to be done first
--   * edge_agent_topo_concerns     — topo node → concrete vertex (nursery / pollen / etc.)
--   * mv_agent_topo_ready          — nodes whose hard dependencies are all 'done' (= next eligible work)
--   * mv_agent_topo_progress       — (app_did, layer) → completion ratio
--
-- Concrete layer for kafun-bokumetsu (referenced by edge_agent_topo_concerns):
--   * vertex_kafun_nursery            (L1-1)
--   * vertex_kafun_forest_unit        (L3-1)
--   * vertex_kafun_pollen_observation (L4-1) — daily timeseries
--   * mv_kafun_pollen_yoy             — prefecture × year × species YoY change
--
-- Seed data: 16-row topology of the kafun eradication DAG (L0 → L5).
--
-- Persistence model: record-log semantics (PK re-INSERT = implicit upsert; no
-- ON CONFLICT, no UPDATE). RisingWave: no JSONB; JSON stored as VARCHAR.

-- ─────────────────────────────────────────────────────────────────────────
-- Generic agent goal-DAG schema
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_agent_topo_node (
  vertex_id        varchar PRIMARY KEY,           -- at://{controller_did}/com.etzhayyim.agent.topoNode/{node_id}
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  app_did          varchar NOT NULL,              -- controller DID of the owning app
  node_id          varchar NOT NULL,              -- e.g. 'L1-1' (unique per app_did)
  layer            bigint NOT NULL,               -- 0..N
  category         varchar NOT NULL,              -- evidence|capacity|funding|execution|measurement|goal
  title            varchar NOT NULL,
  description      varchar,
  status           varchar DEFAULT 'planned',     -- planned|in_progress|blocked|done|abandoned
  bottleneck_rank  bigint DEFAULT 0,              -- Theory-of-Constraints rank; 1 = tightest, 0 = unranked
  kpi_weight       double precision DEFAULT 1.0,  -- Shannon priority weight (root CLAUDE.md [[heuristic_weights]])
  target_metric    varchar,                       -- e.g. 'sugi_pollen_count_per_m3'
  target_value     double precision,              -- numeric target
  target_unit      varchar,                       -- 'count/m³', 'ha', 'JPY', '%'
  current_value    double precision,              -- last observed; updated by tick
  owner_actor_did  varchar,                       -- path-based DID accountable for this node
  evidence_uri     varchar,                       -- optional supporting URL
  created_at       varchar,
  updated_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_topo_node_app_layer  ON vertex_agent_topo_node (app_did, layer, status);
CREATE INDEX IF NOT EXISTS idx_topo_node_status     ON vertex_agent_topo_node (status, bottleneck_rank);
CREATE INDEX IF NOT EXISTS idx_topo_node_owner      ON vertex_agent_topo_node (owner_actor_did);

CREATE TABLE IF NOT EXISTS edge_agent_topo_depends (
  edge_id          varchar PRIMARY KEY,           -- {src_node_id}->{dst_node_id}
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  src_vid          varchar NOT NULL,              -- dependent (cannot start until dst done)
  dst_vid          varchar NOT NULL,              -- prerequisite
  dep_kind         varchar DEFAULT 'hard',        -- hard | soft
  weight           double precision DEFAULT 1.0,  -- criticality (hard ≈ 1.0; soft 0.1..0.5)
  created_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_topo_depends_src ON edge_agent_topo_depends (src_vid, dep_kind);
CREATE INDEX IF NOT EXISTS idx_topo_depends_dst ON edge_agent_topo_depends (dst_vid);

CREATE TABLE IF NOT EXISTS edge_agent_topo_concerns (
  edge_id          varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  src_vid          varchar NOT NULL,              -- topo_node vertex_id
  dst_vid          varchar NOT NULL,              -- concrete vertex (nursery, forest_unit, observation, etc.)
  relation         varchar DEFAULT 'tracks',      -- tracks | funds | blocks_on
  weight           double precision DEFAULT 1.0,
  created_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_topo_concerns_src ON edge_agent_topo_concerns (src_vid, relation);
CREATE INDEX IF NOT EXISTS idx_topo_concerns_dst ON edge_agent_topo_concerns (dst_vid);

-- "Ready" = node not yet done AND every hard dependency is done.
-- Output: one row per ready node. Agent.tick orders these by (bottleneck_rank, layer, kpi_weight).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_agent_topo_ready AS
SELECT n.vertex_id,
       n.app_did,
       n.node_id,
       n.layer,
       n.category,
       n.title,
       n.bottleneck_rank,
       n.kpi_weight,
       n.owner_actor_did
FROM   vertex_agent_topo_node n
WHERE  n.status IN ('planned', 'blocked')
  AND  NOT EXISTS (
         SELECT 1
         FROM   edge_agent_topo_depends d
         JOIN   vertex_agent_topo_node p ON p.vertex_id = d.dst_vid
         WHERE  d.src_vid  = n.vertex_id
           AND  d.dep_kind = 'hard'
           AND  p.status   <> 'done'
       );

-- Per-(app, layer) progress rollup. Cardinality bounded by app_count × max_layer (low).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_agent_topo_progress AS
SELECT app_did,
       layer,
       COUNT(*)                                                    AS total,
       COUNT(*) FILTER (WHERE status = 'done')                     AS done,
       COUNT(*) FILTER (WHERE status = 'in_progress')              AS in_progress,
       COUNT(*) FILTER (WHERE status = 'blocked')                  AS blocked,
       SUM(kpi_weight)                                             AS weight_total,
       SUM(kpi_weight) FILTER (WHERE status = 'done')              AS weight_done
FROM   vertex_agent_topo_node
GROUP  BY app_did, layer;

-- ─────────────────────────────────────────────────────────────────────────
-- Kafun concrete layer
-- ─────────────────────────────────────────────────────────────────────────

-- L1-1 苗木生産者 / nurseries that can supply pollen-free Cryptomeria seedlings.
CREATE TABLE IF NOT EXISTS vertex_kafun_nursery (
  vertex_id           varchar PRIMARY KEY,         -- at://{controller_did}/com.etzhayyim.apps.kafun.nursery/{id}
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 0,
  owner_did           varchar,
  name                varchar,
  legal_entity_lei    varchar,                     -- → vertex_legal_entity (LEI)
  prefecture          varchar,                     -- ISO 3166-2:JP code
  capacity_per_year   bigint DEFAULT 0,            -- seedlings/year
  cultivars           varchar,                     -- JSON array of registered cultivar IDs
  price_jpy_per_unit  bigint,
  contact_email       varchar,
  status              varchar DEFAULT 'active',    -- active | inactive
  created_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_kafun_nursery_pref ON vertex_kafun_nursery (prefecture, status);

-- L3-1 林班 / forest compartments dominated by pollen-emitting species.
CREATE TABLE IF NOT EXISTS vertex_kafun_forest_unit (
  vertex_id           varchar PRIMARY KEY,         -- at://{controller_did}/com.etzhayyim.apps.kafun.forestUnit/{id}
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 0,
  owner_did           varchar,
  prefecture          varchar,
  municipality        varchar,
  forest_office       varchar,                     -- 営林署
  owner_legal_entity_lei varchar,
  area_ha             double precision,
  dominant_species    varchar,                     -- sugi | hinoki | mixed
  age_years           bigint,
  planned_action      varchar DEFAULT 'none',      -- none | clearcut | thinning | replant_no_pollen
  planned_year        bigint,
  geom_geojson        varchar,                     -- WGS84 polygon
  created_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_kafun_forest_pref       ON vertex_kafun_forest_unit (prefecture, dominant_species);
CREATE INDEX IF NOT EXISTS idx_kafun_forest_action     ON vertex_kafun_forest_unit (planned_action, planned_year);

-- L4-1 飛散観測 (環境省ダーラム法 + 自動計数機).
CREATE TABLE IF NOT EXISTS vertex_kafun_pollen_observation (
  vertex_id           varchar PRIMARY KEY,         -- at://{controller_did}/com.etzhayyim.apps.kafun.pollenObservation/{sha256(station:obs_at)[:24]}
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 0,
  owner_did           varchar,
  station_id          varchar NOT NULL,
  prefecture          varchar NOT NULL,
  obs_at              varchar NOT NULL,            -- ISO 8601 day
  obs_year            bigint NOT NULL,
  obs_season_month    bigint,                      -- 2..5 typical for sugi/hinoki season
  sugi_count_m3       double precision DEFAULT 0,
  hinoki_count_m3     double precision DEFAULT 0,
  total_count_m3      double precision DEFAULT 0,
  source              varchar,                     -- env_moe | jma | citizen_sensor
  created_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_kafun_pollen_station   ON vertex_kafun_pollen_observation (station_id, obs_at);
CREATE INDEX IF NOT EXISTS idx_kafun_pollen_pref_year ON vertex_kafun_pollen_observation (prefecture, obs_year);

-- Year-over-year change per (prefecture × year × species). Cardinality bounded by
-- prefecture (47) × years (~30) × species (2) ≈ 2,820 — safe for streaming MV.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kafun_pollen_yoy AS
SELECT prefecture,
       obs_year,
       SUM(sugi_count_m3)   AS sugi_total,
       SUM(hinoki_count_m3) AS hinoki_total,
       SUM(total_count_m3)  AS season_total,
       COUNT(*)             AS obs_count
FROM   vertex_kafun_pollen_observation
GROUP  BY prefecture, obs_year;

-- ─────────────────────────────────────────────────────────────────────────
-- Seed: kafun eradication DAG (L0 → L5, 16 nodes + dependency edges)
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO vertex_agent_topo_node (vertex_id, _seq, sensitivity_ord, app_did, node_id, layer, category, title, description, status, bottleneck_rank, kpi_weight, target_metric, target_value, target_unit, current_value, owner_actor_did, created_at) VALUES
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-1', 0, 'evidence',    '立木分布 GIS',                '林野庁スギ・ヒノキ立木 GIS の Fund 視点取り込み',                                'in_progress', 0, 0.5, 'forest_units_indexed_count',     710,        'man_ha',   0,    'did:web:n97ik10n.etzhayyim.com:actor:researcher', '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-2', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-2', 0, 'evidence',    '花粉飛散量モニタ',            '環境省ダーラム法 + 自動計数機の年次取り込み',                                  'in_progress', 0, 0.7, 'pollen_observation_count_year',  10000,      'rows',     0,    'did:web:n97ik10n.etzhayyim.com:actor:researcher', '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-3', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-3', 0, 'evidence',    '罹患率・QOL 損失データ',      'kafun-induced 経済損失 ~3.8兆円/年 の連年更新',                                'planned',     0, 0.6, 'qol_loss_estimate_jpy_year',     3800000000000, 'JPY',     NULL, 'did:web:n97ik10n.etzhayyim.com:actor:researcher', '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-4', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-4', 0, 'evidence',    '無花粉品種登録',              '林木育種センター登録の無花粉スギ・少花粉ヒノキ系統一覧',                       'planned',     0, 0.5, 'cultivars_indexed',              200,        'count',    0,    'did:web:n97ik10n.etzhayyim.com:actor:researcher', '2026-05-10T00:00:00Z'),

  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-1', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L1-1', 1, 'capacity',    '無花粉苗木の量産',            'pollen-free seedling 年産能力 (現状は需要の <10%)',                            'planned',     1, 1.0, 'seedlings_per_year',             100000000,  'count',    0,    'did:web:n97ik10n.etzhayyim.com:actor:proposer',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-2', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L1-2', 1, 'capacity',    '林業労働者・機械化',          '高齢化と新規就業者・伐採機械の確保',                                            'planned',     0, 0.7, 'forestry_workforce_count',       50000,      'count',    NULL, 'did:web:n97ik10n.etzhayyim.com:actor:proposer',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-3', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L1-3', 1, 'capacity',    '雄花着花抑制剤の登録',        'Sydowia japonica 等の生物農薬登録 + 量産',                                      'planned',     0, 0.5, 'biocide_registered_count',       3,          'count',    0,    'did:web:n97ik10n.etzhayyim.com:actor:proposer',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-4', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L1-4', 1, 'capacity',    'SLIT 治療薬供給拡大',         '舌下免疫療法薬の生産能力 + 専門医確保',                                          'planned',     0, 0.7, 'slit_doses_per_year',            5000000,    'doses',    NULL, 'did:web:n97ik10n.etzhayyim.com:actor:proposer',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-5', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L1-5', 1, 'capacity',    '国産材需要創出',              'CLT・公共建築・バイオマスでの国産スギ・ヒノキ材需要',                            'planned',     0, 0.6, 'domestic_timber_use_m3_year',    50000000,   'm3',       NULL, 'did:web:n97ik10n.etzhayyim.com:actor:proposer',   '2026-05-10T00:00:00Z'),

  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-1', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L2-1', 2, 'funding',     '国予算',                      '令和の花粉症対策 10年計画予算',                                                  'in_progress', 0, 0.8, 'budget_jpy_year',                100000000000, 'JPY',    NULL, 'did:web:n97ik10n.etzhayyim.com:actor:executor',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-2', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L2-2', 2, 'funding',     'kafun-bokumetsu Fund 自体',   'GCC 取引手数料 → Public Asset → Fund 投入',                                     'in_progress', 0, 1.0, 'fund_balance_jpy',               1000000000, 'JPY',     0,    'did:web:n97ik10n.etzhayyim.com:actor:executor',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-3', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L2-3', 2, 'funding',     '健康保険適用拡大',            'SLIT の保険適用拡大',                                                            'planned',     0, 0.5, 'slit_insured_pct',               80,         '%',        NULL, 'did:web:n97ik10n.etzhayyim.com:actor:executor',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-4', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L2-4', 2, 'funding',     '主伐再造林補助・税制',        '主伐再造林への補助金 + 税優遇',                                                  'planned',     0, 0.7, 'subsidy_coverage_pct',           60,         '%',        NULL, 'did:web:n97ik10n.etzhayyim.com:actor:executor',   '2026-05-10T00:00:00Z'),

  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-1', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L3-1', 3, 'execution',   '主伐再造林スケール 10万 ha/年','現状 ~5万 ha → 10万 ha/年 へ倍増',                                              'planned',     2, 1.0, 'replanting_ha_year',             100000,     'ha',       50000,'did:web:n97ik10n.etzhayyim.com:actor:executor',   '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-3', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L3-3', 3, 'execution',   'SLIT 普及 数百万人',          '舌下免疫療法を実際に受ける患者数',                                              'planned',     0, 0.7, 'slit_patients',                  3000000,    'count',    NULL, 'did:web:n97ik10n.etzhayyim.com:actor:executor',   '2026-05-10T00:00:00Z'),

  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L4-1', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L4-1', 4, 'measurement', '飛散・罹患の年次低下確認',    'mv_kafun_pollen_yoy で前年比 < 1.0 を継続的に確認',                              'planned',     0, 0.8, 'sugi_yoy_ratio',                 0.5,        'ratio',    NULL, 'did:web:n97ik10n.etzhayyim.com:actor:executor',   '2026-05-10T00:00:00Z'),

  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L5',   0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L5',   5, 'goal',        'スギ・ヒノキ花粉症の撲滅',    '罹患率 ≈ 0、飛散量 ≈ 0',                                                         'planned',     0, 1.0, 'patient_count',                  0,          'count',    NULL, 'did:web:n97ik10n.etzhayyim.com',                  '2026-05-10T00:00:00Z');

-- Dependency edges (src depends on dst).
INSERT INTO edge_agent_topo_depends (edge_id, _seq, sensitivity_ord, src_vid, dst_vid, dep_kind, weight, created_at) VALUES
  ('L1-1->L0-4', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-4', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L1-2->L0-1', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-2', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L1-5->L0-1', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-5', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1', 'hard', 1.0, '2026-05-10T00:00:00Z'),

  ('L2-1->L0-3', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-3', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L2-1->L1-1', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-1', 'soft', 0.5, '2026-05-10T00:00:00Z'),
  ('L2-2->L0-3', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-2', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-3', 'soft', 0.5, '2026-05-10T00:00:00Z'),
  ('L2-3->L1-4', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-3', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-4', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L2-4->L1-1', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-4', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-1', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L2-4->L1-2', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-4', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-2', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L2-4->L1-5', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-4', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-5', 'soft', 0.5, '2026-05-10T00:00:00Z'),

  ('L3-1->L1-1', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-1', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L3-1->L1-2', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-2', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L3-1->L2-4', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-4', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L3-3->L1-4', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-3', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-4', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L3-3->L2-3', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-3', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L2-3', 'hard', 1.0, '2026-05-10T00:00:00Z'),

  ('L4-1->L0-2', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L4-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-2', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L4-1->L3-1', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L4-1', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-1', 'soft', 0.5, '2026-05-10T00:00:00Z'),

  ('L5->L3-1',   0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L5',   'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-1', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L5->L3-3',   0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L5',   'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-3', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L5->L4-1',   0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L5',   'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L4-1', 'hard', 1.0, '2026-05-10T00:00:00Z');
