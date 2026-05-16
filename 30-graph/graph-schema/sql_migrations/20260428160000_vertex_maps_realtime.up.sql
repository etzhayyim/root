CREATE TABLE IF NOT EXISTS vertex_maps_vehicle_position (
      feed_id          VARCHAR NOT NULL,
      vehicle_id       VARCHAR NOT NULL,
      ts               TIMESTAMPTZ NOT NULL,
      trip_id          VARCHAR,
      route_id         VARCHAR,
      stop_id          VARCHAR,
      lat              DOUBLE PRECISION,
      lng              DOUBLE PRECISION,
      bearing          REAL,
      speed_mps        REAL,
      occupancy_status VARCHAR,
      current_status   VARCHAR,
      congestion_level VARCHAR,
      label            VARCHAR,
      raw_pb_b64       VARCHAR,
      PRIMARY KEY (feed_id, vehicle_id, ts)
    );

CREATE TABLE IF NOT EXISTS vertex_maps_trip_update (
      feed_id               VARCHAR NOT NULL,
      trip_id               VARCHAR NOT NULL,
      stop_sequence         INT     NOT NULL,
      ts                    TIMESTAMPTZ NOT NULL,
      stop_id               VARCHAR,
      route_id              VARCHAR,
      schedule_relationship VARCHAR,
      arrival_delay_sec     INT,
      departure_delay_sec   INT,
      arrival_time          TIMESTAMPTZ,
      departure_time        TIMESTAMPTZ,
      uncertainty_sec       INT,
      PRIMARY KEY (feed_id, trip_id, stop_sequence, ts)
    );

CREATE TABLE IF NOT EXISTS vertex_maps_service_alert (
      feed_id            VARCHAR NOT NULL,
      alert_id           VARCHAR NOT NULL,
      ts                 TIMESTAMPTZ NOT NULL,
      cause              VARCHAR,
      effect             VARCHAR,
      severity           VARCHAR,
      header_text        VARCHAR,
      description        VARCHAR,
      url                VARCHAR,
      active_from        TIMESTAMPTZ,
      active_until       TIMESTAMPTZ,
      affected_route_ids VARCHAR,
      affected_stop_ids  VARCHAR,
      affected_trip_ids  VARCHAR,
      PRIMARY KEY (feed_id, alert_id, ts)
    );

CREATE INDEX IF NOT EXISTS idx_maps_rt_vp_feed_ts
      ON vertex_maps_vehicle_position (feed_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_maps_rt_tu_trip_stop
      ON vertex_maps_trip_update (feed_id, trip_id, stop_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_maps_rt_alert_active
      ON vertex_maps_service_alert (feed_id, active_until DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_recent_vehicle_position AS
      SELECT DISTINCT ON (feed_id, vehicle_id)
        feed_id, vehicle_id, ts, trip_id, route_id, stop_id,
        lat, lng, bearing, speed_mps,
        occupancy_status, current_status, congestion_level, label
      FROM vertex_maps_vehicle_position
      WHERE ts > now() - INTERVAL '5 minutes'
      ORDER BY feed_id, vehicle_id, ts DESC;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_recent_trip_update AS
      SELECT DISTINCT ON (feed_id, trip_id, stop_sequence)
        feed_id, trip_id, stop_sequence, stop_id, route_id, ts,
        schedule_relationship,
        arrival_delay_sec, departure_delay_sec,
        arrival_time, departure_time, uncertainty_sec
      FROM vertex_maps_trip_update
      WHERE ts > now() - INTERVAL '30 minutes'
      ORDER BY feed_id, trip_id, stop_sequence, ts DESC;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_active_alerts AS
      SELECT DISTINCT ON (feed_id, alert_id)
        feed_id, alert_id, ts, cause, effect, severity,
        header_text, description, url,
        active_from, active_until,
        affected_route_ids, affected_stop_ids, affected_trip_ids
      FROM vertex_maps_service_alert
      WHERE (active_until IS NULL OR active_until > now())
        AND ts > now() - INTERVAL '24 hours'
      ORDER BY feed_id, alert_id, ts DESC;
