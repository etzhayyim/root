DROP MATERIALIZED VIEW IF EXISTS mv_telecom_li_access_audit_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_li_delivery_loss;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_li_active_targets;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_li_warrant_state;

DROP TABLE IF EXISTS edge_telecom_li_audit_to_record;

DROP TABLE IF EXISTS edge_telecom_li_iri_for_event;

DROP TABLE IF EXISTS edge_telecom_li_target_under_warrant;

DROP TABLE IF EXISTS vertex_telecom_li_access_audit;

DROP TABLE IF EXISTS vertex_telecom_li_delivery_ack;

DROP TABLE IF EXISTS vertex_telecom_li_cc_delivery;

DROP TABLE IF EXISTS vertex_telecom_li_iri_delivery;

DROP TABLE IF EXISTS vertex_telecom_li_target;

DROP TABLE IF EXISTS vertex_telecom_li_warrant;
