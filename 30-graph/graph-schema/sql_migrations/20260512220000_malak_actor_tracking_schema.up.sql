-- Malak threat-actor tracking schema (Phase 2)
-- Adds 5 vertex tables + 4 edge tables + 3 MV + 7 indexes.
-- Idempotent (IF NOT EXISTS) so it can be re-applied.
--
-- Convention follows the existing malak schema:
--   vertex_id = at://did:web:malak.gftd.ai/ai.gftd.apps.malak.<kind>/<rkey>
--   ADR-0095 RLS columns: actor_did, org_did, created_at, created_date, sensitivity_ord, owner_did
--   ADR-0004 / record-log: hard delete only, no _alive flag.

-- ────────────────────────────────────────────────────────────────────
-- 1. vertex_malak_threat_actor — 加害アクター (個人 / リング構成員)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_malak_threat_actor (
  vertex_id            VARCHAR PRIMARY KEY,
  rkey                 VARCHAR,
  repo                 VARCHAR,
  actor_name           VARCHAR,            -- 自称名
  alias                VARCHAR,            -- 別名 / handle
  ring_id              VARCHAR,            -- ring 識別子
  role                 VARCHAR,            -- principal | accomplice | sakura | assistant
  nationality          VARCHAR,
  impersonates         VARCHAR,            -- なりすまし対象の実在人物
  description          VARCHAR,
  confidence           DOUBLE PRECISION,
  tlp                  VARCHAR,
  case_id              VARCHAR,
  source_artifact      VARCHAR,
  created_at           VARCHAR,
  created_date         DATE,
  sensitivity_ord      BIGINT,
  owner_did            VARCHAR,
  actor_did            VARCHAR,
  org_did              VARCHAR
);

-- ────────────────────────────────────────────────────────────────────
-- 2. vertex_malak_bank_account — JP fiat 銀行口座 (mule + victim source)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_malak_bank_account (
  vertex_id            VARCHAR PRIMARY KEY,
  rkey                 VARCHAR,
  repo                 VARCHAR,
  account_kind         VARCHAR,            -- mule | victim_source | unknown
  country              VARCHAR,            -- ISO-3166-1 alpha-2 (JP)
  bank_name            VARCHAR,
  branch_name          VARCHAR,
  account_type         VARCHAR,            -- 普通 | 当座 | 貯蓄
  account_number       VARCHAR,
  holder_name          VARCHAR,
  holder_kind          VARCHAR,            -- individual | corporate | unknown
  flagged_by_others    BOOLEAN,            -- 他からも被害届が出されている
  current_balance_yen  BIGINT,
  seized               BOOLEAN,            -- 第三者差押え
  case_id              VARCHAR,
  source_artifact      VARCHAR,
  created_at           VARCHAR,
  created_date         DATE,
  sensitivity_ord      BIGINT,
  owner_did            VARCHAR,
  actor_did            VARCHAR,
  org_did              VARCHAR
);

-- ────────────────────────────────────────────────────────────────────
-- 3. vertex_malak_victim — 被害者
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_malak_victim (
  vertex_id            VARCHAR PRIMARY KEY,
  rkey                 VARCHAR,
  repo                 VARCHAR,
  victim_name          VARCHAR,
  victim_handle        VARCHAR,            -- LINE / handle
  address              VARCHAR,
  phone                VARCHAR,
  email                VARCHAR,
  total_loss_yen       BIGINT,
  incident_start       VARCHAR,
  incident_end         VARCHAR,
  police_case          VARCHAR,            -- 神奈川県警 磯子署 担当 松村 R5.11.27
  case_id              VARCHAR,
  source_artifact      VARCHAR,
  created_at           VARCHAR,
  created_date         DATE,
  sensitivity_ord      BIGINT,
  owner_did            VARCHAR,
  actor_did            VARCHAR,
  org_did              VARCHAR
);

-- ────────────────────────────────────────────────────────────────────
-- 4. vertex_malak_platform — 詐欺プラットフォーム / 偽サイト / 偽アプリ
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_malak_platform (
  vertex_id            VARCHAR PRIMARY KEY,
  rkey                 VARCHAR,
  repo                 VARCHAR,
  platform_kind        VARCHAR,            -- fake_securities | fake_app | landing_site | line_open_chat | line_group
  platform_name        VARCHAR,
  url                  VARCHAR,
  email_contact        VARCHAR,
  fingerprint          VARCHAR,
  is_active            BOOLEAN,
  case_id              VARCHAR,
  source_artifact      VARCHAR,
  created_at           VARCHAR,
  created_date         DATE,
  sensitivity_ord      BIGINT,
  owner_did            VARCHAR,
  actor_did            VARCHAR,
  org_did              VARCHAR
);

-- ────────────────────────────────────────────────────────────────────
-- 5. vertex_malak_line_contact — LINE handle / open chat / group
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_malak_line_contact (
  vertex_id            VARCHAR PRIMARY KEY,
  rkey                 VARCHAR,
  repo                 VARCHAR,
  contact_kind         VARCHAR,            -- p2p | open_chat | group
  display_name         VARCHAR,
  line_id              VARCHAR,            -- e.g. -JrMTzcGJP
  line_url             VARCHAR,
  case_id              VARCHAR,
  source_artifact      VARCHAR,
  created_at           VARCHAR,
  created_date         DATE,
  sensitivity_ord      BIGINT,
  owner_did            VARCHAR,
  actor_did            VARCHAR,
  org_did              VARCHAR
);

