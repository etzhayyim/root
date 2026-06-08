import { sveltekit } from '@sveltejs/kit/vite';
import { paraglideVitePlugin as paraglide } from '@inlang/paraglide-js';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import type { Plugin, UserConfig as ViteUserConfig } from 'vite';

const rootDir = fileURLToPath(new URL('.', import.meta.url));

// Tailwind v4 ships its entrypoint as `@import "tailwindcss"` (resolved via the
// package's `style` export → index.css). Vite/rolldown's CSS @import resolver in
// this setup does not honour that bare specifier and throws ENOENT, so we alias
// `tailwindcss` to the package's self-contained index.css. Resolved dynamically
// (not version-pinned) so a dependabot bump keeps working.
const tailwindEntryCss = path.resolve(
	path.dirname(createRequire(import.meta.url).resolve('tailwindcss/package.json')),
	'index.css'
);
const repoRoot = path.resolve(rootDir, '../../../../..');
const pnpmStore = path.resolve(rootDir, '../../../../../node_modules/.pnpm');
const protobufPkg = path.resolve(pnpmStore, '@bufbuild+protobuf@2.12.0/node_modules/@bufbuild/protobuf');
const connectPkg = path.resolve(pnpmStore, '@connectrpc+connect@2.1.1_@bufbuild+protobuf@2.12.0/node_modules/@connectrpc/connect');
const connectWebPkg = path.resolve(pnpmStore, '@connectrpc+connect-web@2.1.1_@bufbuild+protobuf@2.12.0_@connectrpc+connect@2.1.1_@bufbuild+protobuf@2.12.0_/node_modules/@connectrpc/connect-web');
const clerkPkg = path.resolve(pnpmStore, '@clerk+clerk-js@6.1.0_@solana+web3.js@1.98.4_bufferutil@4.1.0_typescript@5.9.3_utf-8-vaF8acd8f575dfae0b4d488d526c94479a/node_modules/@clerk/clerk-js');
const lexiconRoot = path.resolve(repoRoot, '00-contracts/lexicons');
const paraglideProject = path.resolve(rootDir, 'project.inlang');

