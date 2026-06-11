import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

/**
 * E2E tests against real atproto.etzhayyim.com.
 *
 * atproto.etzhayyim.com requires authentication for all endpoints except /health.
 * Tests validate:
 * - Unauthenticated: endpoint reachability + correct 401 rejection
 * - Authenticated (accessJwt from WebAuthn session): full CRUD round-trip
 */

const PDS = process.env.PDS_BASE_URL || 'https://atproto.etzhayyim.com';
const TOKEN_CACHE_FILE = process.env.YORO_AT_TOKEN_CACHE_FILE?.trim()
	|| path.resolve(process.cwd(), '../../../../../tmp/e2e/yoro-at-token.json');
const USE_WEBAUTHN_TOKEN_BOOTSTRAP = process.env.YORO_USE_WEBAUTHN_TOKEN === '1';
const AUTH_TOKEN = resolveAuthToken();
const IS_AUTHED = !!AUTH_TOKEN;

function readTokenCache(filePath: string): string {
	try {
		if (!fs.existsSync(filePath)) return '';
		const raw = fs.readFileSync(filePath, 'utf8').trim();
		if (!raw) return '';
		if (raw.startsWith('{')) {
			const parsed = JSON.parse(raw) as Record<string, unknown>;
			return typeof parsed.accessJwt === 'string' ? parsed.accessJwt.trim() : '';
		}
		return raw;
	} catch {
		return '';
	}
}

function bootstrapTokenFromWebAuthn(filePath: string): string {
	const args = ['tests/gen-webauthn-at-token.cjs', '--out', filePath, '--quiet'];
	const res = spawnSync('node', args, {
		cwd: process.cwd(),
		encoding: 'utf8',
		timeout: 180_000,
	});
	if (res.status === 0) {
		const token = (res.stdout || '').trim();
		if (token) return token;
		return readTokenCache(filePath);
	}
	if (res.stderr) {
		// Keep runtime context visible without failing unauth flows.
		console.warn(`webauthn token bootstrap failed: ${res.stderr.trim()}`);
	}
	return '';
}

function resolveAuthToken(): string {
	const fromEnv = process.env.YORO_AT_TOKEN?.trim() || '';
	if (fromEnv) return fromEnv;
	const fromCache = readTokenCache(TOKEN_CACHE_FILE);
	if (fromCache) return fromCache;
	if (USE_WEBAUTHN_TOKEN_BOOTSTRAP) return bootstrapTokenFromWebAuthn(TOKEN_CACHE_FILE);
	return '';
}

function authHeaders(): Record<string, string> {
	const h: Record<string, string> = { 'Content-Type': 'application/json' };
	if (AUTH_TOKEN) {
		h['Authorization'] = `Bearer ${AUTH_TOKEN}`;
	}
	return h;
}

async function xrpc(nsid: string, body: Record<string, unknown> = {}) {
	const res = await fetch(`${PDS}/xrpc/${nsid}`, {
		method: 'POST',
		headers: authHeaders(),
		body: JSON.stringify(body),
	});
	return { status: res.status, data: await res.json().catch((_err) => ({})) as Record<string, unknown> };
}

// ─── Health (no auth required) ───────────────────────────────────────────────

test.describe('atproto.etzhayyim.com — Health', () => {
	test('health endpoint returns 200', async () => {
		const res = await fetch(`${PDS}/health`);
		expect(res.status).toBe(200);
		const body = await res.json() as Record<string, unknown>;
		expect(body).toHaveProperty('status');
	});

	test('health response time < 3s', async () => {
		const start = Date.now();
		await fetch(`${PDS}/health`);
		expect(Date.now() - start).toBeLessThan(3000);
	});
});

