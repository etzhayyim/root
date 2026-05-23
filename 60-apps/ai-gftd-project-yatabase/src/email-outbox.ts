// email-outbox.ts — Email notifications via outbox pattern (P15).
//
// Two-mode design:
//   1. Outbox-only (default, no RESEND_API_KEY): writes a row to
//      `vertex_email_outbox` and returns. A separate cron flushes the
//      outbox to Resend / SES later. Customer can watch their outbox
//      via /api/outbox.
//   2. Direct send (RESEND_API_KEY set): emit row + immediately POST to
//      api.resend.com. Outbox row's `status` flips to 'sent'.
//
// This split means: deploying without an email provider key keeps the
// app safe (no spam from misconfigured tests, no API key leaks) while
// still recording intent for later replay.
//
// Triggered from:
//   - /auth/v1/signup       welcome (kind='signup-welcome')
//   - /auth/v1/upgrade      payment confirmation (kind='plan-upgrade')
//   - /auth/v1/invite       member invite link (kind='member-invite')
//   - /auth/v1/revoke       member revoked notification (kind='member-revoked')
//   - /api/account/delete   final account terminated (kind='account-deleted')
//   - quota threshold cron  80% warning (kind='quota-warning')
//   - monthly invoice cron  invoice ready (kind='invoice-ready')

export type OutboxKind =
  | "signup-welcome"
  | "plan-upgrade"
  | "member-invite"
  | "member-revoked"
  | "account-deleted"
  | "quota-warning"
  | "invoice-ready"
  // Agent-emitted (chikada/tanaka/nishino/sakamoto) drafts go to staff inbox
  // until a human approves. Same vertex_email_outbox row, different `kind`.
  | "sales-quota-nudge"
  | "sales-onboarding-nudge"
  | "support-followup"
  | "dev-incident-summary"
  | "qa-regression-report"
  | "trial-day7";

export interface OutboxEvent {
  orgDid: string;
  recipientEmail?: string;
  recipientName?: string;
  kind: OutboxKind;
  subject: string;
  bodyText: string;
  bodyHtml?: string;
}

export interface OutboxEnv {
  HYPERDRIVE?: unknown;
  RESEND_API_KEY?: string;          // optional — outbox-only when missing
  EMAIL_FROM?: string;              // sender, e.g. "noreply@yatabase.etzhayyim.com"
  GFTD_OUTBOX_DISABLED?: string;
  YATABASE_AUTH_CACHE?: KVNamespace; // P89: KV mirror when RW is degraded
}

const KV_OUTBOX_TTL_SECONDS = 30 * 24 * 3600; // 30 days — typical inbox retention

interface RawDb {}

async function getRealDb(env: OutboxEnv): Promise<{ db: RawDb; sql: ((s: TemplateStringsArray, ...v: unknown[]) => unknown) } | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    const db = (sdk as unknown as { createKyselyDb: (h: unknown) => unknown }).createKyselyDb(env.HYPERDRIVE as never) as RawDb;
    const sql = (sdk as unknown as { sql?: (s: TemplateStringsArray, ...v: unknown[]) => unknown }).sql ?? null;
    if (!sql) return null;
    return { db, sql };
  } catch {
    return null;
  }
}

async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * Persist an email intent to the outbox. Optionally hands it to Resend
 * inline when RESEND_API_KEY is set. Status:
 *   pending  — INSERT but no provider yet
 *   sent     — Resend accepted (200)
 *   failed   — Resend rejected; retry by cron
 *   skipped  — outbox disabled or no recipient
 */
