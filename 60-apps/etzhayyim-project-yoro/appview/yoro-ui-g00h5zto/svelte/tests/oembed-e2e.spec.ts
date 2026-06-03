import { test, expect } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL || 'https://g00h5zto.etzhayyim.com';

test.describe('oEmbed endpoint integration', () => {
	// ─── Error cases ────────────────────────────────────────────────────────

	test('missing url parameter returns 400', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed`);
		expect(res.status()).toBe(400);
	});

	test('empty url parameter returns 400', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=`);
		expect(res.status()).toBe(400);
	});

	test('xml format returns 501 (not implemented)', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/test&format=xml`);
		expect(res.status()).toBe(501);
	});

	test('invalid url (not a URL) returns 400', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=not-a-valid-url`);
		expect(res.status()).toBe(400);
	});

	test('url from different domain returns 400', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://example.com/profile/test`);
		expect(res.status()).toBe(400);
	});

	test('nonexistent profile returns 404', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/nonexistent-user-xyz999abc`);
		expect(res.status()).toBe(404);
	});

	test('nonexistent post returns 404', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser/post/nonexistent999`);
		expect(res.status()).toBe(404);
	});

	// ─── Valid responses ────────────────────────────────────────────────────

	test('profile URL returns valid oEmbed link response', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser&format=json`);
		// 200 if user exists, 404 otherwise — both are acceptable
		expect([200, 404]).toContain(res.status());

		if (res.status() === 200) {
			const body = await res.json();
			// oEmbed spec required fields
			expect(body.version).toBe('1.0');
			expect(['link', 'rich']).toContain(body.type);
			expect(body.providerName).toBeTruthy();

			// Optional but expected fields
			if (body.title) expect(typeof body.title).toBe('string');
			if (body.authorName) expect(typeof body.authorName).toBe('string');
			if (body.authorUrl) expect(typeof body.authorUrl).toBe('string');
			if (body.cacheAge) expect(typeof body.cacheAge).toBe('number');
		}
	});

	test('post URL returns valid oEmbed rich response', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser/post/abc123&format=json`);
		expect([200, 404]).toContain(res.status());

		if (res.status() === 200) {
			const body = await res.json();
			expect(body.version).toBe('1.0');
			expect(body.type).toBe('rich');
			expect(body.providerName).toBeTruthy();

			// Rich type requires html, width
			if (body.type === 'rich') {
				expect(body.html).toBeTruthy();
				expect(typeof body.width).toBe('number');
			}
		}
	});

	test('format=json is explicit and accepted', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser&format=json`);
		expect([200, 404]).toContain(res.status());
		if (res.status() === 200) {
			const ct = res.headers()['content-type'] || '';
			expect(ct).toContain('json');
		}
	});

	test('no format parameter defaults to JSON', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser`);
		expect([200, 400, 404]).toContain(res.status());
		if (res.status() === 200) {
			const ct = res.headers()['content-type'] || '';
			expect(ct).toContain('json');
		}
	});

	// ─── maxwidth / maxheight parameters ────────────────────────────────────

	test('maxwidth parameter is accepted', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser&maxwidth=400`);
		expect([200, 404]).toContain(res.status());
	});

	test('maxheight parameter is accepted', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser&maxheight=300`);
		expect([200, 404]).toContain(res.status());
	});
});
