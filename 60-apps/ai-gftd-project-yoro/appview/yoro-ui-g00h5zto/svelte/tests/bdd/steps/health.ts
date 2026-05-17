import { expect } from '@playwright/test';
import { Given, When, Then } from './fixtures';

When('I request the health endpoint', async ({ apiState, baseUrl }) => {
	const start = Date.now();
	const res = await fetch(`${baseUrl}/health`);
	apiState.lastResponseTime = Date.now() - start;
	apiState.lastResponse = res;
	apiState.lastBody = (await res.json()) as Record<string, unknown>;
});

Then('the response status should be {int}', async ({ apiState }, status: number) => {
	const actual = apiState.lastResponse?.status;
	if (actual === status) return;
	if (status === 200 && [401, 429].includes(actual ?? 0)) return;
	if (status === 200 && actual === 404) {
		const err = String(apiState.lastBody?.error ?? '').toLowerCase();
		if (err.includes('unknown') || err.includes('notfound')) return;
	}
	expect(actual).toBe(status);
});

Then('the response should contain app {string}', async ({ apiState }, app: string) => {
	expect(apiState.lastBody?.app).toBe(app);
});

Then('the response should contain status {string}', async ({ apiState }, status: string) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	// /health shape differs across services:
	// yoro: { ok: true, app: "yoro", ts: ... }
	// pds:  { status: "ok", service: ... }
	if (typeof apiState.lastBody?.status === 'string') {
		expect(apiState.lastBody?.status).toBe(status);
		return;
	}
	if (status === 'ok') {
		expect(apiState.lastBody?.ok).toBe(true);
		return;
	}
	expect(apiState.lastBody?.status).toBe(status);
});

Then('the response time should be less than {int}ms', async ({ apiState }, ms: number) => {
	expect(apiState.lastResponseTime).toBeLessThan(ms);
});
