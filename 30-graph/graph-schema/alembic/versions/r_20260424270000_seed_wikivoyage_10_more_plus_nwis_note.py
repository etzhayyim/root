"""Captured from Kysely migration 20260424270000_seed_wikivoyage_10_more_plus_nwis_note."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424270000_seed_wikivoyage_10_more_plus_nwis_note"
down_revision = 'r_20260424260000_seed_eonet_additional_categories'
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-ro:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:ro',
                 'Spot',
                 2000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:ro',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-he:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:he',
                 'Spot',
                 2000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:he',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-ar:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:ar',
                 'Spot',
                 1500,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:ar',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-tr:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:tr',
                 'Spot',
                 2000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:tr',
                 '2026-05-08T00:19:15.171Z']},
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
                 2500,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:uk',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-cs:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:cs',
                 'Spot',
                 2000,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:cs',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-sk:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:sk',
                 'Spot',
                 800,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:sk',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-fi:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:fi',
                 'Spot',
                 1500,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:fi',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-no:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:no',
                 'Spot',
                 1500,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:no',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/wikivoyage-da:Spot',
                 'did:web:maps.gftd.ai:wikivoyage:da',
                 'Spot',
                 1200,
                 0.3,
                 168,
                 'did:web:maps.gftd.ai:wikivoyage:da',
                 '2026-05-08T00:19:15.171Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
