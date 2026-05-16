"""Captured from Kysely migration 20260424490000_seed_osm_notes_regions_3."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424490000_seed_osm_notes_regions_3"
down_revision = 'r_20260424480000_purge_phase51_dead_qids'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/osm_notes-eu:Spot',
                 'did:web:maps.gftd.ai:osm_notes:eu',
                 40000,
                 0.7,
                 'did:web:maps.gftd.ai:osm_notes:eu',
                 '2026-05-08T00:20:39.953Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/osm_notes-us:Spot',
                 'did:web:maps.gftd.ai:osm_notes:us',
                 30000,
                 0.7,
                 'did:web:maps.gftd.ai:osm_notes:us',
                 '2026-05-08T00:20:39.953Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/osm_notes-global:Spot',
                 'did:web:maps.gftd.ai:osm_notes:global',
                 30000,
                 0.6,
                 'did:web:maps.gftd.ai:osm_notes:global',
                 '2026-05-08T00:20:39.953Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
