import { test } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL ?? 'http://localhost:4173';
const DIR = '/tmp/yoro-screenshots';
const AUTH = '?__test_auth=1';

test.use({
	viewport: { width: 390, height: 844 },
	colorScheme: 'dark',
	deviceScaleFactor: 3,
});

const PAGES = [
	// Auth gate (unauthenticated splash)
	{ name: '00-auth-gate', path: '/', auth: false, wait: 9000 },
	// Public legal pages (no auth needed)
	{ name: '01-privacy', path: '/privacy', auth: false },
	{ name: '02-terms', path: '/terms', auth: false },
	{ name: '03-support-tos', path: '/support/tos', auth: false },
	{ name: '04-support-privacy', path: '/support/privacy', auth: false },
	{ name: '05-profile', path: '/profile/alice.etzhayyim.com', auth: false },
	{ name: '06-welcome', path: '/welcome', auth: false },
	// Authenticated pages (with tab bar)
	{ name: '07-home-vibes', path: '/', auth: true },
	{ name: '08-search', path: '/', auth: true, tab: 'search' },
	{ name: '09-profile-tab', path: '/', auth: true, tab: 'profile' },
	{ name: '10-notifications', path: '/notifications', auth: true },
	{ name: '11-settings', path: '/settings', auth: true },
	{ name: '12-messages', path: '/messages', auth: true },
	{ name: '13-feeds', path: '/feeds', auth: true },
];

for (const pg of PAGES) {
	test(`screenshot ${pg.name}`, async ({ page: p }) => {
		const url = `${BASE}${pg.path}${pg.auth ? AUTH : ''}`;
		await p.goto(url, { waitUntil: 'load', timeout: 15000 });

		if (pg.wait) {
			await p.waitForTimeout(pg.wait);
		} else if (pg.auth) {
			// Wait for Clerk timeout (8s) to pass so layout renders authenticated view
			await p.waitForTimeout(9500);
		} else {
			await p.waitForTimeout(1500);
		}

		// If we need to switch tabs, click the tab via JS
		if (pg.tab) {
			await p.evaluate((tab) => {
				// Find the BottomNav button by label
				const buttons = document.querySelectorAll('nav button[aria-label]');
				for (const btn of buttons) {
					if (btn.getAttribute('aria-label')?.toLowerCase() === tab.toLowerCase()) {
						(btn as HTMLElement).click();
						break;
					}
				}
			}, pg.tab);
			await p.waitForTimeout(800);
		}

		await p.screenshot({ path: `${DIR}/${pg.name}.png`, fullPage: false });
	});
}
