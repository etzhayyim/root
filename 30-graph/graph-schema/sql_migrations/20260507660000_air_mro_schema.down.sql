DROP MATERIALIZED VIEW IF EXISTS mv_air_fleet_dispatch_reliability;

DROP INDEX IF EXISTS idx_air_mro_ad_compliance_ad_no;

DROP INDEX IF EXISTS idx_air_mro_component_part_serial;

DROP INDEX IF EXISTS idx_air_mro_work_order_reg_status;

DROP TABLE IF EXISTS edge_air_work_order_on_component;

DROP TABLE IF EXISTS vertex_air_mro_reliability_report;

DROP TABLE IF EXISTS vertex_air_mro_ad_compliance;

DROP TABLE IF EXISTS vertex_air_mro_component;

DROP TABLE IF EXISTS vertex_air_mro_work_order;