export async function emitOutbox(env: OutboxEnv, event: OutboxEvent): Promise<{ status: string; vertexId?: string }> {
  if (env.GFTD_OUTBOX_DISABLED === "1") return { status: "disabled" };
  if (!event.orgDid) return { status: "skipped-no-org" };

  const tsMs = Date.now();
  const nowIso = new Date(tsMs).toISOString();
  const idDigest = await sha256Hex(`${event.orgDid}|${event.kind}|${tsMs}|${Math.random()}`);
  const vertexId = `at://did:web:outbox.etzhayyim.com/ai.gftd.apps.outbox.event/${idDigest.slice(0, 32)}`;
  const recipient = event.recipientEmail ?? "";

  // P65: send via Resend regardless of RW availability. Customers care
  // about the email delivery, not the audit row. RW outbox INSERT is
  // best-effort below.
  let status = recipient ? "pending" : "queued-no-recipient";
  let lastError = "";
  if (recipient && env.RESEND_API_KEY && env.EMAIL_FROM) {
    try {
      const resp = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          authorization: `Bearer ${env.RESEND_API_KEY}`,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          from: env.EMAIL_FROM,
          to: recipient,
          subject: event.subject,
          text: event.bodyText,
          html: event.bodyHtml ?? undefined,
        }),
      });
      if (resp.ok) {
        status = "sent";
      } else {
        status = "failed";
        lastError = (await resp.text().catch(() => "")).slice(0, 240);
        console.warn("[yatabase][outbox] resend rejected:", resp.status, lastError);
      }
    } catch (e) {
      status = "failed";
      lastError = e instanceof Error ? e.message.slice(0, 240) : "unknown";
    }
  } else if (recipient) {
    status = "skipped-no-resend-creds";
  }

  // P89: KV-first mirror so /api/outbox shows real per-tenant history
  // even when RW is degraded. Inverted-tsMs prefix sorts recent-first
  // for the kv.list readback (matches the audit-log P87 shape).
  if (env.YATABASE_AUTH_CACHE) {
    try {
      const invertedTs = (10n ** 16n - BigInt(tsMs)).toString().padStart(16, "0");
      const rand = Math.random().toString(36).slice(2, 10);
      const kvKey = `outbox:v1:${event.orgDid}:${invertedTs}:${rand}`;
      const kvValue = JSON.stringify({
        vertexId, tsMs, kind: event.kind,
        recipientEmail: recipient, recipientName: event.recipientName ?? "",
        subject: event.subject,
        bodyTextSnippet: event.bodyText.slice(0, 240),
        status, lastError,
        sentAt: status === "sent" ? nowIso : null,
        createdAt: nowIso,
      });
      await env.YATABASE_AUTH_CACHE.put(kvKey, kvValue, { expirationTtl: KV_OUTBOX_TTL_SECONDS });
    } catch (e) {
      console.warn("[yatabase][outbox] KV mirror put failed:", e);
    }
  }

  // RW outbox INSERT is best-effort. When createKyselyDb throws under
  // ADR-2605111200, we still return the actual delivery status from
  // Resend. The audit row will land via a future pod-side migration.
  const r = await getRealDb(env);
  if (r) {
    try {
      const { db, sql } = r;
      const q = sql`
        INSERT INTO vertex_email_outbox
          (vertex_id, org_did, recipient_email, recipient_name, subject,
           body_text, body_html, kind, status, scheduled_at, sent_at,
           retry_count, last_error, created_at)
        VALUES (${vertexId}, ${event.orgDid}, ${recipient}, ${event.recipientName ?? ""},
                ${event.subject}, ${event.bodyText}, ${event.bodyHtml ?? ""},
                ${event.kind}, ${status}, ${nowIso},
                ${status === "sent" ? nowIso : ""},
                0, ${lastError}, ${nowIso})
      `;
      const exec = (q as unknown as { execute: (db: unknown) => Promise<unknown> }).execute;
      await exec.call(q, db);
    } catch (e) {
      console.warn("[yatabase][outbox] insert failed (non-fatal, status reflects delivery):", e);
    }
  }

  return { status, vertexId };
}

/**
 * Look up a single outbox row by vertex_id. Used by /api/leads/{id}/send
 * to retrieve the original draft (subject + body) so it can be replayed
 * to a recipient. Read-only; mutation goes through markOutboxSent below.
 */
export async function getOutboxByVertexId(
  env: OutboxEnv,
  vertexId: string,
): Promise<{
  vertex_id: string;
  org_did: string;
  recipient_email: string;
  recipient_name: string;
  subject: string;
  body_text: string;
  body_html: string;
  kind: string;
  status: string;
  created_at: string;
} | null> {
  const r = await getRealDb(env);
  if (!r) return null;
  const { db, sql } = r;
  try {
    const q = sql`
      SELECT vertex_id, org_did, recipient_email, recipient_name,
             subject, body_text, body_html, kind, status, created_at
      FROM vertex_email_outbox
      WHERE vertex_id = ${vertexId}
      LIMIT 1
    ` as unknown as { execute(db: unknown): Promise<{ rows: Array<Record<string, unknown>> }> };
    const res = await q.execute(db);
    if (!(res.rows ?? []).length) return null;
    const row = res.rows[0];
    return {
      vertex_id: String(row.vertex_id ?? ""),
      org_did: String(row.org_did ?? ""),
      recipient_email: String(row.recipient_email ?? ""),
      recipient_name: String(row.recipient_name ?? ""),
      subject: String(row.subject ?? ""),
      body_text: String(row.body_text ?? ""),
      body_html: String(row.body_html ?? ""),
      kind: String(row.kind ?? ""),
      status: String(row.status ?? ""),
      created_at: String(row.created_at ?? ""),
    };
  } catch (e) {
    console.warn("[yata][outbox] getByVertexId failed:", e);
    return null;
  }
}

/**
 * Mark an outbox row as 'sent' (or 'failed') after a real-send attempt.
 * RW UPDATE is rowcount-blind; we trust the WHERE = PK.
 */
