"""Captured from Kysely migration 20260424430000_seed_wikidata_maritime_academic_10."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424430000_seed_wikidata_maritime_academic_10"
down_revision = 'r_20260424420000_seed_wikidata_infra_culture_10'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-maritimeStrait:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:maritimeStrait',
                 'Spot',
                 2000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:maritimeStrait',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-archipelago:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:archipelago',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:archipelago',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-peninsulaWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:peninsulaWd',
                 'Spot',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:peninsulaWd',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-capeWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:capeWd',
                 'Spot',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:capeWd',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-lagoon:Lake',
                 'did:web:maps.etzhayyim.com:registry:wikidata:lagoon',
                 'Lake',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:lagoon',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-estuary:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:estuary',
                 'Spot',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:estuary',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-researchInst:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:researchInst',
                 'Spot',
                 30000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:researchInst',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-scientificLab:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:scientificLab',
                 'Spot',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:scientificLab',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-artistStudio:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:artistStudio',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:artistStudio',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-observatory2:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:observatory2',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:observatory2',
                 '2026-05-08T00:20:17.060Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
