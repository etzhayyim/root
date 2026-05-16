DROP MATERIALIZED VIEW IF EXISTS mv_robotics_supplier_rfq_export;

DROP MATERIALIZED VIEW IF EXISTS mv_robotics_manufacturing_package_readiness;

DROP TABLE IF EXISTS edge_robotics_package_uses_control_adapter;

DROP TABLE IF EXISTS edge_robotics_package_rfq;

DROP TABLE IF EXISTS edge_robotics_process_has_quality_gate;

DROP TABLE IF EXISTS edge_robotics_process_produces_file;

DROP TABLE IF EXISTS edge_robotics_process_consumes_file;

DROP TABLE IF EXISTS edge_robotics_package_has_process;

DROP TABLE IF EXISTS edge_robotics_package_has_file;

DROP TABLE IF EXISTS vertex_robotics_control_adapter_spec;

DROP TABLE IF EXISTS vertex_robotics_rfq;

DROP TABLE IF EXISTS vertex_robotics_quality_gate;

DROP TABLE IF EXISTS vertex_robotics_manufacturing_process;

DROP TABLE IF EXISTS vertex_robotics_product_file;

DROP TABLE IF EXISTS vertex_robotics_product_package;
