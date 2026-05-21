// team.ts — public team page at /team. Shows the four resident AI actors
// (chikada / tanaka / nishino / sakamoto) with role, DID, description,
// and last-7d run count. Differentiator surface for prospects:
// "this product is operated by a transparent AI team, not a human SDR
// pretending to be a chatbot."
//
// Pulls roster from src/agents/registry.ts. Per-agent run counts come
// from vertex_yata_agent_run. Public, no auth, edge-cached 60 s.

import { listAgents } from "./agents/registry";

interface AnyDb {}
interface SqlExec<R = unknown> { execute(db: AnyDb): Promise<R>; }
interface SqlTag {
  (parts: TemplateStringsArray, ...vals: unknown[]): SqlExec<{ rows: Array<Record<string, unknown>> }>;
}

export interface TeamEnv {
  HYPERDRIVE?: unknown;
}

async function loadDb(env: TeamEnv): Promise<{ db: AnyDb; sql: SqlTag } | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    const db = (sdk as { createKyselyDb: (h: unknown) => unknown }).createKyselyDb(
      env.HYPERDRIVE as never,
    ) as AnyDb;
    const sql = (sdk as { sql?: SqlTag }).sql ?? null;
    if (!sql) return null;
    return { db, sql };
  } catch {
    return null;
  }
}

interface AgentActivity {
  runs_7d: number;
  ok_7d: number;
  last_iso: string;
}

async function fetchActivityByAgent(env: TeamEnv): Promise<Record<string, AgentActivity>> {
  const r = await loadDb(env);
  if (!r) return {};
  const { db, sql } = r;
  const since = Date.now() - 7 * 24 * 3600 * 1000;
  try {
    const q = sql`
      SELECT agent_name,
             COUNT(*) AS runs,
             SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) AS ok,
             MAX(ts_ms) AS last_ts
      FROM vertex_yata_agent_run
      WHERE ts_ms >= ${since}
      GROUP BY agent_name
    `;
    const res = await q.execute(db);
    const out: Record<string, AgentActivity> = {};
    for (const row of res.rows ?? []) {
      const lastTsMs = Number(row.last_ts ?? 0);
      out[String(row.agent_name)] = {
        runs_7d: Number(row.runs ?? 0),
        ok_7d: Number(row.ok ?? 0),
        last_iso: lastTsMs > 0 ? new Date(lastTsMs).toISOString() : "",
      };
    }
    return out;
  } catch (e) {
    console.warn("[yata][team] activity query failed:", e);
    return {};
  }
}

const ROLE_AVATARS: Record<string, string> = {
  dev: "🛠",
  qa: "🔬",
  sales: "📣",
  cs: "🤝",
};

