// dispatcher.ts — bpmn-dispatcher internal-trust caller for yatabase Worker.
//
// Forwards a yatabase XRPC / storage REST call to the K8s LangServer pool
// via dispatcher.gftd.ai. Auth: literal shared secret in `x-internal-trust`
// header (`hmac.compare_digest` literal comparison in dispatcher_main.py
// strict mode). All sibling Workers (atproto / kaisya / lawfirm /
// natural-person / kouza / outlook-mcp) follow the same convention.

export interface DispatcherEnv {
  BPMN_DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
}

const DEFAULT_DISPATCHER_URL = "https://dispatcher.gftd.ai";

export interface DispatcherCallerContext {
  orgDid: string;
  actorDid?: string;
  productScope?: "yata" | "obj" | null;
  traceId?: string;
}

export interface DispatcherResult<T = unknown> {
  ok: boolean;
  status: number;
  data: T | null;
  error?: string;
}

export async function dispatchYataXrpc<T = unknown>(
  env: DispatcherEnv,
  nsid: string,
  body: Record<string, unknown>,
  caller: DispatcherCallerContext,
  options: { timeoutMs?: number } = {},
): Promise<DispatcherResult<T>> {
  const base = (env.BPMN_DISPATCHER_URL ?? DEFAULT_DISPATCHER_URL).replace(/\/+$/, "");
  const url = `${base}/xrpc/${nsid}`;
  const bodyJson = JSON.stringify({ ...body, orgDid: caller.orgDid });

  const headers: Record<string, string> = {
    "content-type": "application/json",
    "x-gftd-org-did": caller.orgDid,
  };
  if (caller.actorDid) headers["x-gftd-actor-did"] = caller.actorDid;
  if (caller.productScope) headers["x-gftd-product-scope"] = caller.productScope;
  if (caller.traceId) headers["x-gftd-trace-id"] = caller.traceId;
  if (env.DISPATCHER_INTERNAL_SECRET) {
    headers["x-internal-trust"] = env.DISPATCHER_INTERNAL_SECRET;
  }

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), options.timeoutMs ?? 60_000);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers,
      body: bodyJson,
      signal: ctrl.signal,
    });
    let data: T | null = null;
    let error: string | undefined;
    try {
      data = (await resp.json()) as T;
    } catch (e) {
      error = `dispatcher returned non-JSON: ${e instanceof Error ? e.message : String(e)}`;
    }
    return {
      ok: resp.ok,
      status: resp.status,
      data,
      error: !resp.ok ? error ?? `dispatcher ${resp.status}` : undefined,
    };
  } catch (e) {
    return {
      ok: false,
      status: 502,
      data: null,
      error: `dispatcher fetch failed: ${e instanceof Error ? e.message : String(e)}`,
    };
  } finally {
    clearTimeout(timer);
  }
}
