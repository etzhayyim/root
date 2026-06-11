/**
 * agent-executor.svelte.ts — Browser-side Agent Executor for project AI.
 *
 * Executes tool calls locally in the browser before falling back to PDS.
 * Capabilities:
 * - graph_query: DuckDB/SQL query via kagami-store (XRPC-backed)
 * - summarize: Local LLM text summarization (WebGPU worker)
 * - classify: Local LLM text classification
 * - translate: Local LLM translation
 * - analyze: Local LLM data analysis with graph context
 * - compute: Browser executor worker (reduce/aggregate)
 * - list_labels: List available graph labels
 * - search_graph: Keyword search across graph labels
 *
 * All tools run off-main-thread (Web Worker) where possible.
 * Results are returned synchronously to the caller and persisted
 * to PDS in the background (fire-and-forget).
 *
 * @module
 */

import { useLocalLLM, type ChatMessage } from './local-llm.svelte.js';
import {
	loadLabel,
	hasLabel,
	getCachedRows,
	listAvailableLabels,
	federatedQuery,
} from '$lib/graph/kagami-store.svelte.js';
import { atProcedure, atQuery, searchActors, searchActorsTypeahead } from '$lib/atproto-agent';

/** Tool definition exposed to the LLM for function calling. */
export interface AgentTool {
	name: string;
	description: string;
	parameters: Record<string, { type: string; description: string; required?: boolean }>;
}

/** Result of a tool execution. */
export interface ToolResult {
	tool: string;
	success: boolean;
	data: unknown;
	durationMs: number;
	executedIn: 'browser' | 'pds';
}

/** Browser-executable tools with their definitions. */
export const BROWSER_TOOLS: AgentTool[] = [
	{
		name: 'xrpc.call',
		description: '任意の XRPC NSID を呼び出す。nsid と params/body を指定。',
		parameters: {
			nsid: { type: 'string', description: 'XRPC NSID', required: true },
			httpMethod: { type: 'string', description: 'GET or POST (default: POST)', required: false },
			params: { type: 'string', description: 'クエリ/ボディの JSON object', required: false },
			body: { type: 'string', description: 'POST body (params の別名)', required: false },
			timeoutMs: { type: 'number', description: 'timeout ms (default: 15000)', required: false },
		},
	},
	{
		name: 'mcp.call',
		description: 'MCP JSON-RPC を com.etzhayyim.mcp.message 経由で実行する。',
		parameters: {
			method: { type: 'string', description: 'MCP method (例: tools/list, tools/call)', required: true },
			params: { type: 'string', description: 'JSON-RPC params object', required: false },
			endpoint: { type: 'string', description: 'MCP endpoint (default: atproto.etzhayyim.com)', required: false },
		},
	},
	{
		name: 'forms.call',
		description: 'forms MCP ツールを呼び出す。operation はツール関数名（例: list-forms, get-form, submit-form）。',
		parameters: {
			operation: { type: 'string', description: 'forms operation name', required: true },
			args: { type: 'string', description: 'tools/call に渡す arguments object(JSON)', required: false },
			endpoint: { type: 'string', description: 'MCP endpoint (default: atproto.etzhayyim.com)', required: false },
		},
	},
	{
		name: 'bpmn.call',
		description: 'bpmn MCP ツールを呼び出す。operation はツール関数名（例: list-definitions, start-process, list-tasks）。',
		parameters: {
			operation: { type: 'string', description: 'bpmn operation name', required: true },
			args: { type: 'string', description: 'tools/call に渡す arguments object(JSON)', required: false },
			endpoint: { type: 'string', description: 'MCP endpoint (default: atproto.etzhayyim.com)', required: false },
		},
	},
	{
		name: 'dmn.call',
		description: 'dmn MCP ツールを呼び出す。operation はツール関数名（例: evaluate, evaluate-all, list-models）。',
		parameters: {
			operation: { type: 'string', description: 'dmn operation name', required: true },
			args: { type: 'string', description: 'tools/call に渡す arguments object(JSON)', required: false },
			endpoint: { type: 'string', description: 'MCP endpoint (default: atproto.etzhayyim.com)', required: false },
		},
	},
	{
		name: 'search_agents',
		description: 'DID/handle/displayName に加え、説明文や業務キーワード（例: 法務・訴訟）から Agent のプロフィール候補を検索して特定する。',
		parameters: {
			query: { type: 'string', description: '検索語 (DID, handle, 表示名, 説明・業務キーワード)', required: true },
			limit: { type: 'number', description: '取得件数 (default: 8)', required: false },
		},
	},
	{
		name: 'graph_query',
		description: 'ナレッジグラフからデータを検索。label (Post, Profile, Article, Project 等) とキーワードで絞り込み。',
		parameters: {
			label: { type: 'string', description: 'Graph label (例: Post, Profile, Article, CohortCompany)', required: true },
			keyword: { type: 'string', description: '検索キーワード', required: false },
			limit: { type: 'number', description: '取得件数 (default: 20)', required: false },
		},
	},
	{
		name: 'list_labels',
		description: '利用可能なグラフラベル一覧を取得。どんなデータがあるか確認する。',
		parameters: {},
	},
	{
		name: 'search_graph',
		description: '複数のラベルを横断してキーワード検索。幅広い情報収集に。',
		parameters: {
			keyword: { type: 'string', description: '検索キーワード', required: true },
			labels: { type: 'string', description: 'カンマ区切りのラベル (省略時は全ラベル)', required: false },
			limit: { type: 'number', description: 'ラベル毎の取得件数 (default: 10)', required: false },
		},
	},
	{
		name: 'summarize',
		description: 'テキストを要約 (ブラウザ内 LLM)。長文の会話履歴やドキュメントを短縮。',
		parameters: {
			text: { type: 'string', description: '要約対象テキスト', required: true },
			maxLength: { type: 'number', description: '要約の最大文字数 (default: 200)', required: false },
		},
	},
	{
		name: 'classify',
		description: 'テキストを分類 (ブラウザ内 LLM)。カテゴリ、センチメント、優先度等。',
		parameters: {
			text: { type: 'string', description: '分類対象テキスト', required: true },
			categories: { type: 'string', description: 'カンマ区切りのカテゴリ候補', required: true },
		},
	},
	{
		name: 'translate',
		description: 'テキストを翻訳 (ブラウザ内 LLM)。',
		parameters: {
			text: { type: 'string', description: '翻訳対象テキスト', required: true },
			targetLang: { type: 'string', description: '翻訳先言語 (例: en, ja, zh)', required: true },
		},
	},
	{
		name: 'analyze',
		description: 'グラフデータを取得し、ブラウザ内 LLM で分析・洞察を生成。',
		parameters: {
			query: { type: 'string', description: '分析したい質問やテーマ', required: true },
			label: { type: 'string', description: 'データソースのラベル', required: false },
		},
	},
	{
		name: 'compute',
		description: '数値データの集計 (sum, mean, max, min, count)。ブラウザ内 Worker で実行。',
		parameters: {
			operation: { type: 'string', description: 'sum | mean | max | min | count', required: true },
			values: { type: 'string', description: 'カンマ区切りの数値', required: true },
		},
	},
];

