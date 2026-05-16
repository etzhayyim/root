import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * Migration 0072: calendar core graph spine.
 *
 * Adds typed calendar vertices/edges and two narrow MVs.
 * Existing AT records continue to be mirrored in vertex_repo_record; these
 * tables provide query ergonomics and future projector targets.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_calendar_event (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      event_id          VARCHAR,
      title             VARCHAR,
      description       VARCHAR,
      start_time        VARCHAR,
      end_time          VARCHAR,
      location          VARCHAR,
      all_day           VARCHAR,
      timezone          VARCHAR,
      visibility        VARCHAR,
      status            VARCHAR,
      organizer_did     VARCHAR,
      recurrence_id     VARCHAR,
      attendees_json    VARCHAR,
      reminders_json    VARCHAR,
      icalendar_uid     VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  const existingEventColumns = new Set(
    (
      await sql<{ column_name: string }>`
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'vertex_calendar_event'
      `.execute(db)
    ).rows.map((r) => r.column_name)
  );

  if (!existingEventColumns.has("organizer_did")) {
    await sql`ALTER TABLE vertex_calendar_event ADD COLUMN organizer_did VARCHAR`.execute(db);
  }
  if (!existingEventColumns.has("start_time")) {
    await sql`ALTER TABLE vertex_calendar_event ADD COLUMN start_time VARCHAR`.execute(db);
  }
  if (!existingEventColumns.has("event_id")) {
    await sql`ALTER TABLE vertex_calendar_event ADD COLUMN event_id VARCHAR`.execute(db);
  }

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_calendar_event_event_id ON vertex_calendar_event (event_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_calendar_event_organizer_start ON vertex_calendar_event (organizer_did, start_time)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_calendar_invitation (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      invitation_id     VARCHAR,
      event_id          VARCHAR,
      invitee_did       VARCHAR,
      organizer_did     VARCHAR,
      status            VARCHAR,
      responded_at      VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_calendar_invitation_event_id ON vertex_calendar_invitation (event_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_calendar_invitation_invitee_status ON vertex_calendar_invitation (invitee_did, status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_calendar_rsvp (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      rsvp_id           VARCHAR,
      event_id          VARCHAR,
      respondent_did    VARCHAR,
      response          VARCHAR,
      comment           VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_calendar_rsvp_event_id ON vertex_calendar_rsvp (event_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_calendar_rsvp_respondent ON vertex_calendar_rsvp (respondent_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_calendar_reminder (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      reminder_id       VARCHAR,
      event_id          VARCHAR,
      target_did        VARCHAR,
      remind_at         VARCHAR,
      channel           VARCHAR,
      status            VARCHAR,
      message           VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_calendar_reminder_event_id ON vertex_calendar_reminder (event_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_calendar_event_owner (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      role              VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_calendar_event_owner_src ON edge_calendar_event_owner (src_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_calendar_event_attendee (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      invitation_id     VARCHAR,
      status            VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_calendar_event_attendee_src ON edge_calendar_event_attendee (src_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_calendar_events_by_owner_time AS
    SELECT
      organizer_did,
      SUBSTRING(COALESCE(start_time, ''), 1, 10) AS start_day,
      COUNT(*) AS event_count,
      MAX(_seq) AS last_seq
    FROM vertex_calendar_event
    WHERE organizer_did IS NOT NULL
    GROUP BY organizer_did, SUBSTRING(COALESCE(start_time, ''), 1, 10)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_calendar_rsvp_summary AS
    SELECT
      event_id,
      COUNT(*) AS total_rsvps,
      SUM(CASE WHEN LOWER(COALESCE(response, '')) = 'accept' THEN 1 ELSE 0 END) AS accept_count,
      SUM(CASE WHEN LOWER(COALESCE(response, '')) = 'decline' THEN 1 ELSE 0 END) AS decline_count,
      SUM(CASE WHEN LOWER(COALESCE(response, '')) = 'tentative' THEN 1 ELSE 0 END) AS tentative_count,
      MAX(_seq) AS last_seq
    FROM vertex_calendar_rsvp
    WHERE event_id IS NOT NULL
    GROUP BY event_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_calendar_rsvp_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_calendar_events_by_owner_time`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_calendar_event_attendee`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_calendar_event_owner`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_calendar_reminder`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_calendar_rsvp`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_calendar_invitation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_calendar_event`.execute(db);
}
