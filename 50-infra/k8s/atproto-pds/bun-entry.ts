// atproto PDS — Bun runtime entry (ADR-2605111300, Phase P1).
//
// Wraps the existing CF Worker default export (`export { default } from './app'`)
// in `Bun.serve`. CF bindings (HYPERDRIVE, R2, service bindings, AI, secrets store)
// are constructed from env vars and exposed on the `env` object passed to fetch().
//
// Phase P1 scope: keep handler code untouched. Adapters are best-effort; many
// callsites will still hit CF-specific shapes (Service.fetch, R2Bucket.get/put,
// DurableObject namespace). Phase P2 / P3 of this migration will replace each.

import worker from "./app";
import { Pool } from "pg"; // kotoba-datomic-projection: ADR-2605231500

declare global {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface ProcessEnv {}
}

interface PgHyperdriveAdapter {
  connectionString: string;
  query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[]; rowCount: number | null }>;
}

function buildHyperdriveAdapter(): PgHyperdriveAdapter {
  const connectionString = process.env.KOTOBA_URL;
  if (!connectionString) {
    throw new Error("KOTOBA_URL is required (ADR-2605111300, atproto-pds Bun pod)");
  }
  const pool = new Pool({ connectionString, max: Number(process.env.PG_POOL_MAX ?? 16) });
  return {
    connectionString,
    async query(text, params) {
      const result = await pool.query(text, params as unknown[]);
      return { rows: result.rows as Record<string, unknown>[], rowCount: result.rowCount };
    },
  };
}

function proxyFetch(targetBase: string | undefined) {
  if (!targetBase) return undefined;
  const base = targetBase.replace(/\/$/, "");
  return {
    fetch(input: Request | string, init?: RequestInit): Promise<Response> {
      if (typeof input === "string") {
        const url = input.startsWith("http") ? input : base + input;
        return fetch(url, init);
      }
      const u = new URL(input.url);
      return fetch(base + u.pathname + u.search, input as unknown as RequestInit);
    },
  };
}

function r2BucketShim() {
  // Placeholder. Real implementation = aws-sdk v3 S3Client against B2.
  return {
    async get(_key: string) { return null; },
    async put(_key: string, _body: ArrayBuffer | Uint8Array | string) { return; },
    async delete(_key: string) { return; },
    async head(_key: string) { return null; },
  };
}

function secretBinding(value: string | undefined) {
  if (value === undefined) return undefined;
  return {
    async get(): Promise<string> { return value; },
  };
}

function buildEnv(): Record<string, unknown> {
  return {
    HYPERDRIVE: buildHyperdriveAdapter(),
    CACHE_R2: r2BucketShim(),

    // Service bindings → upstream HTTP services.
    AUTH_SERVICE:           proxyFetch(process.env.AUTH_SERVICE_URL),
    GRAPH_QUERY_SERVICE:    proxyFetch(process.env.GRAPH_QUERY_SERVICE_URL),
    ROUTING_GATEWAY:        proxyFetch(process.env.ROUTING_GATEWAY_URL),
    PLC_DIRECTORY:          proxyFetch(process.env.PLC_DIRECTORY_URL),
    VAULT_SERVICE:          proxyFetch(process.env.VAULT_SERVICE_URL),
    APPVIEW_SERVICE:        proxyFetch(process.env.APPVIEW_SERVICE_URL),
    RESOURCE_FLOW_SERVICE:  proxyFetch(process.env.BPMN_DISPATCHER_URL),
    IPFS_API:               proxyFetch(process.env.IPFS_API_URL),
    LLM_GATEWAY:            proxyFetch(process.env.LLM_GATEWAY_URL),

    // Secrets Store bindings (CF presents async .get()).
    SS_REPO_SIGNING_KEK:    secretBinding(process.env.SS_REPO_SIGNING_KEK),
    SS_SIGNING_KEY:         secretBinding(process.env.SS_SIGNING_KEY),

    // Plain env vars pass through.
    ...process.env,
  };
}

const env = buildEnv();
const port = Number(process.env.PORT ?? 8787);

type WorkerHandler = { fetch(req: Request, env: unknown, ctx: ExecutionContext): Promise<Response> | Response };

interface ExecutionContext {
  waitUntil(p: Promise<unknown>): void;
  passThroughOnException(): void;
}

const ctxStub: ExecutionContext = {
  waitUntil(_p) { /* fire-and-forget; Bun keeps the promise alive */ },
  passThroughOnException() { /* no-op */ },
};

const server = Bun.serve({
  port,
  hostname: "0.0.0.0",
  async fetch(request: Request) {
    return (worker as WorkerHandler).fetch(request, env, ctxStub);
  },
});

// eslint-disable-next-line no-console
console.log(`[atproto-pds] Bun runtime listening on :${server.port} (ADR-2605111300)`);
