// agents/registry.ts — yatabase actor team roster + run audit trail.

import type {
  AgentDef,
  AgentEnv,
  AgentName,
  AgentRunReport,
  AgentInput,
} from "./types";
import { runChikada } from "./chikada";
import { runTanaka } from "./tanaka";
import { runNishino } from "./nishino";
import { runSakamoto } from "./sakamoto";

const HOST_DID = "did:web:yatabase.etzhayyim.com";

export const AGENTS: Record<AgentName, AgentDef> = {
  chikada: {
    name: "chikada",
    role: "dev",
    did: `${HOST_DID}:actor:chikada`,
    displayName: "Chikada (近田)",
    description:
      "Engineering agent. Scans audit log for 5xx surfaces, drafts dev proposals.",
    run: runChikada,
  },
  tanaka: {
    name: "tanaka",
    role: "qa",
    did: `${HOST_DID}:actor:tanaka`,
    displayName: "Tanaka (田中)",
    description:
      "QA / reliability agent. Probes public surfaces, records pass/fail to vertex_yata_qa_run.",
    run: runTanaka,
  },
  nishino: {
    name: "nishino",
    role: "sales",
    did: `${HOST_DID}:actor:nishino`,
    displayName: "Nishino (西野)",
    description:
      "Sales / GTM agent. Drafts upgrade nudges for tenants approaching plan quota.",
    run: runNishino,
  },
  sakamoto: {
    name: "sakamoto",
    role: "cs",
    did: `${HOST_DID}:actor:sakamoto`,
    displayName: "Sakamoto (坂本)",
    description:
      "Customer success agent. Triages stalled outbox emails and drafts support follow-ups.",
    run: runSakamoto,
  },
};

export function listAgents(): Array<Omit<AgentDef, "run">> {
  return (Object.values(AGENTS) as AgentDef[]).map((a) => ({
    name: a.name,
    role: a.role,
    did: a.did,
    displayName: a.displayName,
    description: a.description,
  }));
}

export function getAgent(name: string): AgentDef | null {
  return (AGENTS as Record<string, AgentDef>)[name] ?? null;
}

interface AnyKyselyDb {
  insertInto(table: string): {
    values(row: Record<string, unknown>): { execute(): Promise<unknown> };
  };
}

async function getDb(env: AgentEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch {
    return null;
  }
}

export async function recordAgentRun(
  env: AgentEnv,
  report: AgentRunReport,
): Promise<void> {
  const db = await getDb(env);
  if (!db) return;
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    const sql = (sdk as { sql?: unknown }).sql as
      | ((parts: TemplateStringsArray, ...vals: unknown[]) => unknown)
      | undefined;
    const tsMs = Date.now();
    if (sql) {
      const stmt = sql`
        INSERT INTO vertex_yata_agent_run (
          vertex_id, agent_name, agent_did, role,
          run_id, ts_ms, duration_ms,
          actions_count, status, actions_json, notes, created_at
        ) VALUES (
          ${`agentrun:${report.runId}`},
          ${report.agent},
          ${report.did},
          ${report.role},
          ${report.runId},
          ${tsMs},
          ${report.durationMs},
          ${report.actionsCount},
          ${report.ok ? "ok" : "error"},
          ${JSON.stringify(report.actions).slice(0, 8000)},
          ${(report.notes ?? "").slice(0, 1000)},
          ${new Date(tsMs).toISOString()}
        )
      ` as { execute(db: unknown): Promise<unknown> };
      await stmt.execute(db);
    } else {
      await db.insertInto("vertex_yata_agent_run").values({
        vertex_id: `agentrun:${report.runId}`,
        agent_name: report.agent,
        agent_did: report.did,
        role: report.role,
        run_id: report.runId,
        ts_ms: tsMs,
        duration_ms: report.durationMs,
        actions_count: report.actionsCount,
        status: report.ok ? "ok" : "error",
        actions_json: JSON.stringify(report.actions).slice(0, 8000),
        notes: (report.notes ?? "").slice(0, 1000),
        created_at: new Date(tsMs).toISOString(),
      }).execute();
    }
  } catch (e) {
    console.warn("[yata][agent-run] persist failed:", e);
  }
}

