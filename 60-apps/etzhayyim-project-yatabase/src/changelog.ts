// changelog.ts — public /changelog page.
//
// Hand-curated reverse-chronological list of every shipped phase. Pulled
// out of deps.toml [product.next_phases] and surface tables. Updated by
// hand with each iteration; tighter trust signal than a deps.toml dump.

interface ChangelogEntry {
  date: string;
  phase: string;
  title: string;
  detail: string;
}

const ENTRIES: ChangelogEntry[] = [
  {
    date: "2026-05-11",
    phase: "P25",
    title: "GitHub stargazers scraper — second autonomous lead source",
    detail:
      "Added /api/leads/sources/github + scheduled cron `45 */6 * * *`. Five competitor repos rotate 2/fire. " +
      "Parallel /users/{login} fetches via Promise.all. Authed mode via GITHUB_TOKEN secret pushes budget 60→5000/h. " +
      "First scrape ingested 9 real leads from neo4j + supabase stargazers.",
  },
  {
    date: "2026-05-11",
    phase: "P37",
    title: "OpenAPI 3.1 spec at /openapi.json",
    detail:
      "27 paths, 9 component schemas, BearerAuth security scheme, CORS-enabled. Imports cleanly into Postman / " +
      "Swagger UI / openapi-typescript / openapi-python-client. Linked from /docs.",
  },
  {
    date: "2026-05-11",
    phase: "P36",
    title: "schema.org JSON-LD on landing",
    detail:
      "SoftwareApplication + 5 Offer subtypes (Free/Starter/Developer/Business/Enterprise) + Organization " +
      "(etz hayim, T9007028460042) for Google rich snippets and SEO discovery.",
  },
  {
    date: "2026-05-11",
    phase: "P35",
    title: "/privacy + /terms legal pages",
    detail:
      "Privacy maps each retention column to its statute (法人税法 §126, GDPR Art 30, CCPA, etc.). Terms is " +
      "JP-governed (Tokyo District Court), USD-100 / 12-month-fees liability cap. Linked from landing footer.",
  },
  {
    date: "2026-05-11",
    phase: "P34",
    title: "/robots.txt + /sitemap.xml",
    detail:
      "Allows public marketing surfaces; disallows API + operator paths. Sitemap lists 7 routes daily.",
  },
  {
    date: "2026-05-11",
    phase: "P33",
    title: "/docs API reference",
    detail:
      "Self-contained 18 KB HTML covering Quickstart / Auth / Cypher / SPARQL / Storage / S3 / MCP / XRPC / Plans / " +
      "Privacy / Errors / Compliance. Sticky sidebar + working curl examples.",
  },
  {
    date: "2026-05-11",
    phase: "P32",
    title: "/status + /team public pages",
    detail:
      "/status: live uptime + 7d agent activity from vertex_yata_qa_run + vertex_yata_agent_run. /team: 4-actor " +
      "roster with public DIDs and run counts. Both edge-cached 60 s.",
  },
  {
    date: "2026-05-11",
    phase: "P31",
    title: "/api/leads/sendable — operator's ready-to-fire list",
    detail:
      "GET endpoint returning only leads where `outreach_status='approved' AND contact_email <> '' AND outreach_outbox <> ''`. " +
      "Powers the Studio Leads pane sendable filter.",
  },
  {
    date: "2026-05-11",
    phase: "P30",
    title: "Autonomous enrichment cron",
    detail:
      "Domain enrichment now runs on its own cron `30 */6 * * *`. scheduled() dispatches by event.cron prefix. " +
      "yatabase-deploy.sh updated to preserve the multi-cron trigger config across etzhayyim deploys.",
  },
  {
    date: "2026-05-11",
    phase: "P27",
    title: "Lead enrichment via homepage scrape",
    detail:
      "GET https://{domain}/ + regex extract mailto: + role-prefix emails (info@/hello@/contact@/...) + tech-stack " +
      "hints. Self-identifying UA so site owners can robots.txt-block. RFC 2606 example/test/invalid skip. " +
      "Verified live on supabase.com / hackaday.com / val.town / cyberinsider.com.",
  },
  {
    date: "2026-05-11",
    phase: "P26",
    title: "Studio Leads pane (operator UI)",
    detail:
      "Sidebar entry + admin-key prompt. Lists vertex_lead with status filter (new/drafted/approved/dismissed/sent/sendable). " +
      "Per-row buttons: enrich / approve / dismiss / set email / send. Calls existing admin endpoints over fetch().",
  },
  {
    date: "2026-05-11",
    phase: "P24",
    title: "Send pipeline — dry-run + live",
    detail:
      "POST /api/leads/{vertex_id}/send. Without RESEND_API_KEY: returns dry-run preview {from, to, subject, body}. " +
      "With it: POSTs Resend, flips outbox + lead status='sent'. Same code path either way. Validates lead.outreach_status='approved' + non-empty contact_email + valid outreach_outbox vertex.",
  },
  {
    date: "2026-05-11",
    phase: "P23",
    title: "Stripe webhook plan-flip integration test [DEPRECATED per Charter Rider §2]",
    detail:
      "70-tools/scripts/yatabase-stripe-webhook-test.mjs — [DEPRECATED] synthesized Stripe webhook test. " +
      "Stripe external fiat payment is prohibited per Charter Rider §2. See ADR-2605192115 for USDC donation flow migration.",
  },
  {
    date: "2026-05-11",
    phase: "P22",
    title: "HN Algolia scraper + CF Cron Trigger",
    detail:
      "/api/leads/sources/hn + scheduled() every 6 h. Seven queries (graph database, neo4j, supabase, hasura, " +
      "dgraph, arangodb, firebase migrate). 19-host skip-list filters aggregators. Conservative fit scoring.",
  },
  {
    date: "2026-05-11",
    phase: "P21",
    title: "/api/leads/ingest + nishino lead-drain extension",
    detail:
      "vertex_lead schema. handleLeadIngest is idempotent (skip-if-exists). Operator endpoints: approve / dismiss / " +
      "set contact_email. nishino's third pass drains leads with status='new' into outbox drafts.",
  },
  {
    date: "2026-05-11",
    phase: "P18",
    title: "/welcome landing page",
    detail:
      "Marketing surface at /. Hero pitch, 6-card feature grid, 5-tier pricing table, 30-second curl Quickstart, " +
      "compliance footer. Studio moved to /studio + /embed.",
  },
];

