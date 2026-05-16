CREATE MATERIALIZED VIEW IF NOT EXISTS mv_workspace_sync_lag AS
    SELECT
      provider,
      source_kind,
      scope_key,
      MAX(ended_at) AS last_ended_at,
      MAX(CASE WHEN status = 'ok' THEN ended_at ELSE '' END) AS last_success_at,
      SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count_total,
      SUM(CASE WHEN status = 'failed' AND SUBSTRING(COALESCE(ended_at, ''), 1, 10) >= SUBSTRING(CAST(NOW() AS VARCHAR), 1, 10) THEN 1 ELSE 0 END) AS failed_count_today
    FROM vertex_workspace_sync_job
    GROUP BY provider, source_kind, scope_key;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_workspace_activity_daily AS
    WITH activity_union AS (
      SELECT owner_did, SUBSTRING(COALESCE(received_at, sent_at, ''), 1, 10) AS activity_day, 'message' AS activity_kind
      FROM vertex_workspace_message
      WHERE owner_did IS NOT NULL
      UNION ALL
      SELECT owner_did, SUBSTRING(COALESCE(start_at, ''), 1, 10) AS activity_day, 'event' AS activity_kind
      FROM vertex_workspace_event
      WHERE owner_did IS NOT NULL
      UNION ALL
      SELECT owner_did, SUBSTRING(COALESCE(modified_at, ''), 1, 10) AS activity_day, 'file' AS activity_kind
      FROM vertex_workspace_file
      WHERE owner_did IS NOT NULL
    )
    SELECT
      owner_did,
      activity_day,
      activity_kind,
      COUNT(*) AS activity_count
    FROM activity_union
    WHERE activity_day <> ''
    GROUP BY owner_did, activity_day, activity_kind;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_workspace_action_queue AS
    WITH unread AS (
      SELECT owner_did, COUNT(*) AS unread_message_count
      FROM vertex_workspace_message
      WHERE owner_did IS NOT NULL
        AND COALESCE(is_read, FALSE) = FALSE
      GROUP BY owner_did
    ),
    upcoming AS (
      SELECT owner_did, COUNT(*) AS upcoming_event_count
      FROM vertex_workspace_event
      WHERE owner_did IS NOT NULL
        AND SUBSTRING(COALESCE(start_at, ''), 1, 10) >= SUBSTRING(CAST(NOW() AS VARCHAR), 1, 10)
      GROUP BY owner_did
    ),
    stale_threads AS (
      SELECT owner_did, COUNT(*) AS stale_thread_count
      FROM vertex_workspace_thread
      WHERE owner_did IS NOT NULL
        AND SUBSTRING(COALESCE(last_message_at, ''), 1, 10) <= SUBSTRING(CAST(NOW() AS VARCHAR), 1, 10)
      GROUP BY owner_did
    ),
    owners AS (
      SELECT owner_did FROM vertex_workspace_message WHERE owner_did IS NOT NULL
      UNION
      SELECT owner_did FROM vertex_workspace_event WHERE owner_did IS NOT NULL
      UNION
      SELECT owner_did FROM vertex_workspace_thread WHERE owner_did IS NOT NULL
    )
    SELECT
      o.owner_did,
      COALESCE(u.unread_message_count, 0) AS unread_message_count,
      COALESCE(e.upcoming_event_count, 0) AS upcoming_event_count,
      COALESCE(s.stale_thread_count, 0) AS stale_thread_count,
      (COALESCE(u.unread_message_count, 0) * 3 + COALESCE(e.upcoming_event_count, 0) * 2 + COALESCE(s.stale_thread_count, 0)) AS action_score
    FROM owners o
    LEFT JOIN unread u ON u.owner_did = o.owner_did
    LEFT JOIN upcoming e ON e.owner_did = o.owner_did
    LEFT JOIN stale_threads s ON s.owner_did = o.owner_did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_workspace_contact_strength AS
    WITH contact_edges AS (
      SELECT owner_did, dst_vid AS contact_vid, 1.0 AS weight
      FROM edge_workspace_message_from_contact
      WHERE owner_did IS NOT NULL
      UNION ALL
      SELECT owner_did, dst_vid AS contact_vid, 0.8 AS weight
      FROM edge_workspace_message_to_contact
      WHERE owner_did IS NOT NULL
      UNION ALL
      SELECT owner_did, dst_vid AS contact_vid, 1.2 AS weight
      FROM edge_workspace_event_attendee_contact
      WHERE owner_did IS NOT NULL
    )
    SELECT
      owner_did,
      contact_vid,
      COUNT(*) AS interaction_count,
      SUM(weight) AS strength_score
    FROM contact_edges
    GROUP BY owner_did, contact_vid;
