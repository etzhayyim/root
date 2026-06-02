// bmc-forward.ts — stateless XRPC shim from yatabase CF Worker to
// lg-yatabase Granian pod (mitama-yata-pool).
//
// Single-writer principle: the pod owns ALL writes against vertex_bmc_*
// / edge_bmc_* / mv_bmc_*. This Worker never touches Hyperdrive for BMC.
// Reads go through the same path so the pod can use mv_bmc_* (DISTINCT
// ON status / head materialization) without exposing two DB paths.
//
// Auth: caller has already been resolved by the yatabase auth middleware
// (PDS-side `sk_live_yata_*` validate or AT session JWT). Forwarder adds
//   x-internal-trust   = HMAC-SHA256(body, DISPATCHER_INTERNAL_SECRET)
//   x-gftd-actor-did   = AT did
//   x-gftd-org-did     = product-scope org did
//   x-gftd-trace-id    = cf-ray
// Mirrors the bpmn-dispatcher trust pattern documented in yatabase
// CLAUDE.md §"Forwarding model".

export interface ForwardEnv {
  /** Public URL of the lg-yatabase Granian pod (e.g. via cloudflared tunnel). */
  LG_YATABASE_URL?: string;
  /** Shared HMAC secret. Same name/value as the bpmn-dispatcher uses. */
  DISPATCHER_INTERNAL_SECRET?: string;
}

export interface ForwardIdentity {
  did: string;
  orgDid: string;
  activeDid?: string;
  productScope?: "yata" | "obj" | null;
  traceId?: string;
}

const BMC_NSID_PREFIX = "com.etzhayyim.apps.yata.bmc";

export function isBmcNsid(nsid: string): boolean {
  return nsid.startsWith(BMC_NSID_PREFIX);
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

export interface ForwardOptions {
  timeoutMs?: number;
}

export interface ForwardResult {
  ok: boolean;
  status: number;
  data: unknown;
  error?: string;
}

export async function forwardBmc(
  env: ForwardEnv,
  method: "GET" | "POST",
  nsid: string,
  payload: Record<string, unknown>,
  identity: ForwardIdentity,
  opts: ForwardOptions = {},
): Promise<ForwardResult> {
  const base = env.LG_YATABASE_URL;
  if (!base) {
    return {
      ok: false, status: 503,
      data: null,
      error: "LG_YATABASE_URL not configured — BMC pod unreachable",
    };
  }
  const url = new URL(`/xrpc/${nsid}`, base.endsWith("/") ? base : `${base}/`);

  // GET payload travels as query params, POST as JSON body.
  const headers: Record<string, string> = {
    "x-gftd-actor-did": identity.activeDid ?? identity.did,
    "x-gftd-org-did": identity.orgDid,
  };
  if (identity.traceId) headers["x-gftd-trace-id"] = identity.traceId;

  let body: string | undefined;
  if (method === "GET") {
    for (const [k, v] of Object.entries(payload)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
    body = undefined;
  } else {
    body = JSON.stringify(payload ?? {});
    headers["content-type"] = "application/json";
  }

  // Worker MUST always provide an HMAC over the request body (empty string
  // for GET). Pod refuses requests without it when the secret is set.
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
