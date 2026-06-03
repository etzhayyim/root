// cypher.ts — /cypher openCypher HTTP endpoint (ADR-2605080000 §D13).
//
// Wire shape: Neo4j HTTP API subset — `POST /cypher` with
//   { statements: [{ statement, parameters, resultDataContents }] }
// Translation happens in the bpmn-dispatcher LangServer pool (kagami-cypher-compiler
// is too large to bundle into a CF Worker today — Phase P7 will revisit a WASM
// build). The Worker is a thin parser + pre-flight validator + dispatcher caller.
//
// MVP scope (P4a):
//   - READ-only Cypher (MATCH / WITH / RETURN / WHERE / ORDER BY / LIMIT / SKIP / UNION)
//   - WRITE clauses (CREATE / MERGE / SET / DELETE / DETACH / REMOVE) are rejected at
//     the edge with HTTP 400 so the operator catches misuse before paying compute cost
//   - Multi-statement transaction body is supported (Neo4j HTTP API parity) but each
//     statement is dispatched independently — RW does not honour multi-statement TX
//   - Response carries `Sql-Constraint-Mode: rw-eventual` so clients know they cannot
//     assume strict serializability (ADR-2605080000 §D12 invariants)

import type { DispatcherCallerContext } from "./dispatcher";
import { dispatchYataXrpc } from "./dispatcher";

// P4a-13: WRITE patterns allowed within tenant schema (CREATE/MERGE/SET/DELETE
// against the caller's own `yata_<hash>.<table>` is safe — isolation is enforced
// at the schema layer in the Python translator). Forbid only forms that bypass
// the tenant routing or hit unsupported RW DDL paths.
const FORBIDDEN_KEYWORDS = /\b(DETACH|FOREACH|CALL\s+\{[^}]*(?:CREATE|MERGE|SET|DELETE)[^}]*\})\b/i;

interface Statement {
  statement?: string;
  parameters?: Record<string, unknown>;
  resultDataContents?: string[];
}

interface CypherRequestBody {
  statements?: Statement[];
}

interface CypherStatementResult {
  columns: string[];
  data: Array<{ row: unknown[]; meta: Array<unknown | null> }>;
  stats: {
    contains_updates: boolean;
    nodes_created: number;
    nodes_deleted: number;
    relationships_created: number;
    relationships_deleted: number;
    properties_set: number;
    labels_added: number;
    labels_removed: number;
    indexes_added: number;
    indexes_removed: number;
    constraints_added: number;
    constraints_removed: number;
  };
}

interface CypherResponseBody {
  results: CypherStatementResult[];
  errors: Array<{ code: string; message: string }>;
}

const EMPTY_STATS: CypherStatementResult["stats"] = {
  contains_updates: false,
  nodes_created: 0,
  nodes_deleted: 0,
  relationships_created: 0,
  relationships_deleted: 0,
  properties_set: 0,
  labels_added: 0,
  labels_removed: 0,
  indexes_added: 0,
  indexes_removed: 0,
  constraints_added: 0,
  constraints_removed: 0,
};

export interface CypherEnv {
  BPMN_DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
}

interface DispatcherVariables {
  ok?: boolean;
  rowCount?: number;
  columnsJson?: string;
  rowsJson?: string;
  translatedSql?: string;
  elapsedMs?: number;
  error?: string;
}

interface DispatcherCypherOk {
  ok: boolean;
  // dispatcher_main.py wraps process result variables under `variables`.
  variables?: DispatcherVariables;
  // Some legacy/test paths return top-level fields — keep both shapes.
  rowCount?: number;
  columnsJson?: string;
  rowsJson?: string;
  translatedSql?: string;
  elapsedMs?: number;
  error?: string;
}

function withConstraintHeader(resp: Response): Response {
  const headers = new Headers(resp.headers);
  headers.set("Sql-Constraint-Mode", "rw-eventual");
  headers.set("X-Yatabase-Surface", "cypher");
  return new Response(resp.body, { status: resp.status, headers });
}

function jsonResponse(status: number, body: unknown): Response {
  return withConstraintHeader(
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json" },
    }),
  );
}

function neoErrorBody(code: string, message: string): CypherResponseBody {
  return { results: [], errors: [{ code, message }] };
}

