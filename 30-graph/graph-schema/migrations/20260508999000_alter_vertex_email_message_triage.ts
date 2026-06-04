/**
 * ALTER vertex_email_message to support outlook.triage.v1 LangGraph.
 *
 * Phase 4 of the email triage rollout: extend the m365 / kyber-inbox
 * Outlook email table with the same triage columns gmail received in
 * 20260508996000_alter_vertex_gmail_email_triage.ts so outlook.triage
 * can flag rows with classification/score/reasons.
 *
 * vertex_email_message is **shared** across:
 *   - kyber inbox appview (60-apps/etzhayyim-project-kyber-qzzg06nh)
 *   - m365-ingest pipeline (20-actors/m365-ingest)
 *
 * Both writers stay unchanged; only the triage agent populates the new
 * columns. Body/subject are signal:v1: encrypted (Tier-2 BEC), so the
 * triage agent operates strictly on metadata signals (auth headers +
 * from_address/from_domain + reply_to + first_seen_from_domain).
 */
import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS triaged_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS triage_classification VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS triage_score BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS triage_reasons VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_email_message_untriaged ON vertex_email_message (triaged_at)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_email_message_untriaged`.execute(db);
  await sql`ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS triage_reasons`.execute(db);
  await sql`ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS triage_score`.execute(db);
  await sql`ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS triage_classification`.execute(db);
  await sql`ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS triaged_at`.execute(db);
}
