"""Captured from Kysely migration 20260424210000_udf_inaturalist_plus_wp_langs_batch3."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424210000_udf_inaturalist_plus_wp_langs_batch3"
down_revision = 'r_20260424204000_vertex_open_spr'
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/inaturalist:Spot',
                 'did:web:maps.gftd.ai:inaturalist',
                 'Spot',
                 200000000,
                 0.6,
                 24,
                 'did:web:maps.gftd.ai:inaturalist',
                 '2026-05-08T00:18:39.351Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-hi:Spot',
                 'did:web:maps.gftd.ai:wikipedia:hi',
                 'Spot',
                 200000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:hi',
                 '2026-05-08T00:18:39.351Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-bn:Spot',
                 'did:web:maps.gftd.ai:wikipedia:bn',
                 'Spot',
                 150000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:bn',
                 '2026-05-08T00:18:39.351Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-th:Spot',
                 'did:web:maps.gftd.ai:wikipedia:th',
                 'Spot',
                 170000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:th',
                 '2026-05-08T00:18:39.351Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-he:Spot',
                 'did:web:maps.gftd.ai:wikipedia:he',
                 'Spot',
                 350000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:he',
                 '2026-05-08T00:18:39.351Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
