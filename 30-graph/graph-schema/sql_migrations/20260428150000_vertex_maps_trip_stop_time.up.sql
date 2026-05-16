CREATE TABLE IF NOT EXISTS vertex_maps_trip (
      feed_id        VARCHAR NOT NULL,
      trip_id        VARCHAR NOT NULL,
      route_id       VARCHAR NOT NULL,
      service_id     VARCHAR,
      shape_id       VARCHAR,
      direction_id   SMALLINT,
      headsign       VARCHAR,
      short_name     VARCHAR,
      block_id       VARCHAR,
      wheelchair_accessible SMALLINT,
      bikes_allowed  SMALLINT,
      agency         VARCHAR,
      prefecture     VARCHAR,
      created_at     TIMESTAMPTZ DEFAULT now(),
      PRIMARY KEY (feed_id, trip_id)
    );

CREATE TABLE IF NOT EXISTS vertex_maps_stop_time (
      feed_id        VARCHAR NOT NULL,
      trip_id        VARCHAR NOT NULL,
      stop_sequence  INT     NOT NULL,
      stop_id        VARCHAR NOT NULL,
      arrival_time   VARCHAR,
      departure_time VARCHAR,
      pickup_type    SMALLINT,
      drop_off_type  SMALLINT,
      stop_headsign  VARCHAR,
      shape_dist_traveled DOUBLE PRECISION,
      timepoint      SMALLINT,
      PRIMARY KEY (feed_id, trip_id, stop_sequence)
    );

CREATE INDEX IF NOT EXISTS idx_maps_stop_time_stop_dep
      ON vertex_maps_stop_time (stop_id, departure_time);

CREATE INDEX IF NOT EXISTS idx_maps_trip_route
      ON vertex_maps_trip (feed_id, route_id);

CREATE INDEX IF NOT EXISTS idx_maps_trip_service
      ON vertex_maps_trip (feed_id, service_id);
