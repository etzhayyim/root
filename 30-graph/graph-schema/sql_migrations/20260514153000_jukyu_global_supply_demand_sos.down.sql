DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_notification_outbox;
DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_company_exposure_rank;
DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_supply_chain_trace;
DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_global_balance;

DROP INDEX IF EXISTS idx_edge_jukyu_operates_company;
DROP INDEX IF EXISTS idx_edge_jukyu_supply_dst;
DROP INDEX IF EXISTS idx_edge_jukyu_supply_src;
DROP INDEX IF EXISTS idx_vertex_jukyu_notification_target;
DROP INDEX IF EXISTS idx_vertex_jukyu_exposure_rank;
DROP INDEX IF EXISTS idx_vertex_jukyu_exposure_company;
DROP INDEX IF EXISTS idx_vertex_jukyu_balance_country_product;
DROP INDEX IF EXISTS idx_vertex_jukyu_balance_domain_time;
DROP INDEX IF EXISTS idx_vertex_jukyu_supply_node_operator;
DROP INDEX IF EXISTS idx_vertex_jukyu_supply_node_domain_country;

DROP TABLE IF EXISTS edge_jukyu_exposure_triggers_signal;
DROP TABLE IF EXISTS edge_jukyu_company_operates_node;
DROP TABLE IF EXISTS edge_jukyu_supply_dependency;
DROP TABLE IF EXISTS vertex_jukyu_notification_signal;
DROP TABLE IF EXISTS vertex_jukyu_pregel_run;
DROP TABLE IF EXISTS vertex_jukyu_company_exposure;
DROP TABLE IF EXISTS vertex_jukyu_balance_observation;
DROP TABLE IF EXISTS vertex_jukyu_supply_node;
