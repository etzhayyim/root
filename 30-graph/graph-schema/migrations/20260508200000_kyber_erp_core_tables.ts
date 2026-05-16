import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Chart of Accounts ────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_account (
      vertex_id VARCHAR PRIMARY KEY,
      account_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      code VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      account_type VARCHAR NOT NULL,
      seed BOOLEAN NOT NULL DEFAULT FALSE,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Journal Entries ──────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_journal_entry (
      vertex_id VARCHAR PRIMARY KEY,
      entry_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      date VARCHAR NOT NULL,
      description VARCHAR,
      debit_account VARCHAR NOT NULL,
      credit_account VARCHAR NOT NULL,
      amount DOUBLE PRECISION NOT NULL,
      currency VARCHAR NOT NULL DEFAULT 'USD',
      reference VARCHAR,
      period VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Invoices (AP/AR) ─────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_invoice (
      vertex_id VARCHAR PRIMARY KEY,
      invoice_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      invoice_number VARCHAR NOT NULL,
      invoice_type VARCHAR NOT NULL,
      party_did VARCHAR,
      party_name VARCHAR,
      issue_date VARCHAR NOT NULL,
      due_date VARCHAR,
      subtotal DOUBLE PRECISION NOT NULL DEFAULT 0,
      tax DOUBLE PRECISION NOT NULL DEFAULT 0,
      total DOUBLE PRECISION NOT NULL DEFAULT 0,
      currency VARCHAR NOT NULL DEFAULT 'USD',
      status VARCHAR NOT NULL DEFAULT 'draft',
      items_json VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Employees ────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_employee (
      vertex_id VARCHAR PRIMARY KEY,
      employee_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      employee_number VARCHAR NOT NULL,
      first_name VARCHAR NOT NULL,
      last_name VARCHAR NOT NULL,
      email VARCHAR,
      department VARCHAR,
      position VARCHAR,
      employment_type VARCHAR NOT NULL DEFAULT 'full-time',
      hire_date VARCHAR NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Purchase Orders ──────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_purchase_order (
      vertex_id VARCHAR PRIMARY KEY,
      po_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      po_number VARCHAR NOT NULL,
      vendor_did VARCHAR,
      vendor_name VARCHAR,
      order_date VARCHAR NOT NULL,
      expected_delivery VARCHAR,
      subtotal DOUBLE PRECISION NOT NULL DEFAULT 0,
      tax DOUBLE PRECISION NOT NULL DEFAULT 0,
      total DOUBLE PRECISION NOT NULL DEFAULT 0,
      currency VARCHAR NOT NULL DEFAULT 'USD',
      status VARCHAR NOT NULL DEFAULT 'draft',
      items_json VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Inventory Items ──────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_inventory_item (
      vertex_id VARCHAR PRIMARY KEY,
      item_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      sku VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      description VARCHAR,
      category VARCHAR,
      quantity_on_hand DOUBLE PRECISION NOT NULL DEFAULT 0,
      unit_cost DOUBLE PRECISION NOT NULL DEFAULT 0,
      reorder_point DOUBLE PRECISION,
      warehouse VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Sales Orders ─────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_sales_order (
      vertex_id VARCHAR PRIMARY KEY,
      order_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      order_number VARCHAR NOT NULL,
      customer_did VARCHAR,
      customer_name VARCHAR,
      order_date VARCHAR NOT NULL,
      expected_delivery VARCHAR,
      subtotal DOUBLE PRECISION NOT NULL DEFAULT 0,
      tax DOUBLE PRECISION NOT NULL DEFAULT 0,
      total DOUBLE PRECISION NOT NULL DEFAULT 0,
      currency VARCHAR NOT NULL DEFAULT 'USD',
      status VARCHAR NOT NULL DEFAULT 'draft',
      items_json VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Fixed Assets ─────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_fixed_asset (
      vertex_id VARCHAR PRIMARY KEY,
      asset_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      asset_number VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      category VARCHAR,
      acquisition_date VARCHAR NOT NULL,
      acquisition_cost DOUBLE PRECISION NOT NULL,
      useful_life_years INTEGER NOT NULL,
      depreciation_method VARCHAR NOT NULL DEFAULT 'straight-line',
      salvage_value DOUBLE PRECISION NOT NULL DEFAULT 0,
      accumulated_depreciation DOUBLE PRECISION NOT NULL DEFAULT 0,
      net_book_value DOUBLE PRECISION NOT NULL,
      location VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Depreciation Runs ─────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_depreciation_run (
      vertex_id VARCHAR PRIMARY KEY,
      run_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      period VARCHAR NOT NULL,
      total_depreciation DOUBLE PRECISION NOT NULL DEFAULT 0,
      asset_count INTEGER NOT NULL DEFAULT 0,
      status VARCHAR NOT NULL DEFAULT 'completed',
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Policy Controls (Governance) ─────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_policy_control (
      vertex_id VARCHAR PRIMARY KEY,
      control_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      control_code VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      description VARCHAR,
      framework VARCHAR,
      category VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      owner_did VARCHAR,
      review_date VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Risk Issues ───────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_risk_issue (
      vertex_id VARCHAR PRIMARY KEY,
      issue_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      title VARCHAR NOT NULL,
      description VARCHAR,
      category VARCHAR,
      likelihood VARCHAR NOT NULL DEFAULT 'medium',
      impact VARCHAR NOT NULL DEFAULT 'medium',
      risk_score INTEGER,
      status VARCHAR NOT NULL DEFAULT 'open',
      owner_did VARCHAR,
      due_date VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Departments ───────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_department (
      vertex_id VARCHAR PRIMARY KEY,
      department_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      role VARCHAR NOT NULL,
      dept_did VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Integration Bindings ──────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_integration_binding (
      vertex_id VARCHAR PRIMARY KEY,
      binding_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      integration_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      description VARCHAR,
      category VARCHAR,
      xrpc_method VARCHAR,
      synced_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    "vertex_kyber_integration_binding",
    "vertex_kyber_department",
    "vertex_kyber_risk_issue",
    "vertex_kyber_policy_control",
    "vertex_kyber_depreciation_run",
    "vertex_kyber_fixed_asset",
    "vertex_kyber_sales_order",
    "vertex_kyber_inventory_item",
    "vertex_kyber_purchase_order",
    "vertex_kyber_employee",
    "vertex_kyber_invoice",
    "vertex_kyber_journal_entry",
    "vertex_kyber_account",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