// ─── Endpoint reachability (accepts 200 or 401) ─────────────────────────────

	test.describe('atproto.etzhayyim.com — Endpoint Reachability', () => {
	test('com.etzhayyim.convo.listPublicConvos is reachable', async () => {
		const { status } = await xrpc('com.etzhayyim.convo.listPublicConvos', { limit: 5 });
		expect([200, 401]).toContain(status);
	});

	test('chat.bsky.convo.listConvos is reachable', async () => {
		const { status } = await xrpc('chat.bsky.convo.listConvos', { limit: 5 });
		expect([200, 401, 404]).toContain(status);
	});

	test('com.etzhayyim.convo.search is reachable', async () => {
		const { status } = await xrpc('com.etzhayyim.convo.search', { q: 'hello', limit: 5 });
		expect([200, 401]).toContain(status);
	});

	test('app.bsky.actor.getProfile is reachable', async () => {
		const { status } = await xrpc('app.bsky.actor.getProfile', {});
		expect([200, 401]).toContain(status);
	});

	test('com.etzhayyim.convo.getUnread is reachable', async () => {
		const { status } = await xrpc('com.etzhayyim.convo.getUnread', {});
		expect([200, 401]).toContain(status);
	});

	test('app.bsky.feed.getTimeline is reachable', async () => {
		const { status } = await xrpc('app.bsky.feed.getTimeline', { limit: 5 });
		expect([200, 401]).toContain(status);
	});

	test('app.bsky.notification.getUnreadCount is reachable', async () => {
		const { status } = await xrpc('app.bsky.notification.getUnreadCount', {});
		expect([200, 401]).toContain(status);
	});

	test('app.bsky.feed.searchPosts is reachable', async () => {
		const { status } = await xrpc('app.bsky.feed.searchPosts', { q: 'test', limit: 5 });
		expect([200, 401]).toContain(status);
	});

	test('com.etzhayyim.convo.createConvo is reachable', async () => {
		const { status } = await xrpc('com.etzhayyim.convo.createConvo', { name: `probe-${Date.now()}` });
		expect([200, 401, 403]).toContain(status);
	});

	test('Like endpoint is reachable', async () => {
		const { status } = await xrpc('app.bsky.feed.like', {
			subject: { uri: 'at://did:plc:test/app.bsky.feed.post/test', cid: 'bafytest' },
		});
		expect([200, 400, 401]).toContain(status);
	});

	test('Repost endpoint is reachable', async () => {
		const { status } = await xrpc('app.bsky.feed.repost', {
			subject: { uri: 'at://did:plc:test/app.bsky.feed.post/test', cid: 'bafytest' },
		});
		expect([200, 400, 401]).toContain(status);
	});

	test('Reply endpoint is reachable', async () => {
		const { status } = await xrpc('app.bsky.feed.post', {
			text: 'e2e reachability reply',
			reply: {
				root: { uri: 'at://did:plc:test/app.bsky.feed.post/test', cid: 'bafytest' },
				parent: { uri: 'at://did:plc:test/app.bsky.feed.post/test', cid: 'bafytest' },
			},
		});
		expect([200, 400, 401, 404]).toContain(status);
	});

	test('Bookmark create endpoint is reachable', async () => {
		const { status } = await xrpc('app.bsky.bookmark.createBookmark', {
			uri: 'at://did:plc:test/app.bsky.feed.post/test',
		});
		expect([200, 400, 401]).toContain(status);
	});

	test('Bookmark delete endpoint is reachable', async () => {
		const { status } = await xrpc('app.bsky.bookmark.deleteBookmark', {
			uri: 'at://did:plc:test/app.bsky.feed.post/test',
		});
		expect([200, 400, 401, 404]).toContain(status);
	});

	test('XRPC DescribeServer is reachable', async () => {
		const res = await fetch(`${PDS}/xrpc/com.atproto.server.describeServer`, {
			method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
		});
		expect([200, 401]).toContain(res.status);
	});

	test('XRPC ResolveHandle is reachable', async () => {
		const res = await fetch(`${PDS}/xrpc/com.atproto.identity.resolveHandle`, {
			method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ handle: 'etzhayyim.com' }),
		});
		expect([200, 400, 401]).toContain(res.status);
	});

	test('XRPC GetSession unauthenticated = 401', async () => {
		const res = await fetch(`${PDS}/xrpc/com.atproto.server.getSession`, {
			method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
		});
		expect(res.status).toBe(401);
	});
});

// ─── Authenticated round-trip (skipped without accessJwt) ───────────────────

