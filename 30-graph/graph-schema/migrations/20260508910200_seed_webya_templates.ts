import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * webya.etzhayyim.com テンプレート初期データ (4 profession_kind).
 *
 * html_skeleton: Jinja2 テンプレート。slot は {{ slot_name }} 記法。
 * slot_schema_json: 各ページの必須/任意 slot 定義 (JSON 文字列)。
 * pages_json: ページ slug 一覧 (JSON 配列)。
 */

const createdAt = "2026-05-08T09:20:00Z";

const LAW_FIRM_PAGES = JSON.stringify([
  "home", "about", "practice_areas", "attorneys", "fee", "access", "contact",
]);

const LAW_FIRM_SLOT_SCHEMA = JSON.stringify({
  home: {
    required: ["hero_headline", "hero_sub", "cta_label"],
    optional: ["key_strengths"],
  },
  about: {
    required: [
      "history", "philosophy", "bar_association",
      "bar_registration_number", "representative_attorney",
    ],
    optional: ["awards", "team_intro"],
  },
  practice_areas: {
    required: ["areas"],
    optional: [],
  },
  attorneys: {
    required: ["attorneys"],
    optional: [],
  },
  fee: {
    required: ["fee_table", "disclaimer"],
    optional: ["free_consultation_note"],
  },
  access: {
    required: ["address", "hours"],
    optional: ["nearest_station", "parking"],
  },
  contact: {
    required: ["phone", "email"],
    optional: ["form_note", "response_time"],
  },
});

// Minimal Jinja2 skeleton — production would have full HTML with CSS.
// Slots rendered by Jinja2 `render_page_html()` in webya.py.
const LAW_FIRM_HTML_SKELETON = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }} | {{ client_name }}</title>
  <meta name="description" content="{{ meta_description }}">
  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% endif %}
  <link rel="stylesheet" href="/assets/law-firm-v1.css">
</head>
<body class="law-firm" data-profession="law_firm">
  <header>
    <nav><a href="/" class="brand">{{ client_name }}</a>
    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label }}</a></li>{% endfor %}</ul>
    </nav>
  </header>
  <main>{% block content %}{% endblock %}</main>
  <footer>
    <p>{{ client_name }} | {{ bar_association }} 登録番号: {{ bar_registration_number }}</p>
    <p>{{ address }} | TEL: {{ phone }}</p>
  </footer>
</body>
</html>`;

// ─────────────────────────────────────────────────────────────────────────────

const ACCOUNTING_FIRM_PAGES = JSON.stringify([
  "home", "about", "services", "staff", "fee_guide", "access", "contact",
]);

const ACCOUNTING_FIRM_SLOT_SCHEMA = JSON.stringify({
  home: {
    required: ["hero_headline", "hero_sub", "key_services"],
    optional: ["cta_label"],
  },
  about: {
    required: [
      "history", "philosophy",
      "tax_attorney_association", "tax_attorney_registration_number",
    ],
    optional: ["awards", "representative_profile"],
  },
  services: {
    required: ["services"],
    optional: [],
  },
  staff: {
    required: ["staff"],
    optional: [],
  },
  fee_guide: {
    required: ["fee_table"],
    optional: ["consultation_note"],
  },
  access: {
    required: ["address", "hours"],
    optional: ["nearest_station", "parking"],
  },
  contact: {
    required: ["phone", "email"],
    optional: ["form_note", "response_time"],
  },
});

const ACCOUNTING_FIRM_HTML_SKELETON = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }} | {{ client_name }}</title>
  <meta name="description" content="{{ meta_description }}">
  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% endif %}
  <link rel="stylesheet" href="/assets/accounting-firm-v1.css">
</head>
<body class="accounting-firm" data-profession="accounting_firm">
  <header>
    <nav><a href="/" class="brand">{{ client_name }}</a>
    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label }}</a></li>{% endfor %}</ul>
    </nav>
  </header>
  <main>{% block content %}{% endblock %}</main>
  <footer>
    <p>{{ client_name }} | {{ tax_attorney_association }} 登録番号: {{ tax_attorney_registration_number }}</p>
    <p>{{ address }} | TEL: {{ phone }}</p>
  </footer>
</body>
</html>`;

// ─────────────────────────────────────────────────────────────────────────────

const SCRIVENER_PAGES = JSON.stringify([
  "home", "about", "services", "fee", "access", "contact",
]);

const SCRIVENER_SLOT_SCHEMA = JSON.stringify({
  home: {
    required: ["hero_headline", "hero_sub", "key_services"],
    optional: ["cta_label"],
  },
  about: {
    required: ["history", "philosophy", "scrivener_association", "scrivener_registration_number"],
    optional: ["judicial_cert_number", "representative_profile"],
  },
  services: {
    required: ["services"],
    optional: [],
  },
  fee: {
    required: ["fee_table"],
    optional: ["consultation_note", "disclaimer"],
  },
  access: {
    required: ["address", "hours"],
    optional: ["nearest_station"],
  },
  contact: {
    required: ["phone", "email"],
    optional: ["form_note"],
  },
});

