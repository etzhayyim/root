"""Captured from Kysely migration 20260424160000_udf_stac_multi_collection_plus_seed."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424160000_udf_stac_multi_collection_plus_seed"
down_revision = 'r_20260424154100_seed_open_saas_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION maps_source_dispatch_kind(\n'
         '      source_did varchar,\n'
         '      label      varchar\n'
         '    ) RETURNS varchar\n'
         '    LANGUAGE sql\n'
         '    AS $$\n'
         '      SELECT CASE\n'
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:gleif'    THEN 'gleif'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata' THEN 'wikidata'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:%'        THEN "
         "'registry_other'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite'         THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite:%'       THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic'           THEN 'seismic'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:street_view'       THEN 'mapillary'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:infrastructure'    THEN 'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:geocode'           THEN 'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:weather'           THEN 'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gtfs'              THEN 'gtfs'\n"
         "        WHEN source_did LIKE 'did:web:site.etzhayyim.com'                   THEN 'web_crawl'\n"
         "        ELSE 'unsupported'\n"
         '      END\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/satellite-sentinel2:SatelliteScene',
                 'did:web:maps.etzhayyim.com:satellite:sentinel2',
                 'SatelliteScene',
                 5000000,
                 0.6,
                 720,
                 'did:web:maps.etzhayyim.com:satellite:sentinel2',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/satellite-landsat:SatelliteScene',
                 'did:web:maps.etzhayyim.com:satellite:landsat',
                 'SatelliteScene',
                 2000000,
                 0.6,
                 720,
                 'did:web:maps.etzhayyim.com:satellite:landsat',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/satellite-sentinel1:SatelliteScene',
                 'did:web:maps.etzhayyim.com:satellite:sentinel1',
                 'SatelliteScene',
                 1500000,
                 0.6,
                 720,
                 'did:web:maps.etzhayyim.com:satellite:sentinel1',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/satellite-naip:SatelliteScene',
                 'did:web:maps.etzhayyim.com:satellite:naip',
                 'SatelliteScene',
                 500000,
                 0.3,
                 720,
                 'did:web:maps.etzhayyim.com:satellite:naip',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Hospital',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Hospital',
                 150000,
                 0.3,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:School',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'School',
                 1000000,
                 0.3,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Museum',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Museum',
                 50000,
                 0.3,
                 720,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Cafe',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Cafe',
                 3000000,
                 0.1,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Restaurant',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Restaurant',
                 5000000,
                 0.1,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:15:47.099Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
