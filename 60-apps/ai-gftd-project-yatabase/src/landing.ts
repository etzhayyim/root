// landing.ts — public marketing surface for yatabase.etzhayyim.com/.
//
// Deliberately self-contained: no JS, no external CSS, no analytics tags.
// Single Hono response; no auth; no state. The whole page is hot-cacheable
// at the CF edge.
//
// Acts as the canonical homepage. Studio (browser console) lives at
// /studio + /embed; this page links into Studio for logged-in users and
// promotes signup + curl-first onboarding for prospects.

const PRIMARY_USD = { starter: 13, developer: 33, business: 650 };
const FX = 150;

export function landingResponse(): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Yatabase — real-time graph DB + storage</title>
<meta name="description" content="Real-time graph database with integrated S3-style object storage. Cypher, SPARQL, MCP. One bill. BWA-free egress." />
<meta property="og:title" content="Yatabase — real-time graph DB + storage" />
<meta property="og:description" content="Cypher / SPARQL / MCP / S3-compat — one bill. Free tier $0/mo." />
<meta property="og:url" content="https://yatabase.etzhayyim.com/" />
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Yatabase",
  "url": "https://yatabase.etzhayyim.com/",
  "description": "Real-time graph database with integrated S3-style object storage. Cypher, SPARQL, MCP. One bill. AT Protocol native.",
  "applicationCategory": "DeveloperApplication",
  "applicationSubCategory": "Database as a Service",
  "operatingSystem": "Any (HTTPS API)",
  "offers": [
    { "@type": "Offer", "name": "Free",       "price": "0",    "priceCurrency": "USD", "category": "free" },
    { "@type": "Offer", "name": "Starter",    "price": "13",   "priceCurrency": "USD", "category": "subscription" },
    { "@type": "Offer", "name": "Developer",  "price": "33",   "priceCurrency": "USD", "category": "subscription" },
    { "@type": "Offer", "name": "Business",   "price": "650",  "priceCurrency": "USD", "category": "subscription" },
    { "@type": "Offer", "name": "Enterprise", "price": "6700", "priceCurrency": "USD", "category": "subscription", "description": "Floor; sales-negotiated." }
  ],
  "provider": {
    "@type": "Organization",
    "name": "etz hayim",
    "alternateName": ["运営法人", "Operator"],
    "url": "https://yatabase.etzhayyim.com/team",
    "vatID": "T9007028460042",
    "contactPoint": [
      { "@type": "ContactPoint", "contactType": "Privacy",  "email": "privacy@etzhayyim.com" },
      { "@type": "ContactPoint", "contactType": "Legal",    "email": "legal@etzhayyim.com" },
      { "@type": "ContactPoint", "contactType": "Sales",    "email": "sales@etzhayyim.com" }
    ]
  },
  "featureList": [
    "Cypher subset (RisingWave)",
    "SPARQL 1.1 SELECT/CONSTRUCT/ASK",
    "Supabase-shape Storage REST",
    "AWS SigV4 (S3 compat)",
    "MCP JSON-RPC 2.0 tool surface",
    "AT Protocol XRPC pass-through",
    "AT Protocol DID auth",
    "USDC donations on Base L2",
    "適格請求書 invoicing (JP)",
    "CCPA / GDPR / 改正個人情報保護法 endpoints"
  ]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How do I get started with Yatabase?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Run a single curl: curl -X POST https://yatabase.etzhayyim.com/auth/v1/signup. The response contains your sk_live_yata_* API key (shown once), an orgDid, and AWS access keys for the S3-compatible surface. Use the same key on /cypher, /storage, /mcp, and /xrpc."
      }
    },
    {
      "@type": "Question",
      "name": "What does Yatabase cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Free tier is $0/month with 1,000 api_request/day, 5 GB storage, 5 CU-h Cypher. Paid tiers: Starter $13/mo, Developer $33/mo, Business $650/mo. Enterprise starts at $6,700/mo with sales-negotiated SLA. Japan customers receive 適格請求書 (T9007028460042) invoices."
      }
    },
    {
      "@type": "Question",
      "name": "Can my AI agent (Cursor / Claude / LangChain) use Yatabase as a tool?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. /mcp speaks JSON-RPC 2.0 with public initialize/ping/tools-list and authenticated tools/call. Add https://yatabase.etzhayyim.com/mcp to your MCP client config (Cursor, Claude Desktop, Continue.dev) with a Bearer header. See /integrations for paste-ready snippets."
      }
    },
    {
      "@type": "Question",
      "name": "Is Yatabase GDPR / CCPA / 改正個人情報保護法 compliant?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes — per-statute endpoints are documented at /privacy. GET /api/export covers the right to know / portability (CCPA §1798.100, GDPR Art 15+20, 改正個人情報保護法 §33). POST /api/account/delete covers the right to erasure (CCPA §1798.105, GDPR Art 17, 改正個人情報保護法 §34-36). vertex_audit_log keeps GDPR Art 30 records of processing for 90 days."
      }
    },
    {
      "@type": "Question",
      "name": "Where is my data physically stored?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Graph data lives on a per-tenant schema (yata_<sha256(orgDid)[:16]>) in RisingWave Postgres on Vultr (Los Angeles). Object storage is content-addressed on Backblaze B2. Cloudflare handles edge HTTP termination. EU/EEA transfers rely on Standard Contractual Clauses (EU 2021/914)."
      }
    },
    {
      "@type": "Question",
      "name": "What graph operations are supported today?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Cypher subset on RisingWave: MATCH, CREATE, SET, DELETE, edge traversal (a)-[:R]->(b). Forbidden: DETACH DELETE, FOREACH, CALL{}-writes. Deferred: multi-hop, variable-length paths, MERGE, count(), OPTIONAL MATCH, WITH. SPARQL 1.1 SELECT / CONSTRUCT / ASK is also supported. Bolt :7687 is on the roadmap."
      }
    },
    {
      "@type": "Question",
      "name": "Who runs Yatabase?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Operator is etz hayim. Vendor of record (Japan tax invoicing) is Gftd Japan株式会社, qualified-invoice number T9007028460042. The four resident AI actors (chikada, tanaka, nishino, sakamoto) are documented at /team with public DIDs and run counts. Security contact: security@etzhayyim.com (RFC 9116 at /.well-known/security.txt)."
      }
    }
  ]
}
</script>
<style>
  *,*::before,*::after{box-sizing:border-box}
  body{margin:0;font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:980px;margin:0 auto;padding:0 24px}
  header{padding-top:28px;padding-bottom:12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;letter-spacing:-.01em}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  .btn{display:inline-block;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px}
  .btn-primary{background:#0f172a;color:#fff}
  .btn-primary:hover{background:#1e293b}
  .btn-ghost{border:1px solid #cbd5e1;color:#0f172a;background:#fff}
  .btn-ghost:hover{border-color:#0ea5e9;color:#0ea5e9}
  .hero{padding:64px 0 44px;text-align:center}
  .hero h1{font-size:44px;line-height:1.1;letter-spacing:-.02em;margin:0 0 16px}
  .hero h1 em{font-style:normal;background:linear-gradient(90deg,#0ea5e9,#6366f1);-webkit-background-clip:text;background-clip:text;color:transparent}
  .hero p.lede{font-size:18px;color:#475569;max-width:640px;margin:0 auto 28px}
  .cta-row{display:flex;gap:12px;justify-content:center;margin-bottom:28px;flex-wrap:wrap}
  pre.curl{display:inline-block;text-align:left;background:#0f172a;color:#e2e8f0;padding:18px 22px;border-radius:10px;font:13px/1.5 ui-monospace,SF Mono,Menlo,Consolas,monospace;margin:0 auto;max-width:760px;overflow-x:auto}
  pre.curl .c{color:#94a3b8}
  pre.curl .k{color:#7dd3fc}
  pre.curl .s{color:#fcd34d}
  section{padding:48px 0;border-top:1px solid #e2e8f0}
  section h2{font-size:24px;margin:0 0 24px;letter-spacing:-.01em}
  .grid-3{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}
  .card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px}
  .card h3{margin:0 0 6px;font-size:15px}
  .card p{margin:0;color:#475569;font-size:14px}
  .pricing{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}
  .plan{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px}
  .plan.pop{border-color:#0ea5e9;box-shadow:0 0 0 3px rgba(14,165,233,.12)}
  .plan h3{margin:0 0 4px;font-size:16px}
  .plan .price{font-size:28px;font-weight:700;letter-spacing:-.02em;margin:8px 0}
  .plan .price .jpy{display:block;font-size:13px;color:#64748b;font-weight:400}
  .plan ul{padding:0;margin:14px 0 0;list-style:none;font-size:13px;color:#475569}
  .plan li{padding:4px 0;border-bottom:1px dashed #e2e8f0}
  .plan li:last-child{border-bottom:0}
  table.compare{width:100%;border-collapse:collapse;font-size:14px}
  table.compare th,table.compare td{padding:10px 12px;text-align:left;border-bottom:1px solid #e2e8f0}
  table.compare thead th{font-weight:600;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:.06em}
  table.compare tr.us td:first-child{font-weight:600}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
  footer p{margin:6px 0}
  @media (max-width:640px){.hero h1{font-size:32px}.hero p.lede{font-size:16px}}
</style>
</head>
<body>

<header>
  <div class="logo">y<span>at</span>abase</div>
  <nav>
    <a href="/quickstart">Quickstart</a>
    <a href="/docs">Docs</a>
    <a href="/integrations">Integrations</a>
    <a href="/comparison">vs</a>
    <a href="#pricing">Pricing</a>
    <a href="/dashboard">Dashboard</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main>

<section class="hero" style="border-top:0;padding-top:0">
  <h1>Real-time graph DB + storage.<br/><em>One bill. One signup.</em></h1>
  <p class="lede">
    Cypher · SPARQL · MCP · S3-compatible buckets — all on a single account.
    Free tier $0/mo. No egress fee through Cloudflare. AT Protocol native.
  </p>
  <div class="cta-row">
    <a class="btn btn-primary" href="/quickstart">Mint trial key</a>
    <a class="btn btn-ghost" href="/studio">Open Studio</a>
    <a class="btn btn-ghost" href="#try-it">Try it via curl</a>
  </div>

  <pre class="curl" id="try-it"><span class="c"># 1. Sign up (anonymous, mints an API key)</span>
curl -X POST <span class="s">https://yatabase.etzhayyim.com/auth/v1/signup</span>

<span class="c"># 2. Ship your first Cypher query</span>
curl -X POST <span class="s">https://yatabase.etzhayyim.com/cypher</span> \\
  -H <span class="s">'authorization: Bearer sk_live_yata_…'</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">query</span>":"CREATE (n:Demo {name:\\"hello\\"}) RETURN n"}'

<span class="c"># 3. Or talk to it like an MCP tool</span>
curl -X POST <span class="s">https://yatabase.etzhayyim.com/mcp</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">jsonrpc</span>":"2.0","<span class="k">method</span>":"tools/list","<span class="k">id</span>":1}'</pre>
</section>

<section id="features">
  <h2>Why yatabase</h2>
  <div class="grid-3">
    <div class="card"><h3>One bill, no surprises</h3><p>Compute + graph + object storage + egress on the same invoice. No hidden BWA fee. JP-適格請求書 ready.</p></div>
    <div class="card"><h3>Real-time graph</h3><p>RisingWave streaming MV under the hood. Every Cypher write hits a Postgres-compatible row in &lt;100&nbsp;ms.</p></div>
    <div class="card"><h3>S3-compatible storage</h3><p>Supabase-shape REST and AWS SigV4. Public ACL on demand. Backed by B2 dedup.</p></div>
    <div class="card"><h3>MCP native</h3><p>Every surface is also a Model Context Protocol tool. Bring your own LLM agent.</p></div>
    <div class="card"><h3>AT Protocol auth</h3><p>Sign in with did:web / did:plc. Federated identity, BYOI compatible.</p></div>
    <div class="card"><h3>Open API key</h3><p><code>sk_live_yata_*</code> bearer token. Same key works for Cypher, SPARQL, S3, MCP.</p></div>
    <div class="card"><h3>Real graph relationships</h3><p>Not just labeled docs. <code>CREATE (a:Person)-[:FOLLOWS]-&gt;(b)</code> with outgoing + incoming single-hop traversal and WHERE filters (CONTAINS, &gt;=, AND).</p></div>
    <div class="card"><h3>Outbound webhooks</h3><p>POST to your URL on every Cypher mutation. HMAC-signed, label-filterable, per-tenant. Slack / Zapier / your backend.</p></div>
    <div class="card"><h3>Email-based key recovery</h3><p>Anonymous signup but attach an email, click the verification link, recover any time. No support ticket required.</p></div>
  </div>
</section>

<section id="pricing">
  <h2>Pricing — US-first, JPY-secondary</h2>
  <div class="pricing">
    <div class="plan">
      <h3>Free</h3>
      <div class="price">$0<span class="jpy">¥0 / month</span></div>
      <ul><li>1,000 api_request / day</li><li>5 GB storage</li><li>5 CU-h Cypher</li><li>Best for evaluation</li></ul>
    </div>
    <div class="plan pop">
      <h3>Starter</h3>
      <div class="price">$${PRIMARY_USD.starter}<span class="jpy">≈ ¥${(PRIMARY_USD.starter * FX).toLocaleString()} / month</span></div>
      <ul><li>33,333 api_request / day</li><li>50 GB storage</li><li>50 CU-h Cypher</li><li>Solo dev / side project</li></ul>
    </div>
    <div class="plan">
      <h3>Developer</h3>
      <div class="price">$${PRIMARY_USD.developer}<span class="jpy">≈ ¥${(PRIMARY_USD.developer * FX).toLocaleString()} / month</span></div>
      <ul><li>333,333 api_request / day</li><li>500 GB storage</li><li>500 CU-h Cypher</li><li>Production starter</li></ul>
    </div>
    <div class="plan">
      <h3>Business</h3>
      <div class="price">$${PRIMARY_USD.business}<span class="jpy">≈ ¥${(PRIMARY_USD.business * FX).toLocaleString()} / month</span></div>
      <ul><li>33M api_request / day</li><li>5 TB storage</li><li>5,000 CU-h Cypher</li><li>Mid-market</li></ul>
    </div>
    <div class="plan">
      <h3>Enterprise</h3>
      <div class="price">$6,700+<span class="jpy">starting / month</span></div>
      <ul><li>Unlimited usage</li><li>SLA, SSO, multi-region</li><li>Sales-negotiated</li><li><a href="mailto:sales@etzhayyim.com">Contact sales</a></li></ul>
    </div>
  </div>
  <p style="font-size:13px;color:#64748b;margin-top:14px">Upgrade in-product via Studio → Plan (POST /api/donate). USDC donations on Base L2 per Charter Rider §2 — Japan-compliant 適格請求書 included for JP customers (T9007028460042).</p>
</section>

<section id="surfaces">
  <h2>What you get on day 1</h2>
  <table class="compare">
    <thead><tr><th>Surface</th><th>Path</th><th>Status</th></tr></thead>
    <tbody>
      <tr class="us"><td>Cypher (Neo4j subset)</td><td>POST /cypher</td><td>GA</td></tr>
      <tr class="us"><td>SPARQL 1.1</td><td>POST /sparql</td><td>GA</td></tr>
      <tr class="us"><td>Object storage REST</td><td>/storage/v1/object/{bucket}/{key}</td><td>GA</td></tr>
      <tr class="us"><td>S3 SigV4</td><td>/s3/{bucket}/{key}</td><td>GA</td></tr>
      <tr class="us"><td>MCP (JSON-RPC 2.0)</td><td>POST /mcp</td><td>GA</td></tr>
      <tr class="us"><td>XRPC pass-through</td><td>/xrpc/ai.gftd.apps.yata.*</td><td>GA</td></tr>
      <tr class="us"><td>Outbound webhooks</td><td>/api/webhooks (HMAC-signed)</td><td>GA</td></tr>
      <tr class="us"><td>Email key recovery</td><td>/auth/v1/recover + /verify-email</td><td>GA</td></tr>
      <tr class="us"><td>Bolt :7687 (Neo4j driver)</td><td>—</td><td>Roadmap (P11)</td></tr>
      <tr class="us"><td>PostgREST /rest/v1/{table}</td><td>—</td><td>Roadmap (P13)</td></tr>
      <tr class="us"><td>GraphQL /graphql/v1</td><td>—</td><td>Roadmap (P14)</td></tr>
    </tbody>
  </table>
</section>

<section style="text-align:center;background:#0f172a;color:#e2e8f0;border-radius:14px;margin:48px 0;padding:48px 24px">
  <h2 style="color:#fff;margin:0 0 12px">Ready when you are.</h2>
  <p style="color:#cbd5e1;margin:0 0 24px;max-width:560px;margin-left:auto;margin-right:auto">No credit card. Anonymous signup. Your tenant schema auto-provisions on first Cypher call.</p>
  <div class="cta-row" style="margin:0">
    <a class="btn btn-primary" style="background:#0ea5e9" href="/quickstart">Mint trial key</a>
    <a class="btn btn-ghost" style="background:#1e293b;color:#fff;border-color:#334155" href="/studio">Open Studio</a>
  </div>
</section>

</main>

<footer>
  <p><strong>Operator:</strong> etz hayim (運営法人) · <strong>Vendor:</strong> Gftd Japan株式会社</p>
  <p><strong>JP 適格請求書登録番号:</strong> T9007028460042</p>
  <p><strong>Compliance:</strong> CCPA §1798.100/§1798.105 · GDPR Art 17/Art 20/Art 30 · 改正個人情報保護法 §33/§34-36 · 法人税法 §126 · IRS §6001 (7-year retention)</p>
  <p><strong>Legal:</strong> <a href="/privacy" style="color:#0ea5e9">/privacy</a> · <a href="/terms" style="color:#0ea5e9">/terms</a></p>
  <p><strong>Status:</strong> <a href="/docs" style="color:#0ea5e9">/docs</a> · <a href="/integrations" style="color:#0ea5e9">/integrations</a> · <a href="/changelog" style="color:#0ea5e9">/changelog</a> · <a href="/status" style="color:#0ea5e9">/status</a> · <a href="/team" style="color:#0ea5e9">/team</a> · <a href="/.well-known/security.txt" style="color:#0ea5e9">/.well-known/security.txt</a> · <a href="/.well-known/agent.json" style="color:#0ea5e9">/.well-known/agent.json</a></p>
  <p style="margin-top:14px;color:#94a3b8">© 2026 etz hayim. yatabase is an AI Agent — unofficial, not affiliated with the real organizations referenced in MCP discovery responses.</p>
</footer>

</body></html>`;
  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "landing",
      "cache-control": "public, max-age=120, s-maxage=300",
    },
  });
}
