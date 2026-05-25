"""Captured from Kysely migration 20260424190000_udf_dispatch_seismic_variants_plus_wikipedia_langs."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424190000_udf_dispatch_seismic_variants_plus_wikipedia_la"
down_revision = 'r_20260424184100_seed_jpn_edinet_bpmn_actors'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-de:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:de',
                 'Spot',
                 1500000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:de',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-fr:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:fr',
                 'Spot',
                 1200000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:fr',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-it:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:it',
                 'Spot',
                 700000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:it',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-zh:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:zh',
                 'Spot',
                 800000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:zh',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ru:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ru',
                 'Spot',
                 900000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ru',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ar:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ar',
                 'Spot',
                 300000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ar',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-pt:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:pt',
                 'Spot',
                 600000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:pt',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/seismic-week:SpatialEvent',
                 'did:web:maps.etzhayyim.com:seismic:week',
                 'SpatialEvent',
                 20000,
                 0.3,
                 1,
                 'did:web:maps.etzhayyim.com:seismic:week',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/seismic-month:SpatialEvent',
                 'did:web:maps.etzhayyim.com:seismic:month',
                 'SpatialEvent',
                 100000,
                 0.3,
                 24,
                 'did:web:maps.etzhayyim.com:seismic:month',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/seismic-sig_month:SpatialEvent',
                 'did:web:maps.etzhayyim.com:seismic:sig_month',
                 'SpatialEvent',
                 100,
                 0.6,
                 24,
                 'did:web:maps.etzhayyim.com:seismic:sig_month',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/seismic-m6:SpatialEvent',
                 'did:web:maps.etzhayyim.com:seismic:m6',
                 'SpatialEvent',
                 500,
                 0.6,
                 24,
                 'did:web:maps.etzhayyim.com:seismic:m6',
                 '2026-05-08T00:18:28.240Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