/** Format tool definitions as a string for LLM system prompt injection. */
export function formatToolsForPrompt(): string {
	return BROWSER_TOOLS.map((t) => {
		const params = Object.entries(t.parameters)
			.map(([k, v]) => `  ${k}: ${v.type}${v.required ? ' (required)' : ''} — ${v.description}`)
			.join('\n');
		return `[${t.name}] ${t.description}${params ? '\n' + params : ''}`;
	}).join('\n\n');
}

/**
 * Parse tool calls from LLM response text.
 * Supports format: [TOOL_CALL: tool_name({"key": "value"})]
 */
export function parseToolCalls(text: string): Array<{ name: string; args: Record<string, unknown> }> {
	const calls: Array<{ name: string; args: Record<string, unknown> }> = [];
	const regex = /\[TOOL_CALL:\s*([A-Za-z0-9_.-]+)\(([\s\S]*?)\)\s*\]/g;
	let match: RegExpExecArray | null;
	while ((match = regex.exec(text)) !== null) {
		try {
			const args = parseToolArgs(match[2]);
			calls.push({ name: match[1], args });
		} catch { /* skip malformed */ }
	}
	return calls;
}

function parseToolArgs(rawArgs: string): Record<string, unknown> {
	const raw = rawArgs.trim();
	if (!raw) return {};

	// Strict JSON form: {"query":"foo"}
	if (raw.startsWith('{')) {
		try {
			return JSON.parse(raw) as Record<string, unknown>;
		} catch {
			// Fall through to loose parser.
		}
	}

	// Loose form: query: "foo", limit: 8 or query="foo"
	const out: Record<string, unknown> = {};

	const parseNamedObject = (key: string): Record<string, unknown> | undefined => {
		const keyRegex = new RegExp(`${key}\\s*(?::|=)\\s*\\{`, 'i');
		const start = raw.search(keyRegex);
		if (start < 0) return undefined;
		const braceStart = raw.indexOf('{', start);
		if (braceStart < 0) return undefined;
		let depth = 0;
		let inQuote: '"' | "'" | null = null;
		let escaped = false;
		for (let i = braceStart; i < raw.length; i += 1) {
			const ch = raw[i];
			if (inQuote) {
				if (escaped) {
					escaped = false;
					continue;
				}
				if (ch === '\\') {
					escaped = true;
					continue;
				}
				if (ch === inQuote) inQuote = null;
				continue;
			}
			if (ch === '"' || ch === "'") {
				inQuote = ch;
				continue;
			}
			if (ch === '{') depth += 1;
			if (ch === '}') {
				depth -= 1;
				if (depth === 0) {
					const objectLiteral = raw.slice(braceStart, i + 1);
					try {
						return JSON.parse(objectLiteral) as Record<string, unknown>;
					} catch {
						return undefined;
					}
				}
			}
		}
		return undefined;
	};

	const paramsObj = parseNamedObject('params');
	if (paramsObj) out.params = paramsObj;
	const bodyObj = parseNamedObject('body');
	if (bodyObj) out.body = bodyObj;

	const pairRegex = /([A-Za-z_][A-Za-z0-9_]*)\s*(?::|=)\s*("(?:\\.|[^"])*"|'(?:\\.|[^'])*'|true|false|null|-?\d+(?:\.\d+)?)/g;
	let m: RegExpExecArray | null;
	while ((m = pairRegex.exec(raw)) !== null) {
		const key = m[1];
		const token = m[2];
		if ((token.startsWith('"') && token.endsWith('"')) || (token.startsWith("'") && token.endsWith("'"))) {
			out[key] = token.slice(1, -1).replace(/\\'/g, "'").replace(/\\"/g, '"');
			continue;
		}
		if (token === 'true') { out[key] = true; continue; }
		if (token === 'false') { out[key] = false; continue; }
		if (token === 'null') { out[key] = null; continue; }
		const num = Number(token);
		out[key] = Number.isFinite(num) ? num : token;
	}

	// Last resort: treat the whole content as a query string.
	if (Object.keys(out).length === 0) {
		return { query: raw };
	}
	return out;
}

