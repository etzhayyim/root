// AppView Worker for the UNSPSC langserver. Per ADR-2605180900 Phase 7.
//
// Mounts `/xrpc/com.etzhayyim.apps.unispsc.*` at unispsc.etzhayyim.com and
// proxies each call to the in-cluster lg-open-unispsc langserver. The
// XRPC handler library lives in @etzhayyim/kotodama-host-sdk so the same
// surface can be re-mounted from any other Worker.

import { createLangserverXrpcHandler } from "@etzhayyim/kotodama-host-sdk";

export interface Env {
  /** Public-or-private base URL of the UNSPSC langserver. */
  LG_UNISPSC_ENDPOINT: string;
  /** Optional CF Service binding for the langserver (skips DNS). */
  LG_UNISPSC?: { fetch: typeof fetch };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (!env.LG_UNISPSC_ENDPOINT && !env.LG_UNISPSC) {
      return new Response(
        JSON.stringify({ error: "Misconfigured: LG_UNISPSC_ENDPOINT unset" }),
        { status: 500, headers: { "content-type": "application/json" } },
      );
    }
    const app = createLangserverXrpcHandler({
      taxonomy: "unispsc",
      endpoint: env.LG_UNISPSC_ENDPOINT,
      fetcher: env.LG_UNISPSC,
      timeoutMs: 15_000,
    });
    return app.fetch(request);
  },
};
