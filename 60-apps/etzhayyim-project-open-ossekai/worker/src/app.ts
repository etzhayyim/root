// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

// open-ossekai — L1/L2/L3 intelligence + Well-Becoming coaching actor (ADR-0056 BPMN-as-actor)
//
// Write commands (→ BPMN dispatcher):
//   generateIntelBrief          (proc)  L1 LLM intel brief for target actor
//   proposeArbitrageBrief       (proc)  L2 LLM arbitrage proposal for supply/demand gap
//   requestOssekaiConsent       (proc)  L3 consent gate (Tier 3 PII, ADR-0018)
//   scoreJocho                  (proc)  L3 5-axis jocho scoring (consent required)
//   generateWellBecomingPlan    (proc)  L3 Well-Becoming kyu/dan coaching plan
//
// Read queries (→ Hyperdrive/RisingWave):
//   getOssekaiStatus            (query) per-actor signal/brief/arbitrage/plan summary
//   listIntelBriefs             (query) paginated intel briefs
//   listArbitrageOpportunities  (query) paginated open arbitrage opportunities

import {
  asAgentTool,
  createKyselyDb,
  createWorkerExport,
  nsid,
  parseLexiconInput,
  sql,
  type HostSDK,
  withCapabilityTags,
} from "@etzhayyim/kotodama-host-sdk";

type InternalSecret = string | { get(): Promise<string> };
type EnvLike = { DISPATCHER_URL?: string; HYPERDRIVE?: unknown; DISPATCHER_INTERNAL_SECRET?: InternalSecret };

function envOf(sdk: unknown): EnvLike {
  return ((sdk as { env?: EnvLike }).env ?? {}) as EnvLike;
}

function dispatcherUrl(sdk: unknown): string {
  return envOf(sdk).DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com";
}

async function internalTrustHeader(sdk: unknown): Promise<string> {
  const binding = envOf(sdk).DISPATCHER_INTERNAL_SECRET;
  if (!binding) return "";
  try {
    return typeof binding === "string" ? binding : await binding.get();
  } catch { return ""; }
}

function clampLimit(value: unknown, fallback = 20): number {
  const n = Number(value ?? fallback);
  return Number.isFinite(n) ? Math.max(1, Math.min(200, Math.floor(n))) : fallback;
}

async function proxyToBpmn(sdk: HostSDK, toolNsid: string, input: unknown): Promise<string> {
  const started = Date.now();
  const trust = await internalTrustHeader(sdk);
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (trust) headers["x-internal-trust"] = trust;
  const resp = await fetch(`${dispatcherUrl(sdk)}/xrpc/${toolNsid}`, {
    method: "POST",
    headers,
    body: JSON.stringify(input ?? {}),
  });
  const text = await resp.text();
  let result: unknown;
  try { result = text ? JSON.parse(text) : {}; }
  catch { result = { raw: text }; }
  return JSON.stringify({ ok: resp.ok, status: resp.status, nsid: toolNsid, result, latencyMs: Date.now() - started });
}

async function getOssekaiStatus(_sdk: HostSDK, body: Uint8Array): Promise<string> {
  const p = parseLexiconInput("com.etzhayyim.apps.openOssekai.getOssekaiStatus", coerceQueryParams(body)) as any;
  const targetDid = String(p.targetDid ?? "");
  if (!targetDid) return JSON.stringify({ error: "targetDid required" });

  const db = createKyselyDb();

  const [sigRow, briefRow, arbRow, planRow] = await Promise.all([
    db.selectFrom("mv_ossekai_signal_recent" as any)
      .select(["signal_count" as any, "avg_sentiment" as any])
      .where("target_did" as any, "=", targetDid)
      .limit(1).execute(),
    db.selectFrom("vertex_ossekai_brief" as any)
      .select(["brief_id" as any, "title" as any])
      .where("target_did" as any, "=", targetDid)
      .orderBy("generated_at" as any, "desc")
      .limit(1).execute(),
    db.selectFrom("mv_ossekai_arbitrage_open" as any)
      .select(sql<number>`count(*)`.as("cnt"))
      .executeTakeFirst(),
    db.selectFrom("vertex_ossekai_wellbecoming_plan" as any)
      .select(["status" as any, "jocho_score" as any, "current_kyu_dan" as any, "consent_did" as any])
      .where("target_did" as any, "=", targetDid)
      .orderBy("created_at" as any, "desc")
      .limit(1).execute(),
  ]);

  const plan = planRow[0] as any;
  return JSON.stringify({
    targetDid,
    signalCount: Number((sigRow[0] as any)?.signal_count ?? 0),
    latestBriefId: String((briefRow[0] as any)?.brief_id ?? ""),
    latestBriefTitle: String((briefRow[0] as any)?.title ?? ""),
    openArbCount: Number((arbRow as any)?.cnt ?? 0),
    kyuDanPlan: String(plan?.current_kyu_dan ?? ""),
    jochoScore: Number(plan?.jocho_score ?? 0),
    consentStatus: String(plan?.status ?? "none"),
  });
}

