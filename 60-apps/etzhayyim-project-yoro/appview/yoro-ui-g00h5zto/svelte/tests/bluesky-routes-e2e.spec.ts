import { test, expect } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL || 'https://g00h5zto.etzhayyim.com';

// ─── Helpers ────────────────────────────────────────────────────────────────

function routeTest(path: string, expectedStatus = 200) {
	test(`GET ${path} returns ${expectedStatus}`, async ({ request }) => {
		const res = await request.get(`${BASE}${path}`);
		expect(res.status()).toBe(expectedStatus);
		if (expectedStatus === 200) {
			const ct = res.headers()['content-type'] || '';
			expect(ct).toContain('text/html');
		}
	});
}

// ─── Core ───────────────────────────────────────────────────────────────────

test.describe('Core routes', () => {
	routeTest('/');
	routeTest('/search');
	routeTest('/feeds');
	routeTest('/lists');
	routeTest('/notifications');
	routeTest('/find-contacts');
	routeTest('/welcome');
});

// ─── Profile ────────────────────────────────────────────────────────────────

test.describe('Profile routes', () => {
	const handle = 'testuser';
	const rkey = 'abc123';

	const paths = [
		`/profile/${handle}`,
		`/profile/${handle}/followers`,
		`/profile/${handle}/follows`,
		`/profile/${handle}/known-followers`,
		`/profile/${handle}/search`,
		`/profile/${handle}/feed/${rkey}`,
		`/profile/${handle}/feed/${rkey}/liked-by`,
		`/profile/${handle}/labeler/liked-by`,
	];

	for (const p of paths) {
		routeTest(p);
	}
});

// ─── Post ───────────────────────────────────────────────────────────────────

test.describe('Post routes', () => {
	const handle = 'testuser';
	const rkey = 'abc123';

	const paths = [
		`/profile/${handle}/post/${rkey}`,
		`/profile/${handle}/post/${rkey}/liked-by`,
		`/profile/${handle}/post/${rkey}/reposted-by`,
		`/profile/${handle}/post/${rkey}/quotes`,
	];

	for (const p of paths) {
		routeTest(p);
	}
});

// ─── Lists ──────────────────────────────────────────────────────────────────

test.describe('List routes', () => {
	routeTest('/profile/testuser/lists/abc123');
});

// ─── Messages ───────────────────────────────────────────────────────────────

test.describe('Message routes', () => {
	const paths = [
		'/messages',
		'/messages/test-convo-id',
		'/messages/inbox',
		'/messages/settings',
	];

	for (const p of paths) {
		routeTest(p);
	}
});

// ─── Settings ───────────────────────────────────────────────────────────────

test.describe('Settings routes', () => {
	const subPages = [
		'',
		'/language',
		'/app-passwords',
		'/following-feed',
		'/threads',
		'/external-embeds',
		'/accessibility',
		'/appearance',
		'/saved-feeds',
		'/account',
		'/privacy-and-security',
		'/privacy-and-security/activity',
		'/content-and-media',
		'/interests',
		'/about',
		'/app-icon',
		'/notifications',
		'/notifications/replies',
		'/notifications/mentions',
		'/notifications/quotes',
		'/notifications/likes',
		'/notifications/reposts',
		'/notifications/new-followers',
		'/notifications/likes-on-reposts',
		'/notifications/reposts-on-reposts',
		'/notifications/activity',
		'/notifications/miscellaneous',
		'/find-contacts',
	];

	for (const sub of subPages) {
		routeTest(`/settings${sub}`);
	}
});

// ─── Moderation ─────────────────────────────────────────────────────────────

test.describe('Moderation routes', () => {
	const paths = [
		'/moderation',
		'/moderation/modlists',
		'/moderation/muted-accounts',
		'/moderation/blocked-accounts',
		'/moderation/interaction-settings',
		'/moderation/verification-settings',
	];

	for (const p of paths) {
		routeTest(p);
	}
});

// ─── Discovery ──────────────────────────────────────────────────────────────

test.describe('Discovery routes', () => {
	routeTest('/hashtag/test');
});

// ─── Starter Pack ───────────────────────────────────────────────────────────

test.describe('Starter Pack routes', () => {
	routeTest('/starter-pack/testuser/abc123');
	routeTest('/starter-pack/create');
	routeTest('/starter-pack/edit/abc123');
	routeTest('/starter-pack-short/ABCD');
});

// ─── Support / Legal ────────────────────────────────────────────────────────

test.describe('Support and legal routes', () => {
	const paths = [
		'/support/community-guidelines',
		'/support/copyright',
		'/support/privacy',
		'/support/tos',
		'/privacy',
		'/terms',
	];

	for (const p of paths) {
		routeTest(p);
	}
});

// ─── oEmbed endpoint ────────────────────────────────────────────────────────