// ── Tool Executors ──

async function execGraphQuery(args: Record<string, unknown>): Promise<unknown> {
	const label = String(args.label ?? 'Post');
	const keyword = String(args.keyword ?? '');
	const limit = Number(args.limit ?? 20);

	if (!hasLabel(label)) {
		await loadLabel(label, limit);
	}

	if (keyword) {
		const rows = getCachedRows(label).filter((r) => {
			const text = String(r.text ?? r.val ?? '').toLowerCase();
			return text.includes(keyword.toLowerCase());
		});
		if (rows.length < 3) {
			await federatedQuery(label, keyword, limit);
			const refreshed = getCachedRows(label).filter((r) => {
				const text = String(r.text ?? r.val ?? '').toLowerCase();
				return text.includes(keyword.toLowerCase());
			});
			return { label, keyword, count: refreshed.length, rows: refreshed.slice(0, limit) };
		}
		return { label, keyword, count: rows.length, rows: rows.slice(0, limit) };
	}

	const rows = getCachedRows(label);
	return { label, count: rows.length, rows: rows.slice(0, limit) };
}

type SearchableActor = {
	key?: unknown;
	did?: unknown;
	handle?: unknown;
	displayName?: unknown;
	description?: unknown;
	searchText?: unknown;
};

const LEGAL_QUERY_EXPANSIONS: Array<{ pattern: RegExp; terms: string[] }> = [
	{
		pattern: /少額訴訟|small\s*claims?/i,
		terms: ['少額訴訟', '民事訴訟', '訴訟', '裁判', '法務', '法律', '紛争', 'dispute', 'legal', 'law'],
	},
	{
		pattern: /法務|法律|弁護士|訴訟|裁判|紛争/i,
		terms: ['法務', '法律', '弁護士', '訴訟', '裁判', '紛争', 'legal', 'law', 'lawyer', 'dispute'],
	},
];

function normalizeSearchText(text: string): string {
	return text.normalize('NFKC').toLowerCase().trim();
}

