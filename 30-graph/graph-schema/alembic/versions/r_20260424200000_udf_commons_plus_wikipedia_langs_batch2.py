"""Captured from Kysely migration 20260424200000_udf_commons_plus_wikipedia_langs_batch2."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424200000_udf_commons_plus_wikipedia_langs_batch2"
down_revision = 'r_20260424194000_vertex_open_hormuz_warrisk'
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
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons'              THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons:%'            THEN 'commons'\n"
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/commons:Spot',
                 'did:web:maps.etzhayyim.com:commons',
                 'Spot',
                 11000000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:commons',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ko:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ko',
                 'Spot',
                 600000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ko',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-id:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:id',
                 'Spot',
                 700000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:id',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-vi:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:vi',
                 'Spot',
                 1300000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:vi',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-tr:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:tr',
                 'Spot',
                 500000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:tr',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-pl:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:pl',
                 'Spot',
                 1500000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:pl',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-nl:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:nl',
                 'Spot',
                 2000000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:nl',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-sv:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:sv',
                 'Spot',
                 2500000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:sv',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-fi:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:fi',
                 'Spot',
                 550000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:fi',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-no:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:no',
                 'Spot',
                 600000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:no',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-da:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:da',
                 'Spot',
                 300000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:da',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-cs:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:cs',
                 'Spot',
                 500000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:cs',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-hu:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:hu',
                 'Spot',
                 500000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:hu',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-el:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:el',
                 'Spot',
                 220000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:el',
                 '2026-05-08T00:18:34.061Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
