-- ADR-2605101000 §D1 / §"Adapter Catalog (initial)" — P2 target vertex tables.
--
-- One vertex table per `edge_dataset_produces_vertex_type.target_vertex_label`
-- referenced by the Tier 1 binding decisions in
-- `/tmp/bq-allowlist/tier1-bindings.json`. The crypto family bind into two
-- shared tables (block + tx) keyed on `chain_id`; the taxi family binds
-- both NYC and Chicago datasets to a single `vertex_taxi_trip` table keyed
-- on `vendor` + `city`.
--
-- Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
-- no ON CONFLICT. PK re-INSERT = implicit upsert. Append-only.
--
-- Sensitivity: all default Tier 1 (`sensitivity_ord = 1`) — BigQuery public
-- data only. Per-table PII review still gates training corpus inclusion
-- via `edge_dataset_allowed_for_training_task` per ADR §"Acceptance Criteria".
--
-- ── vertex_air_quality_observation ──────────────────────────────────────
-- ADR §"Adapter Catalog (initial)" Tier 1 — epa_historical_air_quality
CREATE TABLE IF NOT EXISTS vertex_air_quality_observation (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 1,
  owner_did          varchar,
  source_dataset_id  varchar NOT NULL,
  state_code         varchar,
  county_code        varchar,
  site_num           varchar,
  parameter_code     varchar,
  parameter_name     varchar,
  date_local         varchar,
  arithmetic_mean    double precision,
  units_of_measure   varchar,
  latitude           double precision,
  longitude          double precision,
  observation_count  bigint,
  props              varchar,
  actor_did          varchar NOT NULL DEFAULT 'anon',
  org_did            varchar NOT NULL DEFAULT 'anon',
  at_did             varchar,
  created_at         varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_air_quality_site ON vertex_air_quality_observation (state_code, county_code, site_num, date_local);
CREATE INDEX IF NOT EXISTS idx_air_quality_parameter ON vertex_air_quality_observation (parameter_code, date_local);
CREATE INDEX IF NOT EXISTS idx_air_quality_geo ON vertex_air_quality_observation (latitude, longitude);

-- ── vertex_taxi_trip ────────────────────────────────────────────────────
-- Shared by new_york_taxi_trips + chicago_taxi_trips
CREATE TABLE IF NOT EXISTS vertex_taxi_trip (
  vertex_id           varchar PRIMARY KEY,
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 1,
  owner_did           varchar,
  source_dataset_id   varchar NOT NULL,
  city                varchar,
  vendor              varchar,
  pickup_datetime     varchar,
  dropoff_datetime    varchar,
  passenger_count     bigint,
  trip_distance_m     bigint,
  pickup_latitude     double precision,
  pickup_longitude    double precision,
  dropoff_latitude    double precision,
  dropoff_longitude   double precision,
  fare_amount_minor   bigint,
  tip_amount_minor    bigint,
  total_amount_minor  bigint,
  currency            varchar,
  payment_type        varchar,
  trip_id             varchar,
  props               varchar,
  actor_did           varchar NOT NULL DEFAULT 'anon',
  org_did             varchar NOT NULL DEFAULT 'anon',
  at_did              varchar,
  created_at          varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_taxi_city_pickup ON vertex_taxi_trip (city, pickup_datetime);
CREATE INDEX IF NOT EXISTS idx_taxi_trip_id ON vertex_taxi_trip (trip_id);

-- ── vertex_qa_post ──────────────────────────────────────────────────────
-- stackoverflow (CC-BY-SA-4.0 — ShareAlike propagates downstream)
CREATE TABLE IF NOT EXISTS vertex_qa_post (
  vertex_id            varchar PRIMARY KEY,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  source_dataset_id    varchar NOT NULL,
  community            varchar,
  post_type            varchar,
  post_id              varchar NOT NULL,
  parent_post_id       varchar,
  accepted_answer_id   varchar,
  title                varchar,
  body_text_uri        varchar,
  body_text_sha256     varchar,
  body_byte_size       bigint,
  score                bigint,
  view_count           bigint,
  answer_count         bigint,
  comment_count        bigint,
  favorite_count       bigint,
  tags                 varchar,
  owner_user_id        varchar,
  posted_at            varchar,
  last_activity_at     varchar,
  last_edit_at         varchar,
  language             varchar,
  license              varchar,
  props                varchar,
  actor_did            varchar NOT NULL DEFAULT 'anon',
  org_did              varchar NOT NULL DEFAULT 'anon',
  at_did               varchar,
  created_at           varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_qa_post_community_id ON vertex_qa_post (community, post_id);
CREATE INDEX IF NOT EXISTS idx_qa_post_parent ON vertex_qa_post (parent_post_id);
CREATE INDEX IF NOT EXISTS idx_qa_post_owner ON vertex_qa_post (owner_user_id);
CREATE INDEX IF NOT EXISTS idx_qa_post_tags ON vertex_qa_post (tags);

-- ── vertex_marine_observation ───────────────────────────────────────────
-- noaa_icoads (international comprehensive ocean-atmosphere data set)
CREATE TABLE IF NOT EXISTS vertex_marine_observation (
  vertex_id           varchar PRIMARY KEY,
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 1,
  owner_did           varchar,
  source_dataset_id   varchar NOT NULL,
  observed_at         varchar,
  year                int,
  month               int,
  day                 int,
  hour                int,
  latitude            double precision,
  longitude            double precision,
  sea_surface_temp_c  double precision,
  air_temp_c          double precision,
  wind_direction_deg  double precision,
  wind_speed_mps      double precision,
  pressure_hpa        double precision,
  platform_id         varchar,
  callsign            varchar,
  country_code        varchar,
  props               varchar,
  actor_did           varchar NOT NULL DEFAULT 'anon',
  org_did             varchar NOT NULL DEFAULT 'anon',
  at_did              varchar,
  created_at          varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_marine_time ON vertex_marine_observation (year, month, day);
CREATE INDEX IF NOT EXISTS idx_marine_geo ON vertex_marine_observation (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_marine_platform ON vertex_marine_observation (platform_id);

-- ── vertex_synthetic_patient ────────────────────────────────────────────
-- cms_synthetic_patient_data_omop — OMOP CDM person + condition surface
CREATE TABLE IF NOT EXISTS vertex_synthetic_patient (
  vertex_id              varchar PRIMARY KEY,
  _seq                   bigint,
  created_date           date,
  sensitivity_ord        bigint DEFAULT 1,
  owner_did              varchar,
  source_dataset_id      varchar NOT NULL,
  person_id              varchar NOT NULL,
  gender_concept_id      bigint,
  year_of_birth          int,
  month_of_birth         int,
  race_concept_id        bigint,
  ethnicity_concept_id   bigint,
  location_id            varchar,
  provider_id            varchar,
  care_site_id           varchar,
  condition_concept_id   bigint,
  drug_concept_id        bigint,
  visit_concept_id       bigint,
  condition_start_date   varchar,
  props                  varchar,
  actor_did              varchar NOT NULL DEFAULT 'anon',
  org_did                varchar NOT NULL DEFAULT 'anon',
  at_did                 varchar,
  created_at             varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_synthetic_person ON vertex_synthetic_patient (person_id);
CREATE INDEX IF NOT EXISTS idx_synthetic_condition ON vertex_synthetic_patient (condition_concept_id);

-- ── vertex_forest_inventory ─────────────────────────────────────────────
-- usfs_fia (US Forest Service Forest Inventory and Analysis)
CREATE TABLE IF NOT EXISTS vertex_forest_inventory (
  vertex_id             varchar PRIMARY KEY,
  _seq                  bigint,
  created_date          date,
  sensitivity_ord       bigint DEFAULT 1,
  owner_did             varchar,
  source_dataset_id     varchar NOT NULL,
  plot_id               varchar NOT NULL,
  state_code            varchar,
  county_code           varchar,
  inventory_year        int,
  latitude              double precision,
  longitude             double precision,
  forest_type_code      varchar,
  stand_age_years       int,
  stand_size_class      varchar,
  ownership_group_code  varchar,
  biomass_dry_kg        double precision,
  carbon_dry_kg         double precision,
  props                 varchar,
  actor_did             varchar NOT NULL DEFAULT 'anon',
  org_did               varchar NOT NULL DEFAULT 'anon',
  at_did                varchar,
  created_at            varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_forest_plot ON vertex_forest_inventory (plot_id);
CREATE INDEX IF NOT EXISTS idx_forest_state_year ON vertex_forest_inventory (state_code, inventory_year);

-- ── vertex_target_evidence ──────────────────────────────────────────────
-- open_targets_platform — gene ↔ disease evidence row
CREATE TABLE IF NOT EXISTS vertex_target_evidence (
  vertex_id            varchar PRIMARY KEY,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  source_dataset_id    varchar NOT NULL,
  evidence_id          varchar NOT NULL,
  target_id            varchar,
  disease_id           varchar,
  datatype_id          varchar,
  datasource_id        varchar,
  score                double precision,
  evidence_origin      varchar,
  literature_pmids     varchar,
  release_year         int,
  props                varchar,
  actor_did            varchar NOT NULL DEFAULT 'anon',
  org_did              varchar NOT NULL DEFAULT 'anon',
  at_did               varchar,
  created_at           varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_target_evidence_target ON vertex_target_evidence (target_id);
CREATE INDEX IF NOT EXISTS idx_target_evidence_disease ON vertex_target_evidence (disease_id);
CREATE INDEX IF NOT EXISTS idx_target_evidence_score ON vertex_target_evidence (datatype_id, score);

-- ── vertex_chemistry_patent ─────────────────────────────────────────────
-- ebi_surechembl — chemistry mention extracted from patent
CREATE TABLE IF NOT EXISTS vertex_chemistry_patent (
  vertex_id            varchar PRIMARY KEY,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  source_dataset_id    varchar NOT NULL,
  schembl_id           varchar NOT NULL,
  patent_id            varchar,
  patent_publication_date varchar,
  chembl_id            varchar,
  inchi_key            varchar,
  smiles               varchar,
  ipc_code             varchar,
  cpc_code             varchar,
  family_id            varchar,
  props                varchar,
  actor_did            varchar NOT NULL DEFAULT 'anon',
  org_did              varchar NOT NULL DEFAULT 'anon',
  at_did               varchar,
  created_at           varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_chempat_inchi ON vertex_chemistry_patent (inchi_key);
CREATE INDEX IF NOT EXISTS idx_chempat_patent ON vertex_chemistry_patent (patent_id);

-- ── vertex_blockchain_block / _tx ───────────────────────────────────────
-- shared across crypto_litecoin, crypto_dogecoin (and future chains).
-- chain_id ∈ {ltc, doge, btc, eth, ...} is the discriminator.
CREATE TABLE IF NOT EXISTS vertex_blockchain_block (
  vertex_id           varchar PRIMARY KEY,
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 1,
  owner_did           varchar,
  source_dataset_id   varchar NOT NULL,
  chain_id            varchar NOT NULL,
  block_height        bigint NOT NULL,
  block_hash          varchar NOT NULL,
  parent_hash         varchar,
  block_time          varchar,
  tx_count            bigint,
  size_bytes          bigint,
  difficulty          double precision,
  reward_satoshis     bigint,
  miner               varchar,
  props               varchar,
  actor_did           varchar NOT NULL DEFAULT 'anon',
  org_did             varchar NOT NULL DEFAULT 'anon',
  at_did              varchar,
  created_at          varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_blockchain_block_chain_height ON vertex_blockchain_block (chain_id, block_height);
CREATE INDEX IF NOT EXISTS idx_blockchain_block_hash ON vertex_blockchain_block (block_hash);
CREATE INDEX IF NOT EXISTS idx_blockchain_block_time ON vertex_blockchain_block (block_time);

CREATE TABLE IF NOT EXISTS vertex_blockchain_tx (
  vertex_id              varchar PRIMARY KEY,
  _seq                   bigint,
  created_date           date,
  sensitivity_ord        bigint DEFAULT 1,
  owner_did              varchar,
  source_dataset_id      varchar NOT NULL,
  chain_id               varchar NOT NULL,
  tx_hash                varchar NOT NULL,
  block_height           bigint,
  block_hash             varchar,
  block_time             varchar,
  input_count            bigint,
  output_count           bigint,
  input_value_satoshis   bigint,
  output_value_satoshis  bigint,
  fee_satoshis           bigint,
  is_coinbase            varchar,
  props                  varchar,
  actor_did              varchar NOT NULL DEFAULT 'anon',
  org_did                varchar NOT NULL DEFAULT 'anon',
  at_did                 varchar,
  created_at             varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_chain_hash ON vertex_blockchain_tx (chain_id, tx_hash);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_block ON vertex_blockchain_tx (chain_id, block_height);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_time ON vertex_blockchain_tx (block_time);

-- ── grants ──────────────────────────────────────────────────────────────
GRANT SELECT, INSERT, UPDATE ON vertex_air_quality_observation TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_air_quality_observation TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_taxi_trip TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_taxi_trip TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_qa_post TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_qa_post TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_marine_observation TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_marine_observation TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_synthetic_patient TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_synthetic_patient TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_forest_inventory TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_forest_inventory TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_target_evidence TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_target_evidence TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_chemistry_patent TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_chemistry_patent TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_blockchain_block TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_blockchain_block TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_blockchain_tx TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_blockchain_tx TO kaisya_app;
