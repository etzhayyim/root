-- migration: 20260513010000_vertex_email_blocker (DOWN)
DROP MATERIALIZED VIEW IF EXISTS graphar.mv_email_blocker_count_by_type;
DROP MATERIALIZED VIEW IF EXISTS graphar.mv_email_blocker_pending;
DROP TABLE IF EXISTS graphar.edge_email_blocked_by;
DROP TABLE IF EXISTS graphar.vertex_email_blocker;
