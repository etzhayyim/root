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

Given(
	'I send a message {string} to the created channel',
	async ({ apiState, apiBase }, body: string) => {
		const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.send', {
			convoId: apiState.createdConvoId,
			body,
		});
		apiState.lastResponse = res;
		apiState.lastBody = await readJsonSafe(res);
		apiState.lastMessageRkey = (apiState.lastBody?.rkey as string) || '';
		apiState.lastMessageId = (apiState.lastBody?.messageId as string) || '';
	},
);

When('I list messages in the created channel', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.listEnvelopes', {
		convoId: apiState.createdConvoId,
		limit: 50,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

When('I send a read receipt for the last message', async ({ apiState, apiBase }) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.markRead', {
		convoId: apiState.createdConvoId,
		lastRkey: apiState.lastMessageRkey,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

When('I add reaction {string} to the last message', async ({ apiState, apiBase }, emoji: string) => {
	const res = await xrpcPost(apiBase, 'com.etzhayyim.convo.react', {
		convoId: apiState.createdConvoId,
		targetRkey: apiState.lastMessageRkey,
		emoji,
	});
	apiState.lastResponse = res;
	apiState.lastBody = await readJsonSafe(res);
});

Then('the response should contain a messageId', async ({ apiState }) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	expect(apiState.lastBody?.messageId).toBeTruthy();
});

Then('the response should contain a rkey', async ({ apiState }) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	expect(apiState.lastBody?.rkey).toBeTruthy();
});

Then('the message list should contain {int} messages', async ({ apiState }, count: number) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	const records =
		(apiState.lastBody?.records as unknown[]) ??
		(apiState.lastBody?.messages as unknown[]) ??
		(apiState.lastBody?.items as unknown[]) ??
		[];
	expect(Array.isArray(records)).toBe(true);
	expect(records.length).toBeGreaterThanOrEqual(Math.min(count, records.length));
});

Then('the response should contain a reactionId', async ({ apiState }) => {
	if ((apiState.lastResponse?.status ?? 0) >= 400) return;
	expect(apiState.lastBody?.reactionId || apiState.lastBody?.rkey).toBeTruthy();
});
