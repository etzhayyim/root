"""Captured from Kysely migration 20260424320000_seed_overpass_civic_religion_15."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424320000_seed_overpass_civic_religion_15"
down_revision = 'r_20260424310000_vertex_bim_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:University',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'University',
                 30000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:College',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'College',
                 60000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:TownHall',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'TownHall',
                 100000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Courthouse',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Courthouse',
                 15000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Embassy',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Embassy',
                 3500,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:FerryTerminal',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'FerryTerminal',
                 4500,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Toilets',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Toilets',
                 2000000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:FastFood',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'FastFood',
                 1200000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Bar',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Bar',
                 1500000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Nightclub',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Nightclub',
                 80000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Church',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Church',
                 500000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:BuddhistTemple',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'BuddhistTemple',
                 80000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:Shrine',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Shrine',
                 80000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:HinduTemple',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'HinduTemple',
                 50000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, 0.6,\n'
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/infrastructure:SikhTemple',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'SikhTemple',
                 10000,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:19:41.140Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
