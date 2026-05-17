import { expect, test, type APIRequestContext } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL || '/';
const PDS = process.env.PDS_BASE_URL || 'https://atproto.etzhayyim.com';

type FeedPost = {
	uri: string;
	author?: { did?: string; handle?: string };
	embed?: { type?: string; images?: unknown[] } | null;
	record?: {
		text?: string;
		embed?: {
			$type?: string;
			images?: Array<{ image?: { ref?: { $link?: string } } }>;
		} | null;
	};
};

function postRkey(uri: string): string {
	return uri.match(/\/app\.bsky\.feed\.post\/([^/?#]+)$/)?.[1] ?? '';
}

function routeActor(post: FeedPost): string {
	const handle = post.author?.handle?.trim();
	if (handle && handle !== 'handle.invalid') return handle;
	const did = post.author?.did?.trim();
	if (did?.startsWith('did:web:')) return did.slice('did:web:'.length);
	return did ?? '';
}

function hasImage(post: FeedPost): boolean {
	return Boolean(post.embed?.images?.length || post.record?.embed?.images?.some((img) => img.image?.ref?.$link));
}

function route(pathname: string): string {
	return BASE === '/' ? pathname : new URL(pathname, BASE).toString();
}

async function getDiscoverImagePost(request: APIRequestContext): Promise<FeedPost> {
	const res = await request.get(`${PDS}/xrpc/app.bsky.feed.getDiscoverFeed?limit=20`);
	expect(res.ok()).toBe(true);
	const body = await res.json() as { feed?: Array<{ post?: FeedPost }> };
	const post = body.feed?.map((item) => item.post).find((candidate): candidate is FeedPost => !!candidate?.uri && hasImage(candidate));
	expect(post, 'discover feed should contain at least one image post').toBeTruthy();
	expect(postRkey(post!.uri), 'image post rkey should be derivable from AT URI').not.toBe('');
	expect(routeActor(post!), 'image post actor should be routable').not.toBe('');
	return post!;
}

test.describe('social post integration', () => {
	test('PDS feed image post can be resolved as a post thread', async ({ request }) => {
		const post = await getDiscoverImagePost(request);
		const res = await request.get(`${PDS}/xrpc/app.bsky.feed.getPostThread?uri=${encodeURIComponent(post.uri)}&depth=0`);
		expect(res.ok()).toBe(true);
		const body = await res.json() as { thread?: { post?: FeedPost } };
		expect(body.thread?.post?.uri).toBe(post.uri);
		expect(hasImage(body.thread!.post!)).toBe(true);
	});

	test('image post detail renders image without not-found', async ({ page, request }) => {
		const post = await getDiscoverImagePost(request);
		await page.goto(route(`/profile/${encodeURIComponent(routeActor(post))}/post/${encodeURIComponent(postRkey(post.uri))}`), { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Accept' }).click({ timeout: 3000 }).catch((error) => {
			console.warn('cookie banner accept skipped:', error);
		});

		await page.waitForURL(/\/profile\/.+\/post\/[^/]+/, { timeout: 10_000 });
		expect(page.url()).not.toContain('undefined');
		await expect(page.getByText('投稿が見つかりません')).toHaveCount(0, { timeout: 15_000 });
		await expect(page.getByTestId('post-embed-image').first()).toBeVisible({ timeout: 10_000 });
	});

	test('home image post renders image and opens detail without not-found', async ({ page, request }) => {
		await getDiscoverImagePost(request);
		await page.goto(route('/'), { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Accept' }).click({ timeout: 3000 }).catch((error) => {
			console.warn('cookie banner accept skipped:', error);
		});

		const firstPost = page.getByTestId('feed-post').first();
		await expect(firstPost).toBeVisible({ timeout: 15_000 });
		await expect(firstPost).toHaveAttribute('data-post-rkey', /^(?!undefined$).+/);
		await expect(firstPost).toHaveAttribute('data-post-actor', /^(?!undefined$).+/);

		const imagePost = page.getByTestId('feed-post').filter({ has: page.getByTestId('post-embed-image') }).first();
		await expect(imagePost).toBeVisible({ timeout: 10_000 });
		await expect(imagePost).toHaveAttribute('data-post-rkey', /^(?!undefined$).+/);
		await expect(imagePost).toHaveAttribute('data-post-actor', /^(?!undefined$).+/);
		await expect(imagePost.getByTestId('post-embed-image').first()).toBeVisible();

		await imagePost.click({ position: { x: 320, y: 24 } });
		await page.waitForURL(/\/profile\/.+\/post\/[^/]+/, { timeout: 10_000 });
		expect(page.url()).not.toContain('undefined');
		await expect(page.getByText('投稿が見つかりません')).toHaveCount(0, { timeout: 15_000 });
		await expect(page.getByTestId('post-embed-image').first()).toBeVisible({ timeout: 10_000 });
	});

	test('core public pages render stable data states', async ({ page, request }) => {
		const post = await getDiscoverImagePost(request);
		const actor = routeActor(post);
		const rkey = postRkey(post.uri);
		const paths = [
			'/',
			`/profile/${encodeURIComponent(actor)}`,
			`/profile/${encodeURIComponent(actor)}/post/${encodeURIComponent(rkey)}`,
			'/search',
			'/feeds',
			'/projects',
		];

		for (const path of paths) {
			await page.goto(route(path), { waitUntil: 'domcontentloaded' });
			await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch((error) => {
				console.warn(`networkidle wait skipped for ${path}:`, error);
			});
			await expect(page.locator('body')).toBeVisible();
			await expect(page.getByText('タイムラインの読み込みに失敗しました')).toHaveCount(0);
			await expect(page.getByText('The server gave an invalid response')).toHaveCount(0);
			if (path.includes('/post/')) {
				await expect(page.getByText('投稿が見つかりません')).toHaveCount(0, { timeout: 15_000 });
				await expect(page.getByTestId('post-embed-image').first()).toBeVisible({ timeout: 10_000 });
			}
		}
	});

	test('keiba actor profile renders record-backed posts and social controls', async ({ page, request }) => {
		const profileRes = await request.get(`${PDS}/xrpc/app.bsky.actor.getProfile?actor=did%3Aweb%3Akeiba.etzhayyim.com`);
		expect(profileRes.ok()).toBe(true);
		const feedRes = await request.get(`${PDS}/xrpc/app.bsky.feed.getAuthorFeed?actor=did%3Aweb%3Akeiba.etzhayyim.com&limit=5`);
		expect(feedRes.ok()).toBe(true);
		const feedBody = await feedRes.json() as { feed?: Array<{ post?: FeedPost }> };
		expect(feedBody.feed?.some((item) => item.post?.record?.text?.includes('keiba domain registered'))).toBe(true);

		await page.goto(route('/profile/did%3Aweb%3Akeiba.etzhayyim.com'), { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Accept' }).click({ timeout: 3000 }).catch((error) => {
			console.warn('cookie banner accept skipped:', error);
		});
		await expect(page.getByText('プロフィールが見つかりません')).toHaveCount(0, { timeout: 15_000 });
		await expect(page.getByText('keiba domain registered. 0 pages indexed from Common Crawl.').first()).toBeVisible({ timeout: 15_000 });
		await expect(page.getByRole('button', { name: /フォロー|フォロー中/ }).first()).toBeVisible();
		await expect(page.getByRole('button', { name: /フォロワー/ }).first()).toBeVisible();
	});
});