-- ────────────────────────────────────────────────────────────────────
-- 6. Edges
-- ────────────────────────────────────────────────────────────────────
-- victim_source_account → mule_account (1 transfer event)
CREATE TABLE IF NOT EXISTS edge_malak_transferred_to (
  edge_id              VARCHAR PRIMARY KEY,
  src_vid              VARCHAR,            -- bank_account (victim_source)
  dst_vid              VARCHAR,            -- bank_account (mule)
  amount_yen           BIGINT,
  transferred_at       VARCHAR,
  transfer_seq         INT,
  case_id              VARCHAR,
  created_date         DATE,
  owner_did            VARCHAR,
  sensitivity_ord      BIGINT
);

CREATE TABLE IF NOT EXISTS edge_malak_member_of_ring (
  edge_id              VARCHAR PRIMARY KEY,
  src_vid              VARCHAR,            -- threat_actor (member)
  dst_vid              VARCHAR,            -- threat_actor (principal / ring)
  role                 VARCHAR,
  case_id              VARCHAR,
  created_date         DATE,
  owner_did            VARCHAR,
  sensitivity_ord      BIGINT
);

CREATE TABLE IF NOT EXISTS edge_malak_uses_platform (
  edge_id              VARCHAR PRIMARY KEY,
  src_vid              VARCHAR,            -- threat_actor
  dst_vid              VARCHAR,            -- platform
  role                 VARCHAR,
  case_id              VARCHAR,
  created_date         DATE,
  owner_did            VARCHAR,
  sensitivity_ord      BIGINT
);

CREATE TABLE IF NOT EXISTS edge_malak_victim_of (
  edge_id              VARCHAR PRIMARY KEY,
  src_vid              VARCHAR,            -- victim
  dst_vid              VARCHAR,            -- threat_actor (ring or principal)
  case_id              VARCHAR,
  total_loss_yen       BIGINT,
  created_date         DATE,
  owner_did            VARCHAR,
  sensitivity_ord      BIGINT
);

CREATE TABLE IF NOT EXISTS edge_malak_uses_contact (
  edge_id              VARCHAR PRIMARY KEY,
  src_vid              VARCHAR,            -- threat_actor
  dst_vid              VARCHAR,            -- line_contact
  case_id              VARCHAR,
  created_date         DATE,
  owner_did            VARCHAR,
  sensitivity_ord      BIGINT
);

CREATE TABLE IF NOT EXISTS edge_malak_owns_account (
  edge_id              VARCHAR PRIMARY KEY,
  src_vid              VARCHAR,            -- victim or threat_actor
  dst_vid              VARCHAR,            -- bank_account
  ownership_kind       VARCHAR,            -- victim_source | mule_holder | nominee
  case_id              VARCHAR,
  created_date         DATE,
  owner_did            VARCHAR,
  sensitivity_ord      BIGINT
);

-- ────────────────────────────────────────────────────────────────────
-- 7. Indexes
-- ────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_malak_threat_actor_name
  ON vertex_malak_threat_actor (actor_name);
CREATE INDEX IF NOT EXISTS idx_malak_threat_actor_ring
  ON vertex_malak_threat_actor (ring_id);
CREATE INDEX IF NOT EXISTS idx_malak_threat_actor_case
  ON vertex_malak_threat_actor (case_id);

CREATE INDEX IF NOT EXISTS idx_malak_bank_account_bank
  ON vertex_malak_bank_account (bank_name, account_number);
CREATE INDEX IF NOT EXISTS idx_malak_bank_account_holder
  ON vertex_malak_bank_account (holder_name);
CREATE INDEX IF NOT EXISTS idx_malak_bank_account_case
  ON vertex_malak_bank_account (case_id, account_kind);

CREATE INDEX IF NOT EXISTS idx_malak_victim_email
  ON vertex_malak_victim (email);
CREATE INDEX IF NOT EXISTS idx_malak_victim_name
  ON vertex_malak_victim (victim_name);

CREATE INDEX IF NOT EXISTS idx_malak_platform_url
  ON vertex_malak_platform (url);

CREATE INDEX IF NOT EXISTS idx_malak_line_contact_id
  ON vertex_malak_line_contact (line_id);

CREATE INDEX IF NOT EXISTS idx_malak_transferred_src_time
  ON edge_malak_transferred_to (src_vid, transferred_at);
CREATE INDEX IF NOT EXISTS idx_malak_transferred_dst_time
  ON edge_malak_transferred_to (dst_vid, transferred_at);

-- ────────────────────────────────────────────────────────────────────
-- 8. Materialized Views (RW async MV — event-driven refresh)
-- ────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_malak_victim_total_loss AS
SELECT
  victim_name,
  victim_handle,
  email,
  SUM(total_loss_yen) AS total_loss_yen,
  MAX(incident_end)   AS last_incident
FROM vertex_malak_victim
GROUP BY victim_name, victim_handle, email;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_malak_mule_account_summary AS
SELECT
  bank_name,
  account_number,
  holder_name,
  current_balance_yen,
  seized,
  COUNT(*)                   AS hit_count,
  MAX(created_date)          AS last_seen
FROM vertex_malak_bank_account
WHERE account_kind = 'mule'
GROUP BY bank_name, account_number, holder_name, current_balance_yen, seized;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_malak_ring_member_count AS
SELECT
  ring_id,
  COUNT(*)            AS member_count,
  MAX(created_date)   AS last_updated
FROM vertex_malak_threat_actor
WHERE ring_id IS NOT NULL
GROUP BY ring_id;