function tokenizeQuery(text: string): string[] {
	return normalizeSearchText(text)
		.split(/[\s、。,.!?！？/・:：()（）\[\]{}「」『』"'`]+/)
		.map((s) => s.trim())
		.filter((s) => s.length >= 2);
}

function buildActorSearchQueries(query: string): string[] {
	const out = [query.trim()];
	for (const token of tokenizeQuery(query)) out.push(token);
	for (const rule of LEGAL_QUERY_EXPANSIONS) {
		if (rule.pattern.test(query)) out.push(...rule.terms);
	}
	const seen = new Set<string>();
	const dedup: string[] = [];
	for (const q of out) {
		const trimmed = q.trim();
		if (!trimmed) continue;
		const key = normalizeSearchText(trimmed);
		if (seen.has(key)) continue;
		seen.add(key);
		dedup.push(trimmed);
		if (dedup.length >= 10) break;
	}
	return dedup;
}

function actorSearchBlob(actor: SearchableActor): string {
	return normalizeSearchText([actor.did, actor.handle, actor.displayName, actor.description, actor.searchText].map((v) => String(v ?? '')).join(' '));
}

function relevanceScore(actor: SearchableActor, originalQuery: string, queryTokens: string[], expansionTerms: string[]): number {
	const haystack = actorSearchBlob(actor);
	const normalizedOriginal = normalizeSearchText(originalQuery);
	let score = 0;
	if (normalizedOriginal && haystack.includes(normalizedOriginal)) score += 100;
	for (const token of queryTokens) {
		if (haystack.includes(token)) score += 12;
	}
	for (const term of expansionTerms) {
		if (haystack.includes(term)) score += 3;
	}
	return score;
}

function toActorView(actor: SearchableActor): Record<string, string> {
	const did = String(actor.did ?? '');
	const handle = String(actor.handle ?? '');
	const identity = handle || did;
	return {
		did,
		handle,
		displayName: String(actor.displayName ?? identity),
		description: String(actor.description ?? ''),
		profileUrl: `https://yoro.etzhayyim.com/profile/${encodeURIComponent(identity)}`,
	};
}

function pickString(...values: unknown[]): string {
	for (const value of values) {
		if (typeof value === 'string' && value.trim()) return value.trim();
	}
	return '';
}

function extractProfileRootId(row: Record<string, unknown>): string {
	const direct = pickString(row.did, row.handle, row.vertex_id);
	if (!direct) return '';
	const [head] = direct.split('::');
	return head ?? direct;
}

function tryParseJsonObject(raw: unknown): Record<string, unknown> {
	if (typeof raw !== 'string') return {};
	try {
		const parsed = JSON.parse(raw);
		return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {};
	} catch {
		return {};
	}
}

function actorFromProfileRow(row: Record<string, unknown>): SearchableActor {
	const valObj = tryParseJsonObject(row.val);
	const profileObj = (valObj.actor ?? valObj.profile ?? valObj) as Record<string, unknown>;
	const flattenText = (value: unknown, out: string[], depth = 0): void => {
		if (depth > 4 || value == null) return;
		if (typeof value === 'string') {
			const s = value.trim();
			if (s) out.push(s);
			return;
		}
		if (typeof value === 'number' || typeof value === 'boolean') {
			out.push(String(value));
			return;
		}
		if (Array.isArray(value)) {
			for (const item of value.slice(0, 24)) flattenText(item, out, depth + 1);
			return;
		}
		if (typeof value === 'object') {
			const obj = value as Record<string, unknown>;
			for (const k of ['text', 'value', 'name', 'displayName', 'description', 'bio']) {
				if (k in obj) flattenText(obj[k], out, depth + 1);
			}
			for (const v of Object.values(obj).slice(0, 24)) flattenText(v, out, depth + 1);
		}
	};

	const collectTexts = (...values: unknown[]): string[] => {
		const out: string[] = [];
		for (const v of values) flattenText(v, out);
		const dedup = new Set<string>();
		const normalized: string[] = [];
		for (const item of out) {
			const key = normalizeSearchText(item);
			if (!key || dedup.has(key)) continue;
			dedup.add(key);
			normalized.push(item);
		}
		return normalized;
	};

	const displayNameTexts = collectTexts(
		row.displayName,
		profileObj.displayName,
		profileObj.name,
		profileObj.displayName_i18n,
		profileObj.name_i18n,
		profileObj.names,
		valObj.displayName,
		valObj.name,
		valObj.displayName_i18n,
		valObj.name_i18n,
	);
	const descriptionTexts = collectTexts(
		row.description,
		row.text,
		profileObj.description,
		profileObj.bio,
		profileObj.description_i18n,
		profileObj.bio_i18n,
		profileObj.descriptions,
		valObj.description,
		valObj.bio,
		valObj.description_i18n,
		valObj.bio_i18n,
		valObj.text,
	);

	const rootId = extractProfileRootId(row);
	const label = String(row.label ?? '');
	const rawVal = pickString(row.val);
	const did = pickString(row.did, profileObj.did, profileObj.actorDid, profileObj.subjectDid, rootId);
	const handle = pickString(
		row.handle,
		profileObj.handle,
		profileObj.username,
		profileObj.atHandle,
		/^(?:@)?[a-z0-9][a-z0-9._-]*\.[a-z]{2,}$/i.test(rawVal) ? rawVal.replace(/^@/, '') : '',
	);
	const displayName = pickString(displayNameTexts[0], handle, did);
	const description = pickString(descriptionTexts[0]);
	const tagText = [label, String(row.vertex_id ?? ''), String(row.src_label ?? ''), String(row.dst_label ?? '')];
	const searchText = [...displayNameTexts, ...descriptionTexts, rawVal, ...tagText].join(' ');
	const key = pickString(did, handle, rootId, row.vertex_id);
	return { key, did, handle, displayName, description, searchText };
}

async function collectActorsFromProfileGraph(queries: string[], limit: number): Promise<SearchableActor[]> {
	const graphLimit = Math.max(limit * 25, 100);
	const available = await listAvailableLabels().catch((error) => {
		console.warn('[silent-fail] agent-executor.svelte.ts: listAvailableLabels failed', error);
		return [];
	});
	const profileLikeLabels = (available ?? [])
		.map((l) => String(l.label ?? ''))
		.filter((label) => /^Profile/i.test(label))
		.slice(0, 12);
	if (profileLikeLabels.length === 0) profileLikeLabels.push('Profile');

	for (const label of profileLikeLabels) {
		if (!hasLabel(label)) await loadLabel(label, graphLimit);
		for (const q of queries.slice(0, 6)) {
			await federatedQuery(label, q, graphLimit);
		}
	}

	return profileLikeLabels.flatMap((label) => getCachedRows(label).map((row) => actorFromProfileRow(row)));
}

async function execSearchAgents(args: Record<string, unknown>): Promise<unknown> {
	const query = String(args.query ?? '').trim();
	const rawLimit = Number(args.limit ?? 8);
	const limit = Number.isFinite(rawLimit) ? Math.max(1, Math.min(20, Math.floor(rawLimit))) : 8;
	if (!query) return { error: 'query is required' };

	// Embedding/semantic RPC path has been archived (kagami.* non-SQL RPC removed).
	// Keep keyword + graph-row search as the supported path.

	// ── Fallback: Keyword search (searchActors + graph) ──
	const searchQueries = buildActorSearchQueries(query);
	const merged = new Map<string, SearchableActor>();

	const addActors = (list: SearchableActor[] | undefined): void => {
		for (const actor of list ?? []) {
			const explicitKey = String(actor.key ?? '');
			const did = String(actor.did ?? '');
			const handle = String(actor.handle ?? '');
			const key = explicitKey || did || handle;
			if (!key) continue;
			const prev = merged.get(key);
			if (!prev) {
				merged.set(key, actor);
				continue;
			}
			const mergedSearchText = [String(prev.searchText ?? ''), String(actor.searchText ?? '')]
				.map((s) => s.trim())
				.filter(Boolean)
				.join(' ');
			merged.set(key, {
				key,
				did: pickString(prev.did, actor.did),
				handle: pickString(prev.handle, actor.handle),
				displayName: pickString(prev.displayName, actor.displayName),
				description: pickString(prev.description, actor.description),
				searchText: mergedSearchText,
			});
		}
	};

	for (const q of searchQueries) {
		const [searchRes, typeaheadRes] = await Promise.allSettled([
			searchActors(q, { limit: Math.max(limit * 2, 8) }),
			searchActorsTypeahead(q, { limit: Math.max(limit, 8) }),
		]);
		if (searchRes.status === 'fulfilled') addActors((searchRes.value?.actors ?? []) as SearchableActor[]);
		if (typeaheadRes.status === 'fulfilled') addActors((typeaheadRes.value?.actors ?? []) as SearchableActor[]);
	}

	let graphFallbackUsed = false;
	if (merged.size < limit) {
		try {
			const graphActors = await collectActorsFromProfileGraph(searchQueries, limit);
			addActors(graphActors);
			graphFallbackUsed = graphActors.length > 0;
		} catch {
			// XRPC graph query can require auth; keep searchActors-only results when fallback fails.
		}
	}

	const queryTokens = tokenizeQuery(query);
	const expansionTerms = searchQueries.slice(1).map((q) => normalizeSearchText(q));
	const actors = Array.from(merged.values())
		.sort((a, b) => {
			const scoreDiff = relevanceScore(b, query, queryTokens, expansionTerms) - relevanceScore(a, query, queryTokens, expansionTerms);
			if (scoreDiff !== 0) return scoreDiff;
			return String(a.displayName ?? a.handle ?? a.did ?? '').localeCompare(String(b.displayName ?? b.handle ?? b.did ?? ''));
		})
		.slice(0, limit)
		.map((actor) => toActorView(actor));

	return {
		query,
		count: actors.length,
		searchMethod: 'keyword',
		searchedQueries: searchQueries,
		graphFallbackUsed,
		actors,
	};
}

async function execXrpcCall(args: Record<string, unknown>): Promise<unknown> {
	const nsid = String(args.nsid ?? '').trim();
	if (!nsid) return { error: 'nsid is required' };

	const method = String(args.httpMethod ?? 'POST').toUpperCase();
	const timeoutMs = Number(args.timeoutMs ?? 15_000);
	const params = (args.params && typeof args.params === 'object') ? (args.params as Record<string, unknown>) : {};
	const body = (args.body && typeof args.body === 'object') ? (args.body as Record<string, unknown>) : params;

	if (method === 'GET') {
		const data = await atQuery<Record<string, unknown>>(nsid, params);
		return { nsid, method, data };
	}
	const data = await atProcedure<Record<string, unknown>>(nsid, body, { timeout: Number.isFinite(timeoutMs) ? timeoutMs : 15_000 });
	return { nsid, method: 'POST', data };
}

async function execMcpCall(args: Record<string, unknown>): Promise<unknown> {
	const method = String(args.method ?? '').trim();
	if (!method) return { error: 'method is required' };
	const endpoint = String(args.endpoint ?? '/api/mcp');
	const params = (args.params && typeof args.params === 'object') ? args.params : {};
	const id = Date.now();
	const res = await fetch(endpoint, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ jsonrpc: '2.0', id, method, params }),
	});
	const json = await res.json() as { result?: unknown; error?: { message?: string } };
	if (json?.error?.message) throw new Error(json.error.message);
	return { method, result: json?.result ?? null };
}

