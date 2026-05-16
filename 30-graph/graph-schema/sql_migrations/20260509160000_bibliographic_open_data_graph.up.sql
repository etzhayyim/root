-- Global bibliographic open data graph.
--
-- Scope:
--   - public/library catalogue sources such as NDL, LOC, BnF, DNB, Trove,
--     NLC, RSL/NLR, NLAI, Europeana, and similar official services.
--   - raw source records plus normalized property-graph vertices and edges.
--
-- Base tables are Alembic-owned. Rebuildable search/coverage/quality views
-- live in SQLMesh.

CREATE TABLE IF NOT EXISTS vertex_biblio_source (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  source_id varchar NOT NULL,
  country_code varchar,
  country_name varchar,
  institution_name varchar NOT NULL,
  service_name varchar NOT NULL,
  base_url varchar,
  api_base_url varchar,
  access_protocols varchar,
  metadata_formats varchar,
  rights_note varchar,
  machine_readability varchar,
  geopolitical_group varchar,
  status varchar NOT NULL,
  discovered_at varchar,
  updated_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_source_source_id
  ON vertex_biblio_source (source_id);

CREATE INDEX IF NOT EXISTS idx_biblio_source_country
  ON vertex_biblio_source (country_code, geopolitical_group);

CREATE TABLE IF NOT EXISTS vertex_biblio_raw_record (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  source_id varchar NOT NULL,
  source_record_id varchar NOT NULL,
  harvest_run_id varchar,
  protocol varchar,
  record_schema varchar,
  content_type varchar,
  raw_payload varchar,
  raw_sha256 varchar,
  fetched_at varchar,
  source_updated_at varchar,
  status varchar NOT NULL,
  error varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_raw_source_record
  ON vertex_biblio_raw_record (source_id, source_record_id);

CREATE INDEX IF NOT EXISTS idx_biblio_raw_sha
  ON vertex_biblio_raw_record (raw_sha256);

CREATE TABLE IF NOT EXISTS vertex_biblio_entity (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  entity_type varchar NOT NULL,
  canonical_label varchar NOT NULL,
  original_label varchar,
  normalized_label varchar,
  language varchar,
  country_code varchar,
  publication_year int,
  source_id varchar,
  source_record_id varchar,
  source_url varchar,
  metadata_json varchar,
  confidence double precision,
  status varchar NOT NULL,
  created_at varchar,
  updated_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_entity_type_label
  ON vertex_biblio_entity (entity_type, normalized_label);

CREATE INDEX IF NOT EXISTS idx_biblio_entity_source
  ON vertex_biblio_entity (source_id, source_record_id);

CREATE INDEX IF NOT EXISTS idx_biblio_entity_year
  ON vertex_biblio_entity (publication_year);

CREATE TABLE IF NOT EXISTS vertex_biblio_identifier (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  identifier_scheme varchar NOT NULL,
  identifier_value varchar NOT NULL,
  normalized_value varchar NOT NULL,
  entity_vertex_id varchar,
  source_id varchar,
  status varchar NOT NULL,
  created_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_identifier_lookup
  ON vertex_biblio_identifier (identifier_scheme, normalized_value);

CREATE TABLE IF NOT EXISTS edge_biblio_relation (
  edge_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  src_vertex_id varchar NOT NULL,
  dst_vertex_id varchar NOT NULL,
  relation_type varchar NOT NULL,
  source_id varchar,
  source_record_id varchar,
  confidence double precision,
  evidence_json varchar,
  status varchar NOT NULL,
  created_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_edge_src
  ON edge_biblio_relation (src_vertex_id, relation_type);

CREATE INDEX IF NOT EXISTS idx_biblio_edge_dst
  ON edge_biblio_relation (dst_vertex_id, relation_type);

CREATE TABLE IF NOT EXISTS vertex_biblio_ingest_cursor (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  source_id varchar NOT NULL,
  query_key varchar NOT NULL,
  cursor_value varchar,
  last_run_id varchar,
  status varchar NOT NULL,
  updated_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_cursor_source_query
  ON vertex_biblio_ingest_cursor (source_id, query_key);

CREATE TABLE IF NOT EXISTS vertex_biblio_ingest_run (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  run_id varchar NOT NULL,
  source_id varchar NOT NULL,
  protocol varchar,
  query_key varchar,
  cursor_start varchar,
  cursor_end varchar,
  raw_records_seen int,
  raw_records_inserted int,
  entities_inserted int,
  identifiers_inserted int,
  edges_inserted int,
  status varchar NOT NULL,
  error varchar,
  started_at varchar,
  finished_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_ingest_run_source
  ON vertex_biblio_ingest_run (source_id, started_at);

GRANT SELECT, INSERT, UPDATE ON vertex_biblio_source TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_biblio_raw_record TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_biblio_entity TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_biblio_identifier TO root;
GRANT SELECT, INSERT, UPDATE ON edge_biblio_relation TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_biblio_ingest_cursor TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_biblio_ingest_run TO root;

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, assistant_id,
   version, kind, factory_path, description, created_at)
VALUES
  ('biblio_open_data_ingest', 0, DATE '2026-05-09', 2, 'did:web:biblio.gftd.ai',
   'biblio_open_data_ingest', 1, 'py_factory',
   'pymagatama.langgraph_graphs.biblio_open_data_ingest',
   'Global national-library/open bibliographic source ingest graph',
   '2026-05-09T16:00:00Z');

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, nsid,
   assistant_id, version, status, replicas, updated_at)
VALUES
  ('langgraph.builtin.biblio_open_data_ingest', 0, DATE '2026-05-09', 2,
   'did:web:biblio.gftd.ai', 'langgraph.builtin.biblio_open_data_ingest',
   'biblio_open_data_ingest', 1, 'active', 1, '2026-05-09T16:00:00Z');
