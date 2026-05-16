import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_seikyu_payment_received (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      invoice_did VARCHAR NOT NULL,
      payment_date DATE NOT NULL,
      amount DOUBLE PRECISION NOT NULL,
      currency VARCHAR NOT NULL DEFAULT 'JPY',
      payment_method VARCHAR,
      reference VARCHAR,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_seikyu_credit_note (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      invoice_did VARCHAR NOT NULL,
      credit_note_number VARCHAR NOT NULL,
      reason VARCHAR,
      amount DOUBLE PRECISION NOT NULL,
      currency VARCHAR NOT NULL DEFAULT 'JPY',
      issued_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_seikyu_recurring_schedule (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      customer_did VARCHAR NOT NULL,
      agreement_did VARCHAR,
      amount DOUBLE PRECISION NOT NULL,
      currency VARCHAR NOT NULL DEFAULT 'JPY',
      frequency VARCHAR NOT NULL,
      next_issue_date DATE NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_keiyaku_counterparty (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      counterparty_name VARCHAR NOT NULL,
      contact_json VARCHAR,
      tax_id VARCHAR,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 200,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);
  // RW does not honor "ADD COLUMN IF NOT EXISTS"; check first.
  {
    const existing = await sql<{ column_name: string }>`
      SELECT column_name FROM information_schema.columns
      WHERE table_name = 'vertex_atrecord_keiyaku_counterparty'
    `.execute(db);
    const have = new Set(existing.rows.map((r: any) => r.column_name));
    const addCol = async (name: string, type: string) => {
      if (!have.has(name)) {
        await sql.raw(`ALTER TABLE vertex_atrecord_keiyaku_counterparty ADD COLUMN ${name} ${type}`).execute(db);
      }
    };
    await addCol('counterparty_name', 'VARCHAR');
    await addCol('contact_json', 'VARCHAR');
    await addCol('tax_id', 'VARCHAR');
    await addCol('sensitivity_ord', 'INTEGER DEFAULT 200');
  }

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_keiyaku_signing_flow (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      agreement_did VARCHAR NOT NULL,
      signer_did VARCHAR,
      status VARCHAR NOT NULL,
      requested_at TIMESTAMPTZ NOT NULL,
      completed_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 200,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_keiyaku_amendment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      agreement_did VARCHAR NOT NULL,
      title VARCHAR NOT NULL,
      pdf_cid VARCHAR,
      effective_from DATE,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 200,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_keiyaku_obligation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      agreement_did VARCHAR NOT NULL,
      obligation_type VARCHAR NOT NULL,
      due_date DATE,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'open',
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 200,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_kousuu_task (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      project_did VARCHAR NOT NULL,
      task_code VARCHAR NOT NULL,
      task_name VARCHAR NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'open',
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_kousuu_project_cost (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      project_did VARCHAR NOT NULL,
      period_month DATE NOT NULL,
      actual_hours DOUBLE PRECISION NOT NULL DEFAULT 0,
      billable_hours DOUBLE PRECISION NOT NULL DEFAULT 0,
      cost_amount_jpy DOUBLE PRECISION,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_keihi_expense (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      employee_did VARCHAR NOT NULL,
      project_did VARCHAR,
      vendor_name VARCHAR,
      expense_date DATE NOT NULL,
      amount DOUBLE PRECISION NOT NULL,
      currency VARCHAR NOT NULL DEFAULT 'JPY',
      tax_rate DOUBLE PRECISION DEFAULT 0,
      category VARCHAR,
      receipt_cid VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'submitted',
      approved_by_did VARCHAR,
      approved_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_jinji_employee (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      employee_did VARCHAR NOT NULL,
      display_name_encrypted VARCHAR NOT NULL,
      employment_status VARCHAR NOT NULL,
      joined_on DATE,
      left_on DATE,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 300,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_jinji_attendance (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      employee_did VARCHAR NOT NULL,
      work_date DATE NOT NULL,
      minutes_worked INTEGER NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'submitted',
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 300,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_jinji_payroll_run (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      payroll_month VARCHAR NOT NULL,
      gross_total_encrypted VARCHAR NOT NULL,
      statutory_total_encrypted VARCHAR,
      net_total_encrypted VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'draft',
      completed_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 300,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const table of [
    "vertex_atrecord_jinji_payroll_run",
    "vertex_atrecord_jinji_attendance",
    "vertex_atrecord_jinji_employee",
    "vertex_atrecord_keihi_expense",
    "vertex_atrecord_kousuu_project_cost",
    "vertex_atrecord_kousuu_task",
    "vertex_atrecord_keiyaku_obligation",
    "vertex_atrecord_keiyaku_amendment",
    "vertex_atrecord_keiyaku_signing_flow",
    "vertex_atrecord_keiyaku_counterparty",
    "vertex_atrecord_seikyu_recurring_schedule",
    "vertex_atrecord_seikyu_credit_note",
    "vertex_atrecord_seikyu_payment_received",
  ]) {
    await sql.raw(`DROP TABLE IF EXISTS ${table}`).execute(db);
  }
}
