"""Captured from Kysely migration 20260424330000_seed_wikidata_civic_10."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424330000_seed_wikidata_civic_10"
down_revision = 'r_20260424320000_seed_overpass_civic_religion_15'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-parliamentBldg:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:parliamentBldg',
                 2000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:parliamentBldg',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-primarySchool:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:primarySchool',
                 500000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:primarySchool',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-middleSchool:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:middleSchool',
                 200000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:middleSchool',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-highSchoolWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:highSchoolWd',
                 300000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:highSchoolWd',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-boardingSchool:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:boardingSchool',
                 8000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:boardingSchool',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-prisonWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:prisonWd',
                 25000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:prisonWd',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-gurdwara:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:gurdwara',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:gurdwara',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-aquariumWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:aquariumWd',
                 1000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:aquariumWd',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-botanicalGarden:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:botanicalGarden',
                 3000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:botanicalGarden',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-basilica:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:basilica',
                 3000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:basilica',
                 '2026-05-08T00:19:44.506Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
