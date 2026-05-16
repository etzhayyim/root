-- ADR-2605080600 amendment — RW-resident LangGraph assistant deployment SSoT.
-- Stores assistant topology (graph_def) + node bindings + active deployment pin.
-- Deploy = INSERT row; rollback = re-INSERT prior row (PK implicit upsert).
--
-- v1 scope: kind='py_factory' only (existing build_graph() factories).
-- Topology JSON schema reserved for v2 (kind='topology' + node bindings).
--
-- Naming follows LangGraph wire vocabulary (assistant_id) — matches
-- vertex_langgraph_run.assistant_id and the /assistants /runs API surface.

CREATE TABLE IF NOT EXISTS vertex_langgraph_assistant (
  vertex_id        varchar PRIMARY KEY,        -- = assistant_id
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  assistant_id     varchar NOT NULL,
  version          bigint NOT NULL DEFAULT 1,
  kind             varchar NOT NULL DEFAULT 'py_factory',  -- py_factory | topology (v2)
  factory_path     varchar,                     -- dotted path to module exposing build_graph()
  spec             varchar,                     -- topology JSON (v2)
  description      varchar,
  created_at       varchar
);

CREATE INDEX IF NOT EXISTS idx_langgraph_assistant_id
  ON vertex_langgraph_assistant (assistant_id);

-- Per-node binding for kind='topology' (v2). Empty for v1 py_factory rows.
CREATE TABLE IF NOT EXISTS vertex_langgraph_assistant_node (
  vertex_id        varchar PRIMARY KEY,        -- = assistant_id || ':' || node_id
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  assistant_id     varchar NOT NULL,
  node_id          varchar NOT NULL,
  kind             varchar NOT NULL,           -- sql_udf | rust_udf | py_ext_udf | py_primitive | mcp_tool | llm
  ref              varchar NOT NULL,           -- dotted path / UDF name / tool URI / model id
  config           varchar,                    -- JSON
  created_at       varchar
);

CREATE INDEX IF NOT EXISTS idx_langgraph_assistant_node_aid
  ON vertex_langgraph_assistant_node (assistant_id);

-- Active version pin. PK = nsid → re-INSERT overwrites (RW implicit upsert).
-- Rollback = re-INSERT prior row. No UPDATE WHERE.
CREATE TABLE IF NOT EXISTS vertex_langgraph_deployment (
  vertex_id        varchar PRIMARY KEY,        -- = nsid
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  nsid             varchar NOT NULL,
  assistant_id     varchar NOT NULL,
  version          bigint NOT NULL DEFAULT 1,
  status           varchar NOT NULL DEFAULT 'active',  -- active | disabled
  replicas         bigint DEFAULT 1,
  updated_at       varchar
);

CREATE INDEX IF NOT EXISTS idx_langgraph_deployment_status
  ON vertex_langgraph_deployment (status, nsid);
