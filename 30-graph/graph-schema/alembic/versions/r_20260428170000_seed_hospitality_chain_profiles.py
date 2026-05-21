"""Captured from Kysely migration 20260428170000_seed_hospitality_chain_profiles."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428170000_seed_hospitality_chain_profiles"
down_revision = None  # parent removed: vendor malak dashboard MV
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:marriott/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:marriott',
                 'did:web:hospitality.etzhayyim.com:actor:chain:marriott',
                 'chain-marriott-hospitality.etzhayyim.com',
                 'Marriott International',
                 'Global hotel chain (ISIC I5510). Brands: Marriott, Sheraton, Westin, '
                 'Ritz-Carlton, JW Marriott.',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:marriott/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:hilton/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:hilton',
                 'did:web:hospitality.etzhayyim.com:actor:chain:hilton',
                 'chain-hilton-hospitality.etzhayyim.com',
                 'Hilton Worldwide',
                 'Global hotel chain (ISIC I5510). Brands: Hilton, Conrad, Waldorf Astoria, '
                 'DoubleTree, Hampton.',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:hilton/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:hyatt/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:hyatt',
                 'did:web:hospitality.etzhayyim.com:actor:chain:hyatt',
                 'chain-hyatt-hospitality.etzhayyim.com',
                 'Hyatt Hotels Corporation',
                 'Global hotel chain (ISIC I5510). Brands: Park Hyatt, Grand Hyatt, Hyatt Regency, '
                 'Andaz.',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:hyatt/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:ihg/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:ihg',
                 'did:web:hospitality.etzhayyim.com:actor:chain:ihg',
                 'chain-ihg-hospitality.etzhayyim.com',
                 'InterContinental Hotels Group',
                 'Global hotel chain (ISIC I5510). Brands: InterContinental, Holiday Inn, Crowne '
                 'Plaza, Kimpton.',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:ihg/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:accor/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:accor',
                 'did:web:hospitality.etzhayyim.com:actor:chain:accor',
                 'chain-accor-hospitality.etzhayyim.com',
                 'Accor',
                 'Global hotel chain (ISIC I5510). Brands: Sofitel, Mercure, Novotel, ibis, '
                 'Raffles.',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:accor/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:wyndham/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:wyndham',
                 'did:web:hospitality.etzhayyim.com:actor:chain:wyndham',
                 'chain-wyndham-hospitality.etzhayyim.com',
                 'Wyndham Hotels & Resorts',
                 'Global hotel chain (ISIC I5510).',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:wyndham/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:choice/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:choice',
                 'did:web:hospitality.etzhayyim.com:actor:chain:choice',
                 'chain-choice-hospitality.etzhayyim.com',
                 'Choice Hotels International',
                 'Global hotel chain (ISIC I5510). Brands: Comfort Inn, Quality Inn.',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:choice/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:hoshino/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:hoshino',
                 'did:web:hospitality.etzhayyim.com:actor:chain:hoshino',
                 'chain-hoshino-hospitality.etzhayyim.com',
                 '星野リゾート (Hoshino Resorts)',
                 'Japanese hotel chain (ISIC I5510). Brands: 星のや, リゾナーレ, OMO, BEB.',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:hoshino/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:prince/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:prince',
                 'did:web:hospitality.etzhayyim.com:actor:chain:prince',
                 'chain-prince-hospitality.etzhayyim.com',
                 'プリンスホテル (Prince Hotels)',
                 'Japanese hotel chain (ISIC I5510).',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:prince/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:tokyu-stay/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:tokyu-stay',
                 'did:web:hospitality.etzhayyim.com:actor:chain:tokyu-stay',
                 'chain-tokyu-stay-hospitality.etzhayyim.com',
                 '東急ステイ (Tokyu Stay)',
                 'Japanese hotel chain (ISIC I5510).',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:tokyu-stay/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:apa/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:apa',
                 'did:web:hospitality.etzhayyim.com:actor:chain:apa',
                 'chain-apa-hospitality.etzhayyim.com',
                 'アパホテル (APA Hotel)',
                 'Japanese hotel chain (ISIC I5510).',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:apa/app.bsky.actor.profile/self']},
 {'sql': '\n'
         '      INSERT INTO vertex_profile (\n'
         '        vertex_id, sensitivity_ord, owner_did,\n'
         '        did, repo, handle, display_name, description,\n'
         '        collection, rkey, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, 1, $2,\n'
         '        $3, $4, $5, $6, $7,\n'
         "        'app.bsky.actor.profile', 'self', $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_profile WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:hospitality.etzhayyim.com:actor:chain:route-inn/app.bsky.actor.profile/self',
                 'did:web:hospitality.etzhayyim.com',
                 'did:web:hospitality.etzhayyim.com:actor:chain:route-inn',
                 'did:web:hospitality.etzhayyim.com:actor:chain:route-inn',
                 'chain-route-inn-hospitality.etzhayyim.com',
                 'ルートイン (Route Inn)',
                 'Japanese hotel chain (ISIC I5510).',
                 '2026-04-28T17:00:00Z',
                 'at://did:web:hospitality.etzhayyim.com:actor:chain:route-inn/app.bsky.actor.profile/self']}]

DOWN = [{'sql': '\n'
         '    DELETE FROM vertex_profile\n'
         '    WHERE owner_did = $1\n'
         "      AND handle LIKE 'chain-%.hospitality.etzhayyim.com'\n"
         '      AND created_at = $2\n'
         '  ',
  'parameters': ['did:web:hospitality.etzhayyim.com', '2026-04-28T17:00:00Z']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
