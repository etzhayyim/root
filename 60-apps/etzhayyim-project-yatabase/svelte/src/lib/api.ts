/**
 * yatabase Studio API client.
 *
 * Thin typed wrappers over the same surfaces documented in
 * `60-apps/etzhayyim-project-yatabase/CLAUDE.md` §Surfaces. All requests
 * carry the user's `sk_live_yata_*` API key as a Bearer token. The
 * Studio never talks to RisingWave / B2 / Stripe directly — every
 * call goes through the same edge Worker the rest of the customer
 * journey uses, so anything that works here works for any SDK client.
 */

import { browser } from '$app/environment';

const _DEFAULT_ORIGIN =
	(browser && (window as any).VITE_YATABASE_ORIGIN) ||
	import.meta.env.VITE_YATABASE_ORIGIN ||
	'';

/** Resolve the absolute origin for a request. Empty string = same-origin. */
function origin(): string {
	return _DEFAULT_ORIGIN;
}

export class ApiError extends Error {
	constructor(
		public readonly status: number,
		public readonly url: string,
		message: string,
	) {
		super(message);
	}
}

interface RequestOpts {
	apiKey?: string;
	body?: unknown;
	method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'HEAD';
	headers?: Record<string, string>;
	rawBody?: BodyInit;
	contentType?: string;
	skipAuth?: boolean;
}

async function request<T = unknown>(path: string, opts: RequestOpts = {}): Promise<T> {
	const url = `${origin()}${path}`;
	const headers: Record<string, string> = {
		accept: 'application/json',
		...(opts.headers || {}),
	};
	if (opts.apiKey && !opts.skipAuth) headers.authorization = `Bearer ${opts.apiKey}`;
	let body: BodyInit | undefined = opts.rawBody;
	if (opts.body !== undefined && body === undefined) {
		headers['content-type'] = opts.contentType || 'application/json';
		body = JSON.stringify(opts.body);
	} else if (opts.contentType && !headers['content-type']) {
		headers['content-type'] = opts.contentType;
	}

	const resp = await fetch(url, {
		method: opts.method || (body ? 'POST' : 'GET'),
		headers,
		body,
		credentials: 'omit',
	});
	if (!resp.ok) {
		const text = await resp.text().catch(() => '');
		throw new ApiError(resp.status, url, text || `HTTP ${resp.status}`);
	}
	const ct = resp.headers.get('content-type') || '';
	if (ct.includes('application/json')) return (await resp.json()) as T;
	if (ct.startsWith('text/')) return (await resp.text()) as unknown as T;
	return (await resp.arrayBuffer()) as unknown as T;
}

// ─── Auth ─────────────────────────────────────────────────────────────────

export interface WhoamiResp {
	did?: string;
	orgDid?: string;
	tenantName?: string | null;
	productScope?: string;
	plan?: string;
	emailAttached?: string | null;
}

export const auth = {
	whoami(apiKey: string) {
		return request<WhoamiResp>('/auth/v1/whoami', { apiKey });
	},
	// Charter Rider §2 (ADR-2605192115): paid upgrades return 403 from this
	// endpoint. Use `donate.submit()` below to drive USDC plan transitions.
	// Free-tier downgrade still flows through here.
	downgradeToFree(apiKey: string) {
		return request<{ ok?: boolean; plan?: string; mode?: string; message?: string }>(
			'/auth/v1/upgrade',
			{
				apiKey,
				body: { plan: 'free' },
			},
		);
	},
	attachEmail(apiKey: string, email: string) {
		return request<{ ok: boolean; message?: string }>('/auth/v1/attach-email', {
			apiKey,
			body: { email },
		});
	},
};

// ─── USDC donation (Charter Rider §2 replacement for Stripe portal/upgrade) ─

export type DonationPurpose =
	| 'donation'
	| 'kisha'
	| 'grant'
	| 'tithe'
	| 'escrow-refund'
	| 'internal-purchase'
	| 'internal-subscription'
	| 'internal-promo';

export interface DonateRequest {
	/** Recipient address on Base L2. */
	to: string;
	/** Amount in human-readable USDC ("50.00") or base units. */
	amountUsdc: string | number;
	/** Purpose category per ADR-2605192115. */
	purpose: DonationPurpose;
	/** Optional memo (≤280 chars). */
	memo?: string;
	/** Optional AT URI being funded. */
	forUri?: string;
}

export interface DonateResponse {
	ok?: boolean;
	error?: string;
	code?: string;
	txHash?: string;
	paymentReceipt?: {
		txHash: string;
		blockNumber: number;
		recordUri: string;
		from?: string;
		to?: string;
		amount?: string;
	};
	message?: string;
}

export const donate = {
	submit(apiKey: string, body: DonateRequest) {
		return request<DonateResponse>('/api/donate', {
			apiKey,
			body,
		});
	},
};

// ─── Plan + usage ─────────────────────────────────────────────────────────

export interface PlanResp {
	plan: string;
	status?: string;
	billing_period_start?: string;
	billing_period_end?: string;
}

export interface UsageMetric {
	metric: string;
	totalQty: number;
}
export interface UsageResp {
	usage: Record<string, UsageMetric>;
	windowHours?: number;
}

