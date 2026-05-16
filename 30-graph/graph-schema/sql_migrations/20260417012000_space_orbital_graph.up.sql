CREATE TABLE IF NOT EXISTS vertex_orbital_system (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date TIMESTAMP,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      label VARCHAR,
      did VARCHAR,
      name VARCHAR,
      display_name VARCHAR,
      description TEXT,
      category VARCHAR,
      system_id VARCHAR,
      parent_system_id VARCHAR,
      frame VARCHAR,
      primary_body_id VARCHAR,
      scale_kind VARCHAR,
      status VARCHAR,
      metadata_json TEXT,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_orbital_body (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date TIMESTAMP,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      label VARCHAR,
      did VARCHAR,
      name VARCHAR,
      display_name VARCHAR,
      description TEXT,
      category VARCHAR,
      body_id VARCHAR,
      system_id VARCHAR,
      body_kind VARCHAR,
      parent_body_id VARCHAR,
      source_catalog VARCHAR,
      norad_id VARCHAR,
      tle_line1 VARCHAR,
      tle_line2 VARCHAR,
      semi_major_axis_m DOUBLE PRECISION,
      eccentricity DOUBLE PRECISION,
      inclination_deg DOUBLE PRECISION,
      orbital_period_s DOUBLE PRECISION,
      mean_longitude_deg DOUBLE PRECISION,
      render_radius_m DOUBLE PRECISION,
      color_hex VARCHAR,
      status VARCHAR,
      metadata_json TEXT,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_orbital_system_system_id ON vertex_orbital_system (system_id);

CREATE INDEX IF NOT EXISTS idx_vertex_orbital_body_system_id ON vertex_orbital_body (system_id);

CREATE INDEX IF NOT EXISTS idx_vertex_orbital_body_body_kind ON vertex_orbital_body (body_kind);

CREATE INDEX IF NOT EXISTS idx_vertex_orbital_body_norad_id ON vertex_orbital_body (norad_id);

INSERT INTO vertex_orbital_system (
      vertex_id, rkey, label, name, display_name, description, category,
      system_id, parent_system_id, frame, primary_body_id, scale_kind, status, metadata_json, created_at, updated_at
    )
    SELECT * FROM (
      VALUES
      (
        'orbital-system:earth-moon', 'earth-moon', 'OrbitalSystem', 'Earth-Moon System', 'Earth-Moon',
        'Local cislunar orbital frame for LEO, GEO, lunar and ISS placement.', 'space',
        'orbital-system:earth-moon', 'orbital-system:solar-system', 'earth-centered-inertial', 'orbital-body:earth', 'planetary', 'active',
        '{"sceneRole":"cislunar","ephemeris":"analytic"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-system:solar-system', 'solar-system', 'OrbitalSystem', 'Solar System', 'Solar System',
        'Heliocentric orbital frame for planets and solar vortex rendering.', 'space',
        'orbital-system:solar-system', 'orbital-system:milky-way', 'heliocentric-ecliptic', 'orbital-body:sun', 'stellar', 'active',
        '{"sceneRole":"solar","ephemeris":"analytic"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-system:milky-way', 'milky-way', 'OrbitalSystem', 'Milky Way Reference Frame', 'Milky Way',
        'Galactic reference frame for solar-system spiral transit around the galactic center.', 'space',
        'orbital-system:milky-way', NULL, 'galactocentric', 'orbital-body:sun', 'galactic', 'active',
        '{"sceneRole":"galaxy","ephemeris":"analytic"}', NOW()::VARCHAR, NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, category,
      system_id, parent_system_id, frame, primary_body_id, scale_kind, status, metadata_json, created_at, updated_at
    )
    WHERE NOT EXISTS (SELECT 1 FROM vertex_orbital_system WHERE system_id = seed.system_id);

INSERT INTO vertex_orbital_body (
      vertex_id, rkey, label, name, display_name, description, category,
      body_id, system_id, body_kind, parent_body_id, source_catalog, norad_id, tle_line1, tle_line2,
      semi_major_axis_m, eccentricity, inclination_deg, orbital_period_s, mean_longitude_deg,
      render_radius_m, color_hex, status, metadata_json, created_at, updated_at
    )
    SELECT * FROM (
      VALUES
      (
        'orbital-body:earth', 'earth', 'OrbitalBody', 'Earth', 'Earth', 'Reference planet for globe/cosmic rendering.', 'space',
        'orbital-body:earth', 'orbital-system:earth-moon', 'planet', NULL, 'iau', NULL, NULL, NULL,
        149597870700.0, 0.0167, 0.0, 31558149.0, 100.0,
        6378137.0, '#72a7ff', 'active', '{"sceneRole":"home"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:moon', 'moon', 'OrbitalBody', 'Moon', 'Moon', 'Natural satellite of Earth.', 'space',
        'orbital-body:moon', 'orbital-system:earth-moon', 'moon', 'orbital-body:earth', 'iau', NULL, NULL, NULL,
        384400000.0, 0.0549, 5.145, 2360591.0, 218.3,
        1737400.0, '#d7dce4', 'active', '{"sceneRole":"cislunar"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:sun', 'sun', 'OrbitalBody', 'Sun', 'Sun', 'Primary star of the solar system.', 'space',
        'orbital-body:sun', 'orbital-system:solar-system', 'star', NULL, 'iau', NULL, NULL, NULL,
        0.0, 0.0, 0.0, 0.0, 0.0,
        696340000.0, '#ffc24a', 'active', '{"sceneRole":"primary"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:iss', 'iss', 'OrbitalBody', 'International Space Station', 'ISS', 'Low Earth orbit station represented by current mean orbital elements placeholder + NORAD catalog id.', 'space',
        'orbital-body:iss', 'orbital-system:earth-moon', 'station', 'orbital-body:earth', 'norad', '25544',
        '1 25544U 98067A   26106.25000000  .00016717  00000+0  10270-3 0  9995',
        '2 25544  51.6408  30.1234 0005221 244.1234 176.4321 15.50000000400000',
        6771000.0, 0.0005, 51.64, 5570.0, 0.0,
        109.0, '#ffffff', 'active', '{"sceneRole":"leo"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:geo-ring', 'geo-ring', 'OrbitalBody', 'Geostationary Belt', 'GEO Belt', 'Representative body for the geostationary satellite ring.', 'space',
        'orbital-body:geo-ring', 'orbital-system:earth-moon', 'satellite-belt', 'orbital-body:earth', 'analytic', NULL, NULL, NULL,
        42164000.0, 0.0, 0.0, 86164.0, 0.0,
        1000.0, '#7dd3fc', 'active', '{"sceneRole":"geo"}', NOW()::VARCHAR, NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, category,
      body_id, system_id, body_kind, parent_body_id, source_catalog, norad_id, tle_line1, tle_line2,
      semi_major_axis_m, eccentricity, inclination_deg, orbital_period_s, mean_longitude_deg,
      render_radius_m, color_hex, status, metadata_json, created_at, updated_at
    )
    WHERE NOT EXISTS (SELECT 1 FROM vertex_orbital_body WHERE body_id = seed.body_id);
