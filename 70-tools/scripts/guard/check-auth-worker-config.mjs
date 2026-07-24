import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const configPath = path.join(
	root,
	'orgs/etzhayyim/com-etzhayyim-app-auth/worker/wrangler.jsonc',
);

const raw = fs.readFileSync(configPath, 'utf8');
// Strip JSONC comments (// line, /* block */) before JSON.parse.
const stripped = raw
	.replace(/\/\*[\s\S]*?\*\//g, '')
	.replace(/(^|[^:])\/\/.*$/gm, '$1');
let config;
try {
	config = JSON.parse(stripped);
} catch (error) {
	console.error(`[auth-worker-config] invalid JSON at ${configPath}`);
	console.error(error instanceof Error ? error.message : String(error));
	process.exit(1);
}

const d1s = Array.isArray(config.d1_databases) ? config.d1_databases : [];
const authDb = d1s.find((entry) => entry?.binding === 'AUTH_DB');

if (!authDb) {
	console.error('[auth-worker-config] missing required D1 binding: AUTH_DB');
	process.exit(1);
}

if (typeof authDb.database_id !== 'string' || authDb.database_id.trim().length === 0) {
	console.error('[auth-worker-config] AUTH_DB binding has empty database_id');
	process.exit(1);
}

console.log('[auth-worker-config] OK: AUTH_DB D1 binding is present');
