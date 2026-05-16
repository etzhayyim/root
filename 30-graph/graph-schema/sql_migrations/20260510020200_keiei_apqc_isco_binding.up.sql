-- Bind keiei C-suite roles to APQC PCF L1 + ISCO-08 unit groups.
--
-- - APQC PCF L1: 13 cross-industry process categories (1.0 Vision&Strategy …
--   13.0 Sustainability). Already seeded in repo as `cohort-apqc-{1..13}`
--   per `deps.toml [[cohorts]]` (ADR-0025 Kyber APQC/BPMN Projector +
--   ADR-0026 cohort lineage). One role can own / participate in many PCF
--   categories; the *primary* category is denormalized on vertex for fast
--   reads, the full set lives on edge_keiei_role_owns_apqc.
-- - ISCO-08: ILO 4-digit unit-group code. `vertex_occupation` (migration
--   0074, 393 rows) carries the canonical labels. We denormalize the code
--   on the role vertex and link to the canonical row via
--   edge_keiei_role_isco for traversal.
--
-- Append-only: re-INSERT into vertex_keiei_role acts as upsert (RisingWave
-- record-log semantics, no ON CONFLICT — see 30-graph/graph-schema/CLAUDE.md).

-- ─────────────────────────────────────────────────────────────────────────
-- 1. ALTER vertex_keiei_role — add APQC + ISCO columns.
-- ─────────────────────────────────────────────────────────────────────────

ALTER TABLE vertex_keiei_role ADD COLUMN IF NOT EXISTS apqc_pcf_l1_primary  varchar;
ALTER TABLE vertex_keiei_role ADD COLUMN IF NOT EXISTS apqc_pcf_l1_set      varchar;  -- comma-joined "1.0,7.0,11.0"
ALTER TABLE vertex_keiei_role ADD COLUMN IF NOT EXISTS isco_08_unit_group   varchar;  -- 4-digit code
ALTER TABLE vertex_keiei_role ADD COLUMN IF NOT EXISTS isco_08_label        varchar;
ALTER TABLE vertex_keiei_role ADD COLUMN IF NOT EXISTS isco_08_skill_level  bigint;   -- 1..4 per ILO

CREATE INDEX IF NOT EXISTS idx_keiei_role_apqc ON vertex_keiei_role (apqc_pcf_l1_primary);
CREATE INDEX IF NOT EXISTS idx_keiei_role_isco ON vertex_keiei_role (isco_08_unit_group);

-- ─────────────────────────────────────────────────────────────────────────
-- 2. Edge: role ─owns_apqc─▶ cohort_apqc_* (many-to-many).
--    src_vid = vertex_keiei_role.vertex_id
--    dst_vid = at://did:web:cohort.gftd.ai/ai.gftd.cohort.actor/cohort-apqc-{N}
--              (matches existing vertex_cohort_actor seed)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS edge_keiei_role_owns_apqc (
  edge_id          varchar PRIMARY KEY,
  src_vid          varchar NOT NULL,
  dst_vid          varchar NOT NULL,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 1,
  owner_did        varchar,
  apqc_pcf_l1      varchar NOT NULL,        -- "1.0" / "7.0" / ...
  ownership_kind   varchar NOT NULL,         -- "primary" | "participates" | "consults"
  binding_strength double precision DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_keiei_owns_apqc_src ON edge_keiei_role_owns_apqc (src_vid);
CREATE INDEX IF NOT EXISTS idx_keiei_owns_apqc_dst ON edge_keiei_role_owns_apqc (dst_vid);
CREATE INDEX IF NOT EXISTS idx_keiei_owns_apqc_pcf ON edge_keiei_role_owns_apqc (apqc_pcf_l1);

-- ─────────────────────────────────────────────────────────────────────────
-- 3. Edge: role ─classified_isco─▶ vertex_occupation (ISCO-08 row).
--    dst_vid = at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/{4digit}
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS edge_keiei_role_isco (
  edge_id          varchar PRIMARY KEY,
  src_vid          varchar NOT NULL,
  dst_vid          varchar NOT NULL,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 1,
  owner_did        varchar,
  isco_08_unit_group varchar NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_keiei_role_isco_src ON edge_keiei_role_isco (src_vid);
CREATE INDEX IF NOT EXISTS idx_keiei_role_isco_dst ON edge_keiei_role_isco (dst_vid);

FLUSH;
