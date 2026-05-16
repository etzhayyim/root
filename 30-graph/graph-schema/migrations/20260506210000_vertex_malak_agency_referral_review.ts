import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_malak_agency_referral_review (
      vertex_id         VARCHAR PRIMARY KEY,
      rkey              VARCHAR NOT NULL,
      repo              VARCHAR NOT NULL,
      review_id         VARCHAR NOT NULL,
      referral_id       VARCHAR NOT NULL,
      decision          VARCHAR NOT NULL,
      draft_state       VARCHAR NOT NULL,
      reviewer_did      VARCHAR NOT NULL,
      reviewer_role     VARCHAR NOT NULL DEFAULT '',
      reason            VARCHAR NOT NULL,
      approval_ref      VARCHAR NOT NULL DEFAULT '',
      external_case_ref VARCHAR NOT NULL DEFAULT '',
      notes             VARCHAR NOT NULL DEFAULT '',
      payload_hash      VARCHAR NOT NULL,
      created_at        VARCHAR NOT NULL,
      created_date      DATE NOT NULL,
      sensitivity_ord   BIGINT NOT NULL DEFAULT 100,
      owner_did         VARCHAR NOT NULL,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_did         VARCHAR,
      org_did           VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_review_referral_time
      ON vertex_malak_agency_referral_review (referral_id, created_at)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_review_decision_time
      ON vertex_malak_agency_referral_review (decision, created_at)
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_malak_agency_referral_review_decision_time`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_malak_agency_referral_review_referral_time`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_agency_referral_review`.execute(db);
  await sql`FLUSH`.execute(db);
}
