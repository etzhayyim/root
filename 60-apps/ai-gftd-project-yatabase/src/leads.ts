// leads.ts — top-of-funnel CRM persistence (vertex_lead).
//
// Used by:
//   - POST /api/leads/ingest      — admin-keyed ingestion from external scrapers
//                                    (HN scrape, GitHub stars, Common Crawl, manual)
//   - GET  /api/leads             — admin-keyed list + filter for human review
//   - nishino agent (3rd pass)    — drafts cold outreach for new rows, advances
//                                    outreach_status NULL → drafted
//   - lg-yatabase marketing graph — full LLM-driven enrichment + scoring (P19)

interface AnyDb {}
interface SqlExec<R = unknown> { execute(db: AnyDb): Promise<R>; }
interface SqlTag {
  (parts: TemplateStringsArray, ...vals: unknown[]): SqlExec<{ rows: Array<Record<string, unknown>> }>;
}

export interface LeadsEnv {
  HYPERDRIVE?: unknown;
  RESEND_API_KEY?: string;
  EMAIL_FROM?: string;
  /** Post-ADR-2605111200: when set, all vertex_lead I/O forwards to lg-yatabase pod. */
  LG_YATABASE_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
}

async function loadDb(env: LeadsEnv): Promise<{ db: AnyDb; sql: SqlTag } | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
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

export interface LeadIngest {
  company: string;
  domain: string;
  contact_name?: string;
  contact_email?: string;
  source?: string;       // 'hn', 'github-stars', 'crunchbase', 'manual', …
  source_url?: string;
  signal?: string;       // why this lead matters in 1 sentence
  tech_stack?: string[]; // ["supabase","neo4j","postgres"]
  employees?: string;    // "1-10", "11-50", …
  fit_score?: number;    // 0-100; defaults to 0 (let scorer fill in later)
  reasoning?: string;
  notes?: string;
  force?: boolean;       // overwrite existing row (default: skip-if-exists)
}

export interface LeadIngestResult {
  ok: boolean;
  vertex_id: string;
  domain: string;
  outreach_status: string;
  message?: string;
}

function vertexIdForDomain(domain: string): string {
  return `lead:${domain.toLowerCase().replace(/[^a-z0-9.-]/g, "")}`;
}

const VALID_DOMAIN = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/i;

