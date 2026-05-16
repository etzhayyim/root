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
    );

ALTER TABLE vertex_calendar_event ADD COLUMN organizer_did VARCHAR;

ALTER TABLE vertex_calendar_event ADD COLUMN start_time VARCHAR;

ALTER TABLE vertex_calendar_event ADD COLUMN event_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_calendar_event_event_id ON vertex_calendar_event (event_id);

CREATE INDEX IF NOT EXISTS idx_vertex_calendar_event_organizer_start ON vertex_calendar_event (organizer_did, start_time);

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
    );

CREATE INDEX IF NOT EXISTS idx_vertex_calendar_invitation_event_id ON vertex_calendar_invitation (event_id);

CREATE INDEX IF NOT EXISTS idx_vertex_calendar_invitation_invitee_status ON vertex_calendar_invitation (invitee_did, status);

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
    );

CREATE INDEX IF NOT EXISTS idx_vertex_calendar_rsvp_event_id ON vertex_calendar_rsvp (event_id);

CREATE INDEX IF NOT EXISTS idx_vertex_calendar_rsvp_respondent ON vertex_calendar_rsvp (respondent_did);

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
    );

CREATE INDEX IF NOT EXISTS idx_vertex_calendar_reminder_event_id ON vertex_calendar_reminder (event_id);

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
    );

CREATE INDEX IF NOT EXISTS idx_edge_calendar_event_owner_src ON edge_calendar_event_owner (src_vid);

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
    );

CREATE INDEX IF NOT EXISTS idx_edge_calendar_event_attendee_src ON edge_calendar_event_attendee (src_vid);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_calendar_events_by_owner_time AS
    SELECT
      organizer_did,
      SUBSTRING(COALESCE(start_time, ''), 1, 10) AS start_day,
      COUNT(*) AS event_count,
      MAX(_seq) AS last_seq
    FROM vertex_calendar_event
    WHERE organizer_did IS NOT NULL
    GROUP BY organizer_did, SUBSTRING(COALESCE(start_time, ''), 1, 10);

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
    GROUP BY event_id;
