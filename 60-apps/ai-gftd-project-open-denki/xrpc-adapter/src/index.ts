/**
 * open-denki XRPC adapter — CF Worker.
 *
 * Wires the rw-free reference impl (12 pure TS functions) into a deployable
 * CF Worker that exposes each function as an XRPC endpoint.
 *
 * Per ADR-2605210000 first execution-layer demonstration.
 */

import { Etzhayyim } from "@etzhayyim/sdk";
import * as openDenkiRwFree from "@etzhayyim/open-denki-rw-free";

interface Env {
  ACTOR_DID: string;
  PDS_URL: string;
  L2_RPC_URL: string;
}

type Handler = (e: Etzhayyim, input: unknown) => Promise<unknown>;

const NSID_BASE = "ai.gftd.apps.openDenki";

interface RouteConfig {
  method: "POST" | "GET";
  handler: Handler;
}

const routes: Record<string, RouteConfig> = {
  [`${NSID_BASE}.defineGenerationNode`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.defineGenerationNode(e, input as any),
  },
  [`${NSID_BASE}.defineSubstation`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.defineSubstation(e, input as any),
  },
  [`${NSID_BASE}.defineFeeder`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.defineFeeder(e, input as any),
  },
  [`${NSID_BASE}.registerSmartMeter`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.registerSmartMeter(e, input as any),
  },
  [`${NSID_BASE}.getNode`]: {
    method: "GET",
    handler: (e, input) => openDenkiRwFree.getNode(e, input as any),
  },
  [`${NSID_BASE}.recordMeterReading`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.recordMeterReading(e, input as any),
  },
  [`${NSID_BASE}.reportFault`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.reportFault(e, input as any),
  },
  [`${NSID_BASE}.recordDemandResponse`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.recordDemandResponse(e, input as any),
  },
  [`${NSID_BASE}.recordRenewableOutput`]: {
    method: "POST",
    handler: (e, input) => openDenkiRwFree.recordRenewableOutput(e, input as any),
  },
  [`${NSID_BASE}.listFeeders`]: {
    method: "GET",
    handler: (e, input) => openDenkiRwFree.listFeeders(e, input as any),
  },
  [`${NSID_BASE}.listFaults`]: {
    method: "GET",
    handler: (e, input) => openDenkiRwFree.listFaults(e, input as any),
  },
  [`${NSID_BASE}.listReadings`]: {
    method: "GET",
    handler: (e, input) => openDenkiRwFree.listReadings(e, input as any),
  },
};

function mapStatus(status?: string): number {
  if (status === "rejected" || status === "notFound") return 400;
  return 200;
}

function jsonResponse(body: unknown, status: number = 200, init?: ResponseInit): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...init?.headers },
    ...init,
  });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/xrpc/")) return jsonResponse({ error: "NotFound" }, 404);

    const nsid = url.pathname.slice("/xrpc/".length);
    const route = routes[nsid];
    if (!route) return jsonResponse({ error: "MethodNotFound", nsid }, 404);
    if (req.method !== route.method) return jsonResponse({ error: "MethodNotAllowed" }, 405);

    const e = new Etzhayyim({
      did: env.ACTOR_DID,
      pdsUrl: env.PDS_URL,
      l2RpcUrl: env.L2_RPC_URL,
    });

    let input: unknown;
    try {
      input = route.method === "POST" ? await req.json().catch(() => ({})) : Object.fromEntries(url.searchParams.entries());
      const typed = input as Record<string, unknown>;
      ["limit", "offset", "maxScan", "capacityKw", "primaryVoltageKv", "secondaryVoltageKv", "capacityMva", "customerCount", "lengthM", "kwhCumulative", "kwDemand", "voltageV", "deviationPercentPermille", "affectedCustomers"].forEach(k => {
        if (typed[k]) typed[k] = Number(typed[k]);
      });
    } catch (err) {
      return jsonResponse({ error: "InvalidInput", message: `Failed to parse ${route.method === "POST" ? "JSON" : "query params"}` }, 400);
    }

    try {
      const result = await route.handler(e, input);
      return jsonResponse(result, mapStatus((result as any)?.status));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return jsonResponse({ error: "InternalError", message, nsid }, 500);
    }
  },
} satisfies ExportedHandler<Env>;
