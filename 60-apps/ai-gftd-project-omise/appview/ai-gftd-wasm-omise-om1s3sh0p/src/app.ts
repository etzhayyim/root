// Omise thin facade. Marketplace domain logic runs in AgentGateway MCP + pod-side LangServer workers.

type Env = {
  DISPATCHER_URL?: string;
  ASSETS?: { fetch(request: Request): Promise<Response> };
};

const ACTOR = {
  name: "Omise",
  did: "did:web:omise.etzhayyim.com",
  nanoid: "om1s3sh0p",
};

const NSIDS = new Set([
  "app.etzhayyim.apps.omise.acceptOrder",
  "app.etzhayyim.apps.omise.addToCart",
  "app.etzhayyim.apps.omise.applyCoupon",
  "app.etzhayyim.apps.omise.approveSeller",
  "app.etzhayyim.apps.omise.archiveProduct",
  "app.etzhayyim.apps.omise.cardHome",
  "app.etzhayyim.apps.omise.clearCart",
  "app.etzhayyim.apps.omise.createCoupon",
  "app.etzhayyim.apps.omise.createOrder",
  "app.etzhayyim.apps.omise.createProduct",
  "app.etzhayyim.apps.omise.createShipment",
  "app.etzhayyim.apps.omise.deactivateCoupon",
  "app.etzhayyim.apps.omise.getCart",
  "app.etzhayyim.apps.omise.getOrder",
  "app.etzhayyim.apps.omise.getProduct",
  "app.etzhayyim.apps.omise.getSellerBalance",
  "app.etzhayyim.apps.omise.getSellerProfile",
  "app.etzhayyim.apps.omise.getSellerRevenue",
  "app.etzhayyim.apps.omise.getShipment",
  "app.etzhayyim.apps.omise.listCoupons",
  "app.etzhayyim.apps.omise.listOrders",
  "app.etzhayyim.apps.omise.listPendingSellers",
  "app.etzhayyim.apps.omise.listReviews",
  "app.etzhayyim.apps.omise.listSellerOrders",
  "app.etzhayyim.apps.omise.listSellerProducts",
  "app.etzhayyim.apps.omise.listSellers",
  "app.etzhayyim.apps.omise.listSettlements",
  "app.etzhayyim.apps.omise.listShipments",
  "app.etzhayyim.apps.omise.markReadyToShip",
  "app.etzhayyim.apps.omise.platformAnalytics",
  "app.etzhayyim.apps.omise.registerSeller",
  "app.etzhayyim.apps.omise.rejectOrder",
  "app.etzhayyim.apps.omise.removeFromCart",
  "app.etzhayyim.apps.omise.requestPayout",
  "app.etzhayyim.apps.omise.requestPickup",
  "app.etzhayyim.apps.omise.resolveDispute",
  "app.etzhayyim.apps.omise.searchProducts",
  "app.etzhayyim.apps.omise.submitReview",
  "app.etzhayyim.apps.omise.suspendSeller",
  "app.etzhayyim.apps.omise.updateInventory",
  "app.etzhayyim.apps.omise.updateProduct",
  "app.etzhayyim.apps.omise.updateSellerProfile",
  "app.etzhayyim.apps.omise.updateShipmentStatus",
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
    if (url.pathname === "/health") return json({ ok: true, actor: ACTOR.name, did: ACTOR.did });
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
