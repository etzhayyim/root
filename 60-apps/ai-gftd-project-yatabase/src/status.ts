// status.ts — public status page at /status.
//
// Queries vertex_yata_qa_run (tanaka's probes) for the last 24h and
// vertex_yata_agent_run (all 4 actors) for the last 7d. No tenant data
// exposed — only platform-level health metrics.
//
// Edge-cached 60s. Public, no auth. Acts as the trust signal for
// prospects evaluating yatabase.

interface AnyDb {}
interface SqlExec<R = unknown> { execute(db: AnyDb): Promise<R>; }
interface SqlTag {
  (parts: TemplateStringsArray, ...vals: unknown[]): SqlExec<{ rows: Array<Record<string, unknown>> }>;
}

export interface StatusEnv {
  HYPERDRIVE?: unknown;
  YATA_VERSION?: string;
}

async function loadDb(env: StatusEnv): Promise<{ db: AnyDb; sql: SqlTag } | null> {
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

interface ProbeStat {
  path: string;
  total: number;
  ok: number;
  avg_latency_ms: number;
  pass_pct: number;
  status: "ok" | "degraded" | "down";
}

interface AgentStat {
  name: string;
  runs_7d: number;
  ok_7d: number;
  last_run_at: string;
  last_run_status: string;
}

async function fetchProbeStats(env: StatusEnv): Promise<ProbeStat[]> {
  const r = await loadDb(env);
  if (!r) return [];
  const { db, sql } = r;
  const since = Date.now() - 24 * 3600 * 1000;
  try {
    const q = sql`
      SELECT path,
             COUNT(*)                AS total,
             SUM(CASE WHEN ok = 1 THEN 1 ELSE 0 END) AS ok,
             AVG(latency_ms)         AS avg_latency_ms
      FROM vertex_yata_qa_run
      WHERE ts_ms >= ${since}
      GROUP BY path
      ORDER BY path ASC
    `;
    const res = await q.execute(db);
    return (res.rows ?? []).map((row) => {
      const total = Number(row.total ?? 0);
      const ok = Number(row.ok ?? 0);
      const pass = total > 0 ? (ok / total) * 100 : 0;
      const status: ProbeStat["status"] = pass >= 99 ? "ok" : pass >= 80 ? "degraded" : "down";
      return {
        path: String(row.path ?? ""),
        total,
        ok,
        avg_latency_ms: Math.round(Number(row.avg_latency_ms ?? 0)),
        pass_pct: Math.round(pass * 10) / 10,
        status,
      };
    });
  } catch (e) {
    console.warn("[yata][status] probe stats query failed:", e);
    return [];
  }
}

async function fetchAgentStats(env: StatusEnv): Promise<AgentStat[]> {
  const r = await loadDb(env);
  if (!r) return [];
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
      ORDER BY agent_name ASC
    `;
    const res = await q.execute(db);
    const out: AgentStat[] = [];
    for (const row of res.rows ?? []) {
      const lastTsMs = Number(row.last_ts ?? 0);
      let lastIso = "";
      let lastStatus = "—";
      if (lastTsMs > 0) {
        lastIso = new Date(lastTsMs).toISOString();
        const lastQ = sql`
          SELECT status FROM vertex_yata_agent_run
          WHERE agent_name = ${String(row.agent_name)} AND ts_ms = ${lastTsMs}
          LIMIT 1
        `;
        try {
          const lastRes = await lastQ.execute(db);
          if ((lastRes.rows ?? []).length > 0) {
            lastStatus = String(lastRes.rows[0].status ?? "—");
          }
        } catch { /* leave as — */ }
      }
      out.push({
        name: String(row.agent_name ?? ""),
        runs_7d: Number(row.runs ?? 0),
        ok_7d: Number(row.ok ?? 0),
        last_run_at: lastIso,
        last_run_status: lastStatus,
      });
    }
    return out;
  } catch (e) {
    console.warn("[yata][status] agent stats query failed:", e);
    return [];
  }
}

function probePill(p: ProbeStat): string {
  const cls = p.status === "ok" ? "ok" : p.status === "degraded" ? "warn" : "err";
  const label = p.status === "ok" ? "operational" : p.status === "degraded" ? "degraded" : "down";
  return `<span class="pill ${cls}">${label}</span>`;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export async function statusResponse(env: StatusEnv): Promise<Response> {
  const [probes, agents] = await Promise.all([fetchProbeStats(env), fetchAgentStats(env)]);
  const overall: "ok" | "degraded" | "down" = (() => {
    if (probes.length === 0) return "ok";
    const downCount = probes.filter((p) => p.status === "down").length;
    const degCount = probes.filter((p) => p.status === "degraded").length;
    if (downCount > 0) return "down";
    if (degCount > 0) return "degraded";
    return "ok";
  })();
  const overallLabel =
    overall === "ok" ? "All systems operational" : overall === "degraded" ? "Degraded performance" : "Active incident";
  const overallCls = overall === "ok" ? "ok" : overall === "degraded" ? "warn" : "err";

  const probeRows = probes.length === 0
    ? '<tr><td colspan="4"><em>No probe data in last 24 h. <a href="/_agents/list">Agent roster</a> still public.</em></td></tr>'
    : probes.map((p) => `
        <tr>
          <td><code>${escapeHtml(p.path)}</code></td>
          <td>${probePill(p)}</td>
          <td>${p.pass_pct}% (${p.ok}/${p.total})</td>
          <td>${p.avg_latency_ms} ms</td>
        </tr>`).join("");

  const agentRows = agents.length === 0
    ? '<tr><td colspan="5"><em>No agent runs in last 7 d. <a href="/_agents/list">Roster</a>.</em></td></tr>'
    : agents.map((a) => `
        <tr>
          <td><strong>${escapeHtml(a.name)}</strong></td>
          <td>${a.runs_7d}</td>
          <td>${a.ok_7d}/${a.runs_7d}</td>
          <td>${escapeHtml(a.last_run_at || "—")}</td>
          <td>${escapeHtml(a.last_run_status)}</td>
        </tr>`).join("");

  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Status — Yatabase</title>
<meta name="description" content="Live operational status for yatabase.gftd.ai. Probe results, agent activity, version." />
<style>
  body{margin:0;font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:980px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  .banner{padding:32px 24px;border-radius:12px;text-align:center;margin:24px 0;font-size:18px;font-weight:600}
  .banner.ok{background:#ecfdf5;color:#047857;border:1px solid #6ee7b7}
  .banner.warn{background:#fefce8;color:#a16207;border:1px solid #fcd34d}
  .banner.err{background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5}
  h2{font-size:20px;letter-spacing:-.01em;margin:32px 0 12px}
  table{width:100%;border-collapse:collapse;font-size:14px;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #e2e8f0}
  th{font-weight:600;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:.06em;background:#f8fafc}
  tr:last-child td{border-bottom:0}
  .pill{display:inline-block;padding:2px 10px;font-size:12px;border-radius:12px;font-weight:600}
  .pill.ok{background:#dcfce7;color:#166534}
  .pill.warn{background:#fef3c7;color:#92400e}
  .pill.err{background:#fee2e2;color:#991b1b}
  code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:13px}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
  footer p{margin:6px 0}
  footer a{color:#0ea5e9;text-decoration:none}
</style>
</head>
<body>

<header>
  <a href="/" class="logo" style="text-decoration:none;color:inherit">y<span>at</span>abase</a>
  <nav>
    <a href="/">Home</a>
    <a href="/studio">Studio</a>
    <a href="/team">Team</a>
    <a href="/.well-known/agent.json">.well-known</a>
  </nav>
</header>

<main>

<div class="banner ${overallCls}">
  ${overall === "ok" ? "✓" : overall === "degraded" ? "⚠" : "✗"} ${overallLabel}
</div>

<h2>Public surface health (last 24 h)</h2>
<p style="font-size:13px;color:#64748b;margin:0 0 12px">
  Tanaka (QA agent) probes these surfaces from inside the Worker every cron tick. Pass rate &amp; avg latency over the last 24 h.
</p>
<table>
  <thead>
    <tr><th>Path</th><th>Status</th><th>Pass rate</th><th>Avg latency</th></tr>
  </thead>
  <tbody>
${probeRows}
  </tbody>
</table>

<h2>AI agent activity (last 7 d)</h2>
<p style="font-size:13px;color:#64748b;margin:0 0 12px">
  Yatabase ships with four resident AI actors: <a href="/team">chikada / tanaka / nishino / sakamoto</a>.
  Each writes a row to <code>vertex_yata_agent_run</code> per fire.
</p>
<table>
  <thead>
    <tr><th>Agent</th><th>Runs</th><th>OK / Total</th><th>Last run at</th><th>Last status</th></tr>
  </thead>
  <tbody>
${agentRows}
  </tbody>
</table>

<h2>Version</h2>
<p>Worker version: <code>${escapeHtml(env.YATA_VERSION ?? "0.0.0")}</code></p>
<p>Live probes: <a href="/health">/health</a> · <a href="/_app/meta">/_app/meta</a></p>

</main>

<footer>
  <p>This page is generated from <code>vertex_yata_qa_run</code> + <code>vertex_yata_agent_run</code> in RisingWave (Vultr LAX).
     No tenant data exposed.</p>
  <p>Edge-cached 60 s. <a href="/.well-known/agent.json">agent.json</a> · <a href="/.well-known/mcp.json">mcp.json</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "status",
      "cache-control": "public, max-age=60, s-maxage=60",
    },
  });
}
