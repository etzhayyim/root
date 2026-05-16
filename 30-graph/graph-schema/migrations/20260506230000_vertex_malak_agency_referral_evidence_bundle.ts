import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_malak_agency_referral_evidence_bundle (
      vertex_id                 VARCHAR PRIMARY KEY,
      rkey                      VARCHAR NOT NULL,
      repo                      VARCHAR NOT NULL,
      bundle_id                 VARCHAR NOT NULL,
      referral_id               VARCHAR NOT NULL,
      evidence_ids_json         VARCHAR NOT NULL,
      resolved_evidence_json    VARCHAR NOT NULL,
      missing_evidence_ids_json VARCHAR NOT NULL,
      evidence_count            BIGINT NOT NULL,
      bundle_hash               VARCHAR NOT NULL,
      complete                  BOOLEAN NOT NULL DEFAULT false,
      created_at                VARCHAR NOT NULL,
      created_date              DATE NOT NULL,
      sensitivity_ord           BIGINT NOT NULL DEFAULT 100,
      owner_did                 VARCHAR NOT NULL,
      org_id                    VARCHAR,
      user_id                   VARCHAR,
      actor_did                 VARCHAR,
      org_did                   VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_evidence_bundle_referral_time
      ON vertex_malak_agency_referral_evidence_bundle (referral_id, created_at)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_evidence_bundle_complete
      ON vertex_malak_agency_referral_evidence_bundle (complete, created_at)
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_malak_agency_referral_evidence_bundle_complete`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_malak_agency_referral_evidence_bundle_referral_time`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_agency_referral_evidence_bundle`.execute(db);
  await sql`FLUSH`.execute(db);
}
