// agents/chikada.ts — Engineering / DevEx agent.
//
// Loop:
//   1. SELECT vertex_audit_log last 1h WHERE status_code >= 500
//      GROUP BY surface, method.
//   2. Any (surface, method) with >= 3 errors → emit dev-incident-summary
//      outbox row (kind='dev-incident-summary') addressed to the operating
//      org (did:web:yatabase.gftd.ai), so the staff inbox lights up.
//   3. Sample 1 representative path/status_code per group for the body.
//
// Deliberately read-only on production data. No code is ever modified by
// the agent — the output is a draft incident summary for a human to act on.

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

const HOT_GROUP_THRESHOLD = 3;

export async function runChikada(
  env: AgentEnv,
  input?: AgentInput,
): Promise<AgentRunReport> {
  const t0 = Date.now();
  const startedAt = new Date(t0).toISOString();
  const runId = newRunId();
  const dryRun = input?.dryRun ?? false;
  const cap = input?.maxActions ?? 10;

  const r = await loadDb(env);
  if (!r) {
    return {
      ok: false,
      agent: "chikada",
      role: "dev",
      did: "did:web:yatabase.gftd.ai:actor:chikada",
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

  const since = Date.now() - 60 * 60 * 1000;
  interface Group {
    surface: string;
    method: string;
    count: number;
    samplePath: string;
    sampleStatus: number;
  }
  const groups: Group[] = [];
  try {
    const q = sql`
      SELECT surface, method, COUNT(*) AS c,
             MIN(path) AS sample_path,
             MIN(status_code) AS sample_status
      FROM vertex_audit_log
      WHERE ts_ms >= ${since}
        AND status_code >= 500
      GROUP BY surface, method
      ORDER BY c DESC
      LIMIT 50
    `;
    const res = await q.execute(db);
    for (const row of res.rows ?? []) {
      const c = Number(row.c ?? 0);
      if (c < HOT_GROUP_THRESHOLD) continue;
      groups.push({
        surface: String(row.surface ?? "other"),
        method: String(row.method ?? "?"),
        count: c,
        samplePath: String(row.sample_path ?? ""),
        sampleStatus: Number(row.sample_status ?? 500),
      });
    }
  } catch (e) {
    return {
      ok: false,
      agent: "chikada",
      role: "dev",
      did: "did:web:yatabase.gftd.ai:actor:chikada",
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
  for (const g of groups) {
    if (actions.length >= cap) break;
    const subject = `[Yatabase][dev] ${g.count}× ${g.method} ${g.surface} 5xx in last hour`;
    const body = [
      `Engineering incident summary (auto-generated, requires human triage)`,
      ``,
      `Surface : ${g.surface}`,
      `Method  : ${g.method}`,
      `Count   : ${g.count} errors in last 60 min`,
      `Sample  : ${g.method} ${g.samplePath} → ${g.sampleStatus}`,
      ``,
      `Probable next steps:`,
      `  • Tail vertex_audit_log WHERE surface='${g.surface}' AND status_code >= 500 ORDER BY ts_ms DESC LIMIT 20`,
      `  • Inspect Worker logs: wrangler tail magatama-y4t4b4se`,
      `  • Check downstream: agentgateway MCP router / yata-langserver pod / RW access path`,
      ``,
      `— Chikada (Yatabase engineering agent)`,
    ].join("\n");
    if (!dryRun) {
      const r2 = await emitOutbox(env, {
        orgDid: "did:web:yatabase.gftd.ai",
        kind: "dev-incident-summary",
        subject,
        bodyText: body,
      }).catch(() => ({ status: "error" }));
      actions.push({
        kind: "dev-incident-summary",
        target: `${g.method}:${g.surface}`,
        summary: `${g.count} 5xx errors in last hour`,
        outboxId: r2.status,
      });
    } else {
      actions.push({
        kind: "dev-incident-summary[dry]",
        target: `${g.method}:${g.surface}`,
        summary: `would draft (count=${g.count})`,
      });
    }
  }

  return {
    ok: true,
    agent: "chikada",
    role: "dev",
    did: "did:web:yatabase.gftd.ai:actor:chikada",
    runId,
    startedAt,
    durationMs: Date.now() - t0,
    actionsCount: actions.length,
    actions,
    notes: `scanned audit log since ${new Date(since).toISOString()}, found ${groups.length} hot groups`,
    dryRun,
  };
}
