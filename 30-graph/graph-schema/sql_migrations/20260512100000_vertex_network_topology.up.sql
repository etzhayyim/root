-- LAN topology scans as graph data.
--
-- Captures the output of `pymagatama.lan_topology.scan_all_async` per run:
-- the interfaces enumerated, the hosts observed on each interface (via
-- per-IF ARP sweep), and the derived L2 segments (one per distinct
-- gateway MAC seen on a given subnet).
--
-- Designed so that "two routers both NATing 192.168.1.0/24" — the dual-router
-- split-L2 condition that breaks Bonjour / ShareMouse / mDNS — is queryable
-- as `mv_network_split_l2_detection`, and IP collisions as
-- `mv_network_ip_collision`.
--
-- MV memory safety: every GROUP BY is bounded by (scan_id, subnet) or
-- (scan_id, gateway_mac); both are O(<10) per scan. No GROUP BY on
-- per-host keys.

-- ── vertex_network_scan ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_network_scan (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  host_did         VARCHAR,
  host_hostname    VARCHAR,
  scanned_at       VARCHAR NOT NULL,
  iface_count      BIGINT DEFAULT 0,
  total_hosts      BIGINT DEFAULT 0,
  segment_count    BIGINT DEFAULT 0,
  finding_count    BIGINT DEFAULT 0,
  findings_text    VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_network_scan_at
  ON vertex_network_scan (scanned_at DESC);
CREATE INDEX IF NOT EXISTS idx_network_scan_host
  ON vertex_network_scan (host_did, scanned_at DESC);

-- ── vertex_network_interface ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_network_interface (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  iface_name       VARCHAR NOT NULL,
  ip               VARCHAR,
  netmask          VARCHAR,
  prefix_len       BIGINT,
  mac              VARCHAR,
  medium           VARCHAR,
  is_active        BOOLEAN DEFAULT true,
  gateway_ip       VARCHAR,
  gateway_mac      VARCHAR,
  host_count       BIGINT DEFAULT 0,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_network_interface_scan
  ON vertex_network_interface (scan_id, iface_name);
CREATE INDEX IF NOT EXISTS idx_network_interface_gw
  ON vertex_network_interface (gateway_mac);

-- ── vertex_network_host ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_network_host (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  iface_name       VARCHAR NOT NULL,
  ip               VARCHAR NOT NULL,
  mac              VARCHAR NOT NULL,
  oui_hint         VARCHAR,
  is_gateway       BOOLEAN DEFAULT false,
  is_self          BOOLEAN DEFAULT false,
  is_random_mac    BOOLEAN DEFAULT false,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_network_host_scan_ip
  ON vertex_network_host (scan_id, ip);
CREATE INDEX IF NOT EXISTS idx_network_host_mac
  ON vertex_network_host (mac);
CREATE INDEX IF NOT EXISTS idx_network_host_iface
  ON vertex_network_host (scan_id, iface_name);

-- ── vertex_network_segment ──────────────────────────────────────────────
-- One row per distinct (scan_id, subnet, gateway_mac). A split-L2 condition
-- produces N rows with the same subnet but different gateway_mac.
CREATE TABLE IF NOT EXISTS vertex_network_segment (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  subnet_cidr      VARCHAR NOT NULL,
  gateway_ip       VARCHAR,
  gateway_mac      VARCHAR,
  gateway_oui_hint VARCHAR,
  iface_names      VARCHAR,
  host_count       BIGINT DEFAULT 0,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_network_segment_scan
  ON vertex_network_segment (scan_id, subnet_cidr);
CREATE INDEX IF NOT EXISTS idx_network_segment_gw
  ON vertex_network_segment (gateway_mac);

-- ── edge_scan_observed_interface ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_scan_observed_interface (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edge_scan_iface_src
  ON edge_scan_observed_interface (src_vid);

-- ── edge_interface_in_segment ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_interface_in_segment (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edge_iface_seg_src
  ON edge_interface_in_segment (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_iface_seg_dst
  ON edge_interface_in_segment (dst_vid);

-- ── edge_host_in_segment ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_host_in_segment (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  ip               VARCHAR,
  mac              VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edge_host_seg_src
  ON edge_host_in_segment (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_host_seg_dst
  ON edge_host_in_segment (dst_vid);

-- ── edge_segment_has_gateway ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_segment_has_gateway (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  gateway_ip       VARCHAR,
  gateway_mac      VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edge_seg_gw_src
  ON edge_segment_has_gateway (src_vid);

-- ── mv_network_segment_summary ──────────────────────────────────────────
-- Per (scan_id, subnet, gateway_mac): segment-level rollup.
-- Cardinality bounded by O(scans × subnets × routers/subnet) — tiny.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_network_segment_summary AS
SELECT
  s.scan_id,
  s.subnet_cidr,
  s.gateway_mac,
  s.gateway_ip,
  s.gateway_oui_hint,
  s.iface_names,
  s.host_count,
  s.created_at
FROM vertex_network_segment s;

-- ── mv_network_split_l2_detection ───────────────────────────────────────
-- For each (scan_id, subnet) flag if >1 distinct gateway_mac was observed.
-- That is the structural signature of a dual-router split-L2 condition.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_network_split_l2_detection AS
SELECT
  scan_id,
  subnet_cidr,
  COUNT(*)                            AS segment_count,
  COUNT(DISTINCT gateway_mac)         AS gateway_mac_count,
  SUM(host_count)                     AS total_hosts,
  (COUNT(DISTINCT gateway_mac) > 1)   AS is_split_l2
FROM vertex_network_segment
GROUP BY scan_id, subnet_cidr;

-- ── mv_network_ip_collision ─────────────────────────────────────────────
-- Per (scan_id, ip): how many distinct MACs claimed that IP across
-- different interfaces? >1 = active collision (two devices hand-shaking
-- to two different DHCPs that overlap the same range).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_network_ip_collision AS
SELECT
  scan_id,
  ip,
  COUNT(DISTINCT mac)                 AS mac_count,
  COUNT(DISTINCT iface_name)          AS iface_count,
  (COUNT(DISTINCT mac) > 1)           AS is_collision
FROM vertex_network_host
GROUP BY scan_id, ip;

-- ════════════════════════════════════════════════════════════════════════
-- Device / hardware inventory (host_inventory actor)
-- ════════════════════════════════════════════════════════════════════════
--
-- `vertex_device` is the stable identity (keyed by hardware_uuid /
-- serial_number). `vertex_device_snapshot` is the per-scan point-in-time
-- state. Hardware fields that virtually never change (serial, model,
-- chip_arch) live on `vertex_device`; volatile fields (cpu_usage,
-- memory_used, uptime) live on the snapshot row.

-- ── vertex_device ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_device (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  hardware_uuid    VARCHAR,
  serial_number    VARCHAR,
  hostname         VARCHAR,
  device_kind      VARCHAR,
  model_name       VARCHAR,
  model_identifier VARCHAR,
  chip_arch        VARCHAR,
  cpu_brand        VARCHAR,
  cpu_cores        BIGINT,
  cpu_threads      BIGINT,
  memory_gb        BIGINT,
  storage_gb       BIGINT,
  os_name          VARCHAR,
  os_version       VARCHAR,
  os_build         VARCHAR,
  first_seen_at    VARCHAR,
  last_seen_at     VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_hw_uuid
  ON vertex_device (hardware_uuid);
CREATE INDEX IF NOT EXISTS idx_device_serial
  ON vertex_device (serial_number);
CREATE INDEX IF NOT EXISTS idx_device_hostname
  ON vertex_device (hostname);

-- ── vertex_device_snapshot ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_device_snapshot (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  snapshot_at      VARCHAR NOT NULL,
  boot_time        VARCHAR,
  uptime_seconds   BIGINT,
  cpu_usage_x100   BIGINT,
  memory_used_mb   BIGINT,
  memory_free_mb   BIGINT,
  swap_used_mb     BIGINT,
  load_1m_x100     BIGINT,
  load_5m_x100     BIGINT,
  load_15m_x100    BIGINT,
  process_count    BIGINT,
  thread_count     BIGINT,
  thermal_state    VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_snapshot_scan
  ON vertex_device_snapshot (scan_id);
CREATE INDEX IF NOT EXISTS idx_device_snapshot_device
  ON vertex_device_snapshot (device_vid, snapshot_at DESC);

-- ── vertex_device_disk ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_device_disk (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  bsd_name         VARCHAR,
  mount_point      VARCHAR,
  fs_type          VARCHAR,
  size_gb          BIGINT,
  used_gb          BIGINT,
  available_gb     BIGINT,
  use_pct_x100     BIGINT,
  is_internal      BOOLEAN DEFAULT false,
  is_encrypted     BOOLEAN DEFAULT false,
  is_removable     BOOLEAN DEFAULT false,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_disk_scan
  ON vertex_device_disk (scan_id, device_vid);

-- ── vertex_device_battery ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_device_battery (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  charge_pct       BIGINT,
  cycle_count      BIGINT,
  condition        VARCHAR,
  is_charging      BOOLEAN DEFAULT false,
  is_plugged       BOOLEAN DEFAULT false,
  max_capacity_pct BIGINT,
  design_capacity_mah BIGINT,
  current_capacity_mah BIGINT,
  voltage_mv       BIGINT,
  amperage_ma      BIGINT,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_battery_scan
  ON vertex_device_battery (scan_id, device_vid);

-- ── vertex_device_display ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_device_display (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  display_name     VARCHAR,
  vendor_id        VARCHAR,
  product_id       VARCHAR,
  resolution_w     BIGINT,
  resolution_h     BIGINT,
  refresh_hz       BIGINT,
  pixel_depth_bits BIGINT,
  is_main          BOOLEAN DEFAULT false,
  is_builtin       BOOLEAN DEFAULT false,
  is_mirrored      BOOLEAN DEFAULT false,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_display_scan
  ON vertex_device_display (scan_id, device_vid);

-- ════════════════════════════════════════════════════════════════════════
-- Application inventory
-- ════════════════════════════════════════════════════════════════════════

-- ── vertex_app_installed ────────────────────────────────────────────────
-- Stable identity per app (keyed by bundle_id). One row per known app,
-- updated last_seen_at on every observation.
CREATE TABLE IF NOT EXISTS vertex_app_installed (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  bundle_id        VARCHAR NOT NULL,
  app_name         VARCHAR,
  vendor           VARCHAR,
  category         VARCHAR,
  install_kind     VARCHAR,
  first_seen_at    VARCHAR,
  last_seen_at     VARCHAR,
  latest_version   VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_installed_bundle
  ON vertex_app_installed (bundle_id);

-- ── vertex_app_installation ─────────────────────────────────────────────
-- One row per (scan, device, app). Captures the version actually present
-- on this device at scan time.
CREATE TABLE IF NOT EXISTS vertex_app_installation (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  app_vid          VARCHAR NOT NULL,
  bundle_id        VARCHAR NOT NULL,
  app_name         VARCHAR,
  version          VARCHAR,
  short_version    VARCHAR,
  app_path         VARCHAR,
  size_mb          BIGINT,
  install_date     VARCHAR,
  last_modified    VARCHAR,
  signature_authority VARCHAR,
  obtained_from    VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_install_scan
  ON vertex_app_installation (scan_id, device_vid);
CREATE INDEX IF NOT EXISTS idx_app_install_bundle
  ON vertex_app_installation (bundle_id);

-- ── vertex_app_process ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_app_process (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  pid              BIGINT NOT NULL,
  ppid             BIGINT,
  process_name     VARCHAR,
  command          VARCHAR,
  user_name        VARCHAR,
  cpu_pct_x100     BIGINT,
  memory_pct_x100  BIGINT,
  rss_kb           BIGINT,
  vsz_kb           BIGINT,
  started_at       VARCHAR,
  elapsed_seconds  BIGINT,
  bundle_id        VARCHAR,
  app_vid          VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_process_scan
  ON vertex_app_process (scan_id, device_vid);
CREATE INDEX IF NOT EXISTS idx_app_process_pid
  ON vertex_app_process (scan_id, pid);
CREATE INDEX IF NOT EXISTS idx_app_process_bundle
  ON vertex_app_process (bundle_id);

-- ── vertex_app_launchitem ───────────────────────────────────────────────
-- Combines LaunchAgents + LaunchDaemons. is_user discriminates.
CREATE TABLE IF NOT EXISTS vertex_app_launchitem (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  label            VARCHAR,
  plist_path       VARCHAR,
  program          VARCHAR,
  is_loaded        BOOLEAN DEFAULT false,
  is_user          BOOLEAN DEFAULT false,
  run_at_load      BOOLEAN DEFAULT false,
  keep_alive       BOOLEAN DEFAULT false,
  created_at       VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_launchitem_scan
  ON vertex_app_launchitem (scan_id, device_vid);

-- ════════════════════════════════════════════════════════════════════════
-- Cross-domain edges (device ↔ network ↔ app)
-- ════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS edge_scan_observed_device (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR NOT NULL,
  created_at       VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edge_scan_device_src
  ON edge_scan_observed_device (src_vid);

CREATE TABLE IF NOT EXISTS edge_device_has_interface (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR NOT NULL,
  iface_name       VARCHAR,
  created_at       VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edge_device_iface_src
  ON edge_device_has_interface (src_vid);

CREATE TABLE IF NOT EXISTS edge_device_has_disk (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR NOT NULL,
  created_at       VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edge_device_disk_src
  ON edge_device_has_disk (src_vid);

CREATE TABLE IF NOT EXISTS edge_device_runs_process (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR NOT NULL,
  pid              BIGINT,
  created_at       VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edge_device_proc_src
  ON edge_device_runs_process (src_vid);

CREATE TABLE IF NOT EXISTS edge_process_is_app (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR NOT NULL,
  bundle_id        VARCHAR,
  created_at       VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edge_proc_app_src
  ON edge_process_is_app (src_vid);

CREATE TABLE IF NOT EXISTS edge_device_has_app_installed (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR NOT NULL,
  bundle_id        VARCHAR,
  version          VARCHAR,
  created_at       VARCHAR NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edge_device_app_src
  ON edge_device_has_app_installed (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_device_app_dst
  ON edge_device_has_app_installed (dst_vid);

-- ════════════════════════════════════════════════════════════════════════
-- Streaming MVs over device / app data
-- ════════════════════════════════════════════════════════════════════════

-- Per device latest snapshot timestamp. Cardinality = device count (~10).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_device_latest_snapshot AS
SELECT
  device_vid,
  MAX(snapshot_at)  AS latest_snapshot_at,
  COUNT(*)          AS snapshot_count
FROM vertex_device_snapshot
GROUP BY device_vid;

-- Per (scan, device) app installation rollup. Cardinality bounded.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_device_app_inventory AS
SELECT
  scan_id,
  device_vid,
  COUNT(*)                          AS app_count,
  COUNT(DISTINCT bundle_id)         AS distinct_bundle_count,
  SUM(size_mb)                      AS total_size_mb
FROM vertex_app_installation
GROUP BY scan_id, device_vid;

-- Per (scan, device) disk pressure. SUM bounded by disk count (~5).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_device_disk_pressure AS
SELECT
  scan_id,
  device_vid,
  COUNT(*)              AS disk_count,
  SUM(size_gb)          AS total_size_gb,
  SUM(used_gb)          AS total_used_gb,
  SUM(available_gb)     AS total_available_gb
FROM vertex_device_disk
GROUP BY scan_id, device_vid;

-- Per (scan, device) process rollup. Cardinality scan×device, value
-- aggregated over potentially many processes (~500). Safe: no MAX over
-- wide VARCHAR.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_device_process_summary AS
SELECT
  scan_id,
  device_vid,
  COUNT(*)                AS process_count,
  COUNT(DISTINCT bundle_id) AS distinct_bundle_count,
  SUM(rss_kb)             AS total_rss_kb,
  AVG(cpu_pct_x100)::BIGINT AS avg_cpu_x100
FROM vertex_app_process
GROUP BY scan_id, device_vid;

-- Per app (bundle_id) installation reach. Cardinality = distinct apps
-- (~hundreds).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_app_install_reach AS
SELECT
  bundle_id,
  COUNT(DISTINCT device_vid) AS device_count,
  COUNT(DISTINCT scan_id)    AS scan_count,
  COUNT(*)                   AS total_observations
FROM vertex_app_installation
GROUP BY bundle_id;
