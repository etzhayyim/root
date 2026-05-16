-- keiei (経営) C-suite AI role layer — graph projection.
--
-- ADR 2605101200 — AI CXO roles as resident lang-server.
-- Operating entity = amanomibashira (sole principal). Vendor = Gftd Japan.
-- Path-based DIDs (ADR-0019):
--   did:web:keiei.gftd.ai                            — controller
--   did:web:keiei.gftd.ai:role:{role_id}             — role vertex
--   did:web:keiei.gftd.ai:role:{role_id}:agent       — AI agent acting in role
--   did:web:keiei.gftd.ai:role:{role_id}:profile     — public profile (atproto)
--
-- Persistence: ADR-0036 worker-direct Hyperdrive. Decisions are append-only
-- (record-log semantics; PK re-INSERT = implicit upsert; no ON CONFLICT).
--
-- 4 vertex + 4 edge + 2 narrow MV.

-- ─────────────────────────────────────────────────────────────────────────
-- vertex_keiei_role — declarative role spec (CEO/COO/CTO/...)
-- 1 row per role, seeded from pymagatama.keiei.roles.ROLES.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_keiei_role (
  vertex_id            varchar PRIMARY KEY,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  actor_did            varchar NOT NULL,
  org_did              varchar NOT NULL,
  role_id              varchar NOT NULL,                -- "ceo" / "cto" / ...
  title                varchar NOT NULL,
  title_ja             varchar,
  mode                 varchar NOT NULL,                -- "shadow" | "primary"
  human_seat_email     varchar,                          -- NULL = vacant
  human_seat_did       varchar,
  autonomous_classes   varchar,                          -- comma-joined: "C" or "C,D"
  confirm_classes      varchar,                          -- "B"
  escalate_to_emails   varchar NOT NULL,                  -- comma-joined
  financial_action_gated bigint DEFAULT 0,
  payroll_gated        bigint DEFAULT 0,
  scope               varchar,                            -- short responsibility statement
  kpis                varchar,                            -- comma-joined KPI ids
  reports_to_role_id   varchar,                           -- e.g. cmo→coo, cto→ceo
  notes               varchar,
  created_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_keiei_role_role_id   ON vertex_keiei_role (role_id);
CREATE INDEX IF NOT EXISTS idx_keiei_role_mode      ON vertex_keiei_role (mode);
CREATE INDEX IF NOT EXISTS idx_keiei_role_human     ON vertex_keiei_role (human_seat_email);

-- ─────────────────────────────────────────────────────────────────────────
-- vertex_keiei_agent — concrete AI agent instance bound to a role
-- 1 row per (role × deployment) — typically 1:1 today, 1:N once HA enabled.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_keiei_agent (
  vertex_id            varchar PRIMARY KEY,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  actor_did            varchar NOT NULL,
  org_did              varchar NOT NULL,
  role_id              varchar NOT NULL,
  agent_did            varchar NOT NULL,                  -- did:web:keiei.gftd.ai:role:cto:agent
  display_name         varchar NOT NULL,
  llm_model_hint       varchar,                            -- resolves via MODEL_REGISTRY
  langgraph_module     varchar,                            -- pymagatama.keiei.graph.cto
  lsp_endpoint         varchar,                            -- unix:/run/keiei.sock or wss://...
  lsp_method_prefix    varchar,                            -- cxo/{role_id}
  shinka_enabled       bigint DEFAULT 0,                   -- joucho cadence opt-in
  status               varchar NOT NULL DEFAULT 'proposed',-- proposed|active|paused|retired
  last_heartbeat_at    varchar,
  spawned_at           varchar,
  retired_at           varchar,
  created_at           varchar
);
CREATE INDEX IF NOT EXISTS idx_keiei_agent_role     ON vertex_keiei_agent (role_id);
CREATE INDEX IF NOT EXISTS idx_keiei_agent_did      ON vertex_keiei_agent (agent_did);
CREATE INDEX IF NOT EXISTS idx_keiei_agent_status   ON vertex_keiei_agent (status);

-- ─────────────────────────────────────────────────────────────────────────
-- vertex_keiei_profile — public-facing profile (atproto profile, ActorCard)
-- 1 row per role. Drives `app.bsky.actor.profile` for the role DID and
-- powers the ActorRegistry entry for cross-app discovery.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_keiei_profile (
  vertex_id            varchar PRIMARY KEY,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  actor_did            varchar NOT NULL,
  org_did              varchar NOT NULL,
  role_id              varchar NOT NULL,
  profile_did          varchar NOT NULL,                  -- did:web:keiei.gftd.ai:role:cto:profile
  handle               varchar,                            -- e.g. cto.keiei.gftd.ai
  display_name         varchar NOT NULL,
  display_name_ja      varchar,
  bio                  varchar NOT NULL,                   -- 1-paragraph public statement
  bio_ja               varchar,
  avatar_url           varchar,
  banner_url           varchar,
  is_bot               bigint DEFAULT 1,                    -- always 1 — these are AI agents
  disclaimer           varchar NOT NULL DEFAULT 'AI agent (operated by amanomibashira through Gftd Japan vendor capacity, ADR 2605101200) — not a fiduciary, not legal authority.',
  pronouns             varchar,                            -- e.g. "they/them" — generic
  manifesto            varchar,                            -- ideal voice / first-principles
  primary_tools        varchar,                            -- comma-joined NSIDs they invoke
  external_visibility  varchar DEFAULT 'public',           -- public|internal|restricted
  created_at           varchar
);
CREATE INDEX IF NOT EXISTS idx_keiei_profile_role   ON vertex_keiei_profile (role_id);
CREATE INDEX IF NOT EXISTS idx_keiei_profile_handle ON vertex_keiei_profile (handle);

-- ─────────────────────────────────────────────────────────────────────────
-- vertex_keiei_decision — append-only ledger row per CXO decision.
-- Mirrors _working/keiei/CXO-LEDGER.md but in graph form. Class A = always
-- escalated; Class B (primary mode) = autonomous + 24h auto-disclose; Class
-- C = autonomous; financial/payroll-gated = pending-confirm.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_keiei_decision (
  vertex_id            varchar PRIMARY KEY,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 2,
  owner_did            varchar,
  actor_did            varchar NOT NULL,
  org_did              varchar NOT NULL,
  decision_id          varchar NOT NULL,                  -- ULID
  role_id              varchar NOT NULL,
  agent_did            varchar,
  decision_class       varchar NOT NULL,                   -- A | B | C | D
  action_kind          varchar,                            -- spend|hire|post|review|...
  status               varchar NOT NULL,                   -- executed|pending-confirm|escalated|denied|confirmed|rejected
  summary              varchar NOT NULL,
  rationale            varchar,                            -- LangGraph trace digest
  artefact_uri         varchar,                            -- at:// or path
  escalated_to_emails  varchar,                            -- comma-joined
  decided_by           varchar,                            -- AI-CTO (acting via j.kawasaki) | escalated
  confirmed_by_email   varchar,                            -- when status=confirmed
  confirmed_at         varchar,
  ledger_seq           bigint,                              -- mirrors CXO-LEDGER.md row id
  decided_at           varchar NOT NULL,
  created_at           varchar
);
CREATE INDEX IF NOT EXISTS idx_keiei_decision_role     ON vertex_keiei_decision (role_id, decided_at);
CREATE INDEX IF NOT EXISTS idx_keiei_decision_class    ON vertex_keiei_decision (decision_class);
CREATE INDEX IF NOT EXISTS idx_keiei_decision_status   ON vertex_keiei_decision (status);
CREATE INDEX IF NOT EXISTS idx_keiei_decision_did      ON vertex_keiei_decision (decision_id);

-- ─────────────────────────────────────────────────────────────────────────
-- edges
-- ─────────────────────────────────────────────────────────────────────────

-- agent ──acts_as──▶ role
CREATE TABLE IF NOT EXISTS edge_keiei_agent_acts_as (
  edge_id              varchar PRIMARY KEY,
  src_vid              varchar NOT NULL,                  -- agent vertex_id
  dst_vid              varchar NOT NULL,                  -- role  vertex_id
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  bound_at             varchar,
  binding_strength     double precision DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_keiei_acts_as_src ON edge_keiei_agent_acts_as (src_vid);
CREATE INDEX IF NOT EXISTS idx_keiei_acts_as_dst ON edge_keiei_agent_acts_as (dst_vid);

-- role ──reports_to──▶ role  (org chart edge: cmo→coo, cto→ceo, etc.)
CREATE TABLE IF NOT EXISTS edge_keiei_reports_to (
  edge_id              varchar PRIMARY KEY,
  src_vid              varchar NOT NULL,
  dst_vid              varchar NOT NULL,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  reporting_kind       varchar                             -- "direct" | "dotted" | "escalation"
);
CREATE INDEX IF NOT EXISTS idx_keiei_reports_to_src ON edge_keiei_reports_to (src_vid);
CREATE INDEX IF NOT EXISTS idx_keiei_reports_to_dst ON edge_keiei_reports_to (dst_vid);

-- role ──has_profile──▶ profile
CREATE TABLE IF NOT EXISTS edge_keiei_role_has_profile (
  edge_id              varchar PRIMARY KEY,
  src_vid              varchar NOT NULL,
  dst_vid              varchar NOT NULL,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar
);
CREATE INDEX IF NOT EXISTS idx_keiei_has_profile_src ON edge_keiei_role_has_profile (src_vid);

-- decision ──made_by──▶ agent  (audit chain)
CREATE TABLE IF NOT EXISTS edge_keiei_decision_made_by (
  edge_id              varchar PRIMARY KEY,
  src_vid              varchar NOT NULL,                  -- decision vertex_id
  dst_vid              varchar NOT NULL,                  -- agent vertex_id
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 2,
  owner_did            varchar,
  decision_class       varchar
);
CREATE INDEX IF NOT EXISTS idx_keiei_decision_made_by_src ON edge_keiei_decision_made_by (src_vid);
CREATE INDEX IF NOT EXISTS idx_keiei_decision_made_by_dst ON edge_keiei_decision_made_by (dst_vid);

-- ─────────────────────────────────────────────────────────────────────────
-- materialized views — narrow only (per MV memory safety guardrail)
-- ─────────────────────────────────────────────────────────────────────────

-- mv_keiei_decision_count_by_role — small (≤9 roles × 4 classes × ~6 statuses)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_keiei_decision_count_by_role AS
SELECT
  role_id,
  decision_class,
  status,
  COUNT(*) AS decision_count
FROM vertex_keiei_decision
GROUP BY role_id, decision_class, status;

-- mv_keiei_role_active_agent — DISTINCT ON role_id, latest active agent
-- (small: at most 1 row per role; safe streaming agg)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_keiei_role_active_agent AS
SELECT
  role_id,
  MAX(agent_did)         AS active_agent_did,
  MAX(last_heartbeat_at) AS last_heartbeat_at
FROM vertex_keiei_agent
WHERE status = 'active'
GROUP BY role_id;

FLUSH;
