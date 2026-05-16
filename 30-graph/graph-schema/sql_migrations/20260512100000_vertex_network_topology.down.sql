DROP MATERIALIZED VIEW IF EXISTS mv_app_install_reach;
DROP MATERIALIZED VIEW IF EXISTS mv_device_process_summary;
DROP MATERIALIZED VIEW IF EXISTS mv_device_disk_pressure;
DROP MATERIALIZED VIEW IF EXISTS mv_device_app_inventory;
DROP MATERIALIZED VIEW IF EXISTS mv_device_latest_snapshot;

DROP INDEX IF EXISTS idx_edge_device_app_dst;
DROP INDEX IF EXISTS idx_edge_device_app_src;
DROP TABLE IF EXISTS edge_device_has_app_installed;
DROP INDEX IF EXISTS idx_edge_proc_app_src;
DROP TABLE IF EXISTS edge_process_is_app;
DROP INDEX IF EXISTS idx_edge_device_proc_src;
DROP TABLE IF EXISTS edge_device_runs_process;
DROP INDEX IF EXISTS idx_edge_device_disk_src;
DROP TABLE IF EXISTS edge_device_has_disk;
DROP INDEX IF EXISTS idx_edge_device_iface_src;
DROP TABLE IF EXISTS edge_device_has_interface;
DROP INDEX IF EXISTS idx_edge_scan_device_src;
DROP TABLE IF EXISTS edge_scan_observed_device;

DROP INDEX IF EXISTS idx_app_launchitem_scan;
DROP TABLE IF EXISTS vertex_app_launchitem;
DROP INDEX IF EXISTS idx_app_process_bundle;
DROP INDEX IF EXISTS idx_app_process_pid;
DROP INDEX IF EXISTS idx_app_process_scan;
DROP TABLE IF EXISTS vertex_app_process;
DROP INDEX IF EXISTS idx_app_install_bundle;
DROP INDEX IF EXISTS idx_app_install_scan;
DROP TABLE IF EXISTS vertex_app_installation;
DROP INDEX IF EXISTS idx_app_installed_bundle;
DROP TABLE IF EXISTS vertex_app_installed;

DROP INDEX IF EXISTS idx_device_display_scan;
DROP TABLE IF EXISTS vertex_device_display;
DROP INDEX IF EXISTS idx_device_battery_scan;
DROP TABLE IF EXISTS vertex_device_battery;
DROP INDEX IF EXISTS idx_device_disk_scan;
DROP TABLE IF EXISTS vertex_device_disk;
DROP INDEX IF EXISTS idx_device_snapshot_device;
DROP INDEX IF EXISTS idx_device_snapshot_scan;
DROP TABLE IF EXISTS vertex_device_snapshot;
DROP INDEX IF EXISTS idx_device_hostname;
DROP INDEX IF EXISTS idx_device_serial;
DROP INDEX IF EXISTS idx_device_hw_uuid;
DROP TABLE IF EXISTS vertex_device;

DROP MATERIALIZED VIEW IF EXISTS mv_network_ip_collision;
DROP MATERIALIZED VIEW IF EXISTS mv_network_split_l2_detection;
DROP MATERIALIZED VIEW IF EXISTS mv_network_segment_summary;

DROP INDEX IF EXISTS idx_edge_seg_gw_src;
DROP TABLE IF EXISTS edge_segment_has_gateway;

DROP INDEX IF EXISTS idx_edge_host_seg_dst;
DROP INDEX IF EXISTS idx_edge_host_seg_src;
DROP TABLE IF EXISTS edge_host_in_segment;

DROP INDEX IF EXISTS idx_edge_iface_seg_dst;
DROP INDEX IF EXISTS idx_edge_iface_seg_src;
DROP TABLE IF EXISTS edge_interface_in_segment;

DROP INDEX IF EXISTS idx_edge_scan_iface_src;
DROP TABLE IF EXISTS edge_scan_observed_interface;

DROP INDEX IF EXISTS idx_network_segment_gw;
DROP INDEX IF EXISTS idx_network_segment_scan;
DROP TABLE IF EXISTS vertex_network_segment;

DROP INDEX IF EXISTS idx_network_host_iface;
DROP INDEX IF EXISTS idx_network_host_mac;
DROP INDEX IF EXISTS idx_network_host_scan_ip;
DROP TABLE IF EXISTS vertex_network_host;

DROP INDEX IF EXISTS idx_network_interface_gw;
DROP INDEX IF EXISTS idx_network_interface_scan;
DROP TABLE IF EXISTS vertex_network_interface;

DROP INDEX IF EXISTS idx_network_scan_host;
DROP INDEX IF EXISTS idx_network_scan_at;
DROP TABLE IF EXISTS vertex_network_scan;