export async function handleLeadIngest(
  env: LeadsEnv,
  body: LeadIngest,
): Promise<{ status: number; result: LeadIngestResult | { error: string; message: string } }> {
  if (!body || typeof body !== "object") {
    return { status: 400, result: { error: "BadRequest", message: "JSON body required" } };
  }

  // Pod path (post-ADR-2605111200). Worker no longer touches Hyperdrive.
  if (env.LG_YATABASE_URL) {
    const { forwardLeadIngest } = await import("./leads-forward");
    const fwd = await forwardLeadIngest(env, body as unknown as Record<string, unknown>);
    if (fwd.ok) {
      const r = fwd.data as LeadIngestResult;
      return { status: 200, result: r };
    }
    const d = fwd.data as { error?: string; message?: string } | null;
    return {
      status: fwd.status === 400 ? 400 : 503,
      result: { error: d?.error ?? "ForwardFailed", message: d?.message ?? fwd.error ?? "lg-yatabase forward failed" },
    };
  }
  const company = String(body.company ?? "").trim().slice(0, 200);
  const domain = String(body.domain ?? "").trim().toLowerCase().slice(0, 200);
  if (!company || !domain) {
    return { status: 400, result: { error: "BadRequest", message: "company + domain required" } };
  }
  if (!VALID_DOMAIN.test(domain)) {
    return { status: 400, result: { error: "BadRequest", message: `invalid domain: ${domain}` } };
  }

  const r = await loadDb(env);
  if (!r) {
    return {
      status: 503,
      result: { error: "ServiceUnavailable", message: "Hyperdrive binding missing" },
    };
  }
  const { db, sql } = r;

  const vertexId = vertexIdForDomain(domain);
  const nowIso = new Date().toISOString();
  const techStack = Array.isArray(body.tech_stack) ? body.tech_stack.join(",") : "";
  const fitScore = Number.isFinite(body.fit_score) ? Math.min(100, Math.max(0, Number(body.fit_score))) : 0;

  // Idempotency: skip if a row already exists for this domain. The scraper
  // re-runs hourly and would otherwise PK-upsert the row (RW semantics)
  // and reset outreach_status='drafted' back to 'new', causing nishino to
  // double-draft. Caller can pass `force:true` to bypass and overwrite.
  if (!body.force) {
    try {
      const existingQ = sql`
        SELECT outreach_status FROM vertex_lead WHERE vertex_id = ${vertexId} LIMIT 1
      `;
      const existing = await existingQ.execute(db);
      if ((existing.rows ?? []).length > 0) {
        const status = String(existing.rows[0].outreach_status ?? "new");
        return {
          status: 200,
          result: {
            ok: true,
            vertex_id: vertexId,
            domain,
            outreach_status: status,
            message: `Lead already exists with outreach_status='${status}'; not re-ingested. Pass force:true to overwrite.`,
          },
        };
      }
    } catch (e) {
      // SELECT failure shouldn't block ingest — fall through to INSERT.
      console.warn("[yata][leads] dedup SELECT failed, proceeding with INSERT:", e);
    }
  }

  try {
    // RW PG path: PK INSERT acts as upsert (RW semantics — duplicate PK
    // overrides). We accept that — the latest enrichment wins and a fresh
    // outreach_status='new' resets the dedup window.
    const q = sql`
      INSERT INTO vertex_lead
        (vertex_id, company, domain, contact_name, contact_email,
         source, source_url, signal, tech_stack, employees,
         fit_score, reasoning, outreach_status, outreach_outbox,
         last_touch_at, notes, ingested_at, updated_at)
      VALUES
        (${vertexId},
         ${company},
         ${domain},
         ${(body.contact_name ?? "").slice(0, 200)},
         ${(body.contact_email ?? "").slice(0, 320)},
         ${(body.source ?? "manual").slice(0, 64)},
         ${(body.source_url ?? "").slice(0, 1024)},
         ${(body.signal ?? "").slice(0, 1024)},
         ${techStack.slice(0, 1024)},
         ${(body.employees ?? "").slice(0, 64)},
         ${fitScore},
         ${(body.reasoning ?? "").slice(0, 2048)},
         'new',
         '',
         '',
         ${(body.notes ?? "").slice(0, 2048)},
         ${nowIso},
         ${nowIso})
    `;
    await q.execute(db);
  } catch (e) {
    console.warn("[yata][leads] ingest insert failed:", e);
    return {
      status: 500,
      result: {
        error: "PersistFailed",
        message: e instanceof Error ? e.message.slice(0, 300) : "INSERT failed",
      },
    };
  }

  return {
    status: 200,
    result: {
      ok: true,
      vertex_id: vertexId,
      domain,
      outreach_status: "new",
      message: "Lead persisted; nishino will draft outreach on next /_agents/nishino/run.",
    },
  };
}

export interface LeadsListResult {
  count: number;
  leads: Array<Record<string, unknown>>;
}

