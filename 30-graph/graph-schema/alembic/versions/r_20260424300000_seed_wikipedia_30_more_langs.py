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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-simple:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:simple',
                 'Spot',
                 150000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:simple',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ml:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ml',
                 'Spot',
                 90000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ml',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ta:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ta',
                 'Spot',
                 200000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ta',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-te:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:te',
                 'Spot',
                 80000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:te',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-kn:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:kn',
                 'Spot',
                 35000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:kn',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-mr:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:mr',
                 'Spot',
                 90000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:mr',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-gu:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:gu',
                 'Spot',
                 30000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:gu',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-pa:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:pa',
                 'Spot',
                 45000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:pa',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ur:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ur',
                 'Spot',
                 210000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ur',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-fa:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:fa',
                 'Spot',
                 900000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:fa',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-uz:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:uz',
                 'Spot',
                 220000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:uz',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ka:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ka',
                 'Spot',
                 170000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ka',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-my:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:my',
                 'Spot',
                 120000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:my',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-km:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:km',
                 'Spot',
                 12000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:km',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-si:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:si',
                 'Spot',
                 24000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:si',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ne:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ne',
                 'Spot',
                 35000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ne',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-jv:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:jv',
                 'Spot',
                 75000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:jv',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-su:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:su',
                 'Spot',
                 65000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:su',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ms:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ms',
                 'Spot',
                 370000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ms',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-mn:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:mn',
                 'Spot',
                 22000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:mn',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-mk:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:mk',
                 'Spot',
                 140000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:mk',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-sr:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:sr',
                 'Spot',
                 670000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:sr',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-hr:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:hr',
                 'Spot',
                 220000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:hr',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-sl:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:sl',
                 'Spot',
                 180000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:sl',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-lv:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:lv',
                 'Spot',
                 115000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:lv',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-lt:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:lt',
                 'Spot',
                 210000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:lt',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-et:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:et',
                 'Spot',
                 225000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:et',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-is:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:is',
                 'Spot',
                 55000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:is',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-ga:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:ga',
                 'Spot',
                 58000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:ga',
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/wikipedia-cy:Spot',
                 'did:web:maps.etzhayyim.com:wikipedia:cy',
                 'Spot',
                 160000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:wikipedia:cy',
                 '2026-05-08T00:19:32.578Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
