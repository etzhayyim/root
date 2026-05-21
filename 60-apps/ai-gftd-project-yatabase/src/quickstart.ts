// quickstart.ts — interactive /quickstart page.
//
// Reduces TTV from "read docs + copy curl + paste key" to "click Mint →
// copy a single curl line". The page is a self-contained SPA:
//   1. On load, restore localStorage('yatabase.apiKey') if present.
//   2. "Mint trial key" button → POST /auth/v1/signup, render apiKey,
//      orgDid, awsAccessKeyId inline, persist to localStorage.
//   3. 3 curl blocks have the key spliced in — each line is one click
//      from working.
//   4. "Run sample Cypher" runs a CREATE + MATCH against /cypher from
//      the browser using the minted key, renders the JSON response.
//
// Public, no auth. Edge-cached HTML; the actual mint call hits the
// /auth/v1/signup surface, not this page.

export function quickstartResponse(): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Quickstart — Yatabase</title>
<meta name="description" content="Mint a free Yatabase API key in your browser and run your first Cypher query in 30 seconds." />
<style>
  body{margin:0;font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:880px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;color:inherit;text-decoration:none}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  main{padding:8px 24px}
  h1{font-size:32px;letter-spacing:-.02em;margin:8px 0 4px}
  p.lede{font-size:17px;color:#475569;margin:0 0 24px}
  h2{font-size:20px;letter-spacing:-.01em;margin:32px 0 8px}
  h3{font-size:15px;margin:16px 0 4px}
  .panel{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px 20px;margin:12px 0}
  .panel.ok{border-left:3px solid #16a34a}
  .panel.warn{border-left:3px solid #fbbf24}
  .btn{display:inline-block;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;cursor:pointer;border:0}
  .btn-primary{background:#0f172a;color:#fff}
  .btn-primary:hover{background:#1e293b}
  .btn-primary:disabled{background:#94a3b8;cursor:not-allowed}
  .btn-secondary{background:#fff;border:1px solid #cbd5e1;color:#0f172a}
  .btn-secondary:hover{border-color:#0ea5e9;color:#0ea5e9}
  .key-box{display:flex;gap:8px;align-items:center;margin-top:8px;background:#0f172a;color:#fcd34d;padding:10px 12px;border-radius:6px;font:13px ui-monospace,SF Mono,Menlo,monospace;overflow-x:auto}
  .key-box .copy{background:#fcd34d;color:#0f172a;border:0;padding:4px 10px;border-radius:4px;font:11px ui-sans-serif;font-weight:600;cursor:pointer;flex-shrink:0}
  .key-box code{flex:1;white-space:nowrap;overflow-x:auto}
  pre{background:#0f172a;color:#e2e8f0;padding:14px 18px;border-radius:8px;font:13px/1.5 ui-monospace,SF Mono,Menlo,monospace;overflow-x:auto;margin:8px 0;position:relative}
  pre .c{color:#94a3b8}
  pre .k{color:#7dd3fc}
  pre .s{color:#fcd34d}
  pre .copy-pre{position:absolute;top:8px;right:8px;background:#1e293b;color:#e2e8f0;border:1px solid #334155;padding:3px 10px;border-radius:4px;font:11px ui-sans-serif;font-weight:500;cursor:pointer}
  pre .copy-pre:hover{background:#334155}
  .resp{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;margin-top:8px;font:12px/1.5 ui-monospace,SF Mono,Menlo,monospace;overflow-x:auto;max-height:300px;overflow-y:auto;white-space:pre-wrap;word-break:break-word}
  .resp.err{background:#fef2f2;border-color:#fecaca;color:#991b1b}
  .meta{font-size:12px;color:#64748b}
  code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:13px}
  a{color:#0ea5e9}
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

<main>

<h1>Quickstart</h1>
<p class="lede">
  Mint a free Yatabase API key in your browser, then run your first Cypher query —
  no signup form, no email, no credit card. Free tier is $0/month, 1,000
  api_request/day. Closes automatically after 30 days of inactivity.
</p>

<div class="panel" id="mintPanel">
  <h2 style="margin-top:0">Step 1 · Mint a trial key</h2>
  <p class="meta">Calls <code>POST /auth/v1/signup</code> from your browser. The key is shown once
     (we keep only the SHA-256 hash). It's also persisted to <code>localStorage</code> on this
     device so you don't have to re-mint on a refresh.</p>
  <button id="mintBtn" class="btn btn-primary" onclick="mintKey()">Mint trial key</button>
  <button id="forgetBtn" class="btn btn-secondary" onclick="forgetKey()" style="margin-left:6px;display:none">Forget local key</button>
  <div id="mintResult" style="display:none;margin-top:16px"></div>
</div>

<div class="panel" id="useKeyPanel" style="display:none">
  <h2 style="margin-top:0">Step 2 · Run a Cypher query</h2>
  <p>Pre-filled with your trial key. Click <strong>Run</strong> to fire it from this page (the call goes
     to <code>/cypher</code> on this same hostname — no CORS dance), or copy the curl line to a terminal.</p>

  <h3>2a. <code>CREATE</code></h3>
  <pre id="curl1"><button class="copy-pre" onclick="copyPre('curl1')">copy</button><span class="cmd">curl -X POST <span class="s">https://yatabase.gftd.ai/cypher</span> \\
  -H <span class="s">"authorization: Bearer YOUR_KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">query</span>":"CREATE (n:Demo {name:\\"hello world\\", ts:'$(date +%s)'}) RETURN n"}'</span></pre>
  <button class="btn btn-primary" onclick="runQuery('CREATE (n:Demo {name:\\'hello world\\'}) RETURN n', 'resp1')">Run from browser</button>
  <div id="resp1" class="resp" style="display:none"></div>

  <h3 style="margin-top:18px">2b. <code>MATCH</code> (read it back)</h3>
  <pre id="curl2"><button class="copy-pre" onclick="copyPre('curl2')">copy</button><span class="cmd">curl -X POST <span class="s">https://yatabase.gftd.ai/cypher</span> \\
  -H <span class="s">"authorization: Bearer YOUR_KEY"</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">query</span>":"MATCH (n:Demo) RETURN n.name LIMIT 10"}'</span></pre>
  <button class="btn btn-primary" onclick="runQuery('MATCH (n:Demo) RETURN n.name LIMIT 10', 'resp2')">Run from browser</button>
  <div id="resp2" class="resp" style="display:none"></div>

  <h3 style="margin-top:18px">2c. <code>MCP tools/list</code> (no auth on this method)</h3>
  <pre id="curl3"><button class="copy-pre" onclick="copyPre('curl3')">copy</button><span class="cmd">curl -X POST <span class="s">https://yatabase.gftd.ai/mcp</span> \\
  -H <span class="s">'content-type: application/json'</span> \\
  -d '{"<span class="k">jsonrpc</span>":"2.0","<span class="k">method</span>":"tools/list","<span class="k">id</span>":1}'</span></pre>
  <button class="btn btn-primary" onclick="runMcpList('resp3')">Run from browser</button>
  <div id="resp3" class="resp" style="display:none"></div>
</div>

<div class="panel warn" id="recoverPanel" style="display:none">
  <h2 style="margin-top:0">Step 3 · ⚠️ Attach a recovery email <em>now</em></h2>
  <p>Signup was anonymous — if you close this tab without saving the key, the tenant is unreachable.
     Attach an email so you can recover via <code>/auth/v1/recover</code> later:</p>
  <input id="recoverEmail" type="email" placeholder="you@example.com" style="padding:8px 10px;border:1px solid #cbd5e1;border-radius:6px;font:14px ui-sans-serif;width:300px" />
  <button class="btn btn-primary" onclick="attachEmail()">Attach email</button>
  <div id="attachResult" style="margin-top:8px;font:13px ui-monospace,Menlo,monospace"></div>
  <p class="meta" style="margin-top:10px">Attaching emails a 24-hour verification link. <strong>You must click the link to enable recovery</strong> — otherwise <code>/auth/v1/recover</code> silently ignores this address (so attackers can't use yatabase to spam unattached inboxes). Once verified, <code>POST /auth/v1/recover {email}</code> sends a 15-minute link that mints a fresh key. Existing keys remain valid — recovery is additive.</p>
</div>

<div class="panel" id="nextPanel" style="display:none">
  <h2 style="margin-top:0">Step 4 · Where to next</h2>
  <ul>
    <li><strong>Full reference:</strong> <a href="/docs">/docs</a> covers every surface with examples (including <a href="/docs#recovery">key recovery</a> and <a href="/docs#whoami">whoami</a>).</li>
    <li><strong>Machine-readable:</strong> <a href="/openapi.json">/openapi.json</a> — 32 paths, import into Postman / Cursor / openapi-typescript.</li>
    <li><strong>Plug into your AI stack:</strong> <a href="/integrations">/integrations</a> has 12 paste-ready setup recipes (Cursor, LangChain, Claude Desktop, …).</li>
    <li><strong>Browser console:</strong> <a href="/studio">/studio</a> uses the same key you just minted (stored in <code>localStorage.yatabase.apiKey</code>).</li>
    <li><strong>Upgrade:</strong> Once you outgrow free, <code>POST /auth/v1/upgrade</code> opens a Stripe Checkout. Manage billing via <code>POST /auth/v1/portal</code> (Stripe customer portal). Plans at <a href="/#pricing">/#pricing</a>.</li>
  </ul>
</div>

</main>

<script>
const KEY_STORAGE = 'yatabase.apiKey';
const ORG_STORAGE = 'yatabase.orgDid';

function loadKey() { return (localStorage.getItem(KEY_STORAGE) ?? '').trim(); }
function saveKey(k, org) {
  if (k) localStorage.setItem(KEY_STORAGE, k); else localStorage.removeItem(KEY_STORAGE);
  if (org) localStorage.setItem(ORG_STORAGE, org); else localStorage.removeItem(ORG_STORAGE);
}

function escapeHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderKey(key, orgDid, awsId, fromLs) {
  const result = document.getElementById('mintResult');
  result.style.display = 'block';
  result.innerHTML =
    (fromLs ? '<p class="meta">Restored from <code>localStorage</code>:</p>' :
              '<p class="meta">Minted ' + new Date().toISOString() + ':</p>') +
    '<div class="key-box">' +
      '<code>' + escapeHtml(key) + '</code>' +
      '<button class="copy" onclick="navigator.clipboard.writeText(\\'' + key + '\\')">copy</button>' +
    '</div>' +
    '<p class="meta" style="margin-top:8px">' +
      'orgDid: <code>' + escapeHtml(orgDid) + '</code><br/>' +
      (awsId ? 'awsAccessKeyId: <code>' + escapeHtml(awsId) + '</code><br/>' : '') +
      'You can revoke this any time: POST /auth/v1/revoke. Delete account (irreversible): POST /api/account/delete.' +
    '</p>';

  // Splice the key into the curl blocks.
  document.querySelectorAll('pre .cmd').forEach((node) => {
    node.innerHTML = node.innerHTML.replaceAll('YOUR_KEY', key);
  });
  document.getElementById('useKeyPanel').style.display = 'block';
  document.getElementById('recoverPanel').style.display = 'block';
  document.getElementById('nextPanel').style.display = 'block';
  document.getElementById('mintBtn').textContent = 'Mint another key';
  document.getElementById('forgetBtn').style.display = '';
}

async function attachEmail() {
  const key = loadKey();
  const email = (document.getElementById('recoverEmail').value || '').trim();
  const result = document.getElementById('attachResult');
  if (!key) { result.textContent = 'No local key — mint one first.'; return; }
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    result.textContent = 'Enter a valid email address.';
    return;
  }
  result.textContent = 'Attaching…';
  try {
    const r = await fetch('/auth/v1/attach-email', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'authorization': 'Bearer ' + key },
      body: JSON.stringify({ email }),
    });
    const body = await r.json();
    if (r.ok) {
      if (body.attachedEmailVerified) {
        result.style.color = '#047857';
        result.textContent = '✓ already verified for ' + body.attachedEmail;
      } else {
        result.style.color = '#a16207';
        result.innerHTML = '📧 attached <strong>' + body.attachedEmail + '</strong> — check your inbox and click the verification link (24h TTL). Recovery is disabled until you verify.';
      }
    } else {
      result.style.color = '#b91c1c';
      result.textContent = (body.error || 'attach failed') + ': ' + (body.message || '');
    }
  } catch (e) {
    result.style.color = '#b91c1c';
    result.textContent = 'threw: ' + (e?.message || e);
  }
}

async function mintKey() {
  const btn = document.getElementById('mintBtn');
  btn.disabled = true; btn.textContent = 'Minting…';
  try {
    const r = await fetch('/auth/v1/signup', { method: 'POST', headers: {'content-type':'application/json'}, body: '{}' });
    const body = await r.json();
    if (!body.apiKey) {
      alert('mint failed: ' + JSON.stringify(body).slice(0, 200));
      return;
    }
    saveKey(body.apiKey, body.orgDid);
    renderKey(body.apiKey, body.orgDid, body.awsAccessKeyId, false);
  } catch (e) {
    alert('mint threw: ' + (e?.message ?? e));
  } finally {
    btn.disabled = false;
  }
}

function forgetKey() {
  if (!confirm('Forget the trial key from this browser? The key itself stays valid on the server until you revoke it via /auth/v1/revoke.')) return;
  saveKey('', '');
  location.reload();
}

async function runQuery(cypher, respId) {
  const key = loadKey();
  const respEl = document.getElementById(respId);
  respEl.style.display = 'block';
  respEl.className = 'resp';
  respEl.textContent = 'Running…';
  try {
    const r = await fetch('/cypher', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'authorization': 'Bearer ' + key },
      body: JSON.stringify({ query: cypher }),
    });
    const text = await r.text();
    if (!r.ok) respEl.className = 'resp err';
    try { respEl.textContent = JSON.stringify(JSON.parse(text), null, 2); } catch { respEl.textContent = text.slice(0, 4000); }
  } catch (e) {
    respEl.className = 'resp err';
    respEl.textContent = 'fetch threw: ' + (e?.message ?? e);
  }
}

async function runMcpList(respId) {
  const respEl = document.getElementById(respId);
  respEl.style.display = 'block';
  respEl.className = 'resp';
  respEl.textContent = 'Running…';
  try {
    const r = await fetch('/mcp', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/list', id: 1 }),
    });
    const text = await r.text();
    if (!r.ok) respEl.className = 'resp err';
    try { respEl.textContent = JSON.stringify(JSON.parse(text), null, 2); } catch { respEl.textContent = text.slice(0, 4000); }
  } catch (e) {
    respEl.className = 'resp err';
    respEl.textContent = 'fetch threw: ' + (e?.message ?? e);
  }
}

function copyPre(id) {
  const node = document.getElementById(id);
  const cmd = node.querySelector('.cmd');
  const text = cmd.innerText;
  navigator.clipboard.writeText(text).then(() => {
    const btn = node.querySelector('.copy-pre');
    const orig = btn.textContent;
    btn.textContent = 'copied';
    setTimeout(() => { btn.textContent = orig; }, 1200);
  });
}

// Auto-restore if we already have a key on this device.
const existing = loadKey();
if (existing && existing.startsWith('sk_live_yata_')) {
  const org = localStorage.getItem(ORG_STORAGE) ?? '(unknown)';
  renderKey(existing, org, '', true);
}
</script>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.gftd.ai</a> · <a href="/docs">/docs</a> · <a href="/privacy">/privacy</a> · <a href="/terms">/terms</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "quickstart",
      "cache-control": "public, max-age=120, s-maxage=300",
    },
  });
}
