"""Captured from Kysely migration 20260424220000_udf_gbif_plus_wikidata_transit."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424220000_udf_gbif_plus_wikidata_transit"
down_revision = 'r_20260424214000_vertex_open_malacca_emission'
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
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons'              THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons:%'            THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist'          THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist:%'        THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif'                 THEN 'gbif'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif:%'               THEN 'gbif'\n"
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/gbif:Spot',
                 'did:web:maps.gftd.ai:gbif',
                 'Spot',
                 2000000000,
                 0.6,
                 24,
                 'did:web:maps.gftd.ai:gbif',
                 '2026-05-08T00:18:44.964Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-metroStation:Station',
                 'did:web:maps.gftd.ai:registry:wikidata:metroStation',
                 'Station',
                 10000,
                 0.6,
                 720,
                 'did:web:maps.gftd.ai:registry:wikidata:metroStation',
                 '2026-05-08T00:18:44.964Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-busStation:Station',
                 'did:web:maps.gftd.ai:registry:wikidata:busStation',
                 'Station',
                 5000,
                 0.3,
                 720,
                 'did:web:maps.gftd.ai:registry:wikidata:busStation',
                 '2026-05-08T00:18:44.964Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-shoppingMall:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:shoppingMall',
                 'Spot',
                 50000,
                 0.3,
                 720,
                 'did:web:maps.gftd.ai:registry:wikidata:shoppingMall',
                 '2026-05-08T00:18:44.964Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-skyscraper:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:skyscraper',
                 'Spot',
                 20000,
                 0.3,
                 720,
                 'did:web:maps.gftd.ai:registry:wikidata:skyscraper',
                 '2026-05-08T00:18:44.964Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-lighthouse:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:lighthouse',
                 'Spot',
                 20000,
                 0.3,
                 720,
                 'did:web:maps.gftd.ai:registry:wikidata:lighthouse',
                 '2026-05-08T00:18:44.964Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-hotSpring:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:hotSpring',
                 'Spot',
                 10000,
                 0.3,
                 720,
                 'did:web:maps.gftd.ai:registry:wikidata:hotSpring',
                 '2026-05-08T00:18:44.964Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
