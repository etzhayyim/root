CREATE TABLE IF NOT EXISTS vertex_vector_source (
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
      lineage_role VARCHAR,
      assembly_strategy VARCHAR,
      update_cadence VARCHAR,
      diff_url VARCHAR,
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
    );

CREATE TABLE IF NOT EXISTS vertex_vector_asset (
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
      checksum_url VARCHAR,
      manifest_url VARCHAR,
      update_cadence VARCHAR,
      min_zoom BIGINT,
      max_zoom BIGINT,
      tile_size BIGINT,
      metadata_json TEXT,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_vector_source_source_id ON vertex_vector_source (source_id);

CREATE INDEX IF NOT EXISTS idx_vertex_vector_source_slug ON vertex_vector_source (slug);

CREATE INDEX IF NOT EXISTS idx_vertex_vector_source_default_priority ON vertex_vector_source (is_default, priority);

CREATE INDEX IF NOT EXISTS idx_vertex_vector_asset_source_id ON vertex_vector_asset (source_id);

CREATE INDEX IF NOT EXISTS idx_vertex_vector_asset_role ON vertex_vector_asset (asset_role);

INSERT INTO vertex_vector_source (
      vertex_id, rkey, label, name, display_name, description, status,
      source_id, slug, provider, format, source_kind, lineage_role, assembly_strategy,
      update_cadence, diff_url, metadata_json, bbox_json,
      min_zoom, max_zoom, priority, is_default, created_at, updated_at
    )
    SELECT
      'vector-source:osm-planet',
      'osm-planet',
      'VectorSource',
      'OpenStreetMap Planet',
      'OSM Planet',
      'Canonical worldwide OSM vector lineage rooted in planet.osm.pbf with replication diffs and assembled MVT derivatives.',
      'active',
      'vector-source:osm-planet',
      'osm-planet',
      'openstreetmap',
      'osm-pbf',
      'planetSnapshot',
      'baseMap',
      'graphar-osm-assembly',
      'weekly+minutely',
      'https://planet.openstreetmap.org/replication/minute/',
      '{"license":"ODbL-1.0","attribution":"OpenStreetMap contributors","preferredRawAssetRole":"planetSnapshot","preferredAssemblyAssetRole":"assembledVectorTiles"}',
      '{"west":-180,"south":-90,"east":180,"north":90}',
      0,
      14,
      100,
      TRUE,
      NOW()::VARCHAR,
      NOW()::VARCHAR
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_vector_source WHERE source_id = 'vector-source:osm-planet'
    );

INSERT INTO vertex_vector_asset (
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, checksum_url, manifest_url, update_cadence,
      min_zoom, max_zoom, tile_size, metadata_json, created_at, updated_at
    )
    SELECT
      'vector-asset:osm-planet-pbf',
      'osm-planet-pbf',
      'VectorAsset',
      'planet-latest.osm.pbf',
      'OSM Planet Snapshot',
      'Weekly full-planet PBF snapshot.',
      'active',
      'vector-asset:osm-planet-pbf',
      'vector-source:osm-planet',
      'planetSnapshot',
      'planetFile',
      'openstreetmap',
      'osm-pbf',
      'application/x-protobuf',
      'https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf',
      NULL,
      'https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf.md5',
      'https://planet.openstreetmap.org/pbf/planet-pbf-rss.xml',
      'weekly',
      0,
      14,
      NULL,
      '{"sizeGiB":86,"transport":"http+torrent"}',
      NOW()::VARCHAR,
      NOW()::VARCHAR
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_vector_asset WHERE asset_id = 'vector-asset:osm-planet-pbf'
    );

INSERT INTO vertex_vector_asset (
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, checksum_url, manifest_url, update_cadence,
      min_zoom, max_zoom, tile_size, metadata_json, created_at, updated_at
    )
    SELECT
      'vector-asset:osm-minute-diff',
      'osm-minute-diff',
      'VectorAsset',
      'OSM Minute Replication',
      'OSM Minute Diff Feed',
      'Minutely replication diffs for keeping local assemblies current.',
      'active',
      'vector-asset:osm-minute-diff',
      'vector-source:osm-planet',
      'minuteDiff',
      'replicationFeed',
      'openstreetmap',
      'osc-gz',
      'application/gzip',
      'https://planet.openstreetmap.org/replication/minute/',
      'https://planet.openstreetmap.org/replication/minute/{sequence}.osc.gz',
      NULL,
      'https://planet.openstreetmap.org/replication/minute/state.txt',
      'minutely',
      0,
      14,
      NULL,
      '{"stateFile":"https://planet.openstreetmap.org/replication/minute/state.txt"}',
      NOW()::VARCHAR,
      NOW()::VARCHAR
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_vector_asset WHERE asset_id = 'vector-asset:osm-minute-diff'
    );

INSERT INTO vertex_vector_asset (
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, checksum_url, manifest_url, update_cadence,
      min_zoom, max_zoom, tile_size, metadata_json, created_at, updated_at
    )
    SELECT
      'vector-asset:geofabrik-extract-index',
      'geofabrik-extract-index',
      'VectorAsset',
      'Geofabrik Extract Index',
      'Regional Extract Index',
      'Country and regional extract manifest used for bounded imports.',
      'active',
      'vector-asset:geofabrik-extract-index',
      'vector-source:osm-planet',
      'regionalExtractIndex',
      'manifest',
      'geofabrik',
      'json',
      'application/json',
      'https://download.geofabrik.de/index-v1.json',
      NULL,
      NULL,
      'https://download.geofabrik.de/',
      'daily',
      0,
      14,
      NULL,
      '{"extractProvider":"geofabrik"}',
      NOW()::VARCHAR,
      NOW()::VARCHAR
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_vector_asset WHERE asset_id = 'vector-asset:geofabrik-extract-index'
    );

INSERT INTO vertex_vector_asset (
      vertex_id, rkey, label, name, display_name, description, status,
      asset_id, source_id, asset_role, asset_kind, provider, format, media_type,
      href, href_template, checksum_url, manifest_url, update_cadence,
      min_zoom, max_zoom, tile_size, metadata_json, created_at, updated_at
    )
    SELECT
      'vector-asset:openfreemap-mvt',
      'openfreemap-mvt',
      'VectorAsset',
      'OpenFreeMap Planet MVT',
      'Assembled Vector Tiles',
      'MVT service derived from OSM lineage and consumed by maps runtime today.',
      'active',
      'vector-asset:openfreemap-mvt',
      'vector-source:osm-planet',
      'assembledVectorTiles',
      'tileService',
      'openfreemap',
      'mvt',
      'application/vnd.mapbox-vector-tile',
      NULL,
      'https://tiles.openfreemap.org/planet/stable/{z}/{x}/{y}.pbf',
      NULL,
      'https://openfreemap.org/',
      'weekly',
      0,
      14,
      512,
      '{"schema":"openmaptiles","styleUrl":"https://tiles.openfreemap.org/styles/liberty"}',
      NOW()::VARCHAR,
      NOW()::VARCHAR
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_vector_asset WHERE asset_id = 'vector-asset:openfreemap-mvt'
    );