export async function listLeads(
  env: LeadsEnv,
  filters: { status?: string; domain?: string; limit?: number },
): Promise<LeadsListResult> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadList } = await import("./leads-forward");
    const fwd = await forwardLeadList(env, filters);
    if (fwd.ok) return fwd.data as LeadsListResult;
    return { count: 0, leads: [] };
  }
  const r = await loadDb(env);
  if (!r) return { count: 0, leads: [] };
  const { db, sql } = r;
  const cap = Math.max(1, Math.min(200, filters.limit ?? 50));
  try {
    let q;
    if (filters.status && filters.domain) {
      q = sql`
        SELECT vertex_id, company, domain, contact_email, source, signal,
               fit_score, outreach_status, outreach_outbox, last_touch_at,
               ingested_at, updated_at
        FROM vertex_lead
        WHERE outreach_status = ${filters.status} AND domain = ${filters.domain}
        ORDER BY ingested_at DESC
        LIMIT ${cap}
      `;
    } else if (filters.status) {
      q = sql`
        SELECT vertex_id, company, domain, contact_email, source, signal,
               fit_score, outreach_status, outreach_outbox, last_touch_at,
               ingested_at, updated_at
        FROM vertex_lead
        WHERE outreach_status = ${filters.status}
        ORDER BY ingested_at DESC
        LIMIT ${cap}
      `;
    } else if (filters.domain) {
      q = sql`
        SELECT vertex_id, company, domain, contact_email, source, signal,
               fit_score, outreach_status, outreach_outbox, last_touch_at,
               ingested_at, updated_at
        FROM vertex_lead
        WHERE domain = ${filters.domain}
        ORDER BY ingested_at DESC
        LIMIT ${cap}
      `;
    } else {
      q = sql`
        SELECT vertex_id, company, domain, contact_email, source, signal,
               fit_score, outreach_status, outreach_outbox, last_touch_at,
               ingested_at, updated_at
        FROM vertex_lead
        ORDER BY ingested_at DESC
        LIMIT ${cap}
      `;
    }
    const res = await q.execute(db);
    return { count: (res.rows ?? []).length, leads: res.rows ?? [] };
  } catch (e) {
    console.warn("[yata][leads] list failed:", e);
    return { count: 0, leads: [] };
  }
}

/**
 * Read leads ready for outreach: outreach_status='new', limited.
 * Used by nishino's 3rd pass to grab a working set per run.
 */
export async function leadsReadyForOutreach(
  env: LeadsEnv,
  limit = 10,
): Promise<Array<{ vertex_id: string; company: string; domain: string; contact_email: string; signal: string; fit_score: number; }>> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadReady } = await import("./leads-forward");
    const fwd = await forwardLeadReady(env, limit);
    if (!fwd.ok) return [];
    const rows = (fwd.data as { leads?: Array<Record<string, unknown>> }).leads ?? [];
    return rows.map((row) => ({
      vertex_id: String(row.vertex_id ?? ""),
      company: String(row.company ?? ""),
      domain: String(row.domain ?? ""),
      contact_email: String(row.contact_email ?? ""),
      signal: String(row.signal ?? ""),
      fit_score: Number(row.fit_score ?? 0),
    }));
  }
  const r = await loadDb(env);
  if (!r) return [];
  const { db, sql } = r;
  const cap = Math.max(1, Math.min(50, limit));
  try {
    const q = sql`
      SELECT vertex_id, company, domain, contact_email, signal, fit_score
      FROM vertex_lead
      WHERE outreach_status = 'new'
      ORDER BY fit_score DESC, ingested_at ASC
      LIMIT ${cap}
    `;
    const res = await q.execute(db);
    return (res.rows ?? []).map((row) => ({
      vertex_id: String(row.vertex_id ?? ""),
      company: String(row.company ?? ""),
      domain: String(row.domain ?? ""),
      contact_email: String(row.contact_email ?? ""),
      signal: String(row.signal ?? ""),
      fit_score: Number(row.fit_score ?? 0),
    }));
  } catch (e) {
    console.warn("[yata][leads] readyForOutreach failed:", e);
    return [];
  }
}

/**
 * Single-row read by vertex_id. Returns the full lead shape (including
 * outreach_outbox + contact_email) so /send can build the recipient.
 */
