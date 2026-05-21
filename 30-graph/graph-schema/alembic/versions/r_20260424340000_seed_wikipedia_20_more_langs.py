"""Captured from Kysely migration 20260424340000_seed_wikipedia_20_more_langs."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424340000_seed_wikipedia_20_more_langs"
down_revision = 'r_20260424330000_seed_wikidata_civic_10'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-uk:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:uk',
                 1200000,
                 'did:web:maps.etzhayyim.com:wikipedia:uk',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-ceb:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ceb',
                 6100000,
                 'did:web:maps.etzhayyim.com:wikipedia:ceb',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-war:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:war',
                 1300000,
                 'did:web:maps.etzhayyim.com:wikipedia:war',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-ca:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ca',
                 700000,
                 'did:web:maps.etzhayyim.com:wikipedia:ca',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-ro:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ro',
                 430000,
                 'did:web:maps.etzhayyim.com:wikipedia:ro',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-bg:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:bg',
                 290000,
                 'did:web:maps.etzhayyim.com:wikipedia:bg',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-sk:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:sk',
                 240000,
                 'did:web:maps.etzhayyim.com:wikipedia:sk',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-eu:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:eu',
                 400000,
                 'did:web:maps.etzhayyim.com:wikipedia:eu',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-gl:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:gl',
                 200000,
                 'did:web:maps.etzhayyim.com:wikipedia:gl',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-la:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:la',
                 140000,
                 'did:web:maps.etzhayyim.com:wikipedia:la',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-vo:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:vo',
                 120000,
                 'did:web:maps.etzhayyim.com:wikipedia:vo',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-af:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:af',
                 100000,
                 'did:web:maps.etzhayyim.com:wikipedia:af',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-sw:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:sw',
                 80000,
                 'did:web:maps.etzhayyim.com:wikipedia:sw',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-az:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:az',
                 200000,
                 'did:web:maps.etzhayyim.com:wikipedia:az',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-hy:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:hy',
                 290000,
                 'did:web:maps.etzhayyim.com:wikipedia:hy',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-kk:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:kk',
                 240000,
                 'did:web:maps.etzhayyim.com:wikipedia:kk',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-tl:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:tl',
                 45000,
                 'did:web:maps.etzhayyim.com:wikipedia:tl',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-lb:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:lb',
                 60000,
                 'did:web:maps.etzhayyim.com:wikipedia:lb',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-sq:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:sq',
                 100000,
                 'did:web:maps.etzhayyim.com:wikipedia:sq',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, 0.6,\n"
         "        168.0, 'anon', 'anon', $4, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-vec:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:vec',
                 70000,
                 'did:web:maps.etzhayyim.com:wikipedia:vec',
                 '2026-05-08T00:19:48.022Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
