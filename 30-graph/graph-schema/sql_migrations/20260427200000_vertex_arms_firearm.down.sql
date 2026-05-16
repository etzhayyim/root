DROP MATERIALIZED VIEW IF EXISTS mv_arms_active_by_holder;

DROP TABLE IF EXISTS edge_arms_firearm_to_permit;

DROP TABLE IF EXISTS edge_arms_firearm_to_holder;

DROP TABLE IF EXISTS vertex_arms_auth_session;

DROP TABLE IF EXISTS vertex_arms_custody_event;

DROP TABLE IF EXISTS vertex_arms_permit_pii;

DROP TABLE IF EXISTS vertex_arms_permit;

DROP TABLE IF EXISTS vertex_arms_firearm_pii;

DROP TABLE IF EXISTS vertex_arms_firearm;