export async function getLeadByVertexId(
  env: LeadsEnv,
  vertexId: string,
): Promise<{
  vertex_id: string;
  company: string;
  domain: string;
  contact_email: string;
  outreach_status: string;
  outreach_outbox: string;
  fit_score: number;
} | null> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadGet } = await import("./leads-forward");
    const fwd = await forwardLeadGet(env, vertexId);
    if (!fwd.ok) return null;
    const row = fwd.data as Record<string, unknown>;
    return {
      vertex_id: String(row.vertex_id ?? ""),
      company: String(row.company ?? ""),
      domain: String(row.domain ?? ""),
      contact_email: String(row.contact_email ?? ""),
      outreach_status: String(row.outreach_status ?? ""),
      outreach_outbox: String(row.outreach_outbox ?? ""),
      fit_score: Number(row.fit_score ?? 0),
    };
  }
  const r = await loadDb(env);
  if (!r) return null;
  const { db, sql } = r;
  try {
    const q = sql`
      SELECT vertex_id, company, domain, contact_email,
             outreach_status, outreach_outbox, fit_score
      FROM vertex_lead
      WHERE vertex_id = ${vertexId}
      LIMIT 1
    `;
    const res = await q.execute(db);
    if (!(res.rows ?? []).length) return null;
    const row = res.rows[0];
    return {
      vertex_id: String(row.vertex_id ?? ""),
      company: String(row.company ?? ""),
      domain: String(row.domain ?? ""),
      contact_email: String(row.contact_email ?? ""),
      outreach_status: String(row.outreach_status ?? ""),
      outreach_outbox: String(row.outreach_outbox ?? ""),
      fit_score: Number(row.fit_score ?? 0),
    };
  } catch (e) {
    console.warn("[yata][leads] getByVertexId failed:", e);
    return null;
  }
}

/**
 * Operator triage actions on a lead row. RW UPDATE returns rowcount=0
 * even on success (UpdateResult quirk per project CLAUDE.md), so we
 * fire-and-forget and trust the read replica to reflect within the
 * usual propagation window.
 *
 * status_pipeline:
 *   NULL → 'new' → 'drafted' → 'approved' → 'sent' → 'replied' / 'bounced'
 *                          \→ 'dismissed' (operator killed)
 */
export type LeadOpStatus = "approved" | "dismissed";

export async function setLeadOutreachStatus(
  env: LeadsEnv,
  vertexId: string,
  status: LeadOpStatus,
): Promise<{ ok: boolean; vertex_id: string; new_status: LeadOpStatus }> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadSetOutreachStatus } = await import("./leads-forward");
    const fwd = await forwardLeadSetOutreachStatus(env, { vertex_id: vertexId, status });
    return { ok: fwd.ok, vertex_id: vertexId, new_status: status };
  }
  const r = await loadDb(env);
  if (!r) return { ok: false, vertex_id: vertexId, new_status: status };
  const { db, sql } = r;
  const nowIso = new Date().toISOString();
  try {
    const q = sql`
      UPDATE vertex_lead
      SET outreach_status = ${status},
          last_touch_at = ${nowIso},
          updated_at = ${nowIso}
      WHERE vertex_id = ${vertexId}
    `;
    await q.execute(db);
  } catch (e) {
    console.warn(`[yata][leads] setStatus(${status}) failed:`, e);
    return { ok: false, vertex_id: vertexId, new_status: status };
  }
  return { ok: true, vertex_id: vertexId, new_status: status };
}

/**
 * Bulk-set fields populated by domain enrichment (homepage scrape).
 * One UPDATE statement so RW commits the bundle atomically — avoids
 * the race seen with sequential single-field UPDATEs.
 */