function parseStatements(input: unknown): { statements: Statement[]; error?: string } {
  if (!input || typeof input !== "object") return { statements: [], error: "expected JSON object body" };
  const body = input as CypherRequestBody & { query?: string; parameters?: Record<string, unknown> };

  // Three accepted shapes for the request body, in priority order:
  //
  //   1. Neo4j HTTP API:   {statements:[{statement, parameters?}, ...]}
  //   2. Bare statement:   {statement: "MATCH ...", parameters?: {...}}
  //   3. Quickstart alias: {query: "MATCH ...", parameters?: {...}}
  //
  // Shape 3 is what every doc / quickstart / OpenAPI example shows
  // (and what most BaaS clients send by default). Accepting it as an
  // alias for shape 2 closes a long-standing docs-vs-handler drift.
  if (!body.statements && typeof (body as Statement).statement === "string") {
    return { statements: [body as Statement] };
  }
  if (!body.statements && typeof body.query === "string") {
    return {
      statements: [{ statement: body.query, parameters: body.parameters }],
    };
  }
  if (!Array.isArray(body.statements) || body.statements.length === 0) {
    return { statements: [], error: "missing statements[] (also accepted: {statement:'...'} or {query:'...'})" };
  }
  return { statements: body.statements };
}

function preFlightWriteCheck(statements: Statement[]): string | null {
  for (const s of statements) {
    const text = typeof s.statement === "string" ? s.statement : "";
    if (!text.trim()) return "empty statement";
    if (FORBIDDEN_KEYWORDS.test(text)) {
      return "DETACH DELETE / FOREACH / CALL {WRITE} are not yet supported in P4a — use plain CREATE / SET / DELETE within your tenant schema. Phase 7 will add traversal-aware writes.";
    }
  }
  return null;
}

export async function handleCypherRequest(
  req: Request,
  env: CypherEnv,
  caller: DispatcherCallerContext,
): Promise<Response> {
  if (req.method !== "POST") {
    return jsonResponse(405, neoErrorBody("Yatabase.MethodNotAllowed", "POST required"));
  }

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return jsonResponse(400, neoErrorBody("Yatabase.BadRequest", "request body must be JSON"));
  }

  const { statements, error } = parseStatements(raw);
  if (error) return jsonResponse(400, neoErrorBody("Yatabase.BadRequest", error));

  const writeReason = preFlightWriteCheck(statements);
  if (writeReason) return jsonResponse(400, neoErrorBody("Yatabase.WriteRejected", writeReason));

  const results: CypherStatementResult[] = [];
  const errors: CypherResponseBody["errors"] = [];

  for (const s of statements) {
    // P64: Worker-side KV fallback for simple CREATE/MATCH. Avoids the
    // dispatcher 404 round-trip until the pod ships
    // com.etzhayyim.apps.yata.runCypher. Returns null for queries the KV engine
    // doesn't understand — those fall through to the dispatcher path.
    const { tryServeCypherFromKv } = await import("./cypher-kv");
    const kvResult = await tryServeCypherFromKv(env as never, caller.orgDid, s.statement ?? "");
    if (kvResult) {
      results.push({
        columns: kvResult.columns,
        data: kvResult.data,
        stats: EMPTY_STATS,
        // P97: surface mutation events so the caller (/cypher route in
        // app.ts) can dispatch webhook deliveries via waitUntil.
        ...(kvResult.mutations ? { mutations: kvResult.mutations } : {}),
      } as never);
      continue;
    }

    const dispatcherResult = await dispatchYataXrpc<DispatcherCypherOk>(
      env,
      "com.etzhayyim.apps.yata.runCypher",
      {
        statement: s.statement ?? "",
        parametersJson: JSON.stringify(s.parameters ?? {}),
        format: pickFormat(s.resultDataContents),
      },
      caller,
      { timeoutMs: 30_000 },
    );

    if (!dispatcherResult.ok || !dispatcherResult.data) {
      errors.push({
        code: "Yatabase.DispatcherError",
        message: dispatcherResult.error ?? `dispatcher status ${dispatcherResult.status}`,
      });
      continue;
    }

    const ok = dispatcherResult.data;
    const inner: DispatcherVariables = ok.variables ?? {};
    const errorMsg = inner.error ?? ok.error;
    if (errorMsg) {
      errors.push({ code: "Yatabase.CypherError", message: errorMsg });
      continue;
    }

    const columnsJson = inner.columnsJson ?? ok.columnsJson;
    const rowsJson = inner.rowsJson ?? ok.rowsJson;
    const columns = safeParseArray<string>(columnsJson) ?? [];
    const rows = safeParseArray<unknown[]>(rowsJson) ?? [];

    results.push({
      columns,
      data: rows.map((row) => ({
        row,
        meta: row.map(() => null),
      })),
      stats: EMPTY_STATS,
    });
  }

  const status = errors.length > 0 && results.length === 0 ? 400 : 200;
  return jsonResponse(status, { results, errors } satisfies CypherResponseBody);
}

function pickFormat(rdc: string[] | undefined): "row" | "graph" | "rest" {
  if (!rdc) return "row";
  if (rdc.includes("graph")) return "graph";
  if (rdc.includes("rest")) return "rest";
  return "row";
}

function safeParseArray<T>(raw: string | undefined): T[] | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as T[]) : null;
  } catch {
    return null;
  }
}