export async function markOutboxStatus(
  env: OutboxEnv,
  vertexId: string,
  status: "sent" | "failed",
  error?: string,
): Promise<void> {
  const r = await getRealDb(env);
  if (!r) return;
  const { db, sql } = r;
  const nowIso = new Date().toISOString();
  try {
    const q = sql`
      UPDATE vertex_email_outbox
      SET status = ${status},
          sent_at = ${status === "sent" ? nowIso : ""},
          last_error = ${(error ?? "").slice(0, 240)}
      WHERE vertex_id = ${vertexId}
    ` as unknown as { execute(db: unknown): Promise<unknown> };
    await q.execute(db);
  } catch (e) {
    console.warn("[yata][outbox] markStatus failed:", e);
  }
}

export interface OutboxQueryResult {
  orgDid: string;
  events: Array<{
    kind: string;
    subject: string;
    recipient: string;
    status: string;
    createdAt: string;
    sentAt: string;
    lastError: string;
  }>;
}

export async function getOutbox(env: OutboxEnv, orgDid: string, limit = 50): Promise<OutboxQueryResult | null> {
  const cap = Math.min(Math.max(limit, 1), 200);

  // P89: KV-first read (authoritative when RW is degraded). Inverted-ts
  // prefix gives recent-first ordering out of kv.list directly.
  if (env.YATABASE_AUTH_CACHE) {
    try {
      const list = await env.YATABASE_AUTH_CACHE.list({ prefix: `outbox:v1:${orgDid}:`, limit: cap });
      if ((list.keys?.length ?? 0) > 0) {
        const events: OutboxQueryResult["events"] = [];
        for (const k of list.keys ?? []) {
          const raw = await env.YATABASE_AUTH_CACHE.get(k.name);
          if (!raw) continue;
          try {
            const e = JSON.parse(raw) as Record<string, unknown>;
            events.push({
              kind: String(e.kind ?? ""),
              subject: String(e.subject ?? ""),
              recipient: String(e.recipientEmail ?? ""),
              status: String(e.status ?? ""),
              createdAt: String(e.createdAt ?? ""),
              sentAt: String(e.sentAt ?? ""),
              lastError: String(e.lastError ?? ""),
            });
          } catch { /* ignore */ }
        }
        return { orgDid, events };
      }
    } catch (e) {
      console.warn("[yatabase][outbox] KV list failed:", e);
    }
  }

  // RW fallback (effectively unused while ADR-2605111200 blocks the read).
  const r = await getRealDb(env);
  if (!r) return null;
  const { db, sql } = r;

  const q = sql`
    SELECT kind, subject, recipient_email, status, created_at, sent_at, last_error
    FROM vertex_email_outbox
    WHERE org_did = ${orgDid}
    ORDER BY created_at DESC
    LIMIT ${cap}
  `;
  let rows: Array<Record<string, unknown>> = [];
  try {
    const exec = (q as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const result = await exec.call(q, db);
    rows = result.rows ?? [];
  } catch (e) {
    console.warn("[yatabase][outbox] query failed:", e);
    return null;
  }

  return {
    orgDid,
    events: rows.map((r) => ({
      kind: String(r.kind ?? ""),
      subject: String(r.subject ?? ""),
      recipient: String(r.recipient_email ?? ""),
      status: String(r.status ?? ""),
      createdAt: String(r.created_at ?? ""),
      sentAt: String(r.sent_at ?? ""),
      lastError: String(r.last_error ?? ""),
    })),
  };
}

// ── Standard email templates (US-primary, JP-secondary) ──

export function welcomeEmail(orgDid: string, apiKey: string, recipientName: string): { subject: string; text: string; html: string } {
  const greet = recipientName && recipientName !== "there" ? `Hi ${recipientName},` : "Hi,";
  const subject = "Welcome to Yatabase — your API key inside";
  // Plain-text fallback. Used by clients that strip HTML and as the
  // text part of multipart messages.
  const text = `${greet}

Welcome to Yatabase — your real-time graph DB + S3-style storage account is ready.

API key (shown ONCE — Yatabase only keeps the SHA-256 hash):

  ${apiKey}

Three things to try right now:

1) First Cypher query
   curl -X POST https://yatabase.etzhayyim.com/cypher \\
     -H "Authorization: Bearer ${apiKey}" \\
     -H "content-type: application/json" \\
     -d '{"query":"CREATE (n:Demo {name:\\"hello\\"}) RETURN n"}'

2) Upload a file (Supabase-shape REST)
   curl -X PUT --data-binary @photo.jpg \\
     -H "Authorization: Bearer ${apiKey}" \\
     https://yatabase.etzhayyim.com/storage/v1/object/my-bucket/photo.jpg

3) List MCP tools (no auth on this one)
   curl -X POST https://yatabase.etzhayyim.com/mcp \\
     -H 'content-type: application/json' \\
     -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

Free tier: $0/month · 1,000 api_request/day · 5 GB storage · 5 CU-h Cypher.
Upgrade when you outgrow: POST /auth/v1/upgrade {"plan":"starter"} → Stripe Checkout.

Reference:
  Docs            https://yatabase.etzhayyim.com/docs
  OpenAPI 3.1     https://yatabase.etzhayyim.com/openapi.json
  Integrations    https://yatabase.etzhayyim.com/integrations
  Studio (UI)     https://yatabase.etzhayyim.com/studio
  Status          https://yatabase.etzhayyim.com/status

Your tenant DID: ${orgDid}
Right to know / delete: GET /api/export · POST /api/account/delete

Questions? Reply to this email — sakamoto (our CS agent) routes it. The
Yatabase team operates as 4 named AI agents — see https://yatabase.etzhayyim.com/team.

— The Yatabase team (chikada / tanaka / nishino / sakamoto)
   Operated by etz hayim · Invoiced by Gftd Japan株式会社 (T9007028460042)
`;

  // HTML body — proper branded email. Inline CSS only (the only thing that
  // survives Gmail / Outlook / Apple Mail rendering reliably). Single-column
  // 600px max width is the email-client lowest-common-denominator.
  const html = `<!doctype html>
<html><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Welcome to Yatabase</title>
</head>
<body style="margin:0;padding:0;background:#fafafa;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;line-height:1.55">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fafafa;padding:32px 0">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#ffffff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.04);overflow:hidden">
      <tr><td style="padding:28px 32px 12px 32px">
        <div style="font-size:22px;font-weight:700;letter-spacing:-0.01em;color:#0f172a">y<span style="color:#0ea5e9">at</span>abase</div>
        <div style="font-size:12px;color:#64748b;margin-top:2px">real-time graph DB + S3-style storage + MCP</div>
      </td></tr>
      <tr><td style="padding:8px 32px 0 32px;font-size:15px">
        <p>${greet}</p>
        <p>Your Yatabase account is ready. Your API key (shown <strong>once</strong> — we keep only the SHA-256 hash):</p>
      </td></tr>
      <tr><td style="padding:4px 32px">
        <div style="background:#0f172a;color:#fcd34d;padding:14px 16px;border-radius:8px;font-family:ui-monospace,SF Mono,Menlo,Consolas,monospace;font-size:13px;word-break:break-all">${apiKey}</div>
      </td></tr>
      <tr><td style="padding:18px 32px 0 32px;font-size:15px">
        <h3 style="margin:8px 0 8px 0;font-size:16px;color:#0f172a">Three things to try right now</h3>
        <p style="margin:6px 0;color:#475569;font-size:13px"><strong>1.</strong> Your first Cypher query:</p>
        <pre style="background:#0f172a;color:#e2e8f0;padding:12px 14px;border-radius:8px;font:12px/1.5 ui-monospace,SF Mono,Menlo,Consolas,monospace;overflow-x:auto;margin:6px 0">curl -X POST https://yatabase.etzhayyim.com/cypher \\
  -H "Authorization: Bearer ${apiKey}" \\
  -H "content-type: application/json" \\
  -d '{"query":"CREATE (n:Demo {name:\\"hello\\"}) RETURN n"}'</pre>

        <p style="margin:14px 0 6px;color:#475569;font-size:13px"><strong>2.</strong> Upload a file (Supabase-shape REST):</p>
        <pre style="background:#0f172a;color:#e2e8f0;padding:12px 14px;border-radius:8px;font:12px/1.5 ui-monospace,SF Mono,Menlo,Consolas,monospace;overflow-x:auto;margin:6px 0">curl -X PUT --data-binary @photo.jpg \\
  -H "Authorization: Bearer ${apiKey}" \\
  https://yatabase.etzhayyim.com/storage/v1/object/my-bucket/photo.jpg</pre>

        <p style="margin:14px 0 6px;color:#475569;font-size:13px"><strong>3.</strong> Talk to it as an MCP tool from Cursor / Claude / LangChain:</p>
        <pre style="background:#0f172a;color:#e2e8f0;padding:12px 14px;border-radius:8px;font:12px/1.5 ui-monospace,SF Mono,Menlo,Consolas,monospace;overflow-x:auto;margin:6px 0">curl -X POST https://yatabase.etzhayyim.com/mcp \\
  -H 'content-type: application/json' \\
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'</pre>
      </td></tr>
      <tr><td style="padding:18px 32px 0 32px;font-size:13px;color:#475569">
        <div style="background:#f1f5f9;border-radius:8px;padding:12px 14px">
          <strong style="color:#0f172a">Free tier:</strong> $0/month · 1,000 api_request/day · 5 GB storage · 5 CU-h Cypher.<br>
          Upgrade anytime: <code style="background:#fff;padding:1px 5px;border-radius:3px">POST /auth/v1/upgrade {"plan":"starter"}</code> → Stripe Checkout.
        </div>
      </td></tr>
      <tr><td style="padding:18px 32px 0 32px;font-size:14px;color:#475569">
        <strong style="color:#0f172a;font-size:13px;text-transform:uppercase;letter-spacing:0.05em">Reference</strong>
        <table cellpadding="0" cellspacing="0" border="0" style="margin-top:6px;font-size:13px">
          <tr><td style="padding:3px 12px 3px 0;color:#64748b">Docs</td><td><a href="https://yatabase.etzhayyim.com/docs" style="color:#0ea5e9;text-decoration:none">yatabase.etzhayyim.com/docs</a></td></tr>
          <tr><td style="padding:3px 12px 3px 0;color:#64748b">OpenAPI 3.1</td><td><a href="https://yatabase.etzhayyim.com/openapi.json" style="color:#0ea5e9;text-decoration:none">/openapi.json</a></td></tr>
          <tr><td style="padding:3px 12px 3px 0;color:#64748b">Integrations</td><td><a href="https://yatabase.etzhayyim.com/integrations" style="color:#0ea5e9;text-decoration:none">/integrations</a> · Cursor / LangChain / Claude / Postman</td></tr>
          <tr><td style="padding:3px 12px 3px 0;color:#64748b">Studio (UI)</td><td><a href="https://yatabase.etzhayyim.com/studio" style="color:#0ea5e9;text-decoration:none">/studio</a></td></tr>
          <tr><td style="padding:3px 12px 3px 0;color:#64748b">Status</td><td><a href="https://yatabase.etzhayyim.com/status" style="color:#0ea5e9;text-decoration:none">/status</a></td></tr>
        </table>
      </td></tr>
      <tr><td style="padding:18px 32px 0 32px;font-size:12px;color:#64748b">
        Tenant DID: <code style="background:#f1f5f9;padding:1px 5px;border-radius:3px">${orgDid}</code><br>
        Data rights: <a href="https://yatabase.etzhayyim.com/api/export" style="color:#0ea5e9">GET /api/export</a> · <a href="https://yatabase.etzhayyim.com/api/account/delete" style="color:#0ea5e9">POST /api/account/delete</a>
      </td></tr>
      <tr><td style="padding:24px 32px 28px 32px;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b;margin-top:24px">
        Questions? Reply to this email — <strong>sakamoto</strong> (our CS agent) routes it.
        The Yatabase team operates as 4 named AI agents: <a href="https://yatabase.etzhayyim.com/team" style="color:#0ea5e9">chikada · tanaka · nishino · sakamoto</a>.
        <br><br>
        Operated by <strong>etz hayim</strong> · Invoiced by <strong>Gftd Japan株式会社</strong> (T9007028460042 — 適格請求書登録番号)
        <br>
        <a href="https://yatabase.etzhayyim.com/privacy" style="color:#94a3b8">Privacy</a> ·
        <a href="https://yatabase.etzhayyim.com/terms" style="color:#94a3b8">Terms</a> ·
        <a href="https://yatabase.etzhayyim.com/.well-known/security.txt" style="color:#94a3b8">security.txt</a>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>`;
  return { subject, text, html };
}

export function planUpgradeEmail(orgDid: string, plan: string, monthlyUsd: number): { subject: string; text: string; html: string } {
  const subject = `Plan upgraded — ${plan} ($${monthlyUsd}/month)`;
  const text = `Your yatabase plan is now: ${plan}

Monthly fee: $${monthlyUsd}
Tenant:      ${orgDid}

New quota:   ${plan} tier limits — see Studio → Plan.
Invoices:    Studio → Invoices (monthly, US/JP dual currency).

— yatabase team`;
  const html = `<p>Your yatabase plan is now: <strong>${plan}</strong></p>
<table cellpadding="6" style="border-collapse:collapse">
  <tr><td>Monthly fee</td><td><strong>$${monthlyUsd}</strong></td></tr>
  <tr><td>Tenant</td><td><code>${orgDid}</code></td></tr>
</table>
<p><a href="https://yatabase.etzhayyim.com/">Open Studio</a> → Plan to see new quota limits, or → Invoices for billing history (USD primary, JPY secondary).</p>`;
  return { subject, text, html };
}

export function memberInviteEmail(orgDid: string, apiKey: string, inviterName: string, memberName: string): { subject: string; text: string; html: string } {
  const subject = `${inviterName} invited you to a yatabase tenant`;
  const text = `${inviterName} added you to their yatabase tenant.

Your API key (shown only once):

  ${apiKey}

Tenant:    ${orgDid}
Member:    ${memberName}

You share the same schema, plan, and billing as the tenant owner.

— yatabase team`;
  const html = `<p><strong>${inviterName}</strong> added you to their yatabase tenant.</p>
<p>Your API key (shown only once):</p>
<pre style="background:#f4f4f4;padding:10px;border-radius:4px"><code>${apiKey}</code></pre>
<p>Tenant: <code>${orgDid}</code><br>
Member: <strong>${memberName}</strong></p>
<p>You share the same schema, plan, and billing as the tenant owner.</p>`;
  return { subject, text, html };
}

// ── Bulk retry of failed / queued outbox rows ─────────────────────────
//
// Operator use: after rotating RESEND_API_KEY or EMAIL_FROM, every row
// in vertex_email_outbox where status='failed' was rejected by Resend
// with the old (bad) key. This helper re-attempts each row using the
// current env credentials and flips status='sent' on success.
//
// Also retries status='pending' rows that have a recipient_email (a
// transient network blip during initial send leaves rows in 'pending').
//
// Pure POST per row — does NOT update body_text/subject/etc, just resends.
// recipient_email='' rows ('queued-no-recipient') are skipped: the
// operator must set a recipient first via the existing Studio Leads
// "set email" action.

export interface RetryOutboxResult {
  tried: number;
  sent: number;
  still_failed: number;
  skipped: number;
  resend_wired: boolean;
  per_row: Array<{
    vertex_id: string;
    kind: string;
    recipient: string;
    status_in: string;
    status_out: string;
    resend_id?: string;
    error?: string;
  }>;
}

export async function retryOutboxBatch(
  env: OutboxEnv,
  opts: { windowHours?: number; limit?: number } = {},
): Promise<RetryOutboxResult> {
  const windowHours = Math.max(1, Math.min(168, opts.windowHours ?? 24));
  const cap = Math.max(1, Math.min(100, opts.limit ?? 25));
  const resendWired = Boolean(env.RESEND_API_KEY && env.EMAIL_FROM);

  const result: RetryOutboxResult = {
    tried: 0,
    sent: 0,
    still_failed: 0,
    skipped: 0,
    resend_wired: resendWired,
    per_row: [],
  };

  const r = await getRealDb(env);
  if (!r) return result;
  const { db, sql } = r;

  // Pick rows worth retrying: failed/pending AND has a recipient AND recent.
  const sinceIso = new Date(Date.now() - windowHours * 3600 * 1000).toISOString();
  let candidates: Array<{ vertex_id: string; kind: string; recipient: string; subject: string; body_text: string; body_html: string; status: string }> = [];
  try {
    const q = sql`
      SELECT vertex_id, kind, recipient_email, subject, body_text, body_html, status
      FROM vertex_email_outbox
      WHERE status IN ('failed', 'pending')
        AND recipient_email IS NOT NULL
        AND recipient_email <> ''
        AND created_at >= ${sinceIso}
      ORDER BY created_at DESC
      LIMIT ${cap}
    ` as unknown as { execute(db: unknown): Promise<{ rows: Array<Record<string, unknown>> }> };
    const res = await q.execute(db);
    candidates = (res.rows ?? []).map((row) => ({
      vertex_id: String(row.vertex_id ?? ""),
      kind: String(row.kind ?? ""),
      recipient: String(row.recipient_email ?? ""),
      subject: String(row.subject ?? ""),
      body_text: String(row.body_text ?? ""),
      body_html: String(row.body_html ?? ""),
      status: String(row.status ?? ""),
    }));
  } catch (e) {
    console.warn("[yata][outbox] retry candidate scan failed:", e);
    return result;
  }

  if (!resendWired) {
    // Without Resend wired, we can still report what would have been
    // retried — useful for the operator to size up the queue before
    // rotating the key.
    for (const c of candidates) {
      result.tried++;
      result.skipped++;
      result.per_row.push({
        vertex_id: c.vertex_id,
        kind: c.kind,
        recipient: c.recipient,
        status_in: c.status,
        status_out: "skipped-no-resend",
      });
    }
    return result;
  }

  // Live retry path.
  for (const c of candidates) {
    result.tried++;
    let sentOk = false;
    let resendId: string | undefined;
    let lastError: string | undefined;
    try {
      const resp = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          authorization: `Bearer ${env.RESEND_API_KEY}`,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          from: env.EMAIL_FROM,
          to: c.recipient,
          subject: c.subject,
          text: c.body_text,
          html: c.body_html || undefined,
        }),
      });
      if (resp.ok) {
        const j = (await resp.json().catch(() => ({}))) as { id?: string };
        resendId = j.id;
        sentOk = true;
      } else {
        lastError = (await resp.text().catch(() => "")).slice(0, 240);
      }
    } catch (e) {
      lastError = e instanceof Error ? e.message.slice(0, 240) : "fetch threw";
    }

    if (sentOk) {
      result.sent++;
      await markOutboxStatus(env, c.vertex_id, "sent").catch(() => {});
      result.per_row.push({
        vertex_id: c.vertex_id,
        kind: c.kind,
        recipient: c.recipient,
        status_in: c.status,
        status_out: "sent",
        resend_id: resendId,
      });
    } else {
      result.still_failed++;
      await markOutboxStatus(env, c.vertex_id, "failed", lastError).catch(() => {});
      result.per_row.push({
        vertex_id: c.vertex_id,
        kind: c.kind,
        recipient: c.recipient,
        status_in: c.status,
        status_out: "failed",
        error: lastError,
      });
    }
  }

  return result;
}