function parseObjectArg(input: unknown): Record<string, unknown> {
	if (input && typeof input === 'object' && !Array.isArray(input)) return input as Record<string, unknown>;
	if (typeof input === 'string' && input.trim()) {
		try {
			const parsed = JSON.parse(input);
			if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed as Record<string, unknown>;
		} catch {
			return {};
		}
	}
	return {};
}

function normalizeOperationName(op: string): string {
	return op.trim().replace(/\s+/g, '-').replace(/_/g, '-');
}

async function execDomainMcpCall(
	domain: 'forms' | 'bpmn' | 'dmn',
	args: Record<string, unknown>,
): Promise<unknown> {
	const opRaw = String(args.operation ?? '').trim();
	if (!opRaw) return { error: 'operation is required' };
	const op = normalizeOperationName(opRaw);
	const endpoint = String(args.endpoint ?? '/api/mcp');
	const toolName = `${domain}.${op}`;
	const callArgs = parseObjectArg(args.args);

	const res = await execMcpCall({
		method: 'tools/call',
		endpoint,
		params: {
			name: toolName,
			arguments: callArgs,
		},
	});

	return { domain, operation: op, toolName, callArgs, mcp: res };
}

async function execListLabels(): Promise<unknown> {
	const labels = await listAvailableLabels();
	return { labels, count: labels.length };
}

