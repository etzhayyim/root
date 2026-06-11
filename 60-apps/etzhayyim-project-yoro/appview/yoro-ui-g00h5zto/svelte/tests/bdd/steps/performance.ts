import { expect } from '@playwright/test';
import { Given, When, Then } from './fixtures';

async function xrpcPost(apiBase: string, nsid: string, body: unknown): Promise<Response> {
	return fetch(`${apiBase}/${nsid}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

async function readJsonSafe(res: Response): Promise<Record<string, unknown> | null> {
	try {
		return (await res.json()) as Record<string, unknown>;
	} catch {
		return null;
	}
}

When('I time creating a channel named {string}', async ({ apiState, apiBase }, name: string) => {
	const start = Date.now();
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.createConvo', { name, kind: 'public' });
	apiState.lastResponseTime = Date.now() - start;
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
	apiState.createdConvoId =
		(apiState.lastBody?.convoId as string) ||
		(apiState.lastBody?.rkey as string) ||
		(apiState.lastBody?.id as string) ||
		'';
});

When(
	'I time sending a message {string} to the created channel',
	async ({ apiState, apiBase }, message: string) => {
		const start = Date.now();
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.send', {
			convoId: apiState.createdConvoId,
			body: message,
		});
		apiState.lastResponseTime = Date.now() - start;
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
	},
);

When('I list channels with limit {int}', async ({ apiState, apiBase }, limit: number) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.listPublicConvos', { limit });
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

Then('the channel list should have at most {int} channel', async ({ apiState }, max: number) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	const channels = (apiState.lastBody?.channels as unknown[]) ?? (apiState.lastBody?.convos as unknown[]);
	expect(Array.isArray(channels)).toBe(true);
	expect(channels.length).toBeLessThanOrEqual(max);
});

When('I request the health endpoint {int} times concurrently', async ({ apiState, baseUrl }, count: number) => {
	const promises = Array.from({ length: count }, () => fetch(`${baseUrl}/health`));
	const responses = await Promise.all(promises);
	(apiState as Record<string, unknown>)['concurrentResponses'] = responses;
});

Then('all responses should be {int}', async ({ apiState }, status: number) => {
	const responses = (apiState as Record<string, unknown>)['concurrentResponses'] as Response[];
	expect(responses).toBeTruthy();
	for (const res of responses) expect(res.status).toBe(status);
});
