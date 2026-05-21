// docs.ts — public API reference at /docs.
//
// Self-contained HTML, no external assets, edge-cacheable. Walks a
// prospect from signup → first request to every public surface
// (Cypher / Storage / S3 / MCP / XRPC / Billing / Data-rights).
//
// Every command is copy-pastable and idempotent. Pricing and limits
// match `[product.pricing]` in deps.toml; if those change, this file
// must be re-rendered.

export function docsResponse(): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Docs — Yatabase</title>
<meta name="description" content="API reference for yatabase.gftd.ai — graph DB + S3-style storage + MCP. Cypher, SPARQL, S3, MCP, XRPC, billing, data rights." />
<meta property="og:title" content="Yatabase API reference" />
<meta property="og:description" content="Cypher / SPARQL / S3 / MCP — copy-pastable curl for every surface." />
<style>
  body{margin:0;font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:980px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;color:inherit;text-decoration:none}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  main{display:grid;grid-template-columns:240px 1fr;gap:32px;padding-top:8px}
  aside{position:sticky;top:8px;align-self:flex-start;font-size:13px;border-right:1px solid #e2e8f0;padding-right:18px;max-height:calc(100vh - 32px);overflow-y:auto}
  aside h4{margin:18px 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#64748b}
  aside a{display:block;padding:3px 0;color:#334155;text-decoration:none}
  aside a:hover{color:#0ea5e9}
  article{min-width:0}
  article h1{font-size:32px;letter-spacing:-.02em;margin:8px 0 12px}
  article h2{font-size:22px;letter-spacing:-.01em;margin:36px 0 8px;padding-top:10px;border-top:1px solid #e2e8f0}
  article h2:first-of-type{border-top:0;padding-top:0}
  article h3{font-size:16px;margin:20px 0 6px}
  article p{margin:8px 0}
  article p.lede{font-size:17px;color:#475569;margin-bottom:24px}
  article code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:13px}
  article pre{background:#0f172a;color:#e2e8f0;padding:14px 18px;border-radius:8px;font:13px/1.55 ui-monospace,SF Mono,Menlo,Consolas,monospace;overflow-x:auto;margin:10px 0}
  article pre .c{color:#94a3b8}
  article pre .k{color:#7dd3fc}
  article pre .s{color:#fcd34d}
  article table{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0 16px;background:#fff;border-radius:8px;overflow:hidden}
  article th,article td{padding:8px 12px;text-align:left;border-bottom:1px solid #e2e8f0}
  article th{font-weight:600;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:.05em;background:#f8fafc}
  article tr:last-child td{border-bottom:0}
  article ul{padding-left:20px;margin:8px 0}
  article li{margin:3px 0}
  .pill{display:inline-block;padding:1px 8px;font-size:11px;border-radius:10px;font-weight:600;background:#dbeafe;color:#1e40af}
  .pill.warn{background:#fef3c7;color:#92400e}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
  footer a{color:#0ea5e9;text-decoration:none}
  @media (max-width:780px){
    main{grid-template-columns:1fr}
    aside{position:static;border-right:0;border-bottom:1px solid #e2e8f0;padding:0 0 12px}
  }
</style>
</head>
<body>

<header>
  <a class="logo" href="/">y<span>at</span>abase</a>
  <nav>
    <a href="/">Home</a>
    <a href="/studio">Studio</a>
    <a href="/team">Team</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main>

<aside>
  <h4>Get started</h4>
  <a href="#quickstart">Quickstart</a>
  <a href="#auth">Auth</a>
  <h4>APIs</h4>
  <a href="#cypher">Cypher (graph)</a>
  <a href="#sparql">SPARQL</a>
  <a href="#storage">Storage REST</a>
  <a href="#s3">S3 SigV4</a>
  <a href="#mcp">MCP (JSON-RPC)</a>
  <a href="#xrpc">XRPC</a>
  <h4>Account</h4>
  <a href="#plans">Plans &amp; quotas</a>
  <a href="#upgrade">Upgrade</a>
  <a href="#members">Members</a>
  <a href="#webhooks">Webhooks</a>
  <a href="#privacy">Data rights</a>
  <h4>Reference</h4>
  <a href="#errors">Errors</a>
  <a href="#observability">Observability</a>
  <a href="#compliance">Compliance</a>
</aside>

<article>

<h1>Yatabase API reference</h1>
<p class="lede">
  Single-host BaaS combining a real-time graph database (Cypher / SPARQL),
  S3-style object storage, an MCP tool surface, and AT Protocol-native auth.
  Every section below is copy-pastable curl that targets <code>https://yatabase.gftd.ai</code>.
</p>
<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:14px 18px;margin:18px 0;font-size:14px">
  <strong style="color:#0369a1">Machine-readable spec:</strong>
  <a href="/openapi.json">/openapi.json</a> (OpenAPI 3.1).
  Import into Postman / Swagger UI, or generate typed clients:
  <pre style="margin-top:8px"><span class="c"># TypeScript types (openapi-typescript)</span>
npx openapi-typescript <span class="s">https://yatabase.gftd.ai/openapi.json</span> -o yatabase.d.ts

<span class="c"># Generate a Python client (openapi-python-client)</span>
openapi-python-client generate --url <span class="s">https://yatabase.gftd.ai/openapi.json</span></pre>
</div>

<h2 id="quickstart">Quickstart</h2>
<p>From zero to first row in 30 seconds:</p>
<pre><span class="c"># 1. Sign up — anonymous mint, returns sk_live_yata_*</span>
SIGNUP=$(curl -sS -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/signup</span>)
KEY=$(echo "$SIGNUP" | python3 -c <span class="s">'import sys,json;print(json.load(sys.stdin)["apiKey"])'</span>)
echo "$KEY"

<span class="c"># 2. Create a vertex</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/cypher</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">query</span>":"CREATE (n:Demo {name:\\"hello\\"}) RETURN n"}'

<span class="c"># 3. Query it back</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/cypher</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">query</span>":"MATCH (n:Demo) RETURN n.name LIMIT 10"}'</pre>
<p>The signup response also contains <code>orgDid</code> (e.g. <code>did:web:t-xxxxx.yata-tenant.gftd.ai</code>),
   a fresh AWS access-key pair, and an <code>emailStatus</code> field if you passed <code>{email, name}</code>.</p>

<h2 id="auth">Auth</h2>
<p>Three accepted token shapes on the <code>Authorization</code> header:</p>
<table>
  <thead><tr><th>Token</th><th>Mints via</th><th>Use</th></tr></thead>
  <tbody>
    <tr><td><code>Bearer sk_live_yata_*</code></td><td>POST <code>/auth/v1/signup</code></td><td>Default. Per-tenant scope.</td></tr>
    <tr><td><code>Bearer sk_live_*</code></td><td><code>ai.gftd.auth.createApiKey</code></td><td>Cross-product key.</td></tr>
    <tr><td>AT Protocol JWT</td><td><code>com.atproto.server.getSession</code></td><td>For atproto-native clients.</td></tr>
  </tbody>
</table>
<p>All authenticated calls also accept <code>X-Active-DID</code> to disambiguate when the caller controls multiple path-based DIDs.</p>

<h2 id="cypher">Cypher (graph)</h2>
<p>POST <code>/cypher</code> — Neo4j HTTP-shape compatible subset on RisingWave.</p>
<p><strong>Supported:</strong></p>
<ul>
  <li><code>MATCH (n:Label) [WHERE prop OP val [(AND|OR) ...]] RETURN n[.prop] [AS alias] [, ...]</code></li>
  <li><code>[ORDER BY n.prop ASC|DESC] [SKIP N] [LIMIT N]</code></li>
  <li><code>CREATE (n:Label {k: v, ...}) [RETURN ...]</code></li>
  <li><code>MATCH (n:Label {pk: v}) SET n.prop = expr [, ...]</code></li>
  <li><code>MATCH (n:Label {pk: v}) DELETE n</code></li>
  <li><code>MATCH (a:L1)-[:R]-&gt;(b:L2) [WHERE ...] RETURN ...</code></li>
  <li><code>MATCH (a:L1{pk:v}),(b:L2{pk:v}) CREATE (a)-[:R]-&gt;(b)</code></li>
</ul>
<p><strong>Forbidden at the edge:</strong> <code>DETACH DELETE</code>, <code>FOREACH</code>, <code>CALL { ... write ... }</code>.</p>
<p><strong>Deferred:</strong> multi-hop, variable-length path, <code>MERGE</code>, <code>count()</code>/<code>collect()</code>, <code>OPTIONAL MATCH</code>, <code>WITH</code>.</p>

<pre><span class="c"># Edge traversal</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/cypher</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">query</span>":"MATCH (a:Person)-[:KNOWS]-&gt;(b:Person) RETURN a.name, b.name LIMIT 25"}'</pre>

<p>Response shape (Neo4j HTTP API compatible):</p>
<pre>{
  "<span class="k">results</span>": [{ "<span class="k">columns</span>": ["a.name","b.name"], "<span class="k">data</span>": [["alice","bob"]] }],
  "<span class="k">errors</span>": []
}</pre>

<h2 id="sparql">SPARQL</h2>
<p>POST <code>/sparql</code> — SPARQL 1.1 SELECT / CONSTRUCT / ASK on the same graph.</p>
<pre>curl -X POST <span class="s">https://yatabase.gftd.ai/sparql</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/sparql-query'</span> \\
  --data '<span class="k">SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10</span>'</pre>

<h2 id="storage">Storage REST (Supabase shape)</h2>
<p>S3-compatible blob store. PUT/GET/HEAD/DELETE on <code>/storage/v1/object/{bucket}/{key}</code>.</p>
<pre><span class="c"># Upload</span>
curl -X PUT --data-binary @photo.jpg \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  <span class="s">https://yatabase.gftd.ai/storage/v1/object/my-bucket/photo.jpg</span>

<span class="c"># List bucket</span>
curl -H <span class="s">"authorization: Bearer $KEY"</span> \\
  <span class="s">https://yatabase.gftd.ai/storage/v1/object/list/my-bucket</span>

<span class="c"># Public download (only if bucket public_read=true AND ACL grants it)</span>
curl <span class="s">https://yatabase.gftd.ai/storage/v1/object/public/my-bucket/photo.jpg</span>

<span class="c"># Presigned URL</span>
curl -X POST -H <span class="s">"authorization: Bearer $KEY"</span> \\
  <span class="s">https://yatabase.gftd.ai/storage/v1/object/sign/my-bucket/photo.jpg</span></pre>

<h2 id="s3">S3 SigV4 compat</h2>
<p>Same blobs, AWS SigV4 wire format. Use the <code>awsAccessKeyId</code> + <code>awsSecretAccessKey</code> returned by <code>/auth/v1/signup</code>.</p>
<pre>aws --endpoint-url <span class="s">https://yatabase.gftd.ai/s3</span> \\
  s3 cp photo.jpg s3://my-bucket/photo.jpg</pre>

<h2 id="mcp">MCP (JSON-RPC 2.0)</h2>
<p>Every yatabase surface is also an MCP tool. POST <code>/mcp</code>.</p>
<p><code>initialize</code> / <code>ping</code> / <code>tools/list</code> / <code>resources/list</code> / <code>prompts/list</code> are public.
   <code>tools/call</code> and <code>resources/read</code> require auth.</p>
<pre><span class="c"># List tools (public)</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/mcp</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">jsonrpc</span>":"2.0","<span class="k">method</span>":"tools/list","<span class="k">id</span>":1}'

<span class="c"># Call yata.graph.cypher</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/mcp</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">jsonrpc</span>":"2.0","<span class="k">method</span>":"tools/call","<span class="k">params</span>":{"<span class="k">name</span>":"yata.graph.cypher","<span class="k">arguments</span>":{"<span class="k">query</span>":"MATCH (n) RETURN n LIMIT 5"}},"<span class="k">id</span>":2}'</pre>
<p>Discovery doc: <a href="/.well-known/mcp.json">/.well-known/mcp.json</a>.</p>

<h2 id="xrpc">XRPC pass-through</h2>
<p>Native AT Protocol XRPC for <code>ai.gftd.apps.yata.*</code> and <code>ai.gftd.apps.billing.*</code>.</p>
<pre>curl -X POST <span class="s">https://yatabase.gftd.ai/xrpc/ai.gftd.apps.yata.runCypher</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">query</span>":"MATCH (n:Demo) RETURN n LIMIT 10"}'</pre>

<h2 id="plans">Plans &amp; quotas</h2>
<p>USD-primary pricing, JPY-secondary (FX 150 JPY/USD).</p>
<table>
  <thead><tr><th>Plan</th><th>USD/mo</th><th>JPY/mo</th><th>API req / day</th><th>Storage</th><th>Cypher CU-h / day</th></tr></thead>
  <tbody>
    <tr><td><strong>Free</strong></td><td>$0</td><td>¥0</td><td>1,000</td><td>5 GB</td><td>5</td></tr>
    <tr><td><strong>Starter</strong></td><td>$13</td><td>¥1,950</td><td>33,333</td><td>50 GB</td><td>50</td></tr>
    <tr><td><strong>Developer</strong></td><td>$33</td><td>¥4,950</td><td>333,333</td><td>500 GB</td><td>500</td></tr>
    <tr><td><strong>Business</strong></td><td>$650</td><td>¥97,500</td><td>33M</td><td>5 TB</td><td>5,000</td></tr>
    <tr><td><strong>Enterprise</strong></td><td>$6,700+</td><td>¥1.005M+</td><td>unlimited</td><td>unlimited</td><td>unlimited</td></tr>
  </tbody>
</table>
<p>Quota check is per-day, sums today's <code>api_request</code> billing events. Hit 429 with <code>Retry-After</code> when exceeded.</p>
<p>Read your usage:</p>
<pre>curl -H <span class="s">"authorization: Bearer $KEY"</span> <span class="s">https://yatabase.gftd.ai/api/usage</span>
curl -H <span class="s">"authorization: Bearer $KEY"</span> <span class="s">https://yatabase.gftd.ai/api/plan</span></pre>

<h2 id="upgrade">Upgrade</h2>
<pre>curl -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/upgrade</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">plan</span>":"starter"}'</pre>
<p>Returns <code>{checkoutUrl, sessionId}</code> when Stripe is wired (live since 2026-05-10).
   Open <code>checkoutUrl</code> to complete payment. Stripe webhook then flips the plan tier
   inside ~40 s of payment confirmation.</p>

<h3>Customer portal (change card, cancel, view invoices)</h3>
<pre>curl -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/portal</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -d '{}'</pre>
<p>Returns <code>{portalUrl}</code> — a Stripe-hosted page where customers self-serve
   billing (update card, cancel subscription, download past invoices). Requires the
   org has completed at least one Checkout (400 <code>NoStripeCustomer</code> on free).</p>

<h2 id="recovery">Key recovery (lost your API key?)</h2>
<p>Anonymous signup is convenient but losing the key would normally orphan the tenant.
   Attach a recovery email <em>before</em> you need it. Attaching emails a 24-hour
   verification link — <strong>you must click it</strong> before recovery works (this
   prevents an attacker from attaching a victim's email and abusing yatabase to send
   them spam-looking "recovery" notices):</p>
<pre><span class="c"># 1a. Attach an email while you still have the key (emails a verify link)</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/attach-email</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -d '{"<span class="k">email</span>":"you@example.com"}'

<span class="c"># 1b. Click the verification link in your inbox. The link calls:</span>
<span class="c">#     GET /auth/v1/verify-email?token=...   (24-hour TTL, single-use)</span>
<span class="c">#     Confirm with: curl https://yatabase.gftd.ai/auth/v1/whoami -H "authorization: Bearer $KEY"</span>
<span class="c">#     attachedEmailVerified should now be true.</span>

<span class="c"># 2. Later, if you lose the key, anyone can request a recovery link</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/recover</span> \\
  -d '{"<span class="k">email</span>":"you@example.com"}'
<span class="c"># Always returns 200 (no enumeration leak). If the email matches a</span>
<span class="c"># tenant, a recovery link is sent. Link contains a 48-hex token with</span>
<span class="c"># a 15-minute TTL.</span>

<span class="c"># 3. Click the link → it posts the token to /auth/v1/redeem and</span>
<span class="c">#    returns a brand-new API key for the matching org.</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/redeem</span> \\
  -d '{"<span class="k">token</span>":"...48 hex chars from the link..."}'</pre>
<p>Existing keys remain valid after recovery — recovery is additive, not replacement.
   Revoke the lost key separately via <code>/auth/v1/revoke</code> once the new key is in hand.</p>

<h2 id="whoami">Who am I?</h2>
<pre>curl -H <span class="s">"authorization: Bearer $KEY"</span> <span class="s">https://yatabase.gftd.ai/auth/v1/whoami</span></pre>
<p>Returns the tenant identity for the current bearer:
   <code>{orgDid, actorDid, plan, attachedEmail, stripeCustomerId, canOpenPortal}</code>.
   Useful for client bootstrap, dashboard rendering, and confirming a recovered key
   resolved to the original tenant.</p>

<h2 id="members">Members &amp; multi-tenant</h2>
<pre><span class="c"># List members of your org</span>
curl -H <span class="s">"authorization: Bearer $KEY"</span> <span class="s">https://yatabase.gftd.ai/api/members</span>

<span class="c"># Mint a new key for a teammate</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/invite</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -d '{"<span class="k">name</span>":"alice"}'

<span class="c"># Revoke a key</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/revoke</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -d '{"<span class="k">vertex_id</span>":"apikey:..."}'</pre>

<h2 id="webhooks">Outbound webhooks</h2>
<p>Register a URL to receive HMAC-signed POST notifications when Cypher mutations happen.
   Useful for replicating to Slack, Zapier, your own backend, or any HTTP endpoint.</p>
<pre><span class="c"># Register a webhook (URL must be HTTPS)</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/api/webhooks</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{
    "<span class="k">url</span>": "https://your-app.example.com/yata-webhook",
    "<span class="k">label</span>": "Person",
    "<span class="k">types</span>": ["cypher.create", "cypher.set", "cypher.delete"]
  }'
<span class="c"># Response includes webhook.secret — save it. Subsequent GETs only show secretPrefix.</span>

<span class="c"># List your webhooks (secret redacted)</span>
curl -H <span class="s">"authorization: Bearer $KEY"</span> <span class="s">https://yatabase.gftd.ai/api/webhooks</span>

<span class="c"># Remove a webhook</span>
curl -X DELETE <span class="s">https://yatabase.gftd.ai/api/webhooks/whk_...</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span></pre>
<table>
  <thead><tr><th>Event</th><th>Fires on</th><th>Payload</th></tr></thead>
  <tbody>
    <tr><td><code>cypher.create</code></td><td><code>CREATE (n:Label {…})</code></td><td><code>{label, properties}</code></td></tr>
    <tr><td><code>cypher.set</code></td><td><code>MATCH … SET n.x = "y"</code></td><td><code>{label, properties, updatedCount}</code></td></tr>
    <tr><td><code>cypher.delete</code></td><td><code>MATCH (n:Label) DELETE n</code></td><td><code>{label, deletedCount}</code></td></tr>
    <tr><td><code>cypher.create_edge</code></td><td><code>CREATE (a)-[:T]-&gt;(b)</code></td><td><code>{srcLabel, srcProperties, edgeType, edgeProperties, dstLabel, dstProperties}</code></td></tr>
    <tr><td><code>cypher.delete_edge</code></td><td><code>MATCH (a)-[r:T]-&gt;(b) DELETE r</code></td><td><code>{srcLabel, edgeType, dstLabel}</code></td></tr>
  </tbody>
</table>
<h3>Delivery contract</h3>
<ul>
  <li><strong>Method:</strong> <code>POST application/json</code></li>
  <li><strong>X-Yatabase-Event:</strong> the event name (e.g. <code>cypher.create</code>)</li>
  <li><strong>X-Yatabase-Signature:</strong> <code>hex(hmac-sha256(secret, body))</code> — verify in your handler to authenticate the call</li>
  <li><strong>X-Yatabase-Delivery:</strong> nanoid for tracing / dedup</li>
  <li><strong>Body:</strong> <code>{event, orgDid, ...payload, ts}</code></li>
  <li><strong>Retries:</strong> fire-and-forget in v1. The next matching mutation will re-fire — design your handler idempotent if you care about exactly-once.</li>
  <li><strong>Per-org cap:</strong> 10 webhooks. <code>DELETE</code> one before adding another.</li>
  <li><strong>HTTPS only:</strong> <code>http://</code> URLs are rejected at registration.</li>
</ul>
<h3>Verifying a delivery (Node example)</h3>
<pre>import crypto from "node:crypto";

function verifyYatabase(req, secret) {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(req.rawBody)  <span class="c">// the exact bytes received</span>
    .digest("hex");
  return req.headers["x-yatabase-signature"] === expected;
}</pre>

<h2 id="privacy">Data rights (CCPA / GDPR / 改正個人情報保護法)</h2>
<pre><span class="c"># Right to know — full export</span>
curl -H <span class="s">"authorization: Bearer $KEY"</span> <span class="s">https://yatabase.gftd.ai/api/export</span>

<span class="c"># Right to delete — irreversible</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/api/account/delete</span> \\
  -H <span class="s">"authorization: Bearer $KEY"</span> \\
  -d '{"<span class="k">confirm</span>":"DELETE"}'</pre>
<p>See <a href="/.well-known/agent.json">/.well-known/agent.json</a> for the legal disclaimer.
   Billing rows (<code>vertex_billing_event</code>) are retained 7 years per 法人税法 §126 / IRS §6001.</p>

<h2 id="errors">Errors</h2>
<table>
  <thead><tr><th>Status</th><th>Body shape</th><th>When</th></tr></thead>
  <tbody>
    <tr><td>400</td><td><code>{error,message}</code></td><td>Bad JSON / forbidden Cypher / invalid params</td></tr>
    <tr><td>401</td><td><code>{error:"Unauthorized"}</code></td><td>Missing / invalid Bearer</td></tr>
    <tr><td>403</td><td><code>{error:"Forbidden"}</code></td><td>Admin gate (operator-only paths)</td></tr>
    <tr><td>404</td><td><code>{error:"NotFound"}</code></td><td>Path / resource missing</td></tr>
    <tr><td>409</td><td><code>{error:"PreconditionFailed"}</code></td><td>State machine violation</td></tr>
    <tr><td>429</td><td><code>{error:"QuotaExceeded"}</code></td><td>Daily plan cap hit; <code>Retry-After</code> header set</td></tr>
    <tr><td>500</td><td><code>{error:"InternalServerError"}</code></td><td>Worker exception</td></tr>
    <tr><td>503</td><td><code>{error:"ServiceUnavailable"}</code></td><td>Hyperdrive / dispatcher unreachable</td></tr>
  </tbody>
</table>

<h2 id="observability">Observability</h2>
<ul>
  <li><a href="/health"><code>/health</code></a> — Worker probe (always JSON ok:true)</li>
  <li><a href="/_app/meta"><code>/_app/meta</code></a> — version + surface listing</li>
  <li><a href="/status"><code>/status</code></a> — public uptime + 7d agent activity</li>
  <li><a href="/team"><code>/team</code></a> — 4 resident AI actors with public DIDs</li>
  <li><code>/api/audit</code> (auth) — last 90 d of your tenant's request log</li>
  <li><code>/api/outbox</code> (auth) — your tenant's email outbox</li>
  <li><code>/api/invoices</code> (auth) — month list; <code>/api/invoice?month=YYYY-MM</code> for HTML</li>
</ul>

<h2 id="compliance">Compliance</h2>
<table>
  <thead><tr><th>Regulation</th><th>Article</th><th>Endpoint</th></tr></thead>
  <tbody>
    <tr><td>CCPA</td><td>§1798.100 (right to know)</td><td><code>GET /api/export</code></td></tr>
    <tr><td>CCPA</td><td>§1798.105 (right to delete)</td><td><code>POST /api/account/delete</code></td></tr>
    <tr><td>GDPR</td><td>Art 17 (erasure)</td><td><code>POST /api/account/delete</code></td></tr>
    <tr><td>GDPR</td><td>Art 20 (portability)</td><td><code>GET /api/export</code></td></tr>
    <tr><td>GDPR</td><td>Art 30 (records of processing)</td><td><code>vertex_audit_log</code> (90 d)</td></tr>
    <tr><td>改正個人情報保護法</td><td>第33条 (開示請求)</td><td><code>GET /api/export</code></td></tr>
    <tr><td>改正個人情報保護法</td><td>第34-36条 (削除請求)</td><td><code>POST /api/account/delete</code></td></tr>
    <tr><td>JP 適格請求書 (T9007028460042)</td><td>etz hayim</td><td><code>GET /api/invoice?month=YYYY-MM</code></td></tr>
    <tr><td>法人税法</td><td>§126 (7 y retention)</td><td><code>vertex_billing_event</code></td></tr>
    <tr><td>IRS</td><td>§6001 (7 y retention)</td><td>same</td></tr>
  </tbody>
</table>
<p>Operator: <strong>etz hayim</strong> (運営法人). Vendor: <strong>Gftd Japan株式会社</strong> (T9007028460042).</p>

</article>

</main>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.gftd.ai</a> · <a href="/status">/status</a> · <a href="/team">/team</a> · <a href="/.well-known/agent.json">/.well-known/agent.json</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "docs",
      "cache-control": "public, max-age=300, s-maxage=600",
    },
  });
}
