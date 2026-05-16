"""Captured from Kysely migration 20260424240000_seed_wikivoyage_10_more_langs."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424240000_seed_wikivoyage_10_more_langs"
down_revision = 'r_20260424234000_vertex_open_panama_neopanamax'
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-es:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:es',
                 'Spot',
                 8000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:es',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-it:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:it',
                 'Spot',
                 7000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:it',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-pt:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:pt',
                 'Spot',
                 5000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:pt',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-nl:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:nl',
                 'Spot',
                 6000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:nl',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-ru:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:ru',
                 'Spot',
                 10000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:ru',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-zh:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:zh',
                 'Spot',
                 5000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:zh',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-ja:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:ja',
                 'Spot',
                 5000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:ja',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-pl:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:pl',
                 'Spot',
                 6000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:pl',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-sv:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:sv',
                 'Spot',
                 4000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:sv',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-uk:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:uk',
                 'Spot',
                 3000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:uk',
                 '2026-05-08T00:18:57.409Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
