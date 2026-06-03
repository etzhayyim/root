// market.etzhayyim.com thin facade. Domain logic runs in AgentGateway MCP + pod-side LangServer workers.

type Env = {
  DISPATCHER_URL?: string;
  ASSETS?: { fetch(request: Request): Promise<Response> };
  BUNDLER_RPC_URL?: string;
  ERC4337_CHAIN_ID?: string;
};

const PRIMARY_DID = "did:web:market.etzhayyim.com";
const NANOID = "mk7r3x9p";
const VALID_LANES = ["vault", "sashiosae", "lawfirm", "bpmn", "murakumo"] as const;
const MARKET_NSIDS = new Set([
  "com.etzhayyim.market.listOffer",
  "com.etzhayyim.market.publishOffer",
  "com.etzhayyim.market.quotePrice",
  "com.etzhayyim.market.settleInvoice",
  "com.etzhayyim.market.observeDemand",
]);

function json(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      ...(init.headers ?? {}),
    },
  });
}

function b64urlDecode(s: string): Uint8Array {
  const padded = s.replace(/-/g, "+").replace(/_/g, "/").padEnd(
    s.length + ((4 - (s.length % 4)) % 4),
    "=",
  );
  return Uint8Array.from(atob(padded), (c) => c.charCodeAt(0));
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    return JSON.parse(new TextDecoder().decode(b64urlDecode(parts[1]))) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function requireLxmAuth(request: Request, nsid: string): Response | null {
  const authHeader = request.headers.get("authorization") ?? "";
  const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
  if (!token) return json({ error: "AuthRequired", detail: "Authorization: Bearer <service-auth-jwt> required" }, { status: 401 });

  const payload = decodeJwtPayload(token);
  if (!payload) return json({ error: "InvalidToken", detail: "JWT decode failed" }, { status: 401 });

  const now = Math.floor(Date.now() / 1000);
  const exp = typeof payload.exp === "number" ? payload.exp : 0;
  const iat = typeof payload.iat === "number" ? payload.iat : exp - 1;
  if (exp < now) return json({ error: "TokenExpired", detail: `exp=${exp} now=${now}` }, { status: 401 });
  if (exp - iat > 60) return json({ error: "TokenLifetimeTooLong", detail: `lifetime=${exp - iat}s max=60s` }, { status: 401 });
  if (payload.lxm !== nsid) return json({ error: "LxmMismatch", detail: `expected=${nsid} got=${String(payload.lxm)}` }, { status: 401 });
  return null;
}

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
    if (url.pathname === "/health" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        actor: PRIMARY_DID,
        nanoid: NANOID,
        phase: "1.2",
        adr: "2605011300",
        lanes: VALID_LANES,
        nsids: [...MARKET_NSIDS],
        mokutekiGate: "live in BPMN worker",
        settlementAnchor: env.BUNDLER_RPC_URL
          ? `erc4337:${env.ERC4337_CHAIN_ID ?? "?"}:<userOpHash>`
          : "anchor:sha256:<64hex> (deterministic, ERC-4337 fallback)",
      });
    }
    if (url.pathname === "/.well-known/atproto-market.json") {
      return dispatch(env, "com.etzhayyim.market.wellKnownMarket", {}, request);
    }
    if (url.pathname.startsWith("/xrpc/")) {
      const nsid = url.pathname.slice("/xrpc/".length);
      if (!MARKET_NSIDS.has(nsid)) return json({ error: "MethodNotFound", nsid }, { status: 404 });
      if (request.method !== "POST" && request.method !== "GET") return json({ error: "MethodNotAllowed" }, { status: 405 });
      const authError = requireLxmAuth(request, nsid);
      if (authError) return authError;
      const body = await readBody(request);
      if (body === null) return json({ error: "InvalidJson" }, { status: 400 });
      return dispatch(env, nsid, body, request);
    }
    if (env.ASSETS) return env.ASSETS.fetch(request);
    return json({ error: "NotFound" }, { status: 404 });
  },
};
