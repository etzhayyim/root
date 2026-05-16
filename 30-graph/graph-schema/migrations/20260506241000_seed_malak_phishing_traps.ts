import type { Kysely } from "kysely";
import { sql } from "kysely";

const MALAK_DID = "did:web:malak.gftd.ai";
const EMAIL_TRAP_ID = "trap-email-malak-spamtrap-primary";
const EMAIL_TRAP_ADDRESS = "spamtrap@malak.gftd.ai";
const CREATED_AT = "2026-05-06T00:00:00.000Z";
const CREATED_DATE = "2026-05-06";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO vertex_malak_phishing_trap (
      vertex_id,
      rkey,
      repo,
      trap_id,
      trap_kind,
      address,
      provider,
      label,
      legal_basis,
      retention_policy,
      status,
      created_at,
      updated_at,
      created_date,
      sensitivity_ord,
      owner_did,
      org_id,
      user_id,
      actor_did,
      org_did
    )
    SELECT
      ${`at://${MALAK_DID}/ai.gftd.apps.malak.phishingTrap/${EMAIL_TRAP_ID}`},
      ${EMAIL_TRAP_ID},
      ${MALAK_DID},
      ${EMAIL_TRAP_ID},
      'email',
      ${EMAIL_TRAP_ADDRESS},
      'gftd-owned-inbound-mail',
      'Malak primary inbound-only phishing spamtrap',
      'owned_inbound_spamtrap_defensive_cti',
      'hash_and_preview_only',
      'active',
      ${CREATED_AT},
      ${CREATED_AT},
      CAST(${CREATED_DATE} AS DATE),
      100,
      ${MALAK_DID},
      ${MALAK_DID},
      ${MALAK_DID},
      ${MALAK_DID},
      ${MALAK_DID}
    WHERE NOT EXISTS (
      SELECT 1
      FROM vertex_malak_phishing_trap
      WHERE trap_id = ${EMAIL_TRAP_ID}
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_malak_phishing_trap
    WHERE trap_id = ${EMAIL_TRAP_ID}
  `.execute(db);
  await sql`FLUSH`.execute(db);
}
