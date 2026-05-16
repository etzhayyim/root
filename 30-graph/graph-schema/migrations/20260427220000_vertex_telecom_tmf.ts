import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (product catalog / product order / product inventory / service order / service activation)
// tier: C (service inventory / customer account / customer bill)
// PII note: registerCustomerAccount — partyName/partyContact/partyTaxId/billingAddress stored sha256: hashed

/**
 * telecom Phase 17 — TM Forum Open APIs (TMF620/622/637/641/640/638/666/678).
 * Covers product lifecycle (catalog → order → inventory), service lifecycle
 * (order → activation → inventory), and customer lifecycle (account + billing).
 *
 * Builds on Phase 1 (service/subscription), Phase 2 (network asset), Phase 8
 * (OSS resource), Phase 12 (NFV — service chaining), Phase 13 (WLAN).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // TMF620 — Product Catalog Management
  await sql`
    CREATE TABLE vertex_telecom_tmf_product_offering (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      offering_id          varchar NOT NULL,
      name                 varchar NOT NULL,
      description          varchar,
      lifecycle_status     varchar NOT NULL,
      product_spec_id      varchar,
      category_ids         varchar,
      channel_ids          varchar,
      market_ids           varchar,
      price_ref            varchar,
      valid_from_at        varchar,
      valid_to_at          varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // TMF622 — Product Ordering Management
  await sql`
    CREATE TABLE vertex_telecom_tmf_product_order (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      product_order_id     varchar NOT NULL,
      account_id           varchar NOT NULL,
      order_kind           varchar NOT NULL,
      offering_id          varchar,
      product_id           varchar,
      order_item_hash      varchar,
      order_item_ref       varchar,
      requested_start_at   varchar,
      requested_completion_at varchar,
      priority             int,
      channel_id           varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // TMF637 — Product Inventory Management
  await sql`
    CREATE TABLE vertex_telecom_tmf_product_inventory (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      record_id            varchar NOT NULL,
      product_id           varchar NOT NULL,
      account_id           varchar NOT NULL,
      offering_id          varchar,
      product_order_id     varchar,
      lifecycle_status     varchar NOT NULL,
      started_at           varchar,
      terminated_at        varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // TMF641 — Service Ordering Management
  await sql`
    CREATE TABLE vertex_telecom_tmf_service_order (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      service_order_id     varchar NOT NULL,
      product_order_id     varchar NOT NULL,
      product_id           varchar,
      service_spec         varchar,
      order_kind           varchar NOT NULL,
      order_item_hash      varchar,
      order_item_ref       varchar,
      requested_start_at   varchar,
      requested_completion_at varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // TMF640 — Service Activation and Configuration
  await sql`
    CREATE TABLE vertex_telecom_tmf_service_activation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      activation_id        varchar NOT NULL,
      service_order_id     varchar NOT NULL,
      service_instance_kind varchar NOT NULL,
      service_instance_vid varchar,
      action               varchar NOT NULL,
      configuration_hash   varchar,
      configuration_ref    varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // TMF638 — Service Inventory Management
  await sql`
    CREATE TABLE vertex_telecom_tmf_service_inventory (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      record_id            varchar NOT NULL,
      service_instance_kind varchar NOT NULL,
      service_instance_vid varchar,
      product_id           varchar,
      service_order_id     varchar,
      lifecycle_status     varchar NOT NULL,
      operational_state    varchar,
      started_at           varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // TMF666 — Account Management (PII hashed: party_name, party_contact, party_tax_id, billing_address)
  await sql`
    CREATE TABLE vertex_telecom_tmf_customer_account (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      account_id           varchar NOT NULL,
      customer_kind        varchar NOT NULL,
      account_kind         varchar NOT NULL,
      party_name           varchar,
      party_contact        varchar,
      party_tax_id         varchar,
      billing_address      varchar,
      currency             varchar,
      payment_method_kind  varchar,
      payment_method_ref   varchar,
      parent_subscriber_id varchar,
      jurisdiction         varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // TMF678 — Customer Bill Management
  await sql`
    CREATE TABLE vertex_telecom_tmf_customer_bill (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      bill_id              varchar NOT NULL,
      account_id           varchar NOT NULL,
      period_start         varchar NOT NULL,
      period_end           varchar NOT NULL,
      currency             varchar,
      source_invoice_vids  varchar,
      due_at               varchar,
      delivery_channel     varchar,
      bill_document_ref    varchar,
      total_amount         double precision,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // Edges: product_order → product_offering, product_inventory → product_order
  await sql`
    CREATE TABLE edge_telecom_tmf_order_offering (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_tmf_inventory_order (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_tmf_service_order_product_order (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    )
  `.execute(db);

  // Materialized views
  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_tmf_active_offerings AS
    SELECT offering_id, name, lifecycle_status, valid_from_at, valid_to_at, org_id
    FROM vertex_telecom_tmf_product_offering
    WHERE lifecycle_status IN ('Active', 'Launched')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_tmf_open_product_orders AS
    SELECT product_order_id, account_id, order_kind, offering_id, priority, observed_at, status, org_id
    FROM vertex_telecom_tmf_product_order
    WHERE status NOT IN ('completed', 'cancelled', 'rejected')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_tmf_open_service_orders AS
    SELECT service_order_id, product_order_id, order_kind, service_spec, observed_at, status, org_id
    FROM vertex_telecom_tmf_service_order
    WHERE status NOT IN ('completed', 'cancelled', 'rejected')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_tmf_active_product_inventory AS
    SELECT record_id, product_id, account_id, lifecycle_status, started_at, org_id
    FROM vertex_telecom_tmf_product_inventory
    WHERE lifecycle_status = 'Active'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_tmf_active_service_inventory AS
    SELECT record_id, service_instance_kind, service_instance_vid, lifecycle_status, operational_state, started_at, org_id
    FROM vertex_telecom_tmf_service_inventory
    WHERE lifecycle_status = 'active'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_tmf_bill_summary AS
    SELECT account_id, period_start, period_end, currency, total_amount, due_at, status, org_id
    FROM vertex_telecom_tmf_customer_bill
    ORDER BY period_end DESC
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_bill_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_active_service_inventory`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_active_product_inventory`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_open_service_orders`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_open_product_orders`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_active_offerings`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_tmf_service_order_product_order`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_tmf_inventory_order`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_tmf_order_offering`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_customer_bill`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_customer_account`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_service_inventory`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_service_activation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_service_order`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_product_inventory`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_product_order`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tmf_product_offering`.execute(db);
}