const SCRIVENER_HTML_SKELETON = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }} | {{ client_name }}</title>
  <meta name="description" content="{{ meta_description }}">
  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% endif %}
  <link rel="stylesheet" href="/assets/scrivener-v1.css">
</head>
<body class="scrivener" data-profession="{{ profession_kind }}">
  <header>
    <nav><a href="/" class="brand">{{ client_name }}</a>
    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label }}</a></li>{% endfor %}</ul>
    </nav>
  </header>
  <main>{% block content %}{% endblock %}</main>
  <footer>
    <p>{{ client_name }} | {{ scrivener_association }} 登録番号: {{ scrivener_registration_number }}</p>
    <p>{{ address }} | TEL: {{ phone }}</p>
  </footer>
</body>
</html>`;

// ─────────────────────────────────────────────────────────────────────────────

const COMPANY_PAGES = JSON.stringify([
  "home", "about", "services", "news", "access", "contact",
]);

const COMPANY_SLOT_SCHEMA = JSON.stringify({
  home: {
    required: ["hero_headline", "hero_sub", "key_strengths"],
    optional: ["cta_label", "featured_services"],
  },
  about: {
    required: [
      "company_name", "founded", "address",
      "representative_name", "business_description",
    ],
    optional: ["corporate_number", "capital", "employees", "history"],
  },
  services: {
    required: ["services"],
    optional: [],
  },
  news: {
    required: [],
    optional: ["news_items"],
  },
  access: {
    required: ["address", "hours"],
    optional: ["nearest_station", "parking", "map_embed_note"],
  },
  contact: {
    required: ["phone", "email"],
    optional: ["form_note", "response_time"],
  },
});

const COMPANY_HTML_SKELETON = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }} | {{ client_name }}</title>
  <meta name="description" content="{{ meta_description }}">
  {% if json_ld %}<script type="application/ld+json">{{ json_ld }}</script>{% endif %}
  <link rel="stylesheet" href="/assets/company-v1.css">
</head>
<body class="company" data-profession="general_company">
  <header>
    <nav><a href="/" class="brand">{{ client_name }}</a>
    <ul>{% for slug, label in nav_items %}<li><a href="/{{ slug }}">{{ label }}</a></li>{% endfor %}</ul>
    </nav>
  </header>
  <main>{% block content %}{% endblock %}</main>
  <footer>
    <p>{{ client_name }}{% if corporate_number %} | 法人番号: {{ corporate_number }}{% endif %}</p>
    <p>{{ address }} | TEL: {{ phone }}</p>
  </footer>
</body>
</html>`;

// ─────────────────────────────────────────────────────────────────────────────

type TemplateRow = {
  vertexId: string;
  templateId: string;
  professionKind: string;
  pagesJson: string;
  htmlSkeleton: string;
  slotSchemaJson: string;
};

const templates: TemplateRow[] = [
  {
    vertexId: "at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/law-firm-v1",
    templateId: "template_law_firm_v1",
    professionKind: "law_firm",
    pagesJson: LAW_FIRM_PAGES,
    htmlSkeleton: LAW_FIRM_HTML_SKELETON,
    slotSchemaJson: LAW_FIRM_SLOT_SCHEMA,
  },
  {
    vertexId: "at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/accounting-firm-v1",
    templateId: "template_accounting_firm_v1",
    professionKind: "accounting_firm",
    pagesJson: ACCOUNTING_FIRM_PAGES,
    htmlSkeleton: ACCOUNTING_FIRM_HTML_SKELETON,
    slotSchemaJson: ACCOUNTING_FIRM_SLOT_SCHEMA,
  },
  {
    vertexId: "at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/scrivener-v1",
    templateId: "template_scrivener_v1",
    professionKind: "judicial_scrivener",
    pagesJson: SCRIVENER_PAGES,
    htmlSkeleton: SCRIVENER_HTML_SKELETON,
    slotSchemaJson: SCRIVENER_SLOT_SCHEMA,
  },
  {
    vertexId: "at://did:web:webya.etzhayyim.com/com.etzhayyim.apps.webya.template/company-v1",
    templateId: "template_company_v1",
    professionKind: "general_company",
    pagesJson: COMPANY_PAGES,
    htmlSkeleton: COMPANY_HTML_SKELETON,
    slotSchemaJson: COMPANY_SLOT_SCHEMA,
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const t of templates) {
    await sql`
      INSERT INTO vertex_webya_template
        (vertex_id, template_id, profession_kind, pages_json,
         html_skeleton, slot_schema_json, version, active, created_at)
      VALUES (
        ${t.vertexId}, ${t.templateId}, ${t.professionKind}, ${t.pagesJson},
        ${t.htmlSkeleton}, ${t.slotSchemaJson}, 1, TRUE, ${createdAt}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of templates) {
    await sql`DELETE FROM vertex_webya_template WHERE vertex_id = ${t.vertexId}`.execute(db);
  }
}
