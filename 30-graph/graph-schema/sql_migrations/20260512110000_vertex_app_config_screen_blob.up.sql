-- App configuration + screen capture + IPFS blob schema.
--
-- Extends 20260512100000_vertex_network_topology with:
--   * App-level config (settings, accepted peers, port bindings)
--   * Screen captures (user-uploaded screenshots tied to a scan + app)
--   * IPFS content-addressed blobs (CIDv1, raw codec, sha2-256, base32 lower)
--
-- The blob layer is content-addressed so the same screenshot uploaded
-- twice produces a single `vertex_blob_ipfs` row, while every observation
-- (different scan, different app, different note) gets its own
-- `vertex_app_screenshot` row pointing at the blob.

-- ── vertex_blob_ipfs ────────────────────────────────────────────────────
-- One row per distinct content hash. PK = `ipfs:<cidv1-base32>`.
CREATE TABLE IF NOT EXISTS vertex_blob_ipfs (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  cid              VARCHAR NOT NULL,
  cid_version      BIGINT DEFAULT 1,
  multicodec       VARCHAR DEFAULT 'raw',
  multihash_code   VARCHAR DEFAULT 'sha2-256',
  multibase        VARCHAR DEFAULT 'base32-lower',
  size_bytes       BIGINT,
  mime_type        VARCHAR,
  sha256_hex       VARCHAR,
  storage_backend  VARCHAR,
  storage_uri      VARCHAR,
  first_seen_at    VARCHAR,
  last_seen_at     VARCHAR,
  is_placeholder   BOOLEAN DEFAULT false,
  created_at       VARCHAR NOT NULL
);

-- ── vertex_app_screenshot ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_app_screenshot (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR,
  device_vid       VARCHAR,
  app_vid          VARCHAR,
  bundle_id        VARCHAR,
  display_vid      VARCHAR,
  blob_cid         VARCHAR,
  blob_vid         VARCHAR,
  label            VARCHAR,
  description      VARCHAR,
  source           VARCHAR,
  width_px         BIGINT,
  height_px        BIGINT,
  captured_at      VARCHAR,
  created_at       VARCHAR NOT NULL
);

-- ── vertex_app_config_snapshot ──────────────────────────────────────────
-- Aggregate config blob captured for an app at a given scan.
CREATE TABLE IF NOT EXISTS vertex_app_config_snapshot (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  app_vid          VARCHAR NOT NULL,
  bundle_id        VARCHAR,
  config_kind      VARCHAR,
  config_source    VARCHAR,
  source_path      VARCHAR,
  config_version   VARCHAR,
  captured_at      VARCHAR,
  setting_count    BIGINT DEFAULT 0,
  notes            VARCHAR,
  created_at       VARCHAR NOT NULL
);

-- ── vertex_app_setting ──────────────────────────────────────────────────
-- Individual typed setting under a snapshot.
CREATE TABLE IF NOT EXISTS vertex_app_setting (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  snapshot_vid     VARCHAR NOT NULL,
  app_vid          VARCHAR NOT NULL,
  bundle_id        VARCHAR,
  setting_key      VARCHAR NOT NULL,
  setting_value    VARCHAR,
  value_type       VARCHAR,
  is_secret        BOOLEAN DEFAULT false,
  is_default       BOOLEAN DEFAULT false,
  created_at       VARCHAR NOT NULL
);

-- ── vertex_app_accepted_peer ────────────────────────────────────────────
-- An IP:port whitelisted by the app (e.g. ShareMouse accepted clients).
CREATE TABLE IF NOT EXISTS vertex_app_accepted_peer (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  app_vid          VARCHAR NOT NULL,
  bundle_id        VARCHAR,
  peer_address     VARCHAR NOT NULL,
  peer_port        BIGINT,
  peer_label       VARCHAR,
  peer_kind        VARCHAR,
  is_active        BOOLEAN DEFAULT true,
  last_seen_at     VARCHAR,
  created_at       VARCHAR NOT NULL
);

-- ── vertex_app_port_binding ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_app_port_binding (
  vertex_id        VARCHAR PRIMARY KEY,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,

  scan_id          VARCHAR NOT NULL,
  device_vid       VARCHAR NOT NULL,
  app_vid          VARCHAR NOT NULL,
  bundle_id        VARCHAR,
  protocol         VARCHAR,
  port             BIGINT,
  bind_address     VARCHAR,
  state            VARCHAR,
  is_listening     BOOLEAN DEFAULT true,
  pid              BIGINT,
  created_at       VARCHAR NOT NULL
);

