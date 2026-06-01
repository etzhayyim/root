"""Captured from Kysely migration 20260424420000_seed_wikidata_infra_culture_10."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424420000_seed_wikidata_infra_culture_10"
down_revision = 'r_20260424410000_stricter_productivity_factor'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-waterTreatment:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:waterTreatment',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:waterTreatment',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-sewageTreatment:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:sewageTreatment',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:sewageTreatment',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-navalBase:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:navalBase',
                 500,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:navalBase',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-operaHouse:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:operaHouse',
                 1500,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:operaHouse',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-concertHall:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:concertHall',
                 5000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:concertHall',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-restAreaWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:restAreaWd',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:restAreaWd',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-tollPlaza:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:tollPlaza',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:tollPlaza',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-lighthouseWd2:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:lighthouseWd2',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:lighthouseWd2',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-miningSite:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:miningSite',
                 30000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:miningSite',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-museumShip:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:museumShip',
                 300,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:museumShip',
                 '2026-05-08T00:20:13.075Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
