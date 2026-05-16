"""Captured from Kysely migration 20260424300000_seed_wikipedia_30_more_langs."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424300000_seed_wikipedia_30_more_langs"
down_revision = 'r_20260424290000_productivity_weighting'
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-simple:Spot',
                 'did:web:maps.gftd.ai:wikipedia:simple',
                 'Spot',
                 150000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:simple',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ml:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ml',
                 'Spot',
                 90000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:ml',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ta:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ta',
                 'Spot',
                 200000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:ta',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-te:Spot',
                 'did:web:maps.gftd.ai:wikipedia:te',
                 'Spot',
                 80000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:te',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-kn:Spot',
                 'did:web:maps.gftd.ai:wikipedia:kn',
                 'Spot',
                 35000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:kn',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-mr:Spot',
                 'did:web:maps.gftd.ai:wikipedia:mr',
                 'Spot',
                 90000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:mr',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-gu:Spot',
                 'did:web:maps.gftd.ai:wikipedia:gu',
                 'Spot',
                 30000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:gu',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-pa:Spot',
                 'did:web:maps.gftd.ai:wikipedia:pa',
                 'Spot',
                 45000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:pa',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ur:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ur',
                 'Spot',
                 210000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:ur',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-fa:Spot',
                 'did:web:maps.gftd.ai:wikipedia:fa',
                 'Spot',
                 900000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:fa',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-uz:Spot',
                 'did:web:maps.gftd.ai:wikipedia:uz',
                 'Spot',
                 220000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:uz',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ka:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ka',
                 'Spot',
                 170000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:ka',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-my:Spot',
                 'did:web:maps.gftd.ai:wikipedia:my',
                 'Spot',
                 120000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:my',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-km:Spot',
                 'did:web:maps.gftd.ai:wikipedia:km',
                 'Spot',
                 12000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:km',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-si:Spot',
                 'did:web:maps.gftd.ai:wikipedia:si',
                 'Spot',
                 24000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:si',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ne:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ne',
                 'Spot',
                 35000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:ne',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-jv:Spot',
                 'did:web:maps.gftd.ai:wikipedia:jv',
                 'Spot',
                 75000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:jv',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-su:Spot',
                 'did:web:maps.gftd.ai:wikipedia:su',
                 'Spot',
                 65000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:su',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ms:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ms',
                 'Spot',
                 370000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:ms',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-mn:Spot',
                 'did:web:maps.gftd.ai:wikipedia:mn',
                 'Spot',
                 22000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:mn',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-mk:Spot',
                 'did:web:maps.gftd.ai:wikipedia:mk',
                 'Spot',
                 140000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:mk',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-sr:Spot',
                 'did:web:maps.gftd.ai:wikipedia:sr',
                 'Spot',
                 670000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:sr',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-hr:Spot',
                 'did:web:maps.gftd.ai:wikipedia:hr',
                 'Spot',
                 220000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:hr',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-sl:Spot',
                 'did:web:maps.gftd.ai:wikipedia:sl',
                 'Spot',
                 180000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:sl',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-lv:Spot',
                 'did:web:maps.gftd.ai:wikipedia:lv',
                 'Spot',
                 115000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:lv',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-lt:Spot',
                 'did:web:maps.gftd.ai:wikipedia:lt',
                 'Spot',
                 210000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:lt',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-et:Spot',
                 'did:web:maps.gftd.ai:wikipedia:et',
                 'Spot',
                 225000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:et',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-is:Spot',
                 'did:web:maps.gftd.ai:wikipedia:is',
                 'Spot',
                 55000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:is',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-ga:Spot',
                 'did:web:maps.gftd.ai:wikipedia:ga',
                 'Spot',
                 58000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:ga',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikipedia-cy:Spot',
                 'did:web:maps.gftd.ai:wikipedia:cy',
                 'Spot',
                 160000,
                 0.6,
                 168,
                 'did:web:maps.gftd.ai:wikipedia:cy',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
