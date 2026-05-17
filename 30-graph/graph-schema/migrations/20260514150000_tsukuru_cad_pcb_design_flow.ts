import { Kysely, sql } from 'kysely';

// tier: B
// SSoT: sql_migrations/20260514150000_tsukuru_cad_pcb_design_flow.up.sql

/**
 * tsukuru CAD/PCB design project schema + LangGraph design-flow topologies.
 *
 * Adds first-class schema for hardware design projects (open-robo and any
 * future kit product) so tsukuru.etzhayyim.com can manage the full loop:
 *   Fusion360 STEP → Meviy quote → production_order → delivery → fit check
 *   KiCad Gerber  → P-Ban.com quote → production_order → assembly → test
 *
 * New tables:
 *   vertex_tsukuru_cad_project  — per-product CAD project tracker
 *   vertex_tsukuru_cad_part     — per-part modeling / ordering status
 *   vertex_tsukuru_pcb_project  — PCB design project tracker
 *   edge_tsukuru_project_part   — project → part membership
 *
 * New LangGraph topologies (inserted into existing vertex_langgraph_assistant):
 *   tsukuru_cad_design_flow.v1
 *   tsukuru_pcb_design_flow.v1
 *
 * Apply note: multi-head Alembic blocks pnpm db:migrate (see CLAUDE.md
 * §Multi-Head Alembic Workaround). Apply directly via psycopg2 in 3 phases:
 *   phase 1 — CREATE TABLE × 4
 *   phase 2 — CREATE INDEX × 10
 *   phase 3 — INSERT vertex_mcp_tool_def + vertex_langgraph_assistant/node + FLUSH
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Phase 1: tables ────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_tsukuru_cad_project (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      actor_did         VARCHAR,
      org_did           VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      project_id        VARCHAR NOT NULL,
      project_name      VARCHAR,
      product_ref       VARCHAR,
      cad_tool          VARCHAR,
      status            VARCHAR,
      total_parts       INTEGER,
      parts_completed   INTEGER,
      assembly_step_ref VARCHAR,
      meviy_quote_id    VARCHAR,
      meviy_quote_jpy   BIGINT,
      meviy_order_id    VARCHAR,
      tsukuru_order_vid VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_tsukuru_cad_part (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      actor_did         VARCHAR,
      org_did           VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      project_vid       VARCHAR NOT NULL,
      part_number       VARCHAR,
      part_name         VARCHAR,
      material          VARCHAR,
      process           VARCHAR,
      status            VARCHAR,
      step_file_ref     VARCHAR,
      tolerance_class   VARCHAR,
      surface_finish    VARCHAR,
      quantity          INTEGER,
      unit_price_jpy    BIGINT,
      meviy_part_id     VARCHAR,
      fit_check_note    VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_tsukuru_pcb_project (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      actor_did           VARCHAR,
      org_did             VARCHAR,
      created_at          VARCHAR,
      updated_at          VARCHAR,
      project_id          VARCHAR NOT NULL,
      pcb_name            VARCHAR,
      product_ref         VARCHAR,
      kicad_version       VARCHAR,
      board_size_mm       VARCHAR,
      layer_count         INTEGER,
      status              VARCHAR,
      schematic_ref       VARCHAR,
      layout_ref          VARCHAR,
      gerber_ref          VARCHAR,
      bom_ref             VARCHAR,
      drc_errors          INTEGER,
      component_count     INTEGER,
      pban_quote_id       VARCHAR,
      pban_quote_jpy      BIGINT,
      pban_order_id       VARCHAR,
      quantity_ordered    INTEGER,
      assembly_vendor     VARCHAR,
      tsukuru_order_vid   VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_tsukuru_project_part (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      relation          VARCHAR,
      created_at        VARCHAR,
      owner_did         VARCHAR,
      sensitivity_ord   BIGINT
    )
  `.execute(db);

  // ── Phase 2: indexes ───────────────────────────────────────────────────────
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_id ON vertex_tsukuru_cad_project (project_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_owner ON vertex_tsukuru_cad_project (owner_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_product_ref ON vertex_tsukuru_cad_project (product_ref)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_project_status ON vertex_tsukuru_cad_project (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_part_project ON vertex_tsukuru_cad_part (project_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_cad_part_status ON vertex_tsukuru_cad_part (project_vid, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_id ON vertex_tsukuru_pcb_project (project_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_owner ON vertex_tsukuru_pcb_project (owner_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_product_ref ON vertex_tsukuru_pcb_project (product_ref)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_pcb_project_status ON vertex_tsukuru_pcb_project (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_project_part_src ON edge_tsukuru_project_part (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_project_part_dst ON edge_tsukuru_project_part (dst_vid)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    'edge_tsukuru_project_part',
    'vertex_tsukuru_cad_part',
    'vertex_tsukuru_cad_project',
    'vertex_tsukuru_pcb_project',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(t)}`.execute(db);
  }
}
