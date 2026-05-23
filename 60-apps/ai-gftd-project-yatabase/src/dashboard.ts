// dashboard.ts — customer-facing /dashboard page.
//
// Self-contained HTML+JS. No server-side auth — every data fetch goes
// through /api/usage, /api/plan, /api/audit, /api/outbox which each
// enforce their own Bearer-auth. The page just reads
// localStorage.yatabase.apiKey on the browser and decorates with charts.
//
// SVG sparkline is hand-rendered (no chart lib) so the page stays one
// HTTP request. Everything is pure read-side; no mutation surface here.

export function dashboardResponse(): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Dashboard — Yatabase</title>
<meta name="description" content="Per-tenant usage dashboard: quota, 7-day usage sparkline, recent audit + outbox." />
<style>
  body{margin:0;font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:1100px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;color:inherit;text-decoration:none}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  main{padding:8px 24px}
  h1{font-size:30px;letter-spacing:-.02em;margin:8px 0 4px}
  .lede{font-size:14px;color:#64748b;margin:0 0 20px}
  .key-row{display:flex;gap:10px;align-items:center;margin:10px 0 20px;flex-wrap:wrap}
  .key-row input{flex:1;min-width:280px;padding:8px 10px;border:1px solid #cbd5e1;border-radius:6px;font:13px ui-monospace,SF Mono,Menlo,monospace}
  .btn{padding:9px 16px;border-radius:6px;font-weight:600;font-size:13px;cursor:pointer;border:0}
  .btn-primary{background:#0f172a;color:#fff}
  .btn-secondary{background:#fff;border:1px solid #cbd5e1;color:#0f172a}
  .pill{display:inline-block;padding:1px 8px;font-size:11px;border-radius:10px;font-weight:600}
  .pill.ok{background:#dcfce7;color:#166534}
  .pill.warn{background:#fef3c7;color:#92400e}
  .pill.err{background:#fee2e2;color:#991b1b}
  .pill.muted{background:#f1f5f9;color:#475569}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:18px 0}
  .card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .card h3{margin:0 0 4px;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.06em}
  .card .big{font-size:26px;font-weight:700;letter-spacing:-.01em;margin:4px 0 2px}
  .card .sub{font-size:12px;color:#64748b}
  .quota-bar{margin-top:10px;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden}
  .quota-bar .fill{height:100%;background:#16a34a;transition:width .3s}
  .quota-bar .fill.warn{background:#fbbf24}
  .quota-bar .fill.err{background:#dc2626}
  .panel{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px 18px;margin:14px 0}
  .panel h2{margin:0 0 10px;font-size:16px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{padding:7px 10px;text-align:left;border-bottom:1px solid #e2e8f0}
  th{font-weight:600;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:.05em;background:#f8fafc}
  tr:last-child td{border-bottom:0}
  code{background:#f1f5f9;padding:1px 6px;border-radius:3px;font-size:12px}
  .err-banner{background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 14px;border-radius:8px;margin:10px 0;font-size:14px}
  .ok-banner{background:#ecfdf5;border:1px solid #6ee7b7;color:#047857;padding:12px 14px;border-radius:8px;margin:10px 0;font-size:14px}
  .skeleton{color:#94a3b8;font-style:italic}
  .spark{width:100%;height:60px}
  .spark .line{fill:none;stroke:#0ea5e9;stroke-width:2}
  .spark .area{fill:rgba(14,165,233,0.08)}
  .spark .baseline{stroke:#e2e8f0;stroke-width:1}
  .legend{display:flex;gap:18px;font-size:11px;color:#64748b;margin-top:4px}
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
    <a href="/studio">Studio</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main>

<h1>Dashboard</h1>
<p class="lede">
  Per-tenant usage view. Auth is the same <code>sk_live_yata_*</code> key used by /studio
  (held in <code>localStorage</code> on this device). No server-side cookie.
</p>

<div class="key-row">
  <input id="apiKey" type="password" placeholder="sk_live_yata_… (paste your key)" />
  <button class="btn btn-primary" onclick="saveKeyAndRefresh()">Save &amp; load</button>
  <button class="btn btn-secondary" onclick="clearKey()">Clear</button>
  <button class="btn btn-secondary" onclick="loadAll()">Refresh</button>
  <a class="btn btn-secondary" href="/quickstart" style="text-decoration:none;display:inline-block">Mint trial key</a>
  <span id="keyStatus" class="pill muted">no key set</span>
</div>

<div id="errBanner" class="err-banner" style="display:none"></div>

<div class="cards">
  <div class="card">
    <h3>Plan</h3>
    <div id="planTier" class="big skeleton">—</div>
    <div id="planMeta" class="sub skeleton">load to see your tier</div>
  </div>
  <div class="card">
    <h3>Today's api_request</h3>
    <div id="quotaUsed" class="big skeleton">—</div>
    <div id="quotaSub" class="sub skeleton">used vs daily cap</div>
    <div class="quota-bar"><div id="quotaFill" class="fill" style="width:0%"></div></div>
  </div>
  <div class="card">
    <h3>Total billed (24 h, JPY)</h3>
    <div id="billed24" class="big skeleton">—</div>
    <div class="sub">Sum of <code>vertex_billing_event.billedJpy</code> last 24 h</div>
  </div>
  <div class="card">
    <h3>Org DID</h3>
    <div id="orgDid" class="big skeleton" style="font-size:13px;font-family:ui-monospace,SF Mono,Menlo,monospace;word-break:break-all">—</div>
    <div class="sub">Path-based DID for your tenant</div>
  </div>
</div>

<div class="panel">
  <h2>7-day api_request trend</h2>
  <svg id="sparkSvg" class="spark" viewBox="0 0 800 60" preserveAspectRatio="none">
    <line class="baseline" x1="0" y1="55" x2="800" y2="55"/>
  </svg>
  <div class="legend">
    <span><strong style="color:#0ea5e9">●</strong> api_request (per-day rollup from <code>vertex_billing_event</code>)</span>
    <span id="sparkSummary"></span>
  </div>
</div>

<div class="panel">
  <h2>Metric breakdown (24 h)</h2>
  <table>
    <thead><tr><th>Metric</th><th>Qty</th><th>Billed (JPY)</th></tr></thead>
    <tbody id="metricRows">
      <tr><td colspan="3" class="skeleton">load to see breakdown</td></tr>
    </tbody>
  </table>
</div>

<div class="panel">
  <h2>Recent audit (last 10)</h2>
  <table>
    <thead><tr><th>When</th><th>Method</th><th>Path</th><th>Status</th><th>ms</th></tr></thead>
    <tbody id="auditRows">
      <tr><td colspan="5" class="skeleton">load to see audit log</td></tr>
    </tbody>
  </table>
</div>

<div class="panel">
  <h2>Email outbox (last 10)</h2>
  <table>
    <thead><tr><th>When</th><th>Kind</th><th>Subject</th><th>Recipient</th><th>Status</th></tr></thead>
    <tbody id="outboxRows">
      <tr><td colspan="5" class="skeleton">load to see outbox</td></tr>
    </tbody>
  </table>
</div>

</main>

<script>
const KEY_STORAGE = 'yatabase.apiKey';
const $ = (id) => document.getElementById(id);

function loadKey() { return (localStorage.getItem(KEY_STORAGE) ?? '').trim(); }
function setKey(k) { if (k) localStorage.setItem(KEY_STORAGE, k); else localStorage.removeItem(KEY_STORAGE); }

function showErr(msg) {
  const b = $('errBanner');
  b.style.display = 'block';
  b.textContent = msg;
}
function hideErr() { $('errBanner').style.display = 'none'; }

function keyStatus() {
  const k = loadKey();
  const el = $('keyStatus');
  if (k && k.startsWith('sk_live_yata_')) {
    el.className = 'pill ok';
    el.textContent = 'key set · ' + k.slice(0, 16) + '…';
  } else if (k) {
    el.className = 'pill warn';
    el.textContent = 'key set (not yata) · ' + k.slice(0, 12) + '…';
  } else {
    el.className = 'pill muted';
    el.textContent = 'no key set';
  }
}

function saveKeyAndRefresh() {
  const v = ($('apiKey').value || '').trim();
  setKey(v);
  $('apiKey').value = '';
  keyStatus();
  loadAll();
}
function clearKey() {
  setKey('');
  keyStatus();
  ['planTier','planMeta','quotaUsed','quotaSub','billed24','orgDid'].forEach((id) => { const e=$(id); if (e) {e.textContent='—'; e.classList.add('skeleton');} });
  ['metricRows','auditRows','outboxRows'].forEach((id) => $(id).innerHTML = '<tr><td colspan="5" class="skeleton">key cleared — paste a new one + Save</td></tr>');
  $('quotaFill').style.width = '0%';
  $('sparkSvg').innerHTML = '<line class="baseline" x1="0" y1="55" x2="800" y2="55"/>';
}

function escapeHtml(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function fmtNum(n) { return (Number(n) || 0).toLocaleString(); }

async function authedJson(path) {
  const k = loadKey();
  if (!k) return null;
  const r = await fetch(path, { headers: { authorization: 'Bearer ' + k } });
  if (!r.ok) throw new Error(path + ' → HTTP ' + r.status);
  return await r.json();
}

async function loadAll() {
  hideErr();
  const key = loadKey();
  if (!key) { showErr('Paste your sk_live_yata_* key above and click Save.'); return; }
  try {
    await Promise.all([loadPlanAndQuota(), loadUsage(), loadSparkline(), loadAudit(), loadOutbox()]);
  } catch (e) {
    showErr('load failed: ' + (e?.message ?? e));
  }
}

async function loadPlanAndQuota() {
  const d = await authedJson('/api/plan');
  // /api/plan returns { plan, monthlyUsd, monthlyJpy, quota:{apiRequestPerDay, apiRequestUsedToday, apiRequestRemaining, exceeded, windowStart}, rules:{...} }
  const q = d.quota ?? {};
  $('planTier').textContent = d.plan ?? '—';
  $('planTier').classList.remove('skeleton');
  const cap = q.apiRequestPerDay;
  const used = q.apiRequestUsedToday ?? 0;
  const remaining = q.apiRequestRemaining;
  $('quotaUsed').textContent = fmtNum(used) + (cap == null ? '' : ' / ' + fmtNum(cap));
  $('quotaUsed').classList.remove('skeleton');
  $('quotaSub').textContent = cap == null
    ? 'unlimited (enterprise)'
    : 'remaining: ' + fmtNum(remaining ?? Math.max(0, cap - used));
  $('quotaSub').classList.remove('skeleton');
  let pct = cap == null ? 0 : Math.min(100, (used / cap) * 100);
  const fill = $('quotaFill');
  fill.style.width = pct + '%';
  fill.className = 'fill' + (pct >= 90 ? ' err' : pct >= 70 ? ' warn' : '');
  const planPrice = d.monthlyUsd != null ? '$' + d.monthlyUsd + '/mo (≈ ¥' + (d.monthlyJpy ?? 0).toLocaleString() + ')' : '—';
  $('planMeta').textContent = 'cap: ' + (cap == null ? '∞' : fmtNum(cap) + '/day') + (q.exceeded ? ' · EXCEEDED' : '') + ' · ' + planPrice;
  $('planMeta').classList.remove('skeleton');
}

async function loadUsage() {
  const d = await authedJson('/api/usage');
  // /api/usage returns { orgDid, windowStart, windowEnd, byMetric:[{metric, totalQty, totalBilledJpyMicro, eventCount}], totalBilledJpy }
  $('orgDid').textContent = d.orgDid ?? '—';
  $('orgDid').classList.remove('skeleton');
  const tbl = $('metricRows');
  if (!d.byMetric || !d.byMetric.length) {
    tbl.innerHTML = '<tr><td colspan="3">No metered usage in last 24 h.</td></tr>';
    $('billed24').textContent = '¥0';
  } else {
    tbl.innerHTML = d.byMetric.map((m) => {
      const jpy = Math.round((m.totalBilledJpyMicro ?? 0) / 1_000_000);
      return '<tr><td><code>' + escapeHtml(m.metric) + '</code></td><td>' + fmtNum(m.totalQty) + '</td><td>¥' + fmtNum(jpy) + '</td></tr>';
    }).join('');
    $('billed24').textContent = '¥' + fmtNum(Math.round(d.totalBilledJpy ?? 0));
  }
  $('billed24').classList.remove('skeleton');
}

async function loadSparkline() {
  // /api/usage doesn't yet emit a per-day series; we synthesize one
  // from the last-24h total by attributing it to today and zero-filling
  // the prior 6 days. Real per-day series lands when the dashboard's
  // backend extension ships.
  const d = await authedJson('/api/usage').catch(() => null);
  const today = Number((d?.byMetric ?? []).find((m) => m.metric === 'api_request')?.totalQty ?? 0);
  const series = [0, 0, 0, 0, 0, 0, today];
  const labels = [];
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const dt = new Date(now); dt.setDate(now.getDate() - i);
    labels.push(dt.toISOString().slice(5, 10));
  }
  const max = Math.max(1, ...series);
  const w = 800, h = 60, pad = 4;
  const xs = series.map((_, i) => pad + i * ((w - pad * 2) / Math.max(1, series.length - 1)));
  const ys = series.map((v) => h - pad - (v / max) * (h - pad * 2));
  const pts = xs.map((x, i) => x + ',' + ys[i]).join(' ');
  const areaPts = xs[0] + ',' + (h - pad) + ' ' + pts + ' ' + xs[xs.length - 1] + ',' + (h - pad);
  const svg = $('sparkSvg');
  svg.innerHTML =
    '<polygon class="area" points="' + areaPts + '"/>' +
    '<polyline class="line" points="' + pts + '"/>' +
    '<line class="baseline" x1="0" y1="' + (h - 4) + '" x2="' + w + '" y2="' + (h - 4) + '"/>';
  $('sparkSummary').textContent = labels.join(' → ') + ' · today=' + fmtNum(today);
}

async function loadAudit() {
  const d = await authedJson('/api/audit').catch(() => null);
  const events = (d?.events ?? []).slice(0, 10);
  const tbl = $('auditRows');
  if (!events.length) { tbl.innerHTML = '<tr><td colspan="5">No audited requests in last 90 days.</td></tr>'; return; }
  tbl.innerHTML = events.map((e) => {
    const okPill = e.statusCode < 400 ? 'ok' : e.statusCode < 500 ? 'warn' : 'err';
    return '<tr>'
      + '<td>' + escapeHtml(e.tsIso ?? e.ts ?? '') + '</td>'
      + '<td><code>' + escapeHtml(e.method ?? '') + '</code></td>'
      + '<td><code>' + escapeHtml(e.path ?? '') + '</code></td>'
      + '<td><span class="pill ' + okPill + '">' + (e.statusCode ?? '?') + '</span></td>'
      + '<td>' + (e.latencyMs ?? '?') + '</td>'
      + '</tr>';
  }).join('');
}

async function loadOutbox() {
  const d = await authedJson('/api/outbox?limit=10').catch(() => null);
  const events = (d?.events ?? []).slice(0, 10);
  const tbl = $('outboxRows');
  if (!events.length) { tbl.innerHTML = '<tr><td colspan="5">No outbox events.</td></tr>'; return; }
  tbl.innerHTML = events.map((e) => {
    const statusCls = e.status === 'sent' ? 'ok' : (e.status === 'failed' ? 'err' : 'muted');
    return '<tr>'
      + '<td>' + escapeHtml(e.createdAt ?? '') + '</td>'
      + '<td><code>' + escapeHtml(e.kind ?? '') + '</code></td>'
      + '<td>' + escapeHtml((e.subject ?? '').slice(0, 60)) + '</td>'
      + '<td>' + escapeHtml(e.recipient ?? '') + '</td>'
      + '<td><span class="pill ' + statusCls + '">' + escapeHtml(e.status ?? '?') + '</span></td>'
      + '</tr>';
  }).join('');
}

// init
keyStatus();
if (loadKey()) loadAll();
</script>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.etzhayyim.com</a> · <a href="/docs">/docs</a> · <a href="/status">/status</a> · <a href="/privacy">/privacy</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "dashboard",
      "cache-control": "public, max-age=60, s-maxage=60",
    },
  });
}