const staticNsidPatterns = [
	{ name: 'atProcedure', regex: /\batProcedure[^(]*\(\s*["']([^"']+)["']/g },
	{ name: 'atQuery', regex: /\batQuery[^(]*\(\s*["']([^"']+)["']/g },
	{ name: 'api.call', regex: /\.api\.call\(\s*["']([^"']+)["']/g },
];
const NSID_RE = /^[a-z0-9-]+(?:\.[a-z0-9-]+){2,}$/;

function walkFiles(dir: string, out: string[] = []): string[] {
	if (!fs.existsSync(dir)) return out;
	for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
		const full = path.join(dir, entry.name);
		if (entry.isDirectory()) {
			if (entry.name === 'node_modules' || entry.name === 'dist' || entry.name === '.svelte-kit') continue;
			walkFiles(full, out);
			continue;
		}
		out.push(full);
	}
	return out;
}

function loadLexiconIds(): Set<string> {
	const ids = new Set<string>();
	for (const file of walkFiles(lexiconRoot)) {
		if (!file.endsWith('.json')) continue;
		const json = JSON.parse(fs.readFileSync(file, 'utf8'));
		if (typeof json?.id === 'string') ids.add(json.id);
	}
	return ids;
}

function scanStaticNsids(file: string): Array<{ line: number; nsid: string; source: string }> {
	const src = fs.readFileSync(file, 'utf8');
	const refs: Array<{ line: number; nsid: string; source: string }> = [];
	for (const pattern of staticNsidPatterns) {
		for (const match of src.matchAll(pattern.regex)) {
			const nsid = match[1];
			if (!nsid) continue;
			if (!NSID_RE.test(nsid)) continue;
			const offset = match.index ?? 0;
			const line = src.slice(0, offset).split('\n').length;
			refs.push({ line, nsid, source: pattern.name });
		}
	}
	return refs;
}

function nsidLexiconExistsPlugin(): Plugin {
	return {
		name: 'etzhayyim-nsid-lexicon-exists',
		apply: 'build',
		buildStart() {
			const lexiconIds = loadLexiconIds();
			const scanRoots = [path.resolve(rootDir, 'src')];
			const failures: string[] = [];
			for (const scanRoot of scanRoots) {
				for (const file of walkFiles(scanRoot)) {
					if (!/\.(ts|js|svelte|mjs)$/.test(file)) continue;
					if (file.endsWith('.gen.ts') || file.includes(`${path.sep}typecheck-shims${path.sep}`)) continue;
					for (const ref of scanStaticNsids(file)) {
						if (lexiconIds.has(ref.nsid)) continue;
						failures.push(`${path.relative(rootDir, file)}:${ref.line} references ${ref.nsid} via ${ref.source}, but no lexicon file exists`);
					}
				}
			}
			if (failures.length > 0) {
				this.error(`NSID/lexicon mismatch:\n${failures.join('\n')}`);
			}
		},
	};
}

type VitestTestConfig = {
	coverage?: {
		provider?: string;
		reporter?: string[];
		include?: string[];
	};
};

type ExtendedUserConfig = ViteUserConfig & { test?: VitestTestConfig };

// @mlc-ai/web-llm@0.2.83 inlines loglevel, which writes `window.document.cookie`
// as a localStorage fallback when persisting log level. That path is dead code
// in our usage (Web Worker has no `document`; main thread always has working
// localStorage), but the static no-cookie lint scanner (CHARTER §2(c) +
// ADR-2605172000) does not analyze reachability. Strip the two cookie writes
// at module-load time so the emitted SPA chunks satisfy the cookie-free
// invariant. Reads are preserved (lint allows them).
function stripWebLlmCookieWritesPlugin(): Plugin {
	return {
		name: 'etzhayyim-strip-web-llm-cookie-writes',
		enforce: 'pre',
		transform(code, id) {
			if (!id.includes('@mlc-ai/web-llm')) return null;
			if (!code.includes('document.cookie')) return null;
			// Rewrite the lvalue only (lookahead matches `=` but does not
			// consume it). Reads (`var c = window.document.cookie;`) are
			// untouched. The RHS expression is preserved but assigned to a
			// throwaway object property, so no cookie is ever written.
			const transformed = code.replace(
				/window\.document\.cookie(?=\s*=[^=])/g,
				'({}).cookie /* no-cookie: stripped per CHARTER §2(c) */',
			);
			return transformed === code ? null : { code: transformed, map: null };
		},
	};
}

// In dev mode, bpmn-js / dmn-js / @bpmn-io/* are not installed.
// Provide empty stubs so Vite's import-analysis doesn't error and block app init.
function bpmnStubPlugin(): Plugin {
	const STUB_RE = /^(bpmn-js|dmn-js|@bpmn-io\/)/;
	return {
		name: 'etzhayyim-bpmn-stub',
		apply: 'serve',
		resolveId(id) {
			if (STUB_RE.test(id)) return '\0bpmn-stub:' + id;
			return null;
		},
		load(id) {
			if (id.startsWith('\0bpmn-stub:')) return 'export default class {}; export {};';
			return null;
		},
	};
}

const config: ExtendedUserConfig = {
	server: {
		hmr: { overlay: false },
	},
	plugins: [
		stripWebLlmCookieWritesPlugin(),
		bpmnStubPlugin(),
		nsidLexiconExistsPlugin(),
		sveltekit(),
		...(fs.existsSync(path.join(paraglideProject, 'settings.json'))
			? [paraglide({
				project: './project.inlang',
				outdir: './src/lib/paraglide',
			})]
			: []),
	],
	ssr: {
		external: ['blake3-wasm'],
	},
	worker: {
		format: 'es',
		plugins: () => [stripWebLlmCookieWritesPlugin()],
	},
	build: {
		outDir: 'build',
		emptyOutDir: true,
		rollupOptions: {
			external: [/^bpmn-js/, /^dmn-js/, /^@bpmn-io/],
			output: {
				manualChunks: undefined,
			},
		},
	},
	resolve: {
		alias: [
			// Tailwind v4 CSS entry — see tailwindEntryCss note above.
			{ find: /^tailwindcss$/, replacement: tailwindEntryCss },
			{ find: 'blake3-wasm/esm/browser/index', replacement: path.resolve(pnpmStore, 'blake3-wasm@2.1.5/node_modules/blake3-wasm/esm/browser/index.js') },
			{ find: /^blake3-wasm/, replacement: path.resolve(pnpmStore, 'blake3-wasm@2.1.5/node_modules/blake3-wasm/esm/browser/index.js') },
			{ find: /^@bufbuild\/protobuf$/, replacement: path.resolve(protobufPkg, 'dist/esm/index.js') },
			{ find: /^@bufbuild\/protobuf\/wkt$/, replacement: path.resolve(protobufPkg, 'dist/esm/wkt/index.js') },
			{ find: /^@clerk\/clerk-js$/, replacement: path.resolve(clerkPkg, 'dist/clerk.mjs') },
			{ find: /^@connectrpc\/connect$/, replacement: path.resolve(connectPkg, 'dist/esm/index.js') },
			{ find: /^@connectrpc\/connect-web$/, replacement: path.resolve(connectWebPkg, 'dist/esm/index.js') },
			{ find: /^@connectrpc\/connect\/protocol$/, replacement: path.resolve(connectPkg, 'dist/esm/protocol/index.js') },
			{ find: /^@connectrpc\/connect\/protocol-connect$/, replacement: path.resolve(connectPkg, 'dist/esm/protocol-connect/index.js') },
			{ find: /^@connectrpc\/connect\/protocol-grpc$/, replacement: path.resolve(connectPkg, 'dist/esm/protocol-grpc/index.js') },
			{ find: /^@connectrpc\/connect\/protocol-grpc-web$/, replacement: path.resolve(connectPkg, 'dist/esm/protocol-grpc-web/index.js') },
		],
	},
	test: {
		setupFiles: ['./src/lib/test-setup.ts'],
		coverage: {
			provider: 'v8',
			reporter: ['text'],
			include: [
				'src/lib/device-import.ts',
				'src/lib/sound.ts',
			],
		},
	},
};

export default config;
