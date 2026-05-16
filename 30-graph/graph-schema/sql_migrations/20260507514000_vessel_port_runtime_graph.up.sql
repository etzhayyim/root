ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS ship_id VARCHAR;

ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS imo_number VARCHAR;

ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS mmsi VARCHAR;

ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS name VARCHAR;

ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS vessel_type VARCHAR;

ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS flag_state VARCHAR;

ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION;

ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;

ALTER TABLE vertex_vessel_shipowner ADD COLUMN IF NOT EXISTS owner_id VARCHAR;

ALTER TABLE vertex_vessel_shipowner ADD COLUMN IF NOT EXISTS name VARCHAR;

ALTER TABLE vertex_vessel_shipowner ADD COLUMN IF NOT EXISTS country VARCHAR;

ALTER TABLE vertex_vessel_ship_registry ADD COLUMN IF NOT EXISTS registry_id VARCHAR;

ALTER TABLE vertex_vessel_ship_registry ADD COLUMN IF NOT EXISTS flag_state VARCHAR;

ALTER TABLE vertex_vessel_ship_registry ADD COLUMN IF NOT EXISTS authority_name VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS position_id VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS imo_number VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS mmsi VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS course DOUBLE PRECISION;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS speed_knots DOUBLE PRECISION;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS heading DOUBLE PRECISION;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS navigation_status VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS destination VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS eta VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS received_at VARCHAR;

ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS source_did VARCHAR;

ALTER TABLE vertex_vessel_voyage ADD COLUMN IF NOT EXISTS voyage_id VARCHAR;

ALTER TABLE vertex_vessel_voyage ADD COLUMN IF NOT EXISTS imo_number VARCHAR;

ALTER TABLE vertex_vessel_voyage ADD COLUMN IF NOT EXISTS port_locode VARCHAR;

ALTER TABLE vertex_vessel_port_call ADD COLUMN IF NOT EXISTS call_id VARCHAR;

ALTER TABLE vertex_vessel_port_call ADD COLUMN IF NOT EXISTS imo_number VARCHAR;

ALTER TABLE vertex_vessel_port_call ADD COLUMN IF NOT EXISTS port_locode VARCHAR;

ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS link_id VARCHAR;

ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS imo_number VARCHAR;

ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS entity_did VARCHAR;

ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS link_type VARCHAR;

ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS linked_at VARCHAR;

ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS berth_id VARCHAR;

ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS port_id VARCHAR;

ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS name VARCHAR;

ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS berth_type VARCHAR;

ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS length_m DOUBLE PRECISION;

ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS depth_m DOUBLE PRECISION;

ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS terminal_id VARCHAR;

ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS port_id VARCHAR;

ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS name VARCHAR;

ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS terminal_type VARCHAR;

ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS operator VARCHAR;

ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS capacity DOUBLE PRECISION;

ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS event_id VARCHAR;

ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS call_id VARCHAR;

ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS port_id VARCHAR;

ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS imo_number VARCHAR;

ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS event_type VARCHAR;

ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS event_timestamp VARCHAR;

ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS berth_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vessel_ship_ship_id ON vertex_vessel_ship (ship_id);

CREATE INDEX IF NOT EXISTS idx_vessel_ship_imo ON vertex_vessel_ship (imo_number);

CREATE INDEX IF NOT EXISTS idx_vessel_ship_mmsi ON vertex_vessel_ship (mmsi);

CREATE INDEX IF NOT EXISTS idx_vessel_ship_flag ON vertex_vessel_ship (flag_state);

CREATE INDEX IF NOT EXISTS idx_vessel_position_imo_received ON vertex_vessel_position (imo_number, received_at);

CREATE INDEX IF NOT EXISTS idx_vessel_position_mmsi_received ON vertex_vessel_position (mmsi, received_at);

CREATE INDEX IF NOT EXISTS idx_vessel_position_lat_lng ON vertex_vessel_position (latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_vessel_port_call_imo ON vertex_vessel_port_call (imo_number);

CREATE INDEX IF NOT EXISTS idx_vessel_port_call_port ON vertex_vessel_port_call (port_locode);

CREATE INDEX IF NOT EXISTS idx_port_berth_port ON vertex_port_berth (port_id);

CREATE INDEX IF NOT EXISTS idx_port_terminal_port ON vertex_port_terminal (port_id);

CREATE INDEX IF NOT EXISTS idx_port_call_event_port_type ON vertex_port_call_event (port_id, event_type);

CREATE INDEX IF NOT EXISTS idx_port_call_event_call ON vertex_port_call_event (call_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vessel_latest_position AS
    SELECT imo_number, max(received_at) AS latest_received_at, count(*) AS position_count
    FROM vertex_vessel_position
    GROUP BY imo_number;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vessel_flag_counts AS
    SELECT flag_state, count(*) AS vessel_count
    FROM vertex_vessel_ship
    GROUP BY flag_state;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_port_occupancy_event_counts AS
    SELECT port_id, event_type, count(*) AS event_count
    FROM vertex_port_call_event
    GROUP BY port_id, event_type;
