"""Captured from Kysely migration 20260424180000_udf_maps_dispatch_add_wikipedia."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424180000_udf_maps_dispatch_add_wikipedia"
down_revision = 'r_20260424174100_seed_open_naics_bpmn_actors'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia',
                 'Spot',
                 7000000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia',
                 '2026-05-08T00:17:40.439Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ja:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ja',
                 'Spot',
                 1500000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ja',
                 '2026-05-08T00:17:40.439Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-es:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:es',
                 'Spot',
                 1800000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:es',
                 '2026-05-08T00:17:40.439Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
