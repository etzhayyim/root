import {
	DummyDriver,
	Kysely,
	PostgresAdapter,
	PostgresQueryCompiler,
	sql,
// CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
} from 'kysely';
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
	const result = await atProcedure<{ rows?: T[] }>('ai.gftd.kagami.sql', { statement });
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
