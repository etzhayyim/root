import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0049 Phase B — register `gmail_upsert_contact` external Python UDF.
 *
 * Fired once per inbound gmail message (right after
 * `INSERT vertex_gmail_email`) to materialize the sender as a
 * `vertex_gmail_contact` row + `edge_gmail_email_from_contact` edge.
 *
 * The UDF is idempotent: concurrent syncs or re-runs see ON CONFLICT
 * DO NOTHING on both inserts. PDS `did.create` registration is
 * intentionally skipped here — a later promotion job can pick up rows
 * that cross an activity threshold.
 *
 * Use from SQL:
 *   SELECT gmail_upsert_contact(
 *     '{"emailId":"email-abc123",
 *       "fromAddr":"\"Alice\" <alice@example.com>",
 *       "accountDid":"did:web:gmail.gftd.ai"}'
 *   ) AS result;
 *
 * Handler: `20-actors/magatama/py/src/pymagatama/handlers/gmail_contact.py`.
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION gmail_upsert_contact(VARCHAR)
      RETURNS VARCHAR
      AS 'ai.gftd.apps.gmail.upsertContact'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS gmail_upsert_contact(VARCHAR)`.execute(db);
}
