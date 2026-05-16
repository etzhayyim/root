DROP MATERIALIZED VIEW IF EXISTS mv_telecom_npn_enrollment_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_npn_prose_policy_state;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_npn_nsacf_admission_rate;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_npn_pni_inventory;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_npn_snpn_state;

DROP TABLE IF EXISTS edge_telecom_npn_enrollment_for_profile;

DROP TABLE IF EXISTS edge_telecom_npn_pni_under_cag;

DROP TABLE IF EXISTS edge_telecom_npn_cag_under_snpn;

DROP TABLE IF EXISTS vertex_telecom_npn_subscriber_enrollment;

DROP TABLE IF EXISTS vertex_telecom_npn_prose_policy;

DROP TABLE IF EXISTS vertex_telecom_npn_nsacf_decision;

DROP TABLE IF EXISTS vertex_telecom_npn_id_mapping;

DROP TABLE IF EXISTS vertex_telecom_npn_pni_slice;

DROP TABLE IF EXISTS vertex_telecom_npn_nid_allocation;

DROP TABLE IF EXISTS vertex_telecom_npn_cag;

DROP TABLE IF EXISTS vertex_telecom_npn_snpn_deployment;
