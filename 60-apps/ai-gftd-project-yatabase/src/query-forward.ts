// query-forward.ts — deploy-first query XRPC shim from yatabase CF Worker
// to lg-yatabase Granian pod (ADR-2605210000).
//
// Mirrors bmc-forward.ts. Adds x-gftd-mv-limit header so the pod knows
// the plan's MV slot cap without a separate DB lookup.

export interface QueryForwardEnv {
  LG_YATABASE_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
}

export interface QueryForwardIdentity {
  did: string;
  orgDid: string;
  activeDid?: string;
  traceId?: string;
}

export interface QueryForwardOptions {
  timeoutMs?: number;
  mvLimit: number;
}

export interface QueryForwardResult {
  ok: boolean;
  status: number;
  data: unknown;
  error?: string;
}

const QUERY_NSIDS = new Set([
  "app.etzhayyim.apps.yata.deployQuery",
  "app.etzhayyim.apps.yata.executeDeployedQuery",
  "app.etzhayyim.apps.yata.listDeployedQueries",
  "app.etzhayyim.apps.yata.deleteDeployedQuery",
]);

export function isQueryNsid(nsid: string): boolean {
  return QUERY_NSIDS.has(nsid);
}

async function hmacHex(secret: string, body: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export async function forwardQuery(
  env: QueryForwardEnv,
  method: "GET" | "POST",
  nsid: string,
  payload: Record<string, unknown>,
  identity: QueryForwardIdentity,
  opts: QueryForwardOptions,
): Promise<QueryForwardResult> {
  const base = env.LG_YATABASE_URL;
  if (!base) {
    return { ok: false, status: 503, data: null, error: "LG_YATABASE_URL not configured" };
  }

  const url = new URL(`/xrpc/${nsid}`, base.endsWith("/") ? base : `${base}/`);

  const headers: Record<string, string> = {
    "x-gftd-actor-did": identity.activeDid ?? identity.did,
    "x-gftd-org-did": identity.orgDid,
    "x-gftd-mv-limit": String(opts.mvLimit),
  };
  if (identity.traceId) headers["x-gftd-trace-id"] = identity.traceId;

  let body: string | undefined;
  if (method === "GET") {
    for (const [k, v] of Object.entries(payload)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
  } else {
    body = JSON.stringify(payload ?? {});
    headers["content-type"] = "application/json";
  }

  if (env.DISPATCHER_INTERNAL_SECRET) {
    headers["x-internal-trust"] = await hmacHex(
      env.DISPATCHER_INTERNAL_SECRET,
      body ?? "",
    );
  }

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), Math.max(1000, opts.timeoutMs ?? 30_000));
  try {
    const resp = await fetch(url.toString(), { method, headers, body, signal: ctrl.signal });
    const text = await resp.text();
    let data: unknown = null;
    try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text.slice(0, 1024) }; }
    if (!resp.ok) {
      return {
        ok: false,
        status: resp.status,
        data,
        error: typeof (data as { error?: string })?.error === "string"
          ? (data as { error: string }).error
          : `lg-yatabase HTTP ${resp.status}`,
      };
    }
    return { ok: true, status: resp.status, data };
  } catch (e) {
    const aborted = e instanceof DOMException && e.name === "AbortError";
    return {
      ok: false,
      status: aborted ? 504 : 502,
      data: null,
      error: aborted ? "lg-yatabase timeout" : e instanceof Error ? e.message.slice(0, 240) : "throw",
    };
  } finally {
    clearTimeout(t);
  }
}
