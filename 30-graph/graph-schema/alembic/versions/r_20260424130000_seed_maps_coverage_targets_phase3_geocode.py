"""Captured from Kysely migration 20260424130000_seed_maps_coverage_targets_phase3_geocode."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424130000_seed_maps_coverage_targets_phase3_geocode"
down_revision = 'r_20260424121000_seed_open_water_bpmn_actors'
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/geocode:Airport',
                 'did:web:maps.gftd.ai:geocode',
                 'Airport',
                 3000,
                 1,
                 168,
                 'did:web:maps.gftd.ai:geocode',
                 '2026-05-08T00:13:05.176Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/geocode:Port',
                 'did:web:maps.gftd.ai:geocode',
                 'Port',
                 5000,
                 1,
                 168,
                 'did:web:maps.gftd.ai:geocode',
                 '2026-05-08T00:13:05.176Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/geocode:Station',
                 'did:web:maps.gftd.ai:geocode',
                 'Station',
                 10000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:geocode',
                 '2026-05-08T00:13:05.176Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/weather:WeatherPoint',
                 'did:web:maps.gftd.ai:weather',
                 'WeatherPoint',
                 50000,
                 0.3,
                 1,
                 'did:web:maps.gftd.ai:weather',
                 '2026-05-08T00:13:05.176Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/infrastructure:InfraSegment',
                 'did:web:maps.gftd.ai:infrastructure',
                 'InfraSegment',
                 1000000,
                 0.3,
                 720,
                 'did:web:maps.gftd.ai:infrastructure',
                 '2026-05-08T00:13:05.176Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/infrastructure:CollectionJob',
                 'did:web:maps.gftd.ai:infrastructure',
                 'CollectionJob',
                 100000,
                 0.1,
                 720,
                 'did:web:maps.gftd.ai:infrastructure',
                 '2026-05-08T00:13:05.176Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
