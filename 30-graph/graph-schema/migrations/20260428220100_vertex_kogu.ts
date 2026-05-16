import type { Kysely } from "kysely";
import { sql } from "kysely";

// kogu actor — 工具・設備ライフサイクル管理 (ADR-0056 BPMN-as-actor)
// tier: A (public; 工具シリアルは非 PII)
// tables: item / calibration / checkout / inspection

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_kogu_item (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      tool_id                  varchar NOT NULL,
      category                 varchar NOT NULL,
      name                     varchar NOT NULL,
      maker                    varchar,
      model                    varchar,
      serial_id                varchar,
      custodian_did            varchar NOT NULL,
      location_code            varchar,
      acquired_at              varchar,
      acquired_price_jpy       double precision,
      calibration_required     boolean NOT NULL DEFAULT false,
      calibration_interval_days integer,
      next_calibration_date    varchar,
      status                   varchar NOT NULL DEFAULT 'available',
      sekkei_drawing_id        varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_item_custodian   ON vertex_kogu_item (custodian_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_item_status      ON vertex_kogu_item (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_item_calibration ON vertex_kogu_item (calibration_required, next_calibration_date)`.execute(db);

  await sql`
    CREATE TABLE vertex_kogu_calibration (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      tool_id                  varchar NOT NULL,
      calibrated_at            varchar NOT NULL,
      calibrator_did           varchar NOT NULL,
      accredited_calibration   boolean NOT NULL DEFAULT false,
      calibration_cert_no      varchar,
      reference_standard_id    varchar,
      before_value             double precision,
      after_value              double precision,
      unit                     varchar,
      tolerance                double precision,
      result                   varchar NOT NULL,
      next_calibration_date    varchar,
      calibration_cost_jpy     double precision,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_calibration_tool ON vertex_kogu_calibration (tool_id)`.execute(db);

  await sql`
    CREATE TABLE vertex_kogu_checkout (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      tool_id                  varchar NOT NULL,
      borrower_did             varchar NOT NULL,
      work_order_id            varchar,
      checked_out_at           varchar,
      expected_return_at       varchar,
      returned_at              varchar,
      condition_on_return      varchar,
      status                   varchar NOT NULL DEFAULT 'checked-out',
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_checkout_tool     ON vertex_kogu_checkout (tool_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_checkout_borrower ON vertex_kogu_checkout (borrower_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_checkout_status   ON vertex_kogu_checkout (status)`.execute(db);

  await sql`
    CREATE TABLE vertex_kogu_inspection (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      tool_id                  varchar NOT NULL,
      inspected_at             varchar NOT NULL,
      inspector_did            varchar NOT NULL,
      inspection_type          varchar,
      check_items              varchar,
      result                   varchar NOT NULL,
      repair_required          boolean,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_kogu_inspection_tool ON vertex_kogu_inspection (tool_id)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_kogu_inspection_tool`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kogu_inspection`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_kogu_checkout_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_kogu_checkout_borrower`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_kogu_checkout_tool`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kogu_checkout`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_kogu_calibration_tool`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kogu_calibration`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_kogu_item_calibration`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_kogu_item_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_kogu_item_custodian`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kogu_item`.execute(db);
  await sql`FLUSH`.execute(db);
}