async function execSearchGraph(args: Record<string, unknown>): Promise<unknown> {
	const keyword = String(args.keyword ?? '');
	const limitPerLabel = Number(args.limit ?? 10);
	const labelStr = String(args.labels ?? '');

	let targetLabels: string[];
	if (labelStr) {
		targetLabels = labelStr.split(',').map((s) => s.trim()).filter(Boolean);
	} else {
		const available = await listAvailableLabels();
		targetLabels = available.slice(0, 8).map((l) => l.label);
	}

	const results: Array<{ label: string; count: number; sample: unknown[] }> = [];
	for (const label of targetLabels) {
		if (!hasLabel(label)) await loadLabel(label, limitPerLabel);
		const rows = getCachedRows(label).filter((r) => {
			const text = String(r.text ?? r.val ?? '').toLowerCase();
			return text.includes(keyword.toLowerCase());
		});
		if (rows.length > 0) {
			results.push({ label, count: rows.length, sample: rows.slice(0, 3) });
		}
	}
	return { keyword, labelsSearched: targetLabels.length, results };
}

async function execSummarize(args: Record<string, unknown>): Promise<unknown> {
	const text = String(args.text ?? '');
	const maxLength = Number(args.maxLength ?? 200);
	const llm = useLocalLLM();
	if (!llm.isReady) return { error: 'Local LLM not ready', fallback: 'pds' };

	const result = await llm.chatCompletion([
		{ role: 'system', content: `Summarize the following text in ${maxLength} characters or less. Respond in the same language as the input.` },
		{ role: 'user', content: text.slice(0, 4000) },
	], { maxTokens: 256, temperature: 0.3 });

	return { summary: result ?? 'Failed to summarize' };
}

async function execClassify(args: Record<string, unknown>): Promise<unknown> {
	const text = String(args.text ?? '');
	const categories = String(args.categories ?? '');
	const llm = useLocalLLM();
	if (!llm.isReady) return { error: 'Local LLM not ready', fallback: 'pds' };

	const result = await llm.chatCompletion([
		{ role: 'system', content: `Classify the text into one of these categories: ${categories}. Return ONLY the category name, nothing else.` },
		{ role: 'user', content: text.slice(0, 2000) },
	], { maxTokens: 32, temperature: 0.1 });

	return { category: result?.trim() ?? 'unknown', categories: categories.split(',').map((s) => s.trim()) };
}

