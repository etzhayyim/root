import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Maps terrain source graph spine.
 *
 * - Add typed terrain source and raster asset vertices for COG/GeoTIFF/STAC-backed terrain
 * - Seed a default Copernicus DEM source with a Terrarium fallback asset
 * - Expose a flat read view for runtime assembly in the maps worker
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_terrain_source (
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
      status VARCHAR,
      source_id VARCHAR,
      slug VARCHAR,
      provider VARCHAR,
      format VARCHAR,
      source_kind VARCHAR,
      terrain_role VARCHAR,
      assembly_strategy VARCHAR,
      stac_api_url VARCHAR,
      stac_collection_id VARCHAR,
      tilejson_url VARCHAR,
      metadata_json TEXT,
      bbox_json TEXT,
      min_zoom BIGINT,
      max_zoom BIGINT,
      priority BIGINT,
      is_default BOOLEAN,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_raster_asset (
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
      status VARCHAR,
      asset_id VARCHAR,
      source_id VARCHAR,
      asset_role VARCHAR,
      asset_kind VARCHAR,
      provider VARCHAR,
      format VARCHAR,
      media_type VARCHAR,
      href VARCHAR,
      href_template VARCHAR,
      band VARCHAR,
      encoding VARCHAR,
      nodata DOUBLE PRECISION,
      resolution_m DOUBLE PRECISION,
      min_zoom BIGINT,
      max_zoom BIGINT,
      tile_size BIGINT,
      crs VARCHAR,
      tile_matrix_set VARCHAR,
      metadata_json TEXT,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_terrain_source_source_id ON vertex_terrain_source (source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_terrain_source_slug ON vertex_terrain_source (slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_terrain_source_default_priority ON vertex_terrain_source (is_default, priority)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_raster_asset_source_id ON vertex_raster_asset (source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_raster_asset_role ON vertex_raster_asset (asset_role)`.execute(db);

  await sql`
    INSERT INTO vertex_terrain_source (
      vertex_id, rkey, label, name, display_name, description, status,
      source_id, slug, provider, format, source_kind, terrain_role, assembly_strategy,
      stac_api_url, stac_collection_id, metadata_json, bbox_json,
      min_zoom, max_zoom, priority, is_default, created_at, updated_at
    )
    SELECT * FROM (
      VALUES (
        'terrain-source:cop-dem-glo-30',
        'cop-dem-glo-30',
        'TerrainSource',
        'Copernicus DEM GLO-30',
        'Copernicus DEM',
        'Global terrain source assembled from Copernicus DEM STAC/COG assets with runtime tile fallbacks.',
        'active',
        'terrain-source:cop-dem-glo-30',
        'cop-dem-glo-30',
        'copernicus',
        'cog',
        'stacCollection',
        'elevation',
        'graph-stac-cog',
        'https://earth-search.aws.element84.com/v1',
        'cop-dem-glo-30',
        '{"catalog":"earth-search","dataset":"cop-dem-glo-30","preferredTransport":"cog","fallbackTransport":"terrarium-png"}',
        '{"west":-180,"south":-90,"east":180,"north":90}',
        CAST(0 AS BIGINT),
        CAST(14 AS BIGINT),
        CAST(100 AS BIGINT),
        TRUE,
        NOW()::VARCHAR,
        NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, status,
      source_id, slug, provider, format, source_kind, terrain_role, assembly_strategy,
      stac_api_url, stac_collection_id, metadata_json, bbox_json,
      min_zoom, max_zoom, priority, is_default, created_at, updated_at
    )
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_terrain_source WHERE source_id = 'terrain-source:cop-dem-glo-30'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_raster_asset (
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, band, encoding, nodata, resolution_m,
      min_zoom, max_zoom, tile_size, crs, tile_matrix_set, metadata_json, created_at, updated_at
    )
    SELECT * FROM (
      VALUES (
        'raster-asset:cop-dem-glo-30-stac',
        'cop-dem-glo-30-stac',
        'RasterAsset',
        'Copernicus DEM STAC collection',
        'Copernicus DEM STAC',
        'STAC collection endpoint used to discover COG-backed DEM items.',
        'active',
        'raster-asset:cop-dem-glo-30-stac',
        'terrain-source:cop-dem-glo-30',
        'catalog',
        'stacCollection',
        'earth-search',
        'stac-json',
        'application/json',
        'https://earth-search.aws.element84.com/v1/collections/cop-dem-glo-30',
        NULL,
        'dem',
        'json',
        CAST(NULL AS DOUBLE PRECISION),
        CAST(30 AS DOUBLE PRECISION),
        CAST(0 AS BIGINT),
        CAST(14 AS BIGINT),
        CAST(NULL AS BIGINT),
        'EPSG:4326',
        'WorldCRS84Quad',
        '{"collectionId":"cop-dem-glo-30","searchUrl":"https://earth-search.aws.element84.com/v1/search"}',
        NOW()::VARCHAR,
        NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, band, encoding, nodata, resolution_m,
      min_zoom, max_zoom, tile_size, crs, tile_matrix_set, metadata_json, created_at, updated_at
    )
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_raster_asset WHERE asset_id = 'raster-asset:cop-dem-glo-30-stac'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_raster_asset (
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, band, encoding, nodata, resolution_m,
      min_zoom, max_zoom, tile_size, crs, tile_matrix_set, metadata_json, created_at, updated_at
    )
    SELECT * FROM (
      VALUES (
        'raster-asset:cop-dem-glo-30-terrarium',
        'cop-dem-glo-30-terrarium',
        'RasterAsset',
        'Copernicus DEM Terrarium fallback',
        'Copernicus DEM Fallback',
        'Runtime tile fallback while COG-native terrain assembly is phased in.',
        'active',
        'raster-asset:cop-dem-glo-30-terrarium',
        'terrain-source:cop-dem-glo-30',
        'demTileFallback',
        'tileTemplate',
        'aws-terrain-tiles',
        'terrarium-png',
        'image/png',
        NULL,
        'https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png',
        'dem',
        'terrarium',
        CAST(-32768 AS DOUBLE PRECISION),
        CAST(30 AS DOUBLE PRECISION),
        CAST(0 AS BIGINT),
        CAST(14 AS BIGINT),
        CAST(256 AS BIGINT),
        'EPSG:3857',
        'WebMercatorQuad',
        '{"transport":"png","decoder":"terrarium-rgb"}',
        NOW()::VARCHAR,
        NOW()::VARCHAR
      )
    ) AS seed(
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, band, encoding, nodata, resolution_m,
      min_zoom, max_zoom, tile_size, crs, tile_matrix_set, metadata_json, created_at, updated_at
    )
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_raster_asset WHERE asset_id = 'raster-asset:cop-dem-glo-30-terrarium'
    )
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_terrain_source_asset_flat AS
    SELECT
      s.vertex_id AS terrain_vertex_id,
      s.source_id,
      s.slug,
      s.name AS source_name,
      s.display_name AS source_display_name,
      s.description AS source_description,
      s.status AS source_status,
      s.provider AS source_provider,
      s.format AS source_format,
      s.source_kind,
      s.terrain_role,
      s.assembly_strategy,
      s.stac_api_url,
      s.stac_collection_id,
      s.tilejson_url,
      s.metadata_json AS source_metadata_json,
      s.bbox_json,
      s.min_zoom AS source_min_zoom,
      s.max_zoom AS source_max_zoom,
      s.priority,
      s.is_default,
      a.vertex_id AS asset_vertex_id,
      a.asset_id,
      a.asset_role,
      a.asset_kind,
      a.provider AS asset_provider,
      a.format AS asset_format,
      a.media_type,
      a.href,
      a.href_template,
      a.band,
      a.encoding,
      a.nodata,
      a.resolution_m,
      a.min_zoom AS asset_min_zoom,
      a.max_zoom AS asset_max_zoom,
      a.tile_size,
      a.crs,
      a.tile_matrix_set,
      a.metadata_json AS asset_metadata_json,
      a.status AS asset_status
    FROM vertex_terrain_source s
    LEFT JOIN vertex_raster_asset a
      ON s.source_id = a.source_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_terrain_source_asset_flat`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_raster_asset_role`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_raster_asset_source_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_terrain_source_default_priority`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_terrain_source_slug`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_terrain_source_source_id`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_raster_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_terrain_source`.execute(db);
}
