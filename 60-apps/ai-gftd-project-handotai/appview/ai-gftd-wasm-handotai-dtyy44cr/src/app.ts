type Env = {
  DISPATCHER_URL?: string;
  ASSETS?: { fetch(request: Request): Promise<Response> };
};

const ACTOR = {
  name: "Handotai",
  did: "did:web:handotai.etzhayyim.com",
  nanoid: "dtyy44cr",
};

const NSIDS = new Set([
  "app.etzhayyim.apps.handotai.alertCreate",
  "app.etzhayyim.apps.handotai.alertDelete",
  "app.etzhayyim.apps.handotai.alertList",
  "app.etzhayyim.apps.handotai.backfillWriterPosts",
  "app.etzhayyim.apps.handotai.crawlTrigger",
  "app.etzhayyim.apps.handotai.getArticle",
  "app.etzhayyim.apps.handotai.getDailyDigest",
  "app.etzhayyim.apps.handotai.getSubscription",
  "app.etzhayyim.apps.handotai.getWeeklyReport",
  "app.etzhayyim.apps.handotai.handleDailyEvolution",
  "app.etzhayyim.apps.handotai.listArticles",
  "app.etzhayyim.apps.handotai.listSemiEntities",
  "app.etzhayyim.apps.handotai.registerSemiEntities",
  "app.etzhayyim.apps.handotai.registerWriterProfiles",
  "app.etzhayyim.apps.handotai.reportGenerate",
  "app.etzhayyim.apps.handotai.searchArticles",
  "app.etzhayyim.apps.handotai.seedArticles",
  "app.etzhayyim.apps.handotai.sourceAdd",
  "app.etzhayyim.apps.handotai.sourceList",
  "app.etzhayyim.apps.handotai.subscribe",
  "app.etzhayyim.apps.handotai.translateArticle",
  "app.etzhayyim.apps.handotai.updateTranslation",
  "app.etzhayyim.apps.handotai.wave",
]);

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "content-type,authorization,x-service-auth",
};

function json(data: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(data), {
    ...init,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...corsHeaders,
      ...(init.headers || {}),
    },
  });
}

async function readInput(request: Request): Promise<Record<string, unknown>> {
  if (request.method === "GET") {
    return Object.fromEntries(new URL(request.url).searchParams.entries());
  }
  const text = await request.text();
  if (!text.trim()) return {};
  const parsed = JSON.parse(text);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("JSON body must be an object");
  }
  return parsed as Record<string, unknown>;
}

async function dispatch(env: Env, nsid: string, input: Record<string, unknown>, request: Request): Promise<Response> {
  const base = (env.DISPATCHER_URL || "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const headers = new Headers({ accept: "application/json", "content-type": "application/json" });
  const auth = request.headers.get("authorization");
  if (auth) headers.set("authorization", auth);
  const activeDid = request.headers.get("x-active-did");
  if (activeDid) headers.set("x-active-did", activeDid);
  const res = await fetch(`${base}/xrpc/${nsid}`, {
    method: "POST",
    headers,
    body: JSON.stringify(input),
  });
  const outHeaders = new Headers(res.headers);
  outHeaders.set("access-control-allow-origin", "*");
  return new Response(res.body, { status: res.status, headers: outHeaders });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return json({ ok: true, actor: ACTOR.name, did: ACTOR.did });
    }
    if (url.pathname === "/_app/meta") {
      return json({ ...ACTOR, nsids: [...NSIDS] });
    }

    if (url.pathname.startsWith("/xrpc/")) {
      const nsid = url.pathname.slice("/xrpc/".length);
      if (!NSIDS.has(nsid)) return json({ error: "unknown nsid", nsid }, { status: 404 });
      if (request.method !== "GET" && request.method !== "POST") return json({ error: "method_not_allowed" }, { status: 405 });
      try {
        const input = await readInput(request);
        return dispatch(env, nsid, input, request);
      } catch (err) {
        return json({ error: err instanceof Error ? err.message : String(err) }, { status: 400 });
      }
    }

    if (env.ASSETS) return env.ASSETS.fetch(request);
    return json({ error: "not found" }, { status: 404 });
  },
};
