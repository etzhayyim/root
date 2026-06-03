/**
 * yoro XRPC adapter — CF Worker.
 *
 * Wires the rw-free reference impl (23 TS functions) into a deployable
 * CF Worker that exposes each function as an XRPC endpoint at
 * https://yoro.etzhayyim.com/xrpc/com.etzhayyim.yoro.*
 *
 * Per ADR-2605210000 execution-layer demonstration. Instantiates the
 * Etzhayyim SDK from env bindings, calls the rw-free function with parsed input,
 * and maps status codes to HTTP responses.
 *
 * Routes organized into 5 sub-namespaces:
 * - com.etzhayyim.yoro.health
 * - com.etzhayyim.yoro.activity.*
 * - com.etzhayyim.yoro.feed.*
 * - com.etzhayyim.yoro.graph.*
 * - com.etzhayyim.yoro.actor.*
 */

import {
  createAuthedEtzhayyim,
  extractBearerToken,
  type Etzhayyim,
} from "@etzhayyim/sdk-auth";
import * as yoroRwFree from "@etzhayyim/yoro-rw-free";
import {
  UNISPSC_AGENTS,
  UNISPSC_TOTAL,
  UNISPSC_GENERATED_AT,
} from "./registry/unispsc-agents.gen";

interface Env {
  ACTOR_DID: string;
  PDS_URL: string;
  L2_RPC_URL: string;
  PDS_ACCESS_JWT?: string;
  PDS_REFRESH_JWT?: string;
  /**
   * kotoba-datomic-projection: feed-discover (ADR-2605231500).
   * `did:web:projector.etzhayyim.com` (or similar). When set, the rw-free
   * feed.ts getDiscoverFeed / getTimeline read the cross-DID projection
   * instead of the single ACTOR_DID MST.
   */
  PROJECTION_DISCOVER_DID?: string;
  /**
   * kotoba server base URL (e.g. `https://kotoba.etzhayyim.com`). When set, the
   * rw-free feed/graph/actor reads resolve through the kotoba canonical Datom
   * log (ADR-2606013200) instead of the PDS/projection path.
   */
  KOTOBA_URL?: string;
  /** Multibase CID of the kotoba graph holding the yoro feed Datoms. */
  YORO_GRAPH_CID?: string;
  // UnispscAgentExecutorCell shard URLs (Phase β). Each is a cloudflared
  // tunnel published from joseph/issachar/dan inside the Murakumo LAN to
  // the corresponding cell at port 16100/16101/16102. Empty string ⇒
  // shard offline; the façade reports notReady + ExecutorOffline.
  UNISPSC_EXECUTOR_SHARD_0?: string;
  UNISPSC_EXECUTOR_SHARD_1?: string;
  UNISPSC_EXECUTOR_SHARD_2?: string;
  UNISPSC_EXECUTOR_TIMEOUT_MS?: string;
}

type Handler = (e: Etzhayyim, input: unknown) => Promise<unknown>;

interface RouteConfig {
  method: "POST" | "GET";
  handler: Handler;
}

// ─── unispsc registry handlers ─────────────────────────────────────────
//
// Phase α: registry rows are bundled at build time (compact tuple form from
// 00-contracts/actor-registry/unispsc.json via the generator script). The
// rw-free contract per ADR-2605172000 requires reads resolve through the
// MST/IPFS substrate — Phase β migrates this to an IPFS-gateway fetch keyed
// by a CID stored in KV, with the bundle as a deploy-time fallback.

const UNISPSC_CODE_INDEX: Map<string, number> = (() => {
  const m = new Map<string, number>();
  for (let i = 0; i < UNISPSC_AGENTS.length; i++) {
    m.set(UNISPSC_AGENTS[i][0], i);
  }
  return m;
})();

async function unispscHealth(_e: Etzhayyim, _input: unknown): Promise<unknown> {
  return {
    status: UNISPSC_TOTAL > 0 ? "healthy" : "degraded",
    registryReady: UNISPSC_TOTAL > 0,
    agentCount: UNISPSC_TOTAL,
    generatedAt: UNISPSC_GENERATED_AT,
    substrate: "bundled-phase-α",
  };
}

async function unispscListAgents(
  _e: Etzhayyim,
  input: unknown,
): Promise<unknown> {
  const params = (input ?? {}) as {
    prefix?: string;
    limit?: number;
    cursor?: string;
  };
  const limit = Math.max(1, Math.min(1000, Number(params.limit) || 100));
  const cursor = params.cursor ? Number(params.cursor) : 0;
  if (!Number.isFinite(cursor) || cursor < 0) {
    return { status: "rejected", error: "InvalidCursor" };
  }
  const prefix = params.prefix?.toString();

  let filtered: typeof UNISPSC_AGENTS;
  if (prefix) {
    filtered = UNISPSC_AGENTS.filter((row) => row[0].startsWith(prefix));
  } else {
    filtered = UNISPSC_AGENTS;
  }
  const page = filtered.slice(cursor, cursor + limit);
  const nextCursor =
    cursor + limit < filtered.length ? String(cursor + limit) : undefined;
  const agents = page.map(([code, handle, title, segment]) => ({
    code,
    handle,
    did: `did:web:etzhayyim.com:actor:${handle}`,
    title,
    segment,
  }));
  return {
    agents,
    totalCount: filtered.length,
    ...(nextCursor ? { cursor: nextCursor } : {}),
  };
}