export function day7RetentionEmail(recipientName: string): { subject: string; text: string; html: string } {
  const greet = recipientName && recipientName !== "there" ? `Hi ${recipientName},` : "Hi,";
  const subject = "7 days in — what have you built with Yatabase?";
  const text = `${greet}

It's been a week. We hope you've had a chance to run your first Cypher query or push a file to your Yatabase bucket.

Here's a quick recap of what you have on the free tier:

  • Cypher graph queries    — CREATE / MATCH / RETURN against a streaming real-time graph
  • S3-style storage        — PUT/GET up to 5 GB, presigned URLs, Supabase-shape REST
  • MCP facade              — 8 AI-agent tools your Claude / Cursor / GPT can call directly
  • Deploy-first queries    — pre-deploy a graph traversal pattern once, read results instantly (new)
  • 1,000 api_request/day  — plenty to prototype a production feature

If you've hit any of those ceilings, the Starter plan ($13/mo) gives you 33k requests/day, 50 GB storage, and 20 deployed query slots — enough to ship to real users.

  Upgrade: curl -X POST https://yatabase.etzhayyim.com/auth/v1/upgrade \\
             -H "Authorization: Bearer <your-key>" \\
             -H "content-type: application/json" \\
             -d '{"plan":"starter"}'

Compare us vs Supabase / Neo4j AuraDB / Hasura:
  https://yatabase.etzhayyim.com/comparison

Quick-start guide:
  https://yatabase.etzhayyim.com/quickstart

Questions? Reply here — sakamoto routes it to the right agent.

— The Yatabase team (chikada / tanaka / nishino / sakamoto)
   Operated by etz hayim · Invoiced by Gftd Japan株式会社 (T9007028460042)
   Unsubscribe: POST /api/account/delete to close your account and erase all data.
`;

  const html = `<!doctype html>
<html><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>7 days in — Yatabase</title>
</head>
<body style="margin:0;padding:0;background:#fafafa;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;line-height:1.55">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fafafa;padding:32px 0">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#ffffff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.04);overflow:hidden">
      <tr><td style="padding:28px 32px 12px 32px">
        <div style="font-size:22px;font-weight:700;letter-spacing:-0.01em;color:#0f172a">y<span style="color:#0ea5e9">at</span>abase</div>
        <div style="font-size:12px;color:#64748b;margin-top:2px">real-time graph DB + S3-style storage + MCP</div>
      </td></tr>
      <tr><td style="padding:20px 32px 0 32px;font-size:15px">
        <p style="margin:0 0 10px 0">${greet}</p>
        <p style="margin:0 0 16px 0">It's been a week. Here's what you have on the <strong>free tier</strong>:</p>
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f8fafc;border-radius:8px;padding:16px;margin-bottom:16px">
          <tr><td style="padding:4px 0;font-size:14px">🔵 <strong>Cypher graph queries</strong> — CREATE / MATCH / RETURN against a streaming real-time graph</td></tr>
          <tr><td style="padding:4px 0;font-size:14px">📦 <strong>S3-style storage</strong> — PUT/GET up to 5 GB, presigned URLs, Supabase-shape REST</td></tr>
          <tr><td style="padding:4px 0;font-size:14px">🤖 <strong>MCP facade</strong> — 8 AI-agent tools your Claude / Cursor / GPT can call</td></tr>
          <tr><td style="padding:4px 0;font-size:14px">⚡ <strong>Deploy-first queries</strong> — pre-deploy a graph pattern, read results instantly (new)</td></tr>
          <tr><td style="padding:4px 0;font-size:14px">📊 <strong>1,000 api_request / day</strong> — enough to prototype a production feature</td></tr>
        </table>
        <p style="margin:0 0 12px 0;font-size:14px;color:#475569">If you've hit those ceilings, <strong>Starter ($13/mo)</strong> gives you 33k requests/day, 50 GB storage, and 20 deployed query slots.</p>
      </td></tr>
      <tr><td style="padding:8px 32px 20px 32px">
        <a href="https://yatabase.etzhayyim.com/studio" style="display:inline-block;background:#0ea5e9;color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;font-size:14px">Upgrade in Studio →</a>
        &nbsp;
        <a href="https://yatabase.etzhayyim.com/comparison" style="display:inline-block;background:#f1f5f9;color:#0f172a;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;font-size:14px">Compare plans</a>
      </td></tr>
      <tr><td style="padding:0 32px 24px 32px;font-size:13px;color:#64748b;border-top:1px solid #f1f5f9">
        <p style="margin:16px 0 4px 0">Questions? Reply here — sakamoto routes it to the right agent.</p>
        <p style="margin:4px 0">— The Yatabase team · Operated by etz hayim · Invoiced by Gftd Japan株式会社</p>
        <p style="margin:4px 0">Unsubscribe: <code>POST /api/account/delete</code> to close your account.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>`;

  return { subject, text, html };
}