test.describe('oEmbed endpoint', () => {
	test('GET /oembed without url returns 400', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed`);
		expect(res.status()).toBe(400);
	});

	test('GET /oembed with format=xml returns 501', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/test&format=xml`);
		expect(res.status()).toBe(501);
	});

	test('GET /oembed with invalid url returns 400', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=not-a-url`);
		expect(res.status()).toBe(400);
	});

	test('GET /oembed with nonexistent profile returns 404', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/nonexistent-user-xyz999`);
		expect(res.status()).toBe(404);
	});

	test('GET /oembed with valid profile URL returns JSON', async ({ request }) => {
		const res = await request.get(`${BASE}/oembed?url=https://yoro.etzhayyim.com/profile/testuser&format=json`);
		// May return 200 (valid user) or 404 (no such user on this instance)
		expect([200, 404]).toContain(res.status());
		if (res.status() === 200) {
			const body = await res.json();
			expect(body).toHaveProperty('version');
			expect(body).toHaveProperty('type');
			expect(body).toHaveProperty('providerName');
		}
	});
});

// ─── Sitemap ────────────────────────────────────────────────────────────────

test.describe('Sitemap endpoint', () => {
	test('GET /sitemap.xml returns valid XML', async ({ request }) => {
		const res = await request.get(`${BASE}/sitemap.xml`);
		expect(res.status()).toBe(200);
		const ct = res.headers()['content-type'] || '';
		expect(ct).toContain('xml');
		const body = await res.text();
		expect(body).toContain('<urlset');
		expect(body).toContain('<url>');
		expect(body).toContain('<loc>');
	});

	test('sitemap contains core public routes', async ({ request }) => {
		const res = await request.get(`${BASE}/sitemap.xml`);
		if (res.status() === 200) {
			const body = await res.text();
			expect(body).toContain('/privacy');
			expect(body).toContain('/terms');
		}
	});
});

// ─── SSR OG tags ────────────────────────────────────────────────────────────

test.describe('SSR OG tags', () => {
	test('profile page has OG meta tags', async ({ request }) => {
		const res = await request.get(`${BASE}/profile/testuser`);
		if (res.status() === 200) {
			const html = await res.text();
			expect(html).toContain('og:title');
			expect(html).toContain('og:description');
			expect(html).toContain('og:image');
			expect(html).toContain('twitter:image');
		}
	});

	test('profile page uses fallback OG image when profile assets are missing', async ({ request }) => {
		const res = await request.get(`${BASE}/profile/nonexistent-user-xyz999`);
		if (res.status() === 200) {
			const html = await res.text();
			expect(html).toContain('https://yoro.etzhayyim.com/logo-v3.png');
			expect(html).toContain('og:image');
			expect(html).toContain('twitter:image');
			expect(html).toContain('og:image:alt');
			expect(html).toContain('application/ld+json');
		}
	});

	test('did:web profile includes complete SEO metadata', async ({ request }) => {
		const did = encodeURIComponent('did:web:a7m8oocs.etzhayyim.com:gta-vi');
		const res = await request.get(`${BASE}/profile/${did}`);
		if (res.status() === 200) {
			const html = await res.text();
			expect(html).toContain('og:image');
			expect(html).toContain('og:image:alt');
			expect(html).toContain('twitter:image');
			expect(html).toContain('application/ld+json');
			expect(html).toContain('at:did');
		}
	});

	test('post page has OG meta tags', async ({ request }) => {
		const res = await request.get(`${BASE}/profile/testuser/post/abc123`);
		if (res.status() === 200) {
			const html = await res.text();
			expect(html).toContain('og:title');
			expect(html).toContain('og:type');
		}
	});

	test('home page returns valid HTML shell', async ({ request }) => {
		const res = await request.get(`${BASE}/`);
		expect(res.status()).toBe(200);
		const html = await res.text();
		expect(html).toContain('<!doctype html>');
		expect(html).toContain('lang="ja"');
	});
});

// ─── SEO fundamentals ───────────────────────────────────────────────────────

test.describe('SEO fundamentals', () => {
	test('robots.txt is accessible', async ({ request }) => {
		const res = await request.get(`${BASE}/robots.txt`);
		expect(res.status()).toBe(200);
		const body = await res.text();
		expect(body).toContain('Sitemap');
		expect(body).toContain('Disallow');
	});

	test('profile page has canonical link', async ({ request }) => {
		const res = await request.get(`${BASE}/profile/testuser`);
		if (res.status() === 200) {
			const html = await res.text();
			expect(html).toContain('rel="canonical"');
		}
	});

	test('profile page has oEmbed discovery link', async ({ request }) => {
		const res = await request.get(`${BASE}/profile/testuser`);
		if (res.status() === 200) {
			const html = await res.text();
			expect(html).toContain('application/json+oembed');
		}
	});
});
