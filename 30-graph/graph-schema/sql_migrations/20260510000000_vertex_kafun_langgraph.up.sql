-- ADR-2605080600 / 2605082000 — kafun-bokumetsu LangGraph migration
--
-- 1. T2 domain tables (ADR-0036 Hyperdrive direct write target):
--      vertex_kafun_research   — researcher actor output
--      vertex_kafun_insight    — proposer  actor output (synthesis)
--      vertex_kafun_proposal   — proposer  actor output (action drafts)
--      vertex_kafun_action     — executor  actor output (dispatched action log)
--
-- 2. LangGraph registry seed:
--      vertex_langgraph_assistant   × 3  (kafun.research.v1 / think.v1 / tick.v1)
--      vertex_langgraph_deployment  × 3  (status='active')
--      vertex_bpmn_lexicon_binding  × 3  (routing_target='langgraph')
--
-- Path-based actor DIDs (ADR-0019, persisted by Worker via sdk.did.create on first request):
--   did:web:n97ik10n.etzhayyim.com:actor:researcher
--   did:web:n97ik10n.etzhayyim.com:actor:proposer
--   did:web:n97ik10n.etzhayyim.com:actor:executor
--
-- Persistence model: record-log semantics (PK re-INSERT = implicit upsert; no ON CONFLICT, no UPDATE).
-- RisingWave: no JSONB; JSON arrays stored as VARCHAR.

-- ─────────────────────────────────────────────────────────────────────────
-- T2 domain tables
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_kafun_research (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  actor_did        varchar NOT NULL,
  category         varchar NOT NULL,
  title            varchar,
  summary          varchar,
  evidence         varchar,
  confidence       double precision DEFAULT 0.5,
  created_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_kafun_research_actor    ON vertex_kafun_research (actor_did, created_at);
CREATE INDEX IF NOT EXISTS idx_kafun_research_category ON vertex_kafun_research (category, created_at);

CREATE TABLE IF NOT EXISTS vertex_kafun_insight (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  actor_did        varchar NOT NULL,
  summary          varchar,
  rationale        varchar,
  source_finding_ids varchar,        -- JSON array of vertex_id (research findings)
  created_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_kafun_insight_actor ON vertex_kafun_insight (actor_did, created_at);

CREATE TABLE IF NOT EXISTS vertex_kafun_proposal (
  vertex_id           varchar PRIMARY KEY,
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 0,
  owner_did           varchar,
  actor_did           varchar NOT NULL,
  from_insight_id     varchar,
  title               varchar,
  action_type         varchar NOT NULL,    -- research|policy|tech|fund_spend|public_post
  estimated_cost_jpy  bigint DEFAULT 0,
  expected_impact     varchar,
  priority            bigint DEFAULT 3,    -- 1 = highest .. 5 = lowest
  status              varchar DEFAULT 'draft',  -- draft|dispatched|done|cancelled
  created_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_kafun_proposal_status   ON vertex_kafun_proposal (status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_kafun_proposal_insight  ON vertex_kafun_proposal (from_insight_id);

CREATE TABLE IF NOT EXISTS vertex_kafun_action (
  vertex_id           varchar PRIMARY KEY,
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 0,
  owner_did           varchar,
  actor_did           varchar NOT NULL,
  from_proposal_id    varchar NOT NULL,
  action_type         varchar NOT NULL,
  cost_jpy            bigint DEFAULT 0,
  status              varchar DEFAULT 'dispatched',  -- dispatched|completed|failed
  dispatch_hint       varchar,                       -- JSON object {transport, graph|method|lexicon}
  created_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_kafun_action_proposal ON vertex_kafun_action (from_proposal_id);
CREATE INDEX IF NOT EXISTS idx_kafun_action_status   ON vertex_kafun_action (status, created_at);

-- ─────────────────────────────────────────────────────────────────────────
-- LangGraph registry seed
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, description, created_at)
VALUES
  ('kafun.research.v1', 0, 0, 'kafun.research.v1', 1, 'py_factory',
   'pymagatama.langgraph_graphs.kafun_research', 'kafun-bokumetsu researcher actor', '2026-05-10T00:00:00Z'),
  ('kafun.think.v1',    0, 0, 'kafun.think.v1',    1, 'py_factory',
   'pymagatama.langgraph_graphs.kafun_think',    'kafun-bokumetsu proposer actor',   '2026-05-10T00:00:00Z'),
  ('kafun.tick.v1',     0, 0, 'kafun.tick.v1',     1, 'py_factory',
   'pymagatama.langgraph_graphs.kafun_tick',     'kafun-bokumetsu executor actor',   '2026-05-10T00:00:00Z');

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at)
VALUES
  ('langgraph.kafun.research.v1', 0, 0, 'com.etzhayyim.apps.kafun.agent.research',
   'kafun.research.v1', 1, 'active', 1, '2026-05-10T00:00:00Z'),
  ('langgraph.kafun.think.v1',    0, 0, 'com.etzhayyim.apps.kafun.agent.think',
   'kafun.think.v1',    1, 'active', 1, '2026-05-10T00:00:00Z'),
  ('langgraph.kafun.tick.v1',     0, 0, 'com.etzhayyim.apps.kafun.agent.tick',
   'kafun.tick.v1',     1, 'active', 1, '2026-05-10T00:00:00Z');

-- bpmn-dispatcher → langgraph routing (NSID → assistant_id).
INSERT INTO vertex_bpmn_lexicon_binding
  (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
   result_timeout_ms, status, created_at, sensitivity_ord,
   org_id, user_id, actor_id, routing_target)
VALUES
  ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kafun-research-langgraph-v1',
   'did:web:bpmn.etzhayyim.com', 'com.etzhayyim.apps.kafun.agent.research',
   'kafun.research.v1', 1, CAST(180000 AS integer), 'active',
   '2026-05-10T00:00:00Z', 1,
   'did:web:bpmn.etzhayyim.com', 'did:web:bpmn.etzhayyim.com', 'did:web:bpmn.etzhayyim.com', 'langgraph'),
  ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kafun-think-langgraph-v1',
   'did:web:bpmn.etzhayyim.com', 'com.etzhayyim.apps.kafun.agent.think',
   'kafun.think.v1', 1, CAST(180000 AS integer), 'active',
   '2026-05-10T00:00:00Z', 1,
   'did:web:bpmn.etzhayyim.com', 'did:web:bpmn.etzhayyim.com', 'did:web:bpmn.etzhayyim.com', 'langgraph'),
  ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kafun-tick-langgraph-v1',
   'did:web:bpmn.etzhayyim.com', 'com.etzhayyim.apps.kafun.agent.tick',
   'kafun.tick.v1', 1, CAST(180000 AS integer), 'active',
   '2026-05-10T00:00:00Z', 1,
   'did:web:bpmn.etzhayyim.com', 'did:web:bpmn.etzhayyim.com', 'did:web:bpmn.etzhayyim.com', 'langgraph');
