import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_gmail_email ADD COLUMN IF NOT EXISTS triaged_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email ADD COLUMN IF NOT EXISTS triage_classification VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email ADD COLUMN IF NOT EXISTS triage_score BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email ADD COLUMN IF NOT EXISTS triage_reasons VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gmail_email_untriaged ON vertex_gmail_email (triaged_at)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_gmail_email_untriaged`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email DROP COLUMN IF EXISTS triage_reasons`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email DROP COLUMN IF EXISTS triage_score`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email DROP COLUMN IF EXISTS triage_classification`.execute(db);
  await sql`ALTER TABLE vertex_gmail_email DROP COLUMN IF EXISTS triaged_at`.execute(db);
}
