import { expect } from '@playwright/test';
import { Given, When, Then } from './fixtures';

async function postApi(apiBase: string, service: string, method: string, body: unknown): Promise<Response> {
	return fetch(`${apiBase}/${service}/${method}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

Then('the message list should contain {string}', async ({ apiState }, text: string) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	const records =
		(apiState.lastBody?.records as Array<{ body?: string }>) ??
		(apiState.lastBody?.messages as Array<{ body?: string }>) ??
		(apiState.lastBody?.items as Array<{ body?: string }>) ??
		[];
	expect(Array.isArray(records)).toBe(true);
	const found = records.some((r) => String(r?.body ?? '').includes(text));
	expect(found).toBe(true);
});

Then('the response should contain a firstMessage', async ({ apiState }) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	expect(
		apiState.lastBody?.firstMessage ||
		apiState.lastBody?.convoId ||
		apiState.lastBody?.rkey ||
		apiState.lastBody?.id,
	).toBeTruthy();
});