async function execTranslate(args: Record<string, unknown>): Promise<unknown> {
	const text = String(args.text ?? '');
	const targetLang = String(args.targetLang ?? 'en');
	const llm = useLocalLLM();
	if (!llm.isReady) return { error: 'Local LLM not ready', fallback: 'pds' };

	const result = await llm.chatCompletion([
		{ role: 'system', content: `Translate the following text to ${targetLang}. Return ONLY the translation.` },
		{ role: 'user', content: text.slice(0, 3000) },
	], { maxTokens: 512, temperature: 0.3 });

	return { translation: result ?? text, targetLang };
}

async function execAnalyze(args: Record<string, unknown>): Promise<unknown> {
	const query = String(args.query ?? '');
	const label = String(args.label ?? '');
	const llm = useLocalLLM();
	if (!llm.isReady) return { error: 'Local LLM not ready', fallback: 'pds' };

	// Gather context from graph
	let context = '';
	if (label) {
		if (!hasLabel(label)) await loadLabel(label, 30);
		const rows = getCachedRows(label).slice(0, 20);
		context = rows.map((r) => {
			const val = r.val ? String(r.val).slice(0, 200) : '';
			const text = r.text ? String(r.text).slice(0, 200) : '';
			return `[${r.label}] ${text || val}`;
		}).join('\n');
	} else {
		// Auto-detect relevant labels from query keywords
		const available = await listAvailableLabels();
		for (const { label: l } of available.slice(0, 5)) {
			if (!hasLabel(l)) await loadLabel(l, 10);
			const rows = getCachedRows(l).slice(0, 5);
			for (const r of rows) {
				const text = String(r.text ?? r.val ?? '').slice(0, 150);
				if (text) context += `[${l}] ${text}\n`;
			}
		}
	}

	const result = await llm.chatCompletion([
		{ role: 'system', content: `You are a data analyst. Analyze the following graph data and answer the user's question. Be concise and data-driven. Respond in the same language as the question.\n\n--- Graph Context ---\n${context.slice(0, 3000)}` },
		{ role: 'user', content: query },
	], { maxTokens: 512, temperature: 0.5 });

	return { analysis: result ?? 'Analysis failed', contextLabels: label || 'auto', contextRows: context.split('\n').length };
}

function execCompute(args: Record<string, unknown>): unknown {
	const operation = String(args.operation ?? 'sum');
	const valuesStr = String(args.values ?? '');
	const values = valuesStr.split(',').map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n));

	if (values.length === 0) return { error: 'No valid numbers provided' };

	let result: number;
	switch (operation) {
		case 'sum': result = values.reduce((a, b) => a + b, 0); break;
		case 'mean': result = values.reduce((a, b) => a + b, 0) / values.length; break;
		case 'max': result = Math.max(...values); break;
		case 'min': result = Math.min(...values); break;
		case 'count': result = values.length; break;
		default: return { error: `Unknown operation: ${operation}` };
	}

	return { operation, result, count: values.length };
}

/**
 * Execute a tool by name with given arguments.
 * Returns ToolResult with execution metadata.
 */
export async function executeTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
	const start = performance.now();

	try {
		let data: unknown;
		switch (name) {
			case 'xrpc.call':
			case 'xrpc_call':
				data = await execXrpcCall(args);
				break;
			case 'mcp.call':
			case 'mcp_call':
				data = await execMcpCall(args);
				break;
			case 'forms.call':
			case 'forms_call':
				data = await execDomainMcpCall('forms', args);
				break;
			case 'bpmn.call':
			case 'bpmn_call':
				data = await execDomainMcpCall('bpmn', args);
				break;
			case 'dmn.call':
			case 'dmn_call':
				data = await execDomainMcpCall('dmn', args);
				break;
			case 'search_agents':
			case 'pm.search_agents':
				data = await execSearchAgents(args);
				break;
			case 'graph_query': data = await execGraphQuery(args); break;
			case 'graph_search': data = await execSearchGraph(args); break;
			case 'list_labels': data = await execListLabels(); break;
			case 'search_graph': data = await execSearchGraph(args); break;
			case 'summarize': data = await execSummarize(args); break;
			case 'classify': data = await execClassify(args); break;
			case 'translate': data = await execTranslate(args); break;
			case 'analyze': data = await execAnalyze(args); break;
			case 'compute': data = execCompute(args); break;
			default:
				return { tool: name, success: false, data: { error: `Unknown tool: ${name}` }, durationMs: performance.now() - start, executedIn: 'browser' };
		}

		// Check if fallback to PDS is needed
		if (data && typeof data === 'object' && 'fallback' in data && (data as Record<string, unknown>).fallback === 'pds') {
			return { tool: name, success: false, data, durationMs: performance.now() - start, executedIn: 'browser' };
		}

		return { tool: name, success: true, data, durationMs: performance.now() - start, executedIn: 'browser' };
	} catch (e) {
		return { tool: name, success: false, data: { error: e instanceof Error ? e.message : String(e) }, durationMs: performance.now() - start, executedIn: 'browser' };
	}
}