export const plan = {
	get(apiKey: string) {
		return request<PlanResp>('/api/plan', { apiKey });
	},
	usage(apiKey: string, windowHours: 24 | 720 = 24) {
		return request<UsageResp>(`/api/usage?window_hours=${windowHours}`, { apiKey });
	},
};

// ─── Cypher ───────────────────────────────────────────────────────────────

export interface CypherResp {
	rows?: Array<Record<string, unknown>>;
	row_count?: number;
	accepted?: boolean;
	source?: string;
	took_ms?: number;
}

export const graph = {
	cypher(apiKey: string, query: string, parameters?: Record<string, unknown>) {
		return request<CypherResp>('/cypher', {
			apiKey,
			body: { query, parameters: parameters ?? {} },
		});
	},
};

// ─── Storage (Supabase-shape REST) ────────────────────────────────────────

export interface BucketRow {
	name: string;
	public_read?: boolean;
	created_at?: string;
	source?: string;
}

export interface ObjectRow {
	name: string;
	size?: number;
	contentType?: string;
	updatedAt?: string;
	etag?: string;
	source?: string;
}

export const storage = {
	buckets(apiKey: string) {
		return request<{ buckets: BucketRow[] }>('/storage/v1/bucket', { apiKey });
	},
	list(apiKey: string, bucket: string, prefix = '', limit = 100) {
		const qs = new URLSearchParams();
		if (prefix) qs.set('prefix', prefix);
		qs.set('limit', String(limit));
		return request<{ objects: ObjectRow[] }>(`/storage/v1/object/list/${encodeURIComponent(bucket)}?${qs}`, {
			apiKey,
		});
	},
	async putObject(apiKey: string, bucket: string, key: string, file: File | Blob, contentType?: string) {
		return request<{ ok: boolean; source?: string; etag?: string }>(
			`/storage/v1/object/${encodeURIComponent(bucket)}/${encodeURIComponent(key)}`,
			{
				apiKey,
				method: 'PUT',
				rawBody: file,
				contentType: contentType || (file as File).type || 'application/octet-stream',
			},
		);
	},
	delete(apiKey: string, bucket: string, key: string) {
		return request<{ ok: boolean; source?: string }>(
			`/storage/v1/object/${encodeURIComponent(bucket)}/${encodeURIComponent(key)}`,
			{ apiKey, method: 'DELETE' },
		);
	},
	mintSignedUrl(apiKey: string, bucket: string, key: string, expiresIn = 3600) {
		return request<{ signedUrl: string; expiresAt?: string }>(
			`/storage/v1/object/sign/${encodeURIComponent(bucket)}/${encodeURIComponent(key)}`,
			{ apiKey, body: { expiresIn } },
		);
	},
	publicUrl(bucket: string, key: string): string {
		return `${origin()}/storage/v1/object/public/${encodeURIComponent(bucket)}/${encodeURIComponent(key)}`;
	},
};

// ─── Outbox review (admin-keyed; not bearer/api-key) ──────────────────────

export interface OutboxRow {
	vertex_id: string;
	org_did?: string | null;
	recipient_email?: string | null;
	recipient_name?: string | null;
	subject?: string | null;
	body_text?: string | null;
	body_html?: string | null;
	kind?: string | null;
	status?: string | null;
	scheduled_at?: string | null;
	sent_at?: string | null;
	retry_count?: number | null;
	last_error?: string | null;
	created_at?: string | null;
}

export interface OutboxListResp {
	rows: OutboxRow[];
	total: number;
	offset: number;
	limit: number;
}

export interface OutboxMutationResp {
	ok: boolean;
	vertex_id: string;
	status: string;
	message: string;
}

async function adminPost<T>(path: string, adminKey: string, body: unknown): Promise<T> {
	return request<T>(path, {
		method: 'POST',
		body,
		headers: { 'x-yata-admin-key': adminKey },
		skipAuth: true,
	});
}

export const outbox = {
	list(adminKey: string, opts: { status?: string; kind?: string; limit?: number } = {}) {
		return adminPost<OutboxListResp>('/api/outbox/list', adminKey, {
			status: opts.status ?? 'queued-no-recipient',
			kind: opts.kind,
			limit: opts.limit ?? 50,
		});
	},
	approve(
		adminKey: string,
		input: {
			vertex_id: string;
			recipient_email: string;
			recipient_name?: string;
			subject?: string;
			body_text?: string;
			body_html?: string;
		},
	) {
		return adminPost<OutboxMutationResp>('/api/outbox/approve', adminKey, input);
	},
	reject(adminKey: string, vertex_id: string, reason = '') {
		return adminPost<OutboxMutationResp>('/api/outbox/reject', adminKey, { vertex_id, reason });
	},
};

// ─── MCP (read-only handshake — for the Studio "MCP" status panel) ────────

export const mcp = {
	toolsList(apiKey: string) {
		return request<{ tools: Array<{ name: string; description?: string }> }>('/mcp', {
			apiKey,
			body: { jsonrpc: '2.0', id: 1, method: 'tools/list' },
		});
	},
};
