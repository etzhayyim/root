"""Captured from Kysely migration 20260508910200_seed_webya_templates."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508910200_seed_webya_templates"
down_revision = 'r_20260508910100_seed_webya_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_webya_template\n'
         '        (vertex_id, template_id, profession_kind, pages_json,\n'
         '         html_skeleton, slot_schema_json, version, active, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3, $4,\n'
         '        $5, $6, 1, TRUE, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/law-firm-v1',
                 'template_law_firm_v1',
                 'law_firm',
                 '["home","about","practice_areas","attorneys","fee","access","contact"]',
                 '<!DOCTYPE html>\n'
                 '<html lang="ja">\n'
                 '<head>\n'
                 '  <meta charset="UTF-8">\n'
                 '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                 '  <title>{{ title }} | {{ client_name }}</title>\n'
                 '  <meta name="description" content="{{ meta_description }}">\n'
                 '  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% '
                 'endif %}\n'
                 '  <link rel="stylesheet" href="/assets/law-firm-v1.css">\n'
                 '</head>\n'
                 '<body class="law-firm" data-profession="law_firm">\n'
                 '  <header>\n'
                 '    <nav><a href="/" class="brand">{{ client_name }}</a>\n'
                 '    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label '
                 '}}</a></li>{% endfor %}</ul>\n'
                 '    </nav>\n'
                 '  </header>\n'
                 '  <main>{% block content %}{% endblock %}</main>\n'
                 '  <footer>\n'
                 '    <p>{{ client_name }} | {{ bar_association }} 登録番号: {{ '
                 'bar_registration_number }}</p>\n'
                 '    <p>{{ address }} | TEL: {{ phone }}</p>\n'
                 '  </footer>\n'
                 '</body>\n'
                 '</html>',
                 '{"home":{"required":["hero_headline","hero_sub","cta_label"],"optional":["key_strengths"]},"about":{"required":["history","philosophy","bar_association","bar_registration_number","representative_attorney"],"optional":["awards","team_intro"]},"practice_areas":{"required":["areas"],"optional":[]},"attorneys":{"required":["attorneys"],"optional":[]},"fee":{"required":["fee_table","disclaimer"],"optional":["free_consultation_note"]},"access":{"required":["address","hours"],"optional":["nearest_station","parking"]},"contact":{"required":["phone","email"],"optional":["form_note","response_time"]}}',
                 '2026-05-08T09:20:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_webya_template\n'
         '        (vertex_id, template_id, profession_kind, pages_json,\n'
         '         html_skeleton, slot_schema_json, version, active, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3, $4,\n'
         '        $5, $6, 1, TRUE, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/accounting-firm-v1',
                 'template_accounting_firm_v1',
                 'accounting_firm',
                 '["home","about","services","staff","fee_guide","access","contact"]',
                 '<!DOCTYPE html>\n'
                 '<html lang="ja">\n'
                 '<head>\n'
                 '  <meta charset="UTF-8">\n'
                 '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                 '  <title>{{ title }} | {{ client_name }}</title>\n'
                 '  <meta name="description" content="{{ meta_description }}">\n'
                 '  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% '
                 'endif %}\n'
                 '  <link rel="stylesheet" href="/assets/accounting-firm-v1.css">\n'
                 '</head>\n'
                 '<body class="accounting-firm" data-profession="accounting_firm">\n'
                 '  <header>\n'
                 '    <nav><a href="/" class="brand">{{ client_name }}</a>\n'
                 '    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label '
                 '}}</a></li>{% endfor %}</ul>\n'
                 '    </nav>\n'
                 '  </header>\n'
                 '  <main>{% block content %}{% endblock %}</main>\n'
                 '  <footer>\n'
                 '    <p>{{ client_name }} | {{ tax_attorney_association }} 登録番号: {{ '
                 'tax_attorney_registration_number }}</p>\n'
                 '    <p>{{ address }} | TEL: {{ phone }}</p>\n'
                 '  </footer>\n'
                 '</body>\n'
                 '</html>',
                 '{"home":{"required":["hero_headline","hero_sub","key_services"],"optional":["cta_label"]},"about":{"required":["history","philosophy","tax_attorney_association","tax_attorney_registration_number"],"optional":["awards","representative_profile"]},"services":{"required":["services"],"optional":[]},"staff":{"required":["staff"],"optional":[]},"fee_guide":{"required":["fee_table"],"optional":["consultation_note"]},"access":{"required":["address","hours"],"optional":["nearest_station","parking"]},"contact":{"required":["phone","email"],"optional":["form_note","response_time"]}}',
                 '2026-05-08T09:20:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_webya_template\n'
         '        (vertex_id, template_id, profession_kind, pages_json,\n'
         '         html_skeleton, slot_schema_json, version, active, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3, $4,\n'
         '        $5, $6, 1, TRUE, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/scrivener-v1',
                 'template_scrivener_v1',
                 'judicial_scrivener',
                 '["home","about","services","fee","access","contact"]',
                 '<!DOCTYPE html>\n'
                 '<html lang="ja">\n'
                 '<head>\n'
                 '  <meta charset="UTF-8">\n'
                 '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                 '  <title>{{ title }} | {{ client_name }}</title>\n'
                 '  <meta name="description" content="{{ meta_description }}">\n'
                 '  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% '
                 'endif %}\n'
                 '  <link rel="stylesheet" href="/assets/scrivener-v1.css">\n'
                 '</head>\n'
                 '<body class="scrivener" data-profession="{{ profession_kind }}">\n'
                 '  <header>\n'
                 '    <nav><a href="/" class="brand">{{ client_name }}</a>\n'
                 '    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label '
                 '}}</a></li>{% endfor %}</ul>\n'
                 '    </nav>\n'
                 '  </header>\n'
                 '  <main>{% block content %}{% endblock %}</main>\n'
                 '  <footer>\n'
                 '    <p>{{ client_name }} | {{ scrivener_association }} 登録番号: {{ '
                 'scrivener_registration_number }}</p>\n'
                 '    <p>{{ address }} | TEL: {{ phone }}</p>\n'
                 '  </footer>\n'
                 '</body>\n'
                 '</html>',
                 '{"home":{"required":["hero_headline","hero_sub","key_services"],"optional":["cta_label"]},"about":{"required":["history","philosophy","scrivener_association","scrivener_registration_number"],"optional":["judicial_cert_number","representative_profile"]},"services":{"required":["services"],"optional":[]},"fee":{"required":["fee_table"],"optional":["consultation_note","disclaimer"]},"access":{"required":["address","hours"],"optional":["nearest_station"]},"contact":{"required":["phone","email"],"optional":["form_note"]}}',
                 '2026-05-08T09:20:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_webya_template\n'
         '        (vertex_id, template_id, profession_kind, pages_json,\n'
         '         html_skeleton, slot_schema_json, version, active, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3, $4,\n'
         '        $5, $6, 1, TRUE, $7\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/company-v1',
                 'template_company_v1',
                 'general_company',
                 '["home","about","services","news","access","contact"]',
                 '<!DOCTYPE html>\n'
                 '<html lang="ja">\n'
                 '<head>\n'
                 '  <meta charset="UTF-8">\n'
                 '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                 '  <title>{{ title }} | {{ client_name }}</title>\n'
                 '  <meta name="description" content="{{ meta_description }}">\n'
                 '  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% '
                 'endif %}\n'
                 '  <link rel="stylesheet" href="/assets/company-v1.css">\n'
                 '</head>\n'
                 '<body class="company" data-profession="general_company">\n'
                 '  <header>\n'
                 '    <nav><a href="/" class="brand">{{ client_name }}</a>\n'
                 '    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label '
                 '}}</a></li>{% endfor %}</ul>\n'
                 '    </nav>\n'
                 '  </header>\n'
                 '  <main>{% block content %}{% endblock %}</main>\n'
                 '  <footer>\n'
                 '    <p>{{ client_name }}{% if corporate_number %} | 法人番号: {{ corporate_number '
                 '}}{% endif %}</p>\n'
                 '    <p>{{ address }} | TEL: {{ phone }}</p>\n'
                 '  </footer>\n'
                 '</body>\n'
                 '</html>',
                 '{"home":{"required":["hero_headline","hero_sub","key_strengths"],"optional":["cta_label","featured_services"]},"about":{"required":["company_name","founded","address","representative_name","business_description"],"optional":["corporate_number","capital","employees","history"]},"services":{"required":["services"],"optional":[]},"news":{"required":[],"optional":["news_items"]},"access":{"required":["address","hours"],"optional":["nearest_station","parking","map_embed_note"]},"contact":{"required":["phone","email"],"optional":["form_note","response_time"]}}',
                 '2026-05-08T09:20:00Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DELETE FROM vertex_webya_template WHERE vertex_id = $1',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/law-firm-v1']},
 {'sql': 'DELETE FROM vertex_webya_template WHERE vertex_id = $1',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/accounting-firm-v1']},
 {'sql': 'DELETE FROM vertex_webya_template WHERE vertex_id = $1',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/scrivener-v1']},
 {'sql': 'DELETE FROM vertex_webya_template WHERE vertex_id = $1',
  'parameters': ['at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/company-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
