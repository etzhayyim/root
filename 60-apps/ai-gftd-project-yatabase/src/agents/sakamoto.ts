// agents/sakamoto.ts — Customer Success / Support agent.
//
// Loop:
//   1. Find vertex_email_outbox rows that need attention:
//      - status='failed'                    → delivery failed; needs retry/contact
//      - status='pending' AND created_at older than 24h → stuck
//      - status='queued-no-recipient' AND created_at older than 7d → orphan
//   2. For each, emit a support-followup outbox row to the staff inbox
//      with a draft reply tailored to the original email kind.
//
// Stays read-only on the original outbox row (no UPDATE — that's the
// human reviewer's call). Just drafts the suggested follow-up.

import type { AgentEnv, AgentInput, AgentRunReport, AgentAction } from "./types";
import { newRunId } from "./registry";
import { emitOutbox } from "../email-outbox";

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

function draftBody(kind: string, status: string, originalSubject: string): string {
  const lines = [
    `Customer success follow-up draft (auto-generated, requires human approval before send)`,
    ``,
    `Original outbox kind   : ${kind}`,
    `Original outbox status : ${status}`,
    `Original subject       : ${originalSubject}`,
    ``,
  ];
  switch (kind) {
    case "signup-welcome":
      lines.push(
        `Suggested action: re-send welcome with a fresh API key only if the customer asked.`,
        `Otherwise: confirm whether the original email landed (check Resend logs).`,
      );
      break;
    case "plan-upgrade":
      lines.push(
        `Suggested action: confirm plan flip on Stripe dashboard, ack via short reply.`,
        `If Stripe shows past_due, escalate to billing.`,
      );
      break;
    case "member-invite":
      lines.push(
        `Suggested action: ask if the invited person received the API key.`,
        `If not, /auth/v1/revoke + re-invite via Studio → Members.`,
      );
      break;
    case "account-deleted":
      lines.push(
        `Suggested action: nothing — deletion is final. If the customer asks for`,
        `restore, explain CCPA / GDPR / 改正個人情報保護法 erasure is irreversible.`,
      );
      break;
    case "quota-warning":
      lines.push(
        `Suggested action: hand-off to Nishino (sales) for upgrade conversation.`,
      );
      break;
    case "invoice-ready":
      lines.push(
        `Suggested action: confirm receipt; offer 適格請求書 (T9007028460042) PDF`,
        `via Studio → Invoices → 'Print invoice'.`,
      );
      break;
    default:
      lines.push(`Suggested action: review manually.`);
  }
  lines.push(``, `— Sakamoto (Yatabase customer success agent)`);
  return lines.join("\n");
}

export async function runSakamoto(
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
      agent: "sakamoto",
      role: "cs",
      did: "did:web:yatabase.etzhayyim.com:actor:sakamoto",
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

  const day = 24 * 3600 * 1000;
  const failedCutoff = new Date(Date.now() - 7 * day).toISOString();
  const stuckCutoff = new Date(Date.now() - 1 * day).toISOString();
  const orphanCutoff = new Date(Date.now() - 7 * day).toISOString();

  interface Row { kind: string; status: string; subject: string; org_did: string; created_at: string; }
  const stuck: Row[] = [];
  try {
    const q = sql`
      SELECT kind, status, subject, org_did, created_at
      FROM vertex_email_outbox
      WHERE (
              (status = 'failed'                AND created_at >= ${failedCutoff})
           OR (status = 'pending'               AND created_at <= ${stuckCutoff})
           OR (status = 'queued-no-recipient'   AND created_at <= ${orphanCutoff})
            )
        AND kind NOT IN (
          'support-followup',
          'dev-incident-summary',
          'qa-regression-report',
          'sales-quota-nudge',
          'sales-onboarding-nudge'
        )
      ORDER BY created_at DESC
      LIMIT 50
    `;
    const res = await q.execute(db);
    for (const row of res.rows ?? []) {
      stuck.push({
        kind: String(row.kind ?? ""),
        status: String(row.status ?? ""),
        subject: String(row.subject ?? ""),
        org_did: String(row.org_did ?? ""),
        created_at: String(row.created_at ?? ""),
      });
    }
  } catch (e) {
    return {
      ok: false,
      agent: "sakamoto",
      role: "cs",
      did: "did:web:yatabase.etzhayyim.com:actor:sakamoto",
      runId,
      startedAt,
      durationMs: Date.now() - t0,
      actionsCount: 0,
      actions: [],
      error: e instanceof Error ? e.message.slice(0, 300) : String(e).slice(0, 300),
      dryRun,
    };
  }

  const actions: AgentAction[] = [];
  for (const row of stuck) {
    if (actions.length >= cap) break;
    const subject = `[Yatabase][cs] follow-up: ${row.kind} (${row.status}) for ${row.org_did}`;
    const body = draftBody(row.kind, row.status, row.subject);
    if (!dryRun) {
      const r2 = await emitOutbox(env, {
        orgDid: "did:web:yatabase.etzhayyim.com",
        kind: "support-followup",
        subject,
        bodyText: body,
      }).catch(() => ({ status: "error" }));
      actions.push({
        kind: "support-followup",
        target: row.org_did,
        summary: `${row.kind} stuck in ${row.status} since ${row.created_at}`,
        outboxId: r2.status,
      });
    } else {
      actions.push({
        kind: "support-followup[dry]",
        target: row.org_did,
        summary: `would draft (kind=${row.kind}, status=${row.status})`,
      });
    }
  }

  return {
    ok: true,
    agent: "sakamoto",
    role: "cs",
    did: "did:web:yatabase.etzhayyim.com:actor:sakamoto",
    runId,
    startedAt,
    durationMs: Date.now() - t0,
    actionsCount: actions.length,
    actions,
    notes: `${stuck.length} stuck/failed outbox rows surveyed`,
    dryRun,
  };
}
