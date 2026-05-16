import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  Kysely,
  PostgresAdapter,
  PostgresIntrospector,
  PostgresQueryCompiler,
} from "kysely";

class CapturingConnection {
  constructor(statements) {
    this.statements = statements;
  }

  async executeQuery(compiledQuery) {
    this.statements.push({
      sql: compiledQuery.sql,
      parameters: Array.from(compiledQuery.parameters ?? []),
    });
    return { rows: [] };
  }

  async *streamQuery() {}
}

class CapturingDriver {
  constructor(statements) {
    this.statements = statements;
  }

  async init() {}

  async acquireConnection() {
    return new CapturingConnection(this.statements);
  }

  async beginTransaction() {}

  async commitTransaction() {}

  async rollbackTransaction() {}

  async releaseConnection() {}

  async destroy() {}
}

function createDb(statements) {
  return new Kysely({
    dialect: {
      createAdapter: () => new PostgresAdapter(),
      createDriver: () => new CapturingDriver(statements),
      createIntrospector: (db) => new PostgresIntrospector(db),
      createQueryCompiler: () => new PostgresQueryCompiler(),
    },
  });
}

async function capture(fn) {
  if (typeof fn !== "function") {
    return [];
  }
  const statements = [];
  const db = createDb(statements);
  try {
    await fn(db);
  } finally {
    await db.destroy();
  }
  return statements;
}

const migrationPath = process.argv[2];
if (!migrationPath) {
  throw new Error("usage: capture-kysely-migration.mjs <migration.ts>");
}

const resolved = path.resolve(migrationPath);
const mod = await import(pathToFileURL(resolved).href);
const result = {
  name: path.basename(resolved).replace(/\.ts$/, ""),
  up: await capture(mod.up),
  down: await capture(mod.down),
};

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
