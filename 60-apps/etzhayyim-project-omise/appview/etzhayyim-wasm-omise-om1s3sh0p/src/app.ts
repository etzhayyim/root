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
  "com.etzhayyim.apps.omise.acceptOrder",
  "com.etzhayyim.apps.omise.addToCart",
  "com.etzhayyim.apps.omise.applyCoupon",
  "com.etzhayyim.apps.omise.approveSeller",
  "com.etzhayyim.apps.omise.archiveProduct",
  "com.etzhayyim.apps.omise.cardHome",
  "com.etzhayyim.apps.omise.clearCart",
  "com.etzhayyim.apps.omise.createCoupon",
  "com.etzhayyim.apps.omise.createOrder",
  "com.etzhayyim.apps.omise.createProduct",
  "com.etzhayyim.apps.omise.createShipment",
  "com.etzhayyim.apps.omise.deactivateCoupon",
  "com.etzhayyim.apps.omise.getCart",
  "com.etzhayyim.apps.omise.getOrder",
  "com.etzhayyim.apps.omise.getProduct",
  "com.etzhayyim.apps.omise.getSellerBalance",
  "com.etzhayyim.apps.omise.getSellerProfile",
  "com.etzhayyim.apps.omise.getSellerRevenue",
  "com.etzhayyim.apps.omise.getShipment",
  "com.etzhayyim.apps.omise.listCoupons",
  "com.etzhayyim.apps.omise.listOrders",
  "com.etzhayyim.apps.omise.listPendingSellers",
  "com.etzhayyim.apps.omise.listReviews",
  "com.etzhayyim.apps.omise.listSellerOrders",
  "com.etzhayyim.apps.omise.listSellerProducts",
  "com.etzhayyim.apps.omise.listSellers",
  "com.etzhayyim.apps.omise.listSettlements",
  "com.etzhayyim.apps.omise.listShipments",
  "com.etzhayyim.apps.omise.markReadyToShip",
  "com.etzhayyim.apps.omise.platformAnalytics",
  "com.etzhayyim.apps.omise.registerSeller",
  "com.etzhayyim.apps.omise.rejectOrder",
  "com.etzhayyim.apps.omise.removeFromCart",
  "com.etzhayyim.apps.omise.requestPayout",
  "com.etzhayyim.apps.omise.requestPickup",
  "com.etzhayyim.apps.omise.resolveDispute",
  "com.etzhayyim.apps.omise.searchProducts",
  "com.etzhayyim.apps.omise.submitReview",
  "com.etzhayyim.apps.omise.suspendSeller",
  "com.etzhayyim.apps.omise.updateInventory",
  "com.etzhayyim.apps.omise.updateProduct",
  "com.etzhayyim.apps.omise.updateSellerProfile",
  "com.etzhayyim.apps.omise.updateShipmentStatus",
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
