import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed representative live TLE-driven satellites for cosmic rendering.
 *
 * Source: CelesTrak current GP/TLE data fetched on 2026-04-17 UTC.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO vertex_orbital_body (
      vertex_id, rkey, label, name, display_name, description, category,
      body_id, system_id, body_kind, parent_body_id, source_catalog, norad_id, tle_line1, tle_line2,
      semi_major_axis_m, eccentricity, inclination_deg, orbital_period_s, mean_longitude_deg,
      render_radius_m, color_hex, status, metadata_json, created_at, updated_at
    )
    SELECT * FROM (
      VALUES
      (
        'orbital-body:tdrs-3', 'tdrs-3', 'OrbitalBody', 'TDRS 3', 'TDRS 3',
        'Tracking and Data Relay Satellite in geosynchronous orbit.', 'space',
        'orbital-body:tdrs-3', 'orbital-system:earth-moon', 'satellite', 'orbital-body:earth', 'celestrak', '19548',
        '1 19548U 88091B   26106.71907971 -.00000295  00000+0  00000+0 0  9994',
        '2 19548  12.6498 341.4048 0040960 355.1683  78.1692  1.00278336124777',
        42164000.0, 0.0040960, 12.6498, 86164.0, 78.1692,
        1200.0, '#67e8f9', 'active', '{"sceneRole":"geo","source":"celestrak","fetchedAt":"2026-04-17"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:tdrs-12', 'tdrs-12', 'OrbitalBody', 'TDRS 12', 'TDRS 12',
        'Tracking and Data Relay Satellite in geosynchronous orbit.', 'space',
        'orbital-body:tdrs-12', 'orbital-system:earth-moon', 'satellite', 'orbital-body:earth', 'celestrak', '39504',
        '1 39504U 14004A   26106.54640801 -.00000262  00000+0  00000+0 0  9992',
        '2 39504   3.9179  18.0148 0002387 248.4196  94.0933  1.00272706 43659',
        42164000.0, 0.0002387, 3.9179, 86164.0, 94.0933,
        1200.0, '#7dd3fc', 'active', '{"sceneRole":"geo","source":"celestrak","fetchedAt":"2026-04-17"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:goes-16', 'goes-16', 'OrbitalBody', 'GOES 16', 'GOES 16',
        'NOAA geostationary weather satellite.', 'space',
        'orbital-body:goes-16', 'orbital-system:earth-moon', 'satellite', 'orbital-body:earth', 'celestrak', '41866',
        '1 41866U 16071A   26106.56232919 -.00000084  00000+0  00000+0 0  9993',
        '2 41866   0.1865  84.9634 0001640 244.7306 332.7601  1.00271537 34485',
        42164000.0, 0.0001640, 0.1865, 86164.0, 332.7601,
        1400.0, '#fbbf24', 'active', '{"sceneRole":"geo-weather","source":"celestrak","fetchedAt":"2026-04-17"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:himawari-9', 'himawari-9', 'OrbitalBody', 'HIMAWARI-9', 'HIMAWARI-9',
        'JMA geostationary weather satellite.', 'space',
        'orbital-body:himawari-9', 'orbital-system:earth-moon', 'satellite', 'orbital-body:earth', 'celestrak', '41836',
        '1 41836U 16064A   26106.71503144 -.00000268  00000+0  00000+0 0  9994',
        '2 41836   0.0384 121.9971 0001007 282.8877 198.1606  1.00270979 34596',
        42164000.0, 0.0001007, 0.0384, 86164.0, 198.1606,
        1400.0, '#f59e0b', 'active', '{"sceneRole":"geo-weather","source":"celestrak","fetchedAt":"2026-04-17"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:goes-18', 'goes-18', 'OrbitalBody', 'GOES 18', 'GOES 18',
        'NOAA geostationary weather satellite.', 'space',
        'orbital-body:goes-18', 'orbital-system:earth-moon', 'satellite', 'orbital-body:earth', 'celestrak', '51850',
        '1 51850U 22021A   26106.62447513  .00000000  00000+0  00000+0 0  9991',
        '2 51850   0.0170  75.0012 0000370  19.1020 198.4730  1.00272014  5977',
        42164000.0, 0.0000370, 0.0170, 86164.0, 198.4730,
        1400.0, '#fcd34d', 'active', '{"sceneRole":"geo-weather","source":"celestrak","fetchedAt":"2026-04-17"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:elektro-l-3', 'elektro-l-3', 'OrbitalBody', 'ELEKTRO-L 3', 'ELEKTRO-L 3',
        'Russian geostationary weather satellite.', 'space',
        'orbital-body:elektro-l-3', 'orbital-system:earth-moon', 'satellite', 'orbital-body:earth', 'celestrak', '44903',
        '1 44903U 19095A   26106.66944968 -.00000089  00000+0  00000+0 0  9997',
        '2 44903   0.0989  70.7225 0001135 310.5823 140.4651  1.00271679 23091',
        42164000.0, 0.0001135, 0.0989, 86164.0, 140.4651,
        1400.0, '#c084fc', 'active', '{"sceneRole":"geo-weather","source":"celestrak","fetchedAt":"2026-04-17"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'orbital-body:ses-17', 'ses-17', 'OrbitalBody', 'SES-17', 'SES-17',
        'Commercial geostationary communications satellite.', 'space',
        'orbital-body:ses-17', 'orbital-system:earth-moon', 'satellite', 'orbital-body:earth', 'celestrak', '49332',
        '1 49332U 21095A   26106.40392036 -.00000266  00000+0  00000+0 0  9993',
        '2 49332   0.0060 285.2738 0000524 125.6844 231.9114  1.00271935 17237',
        42164000.0, 0.0000524, 0.0060, 86164.0, 231.9114,
        1200.0, '#34d399', 'active', '{"sceneRole":"geo-comms","source":"celestrak","fetchedAt":"2026-04-17"}', NOW()::VARCHAR, NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, category,
      body_id, system_id, body_kind, parent_body_id, source_catalog, norad_id, tle_line1, tle_line2,
      semi_major_axis_m, eccentricity, inclination_deg, orbital_period_s, mean_longitude_deg,
      render_radius_m, color_hex, status, metadata_json, created_at, updated_at
    )
    WHERE NOT EXISTS (SELECT 1 FROM vertex_orbital_body WHERE body_id = seed.body_id)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_orbital_body
    WHERE body_id IN (
      'orbital-body:tdrs-3',
      'orbital-body:tdrs-12',
      'orbital-body:goes-16',
      'orbital-body:himawari-9',
      'orbital-body:goes-18',
      'orbital-body:elektro-l-3',
      'orbital-body:ses-17'
    )
  `.execute(db);
}
