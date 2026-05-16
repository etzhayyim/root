import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_manager_journal_entry (
      vertex_id VARCHAR PRIMARY KEY,
      entry_id VARCHAR,
      description TEXT,
      debit_account VARCHAR,
      credit_account VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      fiscal_period VARCHAR,
      approval_status VARCHAR,
      posted_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_manager_invoice (
      vertex_id VARCHAR PRIMARY KEY,
      invoice_id VARCHAR,
      counterparty VARCHAR,
      direction VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      line_items TEXT,
      payment_terms_days BIGINT,
      due_date VARCHAR,
      status VARCHAR,
      issued_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_manager_payment (
      vertex_id VARCHAR PRIMARY KEY,
      payment_id VARCHAR,
      invoice_id VARCHAR,
      amount DOUBLE PRECISION,
      method VARCHAR,
      status_after VARCHAR,
      paid_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_manager_employee (
      vertex_id VARCHAR PRIMARY KEY,
      employee_id VARCHAR,
      full_name VARCHAR,
      department VARCHAR,
      role VARCHAR,
      employment_type VARCHAR,
      start_date VARCHAR,
      salary DOUBLE PRECISION,
      probation_status VARCHAR,
      probation_end_date VARCHAR,
      status VARCHAR,
      registered_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_manager_purchase_order (
      vertex_id VARCHAR PRIMARY KEY,
      po_id VARCHAR,
      vendor VARCHAR,
      items TEXT,
      total_amount DOUBLE PRECISION,
      department VARCHAR,
      justification TEXT,
      approval_level VARCHAR,
      status VARCHAR,
      approver_comment TEXT,
      decided_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_business_manager_budget_allocation (
      vertex_id VARCHAR PRIMARY KEY,
      allocation_id VARCHAR,
      department VARCHAR,
      fiscal_period VARCHAR,
      allocated_amount DOUBLE PRECISION,
      spent_amount DOUBLE PRECISION,
      remaining_amount DOUBLE PRECISION,
      category VARCHAR,
      status VARCHAR,
      allocated_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_business_manager_invoice_payment (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      invoice_id VARCHAR,
      payment_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_business_manager_invoice_payment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_manager_budget_allocation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_manager_purchase_order`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_manager_employee`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_manager_payment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_manager_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_business_manager_journal_entry`.execute(db);
}