export function usageAlertEmail(
  recipientName: string,
  usedToday: number,
  dailyLimit: number,
  pct: number,
): { subject: string; text: string; html: string } {
  const greet = recipientName && recipientName !== "there" ? `Hi ${recipientName},` : "Hi,";
  const remaining = Math.max(0, dailyLimit - usedToday);
  const subject = `You've used ${pct}% of your daily Yatabase quota`;
  const text = `${greet}

A heads-up: your Yatabase free-tier account has consumed ${pct}% of today's request quota.

  Used today:  ${usedToday.toLocaleString()} requests
  Daily limit: ${dailyLimit.toLocaleString()} requests
  Remaining:   ${remaining.toLocaleString()} requests

The quota resets at UTC midnight. The Starter plan ($13/mo) gives you 33× more — 33,000 requests/day.

  curl -X POST https://yatabase.etzhayyim.com/auth/v1/upgrade \\
    -H "Authorization: Bearer <your-key>" \\
    -H "content-type: application/json" \\
    -d '{"plan":"starter"}'

Compare plans: https://yatabase.etzhayyim.com/comparison

— The Yatabase team (chikada / tanaka / nishino / sakamoto)
   Operated by etz hayim · Invoiced by Gftd Japan株式会社 (T9007028460042)
   Unsubscribe: POST /api/account/delete to close your account and erase all data.
`;

  const barFilled = Math.round(pct / 10);
  const bar = "█".repeat(barFilled) + "░".repeat(10 - barFilled);
  const barColor = pct >= 95 ? "#ef4444" : pct >= 80 ? "#f59e0b" : "#0ea5e9";

  const html = `<!doctype html>
<html><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Quota alert — Yatabase</title>
</head>
<body style="margin:0;padding:0;background:#fafafa;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;line-height:1.55">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fafafa;padding:32px 0">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#ffffff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.04);overflow:hidden">
      <tr><td style="padding:28px 32px 12px 32px">
        <div style="font-size:22px;font-weight:700;letter-spacing:-0.01em;color:#0f172a">y<span style="color:#0ea5e9">at</span>abase</div>
        <div style="font-size:12px;color:#64748b;margin-top:2px">real-time graph DB + S3-style storage + MCP</div>
      </td></tr>
      <tr><td style="padding:20px 32px 0 32px;font-size:15px">
        <p style="margin:0 0 10px 0">${greet}</p>
        <p style="margin:0 0 16px 0">You've used <strong style="color:${barColor}">${pct}%</strong> of your free-tier daily quota.</p>
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f8fafc;border-radius:8px;padding:16px;margin-bottom:16px">
          <tr>
            <td style="font-size:13px;color:#64748b;padding-bottom:6px" colspan="2">Today's api_request quota</td>
          </tr>
          <tr>
            <td style="font-family:monospace;font-size:18px;color:${barColor};letter-spacing:2px">${bar}</td>
            <td style="font-size:18px;font-weight:700;color:${barColor};text-align:right">${pct}%</td>
          </tr>
          <tr>
            <td style="font-size:13px;padding-top:8px">Used: <strong>${usedToday.toLocaleString()}</strong></td>
            <td style="font-size:13px;padding-top:8px;text-align:right">Limit: <strong>${dailyLimit.toLocaleString()}</strong></td>
          </tr>
        </table>
        <p style="margin:0 0 12px 0;font-size:14px;color:#475569">
          The quota resets at UTC midnight. <strong>Starter ($13/mo)</strong> gives you 33,000 requests/day — 33× more headroom.
        </p>
      </td></tr>
      <tr><td style="padding:8px 32px 20px 32px">
        <a href="https://yatabase.etzhayyim.com/studio" style="display:inline-block;background:#0ea5e9;color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;font-size:14px">Upgrade in Studio →</a>
        &nbsp;
        <a href="https://yatabase.etzhayyim.com/comparison" style="display:inline-block;background:#f1f5f9;color:#0f172a;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;font-size:14px">Compare plans</a>
      </td></tr>
      <tr><td style="padding:0 32px 24px 32px;font-size:13px;color:#64748b;border-top:1px solid #f1f5f9">
        <p style="margin:16px 0 4px 0">Questions? Reply here — sakamoto routes it to the right agent.</p>
        <p style="margin:4px 0">— The Yatabase team · Operated by etz hayim · Invoiced by Gftd Japan株式会社</p>
        <p style="margin:4px 0">Unsubscribe: <code>POST /api/account/delete</code> to close your account.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>`;

  return { subject, text, html };
}
