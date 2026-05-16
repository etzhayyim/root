import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_agent_minimax_evaluation
    ADD COLUMN IF NOT EXISTS counterparty_uncertainty DOUBLE PRECISION NOT NULL DEFAULT 0.0
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_agent_minimax_evaluation
    DROP COLUMN IF EXISTS counterparty_uncertainty
  `.execute(db);
}
