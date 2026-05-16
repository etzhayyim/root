import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0032 — yabai T2 sender reputation UDF (pure SQL).
 *
 * Sits between T1 (classify_t1, vector-eval rule score) and T3
 * (classify_t3_phishing, LLM second opinion). T2 answers "have we
 * seen this sender's domain behave well in the past?" without ever
 * leaving RisingWave — plan-time inlined to a subquery over
 * `vertex_gmail_email`, no network hop.
 *
 * Score interpretation (higher = more suspicious):
 *   0..30  — established sender, healthy auth history → safe
 *   30..50 — some auth noise, moderate history → monitor
 *   50..100 — new + bad auth + never-seen domain → escalate
 *
 * Signals summed (all clamped to [0, 100]):
 *   +40  if fewer than 5 prior emails from this address (new sender)
 *   +20  if the earliest sighting is < 7 days ago (recently-arrived domain)
 *   +30  if SPF pass-rate over the window < 0.5
 *   +20  if DMARC pass-rate over the window < 0.5
 *   +10  if the sender has any prior phishing_alert row above T1=60
 *
 * Gating suggestion for the gmail Worker's INSERT..SELECT chain:
 *   WHERE classify_t1(...) >= 60
 *     AND yabai_sender_reputation(from_addr) >= 50
 * Under that combined gate, only ~5-10% of inbound volume reaches T3
 * (vs ~20% with T1 alone), keeping LLM spend bounded.
 *
 * Window is 30 days. Longer windows inflate state without improving
 * signal; shorter windows miss cyclical senders (monthly digests).
 */
// Two RW-specific rewrites made during first apply:
// - `created_at::timestamp` rejects gmail's ISO `...Z`-suffix varchar with
//   "Can't cast string to timestamp". Comparing on `created_date` (proper
//   date column) dodges the parser entirely.
// - `current_date` inside a SQL UDF body is misread as a bound parameter
//   ("Bind error: failed to find named parameter current_date"). `now()::date`
//   is accepted as a plain scalar.
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION yabai_sender_reputation(from_addr_arg varchar)
      RETURNS int
      LANGUAGE sql
      AS $$
        WITH stats AS (
          SELECT
            count(*)::int AS total_mails,
            sum(CASE WHEN spf_result  = 'pass' THEN 1 ELSE 0 END)::double precision
              / NULLIF(count(*), 0)   AS spf_pass_rate,
            sum(CASE WHEN dmarc_result = 'pass' THEN 1 ELSE 0 END)::double precision
              / NULLIF(count(*), 0)   AS dmarc_pass_rate,
            (now()::date - min(created_date))::int AS days_since_first_seen
          FROM vertex_gmail_email
          WHERE from_addr = from_addr_arg
            AND created_date > (now()::date - interval '30 days')
        ),
        prior AS (
          SELECT count(*)::int AS phish_hits
          FROM vertex_gmail_phishing_alert
          WHERE from_addr = from_addr_arg
            AND phishing_score >= 60
            AND created_date > (now()::date - interval '30 days')
        )
        SELECT LEAST(100,
            CASE WHEN COALESCE(stats.total_mails, 0) < 5 THEN 40 ELSE 0 END
          + CASE WHEN stats.days_since_first_seen IS NULL
                  OR stats.days_since_first_seen < 7 THEN 20 ELSE 0 END
          + CASE WHEN COALESCE(stats.spf_pass_rate, 0.0) < 0.5 THEN 30 ELSE 0 END
          + CASE WHEN COALESCE(stats.dmarc_pass_rate, 0.0) < 0.5 THEN 20 ELSE 0 END
          + CASE WHEN COALESCE(prior.phish_hits, 0) > 0 THEN 10 ELSE 0 END
        )::int AS score
        FROM stats, prior
      $$
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS yabai_sender_reputation(varchar)`.execute(db);
}
