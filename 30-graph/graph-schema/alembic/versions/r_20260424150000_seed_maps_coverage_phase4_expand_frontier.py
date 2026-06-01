"""Captured from Kysely migration 20260424150000_seed_maps_coverage_phase4_expand_frontier."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424150000_seed_maps_coverage_phase4_expand_frontier"
down_revision = 'r_20260424144100_seed_open_swift_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Waterway',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Waterway',
                 5000000,
                 0.3,
                 720,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:14:39.651Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:River',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'River',
                 500000,
                 0.3,
                 720,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:14:39.651Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Mountain',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Mountain',
                 1000000,
                 0.3,
                 720,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:14:39.651Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:BusStop',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'BusStop',
                 5000000,
                 0.3,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:14:39.651Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Parking',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Parking',
                 50000000,
                 0.3,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:14:39.651Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Sensor',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Sensor',
                 100000,
                 0.1,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:14:39.651Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
