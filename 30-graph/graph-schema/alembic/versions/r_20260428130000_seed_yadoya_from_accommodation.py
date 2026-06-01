"""Captured from Kysely migration 20260428130000_seed_yadoya_from_accommodation."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428130000_seed_yadoya_from_accommodation"
down_revision = 'r_20260428130000_identity_canonical_columns'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_yadoya_hotel (\n'
         '      vertex_id, sensitivity_ord, owner_did,\n'
         '      hotel_slug, osm_id, chain_did, property_did,\n'
         '      name, country, region, city, lat, lon,\n'
         '      isic_code, price_jpy_min, price_jpy_max, capacity_rooms,\n'
         '      lang_codes, source_url, status,\n'
         '      created_at, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         "      'at://' || $1 || '/app.etzhayyim.apps.yadoya.hotel/' || a.osm_id,\n"
         '      1, $2,\n'
         '      a.osm_id,\n'
         '      a.osm_id,\n'
         '      NULL,\n'
         "      $3 || ':actor:property:' || a.osm_id,\n"
         "      COALESCE(a.name, 'unknown-' || a.osm_id),\n"
         "      COALESCE(a.country, 'JP'),\n"
         "      'asia',\n"
         '      a.city,\n'
         '      a.lat,\n'
         '      a.lon,\n'
         "      'I5510',\n"
         '      CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),\n'
         '      a.rooms,\n'
         "      'ja,en',\n"
         '      a.source_url,\n'
         "      'published',\n"
         "      $4, 'anon', 'anon', $5\n"
         '    FROM vertex_accommodation a\n'
         '    WHERE a.city IN ($6, $7, $8, $9, $10, $11, $12, $13, $14, $15)\n'
         '      AND a.type IN ($16, $17, $18)\n'
         '      AND a.osm_id IS NOT NULL\n'
         '      AND a.name IS NOT NULL\n'
         '      AND NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_yadoya_hotel y\n'
         "        WHERE y.vertex_id = 'at://' || $19 || '/app.etzhayyim.apps.yadoya.hotel/' || a.osm_id\n"
         '      )\n'
         '    LIMIT 200\n'
         '  ',
  'parameters': ['did:web:yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com',
                 '2026-04-28T13:00:00Z',
                 'sys.seed.yadoya-from-accommodation',
                 'Tokyo',
                 'Osaka',
                 'Kyoto',
                 'Fukuoka',
                 'Sapporo',
                 'Nagoya',
                 'Yokohama',
                 'Kobe',
                 'Sendai',
                 'Hiroshima',
                 'hotel',
                 'hostel',
                 'guest_house',
                 'did:web:yadoya.etzhayyim.com']},
 {'sql': '\n'
         '    INSERT INTO vertex_profile (\n'
         '      vertex_id, sensitivity_ord, owner_did,\n'
         '      did, repo, handle, display_name, description,\n'
         '      collection, rkey, created_at\n'
         '    )\n'
         '    SELECT\n'
         "      'at://' || y.property_did || '/app.bsky.actor.profile/self',\n"
         '      1, $1,\n'
         '      y.property_did,\n'
         '      y.property_did,\n'
         "      'property-' || y.osm_id || '.hospitality.etzhayyim.com',\n"
         '      y.name,\n'
         "      'Hospitality property (OSM ' || y.osm_id || ', ' || y.city || ', ' || y.country || "
         "')',\n"
         "      'app.bsky.actor.profile',\n"
         "      'self',\n"
         '      $2\n'
         '    FROM vertex_yadoya_hotel y\n'
         '    WHERE y.actor_id = $3\n'
         '      AND y.property_did IS NOT NULL\n'
         '      AND NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile p\n'
         "        WHERE p.vertex_id = 'at://' || y.property_did || '/app.bsky.actor.profile/self'\n"
         '      )\n'
         '  ',
  'parameters': ['did:web:hospitality.etzhayyim.com',
                 '2026-04-28T13:00:00Z',
                 'sys.seed.yadoya-from-accommodation']},
 {'sql': '\n'
         '    INSERT INTO edge_yadoya_property_to_chain (\n'
         '      edge_id, sensitivity_ord, owner_did,\n'
         '      src_vid, dst_vid, role,\n'
         '      created_at, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         "      'edge:yadoya:' || y.osm_id || ':property',\n"
         '      1, $1,\n'
         '      y.vertex_id,\n'
         "      'at://' || y.property_did || '/app.bsky.actor.profile/self',\n"
         "      'property-of',\n"
         "      $2, 'anon', 'anon', $3\n"
         '    FROM vertex_yadoya_hotel y\n'
         '    WHERE y.actor_id = $4\n'
         '      AND y.property_did IS NOT NULL\n'
         '      AND NOT EXISTS (\n'
         '        SELECT 1 FROM edge_yadoya_property_to_chain e\n'
         "        WHERE e.edge_id = 'edge:yadoya:' || y.osm_id || ':property'\n"
         '      )\n'
         '  ',
  'parameters': ['did:web:yadoya.etzhayyim.com',
                 '2026-04-28T13:00:00Z',
                 'sys.seed.yadoya-from-accommodation',
                 'sys.seed.yadoya-from-accommodation']}]

DOWN = [{'sql': 'DELETE FROM edge_yadoya_property_to_chain WHERE actor_id = $1',
  'parameters': ['sys.seed.yadoya-from-accommodation']},
 {'sql': 'DELETE FROM vertex_profile WHERE owner_did = $1 AND handle LIKE '
         "'property-%.hospitality.etzhayyim.com'",
  'parameters': ['did:web:hospitality.etzhayyim.com']},
 {'sql': 'DELETE FROM vertex_yadoya_hotel WHERE actor_id = $1',
  'parameters': ['sys.seed.yadoya-from-accommodation']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
