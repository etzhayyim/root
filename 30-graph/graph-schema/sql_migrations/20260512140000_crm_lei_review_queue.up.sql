-- CRM LEI manual review queue.
--
-- Holds unresolved CRM legal names and ambiguous/manual LEI candidates so
-- LangGraph agents can interrupt for human review without mutating verified
-- CRM links prematurely.

CREATE TABLE IF NOT EXISTS vertex_crm_lei_review_item (
  vertex_id                   varchar PRIMARY KEY,
  review_id                   varchar NOT NULL,
  crm_system                  varchar NOT NULL,
  crm_entity_type             varchar NOT NULL,
  crm_vertex_id               varchar NOT NULL,
  crm_source_id               varchar,
  crm_legal_name              varchar,
  crm_country                 varchar,
  review_status               varchar NOT NULL DEFAULT 'open',
  review_reason               varchar NOT NULL,
  suggested_action            varchar NOT NULL DEFAULT 'manual_review',
  candidate_count             int DEFAULT 0,
  candidates_json             varchar,
  selected_lei                varchar,
  selected_edge_id            varchar,
  evidence_uri                varchar,
  evidence_note               varchar,
  priority                    int DEFAULT 50,
  assigned_to_did             varchar,
  last_reviewed_at            varchar,
  created_at                  varchar,
  updated_at                  varchar,
  sensitivity_ord             int DEFAULT 200,
  owner_did                   varchar,
  actor_did                   varchar,
  org_did                     varchar
);

CREATE INDEX IF NOT EXISTS idx_crm_lei_review_item_status
  ON vertex_crm_lei_review_item (review_status, priority, updated_at);

CREATE INDEX IF NOT EXISTS idx_crm_lei_review_item_crm
  ON vertex_crm_lei_review_item (crm_system, crm_entity_type, crm_source_id);

CREATE VIEW IF NOT EXISTS view_crm_lei_review_queue AS
SELECT
  q.vertex_id,
  q.review_id,
  q.crm_system,
  q.crm_entity_type,
  q.crm_vertex_id,
  q.crm_source_id,
  q.crm_legal_name,
  q.crm_country,
  q.review_status,
  q.review_reason,
  q.suggested_action,
  q.candidate_count,
  q.candidates_json,
  q.selected_lei,
  q.selected_edge_id,
  q.evidence_uri,
  q.evidence_note,
  q.priority,
  q.assigned_to_did,
  q.last_reviewed_at,
  q.created_at,
  q.updated_at,
  p.lei_match_status AS source_lei_match_status,
  p.lei AS source_lei
FROM vertex_crm_lei_review_item q
LEFT JOIN view_crm_lei_pending_resolution p
  ON p.crm_system = q.crm_system
 AND p.crm_entity_type = q.crm_entity_type
 AND p.crm_vertex_id = q.crm_vertex_id;

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, assistant_id,
   version, kind, factory_path, description, checkpointer_mode, created_at)
SELECT
  'crm_lei_review_loop', 0, DATE '2026-05-12', 200, 'did:web:open-lei.gftd.ai',
  'crm_lei_review_loop', 1, 'py_factory',
  'pymagatama.langgraph_graphs.crm_lei_review_loop',
  'CRM LEI review queue loop: enrich unresolved records, autoreview safe matches, interrupt for manual evidence.',
  'rw_vertex',
  '2026-05-12T14:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_assistant
  WHERE assistant_id = 'crm_lei_review_loop' AND version = 1
);

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, nsid,
   assistant_id, version, status, replicas, updated_at)
SELECT
  'langgraph.builtin.crm_lei_review_loop', 0, DATE '2026-05-12', 200,
  'did:web:open-lei.gftd.ai', 'langgraph.builtin.crm_lei_review_loop',
  'crm_lei_review_loop', 1, 'active', 1, '2026-05-12T14:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_deployment
  WHERE vertex_id = 'langgraph.builtin.crm_lei_review_loop'
);
