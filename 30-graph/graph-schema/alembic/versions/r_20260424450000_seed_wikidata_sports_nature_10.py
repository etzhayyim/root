"""Captured from Kysely migration 20260424450000_seed_wikidata_sports_nature_10."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424450000_seed_wikidata_sports_nature_10"
down_revision = 'r_20260424440000_purge_dead_wikivoyage'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-footballStadium:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:footballStadium',
                 'Spot',
                 20000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:footballStadium',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-canyon:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:canyon',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:canyon',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-orchard:Farmland',
                 'did:web:maps.etzhayyim.com:registry:wikidata:orchard',
                 'Farmland',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:orchard',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-wetland:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:wetland',
                 'Spot',
                 20000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:wetland',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-atoll:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:atoll',
                 'Spot',
                 2000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:atoll',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-themePark:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:themePark',
                 'Spot',
                 1000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:themePark',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-hotSpringWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:hotSpringWd',
                 'Spot',
                 5000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:hotSpringWd',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-waterpark:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:waterpark',
                 'Spot',
                 2000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:waterpark',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-fortress:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:fortress',
                 'Spot',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:fortress',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-iceberg:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:iceberg',
                 'Spot',
                 1500,
                 0.5,
                 'did:web:maps.etzhayyim.com:registry:wikidata:iceberg',
                 '2026-05-08T00:20:23.987Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
