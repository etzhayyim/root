import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_yorishiroFlyio_cancellationJob — account closure / info-fetch job
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroFlyio_cancellationJob (
      vertex_id           VARCHAR PRIMARY KEY,
      job_id              VARCHAR NOT NULL,
      phase               VARCHAR NOT NULL,
      email               VARCHAR,
      delete_all_apps_first BOOLEAN,
      provider            VARCHAR,
      entry_url           VARCHAR,
      status              VARCHAR NOT NULL DEFAULT 'pending',
      created_at          VARCHAR NOT NULL,
      org_id              VARCHAR,
      user_id             VARCHAR,
      actor_id            VARCHAR,
      sensitivity_ord     BIGINT NOT NULL DEFAULT 2,
      owner_did           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_cancellationJob_job_id
      ON vertex_yorishiroFlyio_cancellationJob (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_cancellationJob_phase
      ON vertex_yorishiroFlyio_cancellationJob (phase)
  `.execute(db);

  // vertex_yorishiroFlyio_appDeleteJob — individual app deletion job
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroFlyio_appDeleteJob (
      vertex_id       VARCHAR PRIMARY KEY,
      job_id          VARCHAR NOT NULL,
      app_name        VARCHAR NOT NULL,
      org_slug        VARCHAR,
      provider        VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_appDeleteJob_job_id
      ON vertex_yorishiroFlyio_appDeleteJob (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_appDeleteJob_app_name
      ON vertex_yorishiroFlyio_appDeleteJob (app_name)
  `.execute(db);

  // vertex_yorishiroFlyio_orgDeleteJob — organization deletion job
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yorishiroFlyio_orgDeleteJob (
      vertex_id       VARCHAR PRIMARY KEY,
      job_id          VARCHAR NOT NULL,
      org_slug        VARCHAR NOT NULL,
      org_name        VARCHAR,
      provider        VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_orgDeleteJob_job_id
      ON vertex_yorishiroFlyio_orgDeleteJob (job_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_orgDeleteJob_org_slug
      ON vertex_yorishiroFlyio_orgDeleteJob (org_slug)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_yorishiroFlyio_orgDeleteJob`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroFlyio_appDeleteJob`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yorishiroFlyio_cancellationJob`.execute(db);
}
