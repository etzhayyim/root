import { defineConfig } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

const baseURL = process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com';

const testDir = defineBddConfig({
	features: './tests/bdd/features/**/*.feature',
	steps: './tests/bdd/steps/*.ts',
});

export default defineConfig({
	testDir,
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
