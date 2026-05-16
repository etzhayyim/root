"""Captured from Kysely migration 20260424380000_seed_wikipedia_20_more_langs_b."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424380000_seed_wikipedia_20_more_langs_b"
down_revision = 'r_20260424370000_seed_wikidata_historical_10'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-tt:Spot',
                 'did:web:maps.gftd.ai:wikipedia:tt',
                 300000,
                 'did:web:maps.gftd.ai:wikipedia:tt',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-min:Spot',
                 'did:web:maps.gftd.ai:wikipedia:min',
                 250000,
                 'did:web:maps.gftd.ai:wikipedia:min',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-tg:Spot',
                 'did:web:maps.gftd.ai:wikipedia:tg',
                 250000,
                 'did:web:maps.gftd.ai:wikipedia:tg',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ast:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ast',
                 100000,
                 'did:web:maps.gftd.ai:wikipedia:ast',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-mg:Spot',
                 'did:web:maps.gftd.ai:wikipedia:mg',
                 95000,
                 'did:web:maps.gftd.ai:wikipedia:mg',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ky:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ky',
                 80000,
                 'did:web:maps.gftd.ai:wikipedia:ky',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-lmo:Spot',
                 'did:web:maps.gftd.ai:wikipedia:lmo',
                 70000,
                 'did:web:maps.gftd.ai:wikipedia:lmo',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-pms:Spot',
                 'did:web:maps.gftd.ai:wikipedia:pms',
                 65000,
                 'did:web:maps.gftd.ai:wikipedia:pms',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ba:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ba',
                 60000,
                 'did:web:maps.gftd.ai:wikipedia:ba',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-fy:Spot',
                 'did:web:maps.gftd.ai:wikipedia:fy',
                 50000,
                 'did:web:maps.gftd.ai:wikipedia:fy',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-an:Spot',
                 'did:web:maps.gftd.ai:wikipedia:an',
                 40000,
                 'did:web:maps.gftd.ai:wikipedia:an',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ckb:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ckb',
                 40000,
                 'did:web:maps.gftd.ai:wikipedia:ckb',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-bar:Spot',
                 'did:web:maps.gftd.ai:wikipedia:bar',
                 35000,
                 'did:web:maps.gftd.ai:wikipedia:bar',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-scn:Spot',
                 'did:web:maps.gftd.ai:wikipedia:scn',
                 25000,
                 'did:web:maps.gftd.ai:wikipedia:scn',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-gd:Spot',
                 'did:web:maps.gftd.ai:wikipedia:gd',
                 15000,
                 'did:web:maps.gftd.ai:wikipedia:gd',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-yi:Spot',
                 'did:web:maps.gftd.ai:wikipedia:yi',
                 15000,
                 'did:web:maps.gftd.ai:wikipedia:yi',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-wa:Spot',
                 'did:web:maps.gftd.ai:wikipedia:wa',
                 15000,
                 'did:web:maps.gftd.ai:wikipedia:wa',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ha:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ha',
                 10000,
                 'did:web:maps.gftd.ai:wikipedia:ha',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-mi:Spot',
                 'did:web:maps.gftd.ai:wikipedia:mi',
                 10000,
                 'did:web:maps.gftd.ai:wikipedia:mi',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-mt:Spot',
                 'did:web:maps.gftd.ai:wikipedia:mt',
                 5000,
                 'did:web:maps.gftd.ai:wikipedia:mt',
                 '2026-05-08T00:20:04.258Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