const ROLE_LONG: Record<string, { ja: string; en: string }> = {
  dev:   { ja: "開発",       en: "Engineering" },
  qa:    { ja: "QA",         en: "Quality / Reliability" },
  sales: { ja: "セールス",   en: "Sales / GTM" },
  cs:    { ja: "CS",         en: "Customer Success" },
};

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export async function teamResponse(env: TeamEnv): Promise<Response> {
  const roster = listAgents();
  const activity = await fetchActivityByAgent(env);

  const cards = roster.map((a) => {
    const role = ROLE_LONG[a.role] ?? { ja: a.role, en: a.role };
    const stat = activity[a.name];
    const runs = stat?.runs_7d ?? 0;
    const ok = stat?.ok_7d ?? 0;
    const last = stat?.last_iso ?? "—";
    const okPct = runs > 0 ? Math.round((ok / runs) * 100) : 0;
    return `
      <article class="card">
        <header class="card-h">
          <span class="avatar">${ROLE_AVATARS[a.role] ?? "🤖"}</span>
          <div>
            <h3>${escapeHtml(a.displayName)}</h3>
            <p class="role">${escapeHtml(role.en)} · ${escapeHtml(role.ja)}</p>
          </div>
        </header>
        <p class="desc">${escapeHtml(a.description)}</p>
        <div class="meta">
          <div><span class="lbl">DID</span><br/><code>${escapeHtml(a.did)}</code></div>
          <div><span class="lbl">Last 7 d</span><br/><strong>${runs}</strong> runs · ${okPct}% ok</div>
          <div><span class="lbl">Last fire</span><br/>${escapeHtml(last)}</div>
        </div>
      </article>`;
  }).join("");

  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Team — Yatabase</title>
<meta name="description" content="The four resident AI actors that operate yatabase.gftd.ai: chikada (dev), tanaka (qa), nishino (sales), sakamoto (cs). Path-based DIDs, public audit trail." />
<style>
  body{margin:0;font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:980px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  h1{font-size:32px;letter-spacing:-.02em;margin:24px 0 8px}
  p.lede{font-size:17px;color:#475569;max-width:680px;margin:0 0 24px}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:18px}
  .card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:22px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .card-h{display:flex;gap:14px;align-items:center;margin-bottom:10px}
  .avatar{font-size:32px;flex:0 0 auto}
  .card h3{margin:0;font-size:18px}
  .role{margin:2px 0 0;font-size:13px;color:#64748b}
  .desc{font-size:14px;color:#334155;margin:8px 0 12px}
  .meta{display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;color:#475569;border-top:1px solid #e2e8f0;padding-top:10px}
  .meta .lbl{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em}
  .meta code{font-size:11px;background:#f1f5f9;padding:1px 4px;border-radius:3px;word-break:break-all}
  .meta div:nth-child(1){grid-column:1/-1}
  section{padding:32px 0;border-top:1px solid #e2e8f0;margin-top:32px}
  section h2{font-size:20px;margin:0 0 12px;letter-spacing:-.01em}
  pre{background:#0f172a;color:#e2e8f0;padding:14px 18px;border-radius:8px;font:12px/1.5 ui-monospace,SF Mono,Menlo,Consolas,monospace;overflow-x:auto}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
  footer a{color:#0ea5e9;text-decoration:none}
</style>
</head>
<body>

<header>
  <a href="/" class="logo" style="text-decoration:none;color:inherit">y<span>at</span>abase</a>
  <nav>
    <a href="/">Home</a>
    <a href="/studio">Studio</a>
    <a href="/status">Status</a>
    <a href="/.well-known/agent.json">.well-known</a>
  </nav>
</header>

<main>

<h1>The Yatabase team</h1>
<p class="lede">
  Four resident AI actors operate this service end-to-end. Each has a path-based DID,
  a single role, and a public audit trail in <code>vertex_yata_agent_run</code>.
  Run counts below are real-time from RisingWave.
</p>

<div class="grid">
  ${cards}
</div>

<section>
  <h2>How the team works</h2>
  <p>Trigger any agent manually with the operator key:</p>
  <pre>curl -X POST https://yatabase.gftd.ai/_agents/{name}/run \\
  -H "x-yata-admin-key: \${YATA_AGENT_ADMIN_KEY}" \\
  -d '{"dryRun": true}'</pre>
  <p style="margin-top:14px">
    See the public roster at <a href="/_agents/list" style="color:#0ea5e9">/_agents/list</a>.
    Audit trail — last N runs (admin-keyed): <a href="/_agents/recent" style="color:#0ea5e9">/_agents/recent</a>.
  </p>
</section>

<section>
  <h2>Operating entity</h2>
  <p>
    <strong>etz hayim</strong> (運営法人) operates the service. <strong>Gftd Japan株式会社</strong>
    (T9007028460042 — 適格請求書登録番号) is the vendor. Path-based DIDs under
    <code>did:web:yatabase.gftd.ai:actor:*</code> represent the AI roles, all controlled
    by the platform DID <code>did:web:yatabase.gftd.ai</code>.
  </p>
  <p>
    The team is unofficial &mdash; agents do not represent any third-party organization
    referenced in MCP discovery responses. They are an AI Agent system per the AT
    Protocol Lexicon profile.
  </p>
</section>

</main>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.gftd.ai</a> · <a href="/status">/status</a> · <a href="/.well-known/agent.json">/.well-known/agent.json</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "team",
      "cache-control": "public, max-age=60, s-maxage=60",
    },
  });
}