// One-shot DDL: creates vertex_yata_agent_run + vertex_yata_qa_run tables
// in RisingWave. Idempotent (IF NOT EXISTS). Returns per-table outcome.
//
// Called manually via POST /_agents/bootstrap (admin-keyed). Yatabase
// Worker's Hyperdrive connection is allowed DDL because the RW server
// permits it for the gftd-platform tenant; tenant-scoped DDL is gated
// elsewhere (yata-langserver-worker w/ RW_ALLOW_HEAVY_DDL=1).
export async function bootstrapAgentTables(env: AgentEnv): Promise<{
  ok: boolean;
  tables: Array<{ name: string; ok: boolean; error?: string }>;
}> {
  const db = await getDb(env);
  if (!db) return { ok: false, tables: [] };
  const sdk = await import("@etzhayyim/magatama-host-sdk");
  const sql = (sdk as { sql?: unknown }).sql as
    | ((parts: TemplateStringsArray, ...vals: unknown[]) => unknown)
    | undefined;
  if (!sql) return { ok: false, tables: [] };

  const stmts: Array<{ name: string; q: unknown }> = [
    {
      name: "vertex_yata_agent_run",
      q: sql`
        CREATE TABLE IF NOT EXISTS vertex_yata_agent_run (
          vertex_id     VARCHAR PRIMARY KEY,
          agent_name    VARCHAR NOT NULL,
          agent_did     VARCHAR NOT NULL,
          role          VARCHAR NOT NULL,
          run_id        VARCHAR NOT NULL,
          ts_ms         BIGINT NOT NULL,
          duration_ms   INT NOT NULL,
          actions_count INT NOT NULL,
          status        VARCHAR NOT NULL,
          actions_json  VARCHAR,
          notes         VARCHAR,
          created_at    VARCHAR NOT NULL
        )
      `,
    },
    {
      name: "vertex_yata_qa_run",
      q: sql`
        CREATE TABLE IF NOT EXISTS vertex_yata_qa_run (
          vertex_id     VARCHAR PRIMARY KEY,
          run_id        VARCHAR NOT NULL,
          ts_ms         BIGINT NOT NULL,
          agent_did     VARCHAR NOT NULL,
          surface       VARCHAR NOT NULL,
          method        VARCHAR NOT NULL,
          path          VARCHAR NOT NULL,
          status_code   INT NOT NULL,
          latency_ms    INT NOT NULL,
          ok            INT NOT NULL,
          reason        VARCHAR,
          created_at    VARCHAR NOT NULL
        )
      `,
    },
    {
      // Top-of-funnel CRM. One row per (domain) candidate. nishino + the
      // future LangGraph marketing graph both write/read this table.
      // outreach_status pipeline: NULL → 'new' → 'drafted' → 'sent' → 'replied' / 'bounced' / 'dead'
      name: "vertex_lead",
      q: sql`
        CREATE TABLE IF NOT EXISTS vertex_lead (
          vertex_id        VARCHAR PRIMARY KEY,
          company          VARCHAR NOT NULL,
          domain           VARCHAR NOT NULL,
          contact_name     VARCHAR,
          contact_email    VARCHAR,
          source           VARCHAR,
          source_url       VARCHAR,
          signal           VARCHAR,
          tech_stack       VARCHAR,
          employees        VARCHAR,
          fit_score        INT,
          reasoning        VARCHAR,
          outreach_status  VARCHAR NOT NULL,
          outreach_outbox  VARCHAR,
          last_touch_at    VARCHAR,
          notes            VARCHAR,
          ingested_at      VARCHAR NOT NULL,
          updated_at       VARCHAR NOT NULL
        )
      `,
    },
  ];

  const tables: Array<{ name: string; ok: boolean; error?: string }> = [];
  let allOk = true;
  for (const { name, q } of stmts) {
    try {
      const exec = (q as { execute(db: unknown): Promise<unknown> }).execute;
      await exec.call(q, db);
      tables.push({ name, ok: true });
    } catch (e) {
      allOk = false;
      tables.push({
        name,
        ok: false,
        error: e instanceof Error ? e.message.slice(0, 240) : "throw",
      });
    }
  }
  return { ok: allOk, tables };
}

export function newRunId(): string {
  const buf = new Uint8Array(12);
  crypto.getRandomValues(buf);
  return Array.from(buf).map((b) => b.toString(16).padStart(2, "0")).join("");
}

// Read N most recent vertex_yata_agent_run rows (admin-only, for staff inbox).
export async function recentAgentRuns(
  env: AgentEnv,
  limit = 25,
): Promise<Array<Record<string, unknown>>> {
  const db = await getDb(env);
  if (!db) return [];
  const sdk = await import("@etzhayyim/magatama-host-sdk");
  const sql = (sdk as { sql?: unknown }).sql as
    | ((parts: TemplateStringsArray, ...vals: unknown[]) => unknown)
    | undefined;
  if (!sql) return [];
  const cap = Math.max(1, Math.min(200, limit));
  const q = sql`
    SELECT agent_name, agent_did, role, run_id, ts_ms, duration_ms,
           actions_count, status, notes, created_at
    FROM vertex_yata_agent_run
    ORDER BY ts_ms DESC
    LIMIT ${cap}
  ` as { execute(db: unknown): Promise<{ rows: Array<Record<string, unknown>> }> };
  try {
    const r = await q.execute(db);
    return r.rows ?? [];
  } catch (e) {
    console.warn("[yata][agent-recent] read failed:", e);
    return [];
  }
}

export async function runAgent(
  name: AgentName,
  env: AgentEnv,
  input?: AgentInput,
): Promise<AgentRunReport> {
  const def = AGENTS[name];
  const startedAt = new Date().toISOString();
  const t0 = Date.now();
  let report: AgentRunReport;
  try {
    report = await def.run(env, input);
  } catch (e) {
    report = {
      ok: false,
      agent: name,
      role: def.role,
      did: def.did,
      runId: newRunId(),
      startedAt,
      durationMs: Date.now() - t0,
      actionsCount: 0,
      actions: [],
      error: e instanceof Error ? e.message.slice(0, 500) : String(e).slice(0, 500),
      dryRun: input?.dryRun ?? false,
    };
  }
  await recordAgentRun(env, report);
  return report;
}
