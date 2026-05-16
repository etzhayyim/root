DROP MATERIALIZED VIEW IF EXISTS mv_automotive_package_supply_process_graph;

DROP TABLE IF EXISTS edge_automotive_package_references_patent;

DROP TABLE IF EXISTS edge_automotive_process_performed_by;

DROP TABLE IF EXISTS edge_automotive_responsible_party;

DROP TABLE IF EXISTS edge_automotive_intermediate_feeds_process;

DROP TABLE IF EXISTS edge_automotive_process_produces_intermediate;

DROP TABLE IF EXISTS edge_automotive_process_uses_material;

DROP TABLE IF EXISTS edge_automotive_material_supplied_by;

DROP TABLE IF EXISTS edge_automotive_package_requires_material;

DROP TABLE IF EXISTS vertex_automotive_responsibility_assignment;

DROP TABLE IF EXISTS vertex_automotive_intermediate_part;

DROP TABLE IF EXISTS vertex_automotive_material_requirement;
