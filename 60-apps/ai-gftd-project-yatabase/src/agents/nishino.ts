// agents/nishino.ts — Sales / GTM agent.
//
// Loop:
//   1. Aggregate vertex_billing_event last 24h SUM(qty) GROUP BY org_did, metric.
//   2. For each org, resolve plan via plan-quota. Compute api_request used /
//      daily cap → headroom %.
//   3. If headroom < 25% on a non-enterprise plan, draft an upgrade-nudge
//      outbox row addressed to the tenant's owner.
//   4. Also: orgs that signed up >24h ago and have made <100 api_request
//      get an onboarding-nudge.
//
// All emissions land in vertex_email_outbox with kind='sales-quota-nudge' /
// 'sales-onboarding-nudge'. Without RESEND_API_KEY the rows queue in
// 'queued-no-recipient' state — a human reviews the staff inbox first
// before activating direct send (avoids spam from a misfiring agent).

import type { AgentEnv, AgentInput, AgentRunReport, AgentAction } from "./types";
import { newRunId } from "./registry";
import { resolvePlan, PLAN_RULES, type PlanTier } from "../plan-quota";
import { emitOutbox } from "../email-outbox";
import { leadsReadyForOutreach, markLeadDrafted } from "../leads";

interface AnyDb {}
interface SqlTag {
  (parts: TemplateStringsArray, ...vals: unknown[]): {
    execute(db: AnyDb): Promise<{ rows: Array<Record<string, unknown>> }>;
  };
}

async function loadDb(env: AgentEnv): Promise<{ db: AnyDb; sql: SqlTag } | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    const db = (sdk as { createKyselyDb: (h: unknown) => unknown }).createKyselyDb(
      env.HYPERDRIVE as never,
    ) as AnyDb;
    const sql = (sdk as { sql?: SqlTag }).sql ?? null;
    if (!sql) return null;
    return { db, sql };
  } catch {
    return null;
  }
}

interface OrgUsageRow {
  orgDid: string;
  apiRequest: number;
  storageGbHour: number;
}

const NUDGE_HEADROOM_PCT = 25;
const ONBOARDING_QUIET_THRESHOLD = 100;

