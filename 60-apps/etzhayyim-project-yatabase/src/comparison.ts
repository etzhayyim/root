// comparison.ts — public /comparison page.
//
// Head-to-head against the three real competitors a prospect is
// evaluating against (Supabase, Neo4j AuraDB, Hasura). Be honest:
// where we don't have parity (Bolt, GraphQL), say so and link the
// roadmap phase number. The credibility of the page lives in *not*
// claiming we win every row.
//
// Pricing numbers are public list prices on each competitor's
// pricing page (snapshot date in the table). Update when prices
// move; we don't claim live FX rates.

export function comparisonResponse(): Response {
  const snapshotDate = "2026-05-11";

  // [feature, yatabase, supabase, neo4j-aura-db, hasura]
  const rows: Array<{ feature: string; yata: string; sb: string; neo4j: string; hasura: string; yataWins?: boolean }> = [
    {
      feature: "Free tier monthly price",
      yata: "$0",
      sb: "$0",
      neo4j: "$0 (AuraDB Free, 1 instance only)",
      hasura: "$0 (Hasura Cloud Free)",
    },
    {
      feature: "Starter plan",
      yata: "$13 / mo",
      sb: "$25 / mo (Pro)",
      neo4j: "$65 / mo (AuraDB Professional)",
      hasura: "$99 / mo (Hasura Cloud Standard)",
      yataWins: true,
    },
    {
      feature: "Graph database",
      yata: "✓ Cypher with edges, WHERE (CONTAINS / numeric / AND), incoming + outgoing traversal, SET, DELETE",
      sb: "✗ pgvector + relational; no native graph",
      neo4j: "✓ full Cypher + Bolt (native)",
      hasura: "✗ relational PG + GraphQL projection",
    },
    {
      feature: "Object storage built-in",
      yata: "✓ S3 SigV4 + Supabase REST + B2 backend",
      sb: "✓ Supabase Storage",
      neo4j: "✗ separate service",
      hasura: "✗ separate service",
    },
    {
      feature: "MCP (Model Context Protocol)",
      yata: "✓ native JSON-RPC 2.0 at /mcp; every surface is a tool",
      sb: "✗ no first-party MCP",
      neo4j: "✗ no first-party MCP",
      hasura: "✗ no first-party MCP",
      yataWins: true,
    },
    {
      feature: "OpenAPI 3.1 spec",
      yata: "✓ /openapi.json (35 paths) — typed SDK via `openapi-typescript`",
      sb: "partial (auto-generated from PG)",
      neo4j: "✗ separate REST/Cypher docs",
      hasura: "partial (GraphQL schema is the API surface)",
    },
    {
      feature: "AT Protocol / Bluesky-native auth",
      yata: "✓ did:web / did:plc + ES256 JWT alternative",
      sb: "✗",
      neo4j: "✗",
      hasura: "✗",
      yataWins: true,
    },
    {
      feature: "Anonymous signup",
      yata: "✓ single curl, no email required",
      sb: "✗ email + password",
      neo4j: "✗ email + verification",
      hasura: "✗ email + verification",
      yataWins: true,
    },
    {
      feature: "Email-based key recovery",
      yata: "✓ attach-email → verify (24h) → recover (15min token) → redeem; multi-tenant safe",
      sb: "via account console",
      neo4j: "via account console",
      hasura: "via account console",
    },
    {
      feature: "Outbound webhooks (graph mutations)",
      yata: "✓ HMAC-signed POST on cypher.{create,set,delete,create_edge,delete_edge}; label filter; 10/tenant",
      sb: "✓ Postgres webhooks (DB triggers)",
      neo4j: "✗",
      hasura: "✓ event triggers",
    },
    {
      feature: "JP-適格請求書 invoicing",
      yata: "✓ T9007028460042 (etz hayim)",
      sb: "✗",
      neo4j: "✗",
      hasura: "✗",
      yataWins: true,
    },
    {
      feature: "Bolt :7687 (native Neo4j driver)",
      yata: "✗ roadmap P11",
      sb: "—",
      neo4j: "✓ canonical",
      hasura: "—",
    },
    {
      feature: "GraphQL surface",
      yata: "✗ roadmap P14",
      sb: "✓ via PostgREST + GraphQL Mesh",
      neo4j: "partial (community-maintained)",
      hasura: "✓ canonical",
    },
    {
      feature: "Realtime subscriptions (WebSocket)",
      yata: "✗ roadmap P12",
      sb: "✓ Postgres CDC",
      neo4j: "✗",
      hasura: "✓ GraphQL subscriptions",
    },
    {
      feature: "Multi-region",
      yata: "✗ single-region (Vultr LAX); roadmap P16",
      sb: "✓ many regions",
      neo4j: "✓ many regions",
      hasura: "✓ many regions",
    },
    {
      feature: "SLA",
      yata: "99.5% target on paid (non-financial credit). Enterprise = negotiated.",
      sb: "99.9% (Team+)",
      neo4j: "99.95% (AuraDB Professional)",
      hasura: "99.95% (Standard+)",
    },
    {
      feature: "Data location (default)",
      yata: "US (Los Angeles — Vultr / B2 / Cloudflare)",
      sb: "user-chosen (AWS / Fly.io regions)",
      neo4j: "user-chosen (AWS / GCP / Azure)",
      hasura: "user-chosen (AWS regions)",
    },
    {
      feature: "GDPR / CCPA / 改正個人情報保護法 endpoints",
      yata: "✓ /api/export + /api/account/delete; each retention window mapped to a specific statute in /privacy",
      sb: "✓ DPA + console deletion",
      neo4j: "✓ DPA",
      hasura: "✓ DPA",
    },
    {
      feature: "Source code visibility",
      yata: "Closed but operator transparency via /team + /changelog",
      sb: "✓ open source (Apache-2.0)",
      neo4j: "Community Edition open (GPLv3); cloud is closed",
      hasura: "Engine open (Apache-2.0); cloud is closed",
    },
    {
      feature: "Operated by AI agents (with public DIDs)",
      yata: "✓ 4 named actors (chikada / tanaka / nishino / sakamoto)",
      sb: "✗",
      neo4j: "✗",
      hasura: "✗",
      yataWins: true,
    },
  ];

  const tableRows = rows.map((r) => `
    <tr${r.yataWins ? ' class="win"' : ""}>
      <td><strong>${esc(r.feature)}</strong></td>
      <td>${esc(r.yata)}</td>
      <td>${esc(r.sb)}</td>
      <td>${esc(r.neo4j)}</td>
      <td>${esc(r.hasura)}</td>
    </tr>`).join("");

  function esc(s: string): string {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Comparison — Yatabase vs Supabase / Neo4j AuraDB / Hasura</title>
<meta name="description" content="Honest head-to-head comparison between Yatabase, Supabase, Neo4j AuraDB, and Hasura. Pricing, graph DB, storage, MCP, multi-region, SLA, compliance." />
<style>
  body{margin:0;font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:1100px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;color:inherit;text-decoration:none}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  main{padding:8px 24px}
  h1{font-size:32px;letter-spacing:-.02em;margin:8px 0 4px}
  p.lede{font-size:17px;color:#475569;max-width:760px;margin:0 0 24px}
  .panel{background:#fef9c3;border:1px solid #fcd34d;padding:12px 16px;border-radius:8px;font-size:14px;color:#92400e;margin:0 0 18px}
  table{width:100%;border-collapse:collapse;font-size:13.5px;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05)}
  th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #e2e8f0;vertical-align:top}
  th{font-weight:600;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:.05em;background:#f8fafc}
  thead th:first-child{width:240px}
  tbody td:first-child{background:#f8fafc;font-weight:500;width:200px;font-size:13.5px}
  tbody td:nth-child(2){background:#fef9c3}
  tr.win td:nth-child(2){background:#dcfce7;border-left:3px solid #16a34a}
  tr:last-child td{border-bottom:0}
  .badge-yata{display:inline-block;background:#0f172a;color:#fcd34d;padding:1px 8px;border-radius:4px;font:11px ui-monospace;font-weight:600}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
  footer a{color:#0ea5e9}
  @media (max-width:880px){
    table{font-size:12px}
    thead th:first-child,tbody td:first-child{width:auto}
  }
</style>
</head>
<body>

<header>
  <a class="logo" href="/">y<span>at</span>abase</a>
  <nav>
    <a href="/">Home</a>
    <a href="/docs">Docs</a>
    <a href="/quickstart">Quickstart</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main>

<h1>Yatabase vs Supabase / Neo4j AuraDB / Hasura</h1>
<p class="lede">
  Honest head-to-head. Where we win, we say so. Where we don't have parity yet,
  we link the roadmap phase. Snapshot: <strong>${snapshotDate}</strong>. List prices from each
  vendor's public pricing page; update when they move.
</p>

<div class="panel">
  <strong>How to read this:</strong> the <span class="badge-yata">yatabase</span> column is highlighted
  in yellow. Rows where we have a clear, opinionated advantage are marked with a green border.
  Rows where competitors have parity or lead are listed without judgement.
</div>

<table>
  <thead>
    <tr>
      <th>Feature</th>
      <th>Yatabase</th>
      <th>Supabase</th>
      <th>Neo4j AuraDB</th>
      <th>Hasura</th>
    </tr>
  </thead>
  <tbody>
${tableRows}
  </tbody>
</table>

<h2 style="font-size:22px;margin:36px 0 8px">When to pick each</h2>
<p style="font-size:14px;color:#475569">
  <strong>Yatabase</strong> — you want a real graph database + S3 storage + MCP on a single bill,
  you're building an AI-native product, or you need 適格請求書 invoicing in Japan. Pick this
  when single-vendor simplicity matters more than feature breadth.
</p>
<p style="font-size:14px;color:#475569">
  <strong>Supabase</strong> — you need Postgres-first with a polished console, mature realtime, and
  many regions. Pick this when you don't need a native graph layer.
</p>
<p style="font-size:14px;color:#475569">
  <strong>Neo4j AuraDB</strong> — you need full-fat Cypher with Bolt drivers and battle-tested
  graph operations. Pick this when graph is your primary surface and you're willing to glue
  storage / auth / billing separately.
</p>
<p style="font-size:14px;color:#475569">
  <strong>Hasura</strong> — you want GraphQL-as-the-API over Postgres. Pick this when your
  frontend stack is GraphQL-native and you don't need a graph database.
</p>

<h2 style="font-size:22px;margin:36px 0 8px">Closing the parity gaps</h2>
<p style="font-size:14px;color:#475569">
  Honest roadmap of what we don't have yet (from <a href="/changelog">/changelog</a> and
  <a href="/docs">/docs</a>):
</p>
<ul style="font-size:14px;color:#475569">
  <li><strong>P11</strong> — Bolt :7687 protocol gateway so any Neo4j driver works against us.</li>
  <li><strong>P12</strong> — Realtime WS subscriptions (Phoenix channel compat).</li>
  <li><strong>P13</strong> — PostgREST <code>/rest/v1/{table}</code> auto-CRUD.</li>
  <li><strong>P14</strong> — GraphQL <code>/graphql/v1</code> with schema introspection.</li>
  <li><strong>P16</strong> — Multi-region (US east-1 / NRT / AMS).</li>
</ul>

<p style="font-size:14px;color:#475569;margin-top:32px">
  Have a comparison we got wrong? Email <a href="mailto:sales@etzhayyim.com">sales@etzhayyim.com</a> with the
  vendor page link and we'll fix it in the next deploy.
</p>

</main>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.etzhayyim.com</a> · <a href="/docs">/docs</a> · <a href="/changelog">/changelog</a> · <a href="/.well-known/agent.json">/.well-known/agent.json</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "comparison",
      "cache-control": "public, max-age=600, s-maxage=3600",
    },
  });
}
