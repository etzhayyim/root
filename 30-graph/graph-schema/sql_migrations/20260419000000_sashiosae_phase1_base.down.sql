DROP MATERIALIZED VIEW IF EXISTS mv_sashiosae_stats_by_type;

DROP TABLE IF EXISTS edge_sashiosae_case_notice;

DROP TABLE IF EXISTS vertex_atrecord_sashiosae_kanka_result;

DROP TABLE IF EXISTS vertex_atrecord_sashiosae_release;

DROP TABLE IF EXISTS vertex_atrecord_sashiosae_notice;

DROP TABLE IF EXISTS vertex_atrecord_sashiosae_choushuu_case;

ALTER TABLE vertex_page DROP COLUMN IF EXISTS extracted_for_sashiosae;
