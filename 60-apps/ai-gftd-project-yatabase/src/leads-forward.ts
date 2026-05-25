// leads-forward.ts — XRPC shim from yatabase CF Worker to lg-yatabase pod
// for vertex_lead writes + reads. Mirrors auth-forward.ts.
//
// Per ADR-2605111200 the Worker is edge-only; the pod owns vertex_lead.
// The Worker still resolves admin auth on its side (x-yata-admin-key)
// before forwarding — pod trust is via x-internal-trust HMAC only.

import { forwardBmc, type ForwardEnv, type ForwardIdentity, type ForwardResult } from "./bmc-forward";

const SYSTEM_IDENTITY: ForwardIdentity = {
  did: "agent:yatabase-worker",
  orgDid: "agent:yatabase-worker",
};

function withTrace(traceId?: string): ForwardIdentity {
  return traceId ? { ...SYSTEM_IDENTITY, traceId } : SYSTEM_IDENTITY;
}

export async function forwardLeadIngest(
  env: ForwardEnv,
  body: Record<string, unknown>,
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "POST", "app.etzhayyim.apps.yata.leadIngest", body, withTrace(traceId), { timeoutMs: 20_000 });
}

export async function forwardLeadList(
  env: ForwardEnv,
  query: { status?: string; domain?: string; limit?: number },
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "GET", "app.etzhayyim.apps.yata.leadList", query as Record<string, unknown>, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadGet(
  env: ForwardEnv,
  vertex_id: string,
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "GET", "app.etzhayyim.apps.yata.leadGet", { vertex_id }, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadSetOutreachStatus(
  env: ForwardEnv,
  body: { vertex_id: string; status: string },
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "POST", "app.etzhayyim.apps.yata.leadSetOutreachStatus", body as Record<string, unknown>, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadSetContactEmail(
  env: ForwardEnv,
  body: { vertex_id: string; email: string },
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "POST", "app.etzhayyim.apps.yata.leadSetContactEmail", body as Record<string, unknown>, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadSetEnrichment(
  env: ForwardEnv,
  body: { vertex_id: string; contact_email?: string; tech_stack?: string[] },
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "POST", "app.etzhayyim.apps.yata.leadSetEnrichment", body as Record<string, unknown>, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadMarkDrafted(
  env: ForwardEnv,
  body: { vertex_id: string; outbox_id: string },
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "POST", "app.etzhayyim.apps.yata.leadMarkDrafted", body as Record<string, unknown>, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadReady(
  env: ForwardEnv,
  limit: number,
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "GET", "app.etzhayyim.apps.yata.leadReady", { limit }, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadSendable(
  env: ForwardEnv,
  limit: number,
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "GET", "app.etzhayyim.apps.yata.leadSendable", { limit }, withTrace(traceId), { timeoutMs: 10_000 });
}

export async function forwardLeadNeedsEnrichment(
  env: ForwardEnv,
  limit: number,
  traceId?: string,
): Promise<ForwardResult> {
  return forwardBmc(env, "GET", "app.etzhayyim.apps.yata.leadNeedsEnrichment", { limit }, withTrace(traceId), { timeoutMs: 10_000 });
}
