"""Captured from Kysely migration 20260424370000_seed_wikidata_historical_10."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424370000_seed_wikidata_historical_10"
down_revision = 'r_20260424360000_udf_osm_notes_plus_seed'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-battlefield:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:battlefield',
                 'Spot',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:battlefield',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-conventionCtr:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:conventionCtr',
                 'Spot',
                 5000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:conventionCtr',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-musicSchool:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:musicSchool',
                 'Spot',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:musicSchool',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-airForceBase:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:airForceBase',
                 'Spot',
                 2000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:airForceBase',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-busStationWd:Station',
                 'did:web:maps.etzhayyim.com:registry:wikidata:busStationWd',
                 'Station',
                 50000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:busStationWd',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-microbrewery:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:microbrewery',
                 'Spot',
                 30000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:microbrewery',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-cityGate:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:cityGate',
                 'Spot',
                 5000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:cityGate',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-bunker:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:bunker',
                 'Spot',
                 30000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:bunker',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-arsenal:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:arsenal',
                 'Spot',
                 3000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:arsenal',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-farmersMarket:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:farmersMarket',
                 'Spot',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:farmersMarket',
                 '2026-05-08T00:19:59.716Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