export async function runNishino(
  env: AgentEnv,
  input?: AgentInput,
): Promise<AgentRunReport> {
  const t0 = Date.now();
  const startedAt = new Date(t0).toISOString();
  const runId = newRunId();
  const dryRun = input?.dryRun ?? false;
  const cap = input?.maxActions ?? 25;

  const r = await loadDb(env);
  if (!r) {
    return {
      ok: false,
      agent: "nishino",
      role: "sales",
      did: "did:web:yatabase.etzhayyim.com:actor:nishino",
      runId,
      startedAt,
      durationMs: Date.now() - t0,
      actionsCount: 0,
      actions: [],
      error: "no Hyperdrive binding",
      dryRun,
    };
  }
  const { db, sql } = r;

  const since = Date.now() - 24 * 3600 * 1000;
  const usage: OrgUsageRow[] = [];
  try {
    const q = sql`
      SELECT org_did,
             SUM(CASE WHEN metric = 'api_request'   THEN qty ELSE 0 END) AS api_req,
             SUM(CASE WHEN metric = 'storage_gb_hour' THEN qty ELSE 0 END) AS storage_gb
      FROM vertex_billing_event
      WHERE ts_ms >= ${since}
      GROUP BY org_did
      ORDER BY api_req DESC
      LIMIT 200
    `;
    const res = await q.execute(db);
    for (const row of res.rows ?? []) {
      const orgDid = String(row.org_did ?? "");
      if (!orgDid) continue;
      usage.push({
        orgDid,
        apiRequest: Number(row.api_req ?? 0),
        storageGbHour: Number(row.storage_gb ?? 0),
      });
    }
  } catch (e) {
    return {
      ok: false,
      agent: "nishino",
      role: "sales",
      did: "did:web:yatabase.etzhayyim.com:actor:nishino",
      runId,
      startedAt,
      durationMs: Date.now() - t0,
      actionsCount: 0,
      actions: [],
      error: e instanceof Error ? e.message.slice(0, 300) : String(e).slice(0, 300),
      dryRun,
    };
  }

  // Discover quiet new tenants (signed up >24h ago, low traffic).
  const quietOrgs: string[] = [];
  try {
    const q = sql`
      SELECT owner_did, MIN(created_at) AS first_signup
      FROM vertex_api_key
      WHERE owner_did LIKE 'did:web:t-%.yata-tenant.etzhayyim.com'
      GROUP BY owner_did
      HAVING MIN(created_at) <= ${new Date(since).toISOString()}
      LIMIT 100
    `;
    const res = await q.execute(db);
    for (const row of res.rows ?? []) {
      const did = String(row.owner_did ?? "");
      if (did) quietOrgs.push(did);
    }
  } catch {
    /* if api_key table query fails, skip onboarding pass */
  }

  const actions: AgentAction[] = [];

  // Pass 1: quota nudges.
  for (const u of usage) {
    if (actions.length >= cap) break;
    const plan: PlanTier = await resolvePlan(env, u.orgDid).catch(() => "free");
    if (plan === "enterprise") continue;
    const rules = PLAN_RULES[plan];
    if (rules.apiRequestPerDay == null) continue;
    const headroomPct = Math.max(
      0,
      ((rules.apiRequestPerDay - u.apiRequest) / rules.apiRequestPerDay) * 100,
    );
    if (headroomPct >= NUDGE_HEADROOM_PCT) continue;
    const nextPlan: PlanTier =
      plan === "free" ? "starter" : plan === "starter" ? "developer" : "business";
    const nextUsd = PLAN_RULES[nextPlan].monthlyUsd;
    const subject =
      `[Yatabase] You're at ${(100 - headroomPct).toFixed(0)}% of your ${plan} daily quota — upgrade to ${nextPlan}?`;
    const body = [
      `Hi,`,
      ``,
      `Your tenant ${u.orgDid} used ${u.apiRequest.toLocaleString()} api_request in the last 24h —`,
      `that's ${(100 - headroomPct).toFixed(1)}% of the ${plan} plan's ${rules.apiRequestPerDay.toLocaleString()}/day cap.`,
      ``,
      `Recommended next step: upgrade to ${nextPlan} ($${nextUsd}/month, ~¥${(nextUsd * 150).toLocaleString()}).`,
      `Visit Studio → Plan, or hit POST /auth/v1/upgrade with {"plan":"${nextPlan}"}.`,
      ``,
      `— Nishino (Yatabase sales agent)`,
    ].join("\n");

    if (!dryRun) {
      const r2 = await emitOutbox(env, {
        orgDid: u.orgDid,
        kind: "sales-quota-nudge",
        subject,
        bodyText: body,
      }).catch(() => ({ status: "error" }));
      actions.push({
        kind: "sales-quota-nudge",
        target: u.orgDid,
        summary: `${plan} → ${nextPlan} nudge (${(100 - headroomPct).toFixed(0)}% used)`,
        outboxId: r2.status,
      });
    } else {
      actions.push({
        kind: "sales-quota-nudge[dry]",
        target: u.orgDid,
        summary: `would nudge ${plan} → ${nextPlan}`,
      });
    }
  }

  // Pass 2: onboarding nudges (quiet tenants).
  const usedSet = new Set(usage.filter((u) => u.apiRequest > ONBOARDING_QUIET_THRESHOLD).map((u) => u.orgDid));
  for (const did of quietOrgs) {
    if (actions.length >= cap) break;
    if (usedSet.has(did)) continue;
    const subject = `[Yatabase] Welcome — need help making your first Cypher call?`;
    const body = [
      `Hi,`,
      ``,
      `Your Yatabase tenant ${did} signed up over 24 hours ago and hasn't run`,
      `many requests yet. Common first paths:`,
      ``,
      `  • POST /cypher  body: {"query":"CREATE (n:Demo {name:'hello'}) RETURN n"}`,
      `  • POST /storage/v1/object/test/hello.txt  body: any bytes`,
      `  • POST /mcp     body: {"jsonrpc":"2.0","method":"tools/list","id":1}`,
      ``,
      `Free tier is unlimited until you hit 1,000 api_request/day. Stuck?`,
      `Reply to this email and Sakamoto (CS agent) will pick it up.`,
      ``,
      `— Nishino (Yatabase sales agent)`,
    ].join("\n");
    if (!dryRun) {
      const r2 = await emitOutbox(env, {
        orgDid: did,
        kind: "sales-onboarding-nudge",
        subject,
        bodyText: body,
      }).catch(() => ({ status: "error" }));
      actions.push({
        kind: "sales-onboarding-nudge",
        target: did,
        summary: `onboarding nudge for quiet new tenant`,
        outboxId: r2.status,
      });
    } else {
      actions.push({
        kind: "sales-onboarding-nudge[dry]",
        target: did,
        summary: `would onboarding-nudge`,
      });
    }
  }

  // Pass 3: cold outreach to fresh vertex_lead rows.
  // Compliance: each draft lands in vertex_email_outbox with kind='marketing-outbound',
  // status='queued-no-recipient' if contact_email is blank. Human reviewer
  // approves the recipient + body before send (CCPA §1798.120 / GDPR Art 6).
  const leadCap = Math.max(0, (input?.maxActions ?? 25) - actions.length);
  const freshLeads = leadCap > 0 ? await leadsReadyForOutreach(env, Math.min(10, leadCap)) : [];
  for (const lead of freshLeads) {
    if (actions.length >= cap) break;
    const subject = `[Yatabase] One graph DB + S3-style storage for ${lead.company} — open Studio?`;
    const body = [
      `Hi ${lead.company} team,`,
      ``,
      `Saw your team via ${lead.signal || "public signal"} — wanted to share Yatabase:`,
      ``,
      `  • Real-time graph DB (Cypher subset + SPARQL 1.1) on RisingWave`,
      `  • S3-compatible object storage with public ACL on demand`,
      `  • MCP-native: every surface is callable as a tool by your AI agents`,
      `  • One bill, no BWA egress fees, AT Protocol identity`,
      ``,
      `Free tier $0/month → 1k api_request/day. Try it in 30 seconds:`,
      ``,
      `    curl -X POST https://yatabase.etzhayyim.com/auth/v1/signup`,
      ``,
      `Or browse https://yatabase.etzhayyim.com/ for the full pitch + pricing.`,
      ``,
      `If this isn't relevant, hit reply and I'll close the loop.`,
      ``,
      `— Nishino (Yatabase sales agent, etz hayim)`,
    ].join("\n");

    if (!dryRun) {
      const r2 = await emitOutbox(env, {
        // Lead is yatabase's CRM data, not a tenant — use the operator org_did
        // so the outbox row sits in the staff inbox, not a customer's.
        orgDid: "did:web:yatabase.etzhayyim.com",
        recipientEmail: lead.contact_email || undefined,
        recipientName: lead.company,
        kind: "sales-onboarding-nudge",   // cold-outreach reuses onboarding kind
        subject,
        bodyText: body,
      }).catch(() => ({ status: "error", vertexId: undefined as string | undefined }));
      // Store the outbox row's vertex_id (not just the status string) so
      // the future /api/leads/{id}/send can correlate the lead to its draft.
      // Falls back to the status string if vertexId wasn't returned (older
      // emitOutbox shape).
      const outboxRef = r2.vertexId ?? r2.status;
      await markLeadDrafted(env, lead.vertex_id, outboxRef).catch(() => {});
      actions.push({
        kind: "marketing-cold-outreach",
        target: lead.domain,
        summary: `${lead.company} (fit=${lead.fit_score}) — drafted to ${lead.contact_email || "[no email yet]"}`,
        outboxId: outboxRef,
      });
    } else {
      actions.push({
        kind: "marketing-cold-outreach[dry]",
        target: lead.domain,
        summary: `would draft for ${lead.company}`,
      });
    }
  }

  return {
    ok: true,
    agent: "nishino",
    role: "sales",
    did: "did:web:yatabase.etzhayyim.com:actor:nishino",
    runId,
    startedAt,
    durationMs: Date.now() - t0,
    actionsCount: actions.length,
    actions,
    notes: `scanned ${usage.length} active orgs, ${quietOrgs.length} quiet new tenants, ${freshLeads.length} fresh leads`,
    dryRun,
  };
}