export async function setLeadEnrichment(
  env: LeadsEnv,
  vertexId: string,
  enrichment: { contact_email?: string; tech_stack?: string[] },
): Promise<{ ok: boolean; vertex_id: string; applied: { contact_email: string; tech_stack: string } }> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadSetEnrichment } = await import("./leads-forward");
    const fwd = await forwardLeadSetEnrichment(env, { vertex_id: vertexId, ...enrichment });
    if (fwd.ok) return fwd.data as { ok: boolean; vertex_id: string; applied: { contact_email: string; tech_stack: string } };
    return { ok: false, vertex_id: vertexId, applied: { contact_email: "", tech_stack: "" } };
  }
  const r = await loadDb(env);
  if (!r) return { ok: false, vertex_id: vertexId, applied: { contact_email: "", tech_stack: "" } };
  const { db, sql } = r;

  const email = (enrichment.contact_email ?? "").trim().slice(0, 320);
  const tech = (enrichment.tech_stack ?? []).join(",").slice(0, 1024);
  const nowIso = new Date().toISOString();

  try {
    const q = sql`
      UPDATE vertex_lead
      SET contact_email = ${email},
          tech_stack    = ${tech},
          updated_at    = ${nowIso}
      WHERE vertex_id = ${vertexId}
    `;
    await q.execute(db);
  } catch (e) {
    console.warn("[yata][leads] setEnrichment UPDATE failed:", e);
    return { ok: false, vertex_id: vertexId, applied: { contact_email: email, tech_stack: tech } };
  }
  return { ok: true, vertex_id: vertexId, applied: { contact_email: email, tech_stack: tech } };
}

/**
 * Operator-facing list: leads that are ready for the human reviewer to
 * fire `/send` on with no further input — outreach_status='approved' AND
 * contact_email != '' AND outreach_outbox is a real outbox vertex_id.
 *
 * The Studio Leads pane filters on this to give the operator a clean
 * "ready to fire" worklist. When Resend is wired, a one-shot loop over
 * this list ships the queued drafts.
 */
export async function leadsSendable(
  env: LeadsEnv,
  limit = 50,
): Promise<{ count: number; leads: Array<Record<string, unknown>> }> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadSendable } = await import("./leads-forward");
    const fwd = await forwardLeadSendable(env, limit);
    if (fwd.ok) return fwd.data as { count: number; leads: Array<Record<string, unknown>> };
    return { count: 0, leads: [] };
  }
  const r = await loadDb(env);
  if (!r) return { count: 0, leads: [] };
  const { db, sql } = r;
  const cap = Math.max(1, Math.min(200, limit));
  try {
    const q = sql`
      SELECT vertex_id, company, domain, contact_email, fit_score,
             outreach_status, outreach_outbox, ingested_at, last_touch_at
      FROM vertex_lead
      WHERE outreach_status = 'approved'
        AND contact_email IS NOT NULL
        AND contact_email <> ''
        AND outreach_outbox IS NOT NULL
        AND outreach_outbox <> ''
      ORDER BY fit_score DESC, ingested_at ASC
      LIMIT ${cap}
    `;
    const res = await q.execute(db);
    return { count: (res.rows ?? []).length, leads: res.rows ?? [] };
  } catch (e) {
    console.warn("[yata][leads] sendable query failed:", e);
    return { count: 0, leads: [] };
  }
}

export async function leadsNeedingEnrichment(
  env: LeadsEnv,
  limit = 10,
): Promise<Array<{ vertex_id: string; domain: string }>> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadNeedsEnrichment } = await import("./leads-forward");
    const fwd = await forwardLeadNeedsEnrichment(env, limit);
    if (!fwd.ok) return [];
    const rows = (fwd.data as { leads?: Array<Record<string, unknown>> }).leads ?? [];
    return rows.map((row) => ({ vertex_id: String(row.vertex_id ?? ""), domain: String(row.domain ?? "") }));
  }
  const r = await loadDb(env);
  if (!r) return [];
  const { db, sql } = r;
  const cap = Math.max(1, Math.min(50, limit));
  try {
    const q = sql`
      SELECT vertex_id, domain
      FROM vertex_lead
      WHERE (contact_email IS NULL OR contact_email = '')
        AND outreach_status IN ('new', 'drafted')
      ORDER BY ingested_at ASC
      LIMIT ${cap}
    `;
    const res = await q.execute(db);
    return (res.rows ?? []).map((row) => ({
      vertex_id: String(row.vertex_id ?? ""),
      domain: String(row.domain ?? ""),
    }));
  } catch (e) {
    console.warn("[yata][leads] leadsNeedingEnrichment failed:", e);
    return [];
  }
}

