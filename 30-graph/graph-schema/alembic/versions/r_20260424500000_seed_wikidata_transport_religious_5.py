"""Captured from Kysely migration 20260424500000_seed_wikidata_transport_religious_5."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424500000_seed_wikidata_transport_religious_5"
down_revision = 'r_20260424490000_seed_osm_notes_regions_3'
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
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-tramStop:Station',
                 'did:web:maps.gftd.ai:registry:wikidata:tramStop',
                 'Station',
                 50000,
                 0.6,
                 'did:web:maps.gftd.ai:registry:wikidata:tramStop',
                 '2026-05-08T00:20:44.976Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-monasteryWd:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:monasteryWd',
                 'Spot',
                 15000,
                 0.7,
                 'did:web:maps.gftd.ai:registry:wikidata:monasteryWd',
                 '2026-05-08T00:20:44.976Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-funeralHomeWd:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:funeralHomeWd',
                 'Spot',
                 30000,
                 0.5,
                 'did:web:maps.gftd.ai:registry:wikidata:funeralHomeWd',
                 '2026-05-08T00:20:44.976Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-crematoriumWd:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:crematoriumWd',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.gftd.ai:registry:wikidata:crematoriumWd',
                 '2026-05-08T00:20:44.976Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-ferryRouteWd:Spot',
                 'did:web:maps.gftd.ai:registry:wikidata:ferryRouteWd',
                 'Spot',
                 3000,
                 0.6,
                 'did:web:maps.gftd.ai:registry:wikidata:ferryRouteWd',
                 '2026-05-08T00:20:44.976Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
