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
  "ai.gftd.apps.handotai.alertCreate",
  "ai.gftd.apps.handotai.alertDelete",
  "ai.gftd.apps.handotai.alertList",
  "ai.gftd.apps.handotai.backfillWriterPosts",
  "ai.gftd.apps.handotai.crawlTrigger",
  "ai.gftd.apps.handotai.getArticle",
  "ai.gftd.apps.handotai.getDailyDigest",
  "ai.gftd.apps.handotai.getSubscription",
  "ai.gftd.apps.handotai.getWeeklyReport",
  "ai.gftd.apps.handotai.handleDailyEvolution",
  "ai.gftd.apps.handotai.listArticles",
  "ai.gftd.apps.handotai.listSemiEntities",
  "ai.gftd.apps.handotai.registerSemiEntities",
  "ai.gftd.apps.handotai.registerWriterProfiles",
  "ai.gftd.apps.handotai.reportGenerate",
  "ai.gftd.apps.handotai.searchArticles",
  "ai.gftd.apps.handotai.seedArticles",
  "ai.gftd.apps.handotai.sourceAdd",
  "ai.gftd.apps.handotai.sourceList",
  "ai.gftd.apps.handotai.subscribe",
  "ai.gftd.apps.handotai.translateArticle",
  "ai.gftd.apps.handotai.updateTranslation",
  "ai.gftd.apps.handotai.wave",
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
