-- HubSpot CRM ingest schema (ADR-0036 Hyperdrive direct write target).
--
-- Source: HubSpot CRM v3 API (`/crm/v3/objects/{object_type}`).
-- Drives 60-apps/etzhayyim-project-hubspot-hb5p0t1n ingest worker
-- (poll every 15 min via R/PT15M timer, filter by lastmodifieddate cursor).
--
-- 8 T2 domain tables:
--   vertex_hubspot_contact
--   vertex_hubspot_company
--   vertex_hubspot_deal
--   vertex_hubspot_ticket
--   vertex_hubspot_owner
--   vertex_hubspot_engagement   (unified call / email / meeting / note / task)
--   vertex_hubspot_line_item
--   vertex_hubspot_product
--
-- 1 sync cursor table:
--   vertex_hubspot_sync_cursor   (per-object-type lastmodifieddate watermark)
--
-- Persistence: record-log semantics (PK re-INSERT = implicit upsert; no
-- ON CONFLICT, no UPDATE — RisingWave append-only).
-- Property fanout: high-frequency promoted columns are typed; remainder
-- carried as `properties_json` (VARCHAR — RisingWave has no JSON type).
-- Floats: HubSpot amounts kept as VARCHAR (decimal string) to avoid
-- AT-Lexicon-incompatible float columns leaking into downstream lexicon.

