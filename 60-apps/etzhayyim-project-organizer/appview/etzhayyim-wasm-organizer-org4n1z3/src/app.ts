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
  "com.etzhayyim.apps.organizer.addTag",
  "com.etzhayyim.apps.organizer.addToCollection",
  "com.etzhayyim.apps.organizer.analyzeSubscriptions",
  "com.etzhayyim.apps.organizer.createCollection",
  "com.etzhayyim.apps.organizer.createRule",
  "com.etzhayyim.apps.organizer.deleteItem",
  "com.etzhayyim.apps.organizer.deleteRule",
  "com.etzhayyim.apps.organizer.detectSubscription",
  "com.etzhayyim.apps.organizer.getRecommendations",
  "com.etzhayyim.apps.organizer.getVaultStats",
  "com.etzhayyim.apps.organizer.listCollections",
  "com.etzhayyim.apps.organizer.listItems",
  "com.etzhayyim.apps.organizer.reclassify",
  "com.etzhayyim.apps.organizer.registerItem",
  "com.etzhayyim.apps.organizer.removeFromCollection",
  "com.etzhayyim.apps.organizer.removeTag",
  "com.etzhayyim.apps.organizer.requestCancellation",
  "com.etzhayyim.apps.organizer.searchItems",
  "com.etzhayyim.apps.organizer.suggestRules",
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
