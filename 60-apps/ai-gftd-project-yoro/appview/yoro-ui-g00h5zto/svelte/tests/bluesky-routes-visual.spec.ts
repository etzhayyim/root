import { test, expect } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL || 'https://g00h5zto.etzhayyim.com';

test.use({
	viewport: { width: 390, height: 844 },
	colorScheme: 'dark',
	deviceScaleFactor: 3,
});

// ─── Key pages for visual regression ────────────────────────────────────────

const PAGES: { name: string; path: string }[] = [
	{ name: 'home', path: '/' },
	{ name: 'search', path: '/search' },
	{ name: 'profile', path: '/profile/testuser' },
	{ name: 'profile-followers', path: '/profile/testuser/followers' },
	{ name: 'profile-follows', path: '/profile/testuser/follows' },
	{ name: 'post-thread', path: '/profile/testuser/post/abc' },
	{ name: 'post-liked-by', path: '/profile/testuser/post/abc/liked-by' },
	{ name: 'post-reposted-by', path: '/profile/testuser/post/abc/reposted-by' },
	{ name: 'messages', path: '/messages' },
	{ name: 'messages-inbox', path: '/messages/inbox' },
	{ name: 'messages-settings', path: '/messages/settings' },
	{ name: 'settings', path: '/settings' },
	{ name: 'settings-about', path: '/settings/about' },
	{ name: 'settings-appearance', path: '/settings/appearance' },
	{ name: 'settings-notifications', path: '/settings/notifications' },
	{ name: 'settings-account', path: '/settings/account' },
	{ name: 'settings-privacy', path: '/settings/privacy-and-security' },
	{ name: 'moderation', path: '/moderation' },
	{ name: 'muted-accounts', path: '/moderation/muted-accounts' },
	{ name: 'blocked-accounts', path: '/moderation/blocked-accounts' },
	{ name: 'hashtag', path: '/hashtag/test' },
	{ name: 'feeds', path: '/feeds' },
	{ name: 'lists', path: '/lists' },
	{ name: 'notifications', path: '/notifications' },
	{ name: 'starter-pack-create', path: '/starter-pack/create' },
	{ name: 'welcome', path: '/welcome' },
	{ name: 'privacy', path: '/privacy' },
	{ name: 'terms', path: '/terms' },
	{ name: 'community-guidelines', path: '/support/community-guidelines' },
];

test.describe('Visual: Bluesky routes', () => {
	for (const pg of PAGES) {
		test(`${pg.name} (${pg.path})`, async ({ page }) => {
			await page.goto(`${BASE}${pg.path}`, { waitUntil: 'load', timeout: 30000 });
			await page.waitForLoadState('networkidle');
			// Allow animations / skeleton loaders to settle
			await page.waitForTimeout(1500);
			await expect(page).toHaveScreenshot(`bluesky-${pg.name}.png`, {
				maxDiffPixelRatio: 0.05,
			});
		});
	}
});
