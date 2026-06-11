#!/usr/bin/env node
/**
 * Write a RisingWave operation ledger row.
 *
 * Uses psql instead of a Node pg dependency so the wrapper can run from the
 * workspace root without depending on package resolution.
 */
import { spawnSync } from "node:child_process";

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      throw new Error(`unexpected argument: ${arg}`);
    }
    const key = arg.slice(2).replaceAll("-", "_");
    const value = argv[i + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new Error(`missing value for ${arg}`);
    }
    out[key] = value;
    i += 1;
  }
  return out;
}

function sqlString(value) {
  if (value === undefined || value === null || value === "") return "NULL";
  return `'${String(value).replaceAll("'", "''")}'`;
}

function required(args, key) {
  const value = args[key];
  if (!value) throw new Error(`--${key.replaceAll("_", "-")} is required`);
  return value;
}

const args = parseArgs(process.argv.slice(2));
const databaseUrl = process.env.DATABASE_URL || process.env.KOTOBA_URL;
if (!databaseUrl) {
  console.error("[rw-ledger] DATABASE_URL or KOTOBA_URL is required");
  process.exit(2);
}

const operationId = required(args, "operation_id");
const operationKind = required(args, "operation_kind");
const status = required(args, "status");
const now = new Date().toISOString();
const startedAt = status === "running" ? now : undefined;
const finishedAt = status === "succeeded" || status === "failed" ? now : undefined;

const row = {
  operation_id: operationId,
  operation_kind: operationKind,
  status,
  requested_by: args.requested_by || process.env.USER || process.env.LOGNAME,
  session_id: process.env.TERM_SESSION_ID || process.env.SSH_TTY || "",
  purpose: args.purpose,
  lease_name: args.lease_name || process.env.RW_OP_LEASE_NAME || "risingwave-operation-lock",
  lease_holder: args.lease_holder || process.env.RW_OP_ID || operationId,
  migration_name: args.migration_name,
  helm_release: args.helm_release,
  git_ref: args.git_ref,
  payload_json: args.payload_json,
  pre_state_json: args.pre_state_json,
  health_gate_json: args.health_gate_json,
  post_state_json: args.post_state_json,
  error_text: args.error_text,
  created_at: args.created_at || now,
  started_at: startedAt,
  finished_at: finishedAt,
  org_id: args.org_id,
  user_id: args.user_id,
  actor_id: args.actor_id || "sys.risingwave.ops.wrapper",
};

const updateColumns = [
  "operation_kind",
  "status",
  "requested_by",
  "session_id",
  "purpose",
  "lease_name",
  "lease_holder",
  "migration_name",
  "helm_release",
  "git_ref",
  "payload_json",
  "pre_state_json",
  "health_gate_json",
  "post_state_json",
  "error_text",
  "finished_at",
  "org_id",
  "user_id",
  "actor_id",
];

const updateAssignments = [
  ...updateColumns.map((key) => `${key} = ${sqlString(row[key])}`),
  `started_at = COALESCE(${sqlString(row.started_at)}, started_at)`,
].join(",\n      ");

const columns = Object.keys(row);
const values = columns.map((key) => sqlString(row[key]));

const implicitFlushSql = process.env.RW_LEDGER_IMPLICIT_FLUSH === "0"
  ? "SET RW_IMPLICIT_FLUSH = false;"
  : "SET RW_IMPLICIT_FLUSH = true;";
const flushSql = process.env.RW_LEDGER_FLUSH === "0" ? "" : "\nFLUSH;\n";

const sql = `
${implicitFlushSql}

UPDATE vertex_risingwave_operation
SET
      ${updateAssignments}
WHERE operation_id = ${sqlString(operationId)};

INSERT INTO vertex_risingwave_operation (${columns.join(", ")})
SELECT ${values.join(", ")}
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_risingwave_operation
  WHERE operation_id = ${sqlString(operationId)}
);
${flushSql}
`;

const result = spawnSync("psql", [databaseUrl, "-v", "ON_ERROR_STOP=1", "-qAtc", sql], {
  encoding: "utf8",
});

if (result.status !== 0) {
  if (result.stdout) process.stderr.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  process.exit(result.status ?? 1);
}

console.error(`[rw-ledger] ${status} ${operationId}`);
