"""Captured from Kysely migration 20260428234000_vertex_open_cyber_source."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428234000_vertex_open_cyber_source"
down_revision = 'r_20260428230200_mv_open_cyber_vuln_analytics'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_cyber_source (\n'
         '      vertex_id         varchar PRIMARY KEY,\n'
         '      _seq              bigint,\n'
         '      created_date      date,\n'
         '      sensitivity_ord   int,\n'
         '      owner_did         varchar,\n'
         '      source_id         varchar NOT NULL,\n'
         '      display_name      varchar NOT NULL,\n'
         '      base_url          varchar NOT NULL,\n'
         '      cadence_iso8601   varchar NOT NULL,\n'
         '      auth_strategy     varchar NOT NULL,\n'
         '      secret_ref        varchar,\n'
         '      license           varchar,\n'
         '      last_cursor       varchar,\n'
         '      last_fetched_at   varchar,\n'
         '      status            varchar NOT NULL,\n'
         '      created_at        varchar,\n'
         '      org_id            varchar,\n'
         '      user_id           varchar,\n'
         '      actor_id          varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_open_cyber_source\n'
         '        (vertex_id, sensitivity_ord, owner_did, source_id, display_name, base_url, '
         'cadence_iso8601, auth_strategy, secret_ref, license, last_cursor, last_fetched_at, '
         'status, created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10, null, 'active', $11, $12, $13, "
         "'sys.bpmn.seed.open-cyber'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_open_cyber_source WHERE source_id = $14)\n'
         '    ',
  'parameters': ['at://did:web:open-cyber-vuln.etzhayyim.com/com.etzhayyim.apps.openCyberVuln.source/nvd',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'nvd',
                 'NVD CVE 2.0 API',
                 'https://services.nvd.nist.gov/rest/json/cves/2.0',
                 'R/PT6H',
                 'none',
                 None,
                 'public-domain',
                 '2024-01-01T00:00:00.000',
                 '2026-04-28T23:40:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'nvd']},
 {'sql': '\n'
         '      INSERT INTO vertex_open_cyber_source\n'
         '        (vertex_id, sensitivity_ord, owner_did, source_id, display_name, base_url, '
         'cadence_iso8601, auth_strategy, secret_ref, license, last_cursor, last_fetched_at, '
         'status, created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10, null, 'active', $11, $12, $13, "
         "'sys.bpmn.seed.open-cyber'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_open_cyber_source WHERE source_id = $14)\n'
         '    ',
  'parameters': ['at://did:web:open-cyber-vuln.etzhayyim.com/com.etzhayyim.apps.openCyberVuln.source/cisa-kev',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'cisa-kev',
                 'CISA Known Exploited Vulnerabilities',
                 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
                 'R/PT12H',
                 'none',
                 None,
                 'public-domain',
                 None,
                 '2026-04-28T23:40:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'cisa-kev']},
 {'sql': '\n'
         '      INSERT INTO vertex_open_cyber_source\n'
         '        (vertex_id, sensitivity_ord, owner_did, source_id, display_name, base_url, '
         'cadence_iso8601, auth_strategy, secret_ref, license, last_cursor, last_fetched_at, '
         'status, created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10, null, 'active', $11, $12, $13, "
         "'sys.bpmn.seed.open-cyber'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_open_cyber_source WHERE source_id = $14)\n'
         '    ',
  'parameters': ['at://did:web:open-cyber-vuln.etzhayyim.com/com.etzhayyim.apps.openCyberVuln.source/ghsa',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'ghsa',
                 'GitHub Security Advisories (GHSA)',
                 'https://api.github.com/advisories',
                 'R/PT12H',
                 'none',
                 None,
                 'cc-by-4.0',
                 '2024-01-01T00:00:00Z',
                 '2026-04-28T23:40:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'ghsa']},
 {'sql': '\n'
         '      INSERT INTO vertex_open_cyber_source\n'
         '        (vertex_id, sensitivity_ord, owner_did, source_id, display_name, base_url, '
         'cadence_iso8601, auth_strategy, secret_ref, license, last_cursor, last_fetched_at, '
         'status, created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10, null, 'active', $11, $12, $13, "
         "'sys.bpmn.seed.open-cyber'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_open_cyber_source WHERE source_id = $14)\n'
         '    ',
  'parameters': ['at://did:web:open-cyber-vuln.etzhayyim.com/com.etzhayyim.apps.openCyberVuln.source/mitre-attack',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'mitre-attack',
                 'MITRE ATT&CK TAXII 2.1',
                 'https://cti-taxii.mitre.org/stix/collections/95ecc380-afe9-11e4-9b6c-751b66dd541e/objects/',
                 'R/PT24H',
                 'none',
                 None,
                 'cc-by-4.0',
                 None,
                 '2026-04-28T23:40:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'mitre-attack']},
 {'sql': '\n'
         '      INSERT INTO vertex_open_cyber_source\n'
         '        (vertex_id, sensitivity_ord, owner_did, source_id, display_name, base_url, '
         'cadence_iso8601, auth_strategy, secret_ref, license, last_cursor, last_fetched_at, '
         'status, created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, 1, $2, $3, $4, $5, $6, $7, $8, $9, $10, null, 'active', $11, $12, $13, "
         "'sys.bpmn.seed.open-cyber'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_open_cyber_source WHERE source_id = $14)\n'
         '    ',
  'parameters': ['at://did:web:open-cyber-vuln.etzhayyim.com/com.etzhayyim.apps.openCyberVuln.source/cisa-alerts',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'cisa-alerts',
                 'CISA US-CERT Alerts Atom Feed',
                 'https://www.cisa.gov/uscert/ncas/alerts.xml',
                 'R/PT6H',
                 'none',
                 None,
                 'public-domain',
                 None,
                 '2026-04-28T23:40:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'cisa-alerts']}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_open_cyber_source', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
