DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_bill_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_active_service_inventory;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_active_product_inventory;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_open_service_orders;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_open_product_orders;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tmf_active_offerings;

DROP TABLE IF EXISTS edge_telecom_tmf_service_order_product_order;

DROP TABLE IF EXISTS edge_telecom_tmf_inventory_order;

DROP TABLE IF EXISTS edge_telecom_tmf_order_offering;

DROP TABLE IF EXISTS vertex_telecom_tmf_customer_bill;

DROP TABLE IF EXISTS vertex_telecom_tmf_customer_account;

DROP TABLE IF EXISTS vertex_telecom_tmf_service_inventory;

DROP TABLE IF EXISTS vertex_telecom_tmf_service_activation;

DROP TABLE IF EXISTS vertex_telecom_tmf_service_order;

DROP TABLE IF EXISTS vertex_telecom_tmf_product_inventory;

DROP TABLE IF EXISTS vertex_telecom_tmf_product_order;

DROP TABLE IF EXISTS vertex_telecom_tmf_product_offering;
