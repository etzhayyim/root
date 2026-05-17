import { defineConfig } from '@playwright/test';

const baseURL = process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com';

export default defineConfig({
	testDir: './tests',
	testMatch: ['**/*.spec.ts', '**/*.spec.js'],
	timeout: 60_000,
	workers: 1,
	use: {
		baseURL,
		headless: true,
		viewport: { width: 390, height: 844 },
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
	},
	projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
	reporter: [['list'], ['html', { open: 'never' }]],
});
