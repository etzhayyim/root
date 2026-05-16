/**
 * Strict Kysely schema that forbids legacy catch-all tables.
 *
 * Policy:
 * - catch-all graph tables and their rollups are prohibited in app/runtime code.
 * - Use dedicated typed tables (e.g. `vertex_*`) and dedicated rollup MVs.
 */

import type { Database } from "./database.js";

export type ForbiddenLegacyTables =
  | "vertex_other"
  | "edge_other"
  | "mv_vertex_other_count";

export type StrictDatabase = Omit<Database, ForbiddenLegacyTables>;
