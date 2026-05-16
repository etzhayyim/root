-- CRM ↔ Open LEI bridge.
--
-- Connects Salesforce/HubSpot-style CRM surfaces to the existing GLEIF
-- master (`vertex_open_lei_entity`) without duplicating legal-entity rows.
-- Writes remain explicit: resolvers insert `edge_crm_open_lei_match`; views
-- only expose pending/linked state for operators and agents.

ALTER TABLE vertex_lawfirm_lead ADD COLUMN IF NOT EXISTS legal_entity_name varchar;
ALTER TABLE vertex_lawfirm_lead ADD COLUMN IF NOT EXISTS lei varchar;
ALTER TABLE vertex_lawfirm_lead ADD COLUMN IF NOT EXISTS lei_match_status varchar DEFAULT 'unresolved';
ALTER TABLE vertex_lawfirm_lead ADD COLUMN IF NOT EXISTS lei_match_confidence_permille int;
ALTER TABLE vertex_lawfirm_lead ADD COLUMN IF NOT EXISTS lei_verified_at varchar;

ALTER TABLE vertex_lawfirm_tenant ADD COLUMN IF NOT EXISTS lei varchar;
ALTER TABLE vertex_lawfirm_tenant ADD COLUMN IF NOT EXISTS lei_match_status varchar DEFAULT 'unresolved';
ALTER TABLE vertex_lawfirm_tenant ADD COLUMN IF NOT EXISTS lei_match_confidence_permille int;
ALTER TABLE vertex_lawfirm_tenant ADD COLUMN IF NOT EXISTS lei_verified_at varchar;

ALTER TABLE vertex_hubspot_company ADD COLUMN IF NOT EXISTS lei varchar;
ALTER TABLE vertex_hubspot_company ADD COLUMN IF NOT EXISTS lei_match_status varchar DEFAULT 'unresolved';
ALTER TABLE vertex_hubspot_company ADD COLUMN IF NOT EXISTS lei_match_confidence_permille int;
ALTER TABLE vertex_hubspot_company ADD COLUMN IF NOT EXISTS lei_verified_at varchar;

CREATE INDEX IF NOT EXISTS idx_lawfirm_lead_lei
  ON vertex_lawfirm_lead (lei);
CREATE INDEX IF NOT EXISTS idx_lawfirm_lead_lei_status
  ON vertex_lawfirm_lead (lei_match_status, target_country);
CREATE INDEX IF NOT EXISTS idx_lawfirm_tenant_lei
  ON vertex_lawfirm_tenant (lei);
CREATE INDEX IF NOT EXISTS idx_hubspot_company_lei
  ON vertex_hubspot_company (lei);
CREATE INDEX IF NOT EXISTS idx_hubspot_company_lei_status
  ON vertex_hubspot_company (lei_match_status, country);

CREATE TABLE IF NOT EXISTS edge_crm_open_lei_match (
  edge_id                     varchar PRIMARY KEY,
  src_vid                     varchar NOT NULL,
  dst_vid                     varchar NOT NULL,
  crm_system                  varchar NOT NULL,
  crm_entity_type             varchar NOT NULL,
  crm_source_table            varchar NOT NULL,
  crm_source_id               varchar,
  lei                         varchar NOT NULL,
  match_method                varchar NOT NULL,
  match_status                varchar NOT NULL DEFAULT 'candidate',
  confidence_permille         int DEFAULT 0,
  crm_legal_name              varchar,
  lei_legal_name              varchar,
  crm_country                 varchar,
  lei_country                 varchar,
  evidence_uri                varchar,
  evidence_note               varchar,
  verified_at                 varchar,
  expires_at                  varchar,
  created_at                  varchar,
  sensitivity_ord             int DEFAULT 200,
  owner_did                   varchar,
  actor_did                   varchar,
  org_did                     varchar
);

CREATE INDEX IF NOT EXISTS idx_crm_open_lei_match_src
  ON edge_crm_open_lei_match (src_vid);
