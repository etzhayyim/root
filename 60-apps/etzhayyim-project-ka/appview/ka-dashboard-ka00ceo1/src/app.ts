// ka.etzhayyim.com thin edge facade. Strategy dashboard queries run in AgentGateway MCP + pod-side LangServer.

interface SecretBinding { get(): Promise<string>; }
interface Env { DISPATCHER_URL?: string; DISPATCHER_INTERNAL_SECRET?: string | SecretBinding; APP_NANOID?: string; }
interface ExportedHandler<E> { fetch(req: Request, env: E): Promise<Response>; }

const APP = "ka";
const NSID_PREFIX = "com.etzhayyim.apps.ka.";
const API_TO_OP: Record<string, string> = {
  "/api/dashboard": "getDashboard",
  "/api/goals": "getGoals",
  "/api/actions": "getActions",
  "/api/revenue": "getRevenue",
  "/api/burn": "getBurn",
  "/api/risks": "getRisks",
  "/api/cases": "getCases",
  "/api/kpi": "getKpi",
  "/api/projects": "getProjects",
  "/api/infra": "getInfra",
  "/api/milestones": "getMilestones",
  "/api/snapshots": "getSnapshots",
  "/api/topo": "getTopo",
  "/api/inbox": "getInbox",
};

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === "/health" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        actor: "did:web:ka.etzhayyim.com",
        nanoid: env.APP_NANOID ?? "ka00ceo1",
        execution: "edge-proxy+agentgateway-mcp+langserver",
        businessLogic: "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ingest/ka.py",
        bpmn: "etzhayyim-root/00-contracts/bpmn/com/etzhayyim/ka",
      });
    }
    if (url.pathname === "/" || url.pathname === "/index.html") return htmlShell();
    const restOp = API_TO_OP[url.pathname];
    if (restOp && req.method === "GET") {
      const body = queryBody(url);
      return proxyToDispatcher(env, `${NSID_PREFIX}${restOp}`, body, true);
    }
    const nsid = url.pathname.startsWith("/xrpc/") ? url.pathname.slice("/xrpc/".length) : "";
    if (nsid.startsWith(NSID_PREFIX) && (req.method === "POST" || req.method === "GET")) {
      const body = await bodyWithQuery(req, url);
      if (body.__invalidJson) return json({ error: "InvalidJson" }, 400);
      return proxyToDispatcher(env, nsid, body, false);
    }
    return json({ error: "NotFound", message: `${APP} not found` }, 404);
  },
} satisfies ExportedHandler<Env>;

function queryBody(url: URL): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  for (const [k, v] of url.searchParams) body[k] = v;
  return body;
}

async function bodyWithQuery(req: Request, url: URL): Promise<Record<string, unknown>> {
  let body: Record<string, unknown> = {};
  if (req.method === "POST") {
    const text = await req.text();
    try {
      body = text ? JSON.parse(text) : {};
    } catch {
      return { __invalidJson: true };
    }
  }
  for (const [k, v] of url.searchParams) if (!(k in body)) body[k] = v;
  return body;
}

async function proxyToDispatcher(env: Env, nsid: string, body: Record<string, unknown>, unwrapRows: boolean): Promise<Response> {
  const base = (env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const headers: Record<string, string> = { "content-type": "application/json" };
  const trust = await internalTrustSecret(env);
  if (trust) headers["x-internal-trust"] = trust;
  const resp = await fetch(`${base}/xrpc/${nsid}`, { method: "POST", headers, body: JSON.stringify(body) });
  const text = await resp.text();
  if (!unwrapRows || !resp.ok) {
    return new Response(text, { status: resp.status, headers: { "content-type": resp.headers.get("content-type") ?? "application/json", "cache-control": "no-store" } });
  }
  try {
    const parsed = JSON.parse(text);
    return json(Array.isArray(parsed.rows) ? parsed.rows : parsed, resp.status);
  } catch {
    return new Response(text, { status: resp.status, headers: { "content-type": "application/json", "cache-control": "no-store" } });
  }
}

async function internalTrustSecret(env: Env): Promise<string> {
  const binding = env.DISPATCHER_INTERNAL_SECRET;
  if (!binding) return "";
  try {
    return typeof binding === "string" ? binding : await binding.get();
  } catch {
    return "";
  }
}

function htmlShell(): Response {
  return new Response(`<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KA 経営</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Hiragino Kaku Gothic ProN",sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
main{max-width:1120px;margin:0 auto;padding:24px}
h1{font-size:28px;margin:0 0 4px}.sub{color:#94a3b8;margin-bottom:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
section{border:1px solid #334155;background:#1e293b;padding:14px;border-radius:8px;min-height:120px}h2{font-size:16px;color:#38bdf8;margin:0 0 10px}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:4px 6px;border-bottom:1px solid #334155;text-align:left}.num{text-align:right}
</style></head>
<body><main><h1>KA 経営ダッシュボード</h1><div class="sub">Strategy Graph via AgentGateway MCP + pod-side LangServer</div><div id="app">Loading...</div></main>
<script>
const yen = v => "¥" + Number(v || 0).toLocaleString("ja-JP");
fetch("/api/dashboard").then(r=>r.json()).then(d=>{
  const card=(title,rows,cols)=>'<section><h2>'+title+'</h2><table>'+rows.slice(0,10).map(r=>'<tr>'+cols.map(c=>'<td class="'+(c.num?'num':'')+'">'+(c.f?c.f(r[c.k],r):r[c.k]??'')+'</td>').join('')+'</tr>').join('')+'</table></section>';
  document.getElementById("app").innerHTML='<div class="grid">'+
    card("目標",d.goals||[],[{k:"display_name"},{k:"attainment_bps",f:v=>(Number(v||0)/100).toFixed(1)+"%"}])+
    card("収益",d.revenue||[],[{k:"display_name"},{k:"target_mrr_jpy",f:yen,num:true}])+
    card("リスク",d.risks||[],[{k:"display_name"},{k:"expected_loss_jpy",f:yen,num:true}])+
    card("次アクション",d.actions||[],[{k:"display_name"},{k:"phase"},{k:"priority",num:true}])+
  '</div>';
}).catch(e=>{document.getElementById("app").textContent=String(e)});
</script></body></html>`, { headers: { "content-type": "text/html;charset=utf-8", "cache-control": "no-store" } });
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });
}
