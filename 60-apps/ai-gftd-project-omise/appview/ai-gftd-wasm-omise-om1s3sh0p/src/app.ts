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
  "ai.gftd.apps.omise.acceptOrder",
  "ai.gftd.apps.omise.addToCart",
  "ai.gftd.apps.omise.applyCoupon",
  "ai.gftd.apps.omise.approveSeller",
  "ai.gftd.apps.omise.archiveProduct",
  "ai.gftd.apps.omise.cardHome",
  "ai.gftd.apps.omise.clearCart",
  "ai.gftd.apps.omise.createCoupon",
  "ai.gftd.apps.omise.createOrder",
  "ai.gftd.apps.omise.createProduct",
  "ai.gftd.apps.omise.createShipment",
  "ai.gftd.apps.omise.deactivateCoupon",
  "ai.gftd.apps.omise.getCart",
  "ai.gftd.apps.omise.getOrder",
  "ai.gftd.apps.omise.getProduct",
  "ai.gftd.apps.omise.getSellerBalance",
  "ai.gftd.apps.omise.getSellerProfile",
  "ai.gftd.apps.omise.getSellerRevenue",
  "ai.gftd.apps.omise.getShipment",
  "ai.gftd.apps.omise.listCoupons",
  "ai.gftd.apps.omise.listOrders",
  "ai.gftd.apps.omise.listPendingSellers",
  "ai.gftd.apps.omise.listReviews",
  "ai.gftd.apps.omise.listSellerOrders",
  "ai.gftd.apps.omise.listSellerProducts",
  "ai.gftd.apps.omise.listSellers",
  "ai.gftd.apps.omise.listSettlements",
  "ai.gftd.apps.omise.listShipments",
  "ai.gftd.apps.omise.markReadyToShip",
  "ai.gftd.apps.omise.platformAnalytics",
  "ai.gftd.apps.omise.registerSeller",
  "ai.gftd.apps.omise.rejectOrder",
  "ai.gftd.apps.omise.removeFromCart",
  "ai.gftd.apps.omise.requestPayout",
  "ai.gftd.apps.omise.requestPickup",
  "ai.gftd.apps.omise.resolveDispute",
  "ai.gftd.apps.omise.searchProducts",
  "ai.gftd.apps.omise.submitReview",
  "ai.gftd.apps.omise.suspendSeller",
  "ai.gftd.apps.omise.updateInventory",
  "ai.gftd.apps.omise.updateProduct",
  "ai.gftd.apps.omise.updateSellerProfile",
  "ai.gftd.apps.omise.updateShipmentStatus",
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
