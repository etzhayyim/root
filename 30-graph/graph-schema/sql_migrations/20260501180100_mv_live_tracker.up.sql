CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aircraft_currently_airborne AS
    SELECT
      icao24,
      callsign,
      lat,
      lon,
      baro_altitude_m,
      velocity_ms,
      heading_deg,
      vertical_rate_ms,
      origin_country,
      source,
      ts_ms
    FROM vertex_aircraft_state
    WHERE on_ground = false
      AND to_timestamp(ts_ms / 1000.0) > now() - INTERVAL '90 seconds';

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aircraft_country_count AS
    SELECT
      origin_country,
      COUNT(*) AS airborne_count
    FROM vertex_aircraft_state
    WHERE on_ground = false
      AND to_timestamp(ts_ms / 1000.0) > now() - INTERVAL '5 minutes'
    GROUP BY origin_country;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_satellite_visible_now AS
    SELECT
      norad_id,
      observer_h3,
      observer_lat,
      observer_lon,
      aos_ms,
      los_ms,
      max_elevation_deg,
      peak_azimuth_deg,
      visible_at_night,
      magnitude
    FROM vertex_satellite_pass
    WHERE to_timestamp(aos_ms / 1000.0) <= now() + INTERVAL '0 seconds'
      AND to_timestamp(los_ms / 1000.0) >= now() - INTERVAL '0 seconds';
