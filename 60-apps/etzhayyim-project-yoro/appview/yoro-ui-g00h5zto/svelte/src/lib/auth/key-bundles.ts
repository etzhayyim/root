import type {
	KeyBundleClientConfig,
	KeyBundleEnvelopeRecord,
	KeyBundleLookupInput,
	KeyBundleRevokeInput,
	KeyBundleUpsertInput,
} from './types.js';
import { getSessionToken } from './passkey.js';

type KeyBundleResponse = Record<string, unknown>;

function requireField(name: string, value: string): string {
	const trimmed = value.trim();
	if (!trimmed) throw new Error(`${name} is required`);
	return trimmed;
}

/** Normalize API response (accepts both camelCase and snakeCase from server) */
function toRecord(value: unknown): KeyBundleEnvelopeRecord {
	if (!value || typeof value !== 'object') {
		throw new Error('invalid key bundle response');
	}
	const p = value as Record<string, unknown>;
	return {
		orgId: String(p.orgId ?? '').trim(),
		userId: String(p.userId ?? '').trim(),
		deviceId: String(p.deviceId ?? '').trim(),
		version: String(p.version ?? '').trim(),
		envelopeJson: String(p.envelopeJson ?? '').trim(),
		createdAt: String(p.createdAt ?? '').trim(),
		updatedAt: String(p.updatedAt ?? '').trim(),
		revoked: Boolean(p.revoked),
	};
}

function toErrorMessage(value: unknown, fallback: string): string {
	if (!value || typeof value !== 'object') return fallback;
	const payload = value as Record<string, unknown>;
	if (typeof payload.error === 'string' && (payload.error as string).trim()) return (payload.error as string).trim();
	return fallback;
}

export class KeyBundleClient {
	private readonly baseUrl: string;
	private readonly getAuthToken: () => Promise<string | null>;
	private readonly fetchImpl: typeof fetch;

	constructor(config: KeyBundleClientConfig = {}) {
		this.baseUrl = (config.baseUrl ?? '/api').replace(/\/+$/, '');
		this.getAuthToken = config.getAuthToken ?? getSessionToken;
		this.fetchImpl = config.fetchImpl ?? fetch;
	}

	private async request(
		method: 'GET' | 'PUT' | 'POST',
		path: string,
		body?: Record<string, string>,
	): Promise<Record<string, unknown>> {
		const token = await this.getAuthToken();
		if (!token?.trim()) {
			throw new Error('missing Clerk session token');
		}
		const headers: Record<string, string> = {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json',
		};
		const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
			method,
			headers,
			body: body ? JSON.stringify(body) : undefined,
		});
		let payload: Record<string, unknown> | null = null;
		try {
			payload = (await response.json()) as Record<string, unknown>;
		} catch {
			payload = null;
		}
		if (!response.ok) {
			throw new Error(toErrorMessage(payload, `key bundle request failed: ${response.status}`));
		}
		return payload ?? {};
	}

	async fetchBundle(input: KeyBundleLookupInput): Promise<KeyBundleEnvelopeRecord> {
		const orgId = requireField('orgId', input.orgId);
		const userId = requireField('userId', input.userId);
		const deviceId = requireField('deviceId', input.deviceId);
		const query = new URLSearchParams({ orgId, userId, deviceId });
		const payload = await this.request('GET', `/key-bundles?${query.toString()}`);
		return toRecord(payload);
	}

	async upsertBundle(input: KeyBundleUpsertInput): Promise<KeyBundleEnvelopeRecord> {
		const payload = await this.request('PUT', '/key-bundles', {
			orgId: requireField('orgId', input.orgId),
			userId: requireField('userId', input.userId),
			deviceId: requireField('deviceId', input.deviceId),
			version: requireField('version', input.version),
			envelopeJson: requireField('envelopeJson', input.envelopeJson),
		});
		return toRecord(payload);
	}

	async revokeBundle(input: KeyBundleRevokeInput): Promise<KeyBundleEnvelopeRecord> {
		const payload = await this.request('POST', '/key-bundles/revoke', {
			orgId: requireField('orgId', input.orgId),
			userId: requireField('userId', input.userId),
			deviceId: requireField('deviceId', input.deviceId),
		});
		return toRecord(payload);
	}
}