/**
 * Execute all tool calls parsed from LLM response and return results.
 */
export async function executeToolCalls(calls: Array<{ name: string; args: Record<string, unknown> }>): Promise<ToolResult[]> {
	return Promise.all(calls.map((c) => executeTool(c.name, c.args)));
}

/**
 * Build the system prompt for the project AI agent with browser tool definitions.
 */
export function buildAgentSystemPrompt(projectName: string, extraContext?: string): string {
	return `You are the AI agent for project "${projectName}" on yoro.etzhayyim.com.

## Capabilities
You can execute browser-side tools by including tool calls in your response.
Format: [TOOL_CALL: tool_name({"param": "value"})]

## Available Tools
${formatToolsForPrompt()}

## Rules
- Use tools proactively when the user's question can benefit from data lookup or computation.
- For data questions, use graph_query or search_graph first, then analyze the results.
- Chain multiple tools: e.g., list_labels → graph_query → summarize.
- For workflow/form/decision requests, prioritize domain MCP tools:
  - forms.call for form definitions/submissions (operation examples: list-forms, get-form, submit-form)
  - bpmn.call for process definitions/instances/tasks (operation examples: list-definitions, start-process, list-tasks)
  - dmn.call for decision models/evaluation (operation examples: list-models, evaluate, evaluate-all)
- Prefer domain tools over generic mcp.call when the operation is known.
- If a tool returns an error, explain the issue and suggest alternatives.
- Respond concisely in the same language as the user.
- After tool results arrive, synthesize them into a clear answer.

## Tool Call Examples
- [TOOL_CALL: forms.call({"operation":"list-forms","args":{"status":"active","limit":20}})]
- [TOOL_CALL: bpmn.call({"operation":"list-tasks","args":{"instance-id":"<instance-id>"}})]
- [TOOL_CALL: dmn.call({"operation":"evaluate","args":{"model-id":"<model-id>","decision-id":"<decision-id>","context-json":"{}"}})]
${extraContext ? `\n## Context\n${extraContext}` : ''}`;
}

/**
 * Format tool results as a readable message for the chat.
 */
export function formatToolResultsAsMessage(results: ToolResult[]): string {
	return results.map((r) => {
		const duration = `${r.durationMs.toFixed(0)}ms`;
		const where = r.executedIn === 'browser' ? 'browser' : 'server';
		if (!r.success) {
			const err = (r.data as Record<string, unknown>)?.error ?? 'Unknown error';
			return `**${r.tool}** (${where}, ${duration}) — Error: ${err}`;
		}
		const data = r.data as Record<string, unknown>;
		// Compact display
		if (r.tool === 'compute') return `**${r.tool}** (${where}, ${duration}): ${data.operation} = **${data.result}** (${data.count} values)`;
		if (r.tool === 'classify') return `**${r.tool}** (${where}, ${duration}): **${data.category}**`;
		if (r.tool === 'translate') return `**${r.tool}** → ${data.targetLang} (${where}, ${duration}):\n${data.translation}`;
		if (r.tool === 'summarize') return `**${r.tool}** (${where}, ${duration}):\n${data.summary}`;
		if (r.tool === 'analyze') return `**${r.tool}** (${where}, ${duration}, ${data.contextRows} rows):\n${data.analysis}`;
		if (r.tool === 'list_labels') {
			const labels = (data.labels as Array<{ label: string; count?: number }>) ?? [];
			return `**${r.tool}** (${where}, ${duration}): ${labels.map((l) => `\`${l.label}\`${l.count ? ` (${l.count})` : ''}`).join(', ')}`;
		}
		if (r.tool === 'xrpc.call' || r.tool === 'xrpc_call') {
			return `**${r.tool}** (${where}, ${duration}): \`${data.nsid}\` ${data.method}`;
		}
		if (r.tool === 'mcp.call' || r.tool === 'mcp_call') {
			return `**${r.tool}** (${where}, ${duration}): \`${data.method}\``;
		}
		if (r.tool === 'forms.call' || r.tool === 'forms_call' || r.tool === 'bpmn.call' || r.tool === 'bpmn_call' || r.tool === 'dmn.call' || r.tool === 'dmn_call') {
			return `**${r.tool}** (${where}, ${duration}): \`${data.toolName ?? data.operation ?? ''}\``;
		}
		if (r.tool === 'graph_query' || r.tool === 'search_graph' || r.tool === 'graph_search') {
			const count = data.count ?? data.results;
			return `**${r.tool}** (${where}, ${duration}): ${typeof count === 'number' ? count : Array.isArray(count) ? (count as unknown[]).length : '?'} results`;
		}
		return `**${r.tool}** (${where}, ${duration}): ${JSON.stringify(data).slice(0, 200)}`;
	}).join('\n');
}