CREATE INDEX IF NOT EXISTS idx_crm_open_lei_match_lei
  ON edge_crm_open_lei_match (lei);
CREATE INDEX IF NOT EXISTS idx_crm_open_lei_match_status
  ON edge_crm_open_lei_match (crm_system, crm_entity_type, match_status);

CREATE TABLE IF NOT EXISTS vertex_crm_lei_resolution_run (
  vertex_id                   varchar PRIMARY KEY,
  run_id                      varchar NOT NULL,
  crm_system                  varchar NOT NULL,
  crm_entity_type             varchar,
  resolver_kind               varchar NOT NULL,
  input_count                 int DEFAULT 0,
  candidate_count             int DEFAULT 0,
  verified_count              int DEFAULT 0,
  rejected_count              int DEFAULT 0,
  status                      varchar NOT NULL DEFAULT 'planned',
  started_at                  varchar,
  completed_at                varchar,
  error                       varchar,
  created_at                  varchar,
  sensitivity_ord             int DEFAULT 200,
  owner_did                   varchar,
  actor_did                   varchar,
  org_did                     varchar
);

CREATE VIEW IF NOT EXISTS view_crm_lei_pending_resolution AS
SELECT
  'lawfirm' AS crm_system,
  'lead' AS crm_entity_type,
  vertex_id AS crm_vertex_id,
  lead_id AS crm_source_id,
  COALESCE(legal_entity_name, target_name) AS legal_name,
  target_country AS country,
  lei,
  COALESCE(lei_match_status, 'unresolved') AS lei_match_status,
  last_touch_at AS last_seen_at
FROM vertex_lawfirm_lead
WHERE COALESCE(lei_match_status, 'unresolved') IN ('unresolved', 'candidate', 'stale')
UNION ALL
SELECT
  'lawfirm' AS crm_system,
  'tenant' AS crm_entity_type,
  vertex_id AS crm_vertex_id,
  tenant_id AS crm_source_id,
  legal_name,
  country,
  lei,
  COALESCE(lei_match_status, 'unresolved') AS lei_match_status,
  provisioned_at AS last_seen_at
FROM vertex_lawfirm_tenant
WHERE COALESCE(lei_match_status, 'unresolved') IN ('unresolved', 'candidate', 'stale')
UNION ALL
SELECT
  'hubspot' AS crm_system,
  'company' AS crm_entity_type,
  vertex_id AS crm_vertex_id,
  hubspot_id AS crm_source_id,
  name AS legal_name,
  country,
  lei,
  COALESCE(lei_match_status, 'unresolved') AS lei_match_status,
  hs_lastmodified_at AS last_seen_at
FROM vertex_hubspot_company
WHERE COALESCE(lei_match_status, 'unresolved') IN ('unresolved', 'candidate', 'stale');

CREATE VIEW IF NOT EXISTS view_crm_lei_linked_entity AS
SELECT
  e.edge_id,
  e.crm_system,
  e.crm_entity_type,
  e.crm_source_table,
  e.crm_source_id,
  e.src_vid AS crm_vertex_id,
  e.dst_vid AS lei_vertex_id,
  e.lei,
  e.match_method,
  e.match_status,
  e.confidence_permille,
  e.crm_legal_name,
  le.legal_name AS gleif_legal_name,
  e.crm_country,
  le.country AS gleif_country,
  le.registration_status,
  le.status AS lei_lifecycle_status,
  le.next_renewal_at,
  e.verified_at,
  e.expires_at
FROM edge_crm_open_lei_match e
JOIN vertex_open_lei_entity le ON le.vertex_id = e.dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_crm_lei_coverage AS
SELECT
  crm_system,
  crm_entity_type,
  match_status,
  COUNT(*) AS link_count,
  MAX(verified_at) AS latest_verified_at
FROM edge_crm_open_lei_match
GROUP BY crm_system, crm_entity_type, match_status;
