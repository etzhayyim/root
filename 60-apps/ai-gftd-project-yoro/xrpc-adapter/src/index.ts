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

const routes: Record<string, RouteConfig> = {
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