export async function setLeadContactEmail(
  env: LeadsEnv,
  vertexId: string,
  email: string,
): Promise<{ ok: boolean; vertex_id: string; contact_email: string; error?: string }> {
  const trimmed = email.trim().slice(0, 320);
  if (trimmed && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    return { ok: false, vertex_id: vertexId, contact_email: trimmed, error: "invalid email format" };
  }
  if (env.LG_YATABASE_URL) {
    const { forwardLeadSetContactEmail } = await import("./leads-forward");
    const fwd = await forwardLeadSetContactEmail(env, { vertex_id: vertexId, email: trimmed });
    if (fwd.ok) return fwd.data as { ok: boolean; vertex_id: string; contact_email: string };
    return { ok: false, vertex_id: vertexId, contact_email: trimmed, error: fwd.error ?? "forward failed" };
  }
  const r = await loadDb(env);
  if (!r) return { ok: false, vertex_id: vertexId, contact_email: trimmed, error: "no DB" };
  const { db, sql } = r;
  const nowIso = new Date().toISOString();
  try {
    const q = sql`
      UPDATE vertex_lead
      SET contact_email = ${trimmed},
          updated_at = ${nowIso}
      WHERE vertex_id = ${vertexId}
    `;
    await q.execute(db);
  } catch (e) {
    return {
      ok: false,
      vertex_id: vertexId,
      contact_email: trimmed,
      error: e instanceof Error ? e.message.slice(0, 240) : "throw",
    };
  }
  return { ok: true, vertex_id: vertexId, contact_email: trimmed };
}

/**
 * After nishino drafts an outreach email, mark the lead as 'drafted' so
 * we don't re-draft it on the next iteration.
 *
 * RW UPDATE returns rowcount=0 even on success (UpdateResult quirk per
 * project CLAUDE.md). We fall back to delete-then-insert if the SET
 * appears to have not landed by the next read.
 */
export async function markLeadDrafted(
  env: LeadsEnv,
  vertexId: string,
  outboxId: string,
): Promise<void> {
  if (env.LG_YATABASE_URL) {
    const { forwardLeadMarkDrafted } = await import("./leads-forward");
    await forwardLeadMarkDrafted(env, { vertex_id: vertexId, outbox_id: outboxId });
    return;
  }
  const r = await loadDb(env);
  if (!r) return;
  const { db, sql } = r;
  const nowIso = new Date().toISOString();
  try {
    const q = sql`
      UPDATE vertex_lead
      SET outreach_status = 'drafted',
          outreach_outbox = ${outboxId.slice(0, 200)},
          last_touch_at = ${nowIso},
          updated_at = ${nowIso}
      WHERE vertex_id = ${vertexId}
    `;
    await q.execute(db);
  } catch (e) {
    console.warn("[yata][leads] markDrafted UPDATE failed:", e);
  }
}

// ── Outreach send ───────────────────────────────────────────────────────
//
// Bridges the gap between approved drafts and actual delivery. The same
// code path runs in two modes:
//
//   - dry-run (no RESEND_API_KEY / EMAIL_FROM): returns a preview of what
//     would be sent. Lets the operator verify the draft + recipient before
//     wiring Resend.
//
//   - live (both env vars set): POSTs to Resend, marks both the outbox row
//     and the lead row as 'sent' on success. Failure leaves the lead at
//     'approved' so the operator can retry.
//
// Pre-conditions enforced:
//   - lead.outreach_status == 'approved'  (operator must approve via Studio first)
//   - lead.contact_email   != ''           (operator must set via /contact first)
//   - lead.outreach_outbox != ''           (drafted outbox row exists)

import {
  getOutboxByVertexId as _getOutboxByVertexId,
  markOutboxStatus as _markOutboxStatus,
} from "./email-outbox";

export interface SendResult {
  ok: boolean;
  dryRun: boolean;
  lead_vertex_id: string;
  outbox_vertex_id: string;
  preview?: {
    from: string;
    to: string;
    subject: string;
    body: string;
  };
  resend_id?: string;
  error?: string;
}