function groupByDay(entries: ChangelogEntry[]): Map<string, ChangelogEntry[]> {
  const m = new Map<string, ChangelogEntry[]>();
  for (const e of entries) {
    const arr = m.get(e.date) ?? [];
    arr.push(e);
    m.set(e.date, arr);
  }
  return m;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function changelogResponse(): Response {
  const grouped = groupByDay(ENTRIES);
  const days = [...grouped.keys()].sort().reverse();
  const totalShipped = ENTRIES.length;

  const dayBlocks = days.map((d) => {
    const items = (grouped.get(d) ?? []).map((e) => `
      <li>
        <span class="phase">${escapeHtml(e.phase)}</span>
        <strong>${escapeHtml(e.title)}</strong>
        <p>${escapeHtml(e.detail)}</p>
      </li>`).join("");
    return `
      <section class="day">
        <h2>${escapeHtml(d)} <span class="count">${grouped.get(d)?.length ?? 0} shipped</span></h2>
        <ul>${items}</ul>
      </section>`;
  }).join("");

  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Changelog — Yatabase</title>
<meta name="description" content="What we shipped on yatabase.etzhayyim.com. Reverse chronological. Each entry maps to a phase ID in deps.toml." />
<style>
  body{margin:0;font:15px/1.65 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:780px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;color:inherit;text-decoration:none}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  main{padding:8px 0}
  h1{font-size:32px;letter-spacing:-.02em;margin:8px 0 4px}
  .lede{font-size:15px;color:#475569;margin:0 0 28px}
  .day{margin:24px 0 32px;padding-top:14px;border-top:1px solid #e2e8f0}
  .day:first-of-type{border-top:0;padding-top:0}
  .day h2{font-size:18px;margin:0 0 14px;display:flex;align-items:baseline;gap:12px}
  .count{font-size:11px;color:#64748b;font-weight:400;text-transform:uppercase;letter-spacing:.05em}
  .day ul{list-style:none;padding:0;margin:0}
  .day li{margin:0 0 16px;padding:14px 16px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;display:grid;grid-template-columns:64px 1fr;gap:8px 12px}
  .phase{display:inline-block;padding:1px 8px;border-radius:6px;background:#0f172a;color:#e2e8f0;font:600 11px ui-monospace,SF Mono,Menlo,monospace;align-self:start;justify-self:start}
  .day li strong{font-size:14px;align-self:start}
  .day li p{grid-column:1/-1;margin:0;font-size:13px;color:#475569;line-height:1.55}
  .summary{background:#f0f9ff;border:1px solid #bae6fd;padding:16px 18px;border-radius:10px;margin:0 0 24px;font-size:14px;color:#0369a1}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
  footer a{color:#0ea5e9}
</style>
</head>
<body>

<header>
  <a class="logo" href="/">y<span>at</span>abase</a>
  <nav>
    <a href="/">Home</a>
    <a href="/docs">Docs</a>
    <a href="/integrations">Integrations</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main style="padding:24px">

<h1>Changelog</h1>
<p class="lede">
  What we shipped, in reverse chronological order. Each entry maps to a phase ID in
  <code>deps.toml [product.next_phases]</code>. Newest first.
</p>

<div class="summary">
  <strong>${totalShipped}</strong> shipped phases tracked here.
  Live status: <a href="/status">/status</a> · Public surfaces: <a href="/_app/meta">/_app/meta</a> ·
  Cron schedule: <code>0 */6 * * *</code> (HN), <code>30 */6 * * *</code> (enrich), <code>45 */6 * * *</code> (GitHub).
</div>

${dayBlocks}

</main>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.etzhayyim.com</a> · <a href="/team">/team</a> · <a href="/.well-known/agent.json">/.well-known/agent.json</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "changelog",
      "cache-control": "public, max-age=300, s-maxage=600",
    },
  });
}
