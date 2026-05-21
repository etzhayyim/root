// schema-describe.ts — tenant schema introspection (P4a-17).
//
// Returns the list of tables + columns visible to the calling tenant,
// scoped to the per-org schema `yata_<sha256(orgDid)[:16]>`. Read-only,
// no BPMN round-trip — Worker queries `information_schema` directly via
// Hyperdrive. This powers the Studio "Schema" pane and the
// `yata.schema.describe` MCP tool.

interface AnyKyselyDb {
  selectFrom(table: string): unknown;
}

export interface SchemaTable {
  name: string;
  rowCountHint: number | null;
  columns: Array<{
    name: string;
    dataType: string;
    nullable: boolean;
    isPrimaryKey: boolean;
  }>;
}

export interface SchemaDescribeResult {
  schema: string;
  tables: SchemaTable[];
  asOf: string;
}

async function getKyselyForRaw(env: { HYPERDRIVE?: unknown }) {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never);
  } catch (e) {
    console.warn("[yatabase][schema-describe] db init failed:", e);
    return null;
  }
}

async function sha256Hex16(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

export async function tenantSchemaName(orgDid: string): Promise<string> {
  return "yata_" + (await sha256Hex16(orgDid));
}

export async function describeTenantSchema(
  env: { HYPERDRIVE?: unknown },
  orgDid: string,
): Promise<SchemaDescribeResult | null> {
  const schema = await tenantSchemaName(orgDid);
  const db = await getKyselyForRaw(env);
  if (!db) return null;

  // Use Kysely raw SQL via the underlying driver. Kysely's selectFrom is
  // typed against the gftd graph schema, but `information_schema.columns`
  // is a system view — we go through the raw `sql` template tag.
// CHARTER-VIOLATION §substrate (centralized DB forbidden): migrate to AT MST + IPFS + Base L2 anchor
  // Worker host SDK exposes `sql` from kysely.
  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    /* fall through */
  }
  if (!sqlTag) return null;

  // Use pg_catalog directly (1.8s vs 14-35s for information_schema with the
  // PK correlated subquery on RW). pg_catalog is part of every RW catalog
  // and supports the same shape we need for the schema viewer.
  const columnsQuery = sqlTag`
    SELECT
      c.relname AS table_name,
      a.attname AS column_name,
      t.typname AS data_type,
      a.attnotnull AS attnotnull,
      COALESCE(co.contype = 'p', false) AS is_pk
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0
    JOIN pg_type t ON t.oid = a.atttypid
    LEFT JOIN pg_constraint co
      ON co.conrelid = c.oid
     AND a.attnum = ANY(co.conkey)
     AND co.contype = 'p'
    WHERE n.nspname = ${schema} AND c.relkind = 'r'
    ORDER BY c.relname ASC, a.attnum ASC
  `;

  let rawRows: Array<Record<string, unknown>> = [];
  try {
    const exec = (columnsQuery as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const result = await exec.call(columnsQuery, db);
    rawRows = result.rows ?? [];
  } catch (e) {
    console.warn("[yatabase][schema-describe] info_schema query failed:", e);
    return { schema, tables: [], asOf: new Date().toISOString() };
  }

  const tablesMap = new Map<string, SchemaTable>();
  for (const row of rawRows) {
    const tableName = String(row.table_name ?? "");
    if (!tableName) continue;
    let entry = tablesMap.get(tableName);
    if (!entry) {
      entry = { name: tableName, rowCountHint: null, columns: [] };
      tablesMap.set(tableName, entry);
    }
    entry.columns.push({
      name: String(row.column_name ?? ""),
      dataType: String(row.data_type ?? ""),
      // pg_catalog: attnotnull true → NOT NULL → nullable false.
      // information_schema: is_nullable "YES" → nullable true.
      nullable: row.attnotnull === false
        ? true
        : row.attnotnull === true
          ? false
          : row.is_nullable === "YES" || row.is_nullable === true,
      isPrimaryKey: Boolean(row.is_pk),
    });
  }

  return {
    schema,
    tables: Array.from(tablesMap.values()),
    asOf: new Date().toISOString(),
  };
}