export async function sendApprovedLead(
  env: LeadsEnv,
  leadVertexId: string,
): Promise<{ status: number; result: SendResult | { error: string; message: string } }> {
  const lead = await getLeadByVertexId(env, leadVertexId);
  if (!lead) {
    return {
      status: 404,
      result: { error: "NotFound", message: `lead ${leadVertexId} not found` },
    };
  }
  if (lead.outreach_status !== "approved") {
    return {
      status: 409,
      result: {
        error: "PreconditionFailed",
        message: `lead must be 'approved' first; current status='${lead.outreach_status}'`,
      },
    };
  }
  if (!lead.contact_email) {
    return {
      status: 409,
      result: {
        error: "PreconditionFailed",
        message: "lead.contact_email is empty; set via POST /api/leads/{id}/contact first",
      },
    };
  }
  if (!lead.outreach_outbox || !lead.outreach_outbox.startsWith("at://")) {
    return {
      status: 409,
      result: {
        error: "PreconditionFailed",
        message: `lead.outreach_outbox does not point at a valid outbox vertex (got '${lead.outreach_outbox}'); re-run nishino to redraft`,
      },
    };
  }

  const outbox = await _getOutboxByVertexId(env, lead.outreach_outbox);
  if (!outbox) {
    return {
      status: 404,
      result: {
        error: "NotFound",
        message: `outbox row ${lead.outreach_outbox} missing — re-run nishino to redraft`,
      },
    };
  }

  const dryRun = !(env.RESEND_API_KEY && env.EMAIL_FROM);
  const fromAddr = env.EMAIL_FROM ?? "noreply@yatabase.etzhayyim.com";

  if (dryRun) {
    return {
      status: 200,
      result: {
        ok: true,
        dryRun: true,
        lead_vertex_id: lead.vertex_id,
        outbox_vertex_id: outbox.vertex_id,
        preview: {
          from: fromAddr,
          to: lead.contact_email,
          subject: outbox.subject,
          body: outbox.body_text,
        },
      },
    };
  }

  // Live mode — POST Resend + flip both rows to 'sent'.
  let resendId: string | undefined;
  let sendError: string | undefined;
  try {
    const resp = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.RESEND_API_KEY}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        from: fromAddr,
        to: lead.contact_email,
        subject: outbox.subject,
        text: outbox.body_text,
      }),
    });
    if (resp.ok) {
      const j = (await resp.json().catch(() => ({}))) as { id?: string };
      resendId = j.id;
    } else {
      sendError = (await resp.text().catch(() => "")).slice(0, 240);
    }
  } catch (e) {
    sendError = e instanceof Error ? e.message.slice(0, 240) : "throw";
  }

  if (sendError) {
    await _markOutboxStatus(env, outbox.vertex_id, "failed", sendError);
    return {
      status: 500,
      result: {
        ok: false,
        dryRun: false,
        lead_vertex_id: lead.vertex_id,
        outbox_vertex_id: outbox.vertex_id,
        error: sendError,
      },
    };
  }

  await _markOutboxStatus(env, outbox.vertex_id, "sent");
  // setLeadOutreachStatus only handles approve/dismiss; flip lead to 'sent' inline.
  const r2 = await loadDb(env);
  if (r2) {
    const nowIso = new Date().toISOString();
    try {
      const q = r2.sql`
        UPDATE vertex_lead
        SET outreach_status = 'sent',
            last_touch_at = ${nowIso},
            updated_at = ${nowIso}
        WHERE vertex_id = ${lead.vertex_id}
      `;
      await q.execute(r2.db);
    } catch (e) {
      console.warn("[yata][leads] post-send UPDATE failed:", e);
    }
  }

  return {
    status: 200,
    result: {
      ok: true,
      dryRun: false,
      lead_vertex_id: lead.vertex_id,
      outbox_vertex_id: outbox.vertex_id,
      resend_id: resendId,
    },
  };
}
