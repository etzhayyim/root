import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Celestial catalog graph for solar, galactic and deep-space objects.
 *
 * This sits above orbital systems/bodies:
 * - celestial catalogs define authority + frame
 * - celestial objects define the hierarchy from Earth to observable universe
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_celestial_catalog (
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
      catalog_id VARCHAR,
      authority VARCHAR,
      version VARCHAR,
      frame VARCHAR,
      coverage_kind VARCHAR,
      metadata_json TEXT,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_celestial_object (
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
      object_id VARCHAR,
      catalog_id VARCHAR,
      object_kind VARCHAR,
      parent_object_id VARCHAR,
      linked_system_id VARCHAR,
      linked_body_id VARCHAR,
      reference_frame VARCHAR,
      ra_deg DOUBLE PRECISION,
      dec_deg DOUBLE PRECISION,
      distance_au DOUBLE PRECISION,
      distance_ly DOUBLE PRECISION,
      radius_m DOUBLE PRECISION,
      mass_kg DOUBLE PRECISION,
      spectral_class VARCHAR,
      render_priority BIGINT,
      source_ref VARCHAR,
      status VARCHAR,
      metadata_json TEXT,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_celestial_catalog_catalog_id ON vertex_celestial_catalog (catalog_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_celestial_object_object_id ON vertex_celestial_object (object_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_celestial_object_catalog_id ON vertex_celestial_object (catalog_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_celestial_object_parent_object_id ON vertex_celestial_object (parent_object_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_celestial_object_object_kind ON vertex_celestial_object (object_kind)`.execute(db);

  await sql`
    INSERT INTO vertex_celestial_catalog (
      vertex_id, rkey, label, name, display_name, description, category,
      catalog_id, authority, version, frame, coverage_kind, metadata_json, created_at, updated_at
    )
    SELECT * FROM (
      VALUES
      (
        'celestial-catalog:iau-reference', 'iau-reference', 'CelestialCatalog', 'IAU Reference Catalog', 'IAU Reference',
        'Canonical reference catalog for solar-system and galactic anchor bodies.', 'space',
        'celestial-catalog:iau-reference', 'iau', '2026.04', 'icrs', 'solar-galactic',
        '{"sceneRole":"canonical"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-catalog:deep-space-reference', 'deep-space-reference', 'CelestialCatalog', 'Deep Space Reference Catalog', 'Deep Space',
        'Reference catalog for galaxies, local group and observable-universe scale anchors.', 'space',
        'celestial-catalog:deep-space-reference', 'multi-source', '2026.04', 'icrs', 'extragalactic',
        '{"sceneRole":"deep-space"}', NOW()::VARCHAR, NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, category,
      catalog_id, authority, version, frame, coverage_kind, metadata_json, created_at, updated_at
    )
    WHERE NOT EXISTS (SELECT 1 FROM vertex_celestial_catalog WHERE catalog_id = seed.catalog_id)
  `.execute(db);

  await sql`
    INSERT INTO vertex_celestial_object (
      vertex_id, rkey, label, name, display_name, description, category,
      object_id, catalog_id, object_kind, parent_object_id, linked_system_id, linked_body_id, reference_frame,
      ra_deg, dec_deg, distance_au, distance_ly, radius_m, mass_kg, spectral_class, render_priority, source_ref, status, metadata_json, created_at, updated_at
    )
    SELECT * FROM (
      VALUES
      (
        'celestial-object:observable-universe', 'observable-universe', 'CelestialObject', 'Observable Universe', 'Observable Universe',
        'Top-level cosmic shell for the furthest zoomed-out maps view.', 'space',
        'celestial-object:observable-universe', 'celestial-catalog:deep-space-reference', 'universe', NULL, NULL, NULL, 'icrs',
        NULL, NULL, NULL, 46500000000.0, 4.4e26, NULL, NULL, 1, 'analytic', 'active', '{"sceneRole":"universe"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:local-group', 'local-group', 'CelestialObject', 'Local Group', 'Local Group',
        'Galaxy group containing the Milky Way and Andromeda.', 'space',
        'celestial-object:local-group', 'celestial-catalog:deep-space-reference', 'galaxy-group', 'celestial-object:observable-universe', NULL, NULL, 'icrs',
        NULL, NULL, NULL, 5000000.0, NULL, NULL, NULL, 2, 'analytic', 'active', '{"sceneRole":"group"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:milky-way', 'milky-way', 'CelestialObject', 'Milky Way', 'Milky Way',
        'Host galaxy for the solar system and galactic spiral rendering.', 'space',
        'celestial-object:milky-way', 'celestial-catalog:iau-reference', 'galaxy', 'celestial-object:local-group', 'orbital-system:milky-way', NULL, 'galactocentric',
        266.41683, -29.00781, NULL, 0.0, 5.7e20, NULL, NULL, 3, 'iau', 'active', '{"sceneRole":"galaxy"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:sagittarius-a-star', 'sagittarius-a-star', 'CelestialObject', 'Sagittarius A*', 'Sagittarius A*',
        'Supermassive black hole at the center of the Milky Way.', 'space',
        'celestial-object:sagittarius-a-star', 'celestial-catalog:iau-reference', 'black-hole', 'celestial-object:milky-way', NULL, NULL, 'galactocentric',
        266.41683, -29.00781, NULL, 25800.0, 1.27e10, NULL, NULL, 4, 'iau', 'active', '{"sceneRole":"galactic-core","estimatedMassKg":"8.54e36"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:solar-system', 'solar-system', 'CelestialObject', 'Solar System', 'Solar System',
        'Heliocentric planetary system containing Earth, Moon and ISS.', 'space',
        'celestial-object:solar-system', 'celestial-catalog:iau-reference', 'planetary-system', 'celestial-object:milky-way', 'orbital-system:solar-system', NULL, 'heliocentric-ecliptic',
        NULL, NULL, 0.0, 26000.0, NULL, NULL, NULL, 5, 'iau', 'active', '{"sceneRole":"solar"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:sun', 'sun', 'CelestialObject', 'Sun', 'Sun',
        'Primary star of the solar system.', 'space',
        'celestial-object:sun', 'celestial-catalog:iau-reference', 'star', 'celestial-object:solar-system', NULL, 'orbital-body:sun', 'heliocentric-ecliptic',
        NULL, NULL, 0.0, 26000.0, 696340000.0, NULL, 'G2V', 6, 'iau', 'active', '{"sceneRole":"primary","estimatedMassKg":"1.9885e30"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:earth', 'earth', 'CelestialObject', 'Earth', 'Earth',
        'Home world rendered by the globe map.', 'space',
        'celestial-object:earth', 'celestial-catalog:iau-reference', 'planet', 'celestial-object:solar-system', 'orbital-system:earth-moon', 'orbital-body:earth', 'earth-centered-inertial',
        NULL, NULL, 1.0, 26000.0, 6378137.0, NULL, NULL, 7, 'iau', 'active', '{"sceneRole":"home","estimatedMassKg":"5.9722e24"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:moon', 'moon', 'CelestialObject', 'Moon', 'Moon',
        'Natural satellite of Earth.', 'space',
        'celestial-object:moon', 'celestial-catalog:iau-reference', 'moon', 'celestial-object:earth', 'orbital-system:earth-moon', 'orbital-body:moon', 'earth-centered-inertial',
        NULL, NULL, 0.00257, 26000.0, 1737400.0, NULL, NULL, 8, 'iau', 'active', '{"sceneRole":"cislunar","estimatedMassKg":"7.342e22"}', NOW()::VARCHAR, NOW()::VARCHAR
      ),
      (
        'celestial-object:andromeda', 'andromeda', 'CelestialObject', 'Andromeda Galaxy', 'Andromeda',
        'Nearest major galaxy to the Milky Way, used as a deep-space anchor.', 'space',
        'celestial-object:andromeda', 'celestial-catalog:deep-space-reference', 'galaxy', 'celestial-object:local-group', NULL, NULL, 'icrs',
        10.6847083, 41.26875, NULL, 2537000.0, 1.1e21, NULL, NULL, 9, 'simbad', 'active', '{"sceneRole":"deep-space-anchor"}', NOW()::VARCHAR, NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, category,
      object_id, catalog_id, object_kind, parent_object_id, linked_system_id, linked_body_id, reference_frame,
      ra_deg, dec_deg, distance_au, distance_ly, radius_m, mass_kg, spectral_class, render_priority, source_ref, status, metadata_json, created_at, updated_at
    )
    WHERE NOT EXISTS (SELECT 1 FROM vertex_celestial_object WHERE object_id = seed.object_id)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_celestial_object_object_kind`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_celestial_object_parent_object_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_celestial_object_catalog_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_celestial_object_object_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_celestial_catalog_catalog_id`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_celestial_object`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_celestial_catalog`.execute(db);
}
