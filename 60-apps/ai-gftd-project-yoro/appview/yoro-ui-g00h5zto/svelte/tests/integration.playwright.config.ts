import { defineConfig } from '@playwright/test';

export default defineConfig({
	testDir: '.',
	testMatch: ['social-post-integration.spec.ts', 'guest-projector-chat.spec.ts'],
	timeout: 60_000,
	workers: 1,
	webServer: {
		command: 'pnpm preview --host 127.0.0.1 --port 4173',
		url: 'http://127.0.0.1:4173',
		reuseExistingServer: !process.env.CI,
		timeout: 30_000,
	},
	use: {
		baseURL: process.env.YORO_BASE_URL || 'http://127.0.0.1:4173',
		headless: true,
		viewport: { width: 390, height: 844 },
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
	},
	projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
	reporter: [['list']],
});
