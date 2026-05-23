"""Captured from Kysely migration 20260425000000_seed_wikidata_specialty_5."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425000000_seed_wikidata_specialty_5"
down_revision = 'r_20260424510000_rebase_world_total_saturating'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-powerLineWd:PowerLine',
                 'did:web:maps.etzhayyim.com:registry:wikidata:powerLineWd',
                 'PowerLine',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:powerLineWd',
                 '2026-05-08T00:21:19.048Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-radioAntenna:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:radioAntenna',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:radioAntenna',
                 '2026-05-08T00:21:19.048Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-fishingHarbor:Port',
                 'did:web:maps.etzhayyim.com:registry:wikidata:fishingHarbor',
                 'Port',
                 3000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:fishingHarbor',
                 '2026-05-08T00:21:19.048Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-artificialIsland:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:artificialIsland',
                 'Spot',
                 1500,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:artificialIsland',
                 '2026-05-08T00:21:19.048Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-amusementRideWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:amusementRideWd',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:amusementRideWd',
                 '2026-05-08T00:21:19.048Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
