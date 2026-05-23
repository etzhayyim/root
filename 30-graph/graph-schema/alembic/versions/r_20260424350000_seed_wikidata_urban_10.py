"""Captured from Kysely migration 20260424350000_seed_wikidata_urban_10."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424350000_seed_wikidata_urban_10"
down_revision = 'r_20260424340000_seed_wikipedia_20_more_langs'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-subwayStation:Station',
                 'did:web:maps.etzhayyim.com:registry:wikidata:subwayStation',
                 'Station',
                 20000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:subwayStation',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-seaport:Port',
                 'did:web:maps.etzhayyim.com:registry:wikidata:seaport',
                 'Port',
                 2000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:seaport',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-borough:AdminArea',
                 'did:web:maps.etzhayyim.com:registry:wikidata:borough',
                 'AdminArea',
                 15000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:borough',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-hamletWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:hamletWd',
                 'Spot',
                 200000,
                 0.5,
                 'did:web:maps.etzhayyim.com:registry:wikidata:hamletWd',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-neighborhood:AdminArea',
                 'did:web:maps.etzhayyim.com:registry:wikidata:neighborhood',
                 'AdminArea',
                 100000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:neighborhood',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-publicSquare:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:publicSquare',
                 'Spot',
                 30000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:publicSquare',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-skiResort:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:skiResort',
                 'Spot',
                 5000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:skiResort',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-cityPark:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:cityPark',
                 'Spot',
                 50000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:cityPark',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-shoppingCenter:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:shoppingCenter',
                 'Spot',
                 30000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:shoppingCenter',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-policeStationWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:policeStationWd',
                 'Spot',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:policeStationWd',
                 '2026-05-08T00:19:51.881Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
