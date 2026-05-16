import type { Kysely } from "kysely";
import { sql } from "kysely";

// sekkei actor — 設計図・技術文書ライフサイクル管理 (ADR-0056 BPMN-as-actor)
// tier: A (public aggregate; CAD blob refs are pointers only, no raw data)
// tables: drawing / revision / approval / bom_line / release

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_sekkei_drawing (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      title                    varchar NOT NULL,
      drawing_type             varchar NOT NULL,
      owner_did_drawing        varchar NOT NULL,
      project_code             varchar,
      assembly_code            varchar,
      current_rev_no           varchar,
      status                   varchar NOT NULL DEFAULT 'draft',
      cad_file_ref             varchar,
      pdf_file_ref             varchar,
      linked_actor_did         varchar,
      tsukuru_manufacturer_did varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_owner       ON vertex_sekkei_drawing (owner_did_drawing)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_status      ON vertex_sekkei_drawing (status)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_project     ON vertex_sekkei_drawing (project_code)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_linked      ON vertex_sekkei_drawing (linked_actor_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE vertex_sekkei_revision (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      rev_no                   varchar NOT NULL,
      previous_rev_no          varchar,
      revision_reason          varchar NOT NULL,
      change_description       varchar,
      revised_by_did           varchar NOT NULL,
      revised_at               varchar NOT NULL,
      cad_file_ref             varchar,
      pdf_file_ref             varchar,
      status                   varchar NOT NULL DEFAULT 'pending-approval',
      affected_bom_lines       varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_revision_drawing ON vertex_sekkei_revision (drawing_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_revision_status  ON vertex_sekkei_revision (status)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE vertex_sekkei_approval (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      rev_no                   varchar NOT NULL,
      approver_did             varchar NOT NULL,
      approver_role            varchar,
      decision                 varchar NOT NULL,
      decided_at               varchar NOT NULL,
      conditions               varchar,
      rejection_reason         varchar,
      signature_ref            varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_approval_drawing  ON vertex_sekkei_approval (drawing_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_approval_decision ON vertex_sekkei_approval (decision)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE vertex_sekkei_bom_line (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      bom_line_id              varchar NOT NULL,
      parent_drawing_id        varchar NOT NULL,
      parent_rev_no            varchar,
      child_item_code          varchar NOT NULL,
      child_drawing_id         varchar,
      child_item_name          varchar,
      quantity                 double precision NOT NULL,
      unit                     varchar,
      level                    integer,
      item_type                varchar,
      supplier_did             varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_bom_parent ON vertex_sekkei_bom_line (parent_drawing_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_bom_child  ON vertex_sekkei_bom_line (child_item_code)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE vertex_sekkei_release (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      rev_no                   varchar NOT NULL,
      release_type             varchar NOT NULL,
      released_by_did          varchar NOT NULL,
      released_at              varchar NOT NULL,
      target_product_code      varchar,
      effective_date           varchar,
      obsoletes_drawing_id     varchar,
      distribution_list        varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_release_drawing ON vertex_sekkei_release (drawing_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sekkei_release_product ON vertex_sekkei_release (target_product_code)`.execute(db);
  await sql`FLUSH`.execute(db);

  // MV: drawings pending review for > 3 days (sekkei dailyPulse uses this)
  await sql`
    CREATE MATERIALIZED VIEW mv_sekkei_stale_reviews AS
      SELECT
        drawing_id,
        rev_no,
        revised_by_did,
        revised_at
      FROM vertex_sekkei_revision
      WHERE status = 'pending-approval'
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_sekkei_stale_reviews`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_release_product`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_release_drawing`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sekkei_release`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_bom_child`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_bom_parent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sekkei_bom_line`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_approval_decision`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_approval_drawing`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sekkei_approval`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_revision_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_revision_drawing`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sekkei_revision`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_drawing_linked`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_drawing_project`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_drawing_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sekkei_drawing_owner`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sekkei_drawing`.execute(db);
  await sql`FLUSH`.execute(db);
}
