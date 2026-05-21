// agents/tanaka.ts — QA / reliability agent.
//
// Loop:
//   1. Probe internal backend dependencies that yatabase actually relies on:
//      - Hyperdrive (SELECT 1)
//      - vertex_audit_log query (read recent N rows)
//      - vertex_email_outbox query (read recent N rows)
//      - vertex_billing_event query (read recent N rows)
//      - PDS_SERVICE binding describeServer (auth backend)
//   2. Record per-probe status / latency_ms to vertex_yata_qa_run via raw SQL.
//   3. If any probe fails, emit a qa-regression-report outbox row.
//
// Self-fetch (Worker → its own public hostname) is intentionally avoided —
// CF Workers cannot fetch their own routes (zone loop).

import type { AgentEnv, AgentInput, AgentRunReport, AgentAction } from "./types";
import { newRunId } from "./registry";
import { emitOutbox } from "../email-outbox";

interface AnyDb {}
interface SqlExec<R = unknown> { execute(db: AnyDb): Promise<R>; }
interface SqlTag {
  (parts: TemplateStringsArray, ...vals: unknown[]): SqlExec<{ rows: Array<Record<string, unknown>> }>;
}

interface PdsServiceBinding {
  fetch(req: Request): Promise<Response>;
}

interface TanakaEnv extends AgentEnv {
  PDS_SERVICE?: PdsServiceBinding;
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

interface ProbeResult {
  surface: string;
  method: string;
  path: string;
  status: number;
  latencyMs: number;
  ok: boolean;
  reason?: string;
}

async function probeHyperdrivePing(db: AnyDb, sql: SqlTag): Promise<ProbeResult> {
  const t0 = Date.now();
  try {
    const q = sql`SELECT 1 AS ping`;
    const r = await q.execute(db);
    const ok = (r.rows ?? []).length > 0;
    return {
      surface: "backend", method: "SQL", path: "hyperdrive.ping",
      status: ok ? 200 : 500, latencyMs: Date.now() - t0, ok,
      reason: ok ? undefined : "no rows from SELECT 1",
    };
  } catch (e) {
    return {
      surface: "backend", method: "SQL", path: "hyperdrive.ping",
      status: 500, latencyMs: Date.now() - t0, ok: false,
      reason: e instanceof Error ? e.message.slice(0, 240) : "throw",
    };
  }
}

async function probeTableRead(db: AnyDb, sql: SqlTag, table: string): Promise<ProbeResult> {
  const t0 = Date.now();
  try {
    // Inlined identifier (whitelisted) — sql tag binds values, not idents.
    const allowed: Record<string, SqlExec<{ rows: unknown[] }>> = {
      vertex_audit_log: sql`SELECT 1 FROM vertex_audit_log LIMIT 1`,
      vertex_email_outbox: sql`SELECT 1 FROM vertex_email_outbox LIMIT 1`,
      vertex_billing_event: sql`SELECT 1 FROM vertex_billing_event LIMIT 1`,
    } as unknown as Record<string, SqlExec<{ rows: unknown[] }>>;
    const q = allowed[table];
    if (!q) {
      return {
        surface: "backend", method: "SQL", path: `table.${table}`,
        status: 400, latencyMs: Date.now() - t0, ok: false,
        reason: "unknown table",
      };
    }
    await q.execute(db);
    return {
      surface: "backend", method: "SQL", path: `table.${table}`,
      status: 200, latencyMs: Date.now() - t0, ok: true,
    };
  } catch (e) {
    return {
      surface: "backend", method: "SQL", path: `table.${table}`,
      status: 500, latencyMs: Date.now() - t0, ok: false,
      reason: e instanceof Error ? e.message.slice(0, 240) : "throw",
    };
  }
}

async function probePdsService(env: AgentEnv): Promise<ProbeResult> {
  const t0 = Date.now();
  const pdsService = (env as unknown as TanakaEnv).PDS_SERVICE;
  if (!pdsService) {
    return {
      surface: "backend", method: "RPC", path: "pds.describeServer",
      status: 503, latencyMs: 0, ok: false,
      reason: "PDS_SERVICE binding missing",
    };
  }
  try {
    const r = await pdsService.fetch(
      new Request("https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer"),
    );
    return {
      surface: "backend", method: "RPC", path: "pds.describeServer",
      status: r.status, latencyMs: Date.now() - t0, ok: r.ok,
      reason: r.ok ? undefined : `status ${r.status}`,
    };
  } catch (e) {
    return {
      surface: "backend", method: "RPC", path: "pds.describeServer",
      status: 0, latencyMs: Date.now() - t0, ok: false,
      reason: e instanceof Error ? e.message.slice(0, 240) : "throw",
    };
  }
}

export async function runTanaka(
  env: AgentEnv,
  input?: AgentInput,
): Promise<AgentRunReport> {
  const t0 = Date.now();
  const startedAt = new Date(t0).toISOString();
  const runId = newRunId();
  const dryRun = input?.dryRun ?? false;

  const r0 = await loadDb(env);
  const results: ProbeResult[] = [];
  if (r0) {
    results.push(await probeHyperdrivePing(r0.db, r0.sql));
    results.push(await probeTableRead(r0.db, r0.sql, "vertex_audit_log"));
    results.push(await probeTableRead(r0.db, r0.sql, "vertex_email_outbox"));
    results.push(await probeTableRead(r0.db, r0.sql, "vertex_billing_event"));
  } else {
    results.push({
      surface: "backend", method: "SQL", path: "hyperdrive.ping",
      status: 503, latencyMs: 0, ok: false,
      reason: "no Hyperdrive binding",
    });
  }
  results.push(await probePdsService(env));

  // Persist per-probe rows.
  if (r0 && !dryRun) {
    const { db, sql } = r0;
    for (const pr of results) {
      try {
        const q = sql`
          INSERT INTO vertex_yata_qa_run
            (vertex_id, run_id, ts_ms, agent_did, surface, method, path,
             status_code, latency_ms, ok, reason, created_at)
          VALUES (
            ${`qarun:${runId}:${pr.surface}:${pr.path}`},
            ${runId}, ${Date.now()},
            ${"did:web:yatabase.etzhayyim.com:actor:tanaka"},
            ${pr.surface}, ${pr.method}, ${pr.path},
            ${pr.status}, ${pr.latencyMs}, ${pr.ok ? 1 : 0},
            ${pr.reason ?? ""}, ${new Date().toISOString()}
          )
        `;
        await q.execute(db);
      } catch (e) {
        console.warn("[yata][tanaka] qa_run insert failed:", e);
      }
    }
  }

  const failed = results.filter((p) => !p.ok);
  const actions: AgentAction[] = [];
  for (const pr of results) {
    actions.push({
      kind: "qa-probe",
      target: pr.path,
      summary: `${pr.method} ${pr.path} → ${pr.status} (${pr.latencyMs}ms)${pr.ok ? "" : ` FAIL: ${pr.reason ?? "status mismatch"}`}`,
    });
  }

  if (failed.length > 0 && !dryRun) {
    const subject = `[Yatabase][qa] ${failed.length}/${results.length} surface probes failed`;
    const body = [
      `QA regression report (auto-generated)`,
      ``,
      `Run: ${runId}`,
      `Time: ${startedAt}`,
      ``,
      `Failed probes:`,
      ...failed.map((p) => `  ${p.method} ${p.path} → ${p.status} (${p.latencyMs}ms) — ${p.reason ?? "status mismatch"}`),
      ``,
      `All probes:`,
      ...results.map((p) => `  ${p.ok ? "PASS" : "FAIL"} ${p.method} ${p.path} → ${p.status} (${p.latencyMs}ms)`),
      ``,
      `— Tanaka (Yatabase QA agent)`,
    ].join("\n");
    const r2 = await emitOutbox(env, {
      orgDid: "did:web:yatabase.etzhayyim.com",
      kind: "qa-regression-report",
      subject,
      bodyText: body,
    }).catch(() => ({ status: "error" }));
    actions.push({
      kind: "qa-regression-report",
      target: "staff-inbox",
      summary: `${failed.length} probe(s) regressed`,
      outboxId: r2.status,
    });
  }

  return {
    ok: failed.length === 0,
    agent: "tanaka",
    role: "qa",
    did: "did:web:yatabase.etzhayyim.com:actor:tanaka",
    runId,
    startedAt,
    durationMs: Date.now() - t0,
    actionsCount: actions.length,
    actions,
    notes: `${results.length - failed.length}/${results.length} probes passed`,
    dryRun,
  };
}
