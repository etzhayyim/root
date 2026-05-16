import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_saiban_court — 33 courts (JP 8 + USA 5 + UK 6 + DE 8 + FR 6)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_saiban_court (
      vertex_id       VARCHAR PRIMARY KEY,
      court_id        VARCHAR NOT NULL,
      name_ja         VARCHAR NOT NULL,
      name_en         VARCHAR NOT NULL,
      court_level     VARCHAR NOT NULL,
      jurisdiction    VARCHAR NOT NULL,
      court_did       VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'active',
      actor_did       VARCHAR NOT NULL,
      org_did         VARCHAR NOT NULL,
      created_at      VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_court_jurisdiction
      ON vertex_saiban_court (jurisdiction)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_court_court_id
      ON vertex_saiban_court (court_id)
  `.execute(db);

  // vertex_saiban_jiken — legal cases (all types)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_saiban_jiken (
      vertex_id         VARCHAR PRIMARY KEY,
      jiken_id          VARCHAR NOT NULL,
      jiken_did         VARCHAR,
      case_number       VARCHAR,
      case_type         VARCHAR NOT NULL DEFAULT 'civil',
      status            VARCHAR NOT NULL DEFAULT 'filed',
      court_id          VARCHAR,
      court_level       VARCHAR,
      judge_id          VARCHAR,
      title             VARCHAR,
      plaintiff         VARCHAR,
      defendant         VARCHAR,
      filed_at          VARCHAR,
      lawfirm_case_id   VARCHAR,
      hanrei_rkey       VARCHAR,
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL,
      created_at        VARCHAR NOT NULL,
      updated_at        VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_jiken_case_type
      ON vertex_saiban_jiken (case_type)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_jiken_court_id
      ON vertex_saiban_jiken (court_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_jiken_status
      ON vertex_saiban_jiken (status)
  `.execute(db);

  // vertex_saiban_judge — judge profiles (restricted)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_saiban_judge (
      vertex_id             VARCHAR PRIMARY KEY,
      judge_id              VARCHAR NOT NULL,
      judge_did             VARCHAR,
      name_ja               VARCHAR,
      name_en               VARCHAR,
      current_court_id      VARCHAR,
      current_court_level   VARCHAR,
      status                VARCHAR NOT NULL DEFAULT 'active',
      appointed_at          VARCHAR,
      actor_did             VARCHAR NOT NULL,
      org_did               VARCHAR NOT NULL,
      created_at            VARCHAR NOT NULL,
      updated_at            VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_judge_current_court_id
      ON vertex_saiban_judge (current_court_id)
  `.execute(db);

  // vertex_saiban_trial_event — scheduled hearings and events
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_saiban_trial_event (
      vertex_id       VARCHAR PRIMARY KEY,
      event_id        VARCHAR NOT NULL,
      jiken_id        VARCHAR NOT NULL,
      event_type      VARCHAR NOT NULL DEFAULT 'hearing',
      status          VARCHAR NOT NULL DEFAULT 'scheduled',
      title           VARCHAR,
      court_id        VARCHAR,
      judge_id        VARCHAR,
      scheduled_at    VARCHAR,
      location        VARCHAR,
      notes           VARCHAR,
      next_event_date VARCHAR,
      actor_did       VARCHAR NOT NULL,
      org_did         VARCHAR NOT NULL,
      created_at      VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_trial_event_jiken_id
      ON vertex_saiban_trial_event (jiken_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_trial_event_status
      ON vertex_saiban_trial_event (status)
  `.execute(db);

  // vertex_saiban_jurisdiction_map — prefecture/subject-matter → court mapping
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_saiban_jurisdiction_map (
      vertex_id                   VARCHAR PRIMARY KEY,
      map_id                      VARCHAR NOT NULL,
      court_id                    VARCHAR NOT NULL,
      court_level                 VARCHAR,
      region_code                 VARCHAR,
      region_name_ja              VARCHAR,
      prefecture_codes            VARCHAR,
      subject_matter              VARCHAR,
      monetary_threshold_yen      DOUBLE PRECISION,
      notes                       VARCHAR,
      actor_did                   VARCHAR NOT NULL,
      org_did                     VARCHAR NOT NULL,
      created_at                  VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_saiban_jurisdiction_map_court_id
      ON vertex_saiban_jurisdiction_map (court_id)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_saiban_jurisdiction_map`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_saiban_trial_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_saiban_judge`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_saiban_jiken`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_saiban_court`.execute(db);
}