async function unispscClassify(
  _e: Etzhayyim,
  input: unknown,
): Promise<unknown> {
  const body = (input ?? {}) as {
    description?: string;
    topK?: number;
  };
  const desc = (body.description ?? "").toLowerCase();
  if (!desc) {
    return { status: "rejected", error: "DescriptionRequired" };
  }
  const topK = Math.max(1, Math.min(20, Number(body.topK) || 5));
  const tokens = desc.split(/\W+/u).filter((t) => t.length >= 3);
  const scored: { code: string; handle: string; title: string; confidence: number }[] = [];
  for (const [code, handle, title, _segment] of UNISPSC_AGENTS) {
    const lowered = title.toLowerCase();
    let score = 0;
    for (const tok of tokens) {
      if (lowered.includes(tok)) score += 0.5;
      if (code.includes(tok)) score += 0.2;
    }
    if (score > 0) {
      scored.push({ code, handle, title, confidence: Math.min(score, 1.0) });
    }
  }
  scored.sort((a, b) => b.confidence - a.confidence);
  return {
    candidates: scored.slice(0, topK),
    modelUsed: "substring-phase-α",
    escalated: false,
  };
}

function resolveExecutorShard(code: string): 0 | 1 | 2 | null {
  if (code.length < 2 || !/^\d+$/u.test(code)) return null;
  const seg = Number(code.slice(0, 2));
  if (seg >= 10 && seg <= 29) return 0;
  if (seg >= 30 && seg <= 44) return 1;
  if (seg >= 45 && seg <= 60) return 2;
  return null;
}

function executorUrlFor(env: Env, shard: 0 | 1 | 2): string {
  switch (shard) {
    case 0: return env.UNISPSC_EXECUTOR_SHARD_0 ?? "";
    case 1: return env.UNISPSC_EXECUTOR_SHARD_1 ?? "";
    case 2: return env.UNISPSC_EXECUTOR_SHARD_2 ?? "";
  }
}

async function unispscInvokeAgentWithEnv(
  env: Env,
  input: unknown,
): Promise<unknown> {
  const body = (input ?? {}) as {
    code?: string;
    input?: Record<string, unknown>;
    state?: Record<string, unknown>;
    threadId?: string;
  };
  const code = body.code?.toString() ?? "";
  if (!UNISPSC_CODE_INDEX.has(code)) {
    return { status: "notFound", error: "AgentNotFound", code };
  }
  const shard = resolveExecutorShard(code);
  if (shard === null) {
    return { status: "rejected", error: "InvalidCode", code };
  }
  const base = executorUrlFor(env, shard).replace(/\/$/, "");
  if (!base) {
    return {
      status: "notReady",
      error: "ExecutorOffline",
      message: `UnispscAgentExecutorCell shard-${shard} tunnel not configured (env UNISPSC_EXECUTOR_SHARD_${shard})`,
      code,
      shard,
    };
  }
  const timeoutMs = Math.max(
    1_000,
    Math.min(30_000, Number(env.UNISPSC_EXECUTOR_TIMEOUT_MS) || 10_000),
  );
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const resp = await fetch(`${base}/api/invoke`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        code,
        input: body.input ?? body.state ?? {},
        threadId: body.threadId,
      }),
      signal: ctrl.signal,
    });
    const text = await resp.text();
    let parsed: unknown;
    try { parsed = text ? JSON.parse(text) : {}; } catch { parsed = { raw: text }; }
    if (!resp.ok) {
      return {
        status: "executorError",
        httpStatus: resp.status,
        code,
        shard,
        detail: parsed,
      };
    }
    return parsed;
  } catch (err) {
    return {
      status: "executorUnreachable",
      error: (err as Error).name === "AbortError" ? "Timeout" : "FetchFailed",
      code,
      shard,
      message: (err as Error).message,
    };
  } finally {
    clearTimeout(t);
  }
}

