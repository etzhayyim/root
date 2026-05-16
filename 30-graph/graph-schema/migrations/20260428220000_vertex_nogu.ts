import type { Kysely } from "kysely";
import { sql } from "kysely";

// nogu actor — 農具・農機具ライフサイクル管理 (ADR-0056 BPMN-as-actor)
// tier: A (public; 農機シリアルは非 PII)
// tables: item / inspection / maintenance / lease / disposal

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_nogu_item (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      item_id                varchar NOT NULL,
      category               varchar NOT NULL,
      name                   varchar NOT NULL,
      maker                  varchar,
      model                  varchar,
      serial_id              varchar,
      owner_did_item         varchar NOT NULL,
      acquired_at            varchar,
      acquired_price_jpy     double precision,
      status                 varchar NOT NULL DEFAULT 'active',
      next_inspection_date   varchar,
      location_farm_id       varchar,
      notes                  varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_item_owner     ON vertex_nogu_item (owner_did_item)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_item_status    ON vertex_nogu_item (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_item_inspection ON vertex_nogu_item (next_inspection_date)`.execute(db);

  await sql`
    CREATE TABLE vertex_nogu_inspection (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      item_id                varchar NOT NULL,
      item_did               varchar,
      inspected_at           varchar NOT NULL,
      inspector_did          varchar NOT NULL,
      inspection_type        varchar,
      result                 varchar NOT NULL,
      check_items            varchar,
      next_inspection_date   varchar,
      maintenance_required   boolean,
      notes                  varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_inspection_item ON vertex_nogu_inspection (item_id)`.execute(db);

  await sql`
    CREATE TABLE vertex_nogu_maintenance (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      item_id                varchar NOT NULL,
      trigger_inspection_rkey varchar,
      maintenance_type       varchar NOT NULL,
      performed_at           varchar NOT NULL,
      performer_did          varchar NOT NULL,
      parts_used             varchar,
      labor_cost_jpy         double precision,
      total_cost_jpy         double precision,
      status                 varchar NOT NULL DEFAULT 'pending-parts',
      completed_at           varchar,
      notes                  varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_maintenance_item   ON vertex_nogu_maintenance (item_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_maintenance_status ON vertex_nogu_maintenance (status)`.execute(db);

  await sql`
    CREATE TABLE vertex_nogu_lease (
      vertex_id                  varchar PRIMARY KEY,
      _seq                       bigint,
      created_date               date,
      sensitivity_ord            int,
      owner_did                  varchar,
      item_id                    varchar NOT NULL,
      lessee_did_or_member_id    varchar NOT NULL,
      coop_path                  varchar,
      lease_start_date           varchar,
      lease_end_date             varchar,
      lease_purpose              varchar,
      daily_rate_jpy             double precision,
      deposit_jpy                double precision,
      status                     varchar NOT NULL DEFAULT 'active',
      returned_at                varchar,
      condition_on_return        varchar,
      linked_purchase_order_id   varchar,
      notes                      varchar,
      created_at                 varchar,
      org_id                     varchar,
      user_id                    varchar,
      actor_id                   varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_lease_item    ON vertex_nogu_lease (item_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_lease_lessee  ON vertex_nogu_lease (lessee_did_or_member_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_lease_status  ON vertex_nogu_lease (status)`.execute(db);

  await sql`
    CREATE TABLE vertex_nogu_disposal (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      item_id                varchar NOT NULL,
      disposed_at            varchar NOT NULL,
      disposal_method        varchar NOT NULL,
      authorized_by_did      varchar NOT NULL,
      recycler_name          varchar,
      recycler_license_no    varchar,
      salvage_value_jpy      double precision,
      disposal_cost_jpy      double precision,
      certificate_id         varchar,
      notes                  varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_nogu_disposal_item ON vertex_nogu_disposal (item_id)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_nogu_disposal_item`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nogu_disposal`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_lease_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_lease_lessee`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_lease_item`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nogu_lease`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_maintenance_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_maintenance_item`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nogu_maintenance`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_inspection_item`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nogu_inspection`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_item_inspection`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_item_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_nogu_item_owner`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nogu_item`.execute(db);
  await sql`FLUSH`.execute(db);
}