-- ─────────────────────────────────────────────────────────────────────────
-- contact
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_contact (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  portal_id          varchar,
  email              varchar,
  firstname          varchar,
  lastname           varchar,
  phone              varchar,
  jobtitle           varchar,
  lifecyclestage     varchar,
  lead_status        varchar,
  hubspot_owner_id   varchar,
  company_hubspot_id varchar,
  hs_object_id       varchar,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  hs_lastmodified_at varchar,
  archived           bigint DEFAULT 0,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_contact_email     ON vertex_hubspot_contact (email);
CREATE INDEX IF NOT EXISTS idx_hubspot_contact_hsid      ON vertex_hubspot_contact (hubspot_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_contact_modified  ON vertex_hubspot_contact (hs_lastmodified_at);

-- ─────────────────────────────────────────────────────────────────────────
-- company
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_company (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  portal_id          varchar,
  name               varchar,
  domain             varchar,
  industry           varchar,
  city               varchar,
  country            varchar,
  phone              varchar,
  website            varchar,
  numberofemployees  varchar,
  annualrevenue      varchar,
  lifecyclestage     varchar,
  hubspot_owner_id   varchar,
  hs_object_id       varchar,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  hs_lastmodified_at varchar,
  archived           bigint DEFAULT 0,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_company_domain    ON vertex_hubspot_company (domain);
CREATE INDEX IF NOT EXISTS idx_hubspot_company_hsid      ON vertex_hubspot_company (hubspot_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_company_modified  ON vertex_hubspot_company (hs_lastmodified_at);

-- ─────────────────────────────────────────────────────────────────────────
-- deal
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_deal (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  portal_id          varchar,
  dealname           varchar,
  dealstage          varchar,
  pipeline           varchar,
  amount             varchar,
  currency           varchar,
  closedate          varchar,
  dealtype           varchar,
  hubspot_owner_id   varchar,
  hs_object_id       varchar,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  hs_lastmodified_at varchar,
  hs_is_closed       bigint DEFAULT 0,
  hs_is_closed_won   bigint DEFAULT 0,
  archived           bigint DEFAULT 0,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_deal_stage      ON vertex_hubspot_deal (dealstage);
CREATE INDEX IF NOT EXISTS idx_hubspot_deal_pipeline   ON vertex_hubspot_deal (pipeline);
CREATE INDEX IF NOT EXISTS idx_hubspot_deal_hsid       ON vertex_hubspot_deal (hubspot_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_deal_modified   ON vertex_hubspot_deal (hs_lastmodified_at);

-- ─────────────────────────────────────────────────────────────────────────
-- ticket
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_ticket (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  portal_id          varchar,
  subject            varchar,
  content            varchar,
  hs_pipeline        varchar,
  hs_pipeline_stage  varchar,
  hs_ticket_priority varchar,
  hs_ticket_category varchar,
  source_type        varchar,
  hubspot_owner_id   varchar,
  hs_object_id       varchar,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  hs_lastmodified_at varchar,
  archived           bigint DEFAULT 0,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_ticket_pipeline  ON vertex_hubspot_ticket (hs_pipeline, hs_pipeline_stage);
CREATE INDEX IF NOT EXISTS idx_hubspot_ticket_hsid      ON vertex_hubspot_ticket (hubspot_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_ticket_modified  ON vertex_hubspot_ticket (hs_lastmodified_at);

-- ─────────────────────────────────────────────────────────────────────────
-- owner
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_owner (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  portal_id          varchar,
  email              varchar,
  firstname          varchar,
  lastname           varchar,
  user_id            varchar,
  team_id            varchar,
  archived           bigint DEFAULT 0,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_owner_email   ON vertex_hubspot_owner (email);
CREATE INDEX IF NOT EXISTS idx_hubspot_owner_hsid    ON vertex_hubspot_owner (hubspot_id);

-- ─────────────────────────────────────────────────────────────────────────
-- engagement (unified call / email / meeting / note / task)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_engagement (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  engagement_type    varchar NOT NULL,
  portal_id          varchar,
  hs_object_id       varchar,
  hs_engagement_type varchar,
  hs_timestamp       varchar,
  hubspot_owner_id   varchar,
  hs_body_preview    varchar,
  subject            varchar,
  hs_meeting_title   varchar,
  hs_call_disposition varchar,
  hs_call_duration   varchar,
  hs_email_status    varchar,
  hs_task_status     varchar,
  hs_task_priority   varchar,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  hs_lastmodified_at varchar,
  archived           bigint DEFAULT 0,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_engagement_type     ON vertex_hubspot_engagement (engagement_type, hs_lastmodified_at);
CREATE INDEX IF NOT EXISTS idx_hubspot_engagement_hsid     ON vertex_hubspot_engagement (hubspot_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_engagement_modified ON vertex_hubspot_engagement (hs_lastmodified_at);

-- ─────────────────────────────────────────────────────────────────────────
-- line_item
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_line_item (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  portal_id          varchar,
  name               varchar,
  hs_product_id      varchar,
  quantity           varchar,
  price              varchar,
  amount             varchar,
  currency           varchar,
  hs_recurring_billing_period varchar,
  hs_term_in_months  varchar,
  hs_object_id       varchar,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  hs_lastmodified_at varchar,
  archived           bigint DEFAULT 0,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_line_item_product  ON vertex_hubspot_line_item (hs_product_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_line_item_hsid     ON vertex_hubspot_line_item (hubspot_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_line_item_modified ON vertex_hubspot_line_item (hs_lastmodified_at);

-- ─────────────────────────────────────────────────────────────────────────
-- product
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_product (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  at_did             varchar,
  hubspot_id         varchar NOT NULL,
  portal_id          varchar,
  name               varchar,
  description        varchar,
  price              varchar,
  hs_sku             varchar,
  hs_cost_of_goods_sold varchar,
  hs_recurring_billing_period varchar,
  hs_object_id       varchar,
  hs_created_at      varchar,
  hs_updated_at      varchar,
  hs_lastmodified_at varchar,
  archived           bigint DEFAULT 0,
  properties_json    varchar,
  created_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_product_sku       ON vertex_hubspot_product (hs_sku);
CREATE INDEX IF NOT EXISTS idx_hubspot_product_hsid      ON vertex_hubspot_product (hubspot_id);
CREATE INDEX IF NOT EXISTS idx_hubspot_product_modified  ON vertex_hubspot_product (hs_lastmodified_at);

-- ─────────────────────────────────────────────────────────────────────────
-- sync cursor (per-object-type watermark for incremental ingest)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_hubspot_sync_cursor (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 3,
  owner_did          varchar,
  actor_did          varchar NOT NULL,
  org_did            varchar NOT NULL,
  object_type        varchar NOT NULL,
  portal_id          varchar,
  last_modified_cursor varchar,
  last_run_at        varchar,
  last_run_status    varchar,
  last_run_count     bigint DEFAULT 0,
  last_error         varchar,
  created_at         varchar,
  updated_at         varchar
);
CREATE INDEX IF NOT EXISTS idx_hubspot_sync_cursor_obj ON vertex_hubspot_sync_cursor (object_type, portal_id);

FLUSH;
