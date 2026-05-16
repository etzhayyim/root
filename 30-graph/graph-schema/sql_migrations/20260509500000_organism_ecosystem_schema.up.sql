-- ADR-2605091300 / 091400 / 091500 / 091600 / 091800 / 091900
-- ADR-2605092000 / 092100 / 092200 / 092300 / 092400 / 092500
--
-- Organism Ecosystem schema:
--   * Bonsai cultivar layer (flower/fruit/water/prune)
--   * Plasmid horizontal acquisition
--   * Ecosystem-as-Model FP8 vector substrate
--   * Continuous metabolic training signal log
--   * Tool/substrate/cohort routing weights
--
-- Persistence model = root CLAUDE.md "Record-log semantics":
--   no UPDATE, no ON CONFLICT. PK re-INSERT = implicit upsert.
-- Field encryption for private text uses `signal:v1:{ciphertext}` per
--   ADR-2605081300 vault zero-knowledge invariant.
-- All FP8 tensor columns: VARBINARY (BYTEA) holding D bytes E4M3 + REAL scale.
-- RisingWave: no JSONB; JSON stored as VARCHAR. No ON CONFLICT, no UPDATE.

-- ─────────────────────────────────────────────────────────────────────────
-- ADR-2605091900: Yoro flowering / fruiting surface
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_yoro_flower (
  vertex_id        varchar PRIMARY KEY,            -- at://{cohort_did}/yoro.flower/{flower_id}
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 100,
  owner_did        varchar,
  flower_id        varchar NOT NULL,
  cohort_did       varchar NOT NULL,
  branch_id        varchar,                         -- LangGraph subgraph id
  status           varchar DEFAULT 'budding',       -- budding|blooming|aborted
  draft_content    varchar,                         -- JSON string
  modality         varchar,                         -- text|image|audio|code|graph|struct
  ripeness_eta     double precision DEFAULT 0,      -- η accumulator
  created_at       varchar,
  updated_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_yoro_flower_cohort ON vertex_yoro_flower (cohort_did, created_at);
CREATE INDEX IF NOT EXISTS idx_yoro_flower_status ON vertex_yoro_flower (status, ripeness_eta);

CREATE TABLE IF NOT EXISTS vertex_yoro_fruit (
  vertex_id        varchar PRIMARY KEY,            -- content-addressed CID
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 100,
  owner_did        varchar,
  fruit_id         varchar NOT NULL,
  flower_id        varchar,
  cohort_did       varchar NOT NULL,
  status           varchar DEFAULT 'ripening',     -- ripening|ripe|dropped|culled|consumed
  ripeness         double precision DEFAULT 0,     -- 0..1
  artifact_cid     varchar,                         -- IPFS pin
  pds_record_uri   varchar,                         -- AT Protocol post URI (spore)
  consumed_count   bigint DEFAULT 0,
  prune_id         varchar,                         -- FK edge_yoro_prune (logical)
  ripened_at       varchar,
  created_at       varchar,
  updated_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_yoro_fruit_cohort ON vertex_yoro_fruit (cohort_did, ripened_at);
CREATE INDEX IF NOT EXISTS idx_yoro_fruit_flower ON vertex_yoro_fruit (flower_id);

CREATE TABLE IF NOT EXISTS edge_yoro_pollinate (
  edge_id          varchar PRIMARY KEY,
  src_vid          varchar NOT NULL,                -- pollinator_did
  dst_vid          varchar NOT NULL,                -- flower vertex_id
  relation_kind    varchar NOT NULL DEFAULT 'pollinate',
  pollinator_did   varchar NOT NULL,
  flower_id        varchar NOT NULL,
  signal_kind      varchar,                         -- like|mention|cite|quote
  weight_eta       double precision,
  pollinated_at    varchar,
  owner_did        varchar,
  sensitivity_ord  bigint DEFAULT 100
);
CREATE INDEX IF NOT EXISTS idx_yoro_pollinate_flower ON edge_yoro_pollinate (flower_id);
CREATE INDEX IF NOT EXISTS idx_yoro_pollinate_src ON edge_yoro_pollinate (src_vid);

-- ─────────────────────────────────────────────────────────────────────────
-- ADR-2605091800: Pruning Protocol — 6-tier
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_yoro_prune (
  edge_id          varchar PRIMARY KEY,             -- content-addressed
  src_vid          varchar NOT NULL,                -- pruner_did
  dst_vid          varchar NOT NULL,                -- target entity vertex_id
  relation_kind    varchar NOT NULL DEFAULT 'prune',
  pruner_did       varchar NOT NULL,
  target_kind      varchar NOT NULL,                -- fruit|flower|leaf|branch|trunk|seed
  target_id        varchar NOT NULL,
  reason_code      varchar,                         -- bad-quality|off-policy|floor-violation|aesthetic|natural-shedding
  authority        varchar NOT NULL,                -- auto-floor|kakushya-dao|human-owner|partner-permit|auto-prune
  reversible       boolean DEFAULT true,
  evidence_cid     varchar,                         -- IPFS witness
  pruned_at        varchar,
  reverted_at      varchar,
  owner_did        varchar,
  sensitivity_ord  bigint DEFAULT 100
);
CREATE INDEX IF NOT EXISTS idx_yoro_prune_target ON edge_yoro_prune (target_kind, target_id);
CREATE INDEX IF NOT EXISTS idx_yoro_prune_authority ON edge_yoro_prune (authority, pruned_at);

-- ─────────────────────────────────────────────────────────────────────────
-- ADR-2605091500: Mycorrhizal watering & consent-gated mutation
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_bonsai_water (
  edge_id          varchar PRIMARY KEY,             -- content-addressed
  src_vid          varchar NOT NULL,                -- source_did (human/org/external)
  dst_vid          varchar NOT NULL,                -- target cohort/cell
  relation_kind    varchar NOT NULL DEFAULT 'water',
  source_did       varchar NOT NULL,
  target_did       varchar NOT NULL,
  kind             varchar NOT NULL,                -- data|attention|fund|tool-grant|mutate-permit
  scope_json       varchar,                         -- kind-specific scope
  amount           double precision,
  ttl_seconds      bigint,
  consent_proof    varchar,                         -- DPoP+WebAuthn / OAuth grant CID
  expires_at       varchar,
  granted_at       varchar,
  owner_did        varchar,
  sensitivity_ord  bigint DEFAULT 100
);
CREATE INDEX IF NOT EXISTS idx_bonsai_water_target ON edge_bonsai_water (target_did, granted_at);
CREATE INDEX IF NOT EXISTS idx_bonsai_water_kind ON edge_bonsai_water (kind, expires_at);

CREATE TABLE IF NOT EXISTS vertex_water_consent_grant (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 100,
  owner_did        varchar,
  grant_id         varchar NOT NULL,
  source_did       varchar NOT NULL,
  target_did       varchar NOT NULL,
  kind             varchar NOT NULL,
  scope_json       varchar,
  status           varchar DEFAULT 'active',        -- active|revoked|expired
  granted_at       varchar,
  revoked_at       varchar,
  expires_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_water_consent_target ON vertex_water_consent_grant (target_did, status);

-- ─────────────────────────────────────────────────────────────────────────
-- ADR-2605091600: Plasmid + Graft horizontal acquisition
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_kobo_plasmid (
  vertex_id        varchar PRIMARY KEY,             -- content-addressed CIDv1
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 100,
  owner_did        varchar,
  plasmid_id       varchar NOT NULL,
  origin_did       varchar,                          -- 起源 cell / org
  tool_refs_json   varchar,                          -- [{mcp_server, tool_name, version, signature_cid}]
  capability_hash  varchar,
  generation       bigint DEFAULT 0,
  created_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_kobo_plasmid_origin ON vertex_kobo_plasmid (origin_did);

CREATE TABLE IF NOT EXISTS edge_kobo_plasmid_carry (
  edge_id          varchar PRIMARY KEY,
  src_vid          varchar NOT NULL,                 -- cell_did
  dst_vid          varchar NOT NULL,                 -- plasmid vertex_id
  relation_kind    varchar NOT NULL DEFAULT 'plasmid_carry',
  cell_did         varchar NOT NULL,
  plasmid_id       varchar NOT NULL,
  acquired_via     varchar NOT NULL,                 -- shuga|conjugation|graft|water-grant
  acquired_at      varchar,
  active           boolean DEFAULT true,
  owner_did        varchar,
  sensitivity_ord  bigint DEFAULT 100
);
CREATE INDEX IF NOT EXISTS idx_kobo_plasmid_carry_cell ON edge_kobo_plasmid_carry (cell_did, active);
CREATE INDEX IF NOT EXISTS idx_kobo_plasmid_carry_plasmid ON edge_kobo_plasmid_carry (plasmid_id);

CREATE TABLE IF NOT EXISTS edge_yoro_graft (
  edge_id            varchar PRIMARY KEY,
  src_vid            varchar NOT NULL,               -- donor_branch_cid
  dst_vid            varchar NOT NULL,               -- recipient_branch_cid
  relation_kind      varchar NOT NULL DEFAULT 'graft',
  donor_branch_cid   varchar NOT NULL,
  recipient_branch_cid varchar NOT NULL,
  owner_consent_cid  varchar NOT NULL,
  plasmid_bundle_cid varchar,                         -- bundle of plasmids transferred
  grafted_at         varchar,
  owner_did          varchar,
  sensitivity_ord    bigint DEFAULT 100
);
CREATE INDEX IF NOT EXISTS idx_yoro_graft_donor ON edge_yoro_graft (donor_branch_cid);
CREATE INDEX IF NOT EXISTS idx_yoro_graft_recipient ON edge_yoro_graft (recipient_branch_cid);

-- ─────────────────────────────────────────────────────────────────────────
-- ADR-2605092000: Ecosystem-as-Model unified FP8 vector substrate
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_organism_embedding (
  vertex_id        varchar PRIMARY KEY,              -- {entity_kind}:{entity_id}:{modality}
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 100,
  owner_did        varchar,
  entity_kind      varchar NOT NULL,                 -- cell|leaf|branch|fruit|flower|tool|plasmid|prion|karma_edge|human|org|external|adapter
  entity_id        varchar NOT NULL,
  modality         varchar NOT NULL,                 -- text|code|image|audio|bpmn|struct|graph|action|adapter
  vec_fp8          bytea,                            -- D bytes E4M3
  vec_dim          bigint,                            -- D
  scale            real,                              -- per-row dequant scale
  generation       bigint DEFAULT 0,
  trained_until    varchar,
  provenance_cid   varchar,                           -- IPFS witness
  created_at       varchar,
  updated_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_organism_embedding_lookup ON vertex_organism_embedding (entity_kind, entity_id, modality);
CREATE INDEX IF NOT EXISTS idx_organism_embedding_modality ON vertex_organism_embedding (modality, generation);

-- vertex_model_checkpoint pre-exists from prior karma/myco migrations with a
-- different shape (eval_wellbecoming / eval_eta / train_loss / deployed_*).
-- ADR-2605092000 extends it with FP8 model lineage columns via ALTER TABLE.
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS checkpoint_cid varchar;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS parent_cid varchar;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS fp8_format varchar;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS param_count bigint;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS cohort_did varchar;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS pruning_rate double precision;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS fruit_accept_rate double precision;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS karma_safety double precision;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS mutation_acceptance_rate double precision;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS lean_verified boolean;
ALTER TABLE vertex_model_checkpoint ADD COLUMN IF NOT EXISTS ipfs_pinned_layers varchar;

-- ─────────────────────────────────────────────────────────────────────────
-- ADR-2605092400: Tool / substrate / cohort / modality routing weight
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_router_weight (
  vertex_id        varchar PRIMARY KEY,               -- {cell_did}:{target_kind}:{target_id}
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 100,
  owner_did        varchar,
  cell_did         varchar NOT NULL,
  target_kind      varchar NOT NULL,                  -- cell|tool|substrate|modality
  target_id        varchar NOT NULL,
  logit_fp8        smallint,                          -- 1 byte signed
  scale            real,
  hyperparam_json  varchar,                           -- {lambda, mu, gamma, delta, temp}
  updated_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_router_weight_cell ON vertex_router_weight (cell_did, target_kind);
CREATE INDEX IF NOT EXISTS idx_router_weight_target ON vertex_router_weight (target_kind, target_id);

-- ─────────────────────────────────────────────────────────────────────────
-- ADR-2605092200: Continuous metabolic training signal
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_gradient_flow (
  edge_id          varchar PRIMARY KEY,                -- content-addressed
  src_vid          varchar NOT NULL,                   -- source entity vertex_id
  dst_vid          varchar NOT NULL,                   -- destination cell/branch/cohort
  relation_kind    varchar NOT NULL DEFAULT 'gradient_flow',
  signal_kind      varchar NOT NULL,                   -- water-grant|fruit-accept|fruit-cull|branch-prune|leaf-defoliate|karma-eval|mutate-permit|consume|spore-spread
  src_entity       varchar NOT NULL,
  dst_entity       varchar NOT NULL,
  magnitude_fp8    smallint,                           -- 1 byte signed
  scale            real,
  reward_sign      smallint,                           -- +1 / 0 / -1 / -127 (floor sentinel)
  modality_tag     varchar,
  attribution_json varchar,                            -- shapley-lite attribution map
  flowed_at        varchar,
  owner_did        varchar,
  sensitivity_ord  bigint DEFAULT 100
);
CREATE INDEX IF NOT EXISTS idx_gradient_flow_dst ON edge_gradient_flow (dst_entity, flowed_at);
CREATE INDEX IF NOT EXISTS idx_gradient_flow_signal ON edge_gradient_flow (signal_kind, flowed_at);
CREATE INDEX IF NOT EXISTS idx_gradient_flow_reward ON edge_gradient_flow (reward_sign, flowed_at);

-- ─────────────────────────────────────────────────────────────────────────
-- Streaming MV (small + safe — single GROUP BY on bounded keys)
-- ─────────────────────────────────────────────────────────────────────────

-- Pruning rate per cohort (last 24h proxy via simple aggregate)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bonsai_pruning_rate AS
SELECT
  fruit.cohort_did                                      AS cohort_did,
  COUNT(prune.edge_id)                                  AS prune_count,
  COUNT(DISTINCT fruit.fruit_id)                        AS fruit_total
FROM vertex_yoro_fruit fruit
LEFT JOIN edge_yoro_prune prune
  ON prune.target_kind = 'fruit' AND prune.target_id = fruit.fruit_id
GROUP BY fruit.cohort_did;

-- Watering inflow per cohort (rollup, bounded by cohort cardinality)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bonsai_water_inflow AS
SELECT
  target_did                                             AS cohort_did,
  kind,
  COUNT(*)                                               AS grant_count,
  SUM(amount)                                            AS amount_total
FROM edge_bonsai_water
GROUP BY 1, 2;

-- Gradient signal rollup per (signal_kind, dst_entity sample)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gradient_flow_rollup AS
SELECT
  signal_kind,
  reward_sign,
  COUNT(*)                                               AS event_count
FROM edge_gradient_flow
GROUP BY 1, 2;
