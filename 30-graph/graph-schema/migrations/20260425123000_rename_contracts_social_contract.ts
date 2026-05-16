import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Normalize contracts social-contract table naming.
 *
 * The original migration created `vertex_contracts_socialContract`; because
 * identifiers are unquoted in RisingWave, the live table materialized as
 * `vertex_contracts_socialcontract`. The graph table convention is snake_case:
 * `vertex_<actor>_<kind>`, so the canonical name is
 * `vertex_contracts_social_contract`.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const oldTable = await sql<{ table_name: string }>`
    SELECT table_name
      FROM information_schema.tables
     WHERE table_name = 'vertex_contracts_socialcontract'
     LIMIT 1
  `.execute(db);

  if (oldTable.rows.length > 0) {
    await sql`
      ALTER TABLE vertex_contracts_socialcontract
      RENAME TO vertex_contracts_social_contract
    `.execute(db);
  }

  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_jurisdiction
      ON vertex_contracts_social_contract (jurisdiction)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_source_record_id
      ON vertex_contracts_social_contract (source_record_id)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  const newTable = await sql<{ table_name: string }>`
    SELECT table_name
      FROM information_schema.tables
     WHERE table_name = 'vertex_contracts_social_contract'
     LIMIT 1
  `.execute(db);

  if (newTable.rows.length > 0) {
    await sql`
      ALTER TABLE vertex_contracts_social_contract
      RENAME TO vertex_contracts_socialcontract
    `.execute(db);
  }
}
