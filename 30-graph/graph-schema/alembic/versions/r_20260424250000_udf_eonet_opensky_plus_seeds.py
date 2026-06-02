"""Captured from Kysely migration 20260424250000_udf_eonet_opensky_plus_seeds."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424250000_udf_eonet_opensky_plus_seeds"
down_revision = 'r_20260424244000_vertex_open_carrier_esg'
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
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:gleif'       THEN 'gleif'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata'    THEN "
         "'wikidata'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata:%'  THEN "
         "'wikidata'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:%'           THEN "
         "'registry_other'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia'            THEN "
         "'wikipedia'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia:%'          THEN "
         "'wikipedia'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikivoyage'           THEN "
         "'wikivoyage'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikivoyage:%'         THEN "
         "'wikivoyage'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons'              THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons:%'            THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:inaturalist'          THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:inaturalist:%'        THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gbif'                 THEN 'gbif'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gbif:%'               THEN 'gbif'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:eonet'                THEN 'eonet'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:eonet:%'              THEN 'eonet'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:opensky'              THEN 'opensky'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:opensky:%'            THEN 'opensky'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite'            THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite:%'          THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic'              THEN 'seismic'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic:%'            THEN 'seismic'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:street_view'          THEN "
         "'mapillary'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:infrastructure'       THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:geocode'              THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:weather'              THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gtfs'                 THEN 'gtfs'\n"
         "        WHEN source_did LIKE 'did:web:site.etzhayyim.com'                      THEN "
         "'web_crawl'\n"
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
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/eonet:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet',
                 'SpatialEvent',
                 500,
                 0.6,
                 6,
                 'did:web:maps.etzhayyim.com:eonet',
                 '2026-05-08T00:19:02.817Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/eonet-wildfires:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:wildfires',
                 'SpatialEvent',
                 300,
                 0.6,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:wildfires',
                 '2026-05-08T00:19:02.817Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/eonet-severeStorms:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:severeStorms',
                 'SpatialEvent',
                 50,
                 0.6,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:severeStorms',
                 '2026-05-08T00:19:02.817Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/eonet-volcanoes:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:volcanoes',
                 'SpatialEvent',
                 50,
                 0.6,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:volcanoes',
                 '2026-05-08T00:19:02.817Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/opensky:Aircraft',
                 'did:web:maps.etzhayyim.com:opensky',
                 'Aircraft',
                 15000,
                 0.6,
                 1,
                 'did:web:maps.etzhayyim.com:opensky',
                 '2026-05-08T00:19:02.817Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
