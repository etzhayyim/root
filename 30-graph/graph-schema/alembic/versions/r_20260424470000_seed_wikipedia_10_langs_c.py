"""Captured from Kysely migration 20260424470000_seed_wikipedia_10_langs_c."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424470000_seed_wikipedia_10_langs_c"
down_revision = 'r_20260424460000_seed_wikidata_sports_edu_5'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-eo:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:eo',
                 400000,
                 'did:web:maps.etzhayyim.com:wikipedia:eo',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-am:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:am',
                 15000,
                 'did:web:maps.etzhayyim.com:wikipedia:am',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-io:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:io',
                 40000,
                 'did:web:maps.etzhayyim.com:wikipedia:io',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-xh:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:xh',
                 5000,
                 'did:web:maps.etzhayyim.com:wikipedia:xh',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-zu:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:zu',
                 5000,
                 'did:web:maps.etzhayyim.com:wikipedia:zu',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-so:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:so',
                 5000,
                 'did:web:maps.etzhayyim.com:wikipedia:so',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-ig:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ig',
                 8000,
                 'did:web:maps.etzhayyim.com:wikipedia:ig',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-yo:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:yo',
                 15000,
                 'did:web:maps.etzhayyim.com:wikipedia:yo',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-haw:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:haw',
                 2000,
                 'did:web:maps.etzhayyim.com:wikipedia:haw',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.4,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-sah:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:sah',
                 15000,
                 'did:web:maps.etzhayyim.com:wikipedia:sah',
                 '2026-05-08T00:20:31.719Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