function coerceQueryParams(body: Uint8Array): Uint8Array {
  try {
    const raw = JSON.parse(new TextDecoder().decode(body)) as Record<string, unknown>;
    if (raw.limit !== undefined) raw.limit = Number(raw.limit);
    if (raw.offset !== undefined) raw.offset = Number(raw.offset);
    return new TextEncoder().encode(JSON.stringify(raw));
  } catch { return body; }
}

async function listIntelBriefs(_sdk: HostSDK, body: Uint8Array): Promise<string> {
  const p = parseLexiconInput("com.etzhayyim.apps.openOssekai.listIntelBriefs", coerceQueryParams(body)) as any;
  const limit = clampLimit(p.limit, 20);
  const offset = Math.max(0, Math.floor(Number(p.offset ?? 0) || 0));
  const db = createKyselyDb();

  let qb = db.selectFrom("vertex_ossekai_brief" as any).selectAll() as any;
  if (p.targetDid) qb = qb.where("target_did", "=", String(p.targetDid));

  const [rows, countRow] = await Promise.all([
    qb.orderBy("generated_at", "desc").limit(limit).offset(offset).execute(),
    (p.targetDid
      ? db.selectFrom("vertex_ossekai_brief" as any).select(sql<number>`count(*)`.as("cnt")).where("target_did" as any, "=", String(p.targetDid))
      : db.selectFrom("vertex_ossekai_brief" as any).select(sql<number>`count(*)`.as("cnt"))
    ).executeTakeFirst(),
  ]);

  return JSON.stringify({
    briefs: (rows as any[]).map((r: any) => ({
      briefId: r.brief_id,
      targetDid: r.target_did,
      targetHandle: r.target_handle ?? undefined,
      title: r.title,
      summary: r.summary,
      keySignals: r.key_signals,
      confidenceScore: r.confidence_score,
      generatedAt: r.generated_at,
    })),
    total: Number((countRow as any)?.cnt ?? 0),
    limit,
    offset,
  });
}

async function listArbitrageOpportunities(_sdk: HostSDK, body: Uint8Array): Promise<string> {
  const p = parseLexiconInput("com.etzhayyim.apps.openOssekai.listArbitrageOpportunities", coerceQueryParams(body)) as any;
  const limit = clampLimit(p.limit, 20);
  const offset = Math.max(0, Math.floor(Number(p.offset ?? 0) || 0));
  const db = createKyselyDb();

  let qb = db.selectFrom("vertex_ossekai_arbitrage" as any).selectAll().where("status" as any, "=", "open") as any;
  if (p.opportunityKind) qb = qb.where("opportunity_kind", "=", String(p.opportunityKind));

  let cqb = db.selectFrom("vertex_ossekai_arbitrage" as any).select(sql<number>`count(*)`.as("cnt")).where("status" as any, "=", "open") as any;
  if (p.opportunityKind) cqb = cqb.where("opportunity_kind", "=", String(p.opportunityKind));

  const [rows, countRow] = await Promise.all([
    qb.orderBy("estimated_value", "desc").limit(limit).offset(offset).execute(),
    cqb.executeTakeFirst(),
  ]);

  return JSON.stringify({
    opportunities: (rows as any[]).map((r: any) => ({
      arbId: r.arb_id,
      opportunityKind: r.opportunity_kind,
      gapDescription: r.gap_description,
      estimatedValue: r.estimated_value,
      confidenceScore: r.confidence_score,
      recommendedAction: r.recommended_action,
      status: r.status,
      createdAt: r.created_at,
    })),
    total: Number((countRow as any)?.cnt ?? 0),
    limit,
    offset,
  });
}