const routes: Record<string, RouteConfig> = {
  // unispsc registry — bundled rw-free Phase α implementation.
  ["com.etzhayyim.apps.unispsc.health"]: { method: "GET", handler: unispscHealth },
  ["com.etzhayyim.apps.unispsc.listAgents"]: { method: "GET", handler: unispscListAgents },
  ["com.etzhayyim.apps.unispsc.classify"]: { method: "POST", handler: unispscClassify },
  // invokeAgent needs env access for shard tunnel URLs — handled specially
  // in the fetch dispatcher below (see UNISPSC_INVOKE_NSID).

  // Health & Registry
  ["com.etzhayyim.yoro.health"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.health(e, input as any),
  },
  ["com.etzhayyim.yoro.stats"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.stats(e, input as any),
  },

  // Activity
  ["com.etzhayyim.yoro.activity.listActivities"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listActivities(e, input as any),
  },
  ["com.etzhayyim.yoro.activity.getActivityTrace"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getActivityTrace(e, input as any),
  },
  ["com.etzhayyim.yoro.activity.markSeen"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.markSeen(e, input as any),
  },

  // Feed
  ["com.etzhayyim.yoro.feed.getTimeline"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getTimeline(e, input as any),
  },
  ["com.etzhayyim.yoro.feed.getAuthorFeed"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getAuthorFeed(e, input as any),
  },
  ["com.etzhayyim.yoro.feed.getPostThread"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getPostThread(e, input as any),
  },
  ["com.etzhayyim.yoro.feed.getRankedFeed"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getRankedFeed(e, input as any),
  },
  ["com.etzhayyim.yoro.feed.getDiscoverFeed"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getDiscoverFeed(e, input as any),
  },

  // Graph
  ["com.etzhayyim.yoro.graph.getFollowers"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getFollowers(e, input as any),
  },
  ["com.etzhayyim.yoro.graph.getFollows"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getFollows(e, input as any),
  },

  // Actor / Profile
  ["com.etzhayyim.yoro.actor.getProfile"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getProfile(e, input as any),
  },
  ["com.etzhayyim.yoro.actor.searchActors"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.searchActors(e, input as any),
  },

  // Registry / Ingest
  ["com.etzhayyim.yoro.registry.projectEntity"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.projectEntity(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.productResearch"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.productResearch(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.activitySeen"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.activitySeen(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.shinkaEvolution"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.shinkaEvolution(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.shinkaKnowledge"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.shinkaKnowledge(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.ingestProductCategory"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.ingestProductCategory(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.listApps"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listApps(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.listPosts"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listPosts(e, input as any),
  },
  ["com.etzhayyim.yoro.registry.listProductResearch"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listProductResearch(e, input as any),
  },
};

function mapStatus(status?: string): number {
  if (status === "rejected") return 400;
  if (status === "notFound" || status === "invalidId") return 400;
  if (status === "alreadyExists") return 200;
  if (status === "notReady") return 503;
  if (status === "executorError") return 502;
  if (status === "executorUnreachable") return 504;
  return 200;
}

function jsonResponse(
  body: unknown,
  status: number = 200,
  init?: ResponseInit
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      ...init?.headers,
    },
    ...init,
  });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (!url.pathname.startsWith("/xrpc/")) {
      return jsonResponse({ error: "NotFound" }, 404);
    }

    const nsid = url.pathname.slice("/xrpc/".length);

    // Special-case: invokeAgent needs env-bound shard tunnel URLs.
    if (nsid === "com.etzhayyim.apps.unispsc.invokeAgent") {
      if (req.method !== "POST") {
        return jsonResponse({ error: "MethodNotAllowed" }, 405);
      }
      let body: unknown;
      try { body = await req.json().catch(() => ({})); }
      catch { return jsonResponse({ error: "InvalidInput" }, 400); }
      const result = await unispscInvokeAgentWithEnv(env, body);
      const status = mapStatus((result as Record<string, unknown>)?.status as string | undefined);
      return jsonResponse(result, status);
    }

    const route = routes[nsid];

    if (!route) {
      return jsonResponse({ error: "MethodNotFound", nsid }, 404);
    }

    if (req.method !== route.method) {
      return jsonResponse({ error: "MethodNotAllowed" }, 405);
    }

    const bearerToken = extractBearerToken(req);
    const e = createAuthedEtzhayyim({
      env: {
        ACTOR_DID: env.ACTOR_DID,
        PDS_URL: env.PDS_URL,
        L2_RPC_URL: env.L2_RPC_URL,
        PDS_ACCESS_JWT: env.PDS_ACCESS_JWT,
        PDS_REFRESH_JWT: env.PDS_REFRESH_JWT,
        PROJECTION_DISCOVER_DID: env.PROJECTION_DISCOVER_DID,
        KOTOBA_URL: env.KOTOBA_URL,
        YORO_GRAPH_CID: env.YORO_GRAPH_CID,
      },
      bearerToken,
    });

    let input: unknown;
    try {
      if (route.method === "POST") {
        input = await req.json().catch(() => ({}));
      } else {
        input = Object.fromEntries(url.searchParams.entries());
        const typed = input as Record<string, unknown>;
        if (typed.limit) typed.limit = Number(typed.limit);
        if (typed.offset) typed.offset = Number(typed.offset);
        if (typed.maxScan) typed.maxScan = Number(typed.maxScan);
      }
    } catch (err) {
      return jsonResponse(
        {
          error: "InvalidInput",
          message: `Failed to parse ${route.method === "POST" ? "JSON" : "query params"}`,
        },
        400
      );
    }

    try {
      const result = await route.handler(e, input);
      const status = mapStatus((result as Record<string, unknown>)?.status as string | undefined);
      return jsonResponse(result, status);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return jsonResponse(
        {
          error: "InternalError",
          message,
          nsid,
        },
        500
      );
    }
  },
} satisfies ExportedHandler<Env>;
