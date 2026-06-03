// Kysely is used here only as a client-side SQL string builder with DummyDriver
// (no DB connection in this file). Compiled SQL is sent to PDS via XRPC
// com.etzhayyim.kagami.sql, which routes to a kotoba-datomic-projection (RisingWave)
// behind the PDS substrate seam. See ADR-2605231500.
// kotoba-datomic-projection: client-side SQL compiler (DummyDriver, no DB connection)
import { DummyDriver, Kysely, PostgresAdapter, PostgresQueryCompiler, sql } from 'kysely';
import { atProcedure } from '$lib/atproto-agent';

type CompilableQuery = { compile(...args: any[]): { sql: string; parameters: readonly unknown[] } };

export const ksql = sql;

export const kyselyDb = new Kysely<any>({
	dialect: {
		createAdapter: () => new PostgresAdapter(),
		createDriver: () => new DummyDriver(),
		createIntrospector: () => {
			throw new Error('kysely introspection is not supported in browser kagami SQL client');
		},
		createQueryCompiler: () => new PostgresQueryCompiler(),
	},
});

export async function graphSql<T>(statement: string): Promise<T[]> {
	const result = await atProcedure<{ rows?: T[] }>('com.etzhayyim.kagami.sql', { statement });
	return Array.isArray(result?.rows) ? result.rows : [];
}

export function sqlString(value: string): string {
	return `'${String(value ?? '').replace(/'/g, "''")}'`;
}

export function inlineSqlValue(value: unknown): string {
	if (value === null || value === undefined) return 'null';
	if (typeof value === 'string') return sqlString(value);
	if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'null';
	if (typeof value === 'boolean') return value ? 'true' : 'false';
	if (value instanceof Date) return sqlString(value.toISOString());
	if (Array.isArray(value)) return `(${value.map((item) => inlineSqlValue(item)).join(', ')})`;
	return sqlString(JSON.stringify(value));
}

export function compileKysely(query: CompilableQuery): string {
	const compiled = query.compile(kyselyDb.getExecutor());
	let text = compiled.sql;
	for (const [index, parameter] of compiled.parameters.entries()) {
		const token = new RegExp(`\\$${index + 1}(?!\\d)`, 'g');
		text = text.replace(token, inlineSqlValue(parameter));
	}
	return text;
}
