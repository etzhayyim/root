// Organizer thin facade. Domain logic runs in AgentGateway MCP + pod-side LangServer workers.

type Env = {
  DISPATCHER_URL?: string;
  ASSETS?: { fetch(request: Request): Promise<Response> };
};

const ACTOR = {
  name: "Organizer",
  did: "did:web:organizer.etzhayyim.com",
  nanoid: "org4n1z3",
};

const NSIDS = new Set([
  "app.etzhayyim.apps.organizer.addTag",
  "app.etzhayyim.apps.organizer.addToCollection",
  "app.etzhayyim.apps.organizer.analyzeSubscriptions",
  "app.etzhayyim.apps.organizer.createCollection",
  "app.etzhayyim.apps.organizer.createRule",
  "app.etzhayyim.apps.organizer.deleteItem",
  "app.etzhayyim.apps.organizer.deleteRule",
  "app.etzhayyim.apps.organizer.detectSubscription",
  "app.etzhayyim.apps.organizer.getRecommendations",
  "app.etzhayyim.apps.organizer.getVaultStats",
  "app.etzhayyim.apps.organizer.listCollections",
  "app.etzhayyim.apps.organizer.listItems",
  "app.etzhayyim.apps.organizer.reclassify",
  "app.etzhayyim.apps.organizer.registerItem",
  "app.etzhayyim.apps.organizer.removeFromCollection",
  "app.etzhayyim.apps.organizer.removeTag",
  "app.etzhayyim.apps.organizer.requestCancellation",
  "app.etzhayyim.apps.organizer.searchItems",
  "app.etzhayyim.apps.organizer.suggestRules",
]);

const json = (body: unknown, init: ResponseInit = {}) =>
  new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      ...(init.headers ?? {}),
    },
  });

async function readBody(request: Request): Promise<Record<string, unknown> | null> {
  if (request.method === "GET" || request.method === "HEAD") {
    return Object.fromEntries(new URL(request.url).searchParams.entries());
  }
  const text = await request.text();
  if (!text) return {};
  try {
    const parsed = JSON.parse(text);
    return parsed && typeof parsed === "object" ? parsed as Record<string, unknown> : {};
  } catch {
    return null;
  }
}

async function dispatch(env: Env, nsid: string, body: Record<string, unknown>, request: Request): Promise<Response> {
  const base = (env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const headers = new Headers({ accept: "application/json", "content-type": "application/json" });
  const auth = request.headers.get("authorization");
  if (auth) headers.set("authorization", auth);
  const activeDid = request.headers.get("x-active-did");
  if (activeDid) headers.set("x-active-did", activeDid);
  const response = await fetch(`${base}/xrpc/${nsid}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const outHeaders = new Headers(response.headers);
  outHeaders.set("access-control-allow-origin", "*");
  return new Response(response.body, { status: response.status, headers: outHeaders });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-methods": "GET,POST,OPTIONS",
          "access-control-allow-headers": "authorization,content-type,x-active-did",
        },
      });
    }
    if (url.pathname === "/health" || url.pathname === "/status") {
      return json({ ok: true, actor: ACTOR.name, did: ACTOR.did, checkedAt: new Date().toISOString() });
    }
    if (url.pathname === "/_app/meta") return json({ ...ACTOR, nsids: [...NSIDS] });
    if (url.pathname.startsWith("/xrpc/")) {
      const nsid = url.pathname.slice("/xrpc/".length);
      if (!NSIDS.has(nsid)) return json({ error: "unsupported_nsid", nsid }, { status: 404 });
      if (request.method !== "GET" && request.method !== "POST") return json({ error: "method_not_allowed" }, { status: 405 });
      const body = await readBody(request);
      if (body === null) return json({ error: "invalid_json" }, { status: 400 });
      return dispatch(env, nsid, body, request);
    }
    if (env.ASSETS) return env.ASSETS.fetch(request);
    return json({ error: "not_found" }, { status: 404 });
  },
};
