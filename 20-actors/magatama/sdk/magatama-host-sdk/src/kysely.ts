// ADR-2605111200: CF Worker → RisingWave 接続は全面禁止。
// createKyselyDb は CF Worker 環境 (caches + WorkerGlobalScope) では fail-fast。
// K8s pod (Bun/Node) では Hyperdrive adapter を通じた実接続を許可 (ADR-2605111300)。
// DB I/O は AgentGateway MCP 経由で K8s pod-side LangServer に dispatch すること。

import { Kysely } from "kysely";
import type { StrictDatabase } from "@gftd/graph-schema";
import { HyperdriveDialect, type Hyperdrive } from "./hyperdrive-dialect.js";

// CF Worker ランタイム検出: caches AND WorkerGlobalScope が両方 defined の場合のみ CF Worker
function isCFWorker(): boolean {
  return typeof caches !== "undefined" && typeof WorkerGlobalScope !== "undefined";
}

export class WorkerDBProhibitedError extends Error {
  constructor() {
    super(
      "createKyselyDb is prohibited in CF Workers (ADR-2605111200). " +
      "CF Worker is edge-only. Route DB I/O through AgentGateway MCP → pod-side LangServer " +
      "or a server-side XRPC endpoint."
    );
    this.name = "WorkerDBProhibitedError";
  }
}

export function setKyselyHyperdrive(_hyperdrive: Hyperdrive | null | undefined): void {
  // No-op (ADR-2605111200). Bindings are no longer stored; Workers must not hold a RW connection.
}

export function getKyselyHyperdrive(): Hyperdrive | null {
  return null;
}

export function createKyselyDb(hyperdrive?: Hyperdrive): Kysely<StrictDatabase> {
  if (isCFWorker()) {
    throw new WorkerDBProhibitedError();
  }
  // Bun/Node pod path (ADR-2605111300): use HyperdriveDialect with provided adapter.
  if (!hyperdrive?.connectionString) {
    throw new Error(
      "createKyselyDb requires a Hyperdrive binding with connectionString in Bun/Node mode (ADR-2605111300)."
    );
  }
  return new Kysely<StrictDatabase>({ dialect: new HyperdriveDialect(hyperdrive) });
}

export type KyselyDb = Kysely<StrictDatabase>;
export { HyperdriveDialect } from "./hyperdrive-dialect.js";
export type { Hyperdrive } from "./hyperdrive-dialect.js";
export const setKyselyRpc = setKyselyHyperdrive;
export const getKyselyRpc = getKyselyHyperdrive;
export { assertPrivateGraphTable, isPrivateGraphTable, writePrivate } from "./private-write.js";
export type { PrivateGraphTable, WritePrivateOptions, WritePrivateResult } from "./private-write.js";

// Re-export Kysely types for convenience
export { sql } from "kysely";
export type { ExpressionBuilder, Expression, SqlBool } from "kysely";
