import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0076: xlsx core graph spine.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_workbook (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      workbook_id       VARCHAR,
      title             VARCHAR,
      active_sheet_id   VARCHAR,
      sheet_count       BIGINT,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_workbook_id ON vertex_xlsx_workbook (workbook_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_sheet (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      sheet_id          VARCHAR,
      workbook_id       VARCHAR,
      name              VARCHAR,
      sheet_order       BIGINT,
      frozen_panes      VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_sheet_id ON vertex_xlsx_sheet (sheet_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_sheet_workbook ON vertex_xlsx_sheet (workbook_id, sheet_order)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_cell (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      cell_id           VARCHAR,
      workbook_id       VARCHAR,
      sheet_id          VARCHAR,
      cell_ref          VARCHAR,
      row_num           BIGINT,
      col_num           BIGINT,
      value_text        VARCHAR,
      value_num         DOUBLE PRECISION,
      value_type        VARCHAR,
      formula           VARCHAR,
      style_id          VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_cell_sheet_ref ON vertex_xlsx_cell (sheet_id, cell_ref)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_cell_formula ON vertex_xlsx_cell (sheet_id, formula)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_style (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      style_id          VARCHAR,
      workbook_id       VARCHAR,
      number_format     VARCHAR,
      font_json         VARCHAR,
      fill_json         VARCHAR,
      border_json       VARCHAR,
      alignment_json    VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_style_id ON vertex_xlsx_style (style_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_chart (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      chart_id          VARCHAR,
      workbook_id       VARCHAR,
      sheet_id          VARCHAR,
      chart_type        VARCHAR,
      data_range        VARCHAR,
      series_json       VARCHAR,
      title             VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_chart_id ON vertex_xlsx_chart (chart_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_chart_sheet ON vertex_xlsx_chart (sheet_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_table (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      table_id          VARCHAR,
      workbook_id       VARCHAR,
      sheet_id          VARCHAR,
      name              VARCHAR,
      range_ref         VARCHAR,
      columns_json      VARCHAR,
      style_ref         VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_table_id ON vertex_xlsx_table (table_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_defined_name (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      defined_name_id   VARCHAR,
      workbook_id       VARCHAR,
      name              VARCHAR,
      refers_to         VARCHAR,
      scope_sheet_id    VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_defined_name_id ON vertex_xlsx_defined_name (defined_name_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_workbook_template (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      template_id       VARCHAR,
      name              VARCHAR,
      category          VARCHAR,
      workbook_id       VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_workbook_template_id ON vertex_xlsx_workbook_template (template_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_xlsx_pivot (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      pivot_id          VARCHAR,
      workbook_id       VARCHAR,
      sheet_id          VARCHAR,
      source_range      VARCHAR,
      rows_json         VARCHAR,
      columns_json      VARCHAR,
      values_json       VARCHAR,
      filters_json      VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_xlsx_pivot_id ON vertex_xlsx_pivot (pivot_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_xlsx_workbook_sheet (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      sheet_order       BIGINT,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_xlsx_workbook_sheet_src ON edge_xlsx_workbook_sheet (src_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_xlsx_sheet_cell (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      cell_ref          VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_xlsx_sheet_cell_src ON edge_xlsx_sheet_cell (src_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_xlsx_cell_style (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_xlsx_cell_style_src ON edge_xlsx_cell_style (src_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_xlsx_sheet_chart (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_xlsx_sheet_chart_src ON edge_xlsx_sheet_chart (src_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_xlsx_sheet_table (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_xlsx_sheet_table_src ON edge_xlsx_sheet_table (src_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_xlsx_sheet_metrics AS
    SELECT
      c.workbook_id,
      c.sheet_id,
      COUNT(*) AS cell_count,
      SUM(CASE WHEN c.formula IS NOT NULL AND c.formula <> '' THEN 1 ELSE 0 END) AS formula_count,
      SUM(CASE WHEN c.value_num IS NOT NULL THEN 1 ELSE 0 END) AS numeric_cell_count,
      MAX(c._seq) AS last_seq
    FROM vertex_xlsx_cell c
    WHERE c.sheet_id IS NOT NULL
    GROUP BY c.workbook_id, c.sheet_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_xlsx_formula_dependency AS
    SELECT
      workbook_id,
      sheet_id,
      cell_ref,
      formula,
      MAX(_seq) AS last_seq
    FROM vertex_xlsx_cell
    WHERE formula IS NOT NULL AND formula <> ''
    GROUP BY workbook_id, sheet_id, cell_ref, formula
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_xlsx_formula_dependency`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_xlsx_sheet_metrics`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_xlsx_sheet_table`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_xlsx_sheet_chart`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_xlsx_cell_style`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_xlsx_sheet_cell`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_xlsx_workbook_sheet`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_pivot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_workbook_template`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_defined_name`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_table`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_chart`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_style`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_cell`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_sheet`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_xlsx_workbook`.execute(db);
}
