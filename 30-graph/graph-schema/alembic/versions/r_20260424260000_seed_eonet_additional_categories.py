"""Captured from Kysely migration 20260424260000_seed_eonet_additional_categories."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424260000_seed_eonet_additional_categories"
down_revision = 'r_20260424254000_vertex_open_cyber_compliance'
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
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/eonet-seaLakeIce:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:seaLakeIce',
                 'SpatialEvent',
                 50,
                 0.3,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:seaLakeIce',
                 '2026-05-08T00:19:08.108Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/eonet-snow:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:snow',
                 'SpatialEvent',
                 20,
                 0.3,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:snow',
                 '2026-05-08T00:19:08.108Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/eonet-dustHaze:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:dustHaze',
                 'SpatialEvent',
                 30,
                 0.3,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:dustHaze',
                 '2026-05-08T00:19:08.108Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/eonet-tempExtremes:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:tempExtremes',
                 'SpatialEvent',
                 20,
                 0.3,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:tempExtremes',
                 '2026-05-08T00:19:08.108Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/eonet-earthquakes:SpatialEvent',
                 'did:web:maps.etzhayyim.com:eonet:earthquakes',
                 'SpatialEvent',
                 100,
                 0.3,
                 6,
                 'did:web:maps.etzhayyim.com:eonet:earthquakes',
                 '2026-05-08T00:19:08.108Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