test.describe('atproto.etzhayyim.com — Authenticated Round-Trip', () => {
	test.skip(!IS_AUTHED, 'No accessJwt found. Set YORO_AT_TOKEN, or run with YORO_USE_WEBAUTHN_TOKEN=1 to bootstrap from WebAuthn E2E.');

	let convoId = '';
	let rootRkey = '';
	let socialUri = '';
	let socialCid = '';

	test('createConvo', async () => {
		const { status, data } = await xrpc('com.etzhayyim.convo.createConvo', { name: `e2e-auth-${Date.now()}` });
		expect(status).toBe(200);
		convoId = (data.convoId || data.rkey || data.id || '') as string;
		expect(convoId).toBeTruthy();
	});

	test('Send message', async () => {
		if (!convoId) test.skip();
		const { status, data } = await xrpc('com.etzhayyim.convo.send', { convoId, body: 'E2E authenticated test' });
		expect(status).toBe(200);
		rootRkey = (data.rkey || '') as string;
		expect(rootRkey).toBeTruthy();
	});

	test('Send reply', async () => {
		if (!convoId || !rootRkey) test.skip();
		const { status } = await xrpc('com.etzhayyim.convo.send', { convoId, body: 'E2E reply', replyTo: rootRkey, threadId: rootRkey });
		expect(status).toBe(200);
	});

	test('listEnvelopes', async () => {
		if (!convoId) test.skip();
		const { status } = await xrpc('com.etzhayyim.convo.listEnvelopes', { convoId, limit: 10 });
		expect(status).toBe(200);
	});

	test('getThread', async () => {
		if (!convoId || !rootRkey) test.skip();
		const { status } = await xrpc('com.etzhayyim.convo.getThread', { convoId, rootRkey });
		expect(status).toBe(200);
	});

	test('react', async () => {
		if (!convoId || !rootRkey) test.skip();
		const { status } = await xrpc('com.etzhayyim.convo.react', { convoId, rkey: rootRkey, emoji: 'thumbsup' });
		expect(status).toBe(200);
	});

	test('markRead', async () => {
		if (!convoId || !rootRkey) test.skip();
		const { status } = await xrpc('com.etzhayyim.convo.markRead', { convoId, lastRkey: rootRkey });
		expect(status).toBe(200);
	});

	test('getConvo', async () => {
		if (!convoId) test.skip();
		const { status } = await xrpc('chat.bsky.convo.getConvo', { convoId });
		expect(status).toBe(200);
	});

	test('listMembers', async () => {
		if (!convoId) test.skip();
		const { status } = await xrpc('com.etzhayyim.convo.listMembers', { convoId });
		expect(status).toBe(200);
	});

	test('listPublicConvos (authenticated)', async () => {
		const { status, data } = await xrpc('com.etzhayyim.convo.listPublicConvos', { limit: 10 });
		expect(status).toBe(200);
	});

	test('GetProfile (self)', async () => {
		const { status, data } = await xrpc('app.bsky.actor.getProfile', {});
		expect(status).toBe(200);
		expect(data).toHaveProperty('did');
	});

	test('Search messages', async () => {
		const { status } = await xrpc('com.etzhayyim.convo.search', { q: 'E2E', limit: 5 });
		expect(status).toBe(200);
	});

	test('Pick timeline post for social actions', async () => {
		const { status, data } = await xrpc('app.bsky.feed.getTimeline', { limit: 20 });
		expect(status).toBe(200);
		const feed = (data.feed ?? []) as Array<Record<string, unknown>>;
		for (const item of feed) {
			const post = (item?.post ?? item) as Record<string, unknown>;
			const uri = typeof post?.uri === 'string' ? post.uri : '';
			const cid = typeof post?.cid === 'string' ? post.cid : '';
			if (uri && cid) {
				socialUri = uri;
				socialCid = cid;
				break;
			}
		}
		expect(socialUri).toBeTruthy();
		expect(socialCid).toBeTruthy();
	});

	test('Like and unlike timeline post', async () => {
		if (!socialUri || !socialCid) test.skip();
		const likeRes = await xrpc('app.bsky.feed.like', { subject: { uri: socialUri, cid: socialCid } });
		expect([200, 409]).toContain(likeRes.status);
		const unlikeRes = await xrpc('app.bsky.feed.unlike', { uri: socialUri });
		expect([200, 404]).toContain(unlikeRes.status);
	});

	test('Repost and unrepost timeline post', async () => {
		if (!socialUri || !socialCid) test.skip();
		const repostRes = await xrpc('app.bsky.feed.repost', { subject: { uri: socialUri, cid: socialCid } });
		expect([200, 409]).toContain(repostRes.status);
		const unrepostRes = await xrpc('app.bsky.feed.unrepost', { uri: socialUri });
		expect([200, 404]).toContain(unrepostRes.status);
	});

	test('Reply to timeline post', async () => {
		if (!socialUri || !socialCid) test.skip();
		const res = await xrpc('app.bsky.feed.post', {
			text: `E2E reply ${Date.now()}`,
			reply: {
				root: { uri: socialUri, cid: socialCid },
				parent: { uri: socialUri, cid: socialCid },
			},
		});
		expect([200, 400, 403]).toContain(res.status);
	});

	test('Bookmark and unbookmark timeline post', async () => {
		if (!socialUri) test.skip();
		const createRes = await xrpc('app.bsky.bookmark.createBookmark', { uri: socialUri });
		expect([200, 409]).toContain(createRes.status);
		const deleteRes = await xrpc('app.bsky.bookmark.deleteBookmark', { uri: socialUri });
		expect([200, 404]).toContain(deleteRes.status);
	});
});
