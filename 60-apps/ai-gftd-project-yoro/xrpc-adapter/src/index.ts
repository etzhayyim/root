/**
 * yoro XRPC adapter — CF Worker.
 *
 * Wires the rw-free reference impl (23 TS functions) into a deployable
 * CF Worker that exposes each function as an XRPC endpoint at
 * https://yoro.etzhayyim.com/xrpc/ai.gftd.yoro.*
 *
 * Per ADR-2605210000 execution-layer demonstration. Instantiates the
 * Etzhayyim SDK from env bindings, calls the rw-free function with parsed input,
 * and maps status codes to HTTP responses.
 *
 * Routes organized into 5 sub-namespaces:
 * - ai.gftd.yoro.health
 * - ai.gftd.yoro.activity.*
 * - ai.gftd.yoro.feed.*
 * - ai.gftd.yoro.graph.*
 * - ai.gftd.yoro.actor.*
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

async function unispscInvokeAgent(
  _e: Etzhayyim,
  input: unknown,
): Promise<unknown> {
  const body = (input ?? {}) as { code?: string };
  const code = body.code?.toString() ?? "";
  if (!UNISPSC_CODE_INDEX.has(code)) {
    return { status: "notFound", error: "AgentNotFound", code };
  }
  // Phase α: this adapter is read-only. invokeAgent dispatches to the
  // Murakumo cell-runner (UnispscAgentExecutorCell, sharded across joseph/
  // issachar/dan per fleet.toml). The bridge requires a service binding +
  // mTLS to the LAN-side cell-runner that is not yet provisioned.
  return {
    status: "notReady",
    error: "ExecutorBindingNotConfigured",
    message:
      "invokeAgent requires the UnispscAgentExecutorCell bridge; see ADR-2605192415 + fleet.toml",
    code,
  };
}

const routes: Record<string, RouteConfig> = {
  // unispsc registry — bundled rw-free Phase α implementation.
  ["ai.gftd.apps.unispsc.health"]: { method: "GET", handler: unispscHealth },
  ["ai.gftd.apps.unispsc.listAgents"]: { method: "GET", handler: unispscListAgents },
  ["ai.gftd.apps.unispsc.classify"]: { method: "POST", handler: unispscClassify },
  ["ai.gftd.apps.unispsc.invokeAgent"]: { method: "POST", handler: unispscInvokeAgent },

  // Health & Registry
  ["ai.gftd.yoro.health"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.health(e, input as any),
  },
  ["ai.gftd.yoro.stats"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.stats(e, input as any),
  },

  // Activity
  ["ai.gftd.yoro.activity.listActivities"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listActivities(e, input as any),
  },
  ["ai.gftd.yoro.activity.getActivityTrace"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getActivityTrace(e, input as any),
  },
  ["ai.gftd.yoro.activity.markSeen"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.markSeen(e, input as any),
  },

  // Feed
  ["ai.gftd.yoro.feed.getTimeline"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getTimeline(e, input as any),
  },
  ["ai.gftd.yoro.feed.getAuthorFeed"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getAuthorFeed(e, input as any),
  },
  ["ai.gftd.yoro.feed.getPostThread"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getPostThread(e, input as any),
  },
  ["ai.gftd.yoro.feed.getRankedFeed"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getRankedFeed(e, input as any),
  },
  ["ai.gftd.yoro.feed.getDiscoverFeed"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getDiscoverFeed(e, input as any),
  },

  // Graph
  ["ai.gftd.yoro.graph.getFollowers"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getFollowers(e, input as any),
  },
  ["ai.gftd.yoro.graph.getFollows"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getFollows(e, input as any),
  },

  // Actor / Profile
  ["ai.gftd.yoro.actor.getProfile"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.getProfile(e, input as any),
  },
  ["ai.gftd.yoro.actor.searchActors"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.searchActors(e, input as any),
  },

  // Registry / Ingest
  ["ai.gftd.yoro.registry.projectEntity"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.projectEntity(e, input as any),
  },
  ["ai.gftd.yoro.registry.productResearch"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.productResearch(e, input as any),
  },
  ["ai.gftd.yoro.registry.activitySeen"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.activitySeen(e, input as any),
  },
  ["ai.gftd.yoro.registry.shinkaEvolution"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.shinkaEvolution(e, input as any),
  },
  ["ai.gftd.yoro.registry.shinkaKnowledge"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.shinkaKnowledge(e, input as any),
  },
  ["ai.gftd.yoro.registry.ingestProductCategory"]: {
    method: "POST",
    handler: (e, input) => yoroRwFree.ingestProductCategory(e, input as any),
  },
  ["ai.gftd.yoro.registry.listApps"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listApps(e, input as any),
  },
  ["ai.gftd.yoro.registry.listPosts"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listPosts(e, input as any),
  },
  ["ai.gftd.yoro.registry.listProductResearch"]: {
    method: "GET",
    handler: (e, input) => yoroRwFree.listProductResearch(e, input as any),
  },
};

function mapStatus(status?: string): number {
  if (status === "rejected") return 400;
  if (status === "notFound" || status === "invalidId") return 400;
  if (status === "alreadyExists") return 200;
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
