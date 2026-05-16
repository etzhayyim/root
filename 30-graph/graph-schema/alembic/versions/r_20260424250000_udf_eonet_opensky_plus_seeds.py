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
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:gleif'       THEN 'gleif'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:wikidata'    THEN "
         "'wikidata'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:wikidata:%'  THEN "
         "'wikidata'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:%'           THEN "
         "'registry_other'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikipedia'            THEN "
         "'wikipedia'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikipedia:%'          THEN "
         "'wikipedia'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikivoyage'           THEN "
         "'wikivoyage'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikivoyage:%'         THEN "
         "'wikivoyage'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons'              THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons:%'            THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist'          THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist:%'        THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif'                 THEN 'gbif'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif:%'               THEN 'gbif'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:eonet'                THEN 'eonet'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:eonet:%'              THEN 'eonet'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:opensky'              THEN 'opensky'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:opensky:%'            THEN 'opensky'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:satellite'            THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:satellite:%'          THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:seismic'              THEN 'seismic'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:seismic:%'            THEN 'seismic'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:street_view'          THEN "
         "'mapillary'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:infrastructure'       THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:geocode'              THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:weather'              THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gtfs'                 THEN 'gtfs'\n"
         "        WHEN source_did LIKE 'did:web:site.gftd.ai'                      THEN "
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/eonet:SpatialEvent',
                 'did:web:maps.gftd.ai:eonet',
                 'SpatialEvent',
                 500,
                 0.6,
                 6,
                 'did:web:maps.gftd.ai:eonet',
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/eonet-wildfires:SpatialEvent',
                 'did:web:maps.gftd.ai:eonet:wildfires',
                 'SpatialEvent',
                 300,
                 0.6,
                 6,
                 'did:web:maps.gftd.ai:eonet:wildfires',
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/eonet-severeStorms:SpatialEvent',
                 'did:web:maps.gftd.ai:eonet:severeStorms',
                 'SpatialEvent',
                 50,
                 0.6,
                 6,
                 'did:web:maps.gftd.ai:eonet:severeStorms',
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/eonet-volcanoes:SpatialEvent',
                 'did:web:maps.gftd.ai:eonet:volcanoes',
                 'SpatialEvent',
                 50,
                 0.6,
                 6,
                 'did:web:maps.gftd.ai:eonet:volcanoes',
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/opensky:Aircraft',
                 'did:web:maps.gftd.ai:opensky',
                 'Aircraft',
                 15000,
                 0.6,
                 1,
                 'did:web:maps.gftd.ai:opensky',
                 '2026-05-08T00:19:02.817Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