-- ════════════════════════════════════════════════════════════════════════
-- Edges
-- ════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS edge_screenshot_blob (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  cid              VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_screenshot_depicts_app (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_device_has_screenshot (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_app_has_config_snapshot (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_config_snapshot_has_setting (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  setting_key      VARCHAR,
  created_at       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_app_accepts_peer (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  peer_address     VARCHAR,
  peer_port        BIGINT,
  created_at       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_app_binds_port (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  protocol         VARCHAR,
  port             BIGINT,
  created_at       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_peer_resolves_host (
  edge_id          VARCHAR PRIMARY KEY,
  src_vid          VARCHAR NOT NULL,
  dst_vid          VARCHAR NOT NULL,
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT DEFAULT 100,
  owner_did        VARCHAR,
  scan_id          VARCHAR,
  ip               VARCHAR,
  created_at       VARCHAR NOT NULL
);

-- ════════════════════════════════════════════════════════════════════════
-- Indexes (created after tables, separately, to avoid catalog races)
-- ════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_blob_ipfs_cid
  ON vertex_blob_ipfs (cid);
CREATE INDEX IF NOT EXISTS idx_blob_ipfs_sha
  ON vertex_blob_ipfs (sha256_hex);

CREATE INDEX IF NOT EXISTS idx_screenshot_scan
  ON vertex_app_screenshot (scan_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_app
  ON vertex_app_screenshot (app_vid);
CREATE INDEX IF NOT EXISTS idx_screenshot_blob
  ON vertex_app_screenshot (blob_cid);

CREATE INDEX IF NOT EXISTS idx_app_config_scan
  ON vertex_app_config_snapshot (scan_id, app_vid);
CREATE INDEX IF NOT EXISTS idx_app_config_app
  ON vertex_app_config_snapshot (app_vid);

CREATE INDEX IF NOT EXISTS idx_app_setting_snap
  ON vertex_app_setting (snapshot_vid);
CREATE INDEX IF NOT EXISTS idx_app_setting_app_key
  ON vertex_app_setting (app_vid, setting_key);

CREATE INDEX IF NOT EXISTS idx_app_peer_scan
  ON vertex_app_accepted_peer (scan_id, app_vid);
CREATE INDEX IF NOT EXISTS idx_app_peer_addr
  ON vertex_app_accepted_peer (peer_address);

CREATE INDEX IF NOT EXISTS idx_app_port_scan
  ON vertex_app_port_binding (scan_id, app_vid);
CREATE INDEX IF NOT EXISTS idx_app_port_proto_port
  ON vertex_app_port_binding (protocol, port);

CREATE INDEX IF NOT EXISTS idx_edge_screenshot_blob_src
  ON edge_screenshot_blob (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_screenshot_app_src
  ON edge_screenshot_depicts_app (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_dev_screenshot_src
  ON edge_device_has_screenshot (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_app_config_src
  ON edge_app_has_config_snapshot (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_snap_setting_src
  ON edge_config_snapshot_has_setting (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_app_peer_src
  ON edge_app_accepts_peer (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_app_port_src
  ON edge_app_binds_port (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_peer_host_src
  ON edge_peer_resolves_host (src_vid);

-- ════════════════════════════════════════════════════════════════════════
-- MVs
-- ════════════════════════════════════════════════════════════════════════

-- Per (scan, app) accepted-peer rollup. Cardinality bounded.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_app_accepted_peer_count AS
SELECT
  scan_id,
  app_vid,
  bundle_id,
  COUNT(*)                                 AS peer_count,
  COUNT(DISTINCT peer_address)             AS distinct_address_count,
  COUNT(*) FILTER (WHERE peer_port IS NOT NULL) AS with_port_count
FROM vertex_app_accepted_peer
GROUP BY scan_id, app_vid, bundle_id;

-- Per (scan, app) port binding rollup.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_app_port_binding_summary AS
SELECT
  scan_id,
  app_vid,
  bundle_id,
  COUNT(*)                                 AS binding_count,
  COUNT(DISTINCT port)                     AS distinct_port_count,
  COUNT(*) FILTER (WHERE protocol = 'tcp') AS tcp_count,
  COUNT(*) FILTER (WHERE protocol = 'udp') AS udp_count,
  COUNT(*) FILTER (WHERE is_listening)     AS listening_count
FROM vertex_app_port_binding
GROUP BY scan_id, app_vid, bundle_id;

-- Per app, latest config snapshot.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_app_config_latest AS
SELECT
  app_vid,
  bundle_id,
  MAX(captured_at)              AS latest_captured_at,
  COUNT(*)                      AS snapshot_count,
  SUM(setting_count)            AS total_settings_observed
FROM vertex_app_config_snapshot
GROUP BY app_vid, bundle_id;

-- Per app, screenshot count.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_app_screenshot_count AS
SELECT
  app_vid,
  bundle_id,
  COUNT(*)                       AS screenshot_count,
  COUNT(DISTINCT blob_cid)       AS distinct_blob_count
FROM vertex_app_screenshot
GROUP BY app_vid, bundle_id;

-- Per blob, observation count (how many distinct screenshots/scans
-- reference the same content hash).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_blob_ipfs_usage AS
SELECT
  blob_cid                       AS cid,
  COUNT(*)                       AS observation_count,
  COUNT(DISTINCT scan_id)        AS scan_count,
  COUNT(DISTINCT app_vid)        AS app_count
FROM vertex_app_screenshot
WHERE blob_cid IS NOT NULL
GROUP BY blob_cid;

-- Accepted peer ↔ observed network host join (per scan).
-- Surfaces peers that the app trusts but that aren't visible to the
-- scanner — i.e. on a different L2 segment.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_app_peer_reachability AS
SELECT
  p.scan_id,
  p.app_vid,
  p.bundle_id,
  p.peer_address,
  p.peer_port,
  COUNT(h.vertex_id)                    AS observation_count,
  COUNT(DISTINCT h.iface_name)          AS visible_iface_count,
  (COUNT(h.vertex_id) > 0)              AS is_reachable
FROM vertex_app_accepted_peer p
LEFT JOIN vertex_network_host h
  ON h.scan_id = p.scan_id AND h.ip = p.peer_address
GROUP BY p.scan_id, p.app_vid, p.bundle_id, p.peer_address, p.peer_port;
