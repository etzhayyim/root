import { Kysely, sql } from 'kysely';

/**
 * ALTER vertex_email_message to support BEC/phishing screening.
 *
 * Fields mirror vertex_gmail_email (per-provider header normalisation).
 * M365 ingest populates these from Graph `internetMessageHeaders`:
 *   - Authentication-Results → spf_result / dkim_result / dmarc_result / auth_results_raw
 *   - From header (non-encrypted) → from_name (display name)
 *   - Return-Path → return_path
 *   - Reply-To → reply_to
 *
 * Used by 4 BEC screening heuristics:
 *   1. SPF/DKIM/DMARC fail → likely spoof
 *   2. from_name lookalike vs vertex_m365_user.display_name (Levenshtein distance)
 *   3. First-contact sender (first_seen < 7d) + urgent keyword in subject_hash collision
 *   4. Mass-contact domains (gmail.com) with volume anomaly vs established pattern
 */
export async function up(db: Kysely<any>): Promise<void> {
  const alters = [
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS from_name VARCHAR",
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS reply_to VARCHAR",
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS return_path VARCHAR",
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS spf_result VARCHAR",
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS dkim_result VARCHAR",
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS dmarc_result VARCHAR",
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS auth_results_raw VARCHAR",
    "ALTER TABLE vertex_email_message ADD COLUMN IF NOT EXISTS first_seen_from_domain VARCHAR",
  ];
  for (const a of alters) await sql.raw(a).execute(db);

  // BEC-screening MV: first-contact senders (new domain within last 7 days)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_email_first_contact_senders AS
    SELECT
      account_did,
      from_address,
      from_domain,
      MIN(received_at) AS first_seen,
      MAX(received_at) AS last_seen,
      COUNT(*) AS msg_count
    FROM vertex_email_message
    WHERE account_did IS NOT NULL AND from_address IS NOT NULL
    GROUP BY account_did, from_address, from_domain
  `.execute(db);

  // BEC-screening MV: auth-failure hits (SPF/DKIM/DMARC = fail)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_email_auth_fail AS
    SELECT
      account_did,
      from_address,
      from_domain,
      received_at,
      spf_result,
      dkim_result,
      dmarc_result,
      subject_hash
    FROM vertex_email_message
    WHERE
      spf_result = 'fail' OR dkim_result = 'fail' OR dmarc_result = 'fail' OR
      spf_result = 'softfail' OR dmarc_result = 'softfail'
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_email_first_contact ON mv_email_first_contact_senders (account_did, first_seen)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_email_from_name ON vertex_email_message (from_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_email_dmarc ON vertex_email_message (dmarc_result)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_email_auth_fail`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_email_first_contact_senders`.execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS first_seen_from_domain").execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS auth_results_raw").execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS dmarc_result").execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS dkim_result").execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS spf_result").execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS return_path").execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS reply_to").execute(db);
  await sql.raw("ALTER TABLE vertex_email_message DROP COLUMN IF EXISTS from_name").execute(db);
}