export default createWorkerExport((sdk) => {
  sdk.app
    .command(
      nsid("com.etzhayyim.apps.openOssekai.generateIntelBrief"),
      (_ctx, body) => proxyToBpmn(sdk, "com.etzhayyim.apps.openOssekai.generateIntelBrief",
        parseLexiconInput("com.etzhayyim.apps.openOssekai.generateIntelBrief", body)),
      asAgentTool("Generate an LLM-powered intel brief for a target actor (L1 OSINT)."),
      withCapabilityTags("ossekai", "intel", "l1", "bpmn"),
    )
    .command(
      nsid("com.etzhayyim.apps.openOssekai.proposeArbitrageBrief"),
      (_ctx, body) => proxyToBpmn(sdk, "com.etzhayyim.apps.openOssekai.proposeArbitrageBrief",
        parseLexiconInput("com.etzhayyim.apps.openOssekai.proposeArbitrageBrief", body)),
      asAgentTool("Propose an LLM-powered arbitrage action for a supply/demand gap (L2)."),
      withCapabilityTags("ossekai", "arbitrage", "l2", "bpmn"),
    )
    .command(
      nsid("com.etzhayyim.apps.openOssekai.requestOssekaiConsent"),
      (_ctx, body) => proxyToBpmn(sdk, "com.etzhayyim.apps.openOssekai.requestOssekaiConsent",
        parseLexiconInput("com.etzhayyim.apps.openOssekai.requestOssekaiConsent", body)),
      asAgentTool("Request consent for Well-Becoming coaching (L3, ADR-0018 Tier 3 PII gate)."),
      withCapabilityTags("ossekai", "consent", "l3", "pii-tier3", "bpmn"),
    )
    .command(
      nsid("com.etzhayyim.apps.openOssekai.scoreJocho"),
      (_ctx, body) => proxyToBpmn(sdk, "com.etzhayyim.apps.openOssekai.scoreJocho",
        parseLexiconInput("com.etzhayyim.apps.openOssekai.scoreJocho", body)),
      asAgentTool("Score a consented actor on 5 jocho axes: engagement, competence, contribution, growth, resilience (L3)."),
      withCapabilityTags("ossekai", "jocho", "l3", "wellbecoming", "bpmn"),
    )
    .command(
      nsid("com.etzhayyim.apps.openOssekai.generateWellBecomingPlan"),
      (_ctx, body) => proxyToBpmn(sdk, "com.etzhayyim.apps.openOssekai.generateWellBecomingPlan",
        parseLexiconInput("com.etzhayyim.apps.openOssekai.generateWellBecomingPlan", body)),
      asAgentTool("Generate a Well-Becoming kyu/dan coaching roadmap with 30-day action items (L3)."),
      withCapabilityTags("ossekai", "wellbecoming", "kyu-dan", "l3", "bpmn"),
    )
    .query(
      nsid("com.etzhayyim.apps.openOssekai.getOssekaiStatus"),
      (_ctx, body) => getOssekaiStatus(sdk, body),
    )
    .query(
      nsid("com.etzhayyim.apps.openOssekai.listIntelBriefs"),
      (_ctx, body) => listIntelBriefs(sdk, body),
    )
    .query(
      nsid("com.etzhayyim.apps.openOssekai.listArbitrageOpportunities"),
      (_ctx, body) => listArbitrageOpportunities(sdk, body),
    );
}, { mcpRegistry: {} });
