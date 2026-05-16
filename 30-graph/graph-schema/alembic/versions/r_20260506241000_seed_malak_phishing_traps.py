"""Captured from Kysely migration 20260506241000_seed_malak_phishing_traps."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506241000_seed_malak_phishing_traps"
down_revision = 'r_20260506240000_vertex_malak_phishing_trap'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_malak_phishing_trap (\n'
         '      vertex_id,\n'
         '      rkey,\n'
         '      repo,\n'
         '      trap_id,\n'
         '      trap_kind,\n'
         '      address,\n'
         '      provider,\n'
         '      label,\n'
         '      legal_basis,\n'
         '      retention_policy,\n'
         '      status,\n'
         '      created_at,\n'
         '      updated_at,\n'
         '      created_date,\n'
         '      sensitivity_ord,\n'
         '      owner_did,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_did,\n'
         '      org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         "      'email',\n"
         '      $5,\n'
         "      'gftd-owned-inbound-mail',\n"
         "      'Malak primary inbound-only phishing spamtrap',\n"
         "      'owned_inbound_spamtrap_defensive_cti',\n"
         "      'hash_and_preview_only',\n"
         "      'active',\n"
         '      $6,\n'
         '      $7,\n'
         '      CAST($8 AS DATE),\n'
         '      100,\n'
         '      $9,\n'
         '      $10,\n'
         '      $11,\n'
         '      $12,\n'
         '      $13\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1\n'
         '      FROM vertex_malak_phishing_trap\n'
         '      WHERE trap_id = $14\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:malak.gftd.ai/ai.gftd.apps.malak.phishingTrap/trap-email-malak-spamtrap-primary',
                 'trap-email-malak-spamtrap-primary',
                 'did:web:malak.gftd.ai',
                 'trap-email-malak-spamtrap-primary',
                 'spamtrap@malak.gftd.ai',
                 '2026-05-06T00:00:00.000Z',
                 '2026-05-06T00:00:00.000Z',
                 '2026-05-06',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'trap-email-malak-spamtrap-primary']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': '\n    DELETE FROM vertex_malak_phishing_trap\n    WHERE trap_id = $1\n  ',
  'parameters': ['trap-email-malak-spamtrap-primary']},
 {'sql': 'FLUSH', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
