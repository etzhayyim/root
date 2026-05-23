// studio.ts — yatabase Studio (browser console).
//
// A single self-contained HTML page served from the same Worker that runs
// the data-plane endpoints. No external assets, no SSR — pure CSR with
// `fetch('/cypher')` against the customer's own host. The API key is held
// in `localStorage` so the page works offline-first once loaded.
//
// Surfaces consumed:
//   POST /cypher      — Cypher query
//   POST /sparql      — SPARQL query (if customer has the lexicon)
//   GET  /_app/meta   — surface listing (sidebar)

const STUDIO_HTML = String.raw`<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>yatabase Studio</title>
<style>
  * { box-sizing: border-box; }
  body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
         margin: 0; background: #0e1116; color: #e1e4e8; }
  header { padding: 14px 24px; background: #181c24; border-bottom: 1px solid #30363d;
           display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 16px; margin: 0; font-weight: 600; }
  header .meta { font-size: 12px; color: #768390; }
  header .right { margin-left: auto; display: flex; gap: 8px; align-items: center; }
  main { display: grid; grid-template-columns: 220px 1fr; min-height: calc(100vh - 50px); }
  nav { background: #161b22; border-right: 1px solid #30363d; padding: 16px; }
  nav h3 { font-size: 11px; font-weight: 700; color: #768390; text-transform: uppercase;
           letter-spacing: 0.05em; margin: 14px 0 6px; }
  nav h3:first-child { margin-top: 0; }
  nav a { display: block; padding: 5px 8px; color: #d1d5da; text-decoration: none;
          border-radius: 4px; font-size: 13px; cursor: pointer; }
  nav a:hover { background: #21262d; }
  nav a.active { background: #1f6feb; color: white; }
  section { padding: 20px 28px; min-width: 0; }
  textarea { width: 100%; min-height: 140px; font: 13px/1.45 "SF Mono", Menlo, Consolas, monospace;
             background: #0a0d12; color: #e1e4e8; border: 1px solid #30363d; border-radius: 6px;
             padding: 10px 12px; resize: vertical; }
  textarea:focus { outline: 2px solid #1f6feb; outline-offset: -2px; }
  button { background: #2da44e; color: white; border: none; padding: 7px 18px; font: 13px;
           border-radius: 6px; cursor: pointer; font-weight: 500; }
  button:hover { background: #3fb463; }
  button.secondary { background: #21262d; color: #d1d5da; border: 1px solid #30363d; }
  button.secondary:hover { background: #30363d; }
  .toolbar { display: flex; gap: 8px; align-items: center; margin: 10px 0 16px; flex-wrap: wrap; }
  .toolbar label { font-size: 12px; color: #768390; }
  input[type=password], input[type=text] {
    font: 12px "SF Mono", Menlo, monospace; padding: 6px 8px; background: #0a0d12; color: #e1e4e8;
    border: 1px solid #30363d; border-radius: 4px; min-width: 320px; }
  input:focus { outline: 2px solid #1f6feb; outline-offset: -1px; }
  table { border-collapse: collapse; margin-top: 12px; width: 100%; font-size: 13px; }
  th, td { border: 1px solid #30363d; padding: 6px 10px; text-align: left;
           font: 12px/1.4 "SF Mono", Menlo, monospace; vertical-align: top; max-width: 480px;
           word-break: break-all; }
  th { background: #181c24; font-weight: 600; color: #d1d5da; }
  tr:nth-child(even) td { background: #11151c; }
  .pill { display: inline-block; padding: 2px 8px; font-size: 11px; border-radius: 12px;
          background: #21262d; color: #768390; margin-left: 4px; }
  .pill.ok { background: #1a3b1a; color: #7ee787; }
  .pill.err { background: #3b1a1a; color: #ff7b72; }
  .pill.warn { background: #3b2a0e; color: #fbbf24; }
  .bmc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 10px 0 }
  .bmc-cell { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px 12px; min-height: 120px }
  .bmc-cell h4 { margin: 0 0 6px; font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em }
  .bmc-cell ul { list-style: none; padding: 0; margin: 0; font-size: 12px; color: #d1d5da }
  .bmc-cell li { padding: 2px 0; border-bottom: 1px dotted #21262d }
  .bmc-cell li:last-child { border-bottom: 0 }
  pre.json { background: #0a0d12; padding: 12px; border-radius: 6px; overflow: auto;
             max-height: 300px; font: 12px "SF Mono", Menlo, monospace; }
  .error { color: #ff7b72; }
  .meta { font-size: 12px; color: #768390; }
  h2 { font-size: 18px; margin: 4px 0 16px; }
  .empty { color: #768390; padding: 18px; text-align: center; border: 1px dashed #30363d;
           border-radius: 6px; }
  details { margin-top: 16px; }
  details summary { cursor: pointer; font-size: 12px; color: #768390; }
  details[open] summary { color: #d1d5da; }
</style>
</head>
<body>
<header>
  <h1>🔮 yatabase Studio</h1>
  <span class="meta">io-yatabase · Cypher / SPARQL / Storage</span>
  <div class="right">
    <span id="authStatus" class="meta">no key</span>
  </div>
</header>
<main>
  <nav>
    <h3>Query</h3>
    <a class="active" data-pane="cypher">Cypher</a>
    <a data-pane="sparql">SPARQL</a>
    <a data-pane="storage">Storage</a>
    <h3>Schema</h3>
    <a data-pane="schema">Tables</a>
    <h3>Surface</h3>
    <a data-pane="meta">/_app/meta</a>
    <a data-pane="mcp">MCP tools</a>
    <h3>Account</h3>
    <a data-pane="signup">Sign up</a>
    <a data-pane="account">Account</a>
    <a data-pane="plan">Plan</a>
    <a data-pane="usage">Usage</a>
    <a data-pane="invoices">Invoices</a>
    <a data-pane="members">Members</a>
    <a data-pane="audit">Audit log</a>
    <a data-pane="outbox">Email outbox</a>
    <a data-pane="webhooks">Webhooks</a>
    <a data-pane="privacy">Privacy</a>
    <a data-pane="auth">API key</a>
    <h3>Operator</h3>
    <a data-pane="leads">Leads (admin)</a>
    <a data-pane="bmc">BMC (admin)</a>
  </nav>
  <section id="paneCypher" class="pane">
    <h2>Cypher</h2>
    <textarea id="cypherStmt">MATCH (n:Demo) RETURN n.vertex_id, n.name ORDER BY n.created_at DESC LIMIT 10</textarea>
    <div class="toolbar">
      <button onclick="runCypher()">Run</button>
      <button class="secondary" onclick="loadExample('matchAll')">MATCH all</button>
      <button class="secondary" onclick="loadExample('create')">CREATE</button>
      <button class="secondary" onclick="loadExample('where')">WHERE</button>
      <button class="secondary" onclick="loadExample('delete')">DELETE</button>
      <span id="cypherStatus" class="meta"></span>
    </div>
    <div id="cypherResult"></div>
    <details>
      <summary>Subset reference (P4a)</summary>
      <pre class="json">MATCH (n:Label) [WHERE n.prop OP $param | 'literal' | 42 [(AND|OR) ...]]
   RETURN n | n.prop [AS alias], ...
   [ORDER BY n.prop ASC|DESC] [SKIP N] [LIMIT N]

CREATE (n:Label {k: $param | 'lit' | 42 | true | null, ...}) [RETURN ...]

MATCH (n:Label {k: v, ...}) DELETE n

forbidden: DETACH DELETE / FOREACH / CALL { ...write... }
</pre>
    </details>
  </section>
  <section id="paneSparql" class="pane" hidden>
    <h2>SPARQL</h2>
    <textarea id="sparqlStmt">SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10</textarea>
    <div class="toolbar"><button onclick="runSparql()">Run</button>
      <span id="sparqlStatus" class="meta"></span></div>
    <div id="sparqlResult"></div>
  </section>
  <section id="paneStorage" class="pane" hidden>
    <h2>Storage</h2>
    <p class="meta">Supabase-compatible <code>/storage/v1/*</code> + S3 SigV4 <code>/s3/*</code> are live.
    Use <code>aws-sdk-js</code> / <code>boto3</code> with access key prefix <code>gftd_*</code>
    or the API key as Bearer.</p>
    <div class="toolbar">
      <button onclick="listBuckets()">List buckets</button>
      <span id="storageStatus" class="meta"></span>
    </div>
    <div id="storageResult"></div>
  </section>
  <section id="paneSchema" class="pane" hidden>
    <h2>Tables in your tenant schema</h2>
    <p class="meta">Tables auto-created when you <code>CREATE</code> nodes
    of new labels. Click a table to see its columns.</p>
    <div class="toolbar">
      <button onclick="loadSchema()">Refresh</button>
      <span id="schemaStatus" class="meta"></span>
    </div>
    <div id="schemaResult"></div>
  </section>
  <section id="paneMeta" class="pane" hidden>
    <h2>/_app/meta</h2>
    <pre class="json" id="metaResult">loading…</pre>
  </section>
  <section id="paneMcp" class="pane" hidden>
    <h2>MCP tools/list</h2>
    <pre class="json" id="mcpResult">loading…</pre>
  </section>
  <section id="paneSignup" class="pane" hidden>
    <h2>Sign up — get a free API key</h2>
    <p class="meta">Free tier: <strong>$0/month</strong> · 1,000 API
    requests/day · 5 GB storage · multi-tenant graph DB + Supabase-style
    storage + MCP cell-membrane. Click the button below to mint a fresh
    <code>sk_live_yata_*</code> token bound to a new tenant. The key is
    shown <strong>once</strong> — copy it immediately. First Cypher
    call auto-provisions your tenant schema.</p>
    <div class="toolbar">
      <button onclick="signup()">Mint free key</button>
      <span id="signupStatus" class="meta"></span>
    </div>
    <div id="signupResult"></div>
  </section>
  <section id="palePlanPlaceholder" class="pane" hidden></section>
  <section id="paneAccount" class="pane" hidden>
    <h2>Account</h2>
    <p class="meta">Tenant identity for the current API key. Attach a recovery
    email <em>now</em> — if you ever lose the key, you can use
    <code>POST /auth/v1/recover</code> to mint a fresh one. Once you've
    completed a Stripe Checkout, the Customer Portal button below lets
    you change card, cancel, or download past invoices.</p>
    <div class="toolbar">
      <button onclick="loadAccount()">Refresh</button>
      <span id="accountStatus" class="meta"></span>
    </div>
    <div id="accountResult"></div>
    <details>
      <summary>Attach a recovery email</summary>
      <p class="meta">Saves the email to your tenant + adds a SHA-256 entry
      to the reverse index used by <code>/auth/v1/recover</code>. Idempotent.</p>
      <div class="toolbar">
        <input type="text" id="attachEmailInput" placeholder="you@example.com" />
        <button onclick="attachAccountEmail()">Attach</button>
        <span id="attachEmailStatus" class="meta"></span>
      </div>
    </details>
    <details>
      <summary>Open Stripe Customer Portal</summary>
      <p class="meta">Self-serve billing management. Requires the org has
      completed at least one Checkout (otherwise returns 400 NoStripeCustomer).</p>
      <div class="toolbar">
        <button onclick="openPortal()">Open portal</button>
        <span id="portalStatus" class="meta"></span>
      </div>
    </details>
  </section>
  <section id="panePlan" class="pane" hidden>
    <h2>Plan</h2>
    <p class="meta">Plan tier is inferred from your tenant DID. Free
    tier covers anonymous signup; upgrade paths require coordination
    with sales (Stripe checkout in P8).</p>
    <div class="toolbar">
      <button onclick="loadPlan()">Refresh</button>
      <span id="planStatus" class="meta"></span>
    </div>
    <div id="planResult"></div>
  </section>
  <section id="paneUsage" class="pane" hidden>
    <h2>Usage (last 24h)</h2>
    <p class="meta">Each authenticated call to /cypher /storage /mcp emits
    a <code>vertex_billing_event</code> row. Pricing follows the rate
    card in ADR-2605080000 §D1.</p>
    <div class="toolbar">
      <button onclick="loadUsage()">Refresh</button>
      <span id="usageStatus" class="meta"></span>
    </div>
    <div id="usageResult"></div>
  </section>
  <section id="paneInvoices" class="pane" hidden>
    <h2>適格請求書 / Invoices</h2>
    <p class="meta">月別の適格請求書を表示・PDF 印刷できます。登録番号
    <code>T9007028460042</code> (etz hayim 適格請求書発行事業者) 付き。
    印刷 → PDF 保存 で正式な書類になります。</p>
    <div class="toolbar">
      <button onclick="loadInvoices()">Refresh</button>
      <span id="invoicesStatus" class="meta"></span>
    </div>
    <div id="invoicesResult"></div>
  </section>
  <section id="paneMembers" class="pane" hidden>
    <h2>Members</h2>
    <p class="meta">Each member gets their own <code>sk_live_yata_*</code>
    key but they all share this tenant's schema, plan, and billing.
    Invite teammates with one click — they get a key shown once. Revoke
    keys when a member leaves.</p>
    <div class="toolbar">
      <input id="inviteName" type="text" placeholder="Member name (optional)" />
      <button onclick="inviteMember()">Invite member</button>
      <button class="secondary" onclick="loadMembers()">Refresh</button>
      <span id="membersStatus" class="meta"></span>
    </div>
    <div id="invitedKeyResult"></div>
    <div id="membersResult"></div>
  </section>
  <section id="paneWebhooks" class="pane" hidden>
    <h2>Webhooks</h2>
    <p class="meta">Register URLs to receive POST notifications on Cypher
    mutations (create / set / delete / create_edge / delete_edge).
    Optional <code>label</code> filter scopes deliveries to a single
    label. Each POST is signed with <code>X-Yatabase-Signature</code>
    (hex hmac-sha256 over body). Save the secret — it's only shown once.
    Per-org cap: 10.</p>
    <div class="toolbar">
      <input type="text" id="whUrl" placeholder="https://your-app.example.com/webhook" style="min-width:340px" />
      <input type="text" id="whLabel" placeholder="label (optional)" style="min-width:140px" />
      <button onclick="registerWebhookFromStudio()">Register</button>
      <button class="secondary" onclick="loadWebhooks()">Refresh</button>
      <span id="webhooksStatus" class="meta"></span>
    </div>
    <div id="webhooksResult"></div>
  </section>
  <section id="paneOutbox" class="pane" hidden>
    <h2>Email outbox</h2>
    <p class="meta">Every signup / upgrade / member-invite / revoke writes
    a row here. When <code>RESEND_API_KEY</code> is configured the row
    flips to <code>sent</code> immediately; otherwise it stays
    <code>pending</code> for a separate cron flush. Pass <code>email</code>
    in the signup body to receive the welcome message.</p>
    <div class="toolbar">
      <button onclick="loadOutbox()">Refresh</button>
      <span id="outboxStatus" class="meta"></span>
    </div>
    <div id="outboxResult"></div>
  </section>
  <section id="paneAudit" class="pane" hidden>
    <h2>Audit log (last 24h)</h2>
    <p class="meta">Every authenticated call against your tenant is
    recorded. Use this to spot rogue keys (unfamiliar IP hash) or
    confirm that a teammate's action actually happened.
    Retention: 90 days.</p>
    <div class="toolbar">
      <button onclick="loadAudit()">Refresh</button>
      <span id="auditStatus" class="meta"></span>
    </div>
    <div id="auditResult"></div>
  </section>
  <section id="panePrivacy" class="pane" hidden>
    <h2>Privacy &amp; data rights</h2>
    <p class="meta">Compliant with <strong>CCPA §1798.100 / §1798.105</strong>
    (US California), <strong>GDPR Art 17 / Art 20</strong> (EU/UK),
    and <strong>改正個人情報保護法 第33条 / 第34-36条</strong> (Japan).
    <em>Export</em> downloads everything we have on you as JSON;
    <em>Delete</em> permanently terminates your tenant. Billing records
    are retained 7 years (US IRS §6001 / Japan 法人税法 §126).</p>
    <h3>① Right to know / Data export</h3>
    <p class="meta">CCPA §1798.100 · GDPR Art 20 · 個人情報保護法 第33条</p>
    <div class="toolbar">
      <button onclick="exportData()">Download my data (JSON)</button>
      <span id="exportStatus" class="meta"></span>
    </div>
    <h3 style="margin-top:24px">② Right to delete / Account deletion</h3>
    <p class="meta">CCPA §1798.105 · GDPR Art 17 · 個人情報保護法 第34-36条</p>
    <p class="meta error">⚠ One-way. Drops your tenant schema (vertex_*, edge_*).
    All API keys revoked. Billing records retained 7y for tax law (US/JP).</p>
    <div class="toolbar">
      <button onclick="deleteAccount()" style="background:#cf222e">Delete account</button>
      <span id="deleteStatus" class="meta"></span>
    </div>
    <div id="deleteResult"></div>
  </section>
  <section id="paneAuth" class="pane" hidden>
    <h2>API key</h2>
    <p class="meta">Paste your <code>sk_live_yata_*</code> token (or any <code>sk_live_*</code> key
    minted via PDS <code>ai.gftd.auth.createApiKey</code>). Stored in <code>localStorage</code>
    on this device only.</p>
    <div class="toolbar">
      <input id="apiKey" type="password" placeholder="sk_live_yata_..." />
      <button onclick="saveKey()">Save</button>
      <button class="secondary" onclick="clearKey()">Clear</button>
      <span id="keyStatus" class="meta"></span>
    </div>
  </section>

  <section id="paneLeads" class="pane" hidden>
    <h2>Leads (operator only)</h2>
    <p class="meta">Top-of-funnel CRM. Drafts queued by <code>nishino</code> arrive here
      with status <code>new</code> → <code>drafted</code>. Approve to mark for send (still
      requires Resend wired before anything actually leaves the outbox). Admin key is
      gate-checked server-side; held in <code>localStorage</code> on this device only.</p>
    <div class="toolbar">
      <input id="adminKey" type="password" placeholder="x-yata-admin-key (operator-only)" style="min-width:340px" />
      <button onclick="saveAdminKey()">Save</button>
      <button class="secondary" onclick="clearAdminKey()">Clear</button>
      <button onclick="loadLeads()">Refresh</button>
      <select id="leadStatusFilter">
        <option value="">all</option>
        <option value="sendable">sendable (approved + email)</option>
        <option value="new">new</option>
        <option value="drafted" selected>drafted</option>
        <option value="approved">approved</option>
        <option value="dismissed">dismissed</option>
        <option value="sent">sent</option>
      </select>
      <span id="adminKeyStatus" class="meta"></span>
    </div>
    <div class="toolbar" style="margin-top:6px">
      <button onclick="leadsBatchSend(false)" style="background:#0ea5e9;color:white">Send all sendable</button>
      <button class="secondary" onclick="leadsBatchSend(true)">Dry-run preview</button>
      <button class="secondary" onclick="outboxRetryFailed()">Retry failed outbox</button>
      <span class="meta" style="margin-left:8px">Send-batch loops sendable list. Retry failed re-attempts every vertex_email_outbox row with status=failed|pending from last 24h.</span>
    </div>
    <div id="leadsArea" class="meta">No leads loaded yet.</div>
    <div id="batchResult" class="meta" style="margin-top:8px"></div>
  </section>

  <section id="paneBmc" class="pane" hidden>
    <h2>Business Model Canvas (operator only)</h2>
    <p class="meta">Lean Build-Measure-Learn loop anchored to the 9 BMC blocks. Daily LangGraph iteration
       (<code>0 7 * * *</code>) measures the active hypothesis, proposes persevere / pivot / kill.
       Operator overrides via the buttons below. Every BMC edit appends a new version (never UPDATE).</p>
    <div class="toolbar">
      <button onclick="bmcBootstrap()">Bootstrap tables</button>
      <button onclick="bmcRefresh()">Refresh</button>
      <button onclick="bmcIterateNow()" style="background:#0ea5e9;color:white">Iterate now</button>
      <span id="bmcStatus" class="meta"></span>
    </div>
    <div id="bmcIterateResult" class="meta" style="margin:8px 0"></div>
    <h3 style="margin-top:18px">Canvas v<span id="bmcVersion">?</span></h3>
    <p class="meta" id="bmcCanvasMeta"></p>
    <div id="bmcCanvas" class="bmc-grid">No canvas yet — POST /_bmc/state with a v1 body.</div>

    <h3 style="margin-top:24px">Hypothesis backlog</h3>
    <div class="toolbar">
      <button onclick="bmcAddHypothesis()">+ Add hypothesis</button>
      <select id="bmcHypFilter">
        <option value="">all</option>
        <option value="pending" selected>pending</option>
        <option value="active">active</option>
        <option value="completed">completed</option>
        <option value="killed">killed</option>
      </select>
      <button onclick="bmcLoadHypotheses()">Reload</button>
    </div>
    <div id="bmcHypotheses" class="meta">load to see backlog</div>

    <h3 style="margin-top:24px">Recent iterations</h3>
    <div id="bmcIterations" class="meta">load to see iterations</div>

    <h3 style="margin-top:24px">Decision wall</h3>
    <div id="bmcDecisions" class="meta">load to see persevere/pivot/kill outcomes</div>
  </section>
</main>
<script>
const $ = (id) => document.getElementById(id);
const KEY_STORAGE = 'yatabase.apiKey';

function loadKey() { return (localStorage.getItem(KEY_STORAGE) ?? '').trim(); }
function authStatus() {
  const k = loadKey();
  $('authStatus').innerHTML = k
    ? '<span class="pill ok">key set · ' + k.slice(0, 14) + '…</span>'
    : '<span class="pill err">no key — set in Settings</span>';
}
function saveKey() {
  const v = $('apiKey').value.trim();
  if (v) { localStorage.setItem(KEY_STORAGE, v); $('keyStatus').textContent = 'saved'; }
  else { localStorage.removeItem(KEY_STORAGE); $('keyStatus').textContent = 'empty — cleared'; }
  authStatus();
}
function clearKey() {
  localStorage.removeItem(KEY_STORAGE);
  $('apiKey').value = '';
  $('keyStatus').textContent = 'cleared';
  authStatus();
}

document.querySelectorAll('nav a').forEach((a) => {
  a.addEventListener('click', () => {
    document.querySelectorAll('nav a').forEach((b) => b.classList.remove('active'));
    a.classList.add('active');
    document.querySelectorAll('.pane').forEach((p) => (p.hidden = true));
    const target = $('pane' + a.dataset.pane.charAt(0).toUpperCase() + a.dataset.pane.slice(1));
    if (target) target.hidden = false;
    if (a.dataset.pane === 'meta') loadMeta();
    if (a.dataset.pane === 'mcp') loadMcp();
    if (a.dataset.pane === 'schema') loadSchema();
    if (a.dataset.pane === 'usage') loadUsage();
    if (a.dataset.pane === 'plan') loadPlan();
    if (a.dataset.pane === 'account') loadAccount();
    if (a.dataset.pane === 'invoices') loadInvoices();
    if (a.dataset.pane === 'members') loadMembers();
    if (a.dataset.pane === 'audit') loadAudit();
    if (a.dataset.pane === 'outbox') loadOutbox();
    if (a.dataset.pane === 'webhooks') loadWebhooks();
    if (a.dataset.pane === 'privacy') { /* no autoload */ }
    if (a.dataset.pane === 'auth') $('apiKey').value = loadKey();
    if (a.dataset.pane === 'leads') {
      $('adminKey').value = loadAdminKey();
      adminKeyStatus();
      loadLeads();
    }
    if (a.dataset.pane === 'bmc') {
      bmcRefresh();
    }
  });
});

const examples = {
  matchAll: 'MATCH (n:Demo) RETURN n.vertex_id, n.name LIMIT 10',
  create: "CREATE (n:Demo {vertex_id: 'at://my/note-" + Date.now() + "', name: 'My note', created_at: '" + new Date().toISOString() + "'}) RETURN n.vertex_id, n.name",
  where: "MATCH (n:Demo) WHERE n.name <> '' RETURN n.vertex_id, n.name ORDER BY n.created_at DESC LIMIT 10",
  delete: "MATCH (n:Demo {vertex_id: 'at://my/note-PASTE_ID_HERE'}) DELETE n",
};
function loadExample(k) { $('cypherStmt').value = examples[k]; }

async function runCypher() {
  const key = loadKey();
  if (!key) { $('cypherStatus').innerHTML = '<span class="error">✗ API key required (Settings → API key)</span>'; return; }
  const stmt = $('cypherStmt').value.trim();
  $('cypherStatus').textContent = '⏳ running…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/cypher', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify({ statements: [{ statement: stmt, parameters: {} }] }),
    });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('cypherStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    renderCypherResult(body);
  } catch (e) {
    $('cypherStatus').innerHTML = '<span class="pill err">network error</span>';
    $('cypherResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

function renderCypherResult(body) {
  const root = $('cypherResult');
  root.innerHTML = '';
  if (Array.isArray(body.errors) && body.errors.length > 0) {
    root.innerHTML = '<h3>Errors</h3><pre class="json error">' + escapeHtml(JSON.stringify(body.errors, null, 2)) + '</pre>';
    return;
  }
  if (!Array.isArray(body.results) || body.results.length === 0) {
    root.innerHTML = '<div class="empty">no result block</div>';
    return;
  }
  for (const r of body.results) {
    const cols = r.columns ?? [];
    const rows = r.data ?? [];
    if (cols.length === 0) {
      root.innerHTML += '<div class="meta">' + (rows.length === 0 ? 'mutation OK (no rows returned)' : 'rows = ' + rows.length) + '</div>';
      continue;
    }
    let html = '<div class="meta" style="margin:8px 0">' + rows.length + ' row' + (rows.length === 1 ? '' : 's') + '</div>';
    html += '<table><thead><tr>';
    for (const c of cols) html += '<th>' + escapeHtml(c) + '</th>';
    html += '</tr></thead><tbody>';
    for (const row of rows) {
      html += '<tr>';
      for (const cell of (row.row ?? [])) {
        const s = cell === null ? '<span class="meta">null</span>' : escapeHtml(typeof cell === 'string' ? cell : JSON.stringify(cell));
        html += '<td>' + s + '</td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table>';
    root.innerHTML += html;
  }
}

async function runSparql() {
  const key = loadKey();
  if (!key) { $('sparqlStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('sparqlStatus').textContent = '⏳ running…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/sparql', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify({ query: $('sparqlStmt').value.trim(), format: 'json' }),
    });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('sparqlStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    $('sparqlResult').innerHTML = '<pre class="json">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
  } catch (e) {
    $('sparqlStatus').innerHTML = '<span class="pill err">network error</span>';
    $('sparqlResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function listBuckets() {
  const key = loadKey();
  if (!key) { $('storageStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('storageStatus').textContent = '⏳ loading…';
  try {
    const resp = await fetch('/storage/v1/bucket', {
      headers: { 'authorization': 'Bearer ' + key },
    });
    const body = await resp.json();
    $('storageStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span>';
    $('storageResult').innerHTML = '<pre class="json">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
  } catch (e) {
    $('storageStatus').innerHTML = '<span class="pill err">network error</span>';
    $('storageResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function loadMeta() {
  try {
    const resp = await fetch('/_app/meta');
    const body = await resp.json();
    $('metaResult').textContent = JSON.stringify(body, null, 2);
  } catch (e) {
    $('metaResult').innerHTML = '<span class="error">' + escapeHtml(e.message) + '</span>';
  }
}

async function loadWebhooks() {
  const key = loadKey();
  if (!key) { $('webhooksStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('webhooksStatus').textContent = '⏳ loading…';
  try {
    const resp = await fetch('/api/webhooks', { headers: { 'authorization': 'Bearer ' + key } });
    const body = await resp.json();
    $('webhooksStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span>';
    if (!resp.ok) {
      $('webhooksResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    const rows = body.webhooks ?? [];
    if (rows.length === 0) {
      $('webhooksResult').innerHTML = '<div class="empty">No webhooks registered. Add a URL above to receive POST notifications on Cypher mutations.</div>';
      return;
    }
    let html = '<table style="margin-top:14px"><thead><tr><th>id</th><th>url</th><th>label</th><th>types</th><th>secretPrefix</th><th>createdAt</th><th>action</th></tr></thead><tbody>';
    for (const w of rows) {
      html += '<tr>'
        + '<td><code>' + escapeHtml(w.id) + '</code></td>'
        + '<td><code>' + escapeHtml(w.url) + '</code></td>'
        + '<td>' + escapeHtml(w.label ?? '<any>') + '</td>'
        + '<td>' + (w.types || []).map((t) => '<span class="pill">' + escapeHtml(t) + '</span>').join(' ') + '</td>'
        + '<td><code>' + escapeHtml(w.secretPrefix ?? '') + '</code></td>'
        + '<td>' + escapeHtml(w.createdAt ?? '') + '</td>'
        + '<td><button class="secondary" onclick="deleteWebhookFromStudio(\'' + w.id + '\')">delete</button></td>'
        + '</tr>';
    }
    html += '</tbody></table>';
    $('webhooksResult').innerHTML = html;
  } catch (e) {
    $('webhooksStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function registerWebhookFromStudio() {
  const key = loadKey();
  if (!key) { $('webhooksStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  const url = ($('whUrl').value || '').trim();
  const label = ($('whLabel').value || '').trim();
  if (!url) { $('webhooksStatus').innerHTML = '<span class="error">url required</span>'; return; }
  $('webhooksStatus').textContent = '⏳ registering…';
  try {
    const body = label ? { url, label } : { url };
    const resp = await fetch('/api/webhooks', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    const rb = await resp.json();
    if (!resp.ok) {
      $('webhooksStatus').innerHTML = '<span class="pill err">' + resp.status + '</span> ' + escapeHtml(rb.message ?? rb.error ?? '');
      return;
    }
    // Show the secret ONCE in a banner the user can copy.
    $('webhooksStatus').innerHTML = '<span class="pill ok">registered</span>';
    $('webhooksResult').innerHTML =
      '<div style="background:#3b2a0e;color:#fbbf24;padding:14px;border-radius:6px;margin:14px 0;font:13px ui-monospace,Menlo,monospace">'
      + '⚠ <strong>Save this secret now — it will not be shown again.</strong><br/>'
      + 'id: <code>' + escapeHtml(rb.webhook.id) + '</code><br/>'
      + 'secret: <code style="user-select:all">' + escapeHtml(rb.webhook.secret) + '</code>'
      + '</div>';
    $('whUrl').value = ''; $('whLabel').value = '';
    setTimeout(loadWebhooks, 600);
  } catch (e) {
    $('webhooksStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function deleteWebhookFromStudio(id) {
  const key = loadKey();
  if (!key) return;
  if (!confirm('Delete webhook ' + id + '?')) return;
  try {
    await fetch('/api/webhooks/' + encodeURIComponent(id), { method: 'DELETE', headers: { 'authorization': 'Bearer ' + key } });
    loadWebhooks();
  } catch { /* ignore */ }
}

async function loadOutbox() {
  const key = loadKey();
  if (!key) { $('outboxStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('outboxStatus').textContent = '⏳ loading…';
  try {
    const resp = await fetch('/api/outbox?limit=100', { headers: { 'authorization': 'Bearer ' + key } });
    const body = await resp.json();
    if (!resp.ok) {
      $('outboxStatus').innerHTML = '<span class="pill err">' + resp.status + '</span>';
      $('outboxResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    $('outboxStatus').innerHTML = '<span class="pill ok">' + resp.status + '</span> ' + body.events.length + ' email' + (body.events.length === 1 ? '' : 's');
    if (body.events.length === 0) {
      $('outboxResult').innerHTML = '<div class="empty">no email events yet — try /auth/v1/signup with email field, /auth/v1/upgrade, or /auth/v1/invite</div>';
      return;
    }
    let html = '<table style="margin-top:14px"><thead><tr><th>kind</th><th>subject</th><th>recipient</th><th>status</th><th>created</th></tr></thead><tbody>';
    for (const e of body.events) {
      const statusBadge = e.status === 'sent' ? '<span class="pill ok">sent</span>' : (e.status === 'failed' ? '<span class="pill err">failed</span>' : '<span class="pill">' + escapeHtml(e.status) + '</span>');
      html += '<tr><td>' + escapeHtml(e.kind) + '</td><td>' + escapeHtml(e.subject.slice(0, 60)) + '</td><td>' + escapeHtml(e.recipient || '<no recipient>') + '</td><td>' + statusBadge + '</td><td><code style="font-size:10px">' + escapeHtml(e.createdAt.slice(0, 19)) + '</code></td></tr>';
    }
    html += '</tbody></table>';
    $('outboxResult').innerHTML = html;
  } catch (e) {
    $('outboxStatus').innerHTML = '<span class="pill err">network error</span>';
    $('outboxResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function loadAudit() {
  const key = loadKey();
  if (!key) { $('auditStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('auditStatus').textContent = '⏳ loading…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/api/audit?limit=200', { headers: { 'authorization': 'Bearer ' + key } });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('auditStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    if (!resp.ok) {
      $('auditResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    if (!body.events || body.events.length === 0) {
      $('auditResult').innerHTML = '<div class="empty">no audit events in last 24h yet — make a Cypher / Storage / MCP request to populate the log</div>';
      return;
    }
    let html = '<div class="meta" style="margin:10px 0">window: ' + escapeHtml(body.windowStart) + ' → ' + escapeHtml(body.windowEnd) + ' · ' + body.events.length + ' events</div>';
    html += '<table><thead><tr><th>time (UTC)</th><th>surface</th><th>method</th><th>path</th><th>status</th><th>latency</th><th>ip_hash</th><th>ua</th></tr></thead><tbody>';
    for (const e of body.events.slice(0, 100)) {
      const time = new Date(e.tsMs).toISOString().slice(11, 19);
      const statusBadge = e.statusCode < 300 ? '<span class="pill ok">' + e.statusCode + '</span>' : (e.statusCode < 400 ? '<span class="pill">' + e.statusCode + '</span>' : '<span class="pill err">' + e.statusCode + '</span>');
      html += '<tr><td>' + time + '</td><td>' + escapeHtml(e.surface) + '</td><td>' + escapeHtml(e.method) + '</td><td><code style="font-size:10px">' + escapeHtml(e.path) + '</code></td><td>' + statusBadge + '</td><td>' + e.latencyMs + 'ms</td><td><code style="font-size:10px">' + escapeHtml(e.ipHash) + '</code></td><td><code style="font-size:10px">' + escapeHtml(e.userAgentHint.slice(0, 30)) + '</code></td></tr>';
    }
    html += '</tbody></table>';
    if (body.events.length > 100) html += '<div class="meta">… showing 100 of ' + body.events.length + ' events</div>';
    $('auditResult').innerHTML = html;
  } catch (e) {
    $('auditStatus').innerHTML = '<span class="pill err">network error</span>';
    $('auditResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function exportData() {
  const key = loadKey();
  if (!key) { $('exportStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('exportStatus').textContent = '⏳ generating export…';
  try {
    const resp = await fetch('/api/export', { headers: { 'authorization': 'Bearer ' + key } });
    if (!resp.ok) {
      const body = await resp.json();
      $('exportStatus').innerHTML = '<span class="pill err">' + resp.status + '</span> ' + escapeHtml(body.error ?? 'failed');
      return;
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = resp.headers.get('content-disposition')?.match(/filename="([^"]+)"/)?.[1] ?? 'yatabase-export.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    $('exportStatus').innerHTML = '<span class="pill ok">downloaded</span> (' + blob.size.toLocaleString() + ' bytes)';
  } catch (e) {
    $('exportStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function deleteAccount() {
  const key = loadKey();
  if (!key) { $('deleteStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  if (!confirm('本当にアカウントを削除しますか?\nこの操作は取り消せません。')) return;
  if (!confirm('再確認: tenant schema と全 API key が削除されます。続行しますか?')) return;
  $('deleteStatus').textContent = '⏳ deleting…';
  try {
    const resp = await fetch('/api/account/delete', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify({ confirm: 'DELETE' }),
    });
    const body = await resp.json();
    if (!resp.ok) {
      $('deleteStatus').innerHTML = '<span class="pill err">' + resp.status + '</span>';
      $('deleteResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    $('deleteStatus').innerHTML = '<span class="pill ok">deleted</span>';
    $('deleteResult').innerHTML = '<pre class="json">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
    localStorage.removeItem(KEY_STORAGE);
    authStatus();
  } catch (e) {
    $('deleteStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function loadMembers() {
  const key = loadKey();
  if (!key) { $('membersStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('membersStatus').textContent = '⏳ loading…';
  try {
    const resp = await fetch('/api/members', { headers: { 'authorization': 'Bearer ' + key } });
    const body = await resp.json();
    if (!resp.ok) {
      $('membersStatus').innerHTML = '<span class="pill err">' + resp.status + '</span>';
      $('membersResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    $('membersStatus').innerHTML = '<span class="pill ok">' + resp.status + '</span> ' + body.members.length + ' member' + (body.members.length === 1 ? '' : 's');
    let html = '<table style="margin-top:14px"><thead><tr><th>name</th><th>role</th><th>status</th><th>created</th><th>keyId</th><th></th></tr></thead><tbody>';
    for (const m of body.members) {
      const revokeOpener = "if(confirm('Revoke key '+'" + m.keyId + "'+'?')){ fetch('/auth/v1/revoke',{method:'POST',headers:{'authorization':'Bearer '+(localStorage.getItem('yatabase.apiKey')||''),'content-type':'application/json'},body:JSON.stringify({keyId:'" + m.keyId + "'})}).then(r=>r.json()).then(d=>{ alert('revoke: '+JSON.stringify(d)); loadMembers(); }); }";
      const statusBadge = m.status === 'active' ? '<span class="pill ok">active</span>' : '<span class="pill err">' + escapeHtml(m.status) + '</span>';
      html += '<tr><td>' + escapeHtml(m.name) + '</td><td>' + escapeHtml(m.role) + '</td><td>' + statusBadge + '</td><td>' + escapeHtml(m.createdAt.slice(0, 19)) + '</td><td><code style="font-size:10px">' + escapeHtml(m.keyId) + '</code></td><td>' + (m.status === 'active' ? '<button class="secondary" onclick="' + revokeOpener + '">Revoke</button>' : '—') + '</td></tr>';
    }
    html += '</tbody></table>';
    $('membersResult').innerHTML = html;
  } catch (e) {
    $('membersStatus').innerHTML = '<span class="pill err">network error</span>';
    $('membersResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function inviteMember() {
  const key = loadKey();
  if (!key) { $('membersStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  const name = $('inviteName').value.trim();
  $('membersStatus').textContent = '⏳ minting key…';
  try {
    const resp = await fetch('/auth/v1/invite', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    const body = await resp.json();
    if (!resp.ok) {
      $('membersStatus').innerHTML = '<span class="pill err">' + resp.status + '</span>';
      $('invitedKeyResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    $('membersStatus').innerHTML = '<span class="pill ok">invited</span>';
    $('invitedKeyResult').innerHTML =
      '<div style="background:#1a3b1a;color:#7ee787;padding:14px;border-radius:6px;margin-top:14px">' +
      '<strong>New member key (shown once):</strong></div>' +
      '<pre class="json">' + escapeHtml(body.apiKey) + '</pre>' +
      '<div class="meta">Share this key with <code>' + escapeHtml(body.name) + '</code> via your password manager. They join the same tenant ' + escapeHtml(body.orgDid) + '.</div>' +
      '<div class="toolbar"><button class="secondary" onclick="navigator.clipboard.writeText(\'' + body.apiKey + '\')">Copy key</button></div>';
    $('inviteName').value = '';
    await new Promise((r) => setTimeout(r, 1500));
    loadMembers();
  } catch (e) {
    $('membersStatus').innerHTML = '<span class="pill err">network error</span>';
    $('invitedKeyResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function loadInvoices() {
  const key = loadKey();
  if (!key) { $('invoicesStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('invoicesStatus').textContent = '⏳ loading…';
  try {
    const resp = await fetch('/api/invoices', { headers: { 'authorization': 'Bearer ' + key } });
    const body = await resp.json();
    if (!resp.ok) {
      $('invoicesStatus').innerHTML = '<span class="pill err">' + resp.status + '</span>';
      $('invoicesResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    $('invoicesStatus').innerHTML = '<span class="pill ok">' + resp.status + '</span>';
    if (!body.months || body.months.length === 0) {
      $('invoicesResult').innerHTML = '<div class="empty">この tenant にはまだ課金イベントがありません。Cypher / Storage / MCP を呼び出した翌月から請求書が生成可能になります。</div>';
      return;
    }
    let html = '<table style="margin-top:14px"><thead><tr><th>月</th><th>操作</th></tr></thead><tbody>';
    for (const m of body.months.reverse()) {
      const url = '/api/invoice?month=' + m;
      const opener = "var w=window.open(); fetch('" + url + "', { headers: { 'authorization': 'Bearer ' + (localStorage.getItem('yatabase.apiKey')||'') }}).then(r=>r.text()).then(t=>{ w.document.open(); w.document.write(t); w.document.close(); });";
      html += '<tr><td>' + escapeHtml(m) + '</td><td><button class="secondary" onclick="' + opener + '">View invoice</button></td></tr>';
    }
    html += '</tbody></table>';
    html += '<div class="meta" style="margin-top:10px">表示後にブラウザの「印刷」 → 「PDF として保存」で適格請求書 PDF を取得できます (登録番号 T9007028460042)。</div>';
    $('invoicesResult').innerHTML = html;
  } catch (e) {
    $('invoicesStatus').innerHTML = '<span class="pill err">network error</span>';
    $('invoicesResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function upgradeTo(plan) {
  const key = loadKey();
  if (!key) { $('upgradeStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('upgradeStatus').textContent = '⏳ requesting upgrade…';
  try {
    const resp = await fetch('/auth/v1/upgrade', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify({ plan }),
    });
    const body = await resp.json();
    if (!resp.ok) {
      $('upgradeStatus').innerHTML = '<span class="pill err">' + resp.status + '</span> ' + escapeHtml(body.message ?? body.error ?? 'failed');
      return;
    }
    // CHARTER RIDER §2: Stripe mode disabled. Stripe integration removed.
    if (body.mode === 'stripe' && body.checkoutUrl) {
      $('upgradeStatus').innerHTML = '<span class="pill err">Stripe payment is no longer supported (Charter Rider §2). Use the USDC donation flow instead.</span>';
      return;
    }
    $('upgradeStatus').innerHTML = '<span class="pill ok">' + escapeHtml(body.mode) + '</span> ' + escapeHtml(body.message ?? '');
    await new Promise((r) => setTimeout(r, 800));
    loadPlan();
  } catch (e) {
    $('upgradeStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function loadAccount() {
  const key = loadKey();
  if (!key) { $('accountStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('accountStatus').textContent = '⏳ loading…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/auth/v1/whoami', {
      headers: { 'authorization': 'Bearer ' + key },
    });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('accountStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    if (!resp.ok) {
      $('accountResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    const emailRow = body.attachedEmail
      ? '<tr><td>attached email</td><td>' + escapeHtml(body.attachedEmail) +
          (body.attachedEmailVerified
            ? ' <span class="pill ok">verified</span>'
            : ' <span class="pill warn">unverified — recovery disabled until you click the link in your inbox</span>')
        + '</td></tr>'
      : '<tr><td>attached email</td><td><span class="pill warn">none — attach one below</span></td></tr>';
    // CHARTER RIDER §2: Stripe portal row hidden. Stripe integration removed.
    const portalRow = body.canOpenPortal
      ? '<tr><td>Stripe customer [DEPRECATED]</td><td>' + escapeHtml(body.stripeCustomerId) + ' <span class="pill warn">portal unavailable (Charter Rider §2)</span></td></tr>'
      : '<tr><td>Stripe customer [DEPRECATED]</td><td><span class="pill warn">none — Stripe payment is no longer supported</span></td></tr>';
    let html = '<table style="margin-top:14px"><tbody>';
    html += '<tr><td>orgDid</td><td>' + escapeHtml(body.orgDid) + '</td></tr>';
    html += '<tr><td>actorDid</td><td>' + escapeHtml(body.actorDid) + '</td></tr>';
    html += '<tr><td>productScope</td><td>' + escapeHtml(body.productScope) + '</td></tr>';
    html += '<tr><td>plan</td><td>' + escapeHtml(body.plan) + '</td></tr>';
    html += emailRow;
    html += portalRow;
    html += '</tbody></table>';
    $('accountResult').innerHTML = html;
    if (body.attachedEmail) $('attachEmailInput').value = body.attachedEmail;
  } catch (e) {
    $('accountStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function attachAccountEmail() {
  const key = loadKey();
  const email = ($('attachEmailInput').value || '').trim();
  if (!key) { $('attachEmailStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    $('attachEmailStatus').innerHTML = '<span class="error">invalid email</span>';
    return;
  }
  $('attachEmailStatus').textContent = '⏳ attaching…';
  try {
    const resp = await fetch('/auth/v1/attach-email', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const body = await resp.json();
    if (resp.ok) {
      $('attachEmailStatus').innerHTML = '<span class="pill ok">attached</span> ' + escapeHtml(body.attachedAt);
      setTimeout(loadAccount, 400);
    } else {
      $('attachEmailStatus').innerHTML = '<span class="pill err">' + resp.status + '</span> ' + escapeHtml(body.message ?? body.error ?? '');
    }
  } catch (e) {
    $('attachEmailStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function openPortal() {
  const key = loadKey();
  if (!key) { $('portalStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('portalStatus').textContent = '⏳ minting portal…';
  try {
    const resp = await fetch('/auth/v1/portal', {
      method: 'POST',
      headers: { 'authorization': 'Bearer ' + key, 'content-type': 'application/json' },
      body: JSON.stringify({ returnUrl: window.location.href }),
    });
    const body = await resp.json();
    if (resp.ok && body.portalUrl) {
      $('portalStatus').innerHTML = '<span class="pill ok">opening in new tab…</span>';
      window.open(body.portalUrl, '_blank', 'noopener');
    } else {
      $('portalStatus').innerHTML = '<span class="pill err">' + resp.status + '</span> ' + escapeHtml(body.message ?? body.error ?? '');
    }
  } catch (e) {
    $('portalStatus').innerHTML = '<span class="pill err">network error</span> ' + escapeHtml(e.message);
  }
}

async function loadPlan() {
  const key = loadKey();
  if (!key) { $('planStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('planStatus').textContent = '⏳ loading…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/api/plan', {
      headers: { 'authorization': 'Bearer ' + key },
    });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('planStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    if (!resp.ok) {
      $('planResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    const usagePct = body.quota.apiRequestPerDay
      ? Math.round((body.quota.apiRequestUsedToday / body.quota.apiRequestPerDay) * 100)
      : 0;
    const monthlyUsd = (body.rules && typeof body.rules.monthlyUsd === 'number') ? body.rules.monthlyUsd : Math.round(body.monthlyJpy / 150);
    let html = '<div style="background:#1a3b1a;color:#7ee787;padding:14px;border-radius:6px;margin-top:14px">' +
      '<div style="font-size:18px;font-weight:600;margin-bottom:6px">' + escapeHtml(body.plan.toUpperCase()) + ' tier</div>' +
      '<div class="meta" style="color:#7ee787">$' + monthlyUsd.toLocaleString('en-US') + ' / month <span style="opacity:0.65">(≈ ¥' + body.monthlyJpy.toLocaleString() + ')</span></div>' +
      '</div>';
    html += '<table style="margin-top:14px"><thead><tr><th>quota</th><th>used today</th><th>limit</th><th>remaining</th></tr></thead><tbody>';
    html += '<tr><td>api_request</td><td>' + body.quota.apiRequestUsedToday + '</td><td>' + (body.quota.apiRequestPerDay ?? '∞') + '</td><td>' + (body.quota.apiRequestRemaining ?? '∞') + '</td></tr>';
    html += '<tr><td>storage_gb_cap</td><td>—</td><td>' + (body.rules.storageGbCap ?? '∞') + ' GB</td><td>—</td></tr>';
    html += '<tr><td>cypher_cu_ms_per_day</td><td>—</td><td>' + (body.rules.cypherCuMsPerDay ?? '∞') + '</td><td>—</td></tr>';
    html += '</tbody></table>';
    if (body.quota.exceeded) {
      html += '<div style="background:#3b1a1a;color:#ff7b72;padding:10px;border-radius:6px;margin-top:14px">⚠ Quota exceeded — requests will return 429 until ' + escapeHtml(body.quota.windowStart) + ' (UTC midnight)</div>';
    }
    if (usagePct >= 80 && !body.quota.exceeded) {
      html += '<div style="background:#3b3b1a;color:#ffe787;padding:10px;border-radius:6px;margin-top:14px">' + usagePct + '% of daily quota used</div>';
    }
    html += '<h3 style="margin-top:18px">Upgrade</h3><div class="toolbar">';
    for (const target of body.upgradePaths) {
      if (target === 'enterprise') continue; // sales-only
      html += '<button class="secondary" onclick="upgradeTo(\'' + target + '\')">→ ' + target + '</button>';
    }
    if (body.plan !== 'free') {
      html += '<button class="secondary" onclick="upgradeTo(\'free\')">↓ free</button>';
    }
    html += '</div><div id="upgradeStatus" class="meta" style="margin-top:6px"></div><div id="upgradeResult"></div>';
    $('planResult').innerHTML = html;
  } catch (e) {
    $('planStatus').innerHTML = '<span class="pill err">network error</span>';
    $('planResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function signup() {
  $('signupStatus').textContent = '⏳ minting…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/auth/v1/signup', { method: 'POST' });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('signupStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    if (!resp.ok) {
      $('signupResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    localStorage.setItem(KEY_STORAGE, body.apiKey);
    authStatus();
    $('signupResult').innerHTML =
      '<div style="background:#1a3b1a;color:#7ee787;padding:12px;border-radius:6px;margin-top:14px"><strong>Your API key (shown once):</strong></div>' +
      '<pre class="json">' + escapeHtml(body.apiKey) + '</pre>' +
      '<div class="meta" style="margin-top:10px">orgDid: <code>' + escapeHtml(body.orgDid) + '</code></div>' +
      '<div class="meta">' + escapeHtml(body.welcome) + '</div>' +
      '<div class="meta">' + escapeHtml(body.next) + '</div>' +
      '<div class="toolbar"><button class="secondary" onclick="navigator.clipboard.writeText(\'' + body.apiKey + '\')">Copy key</button></div>';
  } catch (e) {
    $('signupStatus').innerHTML = '<span class="pill err">network error</span>';
    $('signupResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function loadUsage() {
  const key = loadKey();
  if (!key) { $('usageStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('usageStatus').textContent = '⏳ loading…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/api/usage', {
      headers: { 'authorization': 'Bearer ' + key },
    });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('usageStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    if (!resp.ok) {
      $('usageResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    let html = '<div class="meta" style="margin:10px 0">window: <code>' + escapeHtml(body.windowStart) + '</code> → <code>' + escapeHtml(body.windowEnd) + '</code></div>';
    if (body.byMetric.length === 0) {
      html += '<div class="empty">no metered events in the last 24h yet — try /cypher / /storage / /mcp tools/call</div>';
    } else {
      html += '<table><thead><tr><th>metric</th><th>events</th><th>total qty</th><th>billed (µJPY)</th></tr></thead><tbody>';
      for (const m of body.byMetric) {
        html += '<tr><td>' + escapeHtml(m.metric) + '</td><td>' + m.eventCount + '</td><td>' + m.totalQty + '</td><td>' + m.totalBilledJpyMicro.toLocaleString() + '</td></tr>';
      }
      html += '</tbody></table>';
      html += '<div class="meta" style="margin-top:8px">total billed (last 24h): <strong>¥' + body.totalBilledJpy + '</strong></div>';
    }
    $('usageResult').innerHTML = html;
  } catch (e) {
    $('usageStatus').innerHTML = '<span class="pill err">network error</span>';
    $('usageResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function loadSchema() {
  const key = loadKey();
  if (!key) { $('schemaStatus').innerHTML = '<span class="error">✗ API key required</span>'; return; }
  $('schemaStatus').textContent = '⏳ loading…';
  const t0 = Date.now();
  try {
    const resp = await fetch('/api/schema', {
      headers: { 'authorization': 'Bearer ' + key },
    });
    const body = await resp.json();
    const ms = Date.now() - t0;
    $('schemaStatus').innerHTML = '<span class="pill ' + (resp.ok ? 'ok' : 'err') + '">' + resp.status + '</span> ' + ms + 'ms';
    if (!resp.ok) {
      $('schemaResult').innerHTML = '<pre class="json error">' + escapeHtml(JSON.stringify(body, null, 2)) + '</pre>';
      return;
    }
    let html = '<div class="meta" style="margin-top:12px">schema: <code>' + escapeHtml(body.schema) + '</code> · ' + body.tables.length + ' table' + (body.tables.length === 1 ? '' : 's') + '</div>';
    if (body.tables.length === 0) {
      html += '<div class="empty">no tables yet — try CREATE (n:NewLabel {...}) in the Cypher pane</div>';
    } else {
      for (const t of body.tables) {
        html += '<details open style="margin-top:14px"><summary><strong>' + escapeHtml(t.name) + '</strong> <span class="meta">(' + t.columns.length + ' columns)</span></summary>';
        html += '<table style="margin-top:8px"><thead><tr><th>column</th><th>type</th><th>nullable</th><th>PK</th></tr></thead><tbody>';
        for (const c of t.columns) {
          html += '<tr><td>' + escapeHtml(c.name) + '</td><td>' + escapeHtml(c.dataType) + '</td><td>' + (c.nullable ? 'YES' : 'NO') + '</td><td>' + (c.isPrimaryKey ? '✓' : '') + '</td></tr>';
        }
        html += '</tbody></table></details>';
      }
    }
    $('schemaResult').innerHTML = html;
  } catch (e) {
    $('schemaStatus').innerHTML = '<span class="pill err">network error</span>';
    $('schemaResult').innerHTML = '<pre class="json error">' + escapeHtml(e.message) + '</pre>';
  }
}

async function loadMcp() {
  try {
    const resp = await fetch('/mcp', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list' }),
    });
    const body = await resp.json();
    $('mcpResult').textContent = JSON.stringify(body.result?.tools ?? body, null, 2);
  } catch (e) {
    $('mcpResult').innerHTML = '<span class="error">' + escapeHtml(e.message) + '</span>';
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

// ── Operator: Leads pane (admin-key gated) ──────────────────────────────
const ADMIN_KEY_STORAGE = 'yatabase.adminKey';
function loadAdminKey() { return (localStorage.getItem(ADMIN_KEY_STORAGE) ?? '').trim(); }
function saveAdminKey() {
  const v = ($('adminKey').value ?? '').trim();
  if (v) localStorage.setItem(ADMIN_KEY_STORAGE, v); else localStorage.removeItem(ADMIN_KEY_STORAGE);
  adminKeyStatus(); loadLeads();
}
function clearAdminKey() {
  localStorage.removeItem(ADMIN_KEY_STORAGE);
  $('adminKey').value = '';
  adminKeyStatus();
  $('leadsArea').innerHTML = 'Admin key cleared.';
}
function adminKeyStatus() {
  const k = loadAdminKey();
  $('adminKeyStatus').innerHTML = k
    ? '<span class="pill ok">key set · ' + k.slice(0, 12) + '…</span>'
    : '<span class="pill err">no admin key</span>';
}

async function leadsAdminFetch(path, init) {
  const k = loadAdminKey();
  if (!k) throw new Error('admin key required');
  const headers = Object.assign({}, init?.headers ?? {}, {
    'x-yata-admin-key': k,
  });
  return fetch(path, Object.assign({}, init ?? {}, { headers }));
}

async function loadLeads() {
  const area = $('leadsArea');
  const k = loadAdminKey();
  if (!k) {
    area.innerHTML = '<span class="error">Set admin key first.</span>';
    return;
  }
  area.innerHTML = 'Loading…';
  const status = $('leadStatusFilter').value;
  // 'sendable' is a synthetic filter — leads that pass /api/leads/sendable
  // (approved + non-empty contact_email + valid outreach_outbox).
  const path = status === 'sendable'
    ? '/api/leads/sendable?limit=200'
    : (status ? '/api/leads?status=' + encodeURIComponent(status) + '&limit=200' : '/api/leads?limit=200');
  let resp;
  try {
    resp = await leadsAdminFetch(path);
  } catch (e) {
    area.innerHTML = '<span class="error">' + escapeHtml(e.message) + '</span>';
    return;
  }
  if (!resp.ok) {
    area.innerHTML = '<span class="error">HTTP ' + resp.status + '</span>';
    return;
  }
  const body = await resp.json();
  if (!body.count) {
    area.innerHTML = '<em>No leads in current filter.</em>';
    return;
  }
  const rows = body.leads.map((l) => {
    const fitClass = l.fit_score >= 80 ? 'ok' : (l.fit_score >= 60 ? '' : 'err');
    return ''
      + '<tr>'
      + '<td><code>' + escapeHtml(l.domain ?? '') + '</code></td>'
      + '<td>' + escapeHtml(l.company ?? '') + '</td>'
      + '<td><span class="pill ' + fitClass + '">' + (l.fit_score ?? 0) + '</span></td>'
      + '<td>' + escapeHtml(l.outreach_status ?? '') + '</td>'
      + '<td>' + escapeHtml((l.signal ?? '').slice(0, 80)) + '</td>'
      + '<td>'
      +   '<button onclick="leadEnrich(\\'' + l.vertex_id + '\\')">enrich</button> '
      +   '<button onclick="leadAction(\\'' + l.vertex_id + '\\',\\'approve\\')">approve</button> '
      +   '<button class="secondary" onclick="leadAction(\\'' + l.vertex_id + '\\',\\'dismiss\\')">dismiss</button> '
      +   '<button onclick="leadSetEmail(\\'' + l.vertex_id + '\\')">set email</button> '
      +   '<button onclick="leadSend(\\'' + l.vertex_id + '\\')">send</button>'
      + '</td>'
      + '</tr>';
  }).join('');
  area.innerHTML = ''
    + '<p class="meta">' + body.count + ' leads</p>'
    + '<table class="leads"><thead><tr>'
    + '<th>domain</th><th>company</th><th>fit</th><th>status</th><th>signal</th><th>actions</th>'
    + '</tr></thead><tbody>'
    + rows
    + '</tbody></table>';
}

async function leadAction(vertexId, action) {
  if (!confirm('Mark ' + vertexId + ' as ' + action + '?')) return;
  const path = '/api/leads/' + encodeURIComponent(vertexId) + '/' + action;
  const resp = await leadsAdminFetch(path, { method: 'POST' });
  if (!resp.ok) { alert('action failed: HTTP ' + resp.status); return; }
  await loadLeads();
}

async function leadSetEmail(vertexId) {
  const email = prompt('contact_email for ' + vertexId + ' (leave empty to clear):');
  if (email === null) return;
  const resp = await leadsAdminFetch('/api/leads/' + encodeURIComponent(vertexId) + '/contact', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email: email.trim() }),
  });
  if (!resp.ok) {
    const t = await resp.text();
    alert('failed: ' + t.slice(0, 240));
    return;
  }
  await loadLeads();
}

async function leadEnrich(vertexId) {
  const resp = await leadsAdminFetch('/api/leads/' + encodeURIComponent(vertexId) + '/enrich', { method: 'POST' });
  const body = await resp.json();
  if (!resp.ok) {
    alert('enrich failed (HTTP ' + resp.status + '): ' + (body.message ?? body.error ?? '').slice(0, 240));
    return;
  }
  const lines = [
    'Domain: ' + body.domain,
    'HTTP:   ' + body.http_status + ' (' + body.duration_ms + ' ms)',
    'Best:   ' + (body.best_email || '(none found)'),
    'Stack:  ' + (body.tech_stack && body.tech_stack.length ? body.tech_stack.join(', ') : '(none)'),
    'Saved:  ' + (body.persisted ? 'yes' : 'no'),
  ];
  if (body.error) lines.push('Error:  ' + body.error);
  alert(lines.join('\\n'));
  await loadLeads();
}

async function leadSend(vertexId) {
  if (!confirm('Send the approved draft for ' + vertexId + '?\\n\\nIf RESEND_API_KEY is unset on the Worker, this returns a dry-run preview only.')) return;
  const resp = await leadsAdminFetch('/api/leads/' + encodeURIComponent(vertexId) + '/send', { method: 'POST' });
  const body = await resp.json();
  if (!resp.ok) {
    alert('send failed (HTTP ' + resp.status + '):\\n' + (body.message ?? body.error ?? JSON.stringify(body)).slice(0, 400));
    return;
  }
  if (body.dryRun) {
    const p = body.preview || {};
    alert('DRY-RUN preview (RESEND_API_KEY not set on Worker):\\n\\n'
      + 'From:    ' + p.from + '\\n'
      + 'To:      ' + p.to + '\\n'
      + 'Subject: ' + p.subject + '\\n\\n'
      + (p.body || '').slice(0, 800));
    return;
  }
  alert('SENT — Resend id: ' + (body.resend_id ?? 'unknown'));
  await loadLeads();
}

async function leadsBatchSend(dryPreview) {
  if (!loadAdminKey()) { alert('Set admin key first.'); return; }
  // Probe how many sendable leads exist first so the confirm dialog is honest.
  const probe = await leadsAdminFetch('/api/leads/sendable?limit=50');
  if (!probe.ok) { alert('Failed to read sendable list (HTTP ' + probe.status + ')'); return; }
  const probeBody = await probe.json();
  const count = probeBody.count ?? 0;
  if (count === 0) {
    alert('No sendable leads. Approve some via the per-row "approve" button + set contact_email first.');
    return;
  }
  const label = dryPreview ? 'preview-as-dry-run (no Resend call attempted)' : 'send (will hit Resend if RESEND_API_KEY is set on the Worker)';
  if (!confirm('Batch-' + label + ' for ' + count + ' lead(s)?')) return;

  const area = $('batchResult');
  area.innerHTML = 'Firing batch over ' + count + ' lead(s)…';
  const resp = await leadsAdminFetch('/api/leads/send-batch', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ limit: count }),
  });
  if (!resp.ok) { area.innerHTML = '<span class="error">batch failed: HTTP ' + resp.status + '</span>'; return; }
  const body = await resp.json();
  const s = body.summary || {};
  const lines = [
    '<p class="meta">Batch result: <strong>' + (s.targets ?? 0) + '</strong> targets · <strong>' + (s.sent ?? 0) + '</strong> sent · <strong>' + (s.dry_run ?? 0) + '</strong> dry-run · <strong>' + (s.failed ?? 0) + '</strong> failed · resend_wired=' + (s.resend_wired ? 'yes' : 'no') + '</p>',
    '<table class="leads"><thead><tr><th>vertex_id</th><th>ok</th><th>status</th><th>resend_id</th><th>error</th></tr></thead><tbody>',
  ];
  for (const r of body.results || []) {
    lines.push(
      '<tr>'
      + '<td><code>' + escapeHtml(r.vertex_id) + '</code></td>'
      + '<td>' + (r.ok ? '<span class="pill ok">ok</span>' : '<span class="pill err">fail</span>') + '</td>'
      + '<td>' + r.status + (r.dryRun ? ' (dry)' : '') + '</td>'
      + '<td>' + escapeHtml(r.resend_id ?? '') + '</td>'
      + '<td>' + escapeHtml((r.error ?? '').slice(0, 120)) + '</td>'
      + '</tr>'
    );
  }
  lines.push('</tbody></table>');
  area.innerHTML = lines.join('');
  await loadLeads();
}

// ── BMC pane handlers ──
const BMC_KEYS = [
  ['customerSegments',      'Customer segments'],
  ['valuePropositions',     'Value propositions'],
  ['channels',              'Channels'],
  ['customerRelationships', 'Customer relationships'],
  ['revenueStreams',        'Revenue streams'],
  ['keyResources',          'Key resources'],
  ['keyActivities',         'Key activities'],
  ['keyPartnerships',       'Key partnerships'],
  ['costStructure',         'Cost structure'],
];

async function bmcBootstrap() {
  if (!loadAdminKey()) { alert('Set admin key in Leads pane first.'); return; }
  const r = await leadsAdminFetch('/_bmc/bootstrap', { method: 'POST' });
  const b = await r.json();
  alert('bootstrap: ' + (b.ok ? 'OK · ' + (b.tables||[]).map((t)=>t.name+'='+(t.ok?'✓':'✗')).join(', ') : 'failed: ' + JSON.stringify(b)));
  bmcRefresh();
}

async function bmcRefresh() {
  if (!loadAdminKey()) { $('bmcStatus').innerHTML = '<span class="pill err">no admin key</span>'; return; }
  $('bmcStatus').innerHTML = 'loading…';
  await Promise.all([bmcLoadState(), bmcLoadHypotheses(), bmcLoadIterations(), bmcLoadDecisions()]);
  $('bmcStatus').innerHTML = 'loaded ' + new Date().toISOString();
}

async function bmcLoadState() {
  const r = await leadsAdminFetch('/_bmc/state');
  if (r.status === 404) {
    $('bmcVersion').textContent = '—';
    $('bmcCanvas').innerHTML = '<em>No BMC state yet. POST /_bmc/state with a v1 canvas (9 blocks each with bullets[]).</em>';
    return;
  }
  if (!r.ok) { $('bmcCanvas').innerHTML = '<span class="error">load failed: HTTP ' + r.status + '</span>'; return; }
  const body = await r.json();
  const head = body.head || {};
  const canvas = head.canvas || {};
  $('bmcVersion').textContent = head.version ?? '?';
  $('bmcCanvasMeta').textContent = 'by ' + (head.created_by || '?') + ' · ' + (head.created_at || '') + ' · rationale: ' + (head.rationale || '—');
  const cells = BMC_KEYS.map(([k, label]) => {
    const b = canvas[k] || { bullets: [] };
    const items = (b.bullets || []).map((s) => '<li>' + escapeHtml(s) + '</li>').join('');
    return '<div class="bmc-cell"><h4>' + escapeHtml(label) + '</h4><ul>' + (items || '<li><em>—</em></li>') + '</ul></div>';
  }).join('');
  $('bmcCanvas').innerHTML = cells;
}

async function bmcLoadHypotheses() {
  const status = $('bmcHypFilter').value;
  const qs = status ? '?status=' + encodeURIComponent(status) + '&limit=50' : '?limit=50';
  const r = await leadsAdminFetch('/_bmc/hypotheses' + qs);
  if (!r.ok) { $('bmcHypotheses').innerHTML = '<span class="error">load failed</span>'; return; }
  const body = await r.json();
  if (!body.count) { $('bmcHypotheses').innerHTML = '<em>No hypotheses in this filter.</em>'; return; }
  const rows = body.hypotheses.map((h) => {
    const statusPill = h.status === 'active' ? 'ok' : (h.status === 'killed' ? 'err' : 'warn');
    return '<tr>'
      + '<td><code>' + escapeHtml(h.slug) + '</code></td>'
      + '<td>' + escapeHtml(h.block) + '</td>'
      + '<td>' + escapeHtml((h.statement || '').slice(0, 80)) + '</td>'
      + '<td>' + h.threshold + ' (baseline ' + h.baseline + ')</td>'
      + '<td>' + escapeHtml((h.deadline_iso || '').slice(0, 10)) + '</td>'
      + '<td><span class="pill ' + statusPill + '">' + escapeHtml(h.status) + '</span></td>'
      + '<td>'
      +   (h.status === 'pending' ? '<button onclick="bmcActivate(\\'' + h.slug + '\\')">activate</button> ' : '')
      +   (h.status !== 'killed' ? '<button class="secondary" onclick="bmcKill(\\'' + h.slug + '\\')">kill</button>' : '')
      + '</td>'
      + '</tr>';
  }).join('');
  $('bmcHypotheses').innerHTML = ''
    + '<table class="leads"><thead><tr>'
    + '<th>slug</th><th>block</th><th>statement</th><th>threshold</th><th>deadline</th><th>status</th><th>actions</th>'
    + '</tr></thead><tbody>' + rows + '</tbody></table>';
}

async function bmcLoadIterations() {
  const r = await leadsAdminFetch('/_bmc/iterations?limit=20');
  if (!r.ok) { $('bmcIterations').innerHTML = '<span class="error">load failed</span>'; return; }
  const body = await r.json();
  if (!body.count) { $('bmcIterations').innerHTML = '<em>No iterations yet. The LangGraph bmc_iteration cron will populate.</em>'; return; }
  const rows = body.iterations.map((it) =>
    '<tr><td>' + escapeHtml((it.created_at || '').slice(0, 19)) + '</td>'
    + '<td><code>' + escapeHtml(it.hypothesis_slug) + '</code></td>'
    + '<td>v' + it.bmc_version_in + ' → v' + it.bmc_version_out + '</td>'
    + '<td>' + it.measured_value + '</td>'
    + '<td><span class="pill ' + (it.passed ? 'ok' : 'err') + '">' + (it.passed ? 'pass' : 'fail') + '</span></td>'
    + '<td>' + escapeHtml((it.notes || '').slice(0, 60)) + '</td></tr>'
  ).join('');
  $('bmcIterations').innerHTML = '<table class="leads"><thead><tr><th>when</th><th>hypothesis</th><th>BMC v</th><th>measured</th><th>passed</th><th>notes</th></tr></thead><tbody>' + rows + '</tbody></table>';
}

async function bmcLoadDecisions() {
  const r = await leadsAdminFetch('/_bmc/decisions?limit=20');
  if (!r.ok) { $('bmcDecisions').innerHTML = '<span class="error">load failed</span>'; return; }
  const body = await r.json();
  if (!body.count) { $('bmcDecisions').innerHTML = '<em>No decisions yet.</em>'; return; }
  const rows = body.decisions.map((d) => {
    const cls = d.action === 'persevere' ? 'ok' : d.action === 'kill' ? 'err' : 'warn';
    return '<tr><td>' + escapeHtml((d.created_at || '').slice(0, 19)) + '</td>'
      + '<td><code>' + escapeHtml(d.hypothesis_slug) + '</code></td>'
      + '<td><span class="pill ' + cls + '">' + escapeHtml(d.action) + '</span></td>'
      + '<td>' + escapeHtml(d.authored_by) + '</td>'
      + '<td>' + escapeHtml((d.rationale || '').slice(0, 100)) + '</td></tr>';
  }).join('');
  $('bmcDecisions').innerHTML = '<table class="leads"><thead><tr><th>when</th><th>hypothesis</th><th>action</th><th>by</th><th>rationale</th></tr></thead><tbody>' + rows + '</tbody></table>';
}

async function bmcActivate(slug) {
  if (!confirm('Activate hypothesis ' + slug + '? The next bmc_iteration cron will start measuring it.')) return;
  const r = await leadsAdminFetch('/_bmc/hypotheses/' + encodeURIComponent(slug) + '/activate', { method: 'POST' });
  if (!r.ok) { alert('activate failed: HTTP ' + r.status); return; }
  await bmcLoadHypotheses();
}
async function bmcKill(slug) {
  if (!confirm('Kill hypothesis ' + slug + '? It will be excluded from future iterations.')) return;
  const r = await leadsAdminFetch('/_bmc/hypotheses/' + encodeURIComponent(slug) + '/kill', { method: 'POST' });
  if (!r.ok) { alert('kill failed: HTTP ' + r.status); return; }
  await bmcLoadHypotheses();
}

async function outboxRetryFailed() {
  if (!loadAdminKey()) { alert('Set admin key first.'); return; }
  if (!confirm('Retry all vertex_email_outbox rows with status=failed|pending from the last 24h?\\n\\nWithout RESEND_API_KEY on the Worker: returns candidate list without attempting send.')) return;
  const area = $('batchResult');
  area.innerHTML = 'Retrying failed/pending outbox rows…';
  const resp = await leadsAdminFetch('/api/outbox/retry-failed', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ window_hours: 24, limit: 50 }),
  });
  if (!resp.ok) { area.innerHTML = '<span class="error">retry failed: HTTP ' + resp.status + '</span>'; return; }
  const body = await resp.json();
  const lines = [
    '<p class="meta">Outbox retry: <strong>' + (body.tried||0) + '</strong> tried · <strong>' + (body.sent||0) + '</strong> sent · <strong>' + (body.still_failed||0) + '</strong> still-failed · <strong>' + (body.skipped||0) + '</strong> skipped · resend_wired=' + (body.resend_wired ? 'yes' : 'no') + '</p>',
    '<table class="leads"><thead><tr><th>vertex_id</th><th>kind</th><th>recipient</th><th>was</th><th>now</th><th>resend_id / error</th></tr></thead><tbody>',
  ];
  for (const r of body.per_row || []) {
    const okCls = r.status_out === 'sent' ? 'ok' : (r.status_out === 'failed' ? 'err' : 'warn');
    lines.push(
      '<tr>'
      + '<td><code>' + escapeHtml((r.vertex_id||'').slice(0,40)) + '</code></td>'
      + '<td>' + escapeHtml(r.kind||'') + '</td>'
      + '<td>' + escapeHtml(r.recipient||'') + '</td>'
      + '<td>' + escapeHtml(r.status_in||'') + '</td>'
      + '<td><span class="pill ' + okCls + '">' + escapeHtml(r.status_out||'') + '</span></td>'
      + '<td>' + escapeHtml((r.resend_id || r.error || '').slice(0,80)) + '</td>'
      + '</tr>'
    );
  }
  lines.push('</tbody></table>');
  area.innerHTML = lines.join('');
}

async function bmcIterateNow() {
  if (!loadAdminKey()) { alert('Set admin key first.'); return; }
  const area = $('bmcIterateResult');
  area.innerHTML = 'Firing one BMC iteration cycle…';
  const r = await leadsAdminFetch('/_bmc/iterate', { method: 'POST' });
  if (!r.ok) { area.innerHTML = '<span class="error">iterate failed: HTTP ' + r.status + '</span>'; return; }
  const body = await r.json();
  const picked = body.picked;
  const meas = body.measurement || {};
  const evalv = body.evaluation || {};
  const dec = body.decision || {};
  const lines = ['<p class="meta">' + escapeHtml(body.notes || '') + '</p>'];
  if (picked) {
    lines.push('<table class="leads"><thead><tr><th>field</th><th>value</th></tr></thead><tbody>');
    lines.push('<tr><td>hypothesis</td><td><code>' + escapeHtml(picked.slug) + '</code></td></tr>');
    lines.push('<tr><td>block</td><td>' + escapeHtml(picked.block) + '</td></tr>');
    lines.push('<tr><td>iteration #</td><td>' + picked.iteration_no + '</td></tr>');
    lines.push('<tr><td>threshold</td><td>' + picked.threshold + '</td></tr>');
    lines.push('<tr><td>measured value</td><td><strong>' + (meas.value ?? '?') + '</strong></td></tr>');
    lines.push('<tr><td>sample size</td><td>' + (meas.sample ?? '?') + '</td></tr>');
    lines.push('<tr><td>source</td><td><code>' + escapeHtml(meas.source ?? '') + '</code></td></tr>');
    if (meas.error) lines.push('<tr><td>measurement error</td><td><span class="pill err">' + escapeHtml(meas.error) + '</span></td></tr>');
    lines.push('<tr><td>passed</td><td><span class="pill ' + (evalv.passed ? 'ok' : 'err') + '">' + (evalv.passed ? 'yes' : 'no') + '</span></td></tr>');
    lines.push('<tr><td>deadline reached</td><td>' + (evalv.deadline_reached ? 'yes' : 'no') + '</td></tr>');
    lines.push('<tr><td>min sample reached</td><td>' + (evalv.min_sample_reached ? 'yes' : 'no') + '</td></tr>');
    const decCls = dec.action === 'persevere' ? 'ok' : dec.action === 'kill' ? 'err' : 'warn';
    lines.push('<tr><td>decision</td><td><span class="pill ' + decCls + '">' + escapeHtml(dec.action ?? '?') + '</span></td></tr>');
    lines.push('<tr><td>rationale</td><td>' + escapeHtml(dec.rationale ?? '') + '</td></tr>');
    lines.push('</tbody></table>');
  } else {
    lines.push('<p class="meta"><em>Loop is idle — no active hypothesis. Add one via the backlog table above + click activate.</em></p>');
  }
  area.innerHTML = lines.join('');
  // Refresh iteration + decision tables so the new rows appear.
  await Promise.all([bmcLoadIterations(), bmcLoadDecisions(), bmcLoadHypotheses()]);
}

async function bmcAddHypothesis() {
  const slug = prompt('slug (e.g. H1-cursor-mcp-listing):'); if (!slug) return;
  const block = prompt('block (one of: customerSegments / valuePropositions / channels / customerRelationships / revenueStreams / keyResources / keyActivities / keyPartnerships / costStructure):');
  if (!block) return;
  const statement = prompt('statement (the hypothesis):'); if (!statement) return;
  const metric = prompt('metric (short id, e.g. signup_count_24h):'); if (!metric) return;
  const metric_query = prompt('metric_query (e.g. sql:vertex_signup_count_window):'); if (!metric_query) return;
  const threshold = parseFloat(prompt('threshold (pass if measured ≥ this):') ?? '0');
  const baseline = parseFloat(prompt('baseline (current value, optional):') ?? '0');
  const deadline_iso = prompt('deadline ISO (e.g. 2026-06-01T00:00:00Z):'); if (!deadline_iso) return;
  const min_sample = parseInt(prompt('min_sample (events needed before we evaluate):') ?? '10', 10);

  const r = await leadsAdminFetch('/_bmc/hypotheses', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ slug, block, statement, metric, metric_query, threshold, baseline, deadline_iso, min_sample }),
  });
  if (!r.ok) { const t = await r.text(); alert('add failed: ' + t.slice(0, 200)); return; }
  await bmcLoadHypotheses();
}

authStatus();
</script>
</body>
</html>`;

export function studioResponse(): Response {
  return new Response(STUDIO_HTML, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "public, max-age=300",
      "x-yatabase-surface": "studio",
    },
  });
}
