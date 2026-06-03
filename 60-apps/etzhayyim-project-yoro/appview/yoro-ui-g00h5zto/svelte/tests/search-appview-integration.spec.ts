import { expect, test } from '@playwright/test';

const YORO_BASE = process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com';
const BSKY_XRPC = process.env.BSKY_XRPC_BASE || 'https://bsky.etzhayyim.com/xrpc';
const ATPROTO_XRPC = process.env.PDS_BASE_URL || 'https://atproto.etzhayyim.com/xrpc';

test.describe('search AppView integration', () => {
	test('bsky AppView searchPosts is reachable with YORO CORS', async ({ request }) => {
		const res = await request.get(`${BSKY_XRPC}/app.bsky.feed.searchPosts`, {
			headers: { Origin: YORO_BASE },
			params: { q: 'test', limit: '2' },
			timeout: 10_000,
		});
		expect(res.status()).toBe(200);
		expect(res.headers()['access-control-allow-origin']).toBe(YORO_BASE);

		const body = await res.json() as { posts?: unknown[]; hitsTotal?: number };
		expect(Array.isArray(body.posts)).toBe(true);
		expect(typeof body.hitsTotal).toBe('number');
	});

	test('atproto app.bsky search routes through AppView without timing out', async ({ request }) => {
		const startedAt = Date.now();
		const posts = await request.get(`${ATPROTO_XRPC}/app.bsky.feed.searchPosts`, {
			params: { q: 'test', limit: '2' },
			timeout: 10_000,
		});
		expect(posts.status()).toBe(200);
		expect(Date.now() - startedAt).toBeLessThan(5_000);
		const postsBody = await posts.json() as { posts?: unknown[] };
		expect(Array.isArray(postsBody.posts)).toBe(true);

		const actorsStartedAt = Date.now();
		const actors = await request.get(`${ATPROTO_XRPC}/app.bsky.actor.searchActors`, {
			params: { q: 'etzhayyim', limit: '2' },
			timeout: 10_000,
		});
		expect(actors.status()).toBe(200);
		expect(Date.now() - actorsStartedAt).toBeLessThan(5_000);
		const actorsBody = await actors.json() as { actors?: unknown[] };
		expect(Array.isArray(actorsBody.actors)).toBe(true);
	});

	test('/search posts tab uses bsky AppView and does not fall back to atproto search', async ({ page }) => {
		const appviewSearchResponses: string[] = [];
		const atprotoSearchCalls: string[] = [];

		await page.route(`${ATPROTO_XRPC}/app.bsky.*`, async (route) => {
			atprotoSearchCalls.push(route.request().url());
			await route.abort('blockedbyclient');
		});

		page.on('response', (response) => {
			const url = response.url();
			if (url.startsWith(BSKY_XRPC) && url.includes('/app.bsky.feed.searchPosts')) {
				appviewSearchResponses.push(`${response.status()} ${url}`);
			}
		});

		await page.goto(`${YORO_BASE}/search?q=etzhayyim`, {
			waitUntil: 'domcontentloaded',
			timeout: 30_000,
		});

		await page.getByText('Posts').click({ timeout: 15_000 });
		await expect
			.poll(() => appviewSearchResponses.some((entry) => entry.startsWith('200 ')), {
				timeout: 15_000,
			})
			.toBe(true);

		expect(atprotoSearchCalls).toEqual([]);
	});
});
